-- ============================================================================
-- MySQL Migration Script: v1.0 to v1.1
-- Multi-Tenant NLP2SQL Root Schema Migration
-- ============================================================================

-- Check current schema version
SELECT schema_version FROM schema_info WHERE database_type = 'mysql' ORDER BY created_at DESC LIMIT 1;

-- Begin transaction
START TRANSACTION;

-- Update schema info
UPDATE schema_info
SET schema_version = 'v1.1',
    updated_at = CURRENT_TIMESTAMP,
    description = 'Schema v1.1 with enhanced security and performance features'
WHERE database_type = 'mysql' AND schema_version = 'v1.0';

-- Add new columns to existing tables

-- Enhance organizations table
ALTER TABLE organizations
ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC' AFTER max_queries_per_day,
ADD COLUMN data_retention_days INT DEFAULT 365 AFTER timezone,
ADD COLUMN security_level ENUM('basic', 'enhanced', 'strict') DEFAULT 'basic' AFTER data_retention_days,
ADD COLUMN api_rate_limit INT DEFAULT 1000 AFTER security_level;

-- Add index for new columns
CREATE INDEX idx_organizations_timezone ON organizations (timezone);
CREATE INDEX idx_organizations_security_level ON organizations (security_level);

-- Enhance users table with additional security features
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20) AFTER department,
ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE AFTER failed_login_attempts,
ADD COLUMN password_expires_at TIMESTAMP NULL AFTER locked_until,
ADD COLUMN consent_given BOOLEAN DEFAULT FALSE AFTER password_expires_at,
ADD COLUMN consent_date TIMESTAMP NULL AFTER consent_given,
ADD COLUMN data_processing_consent JSON AFTER consent_date;

-- Add indexes for new user columns
CREATE INDEX idx_users_phone_number ON users (phone_number);
CREATE INDEX idx_users_two_factor_enabled ON users (two_factor_enabled);
CREATE INDEX idx_users_password_expires_at ON users (password_expires_at);
CREATE INDEX idx_users_consent_given ON users (consent_given);

-- Enhance HDT profiles with versioning
ALTER TABLE hdt_profiles
ADD COLUMN version VARCHAR(10) DEFAULT 'v1.0' AFTER preferences,
ADD COLUMN training_data JSON AFTER version,
ADD COLUMN performance_metrics JSON AFTER training_data,
ADD COLUMN last_training_update TIMESTAMP NULL AFTER performance_metrics;

-- Add index for HDT version
CREATE INDEX idx_hdt_profiles_version ON hdt_profiles (version);

-- Enhance query logs with additional metadata
ALTER TABLE query_logs
ADD COLUMN query_complexity_score DECIMAL(5,2) AFTER result_rows,
ADD COLUMN cached_result BOOLEAN DEFAULT FALSE AFTER query_complexity_score,
ADD COLUMN data_sources JSON AFTER cached_result,
ADD COLUMN compliance_flags JSON AFTER security_flags;

-- Add indexes for query log enhancements
CREATE INDEX idx_query_logs_complexity_score ON query_logs (query_complexity_score);
CREATE INDEX idx_query_logs_cached_result ON query_logs (cached_result);

-- Create new tables for v1.1

-- Query templates table
CREATE TABLE IF NOT EXISTS query_templates (
    template_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    created_by VARCHAR(36) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,
    template_sql TEXT NOT NULL,
    template_parameters JSON,
    usage_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_template_org_id (org_id),
    INDEX idx_template_created_by (created_by),
    INDEX idx_template_name (template_name),
    INDEX idx_template_is_public (is_public),
    INDEX idx_template_usage_count (usage_count)
);

-- Query cache table
CREATE TABLE IF NOT EXISTS query_cache (
    cache_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    result_data LONGTEXT,
    result_count INT,
    cache_hit_count INT DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE KEY unique_org_query_hash (org_id, query_hash),
    INDEX idx_cache_org_id (org_id),
    INDEX idx_cache_query_hash (query_hash),
    INDEX idx_cache_expires_at (expires_at),
    INDEX idx_cache_hit_count (cache_hit_count)
);

