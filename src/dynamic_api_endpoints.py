"""
Dynamic API Endpoints for Multi-Tenant NLP2SQL System
Provides tenant-aware API endpoints with dynamic routing and data isolation.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, Path, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import io
import csv
import logging

from .tenant_connection_manager import TenantConnectionManager
from .tenant_routing_middleware import TenantRoutingContext, TenantSwitchManager
from .tenant_aware_nlp2sql import TenantAwareNLP2SQL, QueryResult, QueryAnalysis
from .jwt_middleware import RBACDependencies
from .rbac_role_templates import ResourceType, PermissionLevel


logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class NLPQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    max_results: Optional[int] = Field(100, description="Maximum number of results")
    format: Optional[str] = Field("json", description="Response format: json, csv, excel")
    include_analysis: Optional[bool] = Field(False, description="Include query analysis")
    cache_enabled: Optional[bool] = Field(True, description="Enable query caching")


class NLPQueryResponse(BaseModel):
    query_id: str
    tenant_id: str
    original_query: str
    generated_sql: str
    execution_time_ms: float
    row_count: int
    data: List[Dict[str, Any]]
    security_filtered: bool
    cached: bool
    analysis: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any]


class TenantSwitchRequest(BaseModel):
    tenant_id: str = Field(..., description="Target tenant ID")


class TenantSwitchResponse(BaseModel):
    success: bool
    access_token: str
    tenant_id: str
    roles: List[str]
    session_id: str
    expires_at: str
    switch_duration_ms: float


class SchemaInfoResponse(BaseModel):
    tenant_id: str
    database_type: str
    tables: Dict[str, Any]
    relationships: List[Dict[str, Any]]
    last_updated: str
    schema_version: str


class ConnectionHealthResponse(BaseModel):
    tenant_id: str
    status: str
    database_type: str
    connection_status: str
    error_count: int
    last_used: str
    metrics: Dict[str, Any]


class PerformanceMetricsResponse(BaseModel):
    tenant_id: str
    total_queries: int
    successful_queries: int
    avg_execution_time_ms: float
    cache_hit_rate: float
    last_query_time: Optional[str]


def setup_dynamic_api_routes(app, connection_manager: TenantConnectionManager,
                           nlp2sql_engine: TenantAwareNLP2SQL,
                           switch_manager: TenantSwitchManager,
                           rbac_deps: RBACDependencies):
    """Setup dynamic API routes for multi-tenant operations."""

    router = APIRouter(prefix="/api/v1/tenant", tags=["Multi-Tenant Operations"])

    # ============================================================================
    # NLP Query Endpoints
    # ============================================================================

    @router.post("/query", response_model=NLPQueryResponse)
    async def execute_nlp_query(
        request: NLPQueryRequest,
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.READ)
        )
    ):
        """Execute natural language query on tenant database."""
        try:
            # Process NLP query with tenant awareness
            result = await nlp2sql_engine.process_nlp_query(
                request.query, tenant_context
            )

            # Limit results if requested
            if request.max_results and request.max_results < len(result.data):
                result.data = result.data[:request.max_results]
                result.row_count = len(result.data)

            # Build response
            response_data = {
                "query_id": result.query_id,
                "tenant_id": result.tenant_id,
                "original_query": result.original_query,
                "generated_sql": result.generated_sql,
                "execution_time_ms": result.execution_time_ms,
                "row_count": result.row_count,
                "data": result.data,
                "security_filtered": result.security_filtered,
                "cached": result.cached,
                "metadata": result.metadata
            }

            # Include analysis if requested
            if request.include_analysis and result.analysis:
                response_data["analysis"] = {
                    "query_type": result.analysis.query_type.value,
                    "tables_involved": result.analysis.tables_involved,
                    "columns_involved": result.analysis.columns_involved,
                    "security_level": result.analysis.security_level.value,
                    "estimated_complexity": result.analysis.estimated_complexity,
                    "confidence_score": result.analysis.confidence_score
                }

            return NLPQueryResponse(**response_data)

        except Exception as e:
            logger.error(f"Error executing NLP query: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to execute query: {str(e)}"
            )

    @router.get("/query/{query_id}")
    async def get_query_result(
        query_id: str = Path(..., description="Query ID"),
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.READ)
        )
    ):
        """Get cached query result by ID."""
        try:
            # This would retrieve from a query results store
            # For now, return a placeholder response
            return {
                "query_id": query_id,
                "tenant_id": tenant_context.tenant_id,
                "status": "completed",
                "message": "Query result retrieval not yet implemented"
            }

        except Exception as e:
            logger.error(f"Error retrieving query result: {e}")
            raise HTTPException(status_code=404, detail="Query result not found")

    @router.post("/query/export")
    async def export_query_results(
        request: NLPQueryRequest,
        export_format: str = Query("csv", description="Export format: csv, excel, json"),
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.READ)
        )
    ):
        """Execute query and export results in specified format."""
        try:
            # Execute query
            result = await nlp2sql_engine.process_nlp_query(
                request.query, tenant_context
            )

            if export_format.lower() == "csv":
                return _export_csv(result)
            elif export_format.lower() == "excel":
                return _export_excel(result)
            elif export_format.lower() == "json":
                return _export_json(result)
            else:
                raise HTTPException(status_code=400, detail="Unsupported export format")

        except Exception as e:
            logger.error(f"Error exporting query results: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to export results: {str(e)}"
            )

    # ============================================================================
    # Tenant Management Endpoints
    # ============================================================================

    @router.post("/switch", response_model=TenantSwitchResponse)
    async def switch_tenant_context(
        request: TenantSwitchRequest,
        http_request: Request,
        tenant_context: TenantRoutingContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Switch to a different tenant context."""
        try:
            result = await switch_manager.switch_tenant_context(
                tenant_context.user_id,
                request.tenant_id,
                tenant_context,
                http_request
            )

            return TenantSwitchResponse(**result)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error switching tenant: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to switch tenant: {str(e)}"
            )

    @router.get("/current")
    async def get_current_tenant_info(
        tenant_context: TenantRoutingContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Get current tenant context information."""
        try:
            tenant_info = connection_manager.get_tenant_info(tenant_context.tenant_id)
            metrics = connection_manager.get_connection_metrics(tenant_context.tenant_id)

            return {
                "tenant_id": tenant_context.tenant_id,
                "user_id": tenant_context.user_id,
                "roles": tenant_context.roles,
                "access_level": tenant_context.access_level,
                "allowed_operations": tenant_context.allowed_operations,
                "session_id": tenant_context.session_id,
                "database_type": tenant_info.database_type.value if tenant_info else "unknown",
                "connection_status": tenant_info.status.value if tenant_info else "unknown",
                "performance_metrics": {
                    "avg_response_time_ms": metrics.avg_response_time_ms if metrics else 0,
                    "last_activity": metrics.last_activity.isoformat() if metrics else None
                }
            }

        except Exception as e:
            logger.error(f"Error getting tenant info: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get tenant info: {str(e)}"
            )

    @router.get("/accessible")
    async def get_accessible_tenants(
        tenant_context: TenantRoutingContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Get list of tenants accessible to current user."""
        try:
            from .tenant_rbac_manager import TenantRBACManager

            # This would use the RBAC manager to get user's tenant access
            # For now, return current tenant
            return {
                "accessible_tenants": [
                    {
                        "tenant_id": tenant_context.tenant_id,
                        "roles": tenant_context.roles,
                        "access_level": tenant_context.access_level,
                        "is_current": True
                    }
                ],
                "total_count": 1
            }

        except Exception as e:
            logger.error(f"Error getting accessible tenants: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get accessible tenants: {str(e)}"
            )

    # ============================================================================
    # Schema and Database Information
    # ============================================================================

    @router.get("/schema", response_model=SchemaInfoResponse)
    async def get_tenant_schema(
        include_sample_data: bool = Query(False, description="Include sample data"),
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.DATABASES, PermissionLevel.READ)
        )
    ):
        """Get tenant database schema information."""
        try:
            schema_info = nlp2sql_engine.schema_manager.get_tenant_schema(tenant_context.tenant_id)

            if not schema_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"Schema not found for tenant: {tenant_context.tenant_id}"
                )

            response_data = {
                "tenant_id": schema_info.tenant_id,
                "database_type": schema_info.database_type.value,
                "tables": schema_info.tables,
                "relationships": schema_info.relationships,
                "last_updated": schema_info.last_updated.isoformat(),
                "schema_version": schema_info.schema_version
            }

            # Include sample data if requested and user has permission
            if include_sample_data and tenant_context.access_level in ['ADMIN', 'SUPER_ADMIN', 'ANALYST']:
                response_data["sample_data"] = await _get_sample_data(tenant_context, schema_info)

            return SchemaInfoResponse(**response_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get schema: {str(e)}"
            )

    @router.post("/schema/refresh")
    async def refresh_tenant_schema(
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.DATABASES, PermissionLevel.UPDATE)
        )
    ):
        """Refresh tenant schema cache."""
        try:
            success = nlp2sql_engine.refresh_tenant_schema(tenant_context.tenant_id)

            if success:
                return {
                    "success": True,
                    "message": "Schema cache refreshed successfully",
                    "tenant_id": tenant_context.tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to refresh schema cache"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing schema: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh schema: {str(e)}"
            )

    # ============================================================================
    # Connection and Health Monitoring
    # ============================================================================

    @router.get("/health", response_model=ConnectionHealthResponse)
    async def get_tenant_health(
        tenant_context: TenantRoutingContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Get tenant database health status."""
        try:
            health_info = connection_manager.health_check(tenant_context.tenant_id)

            if "error" in health_info:
                raise HTTPException(
                    status_code=503,
                    detail=f"Tenant database unhealthy: {health_info['error']}"
                )

            return ConnectionHealthResponse(**health_info)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking health: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check health: {str(e)}"
            )

    @router.get("/metrics", response_model=PerformanceMetricsResponse)
    async def get_tenant_metrics(
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.ANALYTICS, PermissionLevel.READ)
        )
    ):
        """Get tenant performance metrics."""
        try:
            metrics = nlp2sql_engine.get_tenant_metrics(tenant_context.tenant_id)

            if not metrics:
                return PerformanceMetricsResponse(
                    tenant_id=tenant_context.tenant_id,
                    total_queries=0,
                    successful_queries=0,
                    avg_execution_time_ms=0,
                    cache_hit_rate=0,
                    last_query_time=None
                )

            return PerformanceMetricsResponse(
                tenant_id=tenant_context.tenant_id,
                **metrics
            )

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get metrics: {str(e)}"
            )

    @router.post("/connections/refresh")
    async def refresh_tenant_connections(
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.DATABASES, PermissionLevel.UPDATE)
        )
    ):
        """Refresh tenant database connections."""
        try:
            success = connection_manager.create_connection_pool(
                tenant_context.tenant_id, force_recreate=True
            )

            if success:
                return {
                    "success": True,
                    "message": "Connection pool refreshed successfully",
                    "tenant_id": tenant_context.tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to refresh connection pool"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing connections: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh connections: {str(e)}"
            )

    # ============================================================================
    # Cache Management
    # ============================================================================

    @router.post("/cache/clear")
    async def clear_tenant_cache(
        cache_type: str = Query("query", description="Cache type: query, schema, all"),
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.SYSTEM, PermissionLevel.UPDATE)
        )
    ):
        """Clear tenant caches."""
        try:
            if cache_type == "query":
                nlp2sql_engine.clear_cache(tenant_context.tenant_id)
                message = "Query cache cleared"
            elif cache_type == "schema":
                nlp2sql_engine.schema_manager.get_tenant_schema(tenant_context.tenant_id, force_refresh=True)
                message = "Schema cache refreshed"
            elif cache_type == "all":
                nlp2sql_engine.clear_cache(tenant_context.tenant_id)
                nlp2sql_engine.schema_manager.get_tenant_schema(tenant_context.tenant_id, force_refresh=True)
                message = "All caches cleared"
            else:
                raise HTTPException(status_code=400, detail="Invalid cache type")

            return {
                "success": True,
                "message": message,
                "tenant_id": tenant_context.tenant_id,
                "cache_type": cache_type,
                "timestamp": datetime.utcnow().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear cache: {str(e)}"
            )

    # ============================================================================
    # System Status and Diagnostics
    # ============================================================================

    @router.get("/system/status")
    async def get_system_status(
        tenant_context: TenantRoutingContext = Depends(
            rbac_deps.require_permission(ResourceType.SYSTEM, PermissionLevel.READ)
        )
    ):
        """Get system status for tenant operations."""
        try:
            # Get connection manager status
            connection_health = connection_manager.health_check()

            # Get NLP2SQL engine metrics
            nlp_metrics = nlp2sql_engine.get_tenant_metrics()

            # Get routing metrics if available
            routing_metrics = {}
            if hasattr(tenant_context, 'routing_metrics'):
                routing_metrics = tenant_context.routing_metrics

            return {
                "status": "operational",
                "timestamp": datetime.utcnow().isoformat(),
                "tenant_id": tenant_context.tenant_id,
                "components": {
                    "connection_manager": {
                        "status": connection_health.get("overall_status", "unknown"),
                        "total_tenants": connection_health.get("total_tenants", 0),
                        "healthy_tenants": connection_health.get("healthy_tenants", 0)
                    },
                    "nlp2sql_engine": {
                        "status": "operational",
                        "cached_queries": len(nlp2sql_engine.query_cache),
                        "tenant_metrics": len(nlp_metrics)
                    },
                    "routing": {
                        "status": "operational",
                        "metrics": routing_metrics
                    }
                }
            }

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get system status: {str(e)}"
            )

    # Add router to app
    app.include_router(router)

    return router


# Helper functions for export functionality
def _export_csv(result: QueryResult) -> StreamingResponse:
    """Export query results as CSV."""
    output = io.StringIO()
    if result.data:
        writer = csv.DictWriter(output, fieldnames=result.data[0].keys())
        writer.writeheader()
        writer.writerows(result.data)

    response = StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=query_{result.query_id}.csv"}
    )
    return response


def _export_excel(result: QueryResult) -> StreamingResponse:
    """Export query results as Excel."""
    try:
        import pandas as pd

        df = pd.DataFrame(result.data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        response = StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=query_{result.query_id}.xlsx"}
        )
        return response

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel export requires pandas and openpyxl packages"
        )


def _export_json(result: QueryResult) -> JSONResponse:
    """Export query results as JSON."""
    return JSONResponse(
        content={
            "query_id": result.query_id,
            "tenant_id": result.tenant_id,
            "data": result.data,
            "metadata": result.metadata
        },
        headers={"Content-Disposition": f"attachment; filename=query_{result.query_id}.json"}
    )


async def _get_sample_data(tenant_context: TenantRoutingContext, schema_info) -> Dict[str, Any]:
    """Get sample data from tenant tables."""
    sample_data = {}

    try:
        # Get small sample from each table (max 5 rows)
        for table_name in list(schema_info.tables.keys())[:5]:  # Limit to 5 tables
            try:
                # Create a simple SELECT query
                from .tenant_aware_nlp2sql import TenantAwareNLP2SQL
                sample_query = f"show me 3 rows from {table_name}"

                # This would need the actual NLP2SQL engine instance
                # For now, return placeholder
                sample_data[table_name] = [
                    {"sample": "data", "table": table_name, "row": i}
                    for i in range(3)
                ]

            except Exception as e:
                logger.warning(f"Could not get sample data for table {table_name}: {e}")
                sample_data[table_name] = []

    except Exception as e:
        logger.error(f"Error getting sample data: {e}")

    return sample_data