"""
Automated Tenant Provisioning Workflow Engine
Handles complete tenant lifecycle from registration to activation.
"""

import asyncio
import json
import logging
import uuid
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
import threading
from concurrent.futures import ThreadPoolExecutor

from .tenant_onboarding_models import (
    TenantRegistration, TenantConfiguration, OnboardingWorkflow,
    OnboardingStatus, TenantStatus, IndustryType, DatabaseType,
    TenantProvisioningRequest, TenantInfo, IndustryTemplate
)
from .database_cloner import DatabaseCloner
from .tenant_connection_manager import TenantConnectionManager
from .tenant_rbac_manager import TenantRBACManager
from .error_handling_monitoring import MonitoringSystem


logger = logging.getLogger(__name__)


class TenantIDGenerator:
    """Generates unique tenant IDs and manages ID allocation."""

    def __init__(self):
        self.used_ids = set()
        self.current_counter = 1
        self.lock = threading.Lock()

    def generate_tenant_id(self, org_name: str = None) -> str:
        """Generate unique tenant ID."""
        with self.lock:
            # Try organization-based ID first
            if org_name:
                # Clean organization name for ID
                clean_name = ''.join(c.lower() for c in org_name if c.isalnum())[:10]
                for i in range(1, 100):
                    candidate_id = f"tenant-{clean_name}-{i:03d}"
                    if candidate_id not in self.used_ids:
                        self.used_ids.add(candidate_id)
                        return candidate_id

            # Fallback to sequential numbering
            while True:
                candidate_id = f"tenant-{self.current_counter:06d}"
                if candidate_id not in self.used_ids:
                    self.used_ids.add(candidate_id)
                    self.current_counter += 1
                    return candidate_id
                self.current_counter += 1

    def reserve_tenant_id(self, tenant_id: str) -> bool:
        """Reserve a specific tenant ID."""
        with self.lock:
            if tenant_id not in self.used_ids:
                self.used_ids.add(tenant_id)
                return True
            return False

    def load_existing_ids(self, existing_ids: List[str]):
        """Load existing tenant IDs to avoid conflicts."""
        with self.lock:
            self.used_ids.update(existing_ids)
            # Update counter based on highest existing ID
            for tenant_id in existing_ids:
                if tenant_id.startswith("tenant-") and tenant_id.split("-")[-1].isdigit():
                    try:
                        counter = int(tenant_id.split("-")[-1])
                        self.current_counter = max(self.current_counter, counter + 1)
                    except (ValueError, IndexError):
                        continue


class ResourceAllocator:
    """Allocates resources for new tenants."""

    def __init__(self, connection_manager: TenantConnectionManager):
        self.connection_manager = connection_manager
        self.allocated_ports = set()
        self.port_ranges = {
            DatabaseType.MYSQL: (3309, 3400),
            DatabaseType.POSTGRESQL: (5434, 5500),
            DatabaseType.MONGODB: (27019, 27100),
            DatabaseType.SQLITE: (0, 0)  # No port needed
        }

    def allocate_resources(self, registration: TenantRegistration) -> Dict[str, Any]:
        """Allocate resources for tenant based on requirements."""

        # Allocate database port
        port = self._allocate_port(registration.database_type)

        # Calculate resource limits based on expected usage
        resource_limits = self._calculate_resource_limits(registration)

        # Generate container and volume names
        container_name = f"{registration.database_type.value}_tenant_{registration.org_name.lower().replace(' ', '_')}"
        volume_path = f"/data/tenants/{container_name}"

        return {
            "allocated_port": port,
            "container_name": container_name,
            "volume_path": volume_path,
            "resource_limits": resource_limits,
            "network_name": f"tenant_network_{container_name}",
            "backup_path": f"/backups/{container_name}"
        }

    def _allocate_port(self, db_type: DatabaseType) -> int:
        """Allocate unique port for database type."""
        if db_type == DatabaseType.SQLITE:
            return 0  # SQLite doesn't need a port

        start_port, end_port = self.port_ranges[db_type]

        for port in range(start_port, end_port + 1):
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port

        raise Exception(f"No available ports for {db_type.value}")

    def _calculate_resource_limits(self, registration: TenantRegistration) -> Dict[str, Any]:
        """Calculate appropriate resource limits."""
        base_memory = 512  # MB
        base_cpu = 0.5     # CPU cores
        base_storage = 10  # GB

        # Scale based on expected users and queries
        user_multiplier = min(registration.expected_users / 10, 10)  # Max 10x
        query_multiplier = min(registration.expected_queries_per_day / 1000, 10)  # Max 10x

        return {
            "memory_limit_mb": int(base_memory * (1 + user_multiplier * 0.5)),
            "cpu_limit": base_cpu * (1 + query_multiplier * 0.3),
            "storage_limit_gb": max(base_storage, registration.storage_requirements_gb),
            "connection_limit": min(10 + registration.expected_users, 100),
            "query_rate_limit": registration.expected_queries_per_day,
            "backup_retention_days": 30 if registration.security_level == "high" else 7
        }

    def deallocate_resources(self, tenant_config: TenantConfiguration):
        """Deallocate resources when tenant is removed."""
        if tenant_config.allocated_port > 0:
            self.allocated_ports.discard(tenant_config.allocated_port)


