"""
Tenant Management Dashboard
Provides comprehensive web-based dashboard for tenant administration and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from tenant_onboarding_models import (
    TenantStatus, OnboardingStatus, IndustryType, DatabaseType,
    TenantInfo, TenantResourceUsage, OnboardingWorkflow
)
from automated_provisioning import ProvisioningManager
from industry_schema_templates import IndustrySchemaTemplateManager
from tenant_rbac_manager import TenantRBACManager, get_current_user_with_tenant_check
from tenant_connection_manager import TenantConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
templates = Jinja2Templates(directory="templates")
router = APIRouter(prefix="/dashboard", tags=["Tenant Management Dashboard"])

# Global managers (would be dependency injected in production)
provisioning_manager: Optional[ProvisioningManager] = None
template_manager = IndustrySchemaTemplateManager()


def initialize_dashboard(
    prov_mgr: ProvisioningManager,
    conn_mgr: TenantConnectionManager,
    rbac_mgr: TenantRBACManager
):
    """Initialize dashboard with required dependencies."""
    global provisioning_manager
    provisioning_manager = prov_mgr


class DashboardAnalytics:
    """Analytics engine for dashboard metrics and insights."""

    def __init__(self, provisioning_mgr: ProvisioningManager):
        self.provisioning_mgr = provisioning_mgr

    async def get_overview_metrics(self) -> Dict[str, Any]:
        """Get high-level overview metrics for dashboard."""
        try:
            # Get basic counts
            total_tenants = await self.provisioning_mgr.get_total_tenant_count()
            active_tenants = await self.provisioning_mgr.get_active_tenant_count()
            pending_onboarding = await self.provisioning_mgr.get_pending_onboarding_count()
            failed_onboarding = await self.provisioning_mgr.get_failed_onboarding_count()

            # Calculate rates
            success_rate = 0
            if total_tenants > 0:
                success_rate = (active_tenants / total_tenants) * 100

            # Get resource utilization
            total_storage_gb = await self.provisioning_mgr.get_total_storage_usage()
            total_queries_today = await self.provisioning_mgr.get_total_queries_today()
            avg_response_time = await self.provisioning_mgr.get_avg_response_time()

            return {
                "tenant_counts": {
                    "total": total_tenants,
                    "active": active_tenants,
                    "pending": pending_onboarding,
                    "failed": failed_onboarding,
                    "success_rate": round(success_rate, 1)
                },
                "resource_utilization": {
                    "total_storage_gb": total_storage_gb,
                    "total_queries_today": total_queries_today,
                    "avg_response_time_ms": avg_response_time,
                    "system_health": "healthy"  # Would be calculated
                },
                "recent_activity": {
                    "new_registrations_24h": await self.provisioning_mgr.get_new_registrations_24h(),
                    "completed_onboarding_24h": await self.provisioning_mgr.get_completed_onboarding_24h(),
                    "active_queries_1h": await self.provisioning_mgr.get_active_queries_1h()
                }
            }

        except Exception as e:
            logger.error(f"Failed to get overview metrics: {str(e)}")
            return self._get_default_metrics()

    async def get_tenant_distribution(self) -> Dict[str, Any]:
        """Get tenant distribution by various dimensions."""
        try:
            industry_dist = await self.provisioning_mgr.get_tenant_industry_distribution()
            database_dist = await self.provisioning_mgr.get_tenant_database_distribution()
            region_dist = await self.provisioning_mgr.get_tenant_region_distribution()
            status_dist = await self.provisioning_mgr.get_tenant_status_distribution()

            return {
                "by_industry": industry_dist,
                "by_database": database_dist,
                "by_region": region_dist,
                "by_status": status_dist
            }

        except Exception as e:
            logger.error(f"Failed to get tenant distribution: {str(e)}")
            return self._get_default_distribution()

    async def get_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get performance trends over specified period."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get daily metrics
            daily_metrics = await self.provisioning_mgr.get_daily_metrics(start_date, end_date)

            # Process trends
            trends = {
                "dates": [],
                "new_tenants": [],
                "active_queries": [],
                "avg_response_time": [],
                "storage_usage": [],
                "success_rate": []
            }

            for metric in daily_metrics:
                trends["dates"].append(metric["date"].strftime("%Y-%m-%d"))
                trends["new_tenants"].append(metric["new_tenants"])
                trends["active_queries"].append(metric["total_queries"])
                trends["avg_response_time"].append(metric["avg_response_time_ms"])
                trends["storage_usage"].append(metric["storage_usage_gb"])
                trends["success_rate"].append(metric["success_rate"])

            return trends

        except Exception as e:
            logger.error(f"Failed to get performance trends: {str(e)}")
            return self._get_default_trends()

    async def get_top_performing_tenants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing tenants by various metrics."""
        try:
            # Get tenants with highest query volumes
            top_by_queries = await self.provisioning_mgr.get_top_tenants_by_queries(limit)

            # Get tenants with best performance
            top_by_performance = await self.provisioning_mgr.get_top_tenants_by_performance(limit)

            # Get newest active tenants
            newest_tenants = await self.provisioning_mgr.get_newest_active_tenants(limit)

            return {
                "top_by_queries": top_by_queries,
                "top_by_performance": top_by_performance,
                "newest_tenants": newest_tenants
            }

        except Exception as e:
            logger.error(f"Failed to get top performing tenants: {str(e)}")
            return {"top_by_queries": [], "top_by_performance": [], "newest_tenants": []}

    def _get_default_metrics(self) -> Dict[str, Any]:
        """Return default metrics when data unavailable."""
        return {
            "tenant_counts": {"total": 0, "active": 0, "pending": 0, "failed": 0, "success_rate": 0},
            "resource_utilization": {"total_storage_gb": 0, "total_queries_today": 0, "avg_response_time_ms": 0, "system_health": "unknown"},
            "recent_activity": {"new_registrations_24h": 0, "completed_onboarding_24h": 0, "active_queries_1h": 0}
        }

    def _get_default_distribution(self) -> Dict[str, Any]:
        """Return default distribution when data unavailable."""
        return {
            "by_industry": {},
            "by_database": {},
            "by_region": {},
            "by_status": {}
        }

    def _get_default_trends(self) -> Dict[str, Any]:
        """Return default trends when data unavailable."""
        return {
            "dates": [],
            "new_tenants": [],
            "active_queries": [],
            "avg_response_time": [],
            "storage_usage": [],
            "success_rate": []
        }


