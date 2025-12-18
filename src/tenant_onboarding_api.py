"""
Tenant Onboarding API Endpoints
Provides RESTful API for automated tenant registration and management.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging
from contextual_docs import context

from tenant_onboarding_models import (
    TenantRegistration, TenantRegistrationResponse, OnboardingStatusResponse,
    TenantListResponse, TenantDetailResponse, OnboardingWorkflow, TenantInfo,
    OnboardingStatus, TenantStatus, IndustryType, DatabaseType
)
from automated_provisioning import ProvisioningManager, TenantIDGenerator
from industry_schema_templates import IndustrySchemaTemplateManager
from tenant_rbac_manager import TenantRBACManager, get_current_user_with_tenant_check
from database_cloner import DatabaseCloner
from tenant_connection_manager import TenantConnectionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
provisioning_manager = None
template_manager = IndustrySchemaTemplateManager()
tenant_id_generator = TenantIDGenerator()

# Router setup
router = APIRouter(prefix="/api/v1/onboarding", tags=["Tenant Onboarding"])


def get_provisioning_manager() -> ProvisioningManager:
    """Get the provisioning manager instance."""
    global provisioning_manager
    if provisioning_manager is None:
        # Initialize with required dependencies
        # These would typically be injected via dependency injection
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Provisioning manager not initialized"
        )
    return provisioning_manager


def initialize_onboarding_api(
    db_cloner: DatabaseCloner,
    connection_manager: TenantConnectionManager,
    rbac_manager: TenantRBACManager
):
    """Initialize the onboarding API with required dependencies."""
    global provisioning_manager
    provisioning_manager = ProvisioningManager(
        database_cloner=db_cloner,
        connection_manager=connection_manager,
        rbac_manager=rbac_manager,
        template_manager=template_manager
    )


@router.post("/register-tenant", response_model=TenantRegistrationResponse)
async def register_tenant(
    registration: TenantRegistration,
    background_tasks: BackgroundTasks,
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
) -> TenantRegistrationResponse:
    """
    Register a new tenant for automated onboarding.

    This endpoint initiates the complete tenant onboarding workflow:
    1. Validates registration data
    2. Generates unique tenant ID
    3. Creates onboarding workflow
    4. Starts background provisioning process

    Args:
        registration: Tenant registration details
        background_tasks: FastAPI background tasks for async processing
        provisioning_mgr: Provisioning manager dependency

    Returns:
        TenantRegistrationResponse with workflow tracking information
    """
    try:
        logger.info(f"New tenant registration request for {registration.org_name}")

        # Validate registration data
        validation_result = await _validate_registration(registration)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration validation failed: {validation_result['errors']}"
            )

        # Generate unique tenant ID
        tenant_id = tenant_id_generator.generate_tenant_id(registration.org_name)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate unique tenant ID"
            )

        # Create onboarding workflow
        workflow = OnboardingWorkflow(
            tenant_id=tenant_id,
            registration_data=registration,
            submitted_at=datetime.utcnow(),
            current_status=OnboardingStatus.REGISTRATION,
            requires_approval=_requires_manual_approval(registration)
        )

        # Add initial status
        workflow.add_status_change(
            OnboardingStatus.VALIDATION,
            "Registration received and initial validation completed"
        )

        # Start background provisioning process
        background_tasks.add_task(
            _execute_provisioning_workflow,
            workflow,
            provisioning_mgr
        )

        # Calculate estimated completion time
        estimated_completion = _calculate_estimated_completion(registration)

        # Prepare response
        response = TenantRegistrationResponse(
            success=True,
            workflow_id=workflow.workflow_id,
            tenant_id=tenant_id,
            message=f"Tenant registration successful. Provisioning initiated for {registration.org_name}.",
            estimated_completion_time=estimated_completion,
            next_steps=[
                "Database clone creation in progress",
                "Admin user setup and RBAC configuration",
                "Industry-specific schema application",
                "Testing and validation",
                "Welcome email with access instructions"
            ],
            support_email="support@nlp2sql-platform.com",
            support_phone="+1-800-SUPPORT",
            status_check_url=f"/api/v1/onboarding/status/{workflow.workflow_id}"
        )

        logger.info(f"Tenant registration initiated: {tenant_id} (workflow: {workflow.workflow_id})")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tenant registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=OnboardingStatusResponse)
async def get_onboarding_status(
    workflow_id: str,
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
) -> OnboardingStatusResponse:
    """
    Get the current status of a tenant onboarding workflow.

    Args:
        workflow_id: Unique workflow identifier
        provisioning_mgr: Provisioning manager dependency

    Returns:
        OnboardingStatusResponse with current status and progress details
    """
    try:
        # Get workflow from provisioning manager
        workflow = await provisioning_mgr.get_workflow_status(workflow_id)
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )

        # Calculate progress percentage
        progress_percentage = _calculate_progress_percentage(workflow)

        # Determine current and next steps
        current_step = _get_current_step_description(workflow.current_status)
        next_step = _get_next_step_description(workflow.current_status)

        # Prepare response
        response = OnboardingStatusResponse(
            workflow_id=workflow_id,
            tenant_id=workflow.tenant_id,
            current_status=workflow.current_status,
            progress_percentage=progress_percentage,
            steps_completed=workflow.steps_completed,
            current_step=current_step,
            next_step=next_step,
            started_at=workflow.started_at or workflow.submitted_at,
            estimated_completion=workflow.estimated_completion,
            tenant_config=workflow.tenant_config,
            access_instructions=_get_access_instructions(workflow) if workflow.current_status == OnboardingStatus.COMPLETED else None,
            errors=workflow.error_messages,
            last_error=workflow.error_messages[-1] if workflow.error_messages else None
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve status: {str(e)}"
        )


@router.get("/tenants", response_model=TenantListResponse)
async def list_tenants(
    page: int = 1,
    page_size: int = 20,
    industry: Optional[IndustryType] = None,
    status: Optional[TenantStatus] = None,
    database_type: Optional[DatabaseType] = None,
    current_user = Depends(get_current_user_with_tenant_check),
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
) -> TenantListResponse:
    """
    List all tenants with optional filtering and pagination.

    Args:
        page: Page number (1-based)
        page_size: Number of tenants per page
        industry: Filter by industry type
        status: Filter by tenant status
        database_type: Filter by database type
        current_user: Current authenticated user
        provisioning_mgr: Provisioning manager dependency

    Returns:
        TenantListResponse with paginated tenant list and summary statistics
    """
    try:
        # Check if user has permission to list tenants
        if not _has_tenant_management_permission(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list tenants"
            )

        # Get tenant list from provisioning manager
        filters = {}
        if industry:
            filters["industry"] = industry
        if status:
            filters["status"] = status
        if database_type:
            filters["database_type"] = database_type

        tenants, total_count = await provisioning_mgr.list_tenants(
            page=page,
            page_size=page_size,
            filters=filters
        )

        # Generate summary statistics
        status_summary = await provisioning_mgr.get_tenant_status_summary()
        industry_summary = await provisioning_mgr.get_tenant_industry_summary()
        region_summary = await provisioning_mgr.get_tenant_region_summary()

        response = TenantListResponse(
            tenants=tenants,
            total_count=total_count,
            page=page,
            page_size=page_size,
            status_summary=status_summary,
            industry_summary=industry_summary,
            region_summary=region_summary
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list tenants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tenant list: {str(e)}"
        )


@router.get("/tenant/{tenant_id}", response_model=TenantDetailResponse)
async def get_tenant_details(
    tenant_id: str,
    current_user = Depends(get_current_user_with_tenant_check),
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
) -> TenantDetailResponse:
    """
    Get detailed information about a specific tenant.

    Args:
        tenant_id: Unique tenant identifier
        current_user: Current authenticated user
        provisioning_mgr: Provisioning manager dependency

    Returns:
        TenantDetailResponse with comprehensive tenant information
    """
    try:
        # Check permissions
        if not _has_tenant_access_permission(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to access tenant details"
            )

        # Get tenant details
        tenant_info = await provisioning_mgr.get_tenant_info(tenant_id)
        if not tenant_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )

        # Get additional details
        resource_usage = await provisioning_mgr.get_tenant_resource_usage(tenant_id)
        billing_info = await provisioning_mgr.get_tenant_billing_info(tenant_id)
        recent_activity = await provisioning_mgr.get_tenant_recent_activity(tenant_id)
        alerts = await provisioning_mgr.get_tenant_alerts(tenant_id)

        # Get configuration details
        database_config = await provisioning_mgr.get_tenant_database_config(tenant_id)
        rbac_config = await provisioning_mgr.get_tenant_rbac_config(tenant_id)
        compliance_status = await provisioning_mgr.get_tenant_compliance_status(tenant_id)

        response = TenantDetailResponse(
            tenant_info=tenant_info,
            resource_usage=resource_usage,
            billing_info=billing_info,
            recent_activity=recent_activity,
            alerts=alerts,
            database_config=database_config,
            rbac_config=rbac_config,
            compliance_status=compliance_status
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tenant details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve tenant details: {str(e)}"
        )


@router.post("/tenant/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: str,
    current_user = Depends(get_current_user_with_tenant_check),
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
):
    """
    Manually activate a tenant (for cases requiring approval).

    Args:
        tenant_id: Unique tenant identifier
        current_user: Current authenticated user
        provisioning_mgr: Provisioning manager dependency
    """
    try:
        # Check permissions
        if not _has_tenant_activation_permission(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to activate tenant"
            )

        # Activate tenant
        success = await provisioning_mgr.activate_tenant(tenant_id, current_user.user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to activate tenant {tenant_id}"
            )

        return {"message": f"Tenant {tenant_id} activated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate tenant: {str(e)}"
        )


@router.post("/tenant/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    reason: str,
    current_user = Depends(get_current_user_with_tenant_check),
    provisioning_mgr: ProvisioningManager = Depends(get_provisioning_manager)
):
    """
    Suspend a tenant's access.

    Args:
        tenant_id: Unique tenant identifier
        reason: Reason for suspension
        current_user: Current authenticated user
        provisioning_mgr: Provisioning manager dependency
    """
    try:
        # Check permissions
        if not _has_tenant_management_permission(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to suspend tenant"
            )

        # Suspend tenant
        success = await provisioning_mgr.suspend_tenant(tenant_id, reason, current_user.user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to suspend tenant {tenant_id}"
            )

        return {"message": f"Tenant {tenant_id} suspended successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suspend tenant: {str(e)}"
        )


@router.get("/industry-templates", response_model=List[Dict[str, Any]])
async def get_industry_templates(
    current_user = Depends(get_current_user_with_tenant_check)
) -> List[Dict[str, Any]]:
    """
    Get available industry templates and their compliance requirements.

    Args:
        current_user: Current authenticated user

    Returns:
        List of industry templates with compliance information
    """
    try:
        templates = []

        for industry in IndustryType:
            template = template_manager.get_template(industry)
            template_info = {
                "industry": industry.value,
                "template_name": template.template_name,
                "template_version": template.template_version,
                "compliance_frameworks": [cf.value for cf in template.compliance_frameworks],
                "additional_tables_count": len(template.additional_tables),
                "additional_roles_count": len(template.additional_roles),
                "security_level": template.security_requirements.get("access_controls", "basic"),
                "setup_guide_url": template.setup_guide_url,
                "compliance_checklist_items": len(template.compliance_checklist)
            }
            templates.append(template_info)

        return templates

    except Exception as e:
        logger.error(f"Failed to get industry templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve industry templates: {str(e)}"
        )


# Helper Functions

async def _validate_registration(registration: TenantRegistration) -> Dict[str, Any]:
    """Validate tenant registration data."""
    errors = []

    # Validate organization name uniqueness
    if await _organization_name_exists(registration.org_name):
        errors.append("Organization name already exists")

    # Validate org code uniqueness if provided
    if registration.org_code and await _organization_code_exists(registration.org_code):
        errors.append("Organization code already exists")

    # Validate admin email uniqueness
    if await _admin_email_exists(registration.admin_email):
        errors.append("Admin email already registered")

    # Validate custom domain if provided
    if registration.custom_domain and await _custom_domain_exists(registration.custom_domain):
        errors.append("Custom domain already in use")

    # Validate resource requirements
    if registration.expected_users > 1000 and registration.security_level == "basic":
        errors.append("High user count requires elevated security level")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def _requires_manual_approval(registration: TenantRegistration) -> bool:
    """Determine if registration requires manual approval."""
    # Require approval for:
    # - High compliance requirements
    # - Large user counts
    # - Government or healthcare industries
    # - Custom domains

    high_compliance = any(
        cf in [ComplianceFramework.HIPAA, ComplianceFramework.SOX, ComplianceFramework.FISMA]
        for cf in registration.compliance_requirements
    )

    large_deployment = (
        registration.expected_users > 500 or
        registration.storage_requirements_gb > 1000
    )

    sensitive_industry = registration.industry in [
        IndustryType.HEALTHCARE,
        IndustryType.FINANCE,
        IndustryType.GOVERNMENT
    ]

    return high_compliance or large_deployment or sensitive_industry or registration.custom_domain is not None


def _calculate_estimated_completion(registration: TenantRegistration) -> str:
    """Calculate estimated completion time for onboarding."""
    base_time_minutes = 30  # Base onboarding time

    # Add time for complexity factors
    if registration.industry == IndustryType.HEALTHCARE:
        base_time_minutes += 15
    elif registration.industry == IndustryType.FINANCE:
        base_time_minutes += 20
    elif registration.industry == IndustryType.GOVERNMENT:
        base_time_minutes += 25

    if registration.compliance_requirements:
        base_time_minutes += len(registration.compliance_requirements) * 5

    if registration.expected_users > 100:
        base_time_minutes += 10

    if registration.custom_domain:
        base_time_minutes += 10

    completion_time = datetime.utcnow() + timedelta(minutes=base_time_minutes)
    return completion_time.strftime("%Y-%m-%d %H:%M:%S UTC")


async def _execute_provisioning_workflow(
    workflow: OnboardingWorkflow,
    provisioning_mgr: ProvisioningManager
):
    """Execute the provisioning workflow in the background."""
    try:
        success = await provisioning_mgr.execute_onboarding_workflow(workflow)
        if success:
            logger.info(f"Provisioning completed successfully for tenant {workflow.tenant_id}")
        else:
            logger.error(f"Provisioning failed for tenant {workflow.tenant_id}")
    except Exception as e:
        logger.error(f"Provisioning workflow error: {str(e)}")


def _calculate_progress_percentage(workflow: OnboardingWorkflow) -> int:
    """Calculate progress percentage based on completed steps."""
    total_steps = len(OnboardingStatus)
    current_step_value = list(OnboardingStatus).index(workflow.current_status)

    if workflow.current_status == OnboardingStatus.COMPLETED:
        return 100
    elif workflow.current_status == OnboardingStatus.FAILED:
        return 0

    return int((current_step_value / total_steps) * 100)


def _get_current_step_description(status: OnboardingStatus) -> str:
    """Get human-readable description of current step."""
    descriptions = {
        OnboardingStatus.REGISTRATION: "Processing registration",
        OnboardingStatus.VALIDATION: "Validating tenant data",
        OnboardingStatus.CLONE_CREATION: "Creating database clone",
        OnboardingStatus.USER_SETUP: "Setting up admin user",
        OnboardingStatus.RBAC_CONFIGURATION: "Configuring access controls",
        OnboardingStatus.TESTING: "Testing tenant configuration",
        OnboardingStatus.ACTIVATION: "Activating tenant",
        OnboardingStatus.WELCOME_EMAIL: "Sending welcome email",
        OnboardingStatus.COMPLETED: "Onboarding completed",
        OnboardingStatus.FAILED: "Onboarding failed"
    }
    return descriptions.get(status, "Unknown step")


def _get_next_step_description(status: OnboardingStatus) -> Optional[str]:
    """Get description of next step in workflow."""
    status_list = list(OnboardingStatus)
    try:
        current_index = status_list.index(status)
        if current_index < len(status_list) - 1:
            next_status = status_list[current_index + 1]
            return _get_current_step_description(next_status)
    except ValueError:
        pass
    return None


def _get_access_instructions(workflow: OnboardingWorkflow) -> Dict[str, Any]:
    """Get access instructions for completed tenant."""
    if workflow.tenant_config:
        return {
            "tenant_id": workflow.tenant_id,
            "admin_username": workflow.tenant_config.admin_user_id,
            "database_type": workflow.registration_data.database_type.value,
            "connection_url": f"https://app.nlp2sql-platform.com/tenant/{workflow.tenant_id}",
            "api_base_url": f"https://api.nlp2sql-platform.com/v1/tenant/{workflow.tenant_id}",
            "setup_guide": template_manager.get_template(workflow.registration_data.industry).setup_guide_url
        }
    return {}


# Permission helper functions
def _has_tenant_management_permission(user) -> bool:
    """Check if user has tenant management permissions."""
    return "tenant_management" in getattr(user, "permissions", []) or "admin" in getattr(user, "roles", [])


def _has_tenant_access_permission(user, tenant_id: str) -> bool:
    """Check if user has access to specific tenant."""
    return (
        _has_tenant_management_permission(user) or
        getattr(user, "tenant_id", None) == tenant_id
    )


def _has_tenant_activation_permission(user) -> bool:
    """Check if user can activate tenants."""
    return "tenant_activation" in getattr(user, "permissions", []) or "admin" in getattr(user, "roles", [])


# Async validation helpers (these would connect to actual data stores)
async def _organization_name_exists(org_name: str) -> bool:
    """Check if organization name already exists."""
    # Implementation would check database
    return False


async def _organization_code_exists(org_code: str) -> bool:
    """Check if organization code already exists."""
    # Implementation would check database
    return False


async def _admin_email_exists(admin_email: str) -> bool:
    """Check if admin email already exists."""
    # Implementation would check database
    return False


async def _custom_domain_exists(custom_domain: str) -> bool:
    """Check if custom domain already exists."""
    # Implementation would check database
    return False