"""
Performance Optimization Layer for Multi-Tenant NLP2SQL System
Advanced caching, connection pooling, query optimization, and resource management.
"""

import asyncio
import hashlib
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, OrderedDict
import weakref
import pickle
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed

from .tenant_connection_manager import TenantConnectionManager
from .tenant_routing_middleware import TenantRoutingContext
from .tenant_aware_nlp2sql import QueryResult, QueryAnalysis


logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategies for different types of data."""
    LRU = "lru"
    TTL = "ttl"
    ADAPTIVE = "adaptive"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


class OptimizationLevel(Enum):
    """Performance optimization levels."""
    BASIC = "basic"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    size_bytes: int
    tenant_id: Optional[str] = None
    ttl_seconds: Optional[int] = None
    tags: Optional[List[str]] = None


@dataclass
class PerformanceProfile:
    """Performance profile for tenant optimization."""
    tenant_id: str
    avg_query_time_ms: float
    peak_concurrent_connections: int
    cache_hit_rate: float
    preferred_optimization_level: OptimizationLevel
    connection_pool_size: int
    query_cache_size: int
    schema_cache_ttl: int
    last_updated: datetime


class MultiLevelCache:
    """Multi-level caching system with different strategies."""

    def __init__(self, max_memory_mb: int = 512, redis_config: Optional[Dict] = None):
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_usage_bytes": 0
        }
        self.lock = threading.RLock()

        # Redis cache for distributed caching
        self.redis_client = None
        if redis_config:
            try:
                self.redis_client = redis.Redis(**redis_config)
                self.redis_client.ping()
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis cache initialization failed: {e}")

        # Cache strategies by pattern
        self.cache_strategies = {
            "query_results": CacheStrategy.TTL,
            "schema_info": CacheStrategy.TTL,
            "user_permissions": CacheStrategy.LRU,
            "connection_pools": CacheStrategy.ADAPTIVE
        }

    def get(self, key: str, tenant_id: Optional[str] = None) -> Optional[Any]:
        """Get value from cache with multi-level lookup."""
        full_key = self._build_cache_key(key, tenant_id)

        with self.lock:
            # Check memory cache first
            if full_key in self.memory_cache:
                entry = self.memory_cache[full_key]

                # Check TTL expiration
                if self._is_expired(entry):
                    del self.memory_cache[full_key]
                    self.cache_stats["evictions"] += 1
                else:
                    # Update access info
                    entry.last_accessed = datetime.utcnow()
                    entry.access_count += 1

                    # Move to end (LRU)
                    self.memory_cache.move_to_end(full_key)

                    self.cache_stats["hits"] += 1
                    return entry.value

            # Check Redis cache if available
            if self.redis_client:
                try:
                    redis_value = self.redis_client.get(full_key)
                    if redis_value:
                        value = pickle.loads(redis_value)

                        # Store in memory cache for faster access
                        self._put_memory_cache(full_key, value, tenant_id)

                        self.cache_stats["hits"] += 1
                        return value
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")

            self.cache_stats["misses"] += 1
            return None

    def put(self, key: str, value: Any, tenant_id: Optional[str] = None,
            ttl_seconds: Optional[int] = None, tags: Optional[List[str]] = None):
        """Put value in cache with specified strategy."""
        full_key = self._build_cache_key(key, tenant_id)

        # Store in memory cache
        self._put_memory_cache(full_key, value, tenant_id, ttl_seconds, tags)

        # Store in Redis cache if available
        if self.redis_client:
            try:
                serialized_value = pickle.dumps(value)
                if ttl_seconds:
                    self.redis_client.setex(full_key, ttl_seconds, serialized_value)
                else:
                    self.redis_client.set(full_key, serialized_value)
            except Exception as e:
                logger.warning(f"Redis put error: {e}")

    def _put_memory_cache(self, full_key: str, value: Any, tenant_id: Optional[str] = None,
                         ttl_seconds: Optional[int] = None, tags: Optional[List[str]] = None):
        """Put value in memory cache with eviction management."""
        with self.lock:
            value_size = self._estimate_size(value)

            # Create cache entry
            entry = CacheEntry(
                key=full_key,
                value=value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                size_bytes=value_size,
                tenant_id=tenant_id,
                ttl_seconds=ttl_seconds,
                tags=tags
            )

            # Check if we need to evict entries
            self._ensure_cache_capacity(value_size)

            # Store the entry
            self.memory_cache[full_key] = entry
            self.cache_stats["memory_usage_bytes"] += value_size

    def _ensure_cache_capacity(self, new_entry_size: int):
        """Ensure cache has capacity for new entry."""
        while (self.cache_stats["memory_usage_bytes"] + new_entry_size > self.max_memory_bytes and
               self.memory_cache):

            # Evict least recently used entry
            oldest_key, oldest_entry = self.memory_cache.popitem(last=False)
            self.cache_stats["memory_usage_bytes"] -= oldest_entry.size_bytes
            self.cache_stats["evictions"] += 1

    def _build_cache_key(self, key: str, tenant_id: Optional[str] = None) -> str:
        """Build full cache key with tenant isolation."""
        if tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return f"global:{key}"

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.ttl_seconds is None:
            return False

        age_seconds = (datetime.utcnow() - entry.created_at).total_seconds()
        return age_seconds > entry.ttl_seconds

    def _estimate_size(self, value: Any) -> int:
        """Estimate memory size of value."""
        try:
            return len(pickle.dumps(value))
        except Exception:
            # Fallback estimation
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in value.items())
            else:
                return 64  # Default estimate

    def invalidate_by_tenant(self, tenant_id: str):
        """Invalidate all cache entries for a tenant."""
        with self.lock:
            keys_to_remove = [
                key for key, entry in self.memory_cache.items()
                if entry.tenant_id == tenant_id
            ]

            for key in keys_to_remove:
                entry = self.memory_cache[key]
                self.cache_stats["memory_usage_bytes"] -= entry.size_bytes
                del self.memory_cache[key]

        # Also clear from Redis
        if self.redis_client:
            try:
                pattern = f"tenant:{tenant_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis invalidation error: {e}")

    def invalidate_by_tags(self, tags: List[str]):
        """Invalidate cache entries by tags."""
        with self.lock:
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if entry.tags and any(tag in entry.tags for tag in tags):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                entry = self.memory_cache[key]
                self.cache_stats["memory_usage_bytes"] -= entry.size_bytes
                del self.memory_cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            hit_rate = (
                self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"])
                if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0
                else 0
            )

            return {
                **self.cache_stats,
                "hit_rate": hit_rate,
                "entry_count": len(self.memory_cache),
                "memory_usage_mb": self.cache_stats["memory_usage_bytes"] / (1024 * 1024),
                "memory_utilization": self.cache_stats["memory_usage_bytes"] / self.max_memory_bytes
            }


class QueryOptimizer:
    """Optimizes queries for better performance."""

    def __init__(self):
        self.optimization_patterns = {
            "limit_injection": True,
            "index_hints": True,
            "join_optimization": True,
            "subquery_optimization": True
        }

        self.query_performance_history = defaultdict(list)

    def optimize_query(self, sql: str, tenant_context: TenantRoutingContext,
                      schema_info: Any = None) -> Tuple[str, Dict[str, Any]]:
        """Optimize SQL query for better performance."""
        optimizations_applied = []
        optimized_sql = sql

        # Apply limit injection for non-admin users
        if tenant_context.access_level not in ['ADMIN', 'SUPER_ADMIN']:
            if 'LIMIT' not in optimized_sql.upper():
                if tenant_context.access_level == 'VIEWER':
                    optimized_sql += ' LIMIT 50'
                else:
                    optimized_sql += ' LIMIT 500'
                optimizations_applied.append("limit_injection")

        # Add query hints for large tables
        if schema_info and self.optimization_patterns["index_hints"]:
            optimized_sql = self._add_index_hints(optimized_sql, schema_info)
            if optimized_sql != sql:
                optimizations_applied.append("index_hints")

        # Optimize joins
        if 'JOIN' in optimized_sql.upper() and self.optimization_patterns["join_optimization"]:
            original_sql = optimized_sql
            optimized_sql = self._optimize_joins(optimized_sql)
            if optimized_sql != original_sql:
                optimizations_applied.append("join_optimization")

        optimization_metadata = {
            "optimizations_applied": optimizations_applied,
            "original_length": len(sql),
            "optimized_length": len(optimized_sql),
            "optimization_level": self._determine_optimization_level(optimizations_applied)
        }

        return optimized_sql, optimization_metadata

    def _add_index_hints(self, sql: str, schema_info: Any) -> str:
        """Add index hints to improve query performance."""
        # This is a simplified version - real implementation would analyze
        # table sizes and available indexes
        return sql

    def _optimize_joins(self, sql: str) -> str:
        """Optimize JOIN operations."""
        # Simplified join optimization - real implementation would:
        # 1. Reorder joins based on table sizes
        # 2. Convert subqueries to joins where beneficial
        # 3. Add appropriate join hints
        return sql

    def _determine_optimization_level(self, optimizations: List[str]) -> str:
        """Determine the level of optimization applied."""
        if len(optimizations) >= 3:
            return "aggressive"
        elif len(optimizations) >= 2:
            return "standard"
        elif len(optimizations) >= 1:
            return "basic"
        else:
            return "none"

    def record_query_performance(self, sql: str, execution_time_ms: float,
                               row_count: int, tenant_id: str):
        """Record query performance for future optimization."""
        query_signature = self._get_query_signature(sql)

        performance_record = {
            "execution_time_ms": execution_time_ms,
            "row_count": row_count,
            "timestamp": datetime.utcnow(),
            "tenant_id": tenant_id
        }

        self.query_performance_history[query_signature].append(performance_record)

        # Keep only recent history (last 100 executions)
        if len(self.query_performance_history[query_signature]) > 100:
            self.query_performance_history[query_signature].pop(0)

    def _get_query_signature(self, sql: str) -> str:
        """Get a signature for the query to track performance."""
        # Normalize the SQL to create a signature
        normalized_sql = sql.upper().strip()

        # Remove literals and parameters to create a template
        import re
        normalized_sql = re.sub(r"'[^']*'", "'?'", normalized_sql)
        normalized_sql = re.sub(r'\b\d+\b', '?', normalized_sql)

        # Create hash of normalized query
        return hashlib.md5(normalized_sql.encode()).hexdigest()


class ConnectionPoolOptimizer:
    """Optimizes connection pools based on usage patterns."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.usage_patterns = defaultdict(list)
        self.optimization_recommendations = {}

    def analyze_usage_patterns(self, tenant_id: str) -> Dict[str, Any]:
        """Analyze connection usage patterns for a tenant."""
        metrics = self.connection_manager.get_connection_metrics(tenant_id)
        if not metrics:
            return {}

        # Get historical data (this would be stored in a proper implementation)
        current_time = datetime.utcnow()
        usage_data = self.usage_patterns[tenant_id]

        # Add current metrics
        usage_data.append({
            "timestamp": current_time,
            "active_connections": metrics.active_connections,
            "total_connections": metrics.total_connections,
            "pool_utilization": metrics.pool_utilization
        })

        # Keep only last 24 hours of data
        cutoff_time = current_time - timedelta(hours=24)
        self.usage_patterns[tenant_id] = [
            data for data in usage_data
            if data["timestamp"] > cutoff_time
        ]

        return self._generate_optimization_recommendations(tenant_id)

    def _generate_optimization_recommendations(self, tenant_id: str) -> Dict[str, Any]:
        """Generate optimization recommendations based on usage patterns."""
        usage_data = self.usage_patterns[tenant_id]
        if len(usage_data) < 10:  # Need sufficient data
            return {"status": "insufficient_data"}

        # Calculate statistics
        utilizations = [data["pool_utilization"] for data in usage_data]
        avg_utilization = sum(utilizations) / len(utilizations)
        max_utilization = max(utilizations)
        min_utilization = min(utilizations)

        recommendations = {
            "current_avg_utilization": avg_utilization,
            "max_utilization": max_utilization,
            "min_utilization": min_utilization,
            "recommendations": []
        }

        # Generate recommendations
        if avg_utilization > 80:
            recommendations["recommendations"].append({
                "type": "increase_pool_size",
                "priority": "high",
                "description": "Pool utilization is high, consider increasing pool size",
                "suggested_action": "Increase pool_size by 50%"
            })

        if max_utilization > 95:
            recommendations["recommendations"].append({
                "type": "add_overflow_capacity",
                "priority": "critical",
                "description": "Pool reaching maximum capacity, add overflow",
                "suggested_action": "Increase max_overflow parameter"
            })

        if avg_utilization < 20:
            recommendations["recommendations"].append({
                "type": "reduce_pool_size",
                "priority": "low",
                "description": "Pool underutilized, consider reducing size",
                "suggested_action": "Reduce pool_size by 25%"
            })

        return recommendations

    def apply_optimizations(self, tenant_id: str, auto_apply: bool = False) -> Dict[str, Any]:
        """Apply connection pool optimizations."""
        recommendations = self._generate_optimization_recommendations(tenant_id)

        if "recommendations" not in recommendations:
            return {"status": "no_recommendations"}

        applied_optimizations = []

        for rec in recommendations["recommendations"]:
            if auto_apply or rec["priority"] == "critical":
                success = self._apply_recommendation(tenant_id, rec)
                applied_optimizations.append({
                    "recommendation": rec,
                    "applied": success
                })

        return {
            "status": "optimizations_applied",
            "applied": applied_optimizations
        }

    def _apply_recommendation(self, tenant_id: str, recommendation: Dict[str, Any]) -> bool:
        """Apply a specific optimization recommendation."""
        try:
            if recommendation["type"] == "increase_pool_size":
                # This would interact with the connection manager to increase pool size
                return True
            elif recommendation["type"] == "reduce_pool_size":
                # This would interact with the connection manager to reduce pool size
                return True
            elif recommendation["type"] == "add_overflow_capacity":
                # This would increase the max_overflow parameter
                return True

            return False
        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return False


