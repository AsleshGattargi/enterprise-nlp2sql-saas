"""
Database Cloning API Integration for FastAPI
Extends the main FastAPI application with tenant database cloning endpoints.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, status as status_module
from pydantic import BaseModel, Field

from .database_cloner import DatabaseCloner, CloneStatus, TenantClone
from .clone_verifier import CloneVerificationResult
from .port_manager import PortManager
from .docker_manager import DockerManager
from .auth import get_admin_user  # Assuming admin auth is required for cloning

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses

class CloneRequest(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier")
    database_type: str = Field(..., description="Database type (mysql, postgresql, sqlite, mongodb)")
    root_version: Optional[str] = Field(None, description="Root schema version (defaults to latest)")
    custom_config: Optional[Dict[str, Any]] = Field(None, description="Custom configuration options")

class CloneResponse(BaseModel):
    success: bool
    message: str
    clone_id: Optional[str] = None
    tenant_id: str
    database_type: str
    status: str
    connection_params: Optional[Dict[str, Any]] = None
    port: Optional[int] = None
    container_id: Optional[str] = None
    created_at: Optional[datetime] = None

class VerificationResponse(BaseModel):
    tenant_id: str
    is_verified: bool
    checks_passed: int
    total_checks: int
    isolation_verified: bool
    schema_integrity: bool
    connection_test: bool
    error_messages: List[str]
    verification_details: Optional[Dict[str, Any]] = None

class CloneListResponse(BaseModel):
    tenant_id: Optional[str]
    clones: List[Dict[str, Any]]
    total_count: int

class CloneStatusResponse(BaseModel):
    tenant_id: str
    clone_id: str
    status: str
    database_type: str
    root_version: str
    database_name: str
    port: Optional[int]
    container_id: Optional[str]
    connection_params: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

class PortAllocationResponse(BaseModel):
    database_type: str
    allocated_ports: List[Dict[str, Any]]
    available_ports: List[int]
    port_statistics: Dict[str, Any]

class SystemStatusResponse(BaseModel):
    total_clones: int
    active_clones: int
    failed_clones: int
    docker_info: Dict[str, Any]
    port_statistics: Dict[str, Any]

# Initialize cloning components
database_cloner = DatabaseCloner()
port_manager = PortManager()
docker_manager = DockerManager()

# Create API router
cloning_router = APIRouter(prefix="/api/v1/cloning", tags=["Database Cloning"])

@cloning_router.post("/create", response_model=CloneResponse)
async def create_tenant_clone(
    request: CloneRequest,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Create a new tenant database clone from root image.
    Requires admin privileges.
    """
    try:
        logger.info(f"Creating clone for tenant {request.tenant_id} by user {current_user['user_id']}")

        # Validate database type
        valid_types = ['mysql', 'postgresql', 'sqlite', 'mongodb']
        if request.database_type.lower() not in valid_types:
            raise HTTPException(
                status_code=status_module.HTTP_400_BAD_REQUEST,
                detail=f"Invalid database type. Must be one of: {', '.join(valid_types)}"
            )

        # Check if tenant already has an active clone
        existing_clones = database_cloner.list_tenant_clones(request.tenant_id)
        active_clones = [c for c in existing_clones if c.status == CloneStatus.COMPLETED]

        if active_clones:
            logger.warning(f"Tenant {request.tenant_id} already has active clones")
            raise HTTPException(
                status_code=status_module.HTTP_409_CONFLICT,
                detail=f"Tenant {request.tenant_id} already has an active database clone"
            )

        # Create the clone
        success, message, clone = database_cloner.clone_from_root(
            tenant_id=request.tenant_id,
            db_type=request.database_type,
            root_version=request.root_version,
            custom_config=request.custom_config
        )

        if not success:
            logger.error(f"Clone creation failed: {message}")
            raise HTTPException(
                status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Clone creation failed: {message}"
            )

        # Return clone information
        response_data = {
            "success": True,
            "message": message,
            "clone_id": clone.clone_id,
            "tenant_id": clone.tenant_id,
            "database_type": clone.database_type.value,
            "status": clone.status.value,
            "connection_params": clone.connection_params,
            "port": clone.port,
            "container_id": clone.container_id,
            "created_at": clone.created_at
        }

        logger.info(f"Clone created successfully for tenant {request.tenant_id}")
        return CloneResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating clone: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during clone creation"
        )

