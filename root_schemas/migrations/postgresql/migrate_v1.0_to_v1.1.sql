-- ============================================================================
-- PostgreSQL Migration Script: v1.0 to v1.1
-- Multi-Tenant NLP2SQL Root Schema Migration
-- ============================================================================

-- Check current schema version
SELECT schema_version FROM schema_info WHERE database_type = 'postgresql' ORDER BY created_at DESC LIMIT 1;

-- Begin transaction
BEGIN;

-- Update schema info
UPDATE schema_info
SET schema_version = 'v1.1',
    updated_at = CURRENT_TIMESTAMP,
    description = 'Schema v1.1 with enhanced security and performance features'
WHERE database_type = 'postgresql' AND schema_version = 'v1.0';

-- Add new columns to existing tables

-- Enhance organizations table
ALTER TABLE organizations
ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN data_retention_days INTEGER DEFAULT 365,
ADD COLUMN security_level VARCHAR(20) DEFAULT 'basic' CHECK (security_level IN ('basic', 'enhanced', 'strict')),
ADD COLUMN api_rate_limit INTEGER DEFAULT 1000;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_organizations_timezone ON organizations (timezone);
CREATE INDEX IF NOT EXISTS idx_organizations_security_level ON organizations (security_level);

-- Enhance users table with additional security features
ALTER TABLE users
ADD COLUMN phone_number VARCHAR(20),
ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN password_expires_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN consent_given BOOLEAN DEFAULT FALSE,
ADD COLUMN consent_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN data_processing_consent JSONB;

-- Add indexes for new user columns
CREATE INDEX IF NOT EXISTS idx_users_phone_number ON users (phone_number);
CREATE INDEX IF NOT EXISTS idx_users_two_factor_enabled ON users (two_factor_enabled);
CREATE INDEX IF NOT EXISTS idx_users_password_expires_at ON users (password_expires_at);
CREATE INDEX IF NOT EXISTS idx_users_consent_given ON users (consent_given);

-- Enhance HDT profiles with versioning
ALTER TABLE hdt_profiles
ADD COLUMN version VARCHAR(10) DEFAULT 'v1.0',
ADD COLUMN training_data JSONB,
ADD COLUMN performance_metrics JSONB,
ADD COLUMN last_training_update TIMESTAMP WITH TIME ZONE;

-- Add index for HDT version
CREATE INDEX IF NOT EXISTS idx_hdt_profiles_version ON hdt_profiles (version);

-- Enhance query logs with additional metadata
ALTER TABLE query_logs
ADD COLUMN query_complexity_score DECIMAL(5,2),
ADD COLUMN cached_result BOOLEAN DEFAULT FALSE,
ADD COLUMN data_sources JSONB,
ADD COLUMN compliance_flags JSONB;

-- Add indexes for query log enhancements
CREATE INDEX IF NOT EXISTS idx_query_logs_complexity_score ON query_logs (query_complexity_score);
CREATE INDEX IF NOT EXISTS idx_query_logs_cached_result ON query_logs (cached_result);

-- Create new tables for v1.1

-- Query templates table
CREATE TABLE IF NOT EXISTS query_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    template_name VARCHAR(255) NOT NULL,
    template_description TEXT,
    template_sql TEXT NOT NULL,
    template_parameters JSONB,
    usage_count INTEGER DEFAULT 0,
    is_public BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_org_id ON query_templates (org_id);
CREATE INDEX IF NOT EXISTS idx_template_created_by ON query_templates (created_by);
CREATE INDEX IF NOT EXISTS idx_template_name ON query_templates (template_name);
CREATE INDEX IF NOT EXISTS idx_template_is_public ON query_templates (is_public);
CREATE INDEX IF NOT EXISTS idx_template_usage_count ON query_templates (usage_count);

-- Query cache table
CREATE TABLE IF NOT EXISTS query_cache (
    cache_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    result_data TEXT,
    result_count INTEGER,
    cache_hit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(org_id, query_hash)
);

CREATE INDEX IF NOT EXISTS idx_cache_org_id ON query_cache (org_id);
CREATE INDEX IF NOT EXISTS idx_cache_query_hash ON query_cache (query_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON query_cache (expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_hit_count ON query_cache (cache_hit_count);

-- Data compliance table
CREATE TABLE IF NOT EXISTS data_compliance (
    compliance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    data_type VARCHAR(20) NOT NULL CHECK (data_type IN ('pii', 'financial', 'healthcare', 'general')),
    retention_period_days INTEGER NOT NULL,
    anonymization_required BOOLEAN DEFAULT FALSE,
    encryption_required BOOLEAN DEFAULT FALSE,
    access_restrictions JSONB,
    compliance_regulations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_compliance_org_id ON data_compliance (org_id);
CREATE INDEX IF NOT EXISTS idx_compliance_data_type ON data_compliance (data_type);
CREATE INDEX IF NOT EXISTS idx_compliance_retention_period ON data_compliance (retention_period_days);

-- Notification settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(20) NOT NULL CHECK (notification_type IN ('email', 'sms', 'push', 'webhook')),
    event_types JSONB NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    delivery_settings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_org_id ON notification_settings (org_id);
CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notification_settings (user_id);
CREATE INDEX IF NOT EXISTS idx_notification_type ON notification_settings (notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_enabled ON notification_settings (is_enabled);

-- Add triggers for updated_at columns
CREATE TRIGGER update_query_templates_updated_at
    BEFORE UPDATE ON query_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_compliance_updated_at
    BEFORE UPDATE ON data_compliance
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_settings_updated_at
    BEFORE UPDATE ON notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

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
ON CONFLICT (org_id, setting_key) DO UPDATE SET
    setting_value = EXCLUDED.setting_value,
    updated_at = CURRENT_TIMESTAMP;

-- Create functions for audit logging

-- Function to log user changes
CREATE OR REPLACE FUNCTION audit_user_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security_logs (org_id, user_id, event_type, event_details, severity, timestamp)
    VALUES (
        NEW.org_id,
        NEW.user_id,
        'user_modified',
        jsonb_build_object(
            'changed_fields', jsonb_build_array(
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
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to log permission changes
CREATE OR REPLACE FUNCTION audit_permission_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO security_logs (org_id, user_id, event_type, event_details, severity, timestamp)
    VALUES (
        NEW.org_id,
        NEW.user_id,
        'permission_granted',
        jsonb_build_object(
            'resource_type', NEW.resource_type,
            'resource_name', NEW.resource_name,
            'permission_type', NEW.permission_type,
            'granted_by', NEW.granted_by
        ),
        'medium',
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER audit_user_changes_trigger
    AFTER UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION audit_user_changes();

CREATE TRIGGER audit_permission_changes_trigger
    AFTER INSERT ON permissions
    FOR EACH ROW
    EXECUTE FUNCTION audit_permission_changes();

-- Function for automatic cache cleanup
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM query_cache WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Update schema version to v1.1
INSERT INTO schema_info (schema_version, database_type, description, is_active)
VALUES ('v1.1', 'postgresql', 'Enhanced schema with security features, query caching, and compliance tools', TRUE);

-- Commit transaction
COMMIT;

-- Verify migration
SELECT
    'Migration completed successfully' as status,
    schema_version,
    created_at,
    updated_at
FROM schema_info
WHERE database_type = 'postgresql'
ORDER BY created_at DESC
LIMIT 1;