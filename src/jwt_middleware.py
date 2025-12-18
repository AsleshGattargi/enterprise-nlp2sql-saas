"""
Enhanced JWT Middleware for Multi-Tenant RBAC System
Provides authentication, authorization, and tenant context injection for FastAPI.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from fastapi import HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

from .tenant_rbac_manager import TenantRBACManager, ResourceType, PermissionLevel


logger = logging.getLogger(__name__)


class TenantContext:
    """Context object containing tenant session information."""

    def __init__(self, user_id: str, tenant_id: str, roles: List[str],
                 session_id: str, is_global_admin: bool = False):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.roles = roles
        self.session_id = session_id
        self.is_global_admin = is_global_admin
        self.permissions_cache = {}


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware with tenant context injection."""

    def __init__(self, app, rbac_manager: TenantRBACManager,
                 exclude_paths: List[str] = None, require_tenant_header: bool = True):
        super().__init__(app)
        self.rbac_manager = rbac_manager
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json",
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/health", "/api/v1/status"
        ]
        self.require_tenant_header = require_tenant_header

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through JWT authentication."""

        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        try:
            # Extract JWT token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return self._unauthorized_response("Missing or invalid Authorization header")

            token = auth_header.split(" ")[1]

            # Validate JWT token
            token_payload = self.rbac_manager.validate_jwt_token(token)
            if not token_payload:
                return self._unauthorized_response("Invalid or expired token")

            # Extract tenant ID from header or token
            tenant_id = request.headers.get("X-Tenant-ID") or token_payload.get("tenant_id")

            if self.require_tenant_header and not tenant_id:
                return self._bad_request_response("Missing X-Tenant-ID header")

            # Verify token matches tenant context
            if tenant_id and token_payload.get("tenant_id") != tenant_id:
                return self._forbidden_response("Token tenant mismatch")

            # Get user profile for global admin check
            user_profile = self.rbac_manager.get_user_profile(token_payload["user_id"])
            if not user_profile:
                return self._unauthorized_response("User not found")

            # Create tenant context
            tenant_context = TenantContext(
                user_id=token_payload["user_id"],
                tenant_id=tenant_id or token_payload["tenant_id"],
                roles=token_payload["roles"],
                session_id=token_payload["session_id"],
                is_global_admin=user_profile.is_global_admin
            )

            # Inject tenant context into request state
            request.state.tenant_context = tenant_context

            # Log request with tenant context
            logger.info(f"Authenticated request: {request.method} {request.url.path} "
                       f"(user: {tenant_context.user_id}, tenant: {tenant_context.tenant_id})")

            response = await call_next(request)

            # Add tenant context headers to response
            response.headers["X-User-ID"] = tenant_context.user_id
            response.headers["X-Tenant-ID"] = tenant_context.tenant_id
            response.headers["X-Session-ID"] = tenant_context.session_id

            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT middleware error: {e}")
            return self._server_error_response("Authentication service error")

    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return 401 Unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={"error": "unauthorized", "message": message}
        )

    def _forbidden_response(self, message: str) -> JSONResponse:
        """Return 403 Forbidden response."""
        return JSONResponse(
            status_code=403,
            content={"error": "forbidden", "message": message}
        )

    def _bad_request_response(self, message: str) -> JSONResponse:
        """Return 400 Bad Request response."""
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "message": message}
        )

    def _server_error_response(self, message: str) -> JSONResponse:
        """Return 500 Internal Server Error response."""
        return JSONResponse(
            status_code=500,
            content={"error": "server_error", "message": message}
        )


class RBACDependencies:
    """FastAPI dependency injection for RBAC operations."""

    def __init__(self, rbac_manager: TenantRBACManager):
        self.rbac_manager = rbac_manager
        self.security = HTTPBearer(auto_error=False)

    def get_current_tenant_context(self, request: Request) -> TenantContext:
        """Get current tenant context from request state."""
        if not hasattr(request.state, 'tenant_context'):
            raise HTTPException(status_code=401, detail="No tenant context available")
        return request.state.tenant_context

    def require_permission(self, resource: ResourceType, level: PermissionLevel,
                          conditions: Optional[Dict[str, Any]] = None):
        """Dependency factory for requiring specific permissions."""

        def permission_checker(tenant_context: TenantContext = Depends(self.get_current_tenant_context)) -> TenantContext:
            # Check if user is global admin (bypass permission checks)
            if tenant_context.is_global_admin:
                return tenant_context

            # Check cached permissions
            cache_key = f"{resource.value}:{level.value}:{json.dumps(conditions, sort_keys=True)}"
            if cache_key in tenant_context.permissions_cache:
                if not tenant_context.permissions_cache[cache_key]:
                    raise HTTPException(status_code=403, detail="Insufficient permissions")
                return tenant_context

            # Check permission through RBAC manager
            has_permission = self.rbac_manager.check_user_permission(
                tenant_context.user_id,
                tenant_context.tenant_id,
                resource,
                level,
                conditions
            )

            # Cache result
            tenant_context.permissions_cache[cache_key] = has_permission

            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {resource.value} {level.value}"
                )

            return tenant_context

        return permission_checker

    def require_role(self, *required_roles: str):
        """Dependency factory for requiring specific roles."""

        def role_checker(tenant_context: TenantContext = Depends(self.get_current_tenant_context)) -> TenantContext:
            # Check if user is global admin (bypass role checks)
            if tenant_context.is_global_admin:
                return tenant_context

            # Check if user has any of the required roles
            if not any(role in tenant_context.roles for role in required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Role required: {' or '.join(required_roles)}"
                )

            return tenant_context

        return role_checker

    def require_global_admin(self, tenant_context: TenantContext = Depends(get_current_tenant_context)) -> TenantContext:
        """Dependency for requiring global admin privileges."""
        if not tenant_context.is_global_admin:
            raise HTTPException(status_code=403, detail="Global admin privileges required")
        return tenant_context

    def get_optional_tenant_context(self, request: Request) -> Optional[TenantContext]:
        """Get tenant context if available (for optional authentication)."""
        return getattr(request.state, 'tenant_context', None)


def setup_jwt_middleware(app, rbac_manager: TenantRBACManager,
                        exclude_paths: List[str] = None,
                        require_tenant_header: bool = True) -> RBACDependencies:
    """Setup JWT middleware and return RBAC dependencies."""

    # Add JWT middleware
    app.add_middleware(
        JWTMiddleware,
        rbac_manager=rbac_manager,
        exclude_paths=exclude_paths,
        require_tenant_header=require_tenant_header
    )

    # Return dependencies for use in route handlers
    return RBACDependencies(rbac_manager)


# Convenience functions for common permission checks
def require_read_queries():
    """Require READ permission for QUERIES resource."""
    def factory(rbac_deps: RBACDependencies):
        return rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.READ)
    return factory


def require_create_queries():
    """Require CREATE permission for QUERIES resource."""
    def factory(rbac_deps: RBACDependencies):
        return rbac_deps.require_permission(ResourceType.QUERIES, PermissionLevel.CREATE)
    return factory


def require_admin_access():
    """Require ADMIN permission for any resource."""
    def factory(rbac_deps: RBACDependencies):
        return rbac_deps.require_permission(ResourceType.SYSTEM, PermissionLevel.ADMIN)
    return factory


def require_user_management():
    """Require USER management permissions."""
    def factory(rbac_deps: RBACDependencies):
        return rbac_deps.require_permission(ResourceType.USERS, PermissionLevel.ADMIN)
    return factory


def require_database_access():
    """Require database access permissions."""
    def factory(rbac_deps: RBACDependencies):
        return rbac_deps.require_permission(ResourceType.DATABASES, PermissionLevel.READ)
    return factory


# Decorator for route-level permission checks
def permission_required(resource: ResourceType, level: PermissionLevel,
                       conditions: Optional[Dict[str, Any]] = None):
    """Decorator for FastAPI routes requiring specific permissions."""

    def decorator(func):
        # This would be used with FastAPI's dependency injection
        # The actual implementation would depend on how dependencies are set up
        func._required_permission = {
            "resource": resource,
            "level": level,
            "conditions": conditions
        }
        return func

    return decorator


# Example usage decorators
@permission_required(ResourceType.QUERIES, PermissionLevel.CREATE)
def create_query_endpoint():
    pass


@permission_required(ResourceType.USERS, PermissionLevel.ADMIN, {"scope": "tenant_only"})
def manage_tenant_users_endpoint():
    pass