class OnboardingMonitor:
    """Monitor onboarding workflows and provide insights."""

    def __init__(self, provisioning_mgr: ProvisioningManager):
        self.provisioning_mgr = provisioning_mgr

    async def get_onboarding_queue_status(self) -> Dict[str, Any]:
        """Get current onboarding queue status."""
        try:
            # Get workflows by status
            workflows_by_status = await self.provisioning_mgr.get_workflows_by_status()

            # Calculate queue metrics
            total_in_queue = sum(
                len(workflows) for status, workflows in workflows_by_status.items()
                if status not in [OnboardingStatus.COMPLETED, OnboardingStatus.FAILED]
            )

            avg_processing_time = await self.provisioning_mgr.get_avg_onboarding_time()
            estimated_queue_time = total_in_queue * (avg_processing_time / 60)  # Convert to hours

            return {
                "queue_status": workflows_by_status,
                "total_in_queue": total_in_queue,
                "avg_processing_time_minutes": avg_processing_time,
                "estimated_queue_time_hours": round(estimated_queue_time, 1),
                "queue_health": "normal" if total_in_queue < 10 else "high"
            }

        except Exception as e:
            logger.error(f"Failed to get onboarding queue status: {str(e)}")
            return {"queue_status": {}, "total_in_queue": 0, "avg_processing_time_minutes": 0, "estimated_queue_time_hours": 0, "queue_health": "unknown"}

    async def get_failed_onboarding_analysis(self) -> Dict[str, Any]:
        """Analyze failed onboarding workflows."""
        try:
            failed_workflows = await self.provisioning_mgr.get_failed_workflows()

            # Analyze failure patterns
            failure_reasons = {}
            failure_steps = {}
            industry_failures = {}

            for workflow in failed_workflows:
                # Group by error messages
                for error in workflow.error_messages:
                    reason = self._categorize_error(error)
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

                # Group by failed steps
                for step in workflow.steps_failed:
                    failure_steps[step] = failure_steps.get(step, 0) + 1

                # Group by industry
                industry = workflow.registration_data.industry.value
                industry_failures[industry] = industry_failures.get(industry, 0) + 1

            return {
                "total_failed": len(failed_workflows),
                "failure_reasons": failure_reasons,
                "failure_steps": failure_steps,
                "industry_failures": industry_failures,
                "recent_failures": failed_workflows[:5]  # Most recent 5
            }

        except Exception as e:
            logger.error(f"Failed to analyze failed onboarding: {str(e)}")
            return {"total_failed": 0, "failure_reasons": {}, "failure_steps": {}, "industry_failures": {}, "recent_failures": []}

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error message into common failure types."""
        error_lower = error_message.lower()

        if "database" in error_lower or "connection" in error_lower:
            return "Database Connection"
        elif "rbac" in error_lower or "permission" in error_lower:
            return "RBAC Configuration"
        elif "clone" in error_lower or "backup" in error_lower:
            return "Database Cloning"
        elif "email" in error_lower or "notification" in error_lower:
            return "Email Delivery"
        elif "validation" in error_lower:
            return "Data Validation"
        elif "timeout" in error_lower:
            return "Timeout"
        else:
            return "Other"


# Dashboard API Endpoints

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(
    request: Request,
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Render main dashboard page."""
    try:
        # Check permissions
        if not _has_dashboard_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access dashboard"
            )

        return templates.TemplateResponse("dashboard/main.html", {
            "request": request,
            "user": current_user,
            "page_title": "Tenant Management Dashboard"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dashboard unavailable"
        )


@router.get("/api/overview")
async def get_dashboard_overview(
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Get dashboard overview data."""
    try:
        if not _has_dashboard_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        analytics = DashboardAnalytics(provisioning_manager)

        # Get all overview data
        overview_metrics = await analytics.get_overview_metrics()
        tenant_distribution = await analytics.get_tenant_distribution()
        performance_trends = await analytics.get_performance_trends(30)
        top_tenants = await analytics.get_top_performing_tenants(10)

        return {
            "metrics": overview_metrics,
            "distribution": tenant_distribution,
            "trends": performance_trends,
            "top_performers": top_tenants,
            "last_updated": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard data: {str(e)}"
        )


@router.get("/api/onboarding-status")
async def get_onboarding_status(
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Get onboarding workflow status and queue information."""
    try:
        if not _has_dashboard_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        monitor = OnboardingMonitor(provisioning_manager)

        # Get onboarding data
        queue_status = await monitor.get_onboarding_queue_status()
        failure_analysis = await monitor.get_failed_onboarding_analysis()

        return {
            "queue": queue_status,
            "failures": failure_analysis,
            "last_updated": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get onboarding status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve onboarding status: {str(e)}"
        )


@router.get("/api/tenant-analytics")
async def get_tenant_analytics(
    tenant_id: Optional[str] = None,
    timeframe: str = "30d",
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Get detailed tenant analytics."""
    try:
        if not _has_dashboard_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        # Parse timeframe
        days = _parse_timeframe(timeframe)

        analytics = DashboardAnalytics(provisioning_manager)

        if tenant_id:
            # Get specific tenant analytics
            tenant_metrics = await analytics.get_tenant_specific_metrics(tenant_id, days)
            return {
                "tenant_id": tenant_id,
                "metrics": tenant_metrics,
                "timeframe": timeframe,
                "last_updated": datetime.utcnow().isoformat()
            }
        else:
            # Get system-wide analytics
            system_metrics = await analytics.get_system_wide_metrics(days)
            return {
                "system_metrics": system_metrics,
                "timeframe": timeframe,
                "last_updated": datetime.utcnow().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant analytics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analytics: {str(e)}"
        )


@router.get("/api/resource-usage")
async def get_resource_usage(
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Get system resource usage information."""
    try:
        if not _has_dashboard_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        # Get resource usage data
        resource_data = await provisioning_manager.get_system_resource_usage()

        # Calculate utilization percentages
        cpu_utilization = await provisioning_manager.get_avg_cpu_utilization()
        memory_utilization = await provisioning_manager.get_avg_memory_utilization()
        storage_utilization = await provisioning_manager.get_storage_utilization()
        network_utilization = await provisioning_manager.get_network_utilization()

        return {
            "resource_usage": resource_data,
            "utilization": {
                "cpu_percent": cpu_utilization,
                "memory_percent": memory_utilization,
                "storage_percent": storage_utilization,
                "network_mbps": network_utilization
            },
            "alerts": await provisioning_manager.get_resource_alerts(),
            "recommendations": await provisioning_manager.get_optimization_recommendations(),
            "last_updated": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resource usage: {str(e)}"
        )


@router.get("/api/compliance-dashboard")
async def get_compliance_dashboard(
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Get compliance status across all tenants."""
    try:
        if not _has_dashboard_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        # Get compliance data
        compliance_summary = await provisioning_manager.get_compliance_summary()
        compliance_violations = await provisioning_manager.get_compliance_violations()
        audit_status = await provisioning_manager.get_audit_status()

        return {
            "compliance_summary": compliance_summary,
            "violations": compliance_violations,
            "audit_status": audit_status,
            "frameworks": {
                "total_frameworks": len(template_manager.compliance_mappings),
                "active_frameworks": await provisioning_manager.get_active_compliance_frameworks()
            },
            "last_updated": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve compliance data: {str(e)}"
        )


@router.post("/api/actions/retry-failed-onboarding")
async def retry_failed_onboarding(
    workflow_id: str,
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Retry a failed onboarding workflow."""
    try:
        if not _has_admin_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        success = await provisioning_manager.retry_failed_workflow(workflow_id, current_user.user_id)

        if success:
            return {"message": f"Workflow {workflow_id} queued for retry", "success": True}
        else:
            return {"message": f"Failed to retry workflow {workflow_id}", "success": False}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry workflow: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry workflow: {str(e)}"
        )


@router.post("/api/actions/cleanup-resources")
async def cleanup_unused_resources(
    current_user = Depends(get_current_user_with_tenant_check)
):
    """Cleanup unused system resources."""
    try:
        if not _has_admin_access(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        if not provisioning_manager:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Dashboard not initialized")

        cleanup_result = await provisioning_manager.cleanup_unused_resources()

        return {
            "message": "Resource cleanup completed",
            "resources_cleaned": cleanup_result,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup resources: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup resources: {str(e)}"
        )


# Helper Functions

def _has_dashboard_access(user) -> bool:
    """Check if user has dashboard access permissions."""
    return (
        "dashboard_access" in getattr(user, "permissions", []) or
        "admin" in getattr(user, "roles", []) or
        "tenant_manager" in getattr(user, "roles", [])
    )


def _has_admin_access(user) -> bool:
    """Check if user has admin access permissions."""
    return "admin" in getattr(user, "roles", [])


def _parse_timeframe(timeframe: str) -> int:
    """Parse timeframe string to number of days."""
    timeframe_map = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90,
        "1y": 365
    }
    return timeframe_map.get(timeframe, 30)


# Dashboard Data Models

class DashboardConfig:
    """Dashboard configuration and settings."""

    def __init__(self):
        self.refresh_interval = 30  # seconds
        self.chart_colors = {
            "primary": "#3B82F6",
            "secondary": "#8B5CF6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "info": "#06B6D4"
        }
        self.default_page_size = 20
        self.max_chart_points = 100

    def get_chart_config(self, chart_type: str) -> Dict[str, Any]:
        """Get configuration for specific chart type."""
        base_config = {
            "responsive": True,
            "maintainAspectRatio": False,
            "animation": {"duration": 1000},
            "colors": list(self.chart_colors.values())
        }

        if chart_type == "line":
            base_config.update({
                "scales": {
                    "x": {"display": True},
                    "y": {"display": True, "beginAtZero": True}
                }
            })
        elif chart_type == "pie":
            base_config.update({
                "plugins": {
                    "legend": {"position": "right"},
                    "tooltip": {"enabled": True}
                }
            })

        return base_config


# Export router and initialization function
__all__ = ["router", "initialize_dashboard", "DashboardAnalytics", "OnboardingMonitor"]