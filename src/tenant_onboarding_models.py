"""
Tenant Onboarding Data Models and Core Types
Defines data structures for automated tenant provisioning and management.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import re
import uuid


class DatabaseType(str, Enum):
    """Supported database types for tenant provisioning."""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class IndustryType(str, Enum):
    """Industry types with specific compliance requirements."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    RETAIL = "retail"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    GENERAL = "general"


class DataRegion(str, Enum):
    """Data residency regions for compliance."""
    US_EAST = "us-east"
    US_WEST = "us-west"
    EU_CENTRAL = "eu-central"
    APAC = "asia-pacific"
    CANADA = "canada"
    UK = "united-kingdom"
    AUSTRALIA = "australia"


class ComplianceFramework(str, Enum):
    """Compliance frameworks and standards."""
    HIPAA = "hipaa"
    SOX = "sox"
    GDPR = "gdpr"
    PCI_DSS = "pci-dss"
    FERPA = "ferpa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    CCPA = "ccpa"
    FISMA = "fisma"


class TenantStatus(str, Enum):
    """Tenant lifecycle status."""
    PENDING = "pending"
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"
    DEACTIVATED = "deactivated"
    ARCHIVED = "archived"


class OnboardingStatus(str, Enum):
    """Onboarding workflow status."""
    REGISTRATION = "registration"
    VALIDATION = "validation"
    CLONE_CREATION = "clone_creation"
    USER_SETUP = "user_setup"
    RBAC_CONFIGURATION = "rbac_configuration"
    TESTING = "testing"
    ACTIVATION = "activation"
    WELCOME_EMAIL = "welcome_email"
    COMPLETED = "completed"
    FAILED = "failed"


