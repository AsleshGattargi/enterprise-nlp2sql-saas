"""
Error Handling and Monitoring System for Multi-Tenant NLP2SQL
Comprehensive error handling, monitoring, alerting, and failover mechanisms.
"""

import logging
import time
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import traceback
from contextlib import contextmanager

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

from .tenant_connection_manager import TenantConnectionManager, ConnectionStatus
from .tenant_routing_middleware import TenantRoutingContext


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    QUERY_EXECUTION = "query_execution"
    DATA_VALIDATION = "data_validation"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"


class AlertType(Enum):
    """Types of alerts."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    LOG = "log"


@dataclass
class ErrorEvent:
    """Represents an error event in the system."""
    error_id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    stack_trace: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    timestamp: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None
    occurrence_count: int = 1


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    metric_name: str
    value: float
    unit: str
    tenant_id: Optional[str]
    timestamp: datetime
    tags: Dict[str, str]


@dataclass
class HealthCheck:
    """Health check result."""
    component: str
    status: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: Optional[float] = None


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern implementation for tenant connections."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable - circuit breaker open"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time:
            return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
        return False

    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class TenantErrorHandler:
    """Handles tenant-specific errors with categorization and escalation."""

    def __init__(self):
        self.error_events: Dict[str, ErrorEvent] = {}
        self.error_patterns: Dict[str, List[ErrorEvent]] = defaultdict(list)
        self.tenant_circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Error thresholds for escalation
        self.escalation_thresholds = {
            ErrorSeverity.LOW: 10,
            ErrorSeverity.MEDIUM: 5,
            ErrorSeverity.HIGH: 2,
            ErrorSeverity.CRITICAL: 1
        }

        # Rate limiting for error notifications
        self.notification_cooldown = {}

    def handle_error(self, error: Exception, tenant_context: Optional[TenantRoutingContext] = None,
                    request: Optional[Request] = None, category: ErrorCategory = ErrorCategory.SYSTEM) -> ErrorEvent:
        """Handle and categorize an error event."""

        error_id = self._generate_error_id()
        severity = self._determine_severity(error, category)

        # Extract context information
        tenant_id = tenant_context.tenant_id if tenant_context else None
        user_id = tenant_context.user_id if tenant_context else None

        # Create error event
        error_event = ErrorEvent(
            error_id=error_id,
            tenant_id=tenant_id,
            user_id=user_id,
            category=category,
            severity=severity,
            message=str(error),
            details=self._extract_error_details(error, tenant_context, request),
            stack_trace=traceback.format_exc(),
            request_path=request.url.path if request else None,
            request_method=request.method if request else None,
            timestamp=datetime.utcnow()
        )

        # Store error event
        self.error_events[error_id] = error_event

        # Pattern detection
        self._detect_error_patterns(error_event)

        # Check for escalation
        self._check_escalation(error_event)

        # Update circuit breaker if tenant-specific
        if tenant_id:
            self._update_circuit_breaker(tenant_id, error_event)

        # Log error appropriately
        self._log_error(error_event)

        return error_event

    def _generate_error_id(self) -> str:
        """Generate unique error ID."""
        import uuid
        return f"err_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity based on error type and category."""

        # Critical errors
        if isinstance(error, (SystemExit, KeyboardInterrupt)):
            return ErrorSeverity.CRITICAL

        if category == ErrorCategory.SECURITY:
            return ErrorSeverity.CRITICAL

        # High severity errors
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH

        if category in [ErrorCategory.CONNECTION, ErrorCategory.AUTHENTICATION]:
            return ErrorSeverity.HIGH

        # Medium severity errors
        if isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM

        if category in [ErrorCategory.QUERY_EXECUTION, ErrorCategory.DATA_VALIDATION]:
            return ErrorSeverity.MEDIUM

        # Default to low severity
        return ErrorSeverity.LOW

    def _extract_error_details(self, error: Exception, tenant_context: Optional[TenantRoutingContext],
                             request: Optional[Request]) -> Dict[str, Any]:
        """Extract detailed error information."""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add tenant context details
        if tenant_context:
            details.update({
                "tenant_id": tenant_context.tenant_id,
                "user_id": tenant_context.user_id,
                "access_level": tenant_context.access_level,
                "session_id": tenant_context.session_id
            })

        # Add request details
        if request:
            details.update({
                "request_url": str(request.url),
                "request_method": request.method,
                "user_agent": request.headers.get("user-agent"),
                "client_ip": request.client.host if request.client else None,
                "request_headers": dict(request.headers)
            })

        # Add system information
        details.update({
            "system_timestamp": datetime.utcnow().isoformat(),
            "thread_id": threading.get_ident(),
            "process_id": os.getpid() if 'os' in globals() else None
        })

        return details

    def _detect_error_patterns(self, error_event: ErrorEvent):
        """Detect patterns in error occurrences."""
        pattern_key = f"{error_event.category.value}:{error_event.message}"
        self.error_patterns[pattern_key].append(error_event)

        # Keep only recent errors for pattern detection (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        self.error_patterns[pattern_key] = [
            event for event in self.error_patterns[pattern_key]
            if event.timestamp > cutoff_time
        ]

        # Check for pattern-based escalation
        recent_errors = len(self.error_patterns[pattern_key])
        if recent_errors >= 5:  # 5 similar errors in an hour
            logger.warning(f"Error pattern detected: {pattern_key} - {recent_errors} occurrences")

    def _check_escalation(self, error_event: ErrorEvent):
        """Check if error should be escalated."""
        threshold = self.escalation_thresholds.get(error_event.severity, 10)

        # Count recent errors of this severity for this tenant
        cutoff_time = datetime.utcnow() - timedelta(minutes=15)
        recent_errors = [
            event for event in self.error_events.values()
            if (event.tenant_id == error_event.tenant_id and
                event.severity == error_event.severity and
                event.timestamp > cutoff_time)
        ]

        if len(recent_errors) >= threshold:
            self._escalate_error(error_event, len(recent_errors))

    def _escalate_error(self, error_event: ErrorEvent, occurrence_count: int):
        """Escalate error to appropriate channels."""
        escalation_key = f"{error_event.tenant_id}:{error_event.severity.value}"

        # Check notification cooldown
        if escalation_key in self.notification_cooldown:
            last_notification = self.notification_cooldown[escalation_key]
            if (datetime.utcnow() - last_notification).seconds < 300:  # 5 minutes cooldown
                return

        # Send escalation notification
        self._send_escalation_notification(error_event, occurrence_count)
        self.notification_cooldown[escalation_key] = datetime.utcnow()

    def _update_circuit_breaker(self, tenant_id: str, error_event: ErrorEvent):
        """Update circuit breaker state for tenant."""
        if tenant_id not in self.tenant_circuit_breakers:
            self.tenant_circuit_breakers[tenant_id] = CircuitBreaker()

        circuit_breaker = self.tenant_circuit_breakers[tenant_id]

        if error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            circuit_breaker._on_failure()

    def get_circuit_breaker(self, tenant_id: str) -> CircuitBreaker:
        """Get circuit breaker for tenant."""
        if tenant_id not in self.tenant_circuit_breakers:
            self.tenant_circuit_breakers[tenant_id] = CircuitBreaker()
        return self.tenant_circuit_breakers[tenant_id]

    def _log_error(self, error_event: ErrorEvent):
        """Log error with appropriate level."""
        log_message = f"[{error_event.error_id}] {error_event.category.value}: {error_event.message}"

        if error_event.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error_event": asdict(error_event)})
        elif error_event.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error_event": asdict(error_event)})
        elif error_event.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error_event": asdict(error_event)})
        else:
            logger.info(log_message, extra={"error_event": asdict(error_event)})

    def _send_escalation_notification(self, error_event: ErrorEvent, occurrence_count: int):
        """Send escalation notification."""
        # This would integrate with actual notification systems
        logger.critical(
            f"ERROR ESCALATION: {error_event.severity.value} error occurred {occurrence_count} times "
            f"for tenant {error_event.tenant_id}: {error_event.message}"
        )

    def get_error_summary(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get error summary statistics."""
        relevant_errors = [
            event for event in self.error_events.values()
            if tenant_id is None or event.tenant_id == tenant_id
        ]

        summary = {
            "total_errors": len(relevant_errors),
            "by_severity": {},
            "by_category": {},
            "recent_errors": [],
            "top_patterns": []
        }

        # Count by severity
        for severity in ErrorSeverity:
            count = len([e for e in relevant_errors if e.severity == severity])
            summary["by_severity"][severity.value] = count

        # Count by category
        for category in ErrorCategory:
            count = len([e for e in relevant_errors if e.category == category])
            summary["by_category"][category.value] = count

        # Recent errors (last hour)
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        recent = [e for e in relevant_errors if e.timestamp > cutoff_time]
        summary["recent_errors"] = [
            {
                "error_id": e.error_id,
                "severity": e.severity.value,
                "category": e.category.value,
                "message": e.message,
                "timestamp": e.timestamp.isoformat()
            }
            for e in sorted(recent, key=lambda x: x.timestamp, reverse=True)[:10]
        ]

        return summary


class PerformanceMonitor:
    """Monitors system performance and detects anomalies."""

    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.thresholds = {
            "response_time_ms": 2000,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
            "connection_pool_utilization": 90,
            "error_rate_percent": 5
        }

    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric."""
        metric_key = f"{metric.metric_name}:{metric.tenant_id or 'global'}"
        self.metrics[metric_key].append(metric)

        # Check for threshold violations
        self._check_thresholds(metric)

    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric violates thresholds."""
        threshold = self.thresholds.get(metric.metric_name)
        if threshold and metric.value > threshold:
            logger.warning(
                f"Performance threshold exceeded: {metric.metric_name} = {metric.value} "
                f"(threshold: {threshold}) for tenant {metric.tenant_id or 'global'}"
            )

    def get_performance_summary(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get performance summary."""
        relevant_metrics = {}

        for key, metric_list in self.metrics.items():
            if tenant_id is None or f":{tenant_id}" in key or ":global" in key:
                if metric_list:
                    latest_metric = metric_list[-1]
                    metric_name = key.split(":")[0]
                    relevant_metrics[metric_name] = {
                        "current_value": latest_metric.value,
                        "unit": latest_metric.unit,
                        "timestamp": latest_metric.timestamp.isoformat(),
                        "trend": self._calculate_trend(metric_list)
                    }

        return {
            "metrics": relevant_metrics,
            "thresholds": self.thresholds,
            "summary_timestamp": datetime.utcnow().isoformat()
        }

    def _calculate_trend(self, metric_list: deque) -> str:
        """Calculate trend direction for metrics."""
        if len(metric_list) < 2:
            return "stable"

        recent_avg = sum(m.value for m in list(metric_list)[-5:]) / min(5, len(metric_list))
        older_avg = sum(m.value for m in list(metric_list)[-10:-5]) / min(5, max(0, len(metric_list) - 5))

        if older_avg == 0:
            return "stable"

        change_percent = ((recent_avg - older_avg) / older_avg) * 100

        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"


class HealthMonitor:
    """Monitors system health and performs health checks."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_check_interval = 60  # seconds

    async def perform_health_checks(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive health checks."""
        health_results = {}

        # Check connection manager health
        health_results["connection_manager"] = await self._check_connection_manager()

        # Check individual tenant health
        tenant_health = await self._check_tenant_health()
        health_results.update(tenant_health)

        # Store results
        self.health_checks.update(health_results)

        return health_results

    async def _check_connection_manager(self) -> HealthCheck:
        """Check connection manager health."""
        start_time = time.time()

        try:
            health_info = self.connection_manager.health_check()
            response_time = (time.time() - start_time) * 1000

            status = "healthy" if health_info.get("overall_status") == "healthy" else "unhealthy"

            return HealthCheck(
                component="connection_manager",
                status=status,
                message="Connection manager operational",
                details=health_info,
                timestamp=datetime.utcnow(),
                response_time_ms=response_time
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            return HealthCheck(
                component="connection_manager",
                status="unhealthy",
                message=f"Connection manager error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                response_time_ms=response_time
            )

    async def _check_tenant_health(self) -> Dict[str, HealthCheck]:
        """Check health of individual tenants."""
        tenant_health = {}

        # Get list of active tenants
        all_metrics = self.connection_manager.get_all_metrics()

        for tenant_id in all_metrics.keys():
            start_time = time.time()

            try:
                health_info = self.connection_manager.health_check(tenant_id)
                response_time = (time.time() - start_time) * 1000

                status = "healthy" if health_info.get("status") == "healthy" else "unhealthy"

                tenant_health[f"tenant_{tenant_id}"] = HealthCheck(
                    component=f"tenant_{tenant_id}",
                    status=status,
                    message=f"Tenant {tenant_id} operational",
                    details=health_info,
                    timestamp=datetime.utcnow(),
                    response_time_ms=response_time
                )

            except Exception as e:
                response_time = (time.time() - start_time) * 1000

                tenant_health[f"tenant_{tenant_id}"] = HealthCheck(
                    component=f"tenant_{tenant_id}",
                    status="unhealthy",
                    message=f"Tenant {tenant_id} error: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.utcnow(),
                    response_time_ms=response_time
                )

        return tenant_health

    def get_overall_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        recent_checks = {
            k: v for k, v in self.health_checks.items()
            if (datetime.utcnow() - v.timestamp).seconds < 300  # Last 5 minutes
        }

        total_checks = len(recent_checks)
        healthy_checks = len([c for c in recent_checks.values() if c.status == "healthy"])

        overall_status = "healthy"
        if total_checks == 0:
            overall_status = "unknown"
        elif healthy_checks < total_checks * 0.8:  # Less than 80% healthy
            overall_status = "degraded"
        elif healthy_checks == 0:
            overall_status = "unhealthy"

        return {
            "overall_status": overall_status,
            "total_components": total_checks,
            "healthy_components": healthy_checks,
            "unhealthy_components": total_checks - healthy_checks,
            "health_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0,
            "last_check": datetime.utcnow().isoformat(),
            "component_details": [
                {
                    "component": check.component,
                    "status": check.status,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "timestamp": check.timestamp.isoformat()
                }
                for check in recent_checks.values()
            ]
        }


class MonitoringSystem:
    """Comprehensive monitoring system integrating all monitoring components."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.error_handler = TenantErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        self.health_monitor = HealthMonitor(connection_manager)

        # Background monitoring tasks
        self.monitoring_tasks = []
        self.monitoring_active = False

    async def start_monitoring(self):
        """Start background monitoring tasks."""
        self.monitoring_active = True

        # Start health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self.monitoring_tasks.append(health_task)

        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.monitoring_tasks.append(cleanup_task)

        logger.info("Monitoring system started")

    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self.monitoring_active = False

        for task in self.monitoring_tasks:
            task.cancel()

        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        self.monitoring_tasks.clear()

        logger.info("Monitoring system stopped")

    async def _health_check_loop(self):
        """Background health check loop."""
        while self.monitoring_active:
            try:
                await self.health_monitor.perform_health_checks()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.monitoring_active:
            try:
                # Clean up old error events (keep last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                old_events = [
                    error_id for error_id, event in self.error_handler.error_events.items()
                    if event.timestamp < cutoff_time
                ]

                for error_id in old_events:
                    del self.error_handler.error_events[error_id]

                if old_events:
                    logger.info(f"Cleaned up {len(old_events)} old error events")

                await asyncio.sleep(3600)  # Clean up every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": self.health_monitor.get_overall_health_status(),
            "performance": self.performance_monitor.get_performance_summary(),
            "errors": self.error_handler.get_error_summary(),
            "monitoring_active": self.monitoring_active
        }

    @contextmanager
    def error_context(self, tenant_context: Optional[TenantRoutingContext] = None,
                     request: Optional[Request] = None,
                     category: ErrorCategory = ErrorCategory.SYSTEM):
        """Context manager for automatic error handling."""
        try:
            yield
        except Exception as e:
            error_event = self.error_handler.handle_error(e, tenant_context, request, category)
            # Re-raise the exception after handling
            raise


# Global monitoring instance (to be initialized in main.py)
monitoring_system: Optional[MonitoringSystem] = None


def setup_monitoring_system(connection_manager: TenantConnectionManager) -> MonitoringSystem:
    """Setup and return global monitoring system."""
    global monitoring_system
    monitoring_system = MonitoringSystem(connection_manager)
    return monitoring_system


def get_monitoring_system() -> Optional[MonitoringSystem]:
    """Get global monitoring system instance."""
    return monitoring_system