-- Data compliance table
CREATE TABLE IF NOT EXISTS data_compliance (
    compliance_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    data_type ENUM('pii', 'financial', 'healthcare', 'general') NOT NULL,
    retention_period_days INT NOT NULL,
    anonymization_required BOOLEAN DEFAULT FALSE,
    encryption_required BOOLEAN DEFAULT FALSE,
    access_restrictions JSON,
    compliance_regulations JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_compliance_org_id (org_id),
    INDEX idx_compliance_data_type (data_type),
    INDEX idx_compliance_retention_period (retention_period_days)
);

-- Notification settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    setting_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    notification_type ENUM('email', 'sms', 'push', 'webhook') NOT NULL,
    event_types JSON NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    delivery_settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_notification_org_id (org_id),
    INDEX idx_notification_user_id (user_id),
    INDEX idx_notification_type (notification_type),
    INDEX idx_notification_enabled (is_enabled)
);

-- Add new system settings for v1.1
INSERT INTO system_settings (setting_key, setting_value, setting_type, is_global, description)
VALUES
    ('query_cache_enabled', 'true', 'boolean', TRUE, 'Enable query result caching'),
    ('query_cache_ttl_minutes', '60', 'number', TRUE, 'Query cache time-to-live in minutes'),
    ('max_template_parameters', '10', 'number', TRUE, 'Maximum parameters allowed in query templates'),
    ('two_factor_auth_required', 'false', 'boolean', FALSE, 'Require two-factor authentication for organization'),
    ('password_expiry_days', '90', 'number', FALSE, 'Password expiration period in days'),
    ('audit_log_retention_days', '730', 'number', TRUE, 'Audit log retention period in days'),
    ('gdpr_compliance_mode', 'false', 'boolean', FALSE, 'Enable GDPR compliance features'),
    ('data_anonymization_enabled', 'false', 'boolean', FALSE, 'Enable automatic data anonymization')
ON DUPLICATE KEY UPDATE
    setting_value = VALUES(setting_value),
    updated_at = CURRENT_TIMESTAMP;

-- Create triggers for audit logging on sensitive operations

-- Trigger for user modifications
DELIMITER //
CREATE TRIGGER audit_user_changes
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO security_logs (org_id, user_id, event_type, event_details, severity, timestamp)
    VALUES (
        NEW.org_id,
        NEW.user_id,
        'user_modified',
        JSON_OBJECT(
            'changed_fields', JSON_ARRAY(
                CASE WHEN OLD.role != NEW.role THEN 'role' ELSE NULL END,
                CASE WHEN OLD.is_active != NEW.is_active THEN 'is_active' ELSE NULL END,
                CASE WHEN OLD.failed_login_attempts != NEW.failed_login_attempts THEN 'failed_login_attempts' ELSE NULL END
            ),
            'old_role', OLD.role,
            'new_role', NEW.role
        ),
        CASE
            WHEN OLD.role != NEW.role THEN 'high'
            WHEN OLD.is_active != NEW.is_active THEN 'medium'
            ELSE 'low'
        END,
        CURRENT_TIMESTAMP
    );
END//
DELIMITER ;

-- Trigger for permission changes
DELIMITER //
CREATE TRIGGER audit_permission_changes
AFTER INSERT ON permissions
FOR EACH ROW
BEGIN
    INSERT INTO security_logs (org_id, user_id, event_type, event_details, severity, timestamp)
    VALUES (
        NEW.org_id,
        NEW.user_id,
        'permission_granted',
        JSON_OBJECT(
            'resource_type', NEW.resource_type,
            'resource_name', NEW.resource_name,
            'permission_type', NEW.permission_type,
            'granted_by', NEW.granted_by
        ),
        'medium',
        CURRENT_TIMESTAMP
    );
END//
DELIMITER ;

-- Update schema version to v1.1
INSERT INTO schema_info (schema_version, database_type, description, is_active)
VALUES ('v1.1', 'mysql', 'Enhanced schema with security features, query caching, and compliance tools', TRUE);

-- Commit transaction
COMMIT;

-- Verify migration
SELECT
    'Migration completed successfully' as status,
    schema_version,
    created_at,
    updated_at
FROM schema_info
WHERE database_type = 'mysql'
ORDER BY created_at DESC
LIMIT 1;