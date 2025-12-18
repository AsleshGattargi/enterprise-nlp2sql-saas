"""
Database Cloning Engine for Multi-Tenant NLP2SQL System
Creates isolated tenant databases from root image templates.
"""

import logging
import json
import uuid
import time
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

import mysql.connector
import psycopg2
import pymongo
import docker
from docker.models.containers import Container

from .root_image_manager import RootImageManager, DatabaseType
from .schema_version_manager import SchemaVersionManager
from .port_manager import PortManager
from .docker_manager import DockerManager
from .clone_verifier import CloneVerifier

logger = logging.getLogger(__name__)

class CloneStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CLEANING_UP = "cleaning_up"
    REMOVED = "removed"

@dataclass
class TenantClone:
    tenant_id: str
    clone_id: str
    database_type: DatabaseType
    root_version: str
    database_name: str
    status: CloneStatus
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    port: Optional[int] = None
    connection_params: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class CloneVerificationResult:
    is_verified: bool
    checks_passed: int
    total_checks: int
    isolation_verified: bool
    schema_integrity: bool
    connection_test: bool
    error_messages: List[str]

class DatabaseCloner:
    """
    Database Cloning Engine for creating isolated tenant databases
    from root image templates with full Docker integration.
    """

    def __init__(self,
                 root_image_manager: RootImageManager = None,
                 version_manager: SchemaVersionManager = None,
                 docker_manager: DockerManager = None,
                 port_manager: PortManager = None,
                 clone_verifier: CloneVerifier = None):
        """
        Initialize the Database Cloning Engine.

        Args:
            root_image_manager: Root image management system
            version_manager: Schema version management
            docker_manager: Docker container management
            port_manager: Port allocation management
            clone_verifier: Clone verification system
        """
        self.root_manager = root_image_manager or RootImageManager()
        self.version_manager = version_manager or SchemaVersionManager()
        self.docker_manager = docker_manager or DockerManager()
        self.port_manager = port_manager or PortManager()
        self.clone_verifier = clone_verifier or CloneVerifier()

        # Clone registry - in production, this should be persistent
        self.clone_registry: Dict[str, TenantClone] = {}

        # Load existing clones from persistence
        self._load_clone_registry()

        logger.info("DatabaseCloner initialized successfully")

    def clone_from_root(self, tenant_id: str, db_type: str, root_version: str = None,
                       custom_config: Dict[str, Any] = None) -> Tuple[bool, str, Optional[TenantClone]]:
        """
        Clone a tenant database from root image.

        Args:
            tenant_id: Unique tenant identifier
            db_type: Database type (mysql, postgresql, sqlite, mongodb)
            root_version: Root schema version to clone from (defaults to latest)
            custom_config: Optional custom configuration

        Returns:
            Tuple of (success: bool, message: str, clone: TenantClone)
        """
        clone_id = f"clone_{tenant_id}_{int(time.time())}"

        try:
            logger.info(f"Starting clone operation: {clone_id}")

            # Validate database type
            try:
                database_type = DatabaseType(db_type.lower())
            except ValueError:
                return False, f"Unsupported database type: {db_type}", None

            # Get root version (use latest if not specified)
            if not root_version:
                latest_version = self.root_manager.get_latest_version(database_type)
                if not latest_version:
                    return False, f"No root image found for {db_type}", None
                root_version = latest_version.version

            # Validate root version exists
            schema_content = self.root_manager.get_schema_content(database_type, root_version)
            if not schema_content:
                return False, f"Root schema not found: {db_type} {root_version}", None

            # Generate tenant database name
            database_name = f"tenant_{tenant_id}_db"

            # Create clone record
            clone = TenantClone(
                tenant_id=tenant_id,
                clone_id=clone_id,
                database_type=database_type,
                root_version=root_version,
                database_name=database_name,
                status=CloneStatus.PENDING,
                created_at=datetime.now()
            )

            self.clone_registry[clone_id] = clone

            # Update status to in progress
            clone.status = CloneStatus.IN_PROGRESS

            # Execute cloning based on database type
            if database_type == DatabaseType.SQLITE:
                success, message = self._clone_sqlite(clone, schema_content, custom_config)
            else:
                # For MySQL, PostgreSQL, MongoDB - create Docker container first
                success, message = self._clone_with_docker(clone, schema_content, custom_config)

            if success:
                clone.status = CloneStatus.COMPLETED
                clone.completed_at = datetime.now()

                # Save clone registry
                self._save_clone_registry()

                logger.info(f"Clone completed successfully: {clone_id}")
                return True, f"Clone created successfully: {clone_id}", clone
            else:
                clone.status = CloneStatus.FAILED
                clone.error_message = message

                # Cleanup failed clone
                self.cleanup_failed_clone(tenant_id)

                logger.error(f"Clone failed: {clone_id} - {message}")
                return False, message, clone

        except Exception as e:
            error_msg = f"Clone operation failed: {str(e)}"
            logger.error(error_msg)

            if clone_id in self.clone_registry:
                self.clone_registry[clone_id].status = CloneStatus.FAILED
                self.clone_registry[clone_id].error_message = error_msg
                self.cleanup_failed_clone(tenant_id)

            return False, error_msg, None

    def verify_clone_isolation(self, tenant_id: str) -> CloneVerificationResult:
        """
        Verify that a cloned tenant database is properly isolated.

        Args:
            tenant_id: Tenant identifier to verify

        Returns:
            CloneVerificationResult with detailed verification status
        """
        try:
            logger.info(f"Verifying clone isolation for tenant: {tenant_id}")

            # Find clone by tenant_id
            clone = self._get_clone_by_tenant_id(tenant_id)
            if not clone:
                return CloneVerificationResult(
                    is_verified=False,
                    checks_passed=0,
                    total_checks=0,
                    isolation_verified=False,
                    schema_integrity=False,
                    connection_test=False,
                    error_messages=[f"Clone not found for tenant: {tenant_id}"]
                )

            return self.clone_verifier.verify_clone(clone)

        except Exception as e:
            error_msg = f"Clone verification failed: {str(e)}"
            logger.error(error_msg)

            return CloneVerificationResult(
                is_verified=False,
                checks_passed=0,
                total_checks=0,
                isolation_verified=False,
                schema_integrity=False,
                connection_test=False,
                error_messages=[error_msg]
            )

    def cleanup_failed_clone(self, tenant_id: str) -> bool:
        """
        Cleanup resources from a failed clone operation.

        Args:
            tenant_id: Tenant identifier to cleanup

        Returns:
            True if cleanup was successful
        """
        try:
            logger.info(f"Cleaning up failed clone for tenant: {tenant_id}")

            clone = self._get_clone_by_tenant_id(tenant_id)
            if not clone:
                logger.warning(f"No clone found for tenant: {tenant_id}")
                return True

            clone.status = CloneStatus.CLEANING_UP

            cleanup_success = True

            # Stop and remove Docker container if exists
            if clone.container_id:
                try:
                    container_removed = self.docker_manager.remove_container(
                        clone.container_id, force=True
                    )
                    if not container_removed:
                        logger.warning(f"Failed to remove container: {clone.container_id}")
                        cleanup_success = False
                except Exception as e:
                    logger.error(f"Error removing container: {e}")
                    cleanup_success = False

            # Release allocated port
            if clone.port:
                try:
                    self.port_manager.release_port(clone.database_type, clone.port)
                except Exception as e:
                    logger.error(f"Error releasing port: {e}")
                    cleanup_success = False

            # Remove SQLite file if exists
            if clone.database_type == DatabaseType.SQLITE:
                try:
                    db_path = Path(f"databases/{clone.database_name}.db")
                    if db_path.exists():
                        db_path.unlink()
                        logger.info(f"Removed SQLite file: {db_path}")
                except Exception as e:
                    logger.error(f"Error removing SQLite file: {e}")
                    cleanup_success = False

            # Update clone status
            if cleanup_success:
                clone.status = CloneStatus.REMOVED
                logger.info(f"Cleanup completed for tenant: {tenant_id}")
            else:
                clone.status = CloneStatus.FAILED
                clone.error_message = "Cleanup partially failed"
                logger.warning(f"Cleanup partially failed for tenant: {tenant_id}")

            self._save_clone_registry()
            return cleanup_success

        except Exception as e:
            error_msg = f"Cleanup operation failed: {str(e)}"
            logger.error(error_msg)
            return False

    def list_tenant_clones(self, tenant_id: str = None) -> List[TenantClone]:
        """
        List clones for a specific tenant or all tenants.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            List of tenant clones
        """
        if tenant_id:
            return [clone for clone in self.clone_registry.values()
                   if clone.tenant_id == tenant_id]
        else:
            return list(self.clone_registry.values())

    def get_tenant_connection_params(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection parameters for a tenant's database.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Connection parameters or None if not found
        """
        clone = self._get_clone_by_tenant_id(tenant_id)
        if clone and clone.status == CloneStatus.COMPLETED:
            return clone.connection_params
        return None

    def stop_tenant_database(self, tenant_id: str) -> bool:
        """
        Stop a tenant's database container.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if stopped successfully
        """
        try:
            clone = self._get_clone_by_tenant_id(tenant_id)
            if not clone or not clone.container_id:
                return False

            return self.docker_manager.stop_container(clone.container_id)

        except Exception as e:
            logger.error(f"Error stopping tenant database: {e}")
            return False

    def start_tenant_database(self, tenant_id: str) -> bool:
        """
        Start a tenant's database container.

        Args:
            tenant_id: Tenant identifier

        Returns:
            True if started successfully
        """
        try:
            clone = self._get_clone_by_tenant_id(tenant_id)
            if not clone or not clone.container_id:
                return False

            return self.docker_manager.start_container(clone.container_id)

        except Exception as e:
            logger.error(f"Error starting tenant database: {e}")
            return False

    def remove_tenant_clone(self, tenant_id: str, force: bool = False) -> bool:
        """
        Completely remove a tenant clone and all associated resources.

        Args:
            tenant_id: Tenant identifier
            force: Force removal even if containers are running

        Returns:
            True if removal was successful
        """
        try:
            logger.info(f"Removing tenant clone: {tenant_id}")

            clone = self._get_clone_by_tenant_id(tenant_id)
            if not clone:
                logger.warning(f"Clone not found for tenant: {tenant_id}")
                return True

            # Stop container if running
            if clone.container_id:
                if not force:
                    # Check if container is running
                    if self.docker_manager.is_container_running(clone.container_id):
                        logger.error(f"Container is running. Use force=True to remove.")
                        return False

                # Stop and remove container
                self.docker_manager.stop_container(clone.container_id)
                self.docker_manager.remove_container(clone.container_id, force=True)

            # Release port
            if clone.port:
                self.port_manager.release_port(clone.database_type, clone.port)

            # Remove from registry
            clone_ids_to_remove = [cid for cid, c in self.clone_registry.items()
                                  if c.tenant_id == tenant_id]

            for clone_id in clone_ids_to_remove:
                del self.clone_registry[clone_id]

            self._save_clone_registry()

            logger.info(f"Successfully removed tenant clone: {tenant_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing tenant clone: {e}")
            return False

    # Private helper methods

    def _clone_sqlite(self, clone: TenantClone, schema_content: str,
                     custom_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Clone SQLite database from root image."""
        try:
            # Create databases directory if it doesn't exist
            databases_dir = Path("databases")
            databases_dir.mkdir(exist_ok=True)

            # Create SQLite database file
            db_path = databases_dir / f"{clone.database_name}.db"

            # Remove existing file if it exists
            if db_path.exists():
                db_path.unlink()

            # Create new database with schema
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Execute schema
            cursor.executescript(schema_content)
            conn.commit()
            conn.close()

            # Set connection parameters
            clone.connection_params = {
                'database': str(db_path),
                'isolation_level': None  # autocommit mode
            }

            logger.info(f"SQLite clone created: {db_path}")
            return True, f"SQLite database created at {db_path}"

        except Exception as e:
            error_msg = f"SQLite clone failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _clone_with_docker(self, clone: TenantClone, schema_content: str,
                          custom_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """Clone database with Docker container."""
        try:
            # Allocate port for the container
            port = self.port_manager.allocate_port(clone.database_type)
            if not port:
                return False, f"No available ports for {clone.database_type.value}"

            clone.port = port

            # Create and start Docker container
            container_config = self._build_container_config(clone, custom_config)

            container = self.docker_manager.create_container(
                image=container_config['image'],
                name=container_config['name'],
                ports=container_config['ports'],
                environment=container_config['environment'],
                volumes=container_config.get('volumes')
            )

            if not container:
                self.port_manager.release_port(clone.database_type, port)
                return False, "Failed to create Docker container"

            clone.container_id = container.id
            clone.container_name = container.name

            # Start container
            if not self.docker_manager.start_container(container.id):
                self.port_manager.release_port(clone.database_type, port)
                self.docker_manager.remove_container(container.id, force=True)
                return False, "Failed to start Docker container"

            # Wait for container to be ready
            if not self._wait_for_container_ready(clone):
                return False, "Container failed to become ready"

            # Create database and apply schema
            success, message = self._apply_schema_to_container(clone, schema_content)
            if not success:
                return False, f"Schema application failed: {message}"

            # Set connection parameters
            clone.connection_params = self._build_connection_params(clone)

            logger.info(f"Docker clone created: {clone.container_name}")
            return True, f"Container created: {clone.container_name}"

        except Exception as e:
            error_msg = f"Docker clone failed: {str(e)}"
            logger.error(error_msg)

            # Cleanup on failure
            if clone.port:
                self.port_manager.release_port(clone.database_type, clone.port)
            if clone.container_id:
                self.docker_manager.remove_container(clone.container_id, force=True)

            return False, error_msg

    def _build_container_config(self, clone: TenantClone,
                               custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build Docker container configuration."""
        config = {
            'name': f"{clone.database_type.value}_{clone.tenant_id}",
            'ports': {f'{self._get_default_port(clone.database_type)}/tcp': clone.port}
        }

        if clone.database_type == DatabaseType.MYSQL:
            config.update({
                'image': 'mysql:8.0',
                'environment': {
                    'MYSQL_ROOT_PASSWORD': f'{clone.tenant_id}_root_password',
                    'MYSQL_DATABASE': clone.database_name,
                    'MYSQL_USER': f'{clone.tenant_id}_user',
                    'MYSQL_PASSWORD': f'{clone.tenant_id}_password'
                }
            })
        elif clone.database_type == DatabaseType.POSTGRESQL:
            config.update({
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': clone.database_name,
                    'POSTGRES_USER': f'{clone.tenant_id}_user',
                    'POSTGRES_PASSWORD': f'{clone.tenant_id}_password'
                }
            })
        elif clone.database_type == DatabaseType.MONGODB:
            config.update({
                'image': 'mongo:7.0',
                'environment': {
                    'MONGO_INITDB_ROOT_USERNAME': f'{clone.tenant_id}_admin',
                    'MONGO_INITDB_ROOT_PASSWORD': f'{clone.tenant_id}_password',
                    'MONGO_INITDB_DATABASE': clone.database_name
                }
            })

        # Apply custom configuration if provided
        if custom_config:
            if 'environment' in custom_config:
                config['environment'].update(custom_config['environment'])
            if 'volumes' in custom_config:
                config['volumes'] = custom_config['volumes']

        return config

    def _get_default_port(self, db_type: DatabaseType) -> int:
        """Get default port for database type."""
        ports = {
            DatabaseType.MYSQL: 3306,
            DatabaseType.POSTGRESQL: 5432,
            DatabaseType.MONGODB: 27017
        }
        return ports.get(db_type, 5432)

    def _wait_for_container_ready(self, clone: TenantClone, timeout: int = 60) -> bool:
        """Wait for container to be ready for connections."""
        try:
            logger.info(f"Waiting for container to be ready: {clone.container_id}")

            start_time = time.time()

            while time.time() - start_time < timeout:
                try:
                    # Test connection based on database type
                    if clone.database_type == DatabaseType.MYSQL:
                        conn = mysql.connector.connect(
                            host='localhost',
                            port=clone.port,
                            user='root',
                            password=f'{clone.tenant_id}_root_password',
                            database=clone.database_name,
                            connection_timeout=5
                        )
                        conn.close()
                        return True

                    elif clone.database_type == DatabaseType.POSTGRESQL:
                        conn = psycopg2.connect(
                            host='localhost',
                            port=clone.port,
                            user=f'{clone.tenant_id}_user',
                            password=f'{clone.tenant_id}_password',
                            database=clone.database_name,
                            connect_timeout=5
                        )
                        conn.close()
                        return True

                    elif clone.database_type == DatabaseType.MONGODB:
                        client = pymongo.MongoClient(
                            f'mongodb://{clone.tenant_id}_admin:{clone.tenant_id}_password@localhost:{clone.port}/',
                            serverSelectionTimeoutMS=5000
                        )
                        client.server_info()
                        client.close()
                        return True

                except Exception:
                    # Connection failed, wait and retry
                    time.sleep(2)
                    continue

            logger.error(f"Container not ready within {timeout} seconds: {clone.container_id}")
            return False

        except Exception as e:
            logger.error(f"Error waiting for container: {e}")
            return False

    def _apply_schema_to_container(self, clone: TenantClone,
                                  schema_content: str) -> Tuple[bool, str]:
        """Apply root schema to the container database."""
        try:
            if clone.database_type == DatabaseType.MYSQL:
                return self._apply_mysql_schema(clone, schema_content)
            elif clone.database_type == DatabaseType.POSTGRESQL:
                return self._apply_postgresql_schema(clone, schema_content)
            elif clone.database_type == DatabaseType.MONGODB:
                return self._apply_mongodb_schema(clone, schema_content)
            else:
                return False, f"Unsupported database type: {clone.database_type}"

        except Exception as e:
            error_msg = f"Schema application failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def _apply_mysql_schema(self, clone: TenantClone, schema_content: str) -> Tuple[bool, str]:
        """Apply MySQL schema to container."""
        try:
            conn = mysql.connector.connect(
                host='localhost',
                port=clone.port,
                user='root',
                password=f'{clone.tenant_id}_root_password',
                database=clone.database_name
            )
            cursor = conn.cursor()

            # Execute schema statements
            statements = [stmt.strip() for stmt in schema_content.split(';') if stmt.strip()]
            for statement in statements:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)

            conn.commit()
            cursor.close()
            conn.close()

            return True, "MySQL schema applied successfully"

        except Exception as e:
            return False, f"MySQL schema application failed: {str(e)}"

    def _apply_postgresql_schema(self, clone: TenantClone, schema_content: str) -> Tuple[bool, str]:
        """Apply PostgreSQL schema to container."""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=clone.port,
                user=f'{clone.tenant_id}_user',
                password=f'{clone.tenant_id}_password',
                database=clone.database_name
            )
            cursor = conn.cursor()

            # Execute schema
            cursor.execute(schema_content)
            conn.commit()
            cursor.close()
            conn.close()

            return True, "PostgreSQL schema applied successfully"

        except Exception as e:
            return False, f"PostgreSQL schema application failed: {str(e)}"

    def _apply_mongodb_schema(self, clone: TenantClone, schema_content: str) -> Tuple[bool, str]:
        """Apply MongoDB schema to container."""
        try:
            schema_data = json.loads(schema_content)

            client = pymongo.MongoClient(
                f'mongodb://{clone.tenant_id}_admin:{clone.tenant_id}_password@localhost:{clone.port}/'
            )
            db = client[clone.database_name]

            # Create collections with validators and indexes
            collections = schema_data.get('collections', {})
            for collection_name, collection_config in collections.items():
                if 'validator' in collection_config:
                    db.create_collection(collection_name, validator=collection_config['validator'])
                else:
                    db.create_collection(collection_name)

                # Create indexes
                if 'indexes' in collection_config:
                    collection = db[collection_name]
                    for index_config in collection_config['indexes']:
                        collection.create_index(
                            list(index_config['key'].items()),
                            name=index_config['name'],
                            unique=index_config.get('unique', False)
                        )

            # Insert initial data if present
            if 'initial_data' in schema_data:
                for collection_name, documents in schema_data['initial_data'].items():
                    if documents:
                        db[collection_name].insert_many(documents)

            client.close()
            return True, "MongoDB schema applied successfully"

        except Exception as e:
            return False, f"MongoDB schema application failed: {str(e)}"

    def _build_connection_params(self, clone: TenantClone) -> Dict[str, Any]:
        """Build connection parameters for the clone."""
        if clone.database_type == DatabaseType.MYSQL:
            return {
                'host': 'localhost',
                'port': clone.port,
                'user': 'root',
                'password': f'{clone.tenant_id}_root_password',
                'database': clone.database_name
            }
        elif clone.database_type == DatabaseType.POSTGRESQL:
            return {
                'host': 'localhost',
                'port': clone.port,
                'user': f'{clone.tenant_id}_user',
                'password': f'{clone.tenant_id}_password',
                'database': clone.database_name
            }
        elif clone.database_type == DatabaseType.MONGODB:
            return {
                'uri': f'mongodb://{clone.tenant_id}_admin:{clone.tenant_id}_password@localhost:{clone.port}/',
                'database': clone.database_name
            }
        else:
            return {}

    def _get_clone_by_tenant_id(self, tenant_id: str) -> Optional[TenantClone]:
        """Get the most recent completed clone for a tenant."""
        tenant_clones = [clone for clone in self.clone_registry.values()
                        if clone.tenant_id == tenant_id and clone.status == CloneStatus.COMPLETED]

        if tenant_clones:
            # Return most recent clone
            return max(tenant_clones, key=lambda c: c.created_at)

        return None

    def _load_clone_registry(self):
        """Load clone registry from persistent storage."""
        try:
            registry_path = Path("clone_registry.json")
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    data = json.load(f)

                # Convert JSON data back to TenantClone objects
                for clone_id, clone_data in data.items():
                    clone_data['database_type'] = DatabaseType(clone_data['database_type'])
                    clone_data['status'] = CloneStatus(clone_data['status'])
                    clone_data['created_at'] = datetime.fromisoformat(clone_data['created_at'])

                    if clone_data.get('completed_at'):
                        clone_data['completed_at'] = datetime.fromisoformat(clone_data['completed_at'])

                    self.clone_registry[clone_id] = TenantClone(**clone_data)

        except Exception as e:
            logger.warning(f"Failed to load clone registry: {e}")

    def _save_clone_registry(self):
        """Save clone registry to persistent storage."""
        try:
            registry_path = Path("clone_registry.json")

            # Convert TenantClone objects to JSON-serializable data
            data = {}
            for clone_id, clone in self.clone_registry.items():
                clone_data = {
                    'tenant_id': clone.tenant_id,
                    'clone_id': clone.clone_id,
                    'database_type': clone.database_type.value,
                    'root_version': clone.root_version,
                    'database_name': clone.database_name,
                    'status': clone.status.value,
                    'container_id': clone.container_id,
                    'container_name': clone.container_name,
                    'port': clone.port,
                    'connection_params': clone.connection_params,
                    'created_at': clone.created_at.isoformat(),
                    'completed_at': clone.completed_at.isoformat() if clone.completed_at else None,
                    'error_message': clone.error_message
                }
                data[clone_id] = clone_data

            with open(registry_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save clone registry: {e}")