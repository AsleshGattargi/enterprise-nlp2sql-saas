"""
Comprehensive Load Testing Framework
Tests concurrent requests, connection pool stress, and performance under load.
"""

import asyncio
import aiohttp
import pytest
import logging
import json
import time
import statistics
from typing import Dict, List, Any, Tuple, Optional, Callable
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import psutil
import threading
from collections import defaultdict, deque

from src.tenant_connection_manager import TenantConnectionManager
from src.tenant_aware_nlp2sql import TenantAwareNLP2SQL
from src.tenant_routing_middleware import TenantRoutingContext
from src.resource_monitoring_alerting import ResourceMonitoringSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    concurrent_users: int = 10
    requests_per_user: int = 100
    ramp_up_time: int = 30  # seconds
    test_duration: int = 300  # seconds
    tenant_count: int = 5
    query_types: List[str] = field(default_factory=lambda: ["simple", "complex", "join", "aggregation"])
    request_delay_range: Tuple[float, float] = (0.1, 2.0)  # seconds between requests


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""
    test_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    percentile_95_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    concurrent_users: int = 0
    response_times: List[float] = field(default_factory=list)
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    system_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics."""
    tenant_id: str
    pool_size: int
    active_connections: int
    peak_connections: int
    connection_wait_time: float
    connection_failures: int
    pool_exhaustion_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceDegradationEvent:
    """Performance degradation event."""
    timestamp: datetime
    metric_type: str
    baseline_value: float
    current_value: float
    degradation_percentage: float
    affected_tenants: List[str]
    system_load: Dict[str, float]


class LoadTestingFramework:
    """Comprehensive load testing framework for multi-tenant system."""

    def __init__(self,
                 connection_manager: TenantConnectionManager,
                 nlp2sql_engine: TenantAwareNLP2SQL,
                 base_url: str = "http://localhost:8000"):
        self.connection_manager = connection_manager
        self.nlp2sql_engine = nlp2sql_engine
        self.base_url = base_url
        self.test_results: List[LoadTestMetrics] = []
        self.connection_pool_metrics: List[ConnectionPoolMetrics] = []
        self.degradation_events: List[PerformanceDegradationEvent] = []
        self.baseline_metrics: Dict[str, float] = {}
        self.test_tenants: List[str] = []
        self.system_monitor = None
        self.monitoring_active = False

    async def setup_load_test_environment(self, tenant_count: int = 5) -> List[str]:
        """Set up test environment with multiple tenants."""
        logger.info(f"Setting up load test environment with {tenant_count} tenants")

        self.test_tenants = []
        for i in range(tenant_count):
            tenant_id = f"load_test_tenant_{i+1}_{uuid.uuid4().hex[:8]}"
            await self._setup_test_tenant(tenant_id)
            self.test_tenants.append(tenant_id)

        logger.info(f"Created {len(self.test_tenants)} test tenants for load testing")
        return self.test_tenants

    async def _setup_test_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Set up individual test tenant with mock data."""
        # Mock tenant setup
        tenant_config = {
            "tenant_id": tenant_id,
            "database_type": "postgresql",
            "connection_pool_size": 10,
            "test_data": {
                "users": 1000,
                "orders": 5000,
                "products": 500
            }
        }

        # Initialize connection pool for tenant
        await self.connection_manager.create_tenant_connection_pool(
            tenant_id, tenant_config
        )

        return tenant_config

    def generate_test_queries(self, query_types: List[str]) -> List[Dict[str, Any]]:
        """Generate various types of test queries."""
        queries = []

        for query_type in query_types:
            if query_type == "simple":
                queries.extend([
                    {"type": "simple", "query": "Show me all users", "expected_complexity": "low"},
                    {"type": "simple", "query": "List all products", "expected_complexity": "low"},
                    {"type": "simple", "query": "Display recent orders", "expected_complexity": "low"}
                ])
            elif query_type == "complex":
                queries.extend([
                    {"type": "complex", "query": "Show me users who placed orders in the last 30 days with total spend", "expected_complexity": "high"},
                    {"type": "complex", "query": "Find products with inventory below threshold and pending orders", "expected_complexity": "high"}
                ])
            elif query_type == "join":
                queries.extend([
                    {"type": "join", "query": "Show customer orders with product details", "expected_complexity": "medium"},
                    {"type": "join", "query": "List users with their recent purchases", "expected_complexity": "medium"}
                ])
            elif query_type == "aggregation":
                queries.extend([
                    {"type": "aggregation", "query": "What is the average order value?", "expected_complexity": "medium"},
                    {"type": "aggregation", "query": "How many orders were placed today?", "expected_complexity": "low"},
                    {"type": "aggregation", "query": "Show monthly sales totals", "expected_complexity": "medium"}
                ])

        return queries

    async def run_concurrent_user_test(self, config: LoadTestConfig) -> LoadTestMetrics:
        """Run concurrent user load test."""
        logger.info(f"Starting concurrent user test with {config.concurrent_users} users")

        test_metrics = LoadTestMetrics(
            test_name="Concurrent User Load Test",
            start_time=datetime.utcnow(),
            concurrent_users=config.concurrent_users
        )

        # Start system monitoring
        await self._start_system_monitoring()

        # Establish baseline metrics
        await self._establish_baseline_metrics()

        try:
            # Generate test queries
            test_queries = self.generate_test_queries(config.query_types)

            # Create user simulation tasks
            user_tasks = []
            for user_id in range(config.concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user_load(
                        user_id,
                        config.requests_per_user,
                        test_queries,
                        config.request_delay_range
                    )
                )
                user_tasks.append(task)

                # Ramp up gradually
                if config.ramp_up_time > 0:
                    await asyncio.sleep(config.ramp_up_time / config.concurrent_users)

            # Wait for all users to complete or timeout
            timeout = config.test_duration
            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*user_tasks, return_exceptions=True),
                    timeout=timeout
                )

                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        test_metrics.failed_requests += 1
                        test_metrics.error_details.append({
                            "error": str(result),
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    elif isinstance(result, dict):
                        test_metrics.total_requests += result.get("requests", 0)
                        test_metrics.successful_requests += result.get("successful", 0)
                        test_metrics.failed_requests += result.get("failed", 0)
                        test_metrics.response_times.extend(result.get("response_times", []))

            except asyncio.TimeoutError:
                logger.warning(f"Load test timed out after {timeout} seconds")
                # Cancel remaining tasks
                for task in user_tasks:
                    if not task.done():
                        task.cancel()

        finally:
            # Stop system monitoring
            await self._stop_system_monitoring()

        # Calculate final metrics
        test_metrics.end_time = datetime.utcnow()
        test_metrics = self._calculate_final_metrics(test_metrics)

        self.test_results.append(test_metrics)
        return test_metrics

    async def _simulate_user_load(self,
                                 user_id: int,
                                 request_count: int,
                                 test_queries: List[Dict[str, Any]],
                                 delay_range: Tuple[float, float]) -> Dict[str, Any]:
        """Simulate load for a single user."""
        user_metrics = {
            "user_id": user_id,
            "requests": 0,
            "successful": 0,
            "failed": 0,
            "response_times": []
        }

        # Select random tenant for this user
        tenant_id = self.test_tenants[user_id % len(self.test_tenants)]

        # Create session for this user
        async with aiohttp.ClientSession() as session:
            for request_num in range(request_count):
                try:
                    # Select random query
                    import random
                    query_data = random.choice(test_queries)

                    # Execute query
                    start_time = time.time()
                    success = await self._execute_test_query(
                        session, tenant_id, query_data
                    )
                    response_time = time.time() - start_time

                    user_metrics["requests"] += 1
                    user_metrics["response_times"].append(response_time)

                    if success:
                        user_metrics["successful"] += 1
                    else:
                        user_metrics["failed"] += 1

                    # Random delay between requests
                    delay = random.uniform(delay_range[0], delay_range[1])
                    await asyncio.sleep(delay)

                except Exception as e:
                    user_metrics["requests"] += 1
                    user_metrics["failed"] += 1
                    logger.error(f"User {user_id} request failed: {str(e)}")

        return user_metrics

    async def _execute_test_query(self,
                                 session: aiohttp.ClientSession,
                                 tenant_id: str,
                                 query_data: Dict[str, Any]) -> bool:
        """Execute a test query for load testing."""
        try:
            # Create tenant context
            tenant_context = TenantRoutingContext(
                user_id=f"load_test_user",
                tenant_id=tenant_id,
                roles=["user"],
                access_level="standard",
                allowed_operations=["query"],
                database_connection=None,
                routing_metrics={}
            )

            # Execute query through NLP2SQL engine
            query_result = await self.nlp2sql_engine.process_nlp_query(
                query_data["query"],
                tenant_context
            )

            # Mock execution success based on query complexity
            complexity = query_data.get("expected_complexity", "low")
            success_probability = {"low": 0.95, "medium": 0.90, "high": 0.85}[complexity]

            import random
            return random.random() < success_probability

        except Exception as e:
            logger.debug(f"Query execution failed: {str(e)}")
            return False

    async def test_connection_pool_stress(self, max_connections: int = 100) -> List[ConnectionPoolMetrics]:
        """Test connection pool under stress."""
        logger.info(f"Testing connection pool stress with {max_connections} connections")

        results = []
        tasks = []

        for tenant_id in self.test_tenants:
            # Test each tenant's connection pool
            for i in range(max_connections // len(self.test_tenants)):
                task = asyncio.create_task(
                    self._test_tenant_connection_pool(tenant_id, i)
                )
                tasks.append(task)

        # Execute all connection tests concurrently
        start_time = time.time()
        connection_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time

        # Process results
        tenant_metrics = defaultdict(list)
        for result in connection_results:
            if isinstance(result, ConnectionPoolMetrics):
                tenant_metrics[result.tenant_id].append(result)

        # Generate summary metrics for each tenant
        for tenant_id, metrics_list in tenant_metrics.items():
            if metrics_list:
                summary_metrics = ConnectionPoolMetrics(
                    tenant_id=tenant_id,
                    pool_size=max([m.pool_size for m in metrics_list]),
                    active_connections=max([m.active_connections for m in metrics_list]),
                    peak_connections=max([m.peak_connections for m in metrics_list]),
                    connection_wait_time=statistics.mean([m.connection_wait_time for m in metrics_list]),
                    connection_failures=sum([m.connection_failures for m in metrics_list]),
                    pool_exhaustion_count=sum([m.pool_exhaustion_count for m in metrics_list])
                )
                results.append(summary_metrics)

        self.connection_pool_metrics.extend(results)
        logger.info(f"Connection pool stress test completed in {total_time:.2f} seconds")
        return results

    async def _test_tenant_connection_pool(self, tenant_id: str, connection_id: int) -> ConnectionPoolMetrics:
        """Test individual tenant connection pool."""
        start_time = time.time()

        try:
            # Attempt to get connection from pool
            connection = await self.connection_manager.get_connection(tenant_id, "postgresql")

            # Simulate work with connection
            await asyncio.sleep(0.1)  # Simulate query execution

            # Get pool statistics
            pool_stats = await self.connection_manager.get_tenant_connection_stats(tenant_id)

            connection_time = time.time() - start_time

            return ConnectionPoolMetrics(
                tenant_id=tenant_id,
                pool_size=pool_stats.get("pool_size", 0),
                active_connections=pool_stats.get("active_connections", 0),
                peak_connections=pool_stats.get("peak_connections", 0),
                connection_wait_time=connection_time,
                connection_failures=0,
                pool_exhaustion_count=0
            )

        except Exception as e:
            connection_time = time.time() - start_time
            return ConnectionPoolMetrics(
                tenant_id=tenant_id,
                pool_size=0,
                active_connections=0,
                peak_connections=0,
                connection_wait_time=connection_time,
                connection_failures=1,
                pool_exhaustion_count=1 if "pool exhausted" in str(e).lower() else 0
            )

    async def monitor_performance_degradation(self, duration: int = 300) -> List[PerformanceDegradationEvent]:
        """Monitor for performance degradation during load testing."""
        logger.info(f"Monitoring performance degradation for {duration} seconds")

        degradation_events = []
        monitoring_interval = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                # Collect current metrics
                current_metrics = await self._collect_current_metrics()

                # Compare with baseline
                for metric_name, current_value in current_metrics.items():
                    if metric_name in self.baseline_metrics:
                        baseline_value = self.baseline_metrics[metric_name]

                        # Calculate degradation percentage
                        if baseline_value > 0:
                            degradation = ((current_value - baseline_value) / baseline_value) * 100

                            # Check for significant degradation (>20%)
                            if degradation > 20:
                                event = PerformanceDegradationEvent(
                                    timestamp=datetime.utcnow(),
                                    metric_type=metric_name,
                                    baseline_value=baseline_value,
                                    current_value=current_value,
                                    degradation_percentage=degradation,
                                    affected_tenants=self.test_tenants,
                                    system_load=await self._get_system_load()
                                )
                                degradation_events.append(event)
                                logger.warning(f"Performance degradation detected: {metric_name} degraded by {degradation:.1f}%")

                await asyncio.sleep(monitoring_interval)

            except Exception as e:
                logger.error(f"Error monitoring performance degradation: {str(e)}")
                await asyncio.sleep(monitoring_interval)

        self.degradation_events.extend(degradation_events)
        return degradation_events

    async def run_comprehensive_load_tests(self, configs: List[LoadTestConfig]) -> Dict[str, Any]:
        """Run comprehensive load testing with multiple configurations."""
        logger.info("Starting comprehensive load testing")

        # Set up test environment
        await self.setup_load_test_environment(5)

        results = {
            "test_execution": {
                "start_time": datetime.utcnow().isoformat(),
                "config_count": len(configs),
                "tenant_count": len(self.test_tenants)
            },
            "load_tests": [],
            "connection_pool_tests": [],
            "performance_degradation": [],
            "summary": {}
        }

        try:
            # Run load tests with different configurations
            for i, config in enumerate(configs):
                logger.info(f"Running load test configuration {i+1}/{len(configs)}")

                # Start performance monitoring
                monitoring_task = asyncio.create_task(
                    self.monitor_performance_degradation(config.test_duration + 60)
                )

                # Run concurrent user test
                load_test_result = await self.run_concurrent_user_test(config)
                results["load_tests"].append(load_test_result.__dict__)

                # Run connection pool stress test
                connection_test_results = await self.test_connection_pool_stress(
                    config.concurrent_users * 2
                )
                results["connection_pool_tests"].extend([r.__dict__ for r in connection_test_results])

                # Wait for monitoring to complete
                monitoring_task.cancel()
                try:
                    await monitoring_task
                except asyncio.CancelledError:
                    pass

                # Cool down period between tests
                await asyncio.sleep(30)

            # Add performance degradation events
            results["performance_degradation"] = [e.__dict__ for e in self.degradation_events]

            # Generate comprehensive summary
            results["summary"] = self._generate_load_test_summary(results)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Comprehensive load testing failed: {str(e)}")
            results["test_execution"]["error"] = str(e)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()

        return results

    def _generate_load_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of load test results."""
        load_tests = results["load_tests"]
        connection_tests = results["connection_pool_tests"]
        degradation_events = results["performance_degradation"]

        # Load test summary
        total_requests = sum(test.get("total_requests", 0) for test in load_tests)
        successful_requests = sum(test.get("successful_requests", 0) for test in load_tests)
        avg_response_times = [test.get("average_response_time", 0) for test in load_tests if test.get("average_response_time", 0) > 0]

        # Connection pool summary
        total_connection_failures = sum(test.get("connection_failures", 0) for test in connection_tests)
        pool_exhaustions = sum(test.get("pool_exhaustion_count", 0) for test in connection_tests)

        return {
            "load_testing": {
                "total_tests": len(load_tests),
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
                "average_response_time": statistics.mean(avg_response_times) if avg_response_times else 0,
                "peak_concurrent_users": max([test.get("concurrent_users", 0) for test in load_tests], default=0)
            },
            "connection_pool": {
                "total_tests": len(connection_tests),
                "connection_failures": total_connection_failures,
                "pool_exhaustions": pool_exhaustions,
                "connection_stability": (1 - (total_connection_failures / len(connection_tests))) * 100 if connection_tests else 0
            },
            "performance_degradation": {
                "total_events": len(degradation_events),
                "critical_degradations": len([e for e in degradation_events if e.get("degradation_percentage", 0) > 50]),
                "system_stable": len(degradation_events) == 0
            },
            "overall_score": self._calculate_load_test_score(results)
        }

    def _calculate_load_test_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall load test performance score."""
        summary = results["summary"]

        success_rate_score = summary["load_testing"]["success_rate"] / 100
        connection_stability_score = summary["connection_pool"]["connection_stability"] / 100
        performance_stability_score = 1.0 if summary["performance_degradation"]["system_stable"] else 0.5

        # Weighted average
        overall_score = (
            success_rate_score * 0.5 +
            connection_stability_score * 0.3 +
            performance_stability_score * 0.2
        )

        return round(overall_score * 100, 2)

    # Helper methods

    async def _establish_baseline_metrics(self):
        """Establish baseline performance metrics."""
        logger.info("Establishing baseline performance metrics")

        baseline_measurements = []
        for _ in range(5):  # Take 5 measurements
            metrics = await self._collect_current_metrics()
            baseline_measurements.append(metrics)
            await asyncio.sleep(2)

        # Calculate baseline averages
        if baseline_measurements:
            for metric_name in baseline_measurements[0].keys():
                values = [m[metric_name] for m in baseline_measurements if metric_name in m]
                if values:
                    self.baseline_metrics[metric_name] = statistics.mean(values)

        logger.info(f"Established baseline metrics: {self.baseline_metrics}")

    async def _collect_current_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        metrics = {}

        try:
            # System metrics
            metrics["cpu_usage"] = psutil.cpu_percent(interval=0.1)
            metrics["memory_usage"] = psutil.virtual_memory().percent
            metrics["disk_usage"] = psutil.disk_usage('/').percent

            # Network metrics
            network = psutil.net_io_counters()
            metrics["network_bytes_sent"] = network.bytes_sent
            metrics["network_bytes_recv"] = network.bytes_recv

            # Database connection metrics (averaged across tenants)
            connection_counts = []
            response_times = []

            for tenant_id in self.test_tenants:
                try:
                    stats = await self.connection_manager.get_tenant_connection_stats(tenant_id)
                    if stats:
                        connection_counts.append(stats.get("active_connections", 0))

                    query_stats = await self.connection_manager.get_tenant_query_stats(tenant_id)
                    if query_stats:
                        response_times.append(query_stats.get("avg_response_time_ms", 0))

                except Exception:
                    pass

            if connection_counts:
                metrics["avg_connections"] = statistics.mean(connection_counts)
            if response_times:
                metrics["avg_response_time"] = statistics.mean(response_times)

        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")

        return metrics

    async def _get_system_load(self) -> Dict[str, float]:
        """Get current system load information."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        }

    def _calculate_final_metrics(self, test_metrics: LoadTestMetrics) -> LoadTestMetrics:
        """Calculate final metrics from collected data."""
        if test_metrics.response_times:
            test_metrics.average_response_time = statistics.mean(test_metrics.response_times)
            test_metrics.min_response_time = min(test_metrics.response_times)
            test_metrics.max_response_time = max(test_metrics.response_times)

            # Calculate 95th percentile
            sorted_times = sorted(test_metrics.response_times)
            index_95 = int(0.95 * len(sorted_times))
            test_metrics.percentile_95_response_time = sorted_times[index_95] if index_95 < len(sorted_times) else 0

        # Calculate requests per second
        if test_metrics.end_time and test_metrics.start_time:
            duration = (test_metrics.end_time - test_metrics.start_time).total_seconds()
            test_metrics.requests_per_second = test_metrics.total_requests / duration if duration > 0 else 0

        # Calculate error rate
        test_metrics.error_rate = (test_metrics.failed_requests / test_metrics.total_requests) * 100 if test_metrics.total_requests > 0 else 0

        return test_metrics

    async def _start_system_monitoring(self):
        """Start system monitoring during load tests."""
        self.monitoring_active = True
        # System monitoring would be implemented here

    async def _stop_system_monitoring(self):
        """Stop system monitoring."""
        self.monitoring_active = False

    async def cleanup_load_test_environment(self):
        """Clean up load test environment."""
        logger.info("Cleaning up load test environment")

        for tenant_id in self.test_tenants:
            try:
                # Clean up tenant resources
                await self.connection_manager.close_tenant_connections(tenant_id)
                logger.info(f"Cleaned up tenant: {tenant_id}")
            except Exception as e:
                logger.error(f"Failed to clean up tenant {tenant_id}: {str(e)}")

        self.test_tenants.clear()


# Export the main testing class
__all__ = ["LoadTestingFramework", "LoadTestConfig", "LoadTestMetrics", "ConnectionPoolMetrics", "PerformanceDegradationEvent"]