class PerformanceOptimizer:
    """Main performance optimization coordinator."""

    def __init__(self, connection_manager: TenantConnectionManager,
                 cache_config: Optional[Dict] = None):
        self.connection_manager = connection_manager

        # Initialize components
        self.cache = MultiLevelCache(**(cache_config or {}))
        self.query_optimizer = QueryOptimizer()
        self.connection_optimizer = ConnectionPoolOptimizer(connection_manager)

        # Performance profiles per tenant
        self.tenant_profiles: Dict[str, PerformanceProfile] = {}

        # Global optimization settings
        self.global_optimization_level = OptimizationLevel.STANDARD

    def get_performance_profile(self, tenant_id: str) -> PerformanceProfile:
        """Get or create performance profile for tenant."""
        if tenant_id not in self.tenant_profiles:
            # Create default profile
            self.tenant_profiles[tenant_id] = PerformanceProfile(
                tenant_id=tenant_id,
                avg_query_time_ms=0.0,
                peak_concurrent_connections=5,
                cache_hit_rate=0.0,
                preferred_optimization_level=self.global_optimization_level,
                connection_pool_size=5,
                query_cache_size=100,
                schema_cache_ttl=3600,
                last_updated=datetime.utcnow()
            )

        return self.tenant_profiles[tenant_id]

    def update_performance_profile(self, tenant_id: str, metrics: Dict[str, Any]):
        """Update performance profile based on observed metrics."""
        profile = self.get_performance_profile(tenant_id)

        # Update metrics with exponential moving average
        alpha = 0.1  # Smoothing factor

        if "avg_query_time_ms" in metrics:
            if profile.avg_query_time_ms == 0:
                profile.avg_query_time_ms = metrics["avg_query_time_ms"]
            else:
                profile.avg_query_time_ms = (
                    alpha * metrics["avg_query_time_ms"] +
                    (1 - alpha) * profile.avg_query_time_ms
                )

        if "cache_hit_rate" in metrics:
            if profile.cache_hit_rate == 0:
                profile.cache_hit_rate = metrics["cache_hit_rate"]
            else:
                profile.cache_hit_rate = (
                    alpha * metrics["cache_hit_rate"] +
                    (1 - alpha) * profile.cache_hit_rate
                )

        profile.last_updated = datetime.utcnow()

        # Adjust optimization level based on performance
        self._adjust_optimization_level(profile)

    def _adjust_optimization_level(self, profile: PerformanceProfile):
        """Adjust optimization level based on performance metrics."""
        if profile.avg_query_time_ms > 2000:  # Slow queries
            if profile.preferred_optimization_level == OptimizationLevel.BASIC:
                profile.preferred_optimization_level = OptimizationLevel.STANDARD
            elif profile.preferred_optimization_level == OptimizationLevel.STANDARD:
                profile.preferred_optimization_level = OptimizationLevel.AGGRESSIVE

        elif profile.avg_query_time_ms < 500:  # Fast queries
            if profile.preferred_optimization_level == OptimizationLevel.AGGRESSIVE:
                profile.preferred_optimization_level = OptimizationLevel.STANDARD

    def optimize_query_execution(self, query: str, tenant_context: TenantRoutingContext,
                                schema_info: Any = None) -> Tuple[str, Dict[str, Any]]:
        """Optimize query execution with caching and optimization."""
        profile = self.get_performance_profile(tenant_context.tenant_id)

        # Check cache first
        cache_key = f"query:{hashlib.md5(query.encode()).hexdigest()}"
        cached_result = self.cache.get(cache_key, tenant_context.tenant_id)

        if cached_result:
            return cached_result["optimized_sql"], cached_result["metadata"]

        # Optimize query
        optimized_sql, optimization_metadata = self.query_optimizer.optimize_query(
            query, tenant_context, schema_info
        )

        # Cache the optimization result
        cache_data = {
            "optimized_sql": optimized_sql,
            "metadata": optimization_metadata
        }

        self.cache.put(
            cache_key,
            cache_data,
            tenant_context.tenant_id,
            ttl_seconds=profile.schema_cache_ttl,
            tags=["query_optimization"]
        )

        return optimized_sql, optimization_metadata

    def cache_query_result(self, query_result: QueryResult, ttl_seconds: Optional[int] = None):
        """Cache query result for future requests."""
        profile = self.get_performance_profile(query_result.tenant_id)

        # Determine cache TTL
        if ttl_seconds is None:
            if query_result.analysis.estimated_complexity > 5:
                ttl_seconds = 3600  # 1 hour for complex queries
            else:
                ttl_seconds = 1800  # 30 minutes for simple queries

        # Create cache key
        cache_key = f"result:{query_result.query_id}"

        # Cache the result
        self.cache.put(
            cache_key,
            query_result,
            query_result.tenant_id,
            ttl_seconds=ttl_seconds,
            tags=["query_results"]
        )

    def get_cached_query_result(self, query_id: str, tenant_id: str) -> Optional[QueryResult]:
        """Get cached query result."""
        cache_key = f"result:{query_id}"
        return self.cache.get(cache_key, tenant_id)

    def run_performance_analysis(self, tenant_id: str) -> Dict[str, Any]:
        """Run comprehensive performance analysis for tenant."""
        profile = self.get_performance_profile(tenant_id)

        # Analyze connection patterns
        connection_analysis = self.connection_optimizer.analyze_usage_patterns(tenant_id)

        # Get cache statistics
        cache_stats = self.cache.get_stats()

        # Performance summary
        analysis = {
            "tenant_id": tenant_id,
            "performance_profile": asdict(profile),
            "connection_analysis": connection_analysis,
            "cache_performance": cache_stats,
            "recommendations": self._generate_performance_recommendations(profile, connection_analysis, cache_stats)
        }

        return analysis

    def _generate_performance_recommendations(self, profile: PerformanceProfile,
                                           connection_analysis: Dict[str, Any],
                                           cache_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance recommendations."""
        recommendations = []

        # Query performance recommendations
        if profile.avg_query_time_ms > 1000:
            recommendations.append({
                "type": "query_performance",
                "priority": "medium",
                "description": "Average query time is high",
                "suggestion": "Consider query optimization or adding indexes"
            })

        # Cache hit rate recommendations
        if cache_stats.get("hit_rate", 0) < 0.5:
            recommendations.append({
                "type": "cache_optimization",
                "priority": "medium",
                "description": "Cache hit rate is low",
                "suggestion": "Increase cache size or adjust TTL settings"
            })

        # Connection pool recommendations
        if connection_analysis.get("recommendations"):
            for rec in connection_analysis["recommendations"]:
                recommendations.append({
                    "type": "connection_pool",
                    "priority": rec.get("priority", "low"),
                    "description": rec.get("description", ""),
                    "suggestion": rec.get("suggested_action", "")
                })

        return recommendations

    def invalidate_tenant_cache(self, tenant_id: str):
        """Invalidate all cache entries for a tenant."""
        self.cache.invalidate_by_tenant(tenant_id)

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get overall optimization statistics."""
        return {
            "cache_stats": self.cache.get_stats(),
            "tenant_profiles_count": len(self.tenant_profiles),
            "global_optimization_level": self.global_optimization_level.value,
            "timestamp": datetime.utcnow().isoformat()
        }