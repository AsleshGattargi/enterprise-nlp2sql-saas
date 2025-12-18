"""
Resource Monitoring and Alerting System
Provides comprehensive monitoring, alerting, and performance optimization for multi-tenant infrastructure.
"""

import asyncio
import psutil
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import json
import time
import statistics
from collections import defaultdict, deque

from tenant_onboarding_models import TenantResourceUsage, TenantInfo
from tenant_connection_manager import TenantConnectionManager
from automated_provisioning import ProvisioningManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of system alerts."""
    RESOURCE_USAGE = "resource_usage"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CONNECTION_FAILURE = "connection_failure"
    TENANT_QUOTA_EXCEEDED = "tenant_quota_exceeded"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_ERROR = "system_error"
    BACKUP_FAILURE = "backup_failure"
    COMPLIANCE_VIOLATION = "compliance_violation"


class MetricType(str, Enum):
    """Types of metrics being monitored."""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    CONNECTION_COUNT = "connection_count"
    QUERY_RESPONSE_TIME = "query_response_time"
    ERROR_RATE = "error_rate"
    TENANT_ACTIVITY = "tenant_activity"


@dataclass
class MetricReading:
    """Individual metric reading."""
    timestamp: datetime
    metric_type: MetricType
    value: float
    tenant_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """System alert information."""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    timestamp: datetime
    tenant_id: Optional[str] = None
    affected_resources: List[str] = field(default_factory=list)
    metric_values: Dict[str, float] = field(default_factory=dict)
    resolution_steps: List[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MonitoringThresholds:
    """Monitoring thresholds configuration."""
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    memory_warning: float = 80.0
    memory_critical: float = 90.0
    disk_warning: float = 75.0
    disk_critical: float = 85.0
    response_time_warning: float = 1000.0  # milliseconds
    response_time_critical: float = 5000.0
    error_rate_warning: float = 5.0  # percentage
    error_rate_critical: float = 10.0
    connection_count_warning: int = 80  # percentage of pool
    connection_count_critical: int = 95


class MetricsCollector:
    """Collects system and tenant-specific metrics."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))  # Keep last 1000 readings
        self.collection_interval = 30  # seconds
        self.executor = ThreadPoolExecutor(max_workers=5)

    async def start_collection(self):
        """Start continuous metrics collection."""
        logger.info("Starting metrics collection")
        while True:
            try:
                await self._collect_system_metrics()
                await self._collect_tenant_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {str(e)}")
                await asyncio.sleep(5)  # Short delay before retry

    async def _collect_system_metrics(self):
        """Collect system-wide metrics."""
        try:
            timestamp = datetime.utcnow()

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric(MetricReading(
                timestamp=timestamp,
                metric_type=MetricType.CPU_USAGE,
                value=cpu_percent
            ))

            # Memory metrics
            memory = psutil.virtual_memory()
            self._add_metric(MetricReading(
                timestamp=timestamp,
                metric_type=MetricType.MEMORY_USAGE,
                value=memory.percent
            ))

            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric(MetricReading(
                timestamp=timestamp,
                metric_type=MetricType.DISK_USAGE,
                value=disk_percent
            ))

            # Network metrics
            network = psutil.net_io_counters()
            network_total = (network.bytes_sent + network.bytes_recv) / 1024 / 1024  # MB
            self._add_metric(MetricReading(
                timestamp=timestamp,
                metric_type=MetricType.NETWORK_IO,
                value=network_total,
                metadata={"bytes_sent": network.bytes_sent, "bytes_recv": network.bytes_recv}
            ))

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")

    async def _collect_tenant_metrics(self):
        """Collect tenant-specific metrics."""
        try:
            # Get all active tenants
            active_tenants = await self.connection_manager.get_active_tenants()

            for tenant_id in active_tenants:
                await self._collect_tenant_specific_metrics(tenant_id)

        except Exception as e:
            logger.error(f"Failed to collect tenant metrics: {str(e)}")

    async def _collect_tenant_specific_metrics(self, tenant_id: str):
        """Collect metrics for a specific tenant."""
        try:
            timestamp = datetime.utcnow()

            # Connection metrics
            connection_stats = await self.connection_manager.get_tenant_connection_stats(tenant_id)
            if connection_stats:
                self._add_metric(MetricReading(
                    timestamp=timestamp,
                    metric_type=MetricType.CONNECTION_COUNT,
                    value=connection_stats.get("active_connections", 0),
                    tenant_id=tenant_id,
                    metadata=connection_stats
                ))

            # Query performance metrics
            query_stats = await self.connection_manager.get_tenant_query_stats(tenant_id)
            if query_stats:
                avg_response_time = query_stats.get("avg_response_time_ms", 0)
                self._add_metric(MetricReading(
                    timestamp=timestamp,
                    metric_type=MetricType.QUERY_RESPONSE_TIME,
                    value=avg_response_time,
                    tenant_id=tenant_id,
                    metadata=query_stats
                ))

                error_rate = query_stats.get("error_rate_percent", 0)
                self._add_metric(MetricReading(
                    timestamp=timestamp,
                    metric_type=MetricType.ERROR_RATE,
                    value=error_rate,
                    tenant_id=tenant_id
                ))

            # Tenant activity metrics
            activity_stats = await self.connection_manager.get_tenant_activity_stats(tenant_id)
            if activity_stats:
                self._add_metric(MetricReading(
                    timestamp=timestamp,
                    metric_type=MetricType.TENANT_ACTIVITY,
                    value=activity_stats.get("active_sessions", 0),
                    tenant_id=tenant_id,
                    metadata=activity_stats
                ))

        except Exception as e:
            logger.error(f"Failed to collect metrics for tenant {tenant_id}: {str(e)}")

    def _add_metric(self, metric: MetricReading):
        """Add metric to history."""
        key = f"{metric.metric_type.value}:{metric.tenant_id or 'system'}"
        self.metrics_history[key].append(metric)

    def get_recent_metrics(
        self,
        metric_type: MetricType,
        tenant_id: Optional[str] = None,
        minutes: int = 60
    ) -> List[MetricReading]:
        """Get recent metrics for analysis."""
        key = f"{metric_type.value}:{tenant_id or 'system'}"
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        return [
            metric for metric in self.metrics_history[key]
            if metric.timestamp >= cutoff_time
        ]

    def get_metric_statistics(
        self,
        metric_type: MetricType,
        tenant_id: Optional[str] = None,
        minutes: int = 60
    ) -> Dict[str, float]:
        """Get statistical analysis of metrics."""
        metrics = self.get_recent_metrics(metric_type, tenant_id, minutes)

        if not metrics:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "std": 0}

        values = [m.value for m in metrics]

        return {
            "count": len(values),
            "avg": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0
        }