class TenantRegistration(BaseModel):
    """Tenant registration request model."""

    # Organization Details
    org_name: str = Field(..., min_length=2, max_length=100, description="Organization name")
    org_code: Optional[str] = Field(None, max_length=20, description="Optional organization code")
    industry: IndustryType = Field(..., description="Industry type for compliance and templates")

    # Database Configuration
    database_type: DatabaseType = Field(..., description="Primary database type")
    data_region: DataRegion = Field(..., description="Data residency region")

    # Admin User Details
    admin_email: EmailStr = Field(..., description="Primary administrator email")
    admin_name: str = Field(..., min_length=2, max_length=100, description="Administrator full name")
    admin_phone: Optional[str] = Field(None, description="Administrator phone number")

    # Compliance and Security
    compliance_requirements: List[ComplianceFramework] = Field(
        default=[], description="Required compliance frameworks"
    )
    security_level: str = Field(default="standard", description="Security level: basic, standard, high")

    # Technical Configuration
    expected_users: int = Field(default=10, ge=1, le=10000, description="Expected number of users")
    expected_queries_per_day: int = Field(default=1000, ge=1, description="Expected daily query volume")
    storage_requirements_gb: int = Field(default=10, ge=1, le=10000, description="Storage requirements in GB")

    # Optional Configuration
    custom_domain: Optional[str] = Field(None, description="Custom domain for tenant")
    timezone: str = Field(default="UTC", description="Default timezone")
    notification_emails: List[EmailStr] = Field(default=[], description="Additional notification emails")

    # Metadata
    referral_source: Optional[str] = Field(None, description="How they found the service")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")

    @validator('org_name')
    def validate_org_name(cls, v):
        """Validate organization name."""
        if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', v):
            raise ValueError('Organization name contains invalid characters')
        return v.strip()

    @validator('org_code')
    def validate_org_code(cls, v):
        """Validate organization code."""
        if v and not re.match(r'^[A-Z0-9\-_]+$', v):
            raise ValueError('Organization code must contain only uppercase letters, numbers, hyphens, and underscores')
        return v

    @validator('admin_phone')
    def validate_phone(cls, v):
        """Validate phone number format."""
        if v and not re.match(r'^\+?[1-9]\d{1,14}$', v.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')):
            raise ValueError('Invalid phone number format')
        return v

    @validator('custom_domain')
    def validate_domain(cls, v):
        """Validate custom domain format."""
        if v and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$', v):
            raise ValueError('Invalid domain format')
        return v.lower() if v else v


class TenantConfiguration(BaseModel):
    """Complete tenant configuration after processing registration."""

    # Generated Identifiers
    tenant_id: str = Field(..., description="Generated tenant identifier")
    tenant_uuid: str = Field(..., description="Unique tenant UUID")

    # Database Configuration
    database_config: Dict[str, Any] = Field(..., description="Database connection configuration")
    connection_string: str = Field(..., description="Database connection string")

    # Resource Allocation
    allocated_port: int = Field(..., description="Allocated database port")
    container_name: str = Field(..., description="Docker container name")
    volume_path: str = Field(..., description="Data volume path")

    # RBAC Configuration
    admin_user_id: str = Field(..., description="Created admin user ID")
    role_assignments: Dict[str, List[str]] = Field(..., description="Role assignments")

    # Industry-Specific Configuration
    schema_template: str = Field(..., description="Applied schema template")
    compliance_config: Dict[str, Any] = Field(..., description="Compliance configuration")

    # Resource Limits
    resource_limits: Dict[str, Any] = Field(..., description="Resource limits and quotas")

    # Monitoring and Alerting
    monitoring_config: Dict[str, Any] = Field(..., description="Monitoring configuration")
    alert_recipients: List[str] = Field(..., description="Alert recipient emails")


class OnboardingWorkflow(BaseModel):
    """Onboarding workflow tracking."""

    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = Field(None, description="Assigned tenant ID")

    # Request Information
    registration_data: TenantRegistration = Field(..., description="Original registration data")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_by: Optional[str] = Field(None, description="User who submitted request")

    # Workflow Status
    current_status: OnboardingStatus = Field(default=OnboardingStatus.REGISTRATION)
    status_history: List[Dict[str, Any]] = Field(default=[], description="Status change history")

    # Progress Tracking
    steps_completed: List[str] = Field(default=[], description="Completed workflow steps")
    steps_failed: List[str] = Field(default=[], description="Failed workflow steps")
    error_messages: List[str] = Field(default=[], description="Error messages")

    # Timing Information
    started_at: Optional[datetime] = Field(None, description="Workflow start time")
    completed_at: Optional[datetime] = Field(None, description="Workflow completion time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

    # Configuration Results
    tenant_config: Optional[TenantConfiguration] = Field(None, description="Generated tenant configuration")

    # Approval Workflow (if required)
    requires_approval: bool = Field(default=False, description="Requires manual approval")
    approved_by: Optional[str] = Field(None, description="Approver user ID")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")
    approval_notes: Optional[str] = Field(None, description="Approval notes")

    def add_status_change(self, new_status: OnboardingStatus, message: str = "", error: bool = False):
        """Add status change to history."""
        self.status_history.append({
            "status": new_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "error": error
        })
        self.current_status = new_status

    def add_completed_step(self, step: str):
        """Mark step as completed."""
        if step not in self.steps_completed:
            self.steps_completed.append(step)

    def add_error(self, step: str, error_message: str):
        """Add error for a step."""
        if step not in self.steps_failed:
            self.steps_failed.append(step)
        self.error_messages.append(f"{step}: {error_message}")


class TenantInfo(BaseModel):
    """Complete tenant information for management."""

    # Basic Information
    tenant_id: str
    tenant_uuid: str
    org_name: str
    org_code: Optional[str]
    industry: IndustryType

    # Status and Lifecycle
    status: TenantStatus
    created_at: datetime
    activated_at: Optional[datetime]
    last_activity: Optional[datetime]

    # Technical Configuration
    database_type: DatabaseType
    data_region: DataRegion
    allocated_resources: Dict[str, Any]

    # User and Access Information
    admin_user_id: str
    admin_email: str
    total_users: int
    active_users: int

    # Usage Statistics
    usage_stats: Dict[str, Any] = Field(default={})
    billing_info: Dict[str, Any] = Field(default={})

    # Compliance and Security
    compliance_frameworks: List[ComplianceFramework]
    security_level: str
    last_security_audit: Optional[datetime]

    # Support and Notifications
    notification_emails: List[str]
    support_tier: str = Field(default="standard")

    # Metadata
    tags: List[str] = Field(default=[])
    notes: Optional[str] = None


class TenantResourceUsage(BaseModel):
    """Tenant resource usage metrics."""

    tenant_id: str
    measurement_time: datetime = Field(default_factory=datetime.utcnow)

    # Database Metrics
    database_size_mb: float
    connection_count: int
    query_count_24h: int
    avg_query_time_ms: float

    # Storage Metrics
    storage_used_gb: float
    storage_limit_gb: float
    backup_size_gb: float

    # User Metrics
    active_users_24h: int
    total_sessions_24h: int
    concurrent_users_peak: int

    # Performance Metrics
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_io_mb_per_sec: float
    network_io_mb_per_sec: float

    # Cost Metrics
    estimated_daily_cost: float
    total_cost_month_to_date: float


class IndustryTemplate(BaseModel):
    """Industry-specific configuration template."""

    industry: IndustryType
    template_name: str
    template_version: str

    # Schema Modifications
    additional_tables: List[Dict[str, Any]] = Field(default=[])
    additional_columns: List[Dict[str, Any]] = Field(default=[])
    additional_indexes: List[Dict[str, Any]] = Field(default=[])

    # Compliance Configuration
    compliance_frameworks: List[ComplianceFramework]
    security_requirements: Dict[str, Any]
    audit_requirements: Dict[str, Any]

    # RBAC Configuration
    additional_roles: List[Dict[str, Any]] = Field(default=[])
    default_permissions: Dict[str, List[str]]

    # Data Retention and Privacy
    data_retention_policies: Dict[str, Any]
    privacy_settings: Dict[str, Any]

    # Monitoring and Alerting
    monitoring_rules: List[Dict[str, Any]] = Field(default=[])
    alert_thresholds: Dict[str, Any]

    # Documentation and Training
    setup_guide_url: Optional[str] = None
    training_materials: List[str] = Field(default=[])
    compliance_checklist: List[str] = Field(default=[])


class OnboardingNotification(BaseModel):
    """Notification configuration for onboarding events."""

    notification_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    notification_type: str  # welcome, status_update, error, completion

    # Recipients
    recipient_emails: List[str]
    cc_emails: List[str] = Field(default=[])

    # Content
    subject: str
    template_name: str
    template_variables: Dict[str, Any] = Field(default={})

    # Scheduling
    send_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivery_status: str = Field(default="pending")  # pending, sent, failed

    # Tracking
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None


class TenantProvisioningRequest(BaseModel):
    """Internal provisioning request model."""

    workflow_id: str
    tenant_id: str
    registration: TenantRegistration

    # Provisioning Configuration
    database_config: Dict[str, Any]
    resource_allocation: Dict[str, Any]
    industry_template: IndustryTemplate

    # RBAC Setup
    admin_user_config: Dict[str, Any]
    initial_roles: List[str]

    # Monitoring Setup
    monitoring_enabled: bool = True
    alert_config: Dict[str, Any]

    # Timeline
    priority: int = Field(default=5, ge=1, le=10)  # 1=highest, 10=lowest
    deadline: Optional[datetime] = None


class TenantBillingInfo(BaseModel):
    """Tenant billing and subscription information."""

    tenant_id: str
    billing_email: str

    # Subscription Details
    plan_name: str
    plan_tier: str  # basic, standard, premium, enterprise
    billing_cycle: str  # monthly, yearly

    # Usage Limits
    user_limit: int
    storage_limit_gb: int
    query_limit_monthly: int
    api_calls_limit_monthly: int

    # Billing Status
    billing_status: str  # active, suspended, past_due
    next_billing_date: datetime
    last_payment_date: Optional[datetime]

    # Cost Information
    monthly_cost: float
    overage_charges: float = Field(default=0.0)
    total_cost_current_period: float

    # Payment Information
    payment_method_id: Optional[str] = None
    auto_pay_enabled: bool = Field(default=True)

    # Usage Tracking
    current_period_usage: TenantResourceUsage
    historical_usage: List[TenantResourceUsage] = Field(default=[])


# Response Models

class TenantRegistrationResponse(BaseModel):
    """Response for tenant registration request."""

    success: bool
    workflow_id: str
    tenant_id: Optional[str] = None

    message: str
    estimated_completion_time: str
    next_steps: List[str]

    # Contact Information
    support_email: str
    support_phone: Optional[str] = None
    status_check_url: str


class OnboardingStatusResponse(BaseModel):
    """Response for onboarding status check."""

    workflow_id: str
    tenant_id: Optional[str]
    current_status: OnboardingStatus
    progress_percentage: int

    # Status Details
    steps_completed: List[str]
    current_step: str
    next_step: Optional[str]

    # Timing
    started_at: datetime
    estimated_completion: Optional[datetime]

    # Results (if completed)
    tenant_config: Optional[TenantConfiguration] = None
    access_instructions: Optional[Dict[str, Any]] = None

    # Errors (if any)
    errors: List[str] = Field(default=[])
    last_error: Optional[str] = None


class TenantListResponse(BaseModel):
    """Response for tenant list request."""

    tenants: List[TenantInfo]
    total_count: int
    page: int
    page_size: int

    # Summary Statistics
    status_summary: Dict[str, int]
    industry_summary: Dict[str, int]
    region_summary: Dict[str, int]


class TenantDetailResponse(BaseModel):
    """Detailed tenant information response."""

    tenant_info: TenantInfo
    resource_usage: TenantResourceUsage
    billing_info: Optional[TenantBillingInfo] = None

    # Recent Activity
    recent_activity: List[Dict[str, Any]] = Field(default=[])
    alerts: List[Dict[str, Any]] = Field(default=[])

    # Configuration
    database_config: Dict[str, Any]
    rbac_config: Dict[str, Any]
    compliance_status: Dict[str, Any]