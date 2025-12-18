"""
Tenant Connection Manager for Dynamic Multi-Tenant Database Routing
Manages connection pools and routing for cloned tenant databases.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

import mysql.connector
from mysql.connector import pooling
import psycopg2
from psycopg2 import pool
import sqlite3
import pymongo
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.orm import sessionmaker

from .database_cloner import DatabaseCloner


logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class ConnectionStatus(Enum):
    """Connection pool status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    MAINTENANCE = "maintenance"


@dataclass
class TenantConnectionInfo:
    """Tenant database connection information."""
    tenant_id: str
    database_type: DatabaseType
    connection_params: Dict[str, Any]
    pool_size: int
    max_overflow: int
    pool_timeout: int
    created_at: datetime
    last_used: datetime
    status: ConnectionStatus
    error_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ConnectionMetrics:
    """Connection pool metrics."""
    tenant_id: str
    active_connections: int
    idle_connections: int
    total_connections: int
    pool_utilization: float
    error_rate: float
    avg_response_time_ms: float
    last_activity: datetime


class TenantConnectionManager:
    """
    Dynamic connection manager for multi-tenant database routing.
    Manages connection pools for each tenant's cloned database.
    """

    def __init__(self, database_cloner: DatabaseCloner, max_tenants: int = 100):
        """Initialize tenant connection manager."""
        self.database_cloner = database_cloner
        self.max_tenants = max_tenants

        # Connection pools and metadata
        self._connection_pools: Dict[str, Any] = {}
        self._tenant_info: Dict[str, TenantConnectionInfo] = {}
        self._connection_metrics: Dict[str, ConnectionMetrics] = {}

        # Thread safety
        self._lock = threading.RLock()
        self._pool_locks: Dict[str, threading.RLock] = {}

        # Configuration
        self.default_pool_config = {
            "mysql": {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True
            },
            "postgresql": {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True
            },
            "sqlite": {
                "pool_size": 1,  # SQLite doesn't support concurrent writes
                "max_overflow": 0,
                "pool_timeout": 30
            },
            "mongodb": {
                "maxPoolSize": 10,
                "minPoolSize": 1,
                "maxIdleTimeMS": 30000,
                "waitQueueTimeoutMS": 5000
            }
        }

        # Performance monitoring
        self._performance_monitor = PerformanceMonitor()

        # Cleanup tasks
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = datetime.utcnow()

    def get_connection(self, tenant_id: str, db_type: str = None) -> Any:
        """
        Get database connection for tenant.
        Returns connection from pool or creates new pool if needed.
        """
        start_time = time.time()

        try:
            # Ensure tenant pool exists
            if tenant_id not in self._connection_pools:
                if not self._initialize_tenant_pool(tenant_id, db_type):
                    raise ConnectionError(f"Failed to initialize connection pool for tenant: {tenant_id}")

            # Get connection from pool
            with self._get_pool_lock(tenant_id):
                pool = self._connection_pools[tenant_id]
                tenant_info = self._tenant_info[tenant_id]

                if tenant_info.database_type == DatabaseType.MYSQL:
                    connection = self._get_mysql_connection(pool, tenant_info)
                elif tenant_info.database_type == DatabaseType.POSTGRESQL:
                    connection = self._get_postgresql_connection(pool, tenant_info)
                elif tenant_info.database_type == DatabaseType.SQLITE:
                    connection = self._get_sqlite_connection(pool, tenant_info)
                elif tenant_info.database_type == DatabaseType.MONGODB:
                    connection = self._get_mongodb_connection(pool, tenant_info)
                else:
                    raise ValueError(f"Unsupported database type: {tenant_info.database_type}")

                # Update metrics
                self._update_connection_metrics(tenant_id, start_time)
                tenant_info.last_used = datetime.utcnow()

                return connection

        except Exception as e:
            self._handle_connection_error(tenant_id, e)
            raise

    @contextmanager
    def get_connection_context(self, tenant_id: str, db_type: str = None):
        """Context manager for database connections with automatic cleanup."""
        connection = None
        try:
            connection = self.get_connection(tenant_id, db_type)
            yield connection
        finally:
            if connection:
                self._return_connection(tenant_id, connection)

    def create_connection_pool(self, tenant_id: str, force_recreate: bool = False) -> bool:
        """Create or recreate connection pool for tenant."""
        try:
            with self._lock:
                # Close existing pool if recreating
                if force_recreate and tenant_id in self._connection_pools:
                    self.close_tenant_connections(tenant_id)

                return self._initialize_tenant_pool(tenant_id)

        except Exception as e:
            logger.error(f"Failed to create connection pool for tenant {tenant_id}: {e}")
            return False

    def close_tenant_connections(self, tenant_id: str) -> bool:
        """Close all connections for a tenant."""
        try:
            with self._lock:
                if tenant_id not in self._connection_pools:
                    return True

                pool = self._connection_pools[tenant_id]
                tenant_info = self._tenant_info[tenant_id]

                # Close pool based on database type
                if tenant_info.database_type == DatabaseType.MYSQL:
                    if hasattr(pool, 'engine'):
                        pool.engine.dispose()
                elif tenant_info.database_type == DatabaseType.POSTGRESQL:
                    if hasattr(pool, 'engine'):
                        pool.engine.dispose()
                elif tenant_info.database_type == DatabaseType.SQLITE:
                    # SQLite connections are closed individually
                    pass
                elif tenant_info.database_type == DatabaseType.MONGODB:
                    if hasattr(pool, 'close'):
                        pool.close()

                # Clean up
                del self._connection_pools[tenant_id]
                del self._tenant_info[tenant_id]
                if tenant_id in self._connection_metrics:
                    del self._connection_metrics[tenant_id]
                if tenant_id in self._pool_locks:
                    del self._pool_locks[tenant_id]

                logger.info(f"Closed connection pool for tenant: {tenant_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to close connections for tenant {tenant_id}: {e}")
            return False

    def get_tenant_info(self, tenant_id: str) -> Optional[TenantConnectionInfo]:
        """Get tenant connection information."""
        return self._tenant_info.get(tenant_id)

    def get_connection_metrics(self, tenant_id: str) -> Optional[ConnectionMetrics]:
        """Get connection metrics for tenant."""
        return self._connection_metrics.get(tenant_id)

    def get_all_metrics(self) -> Dict[str, ConnectionMetrics]:
        """Get metrics for all tenants."""
        return self._connection_metrics.copy()

    def health_check(self, tenant_id: str = None) -> Dict[str, Any]:
        """Perform health check on tenant connections."""
        if tenant_id:
            return self._health_check_tenant(tenant_id)
        else:
            return self._health_check_all_tenants()

    def cleanup_idle_connections(self) -> Dict[str, int]:
        """Clean up idle connections and return cleanup statistics."""
        cleanup_stats = {}
        current_time = datetime.utcnow()

        if (current_time - self._last_cleanup).seconds < self._cleanup_interval:
            return cleanup_stats

        try:
            with self._lock:
                for tenant_id in list(self._tenant_info.keys()):
                    tenant_info = self._tenant_info[tenant_id]

                    # Check if tenant has been idle
                    idle_time = (current_time - tenant_info.last_used).seconds

                    if idle_time > 1800:  # 30 minutes idle
                        cleanup_stats[tenant_id] = self._cleanup_tenant_pool(tenant_id)

                self._last_cleanup = current_time

        except Exception as e:
            logger.error(f"Error during connection cleanup: {e}")

        return cleanup_stats

    def _initialize_tenant_pool(self, tenant_id: str, db_type: str = None) -> bool:
        """Initialize connection pool for tenant."""
        try:
            # Get tenant clone information
            clone = self._get_tenant_clone_info(tenant_id, db_type)
            if not clone:
                logger.error(f"No clone information found for tenant: {tenant_id}")
                return False

            # Get database type and connection parameters
            database_type = DatabaseType(clone.database_type.value)
            connection_params = self._build_connection_params(clone)

            # Get pool configuration
            pool_config = self.default_pool_config.get(database_type.value, {})

            # Create connection pool
            pool = self._create_database_pool(database_type, connection_params, pool_config)

            if not pool:
                return False

            # Store tenant information
            tenant_info = TenantConnectionInfo(
                tenant_id=tenant_id,
                database_type=database_type,
                connection_params=connection_params,
                pool_size=pool_config.get("pool_size", 5),
                max_overflow=pool_config.get("max_overflow", 10),
                pool_timeout=pool_config.get("pool_timeout", 30),
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                status=ConnectionStatus.HEALTHY
            )

            # Initialize metrics
            metrics = ConnectionMetrics(
                tenant_id=tenant_id,
                active_connections=0,
                idle_connections=0,
                total_connections=0,
                pool_utilization=0.0,
                error_rate=0.0,
                avg_response_time_ms=0.0,
                last_activity=datetime.utcnow()
            )

            # Store everything
            self._connection_pools[tenant_id] = pool
            self._tenant_info[tenant_id] = tenant_info
            self._connection_metrics[tenant_id] = metrics
            self._pool_locks[tenant_id] = threading.RLock()

            logger.info(f"Initialized connection pool for tenant {tenant_id} ({database_type.value})")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize tenant pool {tenant_id}: {e}")
            return False

    def _get_tenant_clone_info(self, tenant_id: str, db_type: str = None):
        """Get tenant clone information from database cloner."""
        clones = self.database_cloner.list_tenant_clones(tenant_id)

        if not clones:
            return None

        # If db_type specified, find matching clone
        if db_type:
            for clone in clones:
                if clone.database_type.value == db_type:
                    return clone

        # Return first active clone
        for clone in clones:
            if clone.status.value == "COMPLETED":
                return clone

        return None

    def _build_connection_params(self, clone) -> Dict[str, Any]:
        """Build connection parameters from clone information."""
        if clone.database_type.value == "mysql":
            return {
                "host": "localhost",
                "port": clone.port,
                "database": clone.database_name,
                "user": clone.connection_params.get("username", "tenant_user"),
                "password": clone.connection_params.get("password", "tenant_password"),
                "charset": "utf8mb4",
                "autocommit": True
            }
        elif clone.database_type.value == "postgresql":
            return {
                "host": "localhost",
                "port": clone.port,
                "database": clone.database_name,
                "user": clone.connection_params.get("username", "tenant_user"),
                "password": clone.connection_params.get("password", "tenant_password")
            }
        elif clone.database_type.value == "sqlite":
            return {
                "database": clone.connection_params.get("database_path", f"/tmp/{clone.database_name}.db")
            }
        elif clone.database_type.value == "mongodb":
            return {
                "host": "localhost",
                "port": clone.port,
                "database": clone.database_name,
                "username": clone.connection_params.get("username"),
                "password": clone.connection_params.get("password")
            }
        else:
            raise ValueError(f"Unsupported database type: {clone.database_type}")

    def _create_database_pool(self, database_type: DatabaseType,
                            connection_params: Dict[str, Any],
                            pool_config: Dict[str, Any]) -> Any:
        """Create database-specific connection pool."""

        if database_type == DatabaseType.MYSQL:
            connection_string = (
                f"mysql+pymysql://{connection_params['user']}:{connection_params['password']}"
                f"@{connection_params['host']}:{connection_params['port']}"
                f"/{connection_params['database']}?charset={connection_params.get('charset', 'utf8mb4')}"
            )

            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=pool_config.get("pool_size", 5),
                max_overflow=pool_config.get("max_overflow", 10),
                pool_timeout=pool_config.get("pool_timeout", 30),
                pool_recycle=pool_config.get("pool_recycle", 3600),
                pool_pre_ping=pool_config.get("pool_pre_ping", True),
                echo=False
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return engine

        elif database_type == DatabaseType.POSTGRESQL:
            connection_string = (
                f"postgresql+psycopg2://{connection_params['user']}:{connection_params['password']}"
                f"@{connection_params['host']}:{connection_params['port']}"
                f"/{connection_params['database']}"
            )

            engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=pool_config.get("pool_size", 5),
                max_overflow=pool_config.get("max_overflow", 10),
                pool_timeout=pool_config.get("pool_timeout", 30),
                pool_recycle=pool_config.get("pool_recycle", 3600),
                pool_pre_ping=pool_config.get("pool_pre_ping", True),
                echo=False
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return engine

        elif database_type == DatabaseType.SQLITE:
            connection_string = f"sqlite:///{connection_params['database']}"

            engine = create_engine(
                connection_string,
                poolclass=NullPool,  # SQLite doesn't support connection pooling well
                echo=False
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return engine

        elif database_type == DatabaseType.MONGODB:
            import pymongo

            if connection_params.get("username"):
                connection_string = (
                    f"mongodb://{connection_params['username']}:{connection_params['password']}"
                    f"@{connection_params['host']}:{connection_params['port']}"
                    f"/{connection_params['database']}"
                )
            else:
                connection_string = (
                    f"mongodb://{connection_params['host']}:{connection_params['port']}"
                    f"/{connection_params['database']}"
                )

            client = pymongo.MongoClient(
                connection_string,
                maxPoolSize=pool_config.get("maxPoolSize", 10),
                minPoolSize=pool_config.get("minPoolSize", 1),
                maxIdleTimeMS=pool_config.get("maxIdleTimeMS", 30000),
                waitQueueTimeoutMS=pool_config.get("waitQueueTimeoutMS", 5000)
            )

            # Test connection
            client.admin.command('ping')

            return client

        else:
            raise ValueError(f"Unsupported database type: {database_type}")

    def _get_mysql_connection(self, pool, tenant_info):
        """Get MySQL connection from pool."""
        return pool.connect()

    def _get_postgresql_connection(self, pool, tenant_info):
        """Get PostgreSQL connection from pool."""
        return pool.connect()

    def _get_sqlite_connection(self, pool, tenant_info):
        """Get SQLite connection from pool."""
        return pool.connect()

    def _get_mongodb_connection(self, pool, tenant_info):
        """Get MongoDB connection from pool."""
        return pool[tenant_info.connection_params["database"]]

    def _return_connection(self, tenant_id: str, connection):
        """Return connection to pool."""
        try:
            if hasattr(connection, 'close'):
                connection.close()
        except Exception as e:
            logger.warning(f"Error returning connection for tenant {tenant_id}: {e}")

    def _get_pool_lock(self, tenant_id: str) -> threading.RLock:
        """Get or create pool lock for tenant."""
        if tenant_id not in self._pool_locks:
            self._pool_locks[tenant_id] = threading.RLock()
        return self._pool_locks[tenant_id]

    def _update_connection_metrics(self, tenant_id: str, start_time: float):
        """Update connection metrics."""
        if tenant_id in self._connection_metrics:
            metrics = self._connection_metrics[tenant_id]
            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Update response time (simple moving average)
            if metrics.avg_response_time_ms == 0:
                metrics.avg_response_time_ms = response_time
            else:
                metrics.avg_response_time_ms = (metrics.avg_response_time_ms * 0.9) + (response_time * 0.1)

            metrics.last_activity = datetime.utcnow()

    def _handle_connection_error(self, tenant_id: str, error: Exception):
        """Handle connection errors and update tenant status."""
        if tenant_id in self._tenant_info:
            tenant_info = self._tenant_info[tenant_id]
            tenant_info.error_count += 1

            # Update status based on error count
            if tenant_info.error_count > 10:
                tenant_info.status = ConnectionStatus.FAILED
            elif tenant_info.error_count > 5:
                tenant_info.status = ConnectionStatus.DEGRADED

        logger.error(f"Connection error for tenant {tenant_id}: {error}")

    def _health_check_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Health check for specific tenant."""
        if tenant_id not in self._tenant_info:
            return {"status": "not_found", "tenant_id": tenant_id}

        try:
            with self.get_connection_context(tenant_id) as conn:
                if hasattr(conn, 'execute'):
                    conn.execute(text("SELECT 1"))
                elif hasattr(conn, 'ping'):
                    conn.ping()

            tenant_info = self._tenant_info[tenant_id]
            metrics = self._connection_metrics.get(tenant_id)

            return {
                "status": "healthy",
                "tenant_id": tenant_id,
                "database_type": tenant_info.database_type.value,
                "connection_status": tenant_info.status.value,
                "error_count": tenant_info.error_count,
                "last_used": tenant_info.last_used.isoformat(),
                "metrics": {
                    "avg_response_time_ms": metrics.avg_response_time_ms if metrics else 0,
                    "last_activity": metrics.last_activity.isoformat() if metrics else None
                }
            }

        except Exception as e:
            self._handle_connection_error(tenant_id, e)
            return {
                "status": "unhealthy",
                "tenant_id": tenant_id,
                "error": str(e)
            }

    def _health_check_all_tenants(self) -> Dict[str, Any]:
        """Health check for all tenants."""
        results = {
            "overall_status": "healthy",
            "total_tenants": len(self._tenant_info),
            "healthy_tenants": 0,
            "degraded_tenants": 0,
            "failed_tenants": 0,
            "tenant_details": {}
        }

        for tenant_id in self._tenant_info.keys():
            health = self._health_check_tenant(tenant_id)
            results["tenant_details"][tenant_id] = health

            if health["status"] == "healthy":
                results["healthy_tenants"] += 1
            elif health.get("connection_status") == "degraded":
                results["degraded_tenants"] += 1
            else:
                results["failed_tenants"] += 1

        # Determine overall status
        if results["failed_tenants"] > 0:
            results["overall_status"] = "degraded"
        if results["failed_tenants"] > results["healthy_tenants"]:
            results["overall_status"] = "failed"

        return results

    def _cleanup_tenant_pool(self, tenant_id: str) -> int:
        """Clean up idle connections for a tenant."""
        try:
            # This would implement database-specific cleanup
            # For now, just log the cleanup
            logger.info(f"Cleaning up idle connections for tenant: {tenant_id}")
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up tenant {tenant_id}: {e}")
            return 0


class PerformanceMonitor:
    """Performance monitoring for connection manager."""

    def __init__(self):
        self.metrics = {}
        self._lock = threading.Lock()

    def record_connection_time(self, tenant_id: str, time_ms: float):
        """Record connection acquisition time."""
        with self._lock:
            if tenant_id not in self.metrics:
                self.metrics[tenant_id] = {
                    "connection_times": [],
                    "error_count": 0,
                    "total_requests": 0
                }

            self.metrics[tenant_id]["connection_times"].append(time_ms)
            self.metrics[tenant_id]["total_requests"] += 1

            # Keep only last 100 measurements
            if len(self.metrics[tenant_id]["connection_times"]) > 100:
                self.metrics[tenant_id]["connection_times"].pop(0)

    def record_error(self, tenant_id: str):
        """Record connection error."""
        with self._lock:
            if tenant_id not in self.metrics:
                self.metrics[tenant_id] = {
                    "connection_times": [],
                    "error_count": 0,
                    "total_requests": 0
                }

            self.metrics[tenant_id]["error_count"] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for all tenants."""
        with self._lock:
            summary = {}

            for tenant_id, metrics in self.metrics.items():
                connection_times = metrics["connection_times"]

                if connection_times:
                    avg_time = sum(connection_times) / len(connection_times)
                    max_time = max(connection_times)
                    min_time = min(connection_times)
                else:
                    avg_time = max_time = min_time = 0

                error_rate = (
                    metrics["error_count"] / metrics["total_requests"] * 100
                    if metrics["total_requests"] > 0 else 0
                )

                summary[tenant_id] = {
                    "avg_connection_time_ms": round(avg_time, 2),
                    "max_connection_time_ms": round(max_time, 2),
                    "min_connection_time_ms": round(min_time, 2),
                    "error_rate_percent": round(error_rate, 2),
                    "total_requests": metrics["total_requests"],
                    "total_errors": metrics["error_count"]
                }

            return summary