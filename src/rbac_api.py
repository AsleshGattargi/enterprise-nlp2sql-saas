"""
RBAC API Endpoints for Multi-Tenant System
Provides comprehensive role-based access control API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from .tenant_rbac_manager import TenantRBACManager, UserProfile, TenantSession
from .cross_tenant_user_manager import CrossTenantUserManager, AccessRequestStatus
from .rbac_role_templates import ResourceType, PermissionLevel
from .jwt_middleware import RBACDependencies, TenantContext


logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class LoginRequest(BaseModel):
    username_or_email: str
    password: str
    tenant_id: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_profile: Dict[str, Any]
    tenant_context: Optional[Dict[str, Any]] = None


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    is_global_admin: bool = False
    metadata: Optional[Dict[str, Any]] = None


class TenantAccessRequest(BaseModel):
    user_id: str
    tenant_id: str
    requested_roles: List[str]
    justification: str
    expires_in_days: int = 30


class GrantTenantAccessRequest(BaseModel):
    user_id: str
    tenant_id: str
    role_names: List[str]


class BulkAccessRequest(BaseModel):
    user_ids: List[str]
    tenant_ids: List[str]
    roles: List[str]


class PermissionCheckRequest(BaseModel):
    resource: str
    level: str
    conditions: Optional[Dict[str, Any]] = None


def setup_rbac_routes(app, rbac_manager: TenantRBACManager,
                     cross_tenant_manager: CrossTenantUserManager,
                     rbac_deps: RBACDependencies):
    """Setup RBAC API routes."""

    router = APIRouter(prefix="/api/v1/rbac", tags=["RBAC"])

    # ============================================================================
    # Authentication Endpoints
    # ============================================================================

    @router.post("/auth/login", response_model=LoginResponse)
    async def login(
        request: LoginRequest,
        http_request: Request
    ):
        """Authenticate user and create tenant session."""
        try:
            # Authenticate user
            user_profile = rbac_manager.authenticate_user(
                request.username_or_email,
                request.password
            )

            if not user_profile:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # If tenant_id specified, create tenant session
            tenant_context = None
            if request.tenant_id:
                if request.tenant_id not in user_profile.tenant_access:
                    raise HTTPException(
                        status_code=403,
                        detail="User does not have access to specified tenant"
                    )

                # Create tenant session
                tenant_session = rbac_manager.create_tenant_session(
                    user_profile.user_id,
                    request.tenant_id,
                    ip_address=http_request.client.host,
                    user_agent=http_request.headers.get("user-agent")
                )

                if not tenant_session:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to create tenant session"
                    )

                # Generate JWT token
                access_token = rbac_manager.generate_jwt_token(tenant_session)

                tenant_context = {
                    "session_id": tenant_session.session_id,
                    "tenant_id": tenant_session.tenant_id,
                    "roles": tenant_session.roles,
                    "expires_at": tenant_session.expires_at.isoformat()
                }
            else:
                # Return user profile without tenant context
                access_token = "no_tenant_context"

            return LoginResponse(
                access_token=access_token,
                expires_in=28800,  # 8 hours
                user_profile={
                    "user_id": user_profile.user_id,
                    "username": user_profile.username,
                    "email": user_profile.email,
                    "full_name": user_profile.full_name,
                    "is_global_admin": user_profile.is_global_admin,
                    "tenant_access": user_profile.tenant_access
                },
                tenant_context=tenant_context
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise HTTPException(status_code=500, detail="Authentication service error")

    @router.post("/auth/switch-tenant")
    async def switch_tenant(
        tenant_id: str = Body(..., embed=True),
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context),
        http_request: Request = None
    ):
        """Switch to a different tenant context."""
        try:
            # Get user profile
            user_profile = rbac_manager.get_user_profile(tenant_context.user_id)

            if tenant_id not in user_profile.tenant_access:
                raise HTTPException(
                    status_code=403,
                    detail="User does not have access to specified tenant"
                )

            # Create new tenant session
            new_session = rbac_manager.create_tenant_session(
                tenant_context.user_id,
                tenant_id,
                ip_address=http_request.client.host,
                user_agent=http_request.headers.get("user-agent")
            )

            if not new_session:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create tenant session"
                )

            # Generate new JWT token
            access_token = rbac_manager.generate_jwt_token(new_session)

            return {
                "access_token": access_token,
                "tenant_id": tenant_id,
                "roles": new_session.roles,
                "expires_at": new_session.expires_at.isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Tenant switch error: {e}")
            raise HTTPException(status_code=500, detail="Failed to switch tenant")

    # ============================================================================
    # User Management Endpoints
    # ============================================================================

    @router.post("/users", dependencies=[Depends(rbac_deps.require_global_admin)])
    async def create_user(
        request: CreateUserRequest,
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Create a new user (Global admin only)."""
        try:
            user_id = rbac_manager.create_user(
                username=request.username,
                email=request.email,
                password=request.password,
                full_name=request.full_name,
                is_global_admin=request.is_global_admin,
                metadata=request.metadata
            )

            if not user_id:
                raise HTTPException(
                    status_code=400,
                    detail="User already exists or creation failed"
                )

            return {"user_id": user_id, "message": "User created successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise HTTPException(status_code=500, detail="Failed to create user")

    @router.get("/users/me")
    async def get_current_user_profile(
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Get current user's profile and access summary."""
        try:
            summary = cross_tenant_manager.get_cross_tenant_user_summary(
                tenant_context.user_id
            )

            if not summary:
                raise HTTPException(status_code=404, detail="User not found")

            return {
                "user_summary": {
                    "user_id": summary.user_id,
                    "username": summary.username,
                    "email": summary.email,
                    "full_name": summary.full_name,
                    "global_admin": summary.global_admin,
                    "total_tenants": summary.total_tenants,
                    "active_tenants": summary.active_tenants,
                    "created_at": summary.created_at.isoformat()
                },
                "current_tenant": {
                    "tenant_id": tenant_context.tenant_id,
                    "roles": tenant_context.roles
                },
                "all_tenant_access": summary.tenant_roles
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user profile error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user profile")

    @router.get("/users/{user_id}/report")
    async def get_user_access_report(
        user_id: str,
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Get comprehensive access report for a user."""
        try:
            report = cross_tenant_manager.generate_user_access_report(user_id)

            if not report:
                raise HTTPException(status_code=404, detail="User not found")

            return report

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User report error: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate user report")

    # ============================================================================
    # Tenant Access Management
    # ============================================================================

    @router.post("/access/grant")
    async def grant_tenant_access(
        request: GrantTenantAccessRequest,
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Grant user access to tenant with specified roles."""
        try:
            success = rbac_manager.grant_tenant_access(
                request.user_id,
                request.tenant_id,
                request.role_names,
                tenant_context.user_id
            )

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to grant tenant access"
                )

            return {"message": "Tenant access granted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Grant access error: {e}")
            raise HTTPException(status_code=500, detail="Failed to grant access")

    @router.post("/access/revoke")
    async def revoke_tenant_access(
        user_id: str = Body(...),
        tenant_id: str = Body(...),
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Revoke user's access to tenant."""
        try:
            success = rbac_manager.revoke_tenant_access(
                user_id,
                tenant_id,
                tenant_context.user_id
            )

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to revoke tenant access"
                )

            return {"message": "Tenant access revoked successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Revoke access error: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke access")

    @router.post("/access/request")
    async def request_tenant_access(
        request: TenantAccessRequest,
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Request access to a tenant."""
        try:
            request_id = cross_tenant_manager.request_tenant_access(
                request.user_id,
                request.tenant_id,
                request.requested_roles,
                request.justification,
                tenant_context.user_id,
                request.expires_in_days
            )

            return {
                "request_id": request_id,
                "message": "Access request submitted successfully"
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Access request error: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit access request")

    @router.post("/access/requests/{request_id}/approve")
    async def approve_access_request(
        request_id: str,
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Approve a tenant access request."""
        try:
            success = cross_tenant_manager.approve_access_request(
                request_id,
                tenant_context.user_id
            )

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to approve access request"
                )

            return {"message": "Access request approved successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Approve request error: {e}")
            raise HTTPException(status_code=500, detail="Failed to approve request")

    @router.post("/access/requests/{request_id}/reject")
    async def reject_access_request(
        request_id: str,
        reason: str = Body(..., embed=True),
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Reject a tenant access request."""
        try:
            success = cross_tenant_manager.reject_access_request(
                request_id,
                tenant_context.user_id,
                reason
            )

            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to reject access request"
                )

            return {"message": "Access request rejected successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Reject request error: {e}")
            raise HTTPException(status_code=500, detail="Failed to reject request")

    # ============================================================================
    # Permission and Role Management
    # ============================================================================

    @router.post("/permissions/check")
    async def check_permission(
        request: PermissionCheckRequest,
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """Check if current user has specific permission."""
        try:
            resource = ResourceType(request.resource)
            level = PermissionLevel(request.level)

            has_permission = rbac_manager.check_user_permission(
                tenant_context.user_id,
                tenant_context.tenant_id,
                resource,
                level,
                request.conditions
            )

            return {
                "has_permission": has_permission,
                "resource": request.resource,
                "level": request.level,
                "tenant_id": tenant_context.tenant_id
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid resource or level: {e}")
        except Exception as e:
            logger.error(f"Permission check error: {e}")
            raise HTTPException(status_code=500, detail="Failed to check permission")

    @router.get("/roles/templates")
    async def list_role_templates(
        include_non_assignable: bool = False,
        tenant_context: TenantContext = Depends(rbac_deps.get_current_tenant_context)
    ):
        """List available role templates."""
        try:
            templates = rbac_manager.role_manager.list_role_templates(include_non_assignable)

            return {
                "role_templates": [
                    {
                        "role_name": template.role_name,
                        "display_name": template.display_name,
                        "description": template.description,
                        "is_system_role": template.is_system_role,
                        "is_assignable": template.is_assignable,
                        "permissions": [
                            {
                                "resource": perm.resource.value,
                                "level": perm.level.value,
                                "conditions": perm.conditions
                            }
                            for perm in template.permissions
                        ]
                    }
                    for template in templates
                ]
            }

        except Exception as e:
            logger.error(f"List role templates error: {e}")
            raise HTTPException(status_code=500, detail="Failed to list role templates")

    # ============================================================================
    # Bulk Operations
    # ============================================================================

    @router.post("/bulk/grant-access")
    async def bulk_grant_access(
        request: BulkAccessRequest,
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Initiate bulk access grant operation."""
        try:
            from .cross_tenant_user_manager import BulkOperationType

            operation_id = cross_tenant_manager.initiate_bulk_operation(
                BulkOperationType.GRANT_ACCESS,
                request.user_ids,
                request.tenant_ids,
                {"roles": request.roles},
                tenant_context.user_id
            )

            # Execute the operation
            success = cross_tenant_manager.execute_bulk_grant_access(operation_id)

            return {
                "operation_id": operation_id,
                "success": success,
                "message": "Bulk access grant operation initiated"
            }

        except Exception as e:
            logger.error(f"Bulk grant access error: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate bulk operation")

    # ============================================================================
    # System Management
    # ============================================================================

    @router.get("/system/status")
    async def get_rbac_system_status(
        tenant_context: TenantContext = Depends(rbac_deps.require_global_admin)
    ):
        """Get RBAC system status and statistics."""
        try:
            # Clean up expired sessions and requests
            expired_sessions = rbac_manager.cleanup_expired_sessions()
            expired_requests = cross_tenant_manager.cleanup_expired_access_requests()

            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "cleanup": {
                    "expired_sessions_cleaned": expired_sessions,
                    "expired_requests_cleaned": expired_requests
                },
                "message": "RBAC system operational"
            }

        except Exception as e:
            logger.error(f"RBAC status error: {e}")
            raise HTTPException(status_code=500, detail="Failed to get system status")

    # Add router to app
    app.include_router(router)

    return router