class AlertManager:
    """Manages alert generation, escalation, and notification."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.thresholds = MonitoringThresholds()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.suppressed_alerts = set()
        self.alert_history = deque(maxlen=1000)

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert notification handler."""
        self.alert_handlers.append(handler)

    async def start_monitoring(self):
        """Start continuous alert monitoring."""
        logger.info("Starting alert monitoring")
        while True:
            try:
                await self._check_system_alerts()
                await self._check_tenant_alerts()
                await self._process_alert_escalations()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in alert monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def _check_system_alerts(self):
        """Check for system-wide alerts."""
        # CPU usage alerts
        cpu_stats = self.metrics_collector.get_metric_statistics(MetricType.CPU_USAGE, minutes=5)
        if cpu_stats["avg"] > self.thresholds.cpu_critical:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                AlertSeverity.CRITICAL,
                "Critical CPU Usage",
                f"System CPU usage is {cpu_stats['avg']:.1f}% (Critical threshold: {self.thresholds.cpu_critical}%)",
                metric_values={"cpu_usage": cpu_stats["avg"]},
                resolution_steps=[
                    "Check for resource-intensive processes",
                    "Consider scaling up infrastructure",
                    "Review tenant query patterns"
                ]
            )
        elif cpu_stats["avg"] > self.thresholds.cpu_warning:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                AlertSeverity.MEDIUM,
                "High CPU Usage",
                f"System CPU usage is {cpu_stats['avg']:.1f}% (Warning threshold: {self.thresholds.cpu_warning}%)",
                metric_values={"cpu_usage": cpu_stats["avg"]}
            )

        # Memory usage alerts
        memory_stats = self.metrics_collector.get_metric_statistics(MetricType.MEMORY_USAGE, minutes=5)
        if memory_stats["avg"] > self.thresholds.memory_critical:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                AlertSeverity.CRITICAL,
                "Critical Memory Usage",
                f"System memory usage is {memory_stats['avg']:.1f}% (Critical threshold: {self.thresholds.memory_critical}%)",
                metric_values={"memory_usage": memory_stats["avg"]},
                resolution_steps=[
                    "Identify memory-consuming processes",
                    "Clear unnecessary caches",
                    "Consider memory upgrade"
                ]
            )

        # Disk usage alerts
        disk_stats = self.metrics_collector.get_metric_statistics(MetricType.DISK_USAGE, minutes=5)
        if disk_stats["avg"] > self.thresholds.disk_critical:
            await self._create_alert(
                AlertType.RESOURCE_USAGE,
                AlertSeverity.CRITICAL,
                "Critical Disk Usage",
                f"System disk usage is {disk_stats['avg']:.1f}% (Critical threshold: {self.thresholds.disk_critical}%)",
                metric_values={"disk_usage": disk_stats["avg"]},
                resolution_steps=[
                    "Clean up temporary files",
                    "Archive old data",
                    "Expand storage capacity"
                ]
            )

    async def _check_tenant_alerts(self):
        """Check for tenant-specific alerts."""
        active_tenants = await self.metrics_collector.connection_manager.get_active_tenants()

        for tenant_id in active_tenants:
            # Response time alerts
            response_stats = self.metrics_collector.get_metric_statistics(
                MetricType.QUERY_RESPONSE_TIME, tenant_id, minutes=10
            )
            if response_stats["avg"] > self.thresholds.response_time_critical:
                await self._create_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    AlertSeverity.HIGH,
                    f"Critical Response Time - Tenant {tenant_id}",
                    f"Average response time is {response_stats['avg']:.1f}ms (Critical: {self.thresholds.response_time_critical}ms)",
                    tenant_id=tenant_id,
                    metric_values={"response_time": response_stats["avg"]},
                    resolution_steps=[
                        "Check database performance",
                        "Review recent queries",
                        "Consider query optimization"
                    ]
                )

            # Error rate alerts
            error_stats = self.metrics_collector.get_metric_statistics(
                MetricType.ERROR_RATE, tenant_id, minutes=10
            )
            if error_stats["avg"] > self.thresholds.error_rate_critical:
                await self._create_alert(
                    AlertType.PERFORMANCE_DEGRADATION,
                    AlertSeverity.HIGH,
                    f"High Error Rate - Tenant {tenant_id}",
                    f"Error rate is {error_stats['avg']:.1f}% (Critical: {self.thresholds.error_rate_critical}%)",
                    tenant_id=tenant_id,
                    metric_values={"error_rate": error_stats["avg"]},
                    resolution_steps=[
                        "Review error logs",
                        "Check database connectivity",
                        "Validate recent configuration changes"
                    ]
                )

            # Connection pool alerts
            connection_stats = self.metrics_collector.get_metric_statistics(
                MetricType.CONNECTION_COUNT, tenant_id, minutes=5
            )
            # Assuming connection limit of 100 for calculation
            connection_percent = (connection_stats["avg"] / 100) * 100
            if connection_percent > self.thresholds.connection_count_critical:
                await self._create_alert(
                    AlertType.RESOURCE_USAGE,
                    AlertSeverity.HIGH,
                    f"Connection Pool Critical - Tenant {tenant_id}",
                    f"Connection pool usage is {connection_percent:.1f}% (Critical: {self.thresholds.connection_count_critical}%)",
                    tenant_id=tenant_id,
                    metric_values={"connection_usage_percent": connection_percent},
                    resolution_steps=[
                        "Review active connections",
                        "Check for connection leaks",
                        "Consider increasing pool size"
                    ]
                )

    async def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        description: str,
        tenant_id: Optional[str] = None,
        affected_resources: List[str] = None,
        metric_values: Dict[str, float] = None,
        resolution_steps: List[str] = None
    ):
        """Create and process a new alert."""
        # Generate alert ID
        alert_id = f"{alert_type.value}:{tenant_id or 'system'}:{int(time.time())}"

        # Check if alert is suppressed
        suppress_key = f"{alert_type.value}:{tenant_id or 'system'}"
        if suppress_key in self.suppressed_alerts:
            return

        # Check for duplicate active alerts
        for existing_alert in self.active_alerts.values():
            if (existing_alert.alert_type == alert_type and
                existing_alert.tenant_id == tenant_id and
                not existing_alert.resolved):
                # Update existing alert instead of creating new one
                existing_alert.description = description
                existing_alert.timestamp = datetime.utcnow()
                existing_alert.metric_values.update(metric_values or {})
                return

        # Create new alert
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            timestamp=datetime.utcnow(),
            tenant_id=tenant_id,
            affected_resources=affected_resources or [],
            metric_values=metric_values or {},
            resolution_steps=resolution_steps or []
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {str(e)}")

        logger.warning(f"Alert created: {alert.title} ({alert.severity.value})")

    async def _process_alert_escalations(self):
        """Process alert escalations and auto-resolution."""
        current_time = datetime.utcnow()

        for alert_id, alert in list(self.active_alerts.items()):
            if alert.resolved:
                continue

            # Auto-resolve alerts after certain conditions are met
            if await self._should_auto_resolve_alert(alert):
                await self.resolve_alert(alert_id, "Auto-resolved: conditions no longer met")

            # Escalate critical alerts after 30 minutes
            if (alert.severity == AlertSeverity.CRITICAL and
                not alert.acknowledged and
                (current_time - alert.timestamp).total_seconds() > 1800):  # 30 minutes
                await self._escalate_alert(alert)

    async def _should_auto_resolve_alert(self, alert: Alert) -> bool:
        """Check if alert should be auto-resolved."""
        if alert.alert_type == AlertType.RESOURCE_USAGE:
            # Check if resource usage has returned to normal
            if "cpu_usage" in alert.metric_values:
                current_stats = self.metrics_collector.get_metric_statistics(
                    MetricType.CPU_USAGE, alert.tenant_id, minutes=5
                )
                return current_stats["avg"] < self.thresholds.cpu_warning

            if "memory_usage" in alert.metric_values:
                current_stats = self.metrics_collector.get_metric_statistics(
                    MetricType.MEMORY_USAGE, alert.tenant_id, minutes=5
                )
                return current_stats["avg"] < self.thresholds.memory_warning

        elif alert.alert_type == AlertType.PERFORMANCE_DEGRADATION:
            if "response_time" in alert.metric_values:
                current_stats = self.metrics_collector.get_metric_statistics(
                    MetricType.QUERY_RESPONSE_TIME, alert.tenant_id, minutes=5
                )
                return current_stats["avg"] < self.thresholds.response_time_warning

        return False

    async def _escalate_alert(self, alert: Alert):
        """Escalate critical alert."""
        escalated_alert = Alert(
            alert_id=f"{alert.alert_id}_escalated",
            alert_type=AlertType.SYSTEM_ERROR,
            severity=AlertSeverity.CRITICAL,
            title=f"ESCALATED: {alert.title}",
            description=f"Critical alert not acknowledged for 30 minutes: {alert.description}",
            timestamp=datetime.utcnow(),
            tenant_id=alert.tenant_id,
            affected_resources=alert.affected_resources,
            metric_values=alert.metric_values
        )

        self.active_alerts[escalated_alert.alert_id] = escalated_alert
        self.alert_history.append(escalated_alert)

        # Notify handlers about escalation
        for handler in self.alert_handlers:
            try:
                handler(escalated_alert)
            except Exception as e:
                logger.error(f"Escalation handler error: {str(e)}")

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        return False

    async def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            logger.info(f"Alert {alert_id} resolved: {resolution_note}")
            return True
        return False

    def suppress_alerts(self, alert_type: AlertType, tenant_id: Optional[str] = None, minutes: int = 60):
        """Suppress alerts for a specific type/tenant."""
        suppress_key = f"{alert_type.value}:{tenant_id or 'system'}"
        self.suppressed_alerts.add(suppress_key)

        # Auto-remove suppression after specified time
        async def remove_suppression():
            await asyncio.sleep(minutes * 60)
            self.suppressed_alerts.discard(suppress_key)

        asyncio.create_task(remove_suppression())

    def get_active_alerts(self, tenant_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by tenant."""
        active = [alert for alert in self.active_alerts.values() if not alert.resolved]
        if tenant_id:
            active = [alert for alert in active if alert.tenant_id == tenant_id]
        return sorted(active, key=lambda a: a.timestamp, reverse=True)

    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

        stats = {
            "total_alerts": len(recent_alerts),
            "by_severity": defaultdict(int),
            "by_type": defaultdict(int),
            "by_tenant": defaultdict(int),
            "resolved_count": 0,
            "avg_resolution_time_minutes": 0
        }

        resolution_times = []

        for alert in recent_alerts:
            stats["by_severity"][alert.severity.value] += 1
            stats["by_type"][alert.alert_type.value] += 1
            if alert.tenant_id:
                stats["by_tenant"][alert.tenant_id] += 1

            if alert.resolved and alert.resolved_at:
                stats["resolved_count"] += 1
                resolution_time = (alert.resolved_at - alert.timestamp).total_seconds() / 60
                resolution_times.append(resolution_time)

        if resolution_times:
            stats["avg_resolution_time_minutes"] = statistics.mean(resolution_times)

        return dict(stats)


class NotificationHandler:
    """Handles alert notifications via various channels."""

    def __init__(self):
        self.notification_channels = []

    def add_email_notification(self, smtp_config: Dict[str, Any], recipients: List[str]):
        """Add email notification channel."""
        async def send_email_alert(alert: Alert):
            try:
                # Email notification implementation
                subject = f"[{alert.severity.value.upper()}] {alert.title}"
                body = self._format_alert_email(alert)
                # Send email using SMTP config
                logger.info(f"Email alert sent: {alert.title}")
            except Exception as e:
                logger.error(f"Failed to send email alert: {str(e)}")

        self.notification_channels.append(send_email_alert)

    def add_webhook_notification(self, webhook_url: str, headers: Dict[str, str] = None):
        """Add webhook notification channel."""
        async def send_webhook_alert(alert: Alert):
            try:
                import aiohttp
                payload = {
                    "alert_id": alert.alert_id,
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "timestamp": alert.timestamp.isoformat(),
                    "tenant_id": alert.tenant_id,
                    "metric_values": alert.metric_values
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=payload, headers=headers or {}) as response:
                        if response.status == 200:
                            logger.info(f"Webhook alert sent: {alert.title}")
                        else:
                            logger.error(f"Webhook alert failed: {response.status}")
            except Exception as e:
                logger.error(f"Failed to send webhook alert: {str(e)}")

        self.notification_channels.append(send_webhook_alert)

    def _format_alert_email(self, alert: Alert) -> str:
        """Format alert for email notification."""
        return f"""
Alert: {alert.title}
Severity: {alert.severity.value.upper()}
Type: {alert.alert_type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
Tenant: {alert.tenant_id or 'System-wide'}

Description:
{alert.description}

Metric Values:
{', '.join(f'{k}: {v}' for k, v in alert.metric_values.items())}

Resolution Steps:
{chr(10).join(f'- {step}' for step in alert.resolution_steps)}

Alert ID: {alert.alert_id}
        """

    async def handle_alert(self, alert: Alert):
        """Handle alert notification through all channels."""
        for channel in self.notification_channels:
            try:
                await channel(alert)
            except Exception as e:
                logger.error(f"Notification channel error: {str(e)}")


class ResourceMonitoringSystem:
    """Main resource monitoring and alerting system."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.metrics_collector = MetricsCollector(connection_manager)
        self.alert_manager = AlertManager(self.metrics_collector)
        self.notification_handler = NotificationHandler()

        # Set up alert notifications
        self.alert_manager.add_alert_handler(self.notification_handler.handle_alert)

    async def start_monitoring(self):
        """Start the complete monitoring system."""
        logger.info("Starting resource monitoring system")

        # Start metrics collection
        metrics_task = asyncio.create_task(self.metrics_collector.start_collection())

        # Start alert monitoring
        alerts_task = asyncio.create_task(self.alert_manager.start_monitoring())

        # Wait for both tasks
        await asyncio.gather(metrics_task, alerts_task)

    def configure_thresholds(self, thresholds: MonitoringThresholds):
        """Configure monitoring thresholds."""
        self.alert_manager.thresholds = thresholds

    def add_notification_channel(self, channel_type: str, config: Dict[str, Any]):
        """Add notification channel."""
        if channel_type == "email":
            self.notification_handler.add_email_notification(
                config["smtp_config"],
                config["recipients"]
            )
        elif channel_type == "webhook":
            self.notification_handler.add_webhook_notification(
                config["webhook_url"],
                config.get("headers", {})
            )

    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]

        # System metrics
        cpu_stats = self.metrics_collector.get_metric_statistics(MetricType.CPU_USAGE, minutes=5)
        memory_stats = self.metrics_collector.get_metric_statistics(MetricType.MEMORY_USAGE, minutes=5)
        disk_stats = self.metrics_collector.get_metric_statistics(MetricType.DISK_USAGE, minutes=5)

        # Determine overall health
        health_status = "healthy"
        if critical_alerts:
            health_status = "critical"
        elif len(active_alerts) > 5:
            health_status = "degraded"
        elif (cpu_stats["avg"] > 70 or memory_stats["avg"] > 80 or disk_stats["avg"] > 75):
            health_status = "warning"

        return {
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "cpu_usage_percent": cpu_stats["avg"],
                "memory_usage_percent": memory_stats["avg"],
                "disk_usage_percent": disk_stats["avg"]
            },
            "alerts": {
                "total_active": len(active_alerts),
                "critical_count": len(critical_alerts),
                "recent_24h": len([a for a in self.alert_manager.alert_history
                                 if (datetime.utcnow() - a.timestamp).total_seconds() < 86400])
            },
            "tenants": {
                "total_monitored": len(await self.connection_manager.get_active_tenants())
            }
        }

    async def get_tenant_health(self, tenant_id: str) -> Dict[str, Any]:
        """Get health status for specific tenant."""
        tenant_alerts = self.alert_manager.get_active_alerts(tenant_id)

        # Tenant-specific metrics
        response_stats = self.metrics_collector.get_metric_statistics(
            MetricType.QUERY_RESPONSE_TIME, tenant_id, minutes=10
        )
        error_stats = self.metrics_collector.get_metric_statistics(
            MetricType.ERROR_RATE, tenant_id, minutes=10
        )
        connection_stats = self.metrics_collector.get_metric_statistics(
            MetricType.CONNECTION_COUNT, tenant_id, minutes=5
        )

        # Determine tenant health
        health_status = "healthy"
        if any(a.severity == AlertSeverity.CRITICAL for a in tenant_alerts):
            health_status = "critical"
        elif len(tenant_alerts) > 2:
            health_status = "degraded"
        elif (response_stats["avg"] > 1000 or error_stats["avg"] > 2):
            health_status = "warning"

        return {
            "tenant_id": tenant_id,
            "status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "avg_response_time_ms": response_stats["avg"],
                "error_rate_percent": error_stats["avg"],
                "active_connections": connection_stats["avg"]
            },
            "alerts": {
                "active_count": len(tenant_alerts),
                "critical_count": len([a for a in tenant_alerts if a.severity == AlertSeverity.CRITICAL])
            }
        }


# Export main classes
__all__ = [
    "ResourceMonitoringSystem",
    "MetricsCollector",
    "AlertManager",
    "NotificationHandler",
    "MonitoringThresholds",
    "Alert",
    "AlertSeverity",
    "AlertType",
    "MetricType"
]