@cloning_router.get("/verify/{tenant_id}", response_model=VerificationResponse)
async def verify_tenant_isolation(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Verify tenant database isolation and integrity.
    """
    try:
        logger.info(f"Verifying isolation for tenant {tenant_id}")

        # Run verification
        verification_result = database_cloner.verify_clone_isolation(tenant_id)

        # Prepare detailed verification info
        verification_details = {
            "isolation_tests": [
                {
                    "test_name": test.test_name,
                    "passed": test.passed,
                    "details": test.details,
                    "execution_time_ms": test.execution_time_ms
                }
                for test in verification_result.isolation_tests
            ]
        }

        if verification_result.schema_comparison:
            verification_details["schema_comparison"] = {
                "tables_match": verification_result.schema_comparison.tables_match,
                "indexes_match": verification_result.schema_comparison.indexes_match,
                "constraints_match": verification_result.schema_comparison.constraints_match,
                "missing_tables": verification_result.schema_comparison.missing_tables,
                "extra_tables": verification_result.schema_comparison.extra_tables,
                "missing_indexes": verification_result.schema_comparison.missing_indexes,
                "constraint_differences": verification_result.schema_comparison.constraint_differences
            }

        response_data = {
            "tenant_id": tenant_id,
            "is_verified": verification_result.is_verified,
            "checks_passed": verification_result.checks_passed,
            "total_checks": verification_result.total_checks,
            "isolation_verified": verification_result.isolation_verified,
            "schema_integrity": verification_result.schema_integrity,
            "connection_test": verification_result.connection_test,
            "error_messages": verification_result.error_messages,
            "verification_details": verification_details
        }

        logger.info(f"Verification completed for tenant {tenant_id}: {verification_result.checks_passed}/{verification_result.total_checks} checks passed")
        return VerificationResponse(**response_data)

    except Exception as e:
        logger.error(f"Verification error for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification process failed"
        )

@cloning_router.get("/list", response_model=CloneListResponse)
async def list_tenant_clones(
    tenant_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    List tenant clones with optional filtering by tenant ID.
    """
    try:
        clones = database_cloner.list_tenant_clones(tenant_id)

        clone_data = []
        for clone in clones:
            clone_info = {
                "clone_id": clone.clone_id,
                "tenant_id": clone.tenant_id,
                "database_type": clone.database_type.value,
                "root_version": clone.root_version,
                "database_name": clone.database_name,
                "status": clone.status.value,
                "port": clone.port,
                "container_id": clone.container_id,
                "created_at": clone.created_at.isoformat(),
                "completed_at": clone.completed_at.isoformat() if clone.completed_at else None,
                "error_message": clone.error_message
            }
            clone_data.append(clone_info)

        return CloneListResponse(
            tenant_id=tenant_id,
            clones=clone_data,
            total_count=len(clone_data)
        )

    except Exception as e:
        logger.error(f"Error listing clones: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clone list"
        )

@cloning_router.get("/status/{tenant_id}", response_model=CloneStatusResponse)
async def get_tenant_clone_status(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Get detailed status of a tenant's database clone.
    """
    try:
        clones = database_cloner.list_tenant_clones(tenant_id)
        if not clones:
            raise HTTPException(
                status_code=status_module.HTTP_404_NOT_FOUND,
                detail=f"No clones found for tenant {tenant_id}"
            )

        # Get the most recent clone
        latest_clone = max(clones, key=lambda c: c.created_at)

        return CloneStatusResponse(
            tenant_id=latest_clone.tenant_id,
            clone_id=latest_clone.clone_id,
            status=latest_clone.status.value,
            database_type=latest_clone.database_type.value,
            root_version=latest_clone.root_version,
            database_name=latest_clone.database_name,
            port=latest_clone.port,
            container_id=latest_clone.container_id,
            connection_params=latest_clone.connection_params,
            created_at=latest_clone.created_at,
            completed_at=latest_clone.completed_at,
            error_message=latest_clone.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clone status: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clone status"
        )

@cloning_router.post("/start/{tenant_id}")
async def start_tenant_database(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Start a tenant's database container.
    """
    try:
        success = database_cloner.start_tenant_database(tenant_id)

        if success:
            return {"success": True, "message": f"Database started for tenant {tenant_id}"}
        else:
            raise HTTPException(
                status_code=status_module.HTTP_400_BAD_REQUEST,
                detail=f"Failed to start database for tenant {tenant_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting tenant database: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start tenant database"
        )

@cloning_router.post("/stop/{tenant_id}")
async def stop_tenant_database(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Stop a tenant's database container.
    """
    try:
        success = database_cloner.stop_tenant_database(tenant_id)

        if success:
            return {"success": True, "message": f"Database stopped for tenant {tenant_id}"}
        else:
            raise HTTPException(
                status_code=status_module.HTTP_400_BAD_REQUEST,
                detail=f"Failed to stop database for tenant {tenant_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping tenant database: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop tenant database"
        )

@cloning_router.delete("/remove/{tenant_id}")
async def remove_tenant_clone(
    tenant_id: str,
    force: bool = False,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Remove a tenant's database clone and all associated resources.
    """
    try:
        success = database_cloner.remove_tenant_clone(tenant_id, force=force)

        if success:
            return {"success": True, "message": f"Clone removed for tenant {tenant_id}"}
        else:
            raise HTTPException(
                status_code=status_module.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove clone for tenant {tenant_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing tenant clone: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove tenant clone"
        )

@cloning_router.get("/ports", response_model=PortAllocationResponse)
async def get_port_allocations(
    database_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Get port allocation information for database containers.
    """
    try:
        from .root_image_manager import DatabaseType

        db_type = None
        if database_type:
            try:
                db_type = DatabaseType(database_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status_module.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid database type: {database_type}"
                )

        # Get allocated ports
        allocated_ports = port_manager.get_allocated_ports(db_type, active_only=True)

        allocated_data = []
        for allocation in allocated_ports:
            allocated_data.append({
                "port": allocation.port,
                "database_type": allocation.database_type.value,
                "tenant_id": allocation.tenant_id,
                "container_id": allocation.container_id,
                "allocated_at": allocation.allocated_at,
                "is_active": allocation.is_active
            })

        # Get available ports
        available_ports = []
        if db_type:
            for port in range(*port_manager.port_ranges[db_type]):
                if not port_manager.is_port_in_use(port):
                    available_ports.append(port)
                if len(available_ports) >= 10:  # Limit to first 10 available
                    break

        # Get statistics
        port_statistics = port_manager.get_port_statistics()

        return PortAllocationResponse(
            database_type=database_type or "all",
            allocated_ports=allocated_data,
            available_ports=available_ports,
            port_statistics=port_statistics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting port allocations: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve port allocations"
        )

@cloning_router.get("/system/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Get overall system status for database cloning.
    """
    try:
        # Get clone statistics
        all_clones = database_cloner.list_tenant_clones()
        total_clones = len(all_clones)
        active_clones = len([c for c in all_clones if c.status == CloneStatus.COMPLETED])
        failed_clones = len([c for c in all_clones if c.status == CloneStatus.FAILED])

        # Get Docker system info
        docker_info = docker_manager.get_system_info()

        # Get port statistics
        port_statistics = port_manager.get_port_statistics()

        return SystemStatusResponse(
            total_clones=total_clones,
            active_clones=active_clones,
            failed_clones=failed_clones,
            docker_info=docker_info,
            port_statistics=port_statistics
        )

    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )

@cloning_router.post("/cleanup")
async def cleanup_resources(
    cleanup_inactive: bool = True,
    max_age_hours: int = 24,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Cleanup old and inactive cloning resources.
    """
    try:
        logger.info(f"Starting resource cleanup by user {current_user['user_id']}")

        results = {
            "port_allocations_cleaned": 0,
            "inactive_clones_found": 0,
            "cleanup_errors": []
        }

        # Cleanup inactive port allocations
        if cleanup_inactive:
            cleaned_ports = port_manager.cleanup_inactive_allocations(max_age_hours)
            results["port_allocations_cleaned"] = cleaned_ports

        # Find inactive clones
        all_clones = database_cloner.list_tenant_clones()
        inactive_clones = [c for c in all_clones if c.status in [CloneStatus.FAILED, CloneStatus.REMOVED]]
        results["inactive_clones_found"] = len(inactive_clones)

        logger.info(f"Cleanup completed: {results}")

        return {
            "success": True,
            "message": "Resource cleanup completed",
            "results": results
        }

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Resource cleanup failed"
        )

@cloning_router.get("/connection/{tenant_id}")
async def get_tenant_connection_params(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Get connection parameters for a tenant's database.
    Returns sanitized connection info (without passwords).
    """
    try:
        connection_params = database_cloner.get_tenant_connection_params(tenant_id)

        if not connection_params:
            raise HTTPException(
                status_code=status_module.HTTP_404_NOT_FOUND,
                detail=f"No active database found for tenant {tenant_id}"
            )

        # Sanitize connection parameters (remove sensitive info)
        sanitized_params = connection_params.copy()
        sensitive_keys = ['password', 'root_password', 'admin_password']

        for key in sensitive_keys:
            if key in sanitized_params:
                sanitized_params[key] = "***REDACTED***"

        # Also sanitize URI passwords
        if 'uri' in sanitized_params:
            uri = sanitized_params['uri']
            if '@' in uri and '://' in uri:
                # Replace password in URI
                protocol, rest = uri.split('://', 1)
                if '@' in rest:
                    credentials, host_part = rest.split('@', 1)
                    if ':' in credentials:
                        username, _ = credentials.split(':', 1)
                        sanitized_params['uri'] = f"{protocol}://{username}:***REDACTED***@{host_part}"

        return {
            "tenant_id": tenant_id,
            "connection_params": sanitized_params,
            "note": "Sensitive information has been redacted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection params: {e}")
        raise HTTPException(
            status_code=status_module.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection parameters"
        )

# Function to integrate with main FastAPI app
def setup_cloning_routes(app):
    """
    Add cloning routes to the main FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.include_router(cloning_router)
    logger.info("Database cloning routes integrated with FastAPI app")