class WorkflowExecutor:
    """Executes tenant onboarding workflow steps."""

    def __init__(self, database_cloner: DatabaseCloner,
                 connection_manager: TenantConnectionManager,
                 rbac_manager: TenantRBACManager,
                 monitoring_system: MonitoringSystem):
        self.database_cloner = database_cloner
        self.connection_manager = connection_manager
        self.rbac_manager = rbac_manager
        self.monitoring_system = monitoring_system

        self.tenant_id_generator = TenantIDGenerator()
        self.resource_allocator = ResourceAllocator(connection_manager)

        # Load existing tenant IDs
        self._load_existing_tenant_ids()

    def _load_existing_tenant_ids(self):
        """Load existing tenant IDs from database."""
        try:
            existing_clones = self.database_cloner.list_tenant_clones()
            existing_ids = [clone.tenant_id for clone in existing_clones if clone.tenant_id]
            self.tenant_id_generator.load_existing_ids(existing_ids)
            logger.info(f"Loaded {len(existing_ids)} existing tenant IDs")
        except Exception as e:
            logger.warning(f"Could not load existing tenant IDs: {e}")

    async def execute_workflow(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Execute complete onboarding workflow."""
        logger.info(f"Starting onboarding workflow {workflow.workflow_id}")

        workflow.started_at = datetime.utcnow()
        workflow.estimated_completion = datetime.utcnow() + timedelta(minutes=15)

        try:
            # Step 1: Validation
            workflow = await self._validate_registration(workflow)

            # Step 2: Generate tenant configuration
            workflow = await self._generate_tenant_config(workflow)

            # Step 3: Create database clone
            workflow = await self._create_database_clone(workflow)

            # Step 4: Set up admin user
            workflow = await self._setup_admin_user(workflow)

            # Step 5: Configure RBAC
            workflow = await self._configure_rbac(workflow)

            # Step 6: Apply industry template
            workflow = await self._apply_industry_template(workflow)

            # Step 7: Initialize monitoring
            workflow = await self._initialize_monitoring(workflow)

            # Step 8: Testing
            workflow = await self._test_tenant_setup(workflow)

            # Step 9: Activation
            workflow = await self._activate_tenant(workflow)

            # Step 10: Completion
            workflow.current_status = OnboardingStatus.COMPLETED
            workflow.completed_at = datetime.utcnow()
            workflow.add_status_change(OnboardingStatus.COMPLETED, "Tenant onboarding completed successfully")

            logger.info(f"Completed onboarding workflow {workflow.workflow_id} for tenant {workflow.tenant_id}")

        except Exception as e:
            workflow.current_status = OnboardingStatus.FAILED
            workflow.add_error("workflow_execution", str(e))
            workflow.add_status_change(OnboardingStatus.FAILED, f"Workflow failed: {str(e)}", error=True)
            logger.error(f"Onboarding workflow {workflow.workflow_id} failed: {e}")

            # Cleanup on failure
            await self._cleanup_failed_provisioning(workflow)

        return workflow

    async def _validate_registration(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Validate registration data."""
        workflow.add_status_change(OnboardingStatus.VALIDATION, "Validating registration data")

        registration = workflow.registration_data

        # Validate email uniqueness
        existing_user = self.rbac_manager.get_user_profile_by_email(registration.admin_email)
        if existing_user:
            raise Exception(f"Email {registration.admin_email} is already registered")

        # Validate organization name uniqueness
        if await self._check_org_name_exists(registration.org_name):
            raise Exception(f"Organization name '{registration.org_name}' is already taken")

        # Validate resource requirements
        if registration.expected_users > 1000 and registration.security_level == "basic":
            raise Exception("High user count requires standard or high security level")

        workflow.add_completed_step("validation")
        return workflow

    async def _generate_tenant_config(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Generate tenant configuration."""
        workflow.add_status_change(OnboardingStatus.VALIDATION, "Generating tenant configuration")

        registration = workflow.registration_data

        # Generate tenant ID
        tenant_id = self.tenant_id_generator.generate_tenant_id(registration.org_name)
        workflow.tenant_id = tenant_id

        # Allocate resources
        resources = self.resource_allocator.allocate_resources(registration)

        # Build database configuration
        database_config = self._build_database_config(registration, resources)

        # Create tenant configuration
        tenant_config = TenantConfiguration(
            tenant_id=tenant_id,
            tenant_uuid=str(uuid.uuid4()),
            database_config=database_config,
            connection_string=self._build_connection_string(database_config),
            allocated_port=resources["allocated_port"],
            container_name=resources["container_name"],
            volume_path=resources["volume_path"],
            admin_user_id="",  # Will be set later
            role_assignments={},  # Will be set later
            schema_template=registration.industry.value,
            compliance_config=self._build_compliance_config(registration),
            resource_limits=resources["resource_limits"],
            monitoring_config=self._build_monitoring_config(registration),
            alert_recipients=[registration.admin_email] + registration.notification_emails
        )

        workflow.tenant_config = tenant_config
        workflow.add_completed_step("configuration_generation")
        return workflow

    async def _create_database_clone(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Create database clone for tenant."""
        workflow.add_status_change(OnboardingStatus.CLONE_CREATION, "Creating database clone")

        if not workflow.tenant_config:
            raise Exception("Tenant configuration not available")

        # Create clone using database cloner
        success, message, clone = self.database_cloner.clone_from_root(
            tenant_id=workflow.tenant_id,
            db_type=workflow.registration_data.database_type.value,
            root_version="latest",
            custom_config=workflow.tenant_config.database_config
        )

        if not success:
            raise Exception(f"Database clone creation failed: {message}")

        # Update configuration with clone details
        workflow.tenant_config.database_config.update({
            "clone_id": clone.clone_id,
            "database_name": clone.database_name,
            "container_id": clone.container_id
        })

        workflow.add_completed_step("database_clone")
        return workflow

    async def _setup_admin_user(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Set up admin user for tenant."""
        workflow.add_status_change(OnboardingStatus.USER_SETUP, "Setting up admin user")

        registration = workflow.registration_data

        # Generate secure password
        password = self._generate_secure_password()

        # Create admin user
        admin_user_id = self.rbac_manager.create_user(
            username=f"admin_{workflow.tenant_id}",
            email=registration.admin_email,
            password=password,
            full_name=registration.admin_name,
            is_global_admin=False,
            metadata={
                "tenant_id": workflow.tenant_id,
                "is_tenant_admin": True,
                "created_via_onboarding": True,
                "phone": registration.admin_phone,
                "organization": registration.org_name
            }
        )

        if not admin_user_id:
            raise Exception("Failed to create admin user")

        # Store credentials securely (in production, use secure storage)
        workflow.tenant_config.admin_user_id = admin_user_id

        # Store password for welcome email (temporary, should be secured)
        if not hasattr(workflow, 'temp_credentials'):
            workflow.temp_credentials = {}
        workflow.temp_credentials['admin_password'] = password

        workflow.add_completed_step("admin_user_setup")
        return workflow

    async def _configure_rbac(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Configure RBAC for tenant."""
        workflow.add_status_change(OnboardingStatus.RBAC_CONFIGURATION, "Configuring RBAC")

        # Grant tenant access to admin user
        success = self.rbac_manager.grant_tenant_access(
            workflow.tenant_config.admin_user_id,
            workflow.tenant_id,
            ["admin"],  # Grant admin role
            "system_onboarding"
        )

        if not success:
            raise Exception("Failed to configure RBAC for admin user")

        # Update role assignments
        workflow.tenant_config.role_assignments = {
            workflow.tenant_config.admin_user_id: ["admin"]
        }

        workflow.add_completed_step("rbac_configuration")
        return workflow

    async def _apply_industry_template(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Apply industry-specific template."""
        workflow.add_status_change(OnboardingStatus.TESTING, "Applying industry template")

        # Get industry template
        industry_template = await self._get_industry_template(workflow.registration_data.industry)

        if industry_template:
            # Apply additional schema modifications
            await self._apply_schema_modifications(workflow, industry_template)

            # Apply compliance configurations
            await self._apply_compliance_config(workflow, industry_template)

        workflow.add_completed_step("industry_template")
        return workflow

    async def _initialize_monitoring(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Initialize monitoring for tenant."""
        workflow.add_status_change(OnboardingStatus.TESTING, "Initializing monitoring")

        # Create connection pool for monitoring
        success = self.connection_manager.create_connection_pool(workflow.tenant_id)

        if not success:
            raise Exception("Failed to create connection pool for monitoring")

        # Set up health checks
        health_status = self.connection_manager.health_check(workflow.tenant_id)

        if health_status.get("status") != "healthy":
            raise Exception(f"Tenant database not healthy: {health_status}")

        workflow.add_completed_step("monitoring_initialization")
        return workflow

    async def _test_tenant_setup(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Test tenant setup end-to-end."""
        workflow.add_status_change(OnboardingStatus.TESTING, "Testing tenant setup")

        # Test database connection
        try:
            with self.connection_manager.get_connection_context(workflow.tenant_id) as conn:
                if hasattr(conn, 'execute'):
                    # Test basic query
                    result = conn.execute("SELECT 1 as test_value")
                    test_result = result.fetchone()
                    if not test_result:
                        raise Exception("Database connection test failed")
        except Exception as e:
            raise Exception(f"Database connection test failed: {e}")

        # Test RBAC setup
        user_profile = self.rbac_manager.get_user_profile(workflow.tenant_config.admin_user_id)
        if not user_profile or workflow.tenant_id not in user_profile.tenant_access:
            raise Exception("RBAC configuration test failed")

        # Test admin user authentication
        auth_profile = self.rbac_manager.authenticate_user(
            workflow.registration_data.admin_email,
            workflow.temp_credentials['admin_password']
        )
        if not auth_profile:
            raise Exception("Admin user authentication test failed")

        workflow.add_completed_step("testing")
        return workflow

    async def _activate_tenant(self, workflow: OnboardingWorkflow) -> OnboardingWorkflow:
        """Activate tenant for production use."""
        workflow.add_status_change(OnboardingStatus.ACTIVATION, "Activating tenant")

        # Mark tenant as active in the system
        # This would typically update a tenant registry database

        # Schedule welcome email
        workflow.add_status_change(OnboardingStatus.WELCOME_EMAIL, "Scheduling welcome email")

        workflow.add_completed_step("activation")
        return workflow

    async def _cleanup_failed_provisioning(self, workflow: OnboardingWorkflow):
        """Clean up resources on failed provisioning."""
        try:
            if workflow.tenant_id:
                # Clean up database clone
                self.database_cloner.remove_tenant_clone(workflow.tenant_id, force=True)

                # Clean up connection pools
                self.connection_manager.close_tenant_connections(workflow.tenant_id)

                # Clean up RBAC
                if workflow.tenant_config and workflow.tenant_config.admin_user_id:
                    self.rbac_manager.revoke_tenant_access(
                        workflow.tenant_config.admin_user_id,
                        workflow.tenant_id,
                        "cleanup_failed_provisioning"
                    )

                # Deallocate resources
                if workflow.tenant_config:
                    self.resource_allocator.deallocate_resources(workflow.tenant_config)

                logger.info(f"Cleaned up failed provisioning for {workflow.tenant_id}")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    # Helper methods

    def _build_database_config(self, registration: TenantRegistration, resources: Dict[str, Any]) -> Dict[str, Any]:
        """Build database configuration."""
        base_config = {
            "database_type": registration.database_type.value,
            "port": resources["allocated_port"],
            "container_name": resources["container_name"],
            "volume_path": resources["volume_path"],
            "data_region": registration.data_region.value,
            "backup_enabled": True,
            "backup_schedule": "daily",
            "encryption_enabled": registration.security_level in ["standard", "high"],
            "ssl_enabled": registration.security_level == "high"
        }

        # Database-specific configuration
        if registration.database_type == DatabaseType.MYSQL:
            base_config.update({
                "charset": "utf8mb4",
                "innodb_buffer_pool_size": f"{resources['resource_limits']['memory_limit_mb'] // 2}M",
                "max_connections": resources["resource_limits"]["connection_limit"]
            })
        elif registration.database_type == DatabaseType.POSTGRESQL:
            base_config.update({
                "encoding": "UTF8",
                "shared_buffers": f"{resources['resource_limits']['memory_limit_mb'] // 4}MB",
                "max_connections": resources["resource_limits"]["connection_limit"]
            })

        return base_config

    def _build_connection_string(self, database_config: Dict[str, Any]) -> str:
        """Build database connection string."""
        db_type = database_config["database_type"]

        if db_type == "mysql":
            return f"mysql://tenant_user:tenant_password@localhost:{database_config['port']}/tenant_db"
        elif db_type == "postgresql":
            return f"postgresql://tenant_user:tenant_password@localhost:{database_config['port']}/tenant_db"
        elif db_type == "sqlite":
            return f"sqlite:///{database_config['volume_path']}/tenant.db"
        elif db_type == "mongodb":
            return f"mongodb://tenant_user:tenant_password@localhost:{database_config['port']}/tenant_db"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _build_compliance_config(self, registration: TenantRegistration) -> Dict[str, Any]:
        """Build compliance configuration."""
        config = {
            "frameworks": [framework.value for framework in registration.compliance_requirements],
            "data_region": registration.data_region.value,
            "encryption_at_rest": True,
            "encryption_in_transit": True,
            "audit_logging": True,
            "data_retention_days": 2555 if "sox" in [f.value for f in registration.compliance_requirements] else 365
        }

        # Add framework-specific configurations
        for framework in registration.compliance_requirements:
            if framework.value == "hipaa":
                config.update({
                    "phi_protection": True,
                    "access_controls": "strict",
                    "minimum_necessary": True
                })
            elif framework.value == "gdpr":
                config.update({
                    "right_to_be_forgotten": True,
                    "data_portability": True,
                    "consent_management": True
                })
            elif framework.value == "pci_dss":
                config.update({
                    "card_data_encryption": True,
                    "access_restrictions": "payment_handlers_only",
                    "network_segmentation": True
                })

        return config

    def _build_monitoring_config(self, registration: TenantRegistration) -> Dict[str, Any]:
        """Build monitoring configuration."""
        return {
            "health_checks_enabled": True,
            "performance_monitoring": True,
            "security_monitoring": True,
            "alert_thresholds": {
                "cpu_usage": 80,
                "memory_usage": 85,
                "disk_usage": 90,
                "connection_usage": 90,
                "query_response_time_ms": 2000,
                "error_rate_percent": 5
            },
            "notification_channels": {
                "email": [registration.admin_email] + registration.notification_emails,
                "severity_levels": ["high", "critical"]
            }
        }

    def _generate_secure_password(self, length: int = 16) -> str:
        """Generate secure random password."""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))

    async def _check_org_name_exists(self, org_name: str) -> bool:
        """Check if organization name already exists."""
        # This would check against a central registry
        # For now, return False to allow all names
        return False

    async def _get_industry_template(self, industry: IndustryType) -> Optional[IndustryTemplate]:
        """Get industry-specific template."""
        # This will be implemented in the industry templates module
        return None

    async def _apply_schema_modifications(self, workflow: OnboardingWorkflow, template: IndustryTemplate):
        """Apply schema modifications from industry template."""
        # This would apply additional tables, columns, indexes
        pass

    async def _apply_compliance_config(self, workflow: OnboardingWorkflow, template: IndustryTemplate):
        """Apply compliance configuration from industry template."""
        # This would apply compliance-specific configurations
        pass


class ProvisioningManager:
    """Manages tenant provisioning operations and workflow orchestration."""

    def __init__(self, database_cloner: DatabaseCloner,
                 connection_manager: TenantConnectionManager,
                 rbac_manager: TenantRBACManager,
                 monitoring_system: MonitoringSystem):

        self.workflow_executor = WorkflowExecutor(
            database_cloner, connection_manager, rbac_manager, monitoring_system
        )

        # Active workflows
        self.active_workflows: Dict[str, OnboardingWorkflow] = {}
        self.completed_workflows: Dict[str, OnboardingWorkflow] = {}

        # Workflow queue
        self.workflow_queue = asyncio.Queue()
        self.processing_workflows = False

        # Background task for processing workflows
        self.workflow_processor_task = None

    async def start_processing(self):
        """Start background workflow processing."""
        if not self.processing_workflows:
            self.processing_workflows = True
            self.workflow_processor_task = asyncio.create_task(self._process_workflows())
            logger.info("Started tenant provisioning workflow processor")

    async def stop_processing(self):
        """Stop background workflow processing."""
        self.processing_workflows = False
        if self.workflow_processor_task:
            self.workflow_processor_task.cancel()
            try:
                await self.workflow_processor_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped tenant provisioning workflow processor")

    async def submit_registration(self, registration: TenantRegistration,
                                submitted_by: Optional[str] = None) -> OnboardingWorkflow:
        """Submit tenant registration for processing."""

        # Create workflow
        workflow = OnboardingWorkflow(
            registration_data=registration,
            submitted_by=submitted_by
        )

        # Add to active workflows
        self.active_workflows[workflow.workflow_id] = workflow

        # Queue for processing
        await self.workflow_queue.put(workflow)

        logger.info(f"Submitted tenant registration workflow {workflow.workflow_id}")
        return workflow

    async def get_workflow_status(self, workflow_id: str) -> Optional[OnboardingWorkflow]:
        """Get workflow status by ID."""
        return (self.active_workflows.get(workflow_id) or
                self.completed_workflows.get(workflow_id))

    async def _process_workflows(self):
        """Background task to process workflow queue."""
        while self.processing_workflows:
            try:
                # Get next workflow from queue
                workflow = await asyncio.wait_for(self.workflow_queue.get(), timeout=1.0)

                logger.info(f"Processing workflow {workflow.workflow_id}")

                # Execute workflow
                completed_workflow = await self.workflow_executor.execute_workflow(workflow)

                # Move to completed workflows
                if workflow.workflow_id in self.active_workflows:
                    del self.active_workflows[workflow.workflow_id]
                self.completed_workflows[completed_workflow.workflow_id] = completed_workflow

                # Mark queue task as done
                self.workflow_queue.task_done()

            except asyncio.TimeoutError:
                # No workflows in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing workflow: {e}")
                # Mark queue task as done even on error
                self.workflow_queue.task_done()