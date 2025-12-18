"""
Enhanced FastAPI Middleware for Dynamic Tenant Routing
Handles tenant context extraction, database routing, and multi-tenant user management.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from .tenant_connection_manager import TenantConnectionManager, ConnectionStatus
from .tenant_rbac_manager import TenantRBACManager
from .jwt_middleware import TenantContext


logger = logging.getLogger(__name__)


class TenantRoutingContext:
    """Enhanced tenant context with connection and routing information."""

    def __init__(self, user_id: str, tenant_id: str, roles: List[str],
                 session_id: str, is_global_admin: bool = False,
                 database_connection: Any = None, connection_manager: TenantConnectionManager = None):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles
        self.session_id = session_id
        self.is_global_admin = is_global_admin
        self.database_connection = database_connection
        self.connection_manager = connection_manager

        # Performance tracking
        self.request_start_time = time.time()
        self.routing_metrics = {}

        # Security context
        self.access_level = self._determine_access_level()
        self.allowed_operations = self._determine_allowed_operations()

    def _determine_access_level(self) -> str:
        """Determine user's access level for this tenant."""
        if self.is_global_admin:
            return "SUPER_ADMIN"
        elif "admin" in self.roles:
            return "ADMIN"
        elif "analyst" in self.roles:
            return "ANALYST"
        elif "business_user" in self.roles:
            return "BUSINESS_USER"
        elif "viewer" in self.roles:
            return "VIEWER"
        else:
            return "GUEST"

    def _determine_allowed_operations(self) -> List[str]:
        """Determine allowed operations based on roles."""
        operations = []

        if self.is_global_admin:
            operations = ["READ", "WRITE", "DELETE", "ADMIN", "SCHEMA_MODIFY"]
        elif "admin" in self.roles:
            operations = ["READ", "WRITE", "DELETE", "USER_MANAGE"]
        elif "analyst" in self.roles:
            operations = ["READ", "WRITE", "QUERY_CREATE"]
        elif "business_user" in self.roles:
            operations = ["READ", "QUERY_TEMPLATE"]
        elif "viewer" in self.roles:
            operations = ["READ"]

        return operations

    def get_database_connection(self, db_type: str = None):
        """Get database connection for current tenant."""
        if self.connection_manager:
            return self.connection_manager.get_connection(self.tenant_id, db_type)
        return self.database_connection

    def close_database_connection(self):
        """Close database connection."""
        if self.database_connection and hasattr(self.database_connection, 'close'):
            try:
                self.database_connection.close()
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

    def record_routing_metric(self, operation: str, duration_ms: float, success: bool = True):
        """Record routing operation metrics."""
        if operation not in self.routing_metrics:
            self.routing_metrics[operation] = []

        self.routing_metrics[operation].append({
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_request_duration(self) -> float:
        """Get total request duration in milliseconds."""
        return (time.time() - self.request_start_time) * 1000


class TenantRoutingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for dynamic tenant routing with connection management.
    """

    def __init__(self, app, connection_manager: TenantConnectionManager,
                 rbac_manager: TenantRBACManager,
                 exclude_paths: List[str] = None,
                 enable_connection_pooling: bool = True,
                 enable_query_caching: bool = True):
        super().__init__(app)
        self.connection_manager = connection_manager
        self.rbac_manager = rbac_manager
        self.enable_connection_pooling = enable_connection_pooling
        self.enable_query_caching = enable_query_caching

        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/health", "/api/v1/status",
            "/api/v1/rbac/system/status"
        ]

        # Performance monitoring
        self.request_metrics = {}
        self.tenant_switch_cache = {}  # Cache for recent tenant switches

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enhanced request processing with tenant routing."""

        # Skip middleware for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        start_time = time.time()
        tenant_context = None

        try:
            # Extract and validate tenant context
            tenant_context = await self._extract_tenant_context(request)

            if not tenant_context:
                return self._unauthorized_response("No valid tenant context")

            # Validate tenant access
            if not await self._validate_tenant_access(tenant_context):
                return self._forbidden_response("Invalid tenant access")

            # Initialize database connection if needed
            if self.enable_connection_pooling:
                await self._initialize_tenant_connection(tenant_context, request)

            # Check tenant database health
            health_status = await self._check_tenant_health(tenant_context.tenant_id)
            if health_status.get("status") != "healthy":
                return self._service_unavailable_response(
                    f"Tenant database unavailable: {health_status.get('error', 'Unknown error')}"
                )

            # Inject enhanced tenant context
            request.state.tenant_context = tenant_context

            # Add routing headers
            self._add_routing_headers(request, tenant_context)

            # Process request
            response = await call_next(request)

            # Add response headers and metrics
            self._add_response_headers(response, tenant_context)
            await self._record_request_metrics(request, tenant_context, start_time, True)

            return response

        except HTTPException as e:
            await self._record_request_metrics(request, tenant_context, start_time, False)
            raise
        except Exception as e:
            logger.error(f"Tenant routing middleware error: {e}")
            await self._record_request_metrics(request, tenant_context, start_time, False)
            return self._server_error_response("Tenant routing service error")
        finally:
            # Cleanup connection if needed
            if tenant_context:
                tenant_context.close_database_connection()

    async def _extract_tenant_context(self, request: Request) -> Optional[TenantRoutingContext]:
        """Extract and enhance tenant context from request."""
        try:
            # Get basic tenant context from JWT middleware
            basic_context = getattr(request.state, 'tenant_context', None)

            if not basic_context:
                # Try to extract from headers for API requests
                auth_header = request.headers.get("Authorization")
                tenant_header = request.headers.get("X-Tenant-ID")

                if not auth_header or not tenant_header:
                    return None

                token = auth_header.split(" ")[1] if auth_header.startswith("Bearer ") else None
                if not token:
                    return None

                # Validate token and get user info
                token_payload = self.rbac_manager.validate_jwt_token(token)
                if not token_payload:
                    return None

                # Create basic context from token
                basic_context = TenantContext(
                    user_id=token_payload["user_id"],
                    tenant_id=tenant_header,
                    roles=token_payload.get("roles", []),
                    session_id=token_payload.get("session_id", ""),
                    is_global_admin=False  # Will be set properly below
                )

            # Get user profile for enhanced context
            user_profile = self.rbac_manager.get_user_profile(basic_context.user_id)
            if not user_profile:
                return None

            # Create enhanced tenant context
            enhanced_context = TenantRoutingContext(
                user_id=basic_context.user_id,
                tenant_id=basic_context.tenant_id,
                roles=basic_context.roles,
                session_id=basic_context.session_id,
                is_global_admin=user_profile.is_global_admin,
                connection_manager=self.connection_manager
            )

            return enhanced_context

        except Exception as e:
            logger.error(f"Error extracting tenant context: {e}")
            return None

    async def _validate_tenant_access(self, context: TenantRoutingContext) -> bool:
        """Validate user's access to the tenant."""
        try:
            # Global admins have access to all tenants
            if context.is_global_admin:
                return True

            # Check if user has access to this tenant
            user_profile = self.rbac_manager.get_user_profile(context.user_id)
            if not user_profile:
                return False

            return context.tenant_id in user_profile.tenant_access

        except Exception as e:
            logger.error(f"Error validating tenant access: {e}")
            return False

    async def _initialize_tenant_connection(self, context: TenantRoutingContext, request: Request):
        """Initialize database connection for tenant."""
        if not self.enable_connection_pooling:
            return

        try:
            start_time = time.time()

            # Check if connection pool exists
            tenant_info = self.connection_manager.get_tenant_info(context.tenant_id)

            if not tenant_info:
                # Create new connection pool
                success = self.connection_manager.create_connection_pool(context.tenant_id)
                if not success:
                    raise Exception(f"Failed to create connection pool for tenant: {context.tenant_id}")

            # Record connection initialization metrics
            duration = (time.time() - start_time) * 1000
            context.record_routing_metric("connection_init", duration)

        except Exception as e:
            logger.error(f"Error initializing tenant connection: {e}")
            raise

    async def _check_tenant_health(self, tenant_id: str) -> Dict[str, Any]:
        """Check tenant database health."""
        try:
            return self.connection_manager.health_check(tenant_id)
        except Exception as e:
            logger.error(f"Error checking tenant health: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def _add_routing_headers(self, request: Request, context: TenantRoutingContext):
        """Add routing information to request headers."""
        if not hasattr(request.state, 'routing_headers'):
            request.state.routing_headers = {}

        request.state.routing_headers.update({
            "X-Tenant-ID": context.tenant_id,
            "X-User-ID": context.user_id,
            "X-Access-Level": context.access_level,
            "X-Session-ID": context.session_id,
            "X-Request-ID": f"req_{int(time.time() * 1000)}"
        })

    def _add_response_headers(self, response: Response, context: TenantRoutingContext):
        """Add tenant routing information to response headers."""
        response.headers["X-Tenant-ID"] = context.tenant_id
        response.headers["X-User-ID"] = context.user_id
        response.headers["X-Access-Level"] = context.access_level
        response.headers["X-Request-Duration-Ms"] = str(round(context.get_request_duration(), 2))

        # Add connection pool metrics
        metrics = self.connection_manager.get_connection_metrics(context.tenant_id)
        if metrics:
            response.headers["X-Pool-Utilization"] = str(round(metrics.pool_utilization, 2))

    async def _record_request_metrics(self, request: Request, context: Optional[TenantRoutingContext],
                                    start_time: float, success: bool):
        """Record request metrics for monitoring."""
        try:
            duration = (time.time() - start_time) * 1000
            path = request.url.path
            method = request.method

            if context:
                tenant_id = context.tenant_id

                if tenant_id not in self.request_metrics:
                    self.request_metrics[tenant_id] = {
                        "total_requests": 0,
                        "successful_requests": 0,
                        "failed_requests": 0,
                        "avg_duration_ms": 0,
                        "max_duration_ms": 0,
                        "last_request": None
                    }

                metrics = self.request_metrics[tenant_id]
                metrics["total_requests"] += 1

                if success:
                    metrics["successful_requests"] += 1
                else:
                    metrics["failed_requests"] += 1

                # Update duration metrics
                if metrics["avg_duration_ms"] == 0:
                    metrics["avg_duration_ms"] = duration
                else:
                    metrics["avg_duration_ms"] = (metrics["avg_duration_ms"] * 0.9) + (duration * 0.1)

                metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration)
                metrics["last_request"] = datetime.utcnow().isoformat()

                # Log slow requests
                if duration > 1000:  # More than 1 second
                    logger.warning(f"Slow request: {method} {path} took {duration:.2f}ms for tenant {tenant_id}")

        except Exception as e:
            logger.error(f"Error recording request metrics: {e}")

    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics."""
        return {
            "tenant_metrics": self.request_metrics,
            "connection_metrics": self.connection_manager.get_all_metrics(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return 401 Unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={
                "error": "unauthorized",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _forbidden_response(self, message: str) -> JSONResponse:
        """Return 403 Forbidden response."""
        return JSONResponse(
            status_code=403,
            content={
                "error": "forbidden",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _service_unavailable_response(self, message: str) -> JSONResponse:
        """Return 503 Service Unavailable response."""
        return JSONResponse(
            status_code=503,
            content={
                "error": "service_unavailable",
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_after": 30
            }
        )

    def _server_error_response(self, message: str) -> JSONResponse:
        """Return 500 Internal Server Error response."""
        return JSONResponse(
            status_code=500,
            content={
                "error": "server_error",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class TenantSwitchManager:
    """Manages tenant switching for multi-tenant users."""

    def __init__(self, rbac_manager: TenantRBACManager, connection_manager: TenantConnectionManager):
        self.rbac_manager = rbac_manager
        self.connection_manager = connection_manager
        self.switch_cache = {}  # Cache recent switches
        self.switch_metrics = {}

    async def switch_tenant_context(self, user_id: str, new_tenant_id: str,
                                  current_context: TenantRoutingContext,
                                  request: Request) -> Dict[str, Any]:
        """Switch user to a different tenant context."""
        start_time = time.time()

        try:
            # Validate user has access to new tenant
            user_profile = self.rbac_manager.get_user_profile(user_id)
            if not user_profile:
                raise HTTPException(status_code=404, detail="User not found")

            if new_tenant_id not in user_profile.tenant_access and not user_profile.is_global_admin:
                raise HTTPException(status_code=403, detail="Access denied to tenant")

            # Create new tenant session
            new_session = self.rbac_manager.create_tenant_session(
                user_id,
                new_tenant_id,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )

            if not new_session:
                raise HTTPException(status_code=500, detail="Failed to create tenant session")

            # Generate new JWT token
            new_token = self.rbac_manager.generate_jwt_token(new_session)

            # Initialize connection pool for new tenant if needed
            tenant_info = self.connection_manager.get_tenant_info(new_tenant_id)
            if not tenant_info:
                self.connection_manager.create_connection_pool(new_tenant_id)

            # Record switch metrics
            duration = (time.time() - start_time) * 1000
            self._record_switch_metrics(user_id, current_context.tenant_id, new_tenant_id, duration)

            # Cache the switch for performance
            cache_key = f"{user_id}:{new_tenant_id}"
            self.switch_cache[cache_key] = {
                "timestamp": datetime.utcnow(),
                "roles": new_session.roles,
                "session_id": new_session.session_id
            }

            return {
                "success": True,
                "access_token": new_token,
                "tenant_id": new_tenant_id,
                "roles": new_session.roles,
                "session_id": new_session.session_id,
                "expires_at": new_session.expires_at.isoformat(),
                "switch_duration_ms": round(duration, 2)
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error switching tenant context: {e}")
            raise HTTPException(status_code=500, detail="Failed to switch tenant")

    def _record_switch_metrics(self, user_id: str, from_tenant: str, to_tenant: str, duration_ms: float):
        """Record tenant switch metrics."""
        try:
            if user_id not in self.switch_metrics:
                self.switch_metrics[user_id] = {
                    "total_switches": 0,
                    "avg_duration_ms": 0,
                    "recent_switches": []
                }

            metrics = self.switch_metrics[user_id]
            metrics["total_switches"] += 1

            # Update average duration
            if metrics["avg_duration_ms"] == 0:
                metrics["avg_duration_ms"] = duration_ms
            else:
                metrics["avg_duration_ms"] = (metrics["avg_duration_ms"] * 0.8) + (duration_ms * 0.2)

            # Record recent switch
            metrics["recent_switches"].append({
                "from_tenant": from_tenant,
                "to_tenant": to_tenant,
                "duration_ms": duration_ms,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Keep only last 10 switches
            if len(metrics["recent_switches"]) > 10:
                metrics["recent_switches"].pop(0)

        except Exception as e:
            logger.error(f"Error recording switch metrics: {e}")

    def get_switch_metrics(self, user_id: str = None) -> Dict[str, Any]:
        """Get tenant switch metrics."""
        if user_id:
            return self.switch_metrics.get(user_id, {})
        return self.switch_metrics


def setup_tenant_routing_middleware(app, connection_manager: TenantConnectionManager,
                                  rbac_manager: TenantRBACManager,
                                  exclude_paths: List[str] = None,
                                  enable_connection_pooling: bool = True,
                                  enable_query_caching: bool = True) -> TenantSwitchManager:
    """Setup tenant routing middleware and return switch manager."""

    # Add tenant routing middleware
    app.add_middleware(
        TenantRoutingMiddleware,
        connection_manager=connection_manager,
        rbac_manager=rbac_manager,
        exclude_paths=exclude_paths,
        enable_connection_pooling=enable_connection_pooling,
        enable_query_caching=enable_query_caching
    )

    # Create and return switch manager
    switch_manager = TenantSwitchManager(rbac_manager, connection_manager)

    return switch_manager