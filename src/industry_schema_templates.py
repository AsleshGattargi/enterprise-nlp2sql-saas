"""
Industry-Specific Schema Templates for Automated Tenant Onboarding
Provides compliance-ready schema additions and configurations for different industries.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from tenant_onboarding_models import IndustryType, ComplianceFramework, IndustryTemplate
import json


class TableType(str, Enum):
    """Types of additional tables for industry compliance."""
    AUDIT_LOG = "audit_log"
    COMPLIANCE_TRACKING = "compliance_tracking"
    DATA_RETENTION = "data_retention"
    SECURITY_EVENTS = "security_events"
    PRIVACY_CONTROLS = "privacy_controls"
    FINANCIAL_AUDIT = "financial_audit"
    EDUCATIONAL_RECORDS = "educational_records"
    HEALTHCARE_PHI = "healthcare_phi"
    PAYMENT_PROCESSING = "payment_processing"


class ColumnSensitivity(str, Enum):
    """Data sensitivity levels for column classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    PHI = "phi"  # Protected Health Information
    PII = "pii"  # Personally Identifiable Information
    PCI = "pci"  # Payment Card Industry sensitive


class IndustrySchemaTemplateManager:
    """Manages industry-specific schema templates and compliance configurations."""

    def __init__(self):
        self.templates = self._initialize_templates()
        self.compliance_mappings = self._initialize_compliance_mappings()

    def get_template(self, industry: IndustryType) -> IndustryTemplate:
        """Get industry-specific template with all compliance configurations."""
        if industry not in self.templates:
            return self._get_general_template()

        template_data = self.templates[industry]

        return IndustryTemplate(
            industry=industry,
            template_name=template_data["template_name"],
            template_version=template_data["template_version"],
            additional_tables=template_data["additional_tables"],
            additional_columns=template_data["additional_columns"],
            additional_indexes=template_data["additional_indexes"],
            compliance_frameworks=template_data["compliance_frameworks"],
            security_requirements=template_data["security_requirements"],
            audit_requirements=template_data["audit_requirements"],
            additional_roles=template_data["additional_roles"],
            default_permissions=template_data["default_permissions"],
            data_retention_policies=template_data["data_retention_policies"],
            privacy_settings=template_data["privacy_settings"],
            monitoring_rules=template_data["monitoring_rules"],
            alert_thresholds=template_data["alert_thresholds"],
            setup_guide_url=template_data.get("setup_guide_url"),
            training_materials=template_data["training_materials"],
            compliance_checklist=template_data["compliance_checklist"]
        )

    def _initialize_templates(self) -> Dict[IndustryType, Dict[str, Any]]:
        """Initialize all industry-specific templates."""
        return {
            IndustryType.HEALTHCARE: self._create_healthcare_template(),
            IndustryType.FINANCE: self._create_finance_template(),
            IndustryType.EDUCATION: self._create_education_template(),
            IndustryType.RETAIL: self._create_retail_template(),
            IndustryType.TECHNOLOGY: self._create_technology_template(),
            IndustryType.MANUFACTURING: self._create_manufacturing_template(),
            IndustryType.GOVERNMENT: self._create_government_template(),
            IndustryType.NONPROFIT: self._create_nonprofit_template()
        }

    def _create_healthcare_template(self) -> Dict[str, Any]:
        """Create HIPAA-compliant healthcare template."""
        return {
            "template_name": "Healthcare HIPAA Compliance",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "phi_access_log",
                    "description": "PHI access audit trail for HIPAA compliance",
                    "columns": [
                        {"name": "access_id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "patient_id", "type": "VARCHAR(50)", "nullable": True},
                        {"name": "accessed_data", "type": "TEXT", "nullable": False},
                        {"name": "access_reason", "type": "VARCHAR(200)", "nullable": False},
                        {"name": "access_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "ip_address", "type": "VARCHAR(45)", "nullable": False},
                        {"name": "session_id", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "data_sensitivity", "type": "VARCHAR(20)", "nullable": False}
                    ]
                },
                {
                    "table_name": "hipaa_compliance_tracking",
                    "description": "HIPAA compliance status and violations tracking",
                    "columns": [
                        {"name": "compliance_id", "type": "UUID", "primary_key": True},
                        {"name": "violation_type", "type": "VARCHAR(100)", "nullable": True},
                        {"name": "severity_level", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "detected_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "resolved_timestamp", "type": "TIMESTAMP", "nullable": True},
                        {"name": "remediation_actions", "type": "TEXT", "nullable": True},
                        {"name": "reported_to_authorities", "type": "BOOLEAN", "default": False}
                    ]
                },
                {
                    "table_name": "patient_consent_management",
                    "description": "Patient data usage consent tracking",
                    "columns": [
                        {"name": "consent_id", "type": "UUID", "primary_key": True},
                        {"name": "patient_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "consent_type", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "consent_granted", "type": "BOOLEAN", "nullable": False},
                        {"name": "consent_date", "type": "TIMESTAMP", "nullable": False},
                        {"name": "expiry_date", "type": "TIMESTAMP", "nullable": True},
                        {"name": "withdrawal_date", "type": "TIMESTAMP", "nullable": True},
                        {"name": "purpose_of_use", "type": "TEXT", "nullable": False}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "hipaa_training_completed", "type": "BOOLEAN", "default": False},
                        {"name": "last_hipaa_training_date", "type": "TIMESTAMP", "nullable": True},
                        {"name": "npi_number", "type": "VARCHAR(20)", "nullable": True},
                        {"name": "medical_license_number", "type": "VARCHAR(50)", "nullable": True}
                    ]
                },
                {
                    "table": "queries",
                    "columns": [
                        {"name": "contains_phi", "type": "BOOLEAN", "default": False},
                        {"name": "phi_access_justification", "type": "TEXT", "nullable": True},
                        {"name": "minimum_necessary_applied", "type": "BOOLEAN", "default": True}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "phi_access_log", "columns": ["user_id", "access_timestamp"], "type": "btree"},
                {"table": "phi_access_log", "columns": ["patient_id"], "type": "btree"},
                {"table": "hipaa_compliance_tracking", "columns": ["detected_timestamp"], "type": "btree"},
                {"table": "patient_consent_management", "columns": ["patient_id", "consent_type"], "type": "unique"}
            ],
            "compliance_frameworks": [ComplianceFramework.HIPAA],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "role_based",
                "audit_logging": "comprehensive",
                "data_backup_encryption": True,
                "minimum_password_complexity": "high",
                "session_timeout_minutes": 15,
                "failed_login_lockout": 3,
                "phi_access_monitoring": True
            },
            "audit_requirements": {
                "phi_access_logging": "mandatory",
                "audit_log_retention_years": 6,
                "real_time_monitoring": True,
                "automated_violation_detection": True,
                "breach_notification_automation": True,
                "compliance_reporting_frequency": "monthly"
            },
            "additional_roles": [
                {
                    "role_name": "healthcare_admin",
                    "description": "Healthcare administrator with HIPAA oversight",
                    "permissions": ["phi_access", "audit_review", "compliance_management"]
                },
                {
                    "role_name": "medical_provider",
                    "description": "Medical provider with patient data access",
                    "permissions": ["phi_read", "phi_write", "patient_care_access"]
                },
                {
                    "role_name": "compliance_officer",
                    "description": "HIPAA compliance monitoring and reporting",
                    "permissions": ["audit_read", "compliance_reporting", "violation_management"]
                }
            ],
            "default_permissions": {
                "healthcare_admin": ["all_phi_access", "user_management", "audit_logs"],
                "medical_provider": ["patient_phi_access", "treatment_data", "care_coordination"],
                "compliance_officer": ["audit_monitoring", "compliance_reports", "violation_tracking"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "phi_data_retention_years": 6,
                "audit_log_retention_years": 6,
                "inactive_account_deletion_days": 90,
                "backup_retention_years": 7,
                "compliance_record_retention_years": 10
            },
            "privacy_settings": {
                "default_phi_visibility": "restricted",
                "minimum_necessary_enforcement": True,
                "patient_data_segregation": True,
                "automated_phi_detection": True,
                "data_masking_non_clinical": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "unusual_phi_access",
                    "description": "Detect unusual PHI access patterns",
                    "condition": "phi_access_count > 50 per hour",
                    "action": "alert_compliance_officer"
                },
                {
                    "rule_name": "after_hours_access",
                    "description": "Monitor after-hours PHI access",
                    "condition": "phi_access between 22:00 and 06:00",
                    "action": "require_justification"
                },
                {
                    "rule_name": "bulk_data_export",
                    "description": "Monitor bulk PHI exports",
                    "condition": "export_record_count > 100",
                    "action": "require_approval"
                }
            ],
            "alert_thresholds": {
                "failed_login_attempts": 3,
                "concurrent_sessions": 5,
                "phi_access_per_hour": 50,
                "data_export_size_mb": 100,
                "query_execution_time_minutes": 5
            },
            "setup_guide_url": "https://docs.example.com/healthcare-hipaa-setup",
            "training_materials": [
                "HIPAA Privacy Rule Overview",
                "PHI Handling Best Practices",
                "Breach Notification Procedures",
                "Patient Consent Management"
            ],
            "compliance_checklist": [
                "Verify HIPAA training completion for all users",
                "Configure PHI access monitoring",
                "Set up automated audit log reviews",
                "Implement patient consent tracking",
                "Enable breach detection alerts",
                "Configure data retention policies",
                "Test backup and recovery procedures"
            ]
        }

    def _create_finance_template(self) -> Dict[str, Any]:
        """Create SOX-compliant finance template."""
        return {
            "template_name": "Financial Services SOX Compliance",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "sox_audit_trail",
                    "description": "SOX compliance audit trail for financial data",
                    "columns": [
                        {"name": "audit_id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "transaction_type", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "financial_data_accessed", "type": "TEXT", "nullable": False},
                        {"name": "business_justification", "type": "TEXT", "nullable": False},
                        {"name": "timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "control_assertion", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "segregation_of_duties_verified", "type": "BOOLEAN", "default": False}
                    ]
                },
                {
                    "table_name": "financial_controls_testing",
                    "description": "SOX internal controls testing results",
                    "columns": [
                        {"name": "test_id", "type": "UUID", "primary_key": True},
                        {"name": "control_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "test_date", "type": "TIMESTAMP", "nullable": False},
                        {"name": "test_result", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "deficiency_identified", "type": "BOOLEAN", "default": False},
                        {"name": "remediation_plan", "type": "TEXT", "nullable": True},
                        {"name": "tested_by_user_id", "type": "VARCHAR(50)", "nullable": False}
                    ]
                },
                {
                    "table_name": "segregation_of_duties_matrix",
                    "description": "Role segregation tracking for SOX compliance",
                    "columns": [
                        {"name": "matrix_id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "function_category", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "access_level", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "approval_required", "type": "BOOLEAN", "default": True},
                        {"name": "approver_user_id", "type": "VARCHAR(50)", "nullable": True},
                        {"name": "effective_date", "type": "DATE", "nullable": False}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "sox_certification_date", "type": "TIMESTAMP", "nullable": True},
                        {"name": "financial_disclosure_signed", "type": "BOOLEAN", "default": False},
                        {"name": "conflict_of_interest_declared", "type": "BOOLEAN", "default": False},
                        {"name": "segregation_duties_validated", "type": "BOOLEAN", "default": False}
                    ]
                },
                {
                    "table": "queries",
                    "columns": [
                        {"name": "financial_data_accessed", "type": "BOOLEAN", "default": False},
                        {"name": "sox_control_tested", "type": "VARCHAR(100)", "nullable": True},
                        {"name": "approval_workflow_id", "type": "VARCHAR(50)", "nullable": True}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "sox_audit_trail", "columns": ["user_id", "timestamp"], "type": "btree"},
                {"table": "financial_controls_testing", "columns": ["control_id", "test_date"], "type": "btree"},
                {"table": "segregation_of_duties_matrix", "columns": ["user_id", "function_category"], "type": "unique"}
            ],
            "compliance_frameworks": [ComplianceFramework.SOX],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "segregation_of_duties",
                "audit_logging": "comprehensive",
                "data_backup_encryption": True,
                "minimum_password_complexity": "high",
                "session_timeout_minutes": 30,
                "failed_login_lockout": 5,
                "financial_data_monitoring": True
            },
            "audit_requirements": {
                "financial_access_logging": "mandatory",
                "audit_log_retention_years": 7,
                "real_time_monitoring": True,
                "automated_control_testing": True,
                "quarterly_compliance_review": True,
                "external_auditor_access": True
            },
            "additional_roles": [
                {
                    "role_name": "financial_controller",
                    "description": "Financial controller with oversight responsibilities",
                    "permissions": ["financial_data_access", "control_testing", "sox_reporting"]
                },
                {
                    "role_name": "sox_compliance_manager",
                    "description": "SOX compliance oversight and testing",
                    "permissions": ["control_design", "testing_oversight", "deficiency_tracking"]
                },
                {
                    "role_name": "financial_analyst",
                    "description": "Financial data analysis with restrictions",
                    "permissions": ["financial_read", "report_generation", "data_analysis"]
                }
            ],
            "default_permissions": {
                "financial_controller": ["all_financial_data", "approve_transactions", "control_oversight"],
                "sox_compliance_manager": ["audit_controls", "testing_management", "compliance_reporting"],
                "financial_analyst": ["financial_read", "standard_reports", "data_queries"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "financial_data_retention_years": 7,
                "audit_log_retention_years": 7,
                "sox_documentation_retention_years": 7,
                "control_testing_retention_years": 5,
                "backup_retention_years": 10
            },
            "privacy_settings": {
                "financial_data_segregation": True,
                "role_based_data_access": True,
                "transaction_approval_workflows": True,
                "sensitive_data_masking": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "unusual_financial_access",
                    "description": "Detect unusual financial data access",
                    "condition": "financial_queries > 100 per day",
                    "action": "alert_compliance_manager"
                },
                {
                    "rule_name": "segregation_violation",
                    "description": "Detect segregation of duties violations",
                    "condition": "user accesses conflicting functions",
                    "action": "block_access_alert_manager"
                }
            ],
            "alert_thresholds": {
                "failed_login_attempts": 5,
                "concurrent_sessions": 3,
                "financial_queries_per_day": 100,
                "large_data_export_mb": 500,
                "after_hours_access": True
            },
            "setup_guide_url": "https://docs.example.com/finance-sox-setup",
            "training_materials": [
                "SOX Compliance Overview",
                "Internal Controls Framework",
                "Segregation of Duties Principles",
                "Financial Data Security"
            ],
            "compliance_checklist": [
                "Configure segregation of duties matrix",
                "Set up automated control testing",
                "Implement approval workflows",
                "Enable financial data monitoring",
                "Configure audit trail retention",
                "Test internal controls",
                "Validate user access rights"
            ]
        }

    def _create_education_template(self) -> Dict[str, Any]:
        """Create FERPA-compliant education template."""
        return {
            "template_name": "Educational Institution FERPA Compliance",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "ferpa_access_log",
                    "description": "FERPA-compliant student record access logging",
                    "columns": [
                        {"name": "access_id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "student_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "record_type", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "educational_purpose", "type": "TEXT", "nullable": False},
                        {"name": "access_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "disclosure_authorized", "type": "BOOLEAN", "default": False},
                        {"name": "parent_consent_required", "type": "BOOLEAN", "default": False}
                    ]
                },
                {
                    "table_name": "student_consent_directory",
                    "description": "Student directory information disclosure consent",
                    "columns": [
                        {"name": "consent_id", "type": "UUID", "primary_key": True},
                        {"name": "student_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "directory_info_release", "type": "BOOLEAN", "default": False},
                        {"name": "research_participation", "type": "BOOLEAN", "default": False},
                        {"name": "parent_guardian_id", "type": "VARCHAR(50)", "nullable": True},
                        {"name": "consent_date", "type": "TIMESTAMP", "nullable": False},
                        {"name": "expiry_date", "type": "TIMESTAMP", "nullable": True}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "ferpa_training_completed", "type": "BOOLEAN", "default": False},
                        {"name": "educational_relationship", "type": "VARCHAR(50)", "nullable": True},
                        {"name": "student_consent_on_file", "type": "BOOLEAN", "default": False}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "ferpa_access_log", "columns": ["student_id", "access_timestamp"], "type": "btree"},
                {"table": "student_consent_directory", "columns": ["student_id"], "type": "unique"}
            ],
            "compliance_frameworks": [ComplianceFramework.FERPA],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "educational_purpose",
                "audit_logging": "comprehensive",
                "student_data_isolation": True
            },
            "audit_requirements": {
                "student_record_access_logging": "mandatory",
                "audit_log_retention_years": 5,
                "parent_notification_tracking": True
            },
            "additional_roles": [
                {
                    "role_name": "registrar",
                    "description": "Student records management",
                    "permissions": ["student_records", "transcript_access", "enrollment_data"]
                },
                {
                    "role_name": "academic_advisor",
                    "description": "Student academic guidance and support",
                    "permissions": ["academic_records", "course_planning", "student_communication"]
                }
            ],
            "default_permissions": {
                "registrar": ["full_student_records", "transcript_management", "enrollment_data"],
                "academic_advisor": ["academic_records", "advising_notes", "course_access"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "student_record_retention_years": 5,
                "audit_log_retention_years": 5,
                "consent_record_retention_years": 7
            },
            "privacy_settings": {
                "directory_info_protection": True,
                "parent_consent_tracking": True,
                "educational_purpose_validation": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "unauthorized_student_access",
                    "description": "Detect unauthorized student record access",
                    "condition": "access without educational purpose",
                    "action": "alert_privacy_officer"
                }
            ],
            "alert_thresholds": {
                "failed_login_attempts": 3,
                "student_record_access_per_day": 50
            },
            "setup_guide_url": "https://docs.example.com/education-ferpa-setup",
            "training_materials": [
                "FERPA Privacy Requirements",
                "Student Record Protection",
                "Directory Information Guidelines"
            ],
            "compliance_checklist": [
                "Configure student consent tracking",
                "Set up educational purpose validation",
                "Enable parent notification system",
                "Implement directory info controls"
            ]
        }

    def _create_retail_template(self) -> Dict[str, Any]:
        """Create PCI DSS-compliant retail template."""
        return {
            "template_name": "Retail PCI DSS Compliance",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "pci_security_events",
                    "description": "PCI DSS security event monitoring",
                    "columns": [
                        {"name": "event_id", "type": "UUID", "primary_key": True},
                        {"name": "event_type", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "cardholder_data_involved", "type": "BOOLEAN", "default": False},
                        {"name": "timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "risk_level", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "remediation_status", "type": "VARCHAR(50)", "default": "pending"}
                    ]
                },
                {
                    "table_name": "cardholder_data_access",
                    "description": "Cardholder data access logging for PCI compliance",
                    "columns": [
                        {"name": "access_id", "type": "UUID", "primary_key": True},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "data_type", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "business_justification", "type": "TEXT", "nullable": False},
                        {"name": "access_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "data_elements_accessed", "type": "TEXT", "nullable": False},
                        {"name": "retention_period_days", "type": "INTEGER", "nullable": False}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "pci_training_completed", "type": "BOOLEAN", "default": False},
                        {"name": "cardholder_data_access_level", "type": "VARCHAR(20)", "default": "none"},
                        {"name": "last_security_assessment", "type": "TIMESTAMP", "nullable": True}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "pci_security_events", "columns": ["timestamp", "risk_level"], "type": "btree"},
                {"table": "cardholder_data_access", "columns": ["user_id", "access_timestamp"], "type": "btree"}
            ],
            "compliance_frameworks": [ComplianceFramework.PCI_DSS],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "least_privilege",
                "cardholder_data_isolation": True,
                "network_segmentation": True,
                "vulnerability_scanning": True
            },
            "audit_requirements": {
                "cardholder_data_access_logging": "mandatory",
                "security_event_monitoring": "real_time",
                "quarterly_security_testing": True,
                "annual_pci_assessment": True
            },
            "additional_roles": [
                {
                    "role_name": "payment_processor",
                    "description": "Payment processing and cardholder data access",
                    "permissions": ["payment_processing", "cardholder_data", "transaction_management"]
                },
                {
                    "role_name": "pci_compliance_officer",
                    "description": "PCI DSS compliance oversight",
                    "permissions": ["security_monitoring", "compliance_reporting", "vulnerability_management"]
                }
            ],
            "default_permissions": {
                "payment_processor": ["process_payments", "access_cardholder_data", "transaction_reports"],
                "pci_compliance_officer": ["security_monitoring", "compliance_reports", "access_controls"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "cardholder_data_retention_days": 90,
                "security_log_retention_years": 1,
                "audit_trail_retention_years": 3
            },
            "privacy_settings": {
                "cardholder_data_masking": True,
                "payment_data_encryption": True,
                "secure_data_transmission": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "cardholder_data_access",
                    "description": "Monitor cardholder data access",
                    "condition": "cardholder_data_accessed = true",
                    "action": "log_and_alert"
                },
                {
                    "rule_name": "unusual_payment_activity",
                    "description": "Detect unusual payment processing patterns",
                    "condition": "payment_volume > normal_threshold",
                    "action": "security_review"
                }
            ],
            "alert_thresholds": {
                "failed_login_attempts": 3,
                "cardholder_data_access_attempts": 10,
                "payment_volume_threshold_percent": 150
            },
            "setup_guide_url": "https://docs.example.com/retail-pci-setup",
            "training_materials": [
                "PCI DSS Requirements Overview",
                "Cardholder Data Protection",
                "Payment Security Best Practices"
            ],
            "compliance_checklist": [
                "Configure cardholder data encryption",
                "Set up payment monitoring",
                "Implement access controls",
                "Enable security event logging",
                "Configure data retention policies"
            ]
        }

    def _create_technology_template(self) -> Dict[str, Any]:
        """Create standard technology company template."""
        return {
            "template_name": "Technology Company Standard",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "api_usage_analytics",
                    "description": "API usage tracking and analytics",
                    "columns": [
                        {"name": "usage_id", "type": "UUID", "primary_key": True},
                        {"name": "api_endpoint", "type": "VARCHAR(200)", "nullable": False},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "request_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "response_time_ms", "type": "INTEGER", "nullable": False},
                        {"name": "status_code", "type": "INTEGER", "nullable": False},
                        {"name": "data_volume_bytes", "type": "BIGINT", "nullable": False}
                    ]
                },
                {
                    "table_name": "feature_usage_tracking",
                    "description": "Product feature usage analytics",
                    "columns": [
                        {"name": "tracking_id", "type": "UUID", "primary_key": True},
                        {"name": "feature_name", "type": "VARCHAR(100)", "nullable": False},
                        {"name": "user_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "usage_timestamp", "type": "TIMESTAMP", "nullable": False},
                        {"name": "session_duration_seconds", "type": "INTEGER", "nullable": False},
                        {"name": "feature_success", "type": "BOOLEAN", "default": True}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "developer_access_level", "type": "VARCHAR(20)", "default": "basic"},
                        {"name": "api_key_issued", "type": "BOOLEAN", "default": False},
                        {"name": "feature_flags", "type": "JSON", "nullable": True}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "api_usage_analytics", "columns": ["user_id", "request_timestamp"], "type": "btree"},
                {"table": "feature_usage_tracking", "columns": ["feature_name", "usage_timestamp"], "type": "btree"}
            ],
            "compliance_frameworks": [ComplianceFramework.SOC2, ComplianceFramework.ISO27001],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "api_key_based",
                "rate_limiting": True,
                "api_monitoring": True
            },
            "audit_requirements": {
                "api_access_logging": "comprehensive",
                "feature_usage_tracking": True,
                "security_monitoring": "automated"
            },
            "additional_roles": [
                {
                    "role_name": "developer",
                    "description": "Software developer with API access",
                    "permissions": ["api_access", "feature_development", "testing_environment"]
                },
                {
                    "role_name": "product_manager",
                    "description": "Product management and analytics access",
                    "permissions": ["analytics_access", "feature_configuration", "usage_reports"]
                }
            ],
            "default_permissions": {
                "developer": ["api_access", "development_tools", "testing_data"],
                "product_manager": ["analytics_dashboard", "feature_analytics", "user_insights"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "api_logs_retention_days": 90,
                "feature_usage_retention_days": 365,
                "analytics_data_retention_years": 2
            },
            "privacy_settings": {
                "user_data_anonymization": True,
                "analytics_opt_out": True,
                "data_portability": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "api_rate_limit_exceeded",
                    "description": "Monitor API rate limit violations",
                    "condition": "requests_per_minute > rate_limit",
                    "action": "throttle_and_alert"
                }
            ],
            "alert_thresholds": {
                "api_requests_per_minute": 1000,
                "failed_api_calls_percent": 5,
                "feature_error_rate_percent": 2
            },
            "setup_guide_url": "https://docs.example.com/technology-setup",
            "training_materials": [
                "API Security Best Practices",
                "Feature Development Guidelines",
                "Analytics and Privacy"
            ],
            "compliance_checklist": [
                "Configure API rate limiting",
                "Set up usage analytics",
                "Implement feature tracking",
                "Enable security monitoring"
            ]
        }

    def _create_manufacturing_template(self) -> Dict[str, Any]:
        """Create manufacturing industry template."""
        return {
            "template_name": "Manufacturing Industry Standard",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "quality_control_data",
                    "description": "Quality control and compliance tracking",
                    "columns": [
                        {"name": "qc_id", "type": "UUID", "primary_key": True},
                        {"name": "product_batch", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "inspection_date", "type": "TIMESTAMP", "nullable": False},
                        {"name": "quality_metrics", "type": "JSON", "nullable": False},
                        {"name": "compliance_status", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "inspector_id", "type": "VARCHAR(50)", "nullable": False}
                    ]
                }
            ],
            "additional_columns": [],
            "additional_indexes": [
                {"table": "quality_control_data", "columns": ["product_batch", "inspection_date"], "type": "btree"}
            ],
            "compliance_frameworks": [ComplianceFramework.ISO27001],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "role_based"
            },
            "audit_requirements": {
                "quality_tracking": "mandatory",
                "production_audit_trail": True
            },
            "additional_roles": [
                {
                    "role_name": "quality_inspector",
                    "description": "Quality control and inspection",
                    "permissions": ["quality_data", "inspection_reports", "compliance_tracking"]
                }
            ],
            "default_permissions": {
                "quality_inspector": ["quality_data_access", "inspection_tools", "compliance_reports"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "quality_data_retention_years": 5,
                "audit_trail_retention_years": 7
            },
            "privacy_settings": {
                "production_data_protection": True
            },
            "monitoring_rules": [],
            "alert_thresholds": {
                "quality_failure_rate_percent": 5
            },
            "setup_guide_url": "https://docs.example.com/manufacturing-setup",
            "training_materials": [
                "Quality Control Procedures",
                "Manufacturing Data Security"
            ],
            "compliance_checklist": [
                "Configure quality tracking",
                "Set up production monitoring",
                "Implement audit trails"
            ]
        }

    def _create_government_template(self) -> Dict[str, Any]:
        """Create government/public sector template."""
        return {
            "template_name": "Government/Public Sector",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "fisma_compliance_tracking",
                    "description": "FISMA compliance and security controls",
                    "columns": [
                        {"name": "control_id", "type": "UUID", "primary_key": True},
                        {"name": "nist_control_family", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "implementation_status", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "assessment_date", "type": "TIMESTAMP", "nullable": False},
                        {"name": "risk_level", "type": "VARCHAR(20)", "nullable": False},
                        {"name": "remediation_plan", "type": "TEXT", "nullable": True}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "security_clearance_level", "type": "VARCHAR(20)", "nullable": True},
                        {"name": "background_check_date", "type": "TIMESTAMP", "nullable": True}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "fisma_compliance_tracking", "columns": ["nist_control_family", "assessment_date"], "type": "btree"}
            ],
            "compliance_frameworks": [ComplianceFramework.FISMA],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "clearance_based",
                "comprehensive_logging": True
            },
            "audit_requirements": {
                "fisma_controls_monitoring": "mandatory",
                "security_assessment_annual": True
            },
            "additional_roles": [
                {
                    "role_name": "security_control_assessor",
                    "description": "FISMA security controls assessment",
                    "permissions": ["security_assessment", "compliance_monitoring", "risk_management"]
                }
            ],
            "default_permissions": {
                "security_control_assessor": ["security_controls", "compliance_reports", "risk_assessment"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "security_data_retention_years": 10,
                "compliance_records_retention_years": 10
            },
            "privacy_settings": {
                "classified_data_protection": True,
                "clearance_based_access": True
            },
            "monitoring_rules": [
                {
                    "rule_name": "security_control_violation",
                    "description": "FISMA security control violations",
                    "condition": "control_failure_detected",
                    "action": "immediate_escalation"
                }
            ],
            "alert_thresholds": {
                "security_control_failures": 1,
                "unauthorized_access_attempts": 1
            },
            "setup_guide_url": "https://docs.example.com/government-fisma-setup",
            "training_materials": [
                "FISMA Security Controls",
                "Government Data Protection",
                "NIST Cybersecurity Framework"
            ],
            "compliance_checklist": [
                "Implement FISMA controls",
                "Configure security monitoring",
                "Set up clearance validation",
                "Enable comprehensive logging"
            ]
        }

    def _create_nonprofit_template(self) -> Dict[str, Any]:
        """Create nonprofit organization template."""
        return {
            "template_name": "Nonprofit Organization",
            "template_version": "1.0.0",
            "additional_tables": [
                {
                    "table_name": "donor_privacy_controls",
                    "description": "Donor privacy and communication preferences",
                    "columns": [
                        {"name": "control_id", "type": "UUID", "primary_key": True},
                        {"name": "donor_id", "type": "VARCHAR(50)", "nullable": False},
                        {"name": "anonymity_requested", "type": "BOOLEAN", "default": False},
                        {"name": "communication_opt_out", "type": "BOOLEAN", "default": False},
                        {"name": "data_sharing_consent", "type": "BOOLEAN", "default": False},
                        {"name": "preference_date", "type": "TIMESTAMP", "nullable": False}
                    ]
                }
            ],
            "additional_columns": [
                {
                    "table": "users",
                    "columns": [
                        {"name": "volunteer_status", "type": "BOOLEAN", "default": False},
                        {"name": "donor_privacy_level", "type": "VARCHAR(20)", "default": "standard"}
                    ]
                }
            ],
            "additional_indexes": [
                {"table": "donor_privacy_controls", "columns": ["donor_id"], "type": "unique"}
            ],
            "compliance_frameworks": [],
            "security_requirements": {
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "role_based",
                "donor_data_protection": True
            },
            "audit_requirements": {
                "donor_privacy_tracking": "mandatory",
                "financial_transparency": True
            },
            "additional_roles": [
                {
                    "role_name": "development_coordinator",
                    "description": "Fundraising and donor relationship management",
                    "permissions": ["donor_data", "fundraising_reports", "communication_management"]
                }
            ],
            "default_permissions": {
                "development_coordinator": ["donor_data_access", "fundraising_tools", "communication_tracking"],
                "user": ["own_profile", "basic_query"]
            },
            "data_retention_policies": {
                "donor_data_retention_years": 7,
                "financial_records_retention_years": 7
            },
            "privacy_settings": {
                "donor_anonymity_support": True,
                "communication_preferences": True
            },
            "monitoring_rules": [],
            "alert_thresholds": {
                "data_access_violations": 1
            },
            "setup_guide_url": "https://docs.example.com/nonprofit-setup",
            "training_materials": [
                "Donor Privacy Best Practices",
                "Nonprofit Data Management"
            ],
            "compliance_checklist": [
                "Configure donor privacy controls",
                "Set up communication preferences",
                "Implement financial transparency"
            ]
        }

    def _get_general_template(self) -> IndustryTemplate:
        """Get general template for industries not specifically configured."""
        return IndustryTemplate(
            industry=IndustryType.GENERAL,
            template_name="General Purpose",
            template_version="1.0.0",
            additional_tables=[],
            additional_columns=[],
            additional_indexes=[],
            compliance_frameworks=[],
            security_requirements={
                "encryption_at_rest": True,
                "encryption_in_transit": True,
                "access_controls": "role_based"
            },
            audit_requirements={
                "basic_audit_logging": True
            },
            additional_roles=[],
            default_permissions={
                "user": ["own_profile", "basic_query"]
            },
            data_retention_policies={
                "general_data_retention_years": 3
            },
            privacy_settings={
                "basic_privacy_controls": True
            },
            monitoring_rules=[],
            alert_thresholds={},
            training_materials=[],
            compliance_checklist=[]
        )

    def _initialize_compliance_mappings(self) -> Dict[ComplianceFramework, List[str]]:
        """Initialize mapping between compliance frameworks and required features."""
        return {
            ComplianceFramework.HIPAA: [
                "phi_access_logging", "patient_consent_tracking", "breach_detection",
                "minimum_necessary_enforcement", "audit_trail_retention"
            ],
            ComplianceFramework.SOX: [
                "financial_controls_testing", "segregation_of_duties", "audit_trail",
                "internal_controls_documentation", "quarterly_testing"
            ],
            ComplianceFramework.GDPR: [
                "consent_management", "right_to_erasure", "data_portability",
                "privacy_by_design", "breach_notification"
            ],
            ComplianceFramework.PCI_DSS: [
                "cardholder_data_protection", "access_controls", "network_segmentation",
                "vulnerability_management", "security_monitoring"
            ],
            ComplianceFramework.FERPA: [
                "educational_record_protection", "directory_information_controls",
                "parent_consent_tracking", "legitimate_educational_interest"
            ],
            ComplianceFramework.SOC2: [
                "security_controls", "availability_monitoring", "processing_integrity",
                "confidentiality_controls", "privacy_protection"
            ],
            ComplianceFramework.ISO27001: [
                "information_security_management", "risk_assessment", "security_controls",
                "incident_management", "business_continuity"
            ],
            ComplianceFramework.CCPA: [
                "consumer_rights", "data_disclosure", "opt_out_mechanisms",
                "privacy_policy_management", "data_deletion"
            ],
            ComplianceFramework.FISMA: [
                "nist_controls", "security_categorization", "continuous_monitoring",
                "security_assessment", "authorization"
            ]
        }

    def get_compliance_requirements(self, frameworks: List[ComplianceFramework]) -> List[str]:
        """Get combined compliance requirements for multiple frameworks."""
        requirements = set()
        for framework in frameworks:
            if framework in self.compliance_mappings:
                requirements.update(self.compliance_mappings[framework])
        return list(requirements)

    def validate_template_compliance(self, template: IndustryTemplate) -> Dict[str, Any]:
        """Validate that template meets all compliance requirements."""
        required_features = self.get_compliance_requirements(template.compliance_frameworks)

        validation_result = {
            "compliant": True,
            "missing_features": [],
            "recommendations": [],
            "compliance_score": 0
        }

        # Check for required features based on compliance frameworks
        implemented_features = []

        # Analyze template components for compliance features
        for table in template.additional_tables:
            table_name = table.get("table_name", "")
            if "audit" in table_name or "log" in table_name:
                implemented_features.append("audit_trail")
            if "consent" in table_name:
                implemented_features.append("consent_management")
            if "compliance" in table_name:
                implemented_features.append("compliance_tracking")

        # Check missing features
        missing_features = set(required_features) - set(implemented_features)
        validation_result["missing_features"] = list(missing_features)
        validation_result["compliant"] = len(missing_features) == 0

        if required_features:
            validation_result["compliance_score"] = int(
                ((len(required_features) - len(missing_features)) / len(required_features)) * 100
            )

        return validation_result