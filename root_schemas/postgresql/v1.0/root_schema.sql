-- ============================================================================
-- Multi-Tenant NLP2SQL Root Schema - PostgreSQL v1.0
-- ============================================================================

-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Schema metadata table
CREATE TABLE IF NOT EXISTS schema_info (
    schema_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    database_type VARCHAR(20) NOT NULL DEFAULT 'postgresql' CHECK (database_type IN ('mysql', 'postgresql', 'sqlite', 'mongodb')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_schema_version ON schema_info (schema_version);
CREATE INDEX IF NOT EXISTS idx_database_type ON schema_info (database_type);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_name VARCHAR(255) NOT NULL UNIQUE,
    org_code VARCHAR(50) NOT NULL UNIQUE,
    database_type VARCHAR(20) NOT NULL CHECK (database_type IN ('mysql', 'postgresql', 'sqlite', 'mongodb')),
    database_name VARCHAR(255) NOT NULL,
    database_config JSONB,
    subscription_tier VARCHAR(20) DEFAULT 'basic' CHECK (subscription_tier IN ('basic', 'premium', 'enterprise')),
    max_users INTEGER DEFAULT 50,
    max_queries_per_day INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_org_name ON organizations (org_name);
CREATE INDEX IF NOT EXISTS idx_org_code ON organizations (org_code);
CREATE INDEX IF NOT EXISTS idx_org_database_type ON organizations (database_type);
CREATE INDEX IF NOT EXISTS idx_org_is_active ON organizations (is_active);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    department VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'analyst', 'viewer', 'power_user')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(username, org_id),
    UNIQUE(email, org_id)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users (org_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users (last_login);

-- Human Digital Twins (HDT) profiles
CREATE TABLE IF NOT EXISTS hdt_profiles (
    hdt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    context JSONB,
    skillset JSONB,
    languages JSONB,
    preferences JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_hdt_user_id ON hdt_profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_hdt_org_id ON hdt_profiles (org_id);
CREATE INDEX IF NOT EXISTS idx_hdt_name ON hdt_profiles (name);
CREATE INDEX IF NOT EXISTS idx_hdt_is_active ON hdt_profiles (is_active);

-- HDT Agents
CREATE TABLE IF NOT EXISTS hdt_agents (
    agent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hdt_id UUID NOT NULL REFERENCES hdt_profiles(hdt_id) ON DELETE CASCADE,
    agent_type VARCHAR(20) NOT NULL CHECK (agent_type IN ('analyst', 'reporter', 'validator', 'optimizer')),
    agent_config JSONB,
    capabilities JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agents_hdt_id ON hdt_agents (hdt_id);
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON hdt_agents (agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON hdt_agents (is_active);

-- Query logs
CREATE TABLE IF NOT EXISTS query_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    hdt_id UUID REFERENCES hdt_profiles(hdt_id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    query_type VARCHAR(20) DEFAULT 'nlp2sql' CHECK (query_type IN ('nlp2sql', 'direct_sql', 'template')),
    execution_status VARCHAR(20) NOT NULL CHECK (execution_status IN ('success', 'error', 'blocked', 'timeout')),
    execution_time_ms INTEGER,
    result_rows INTEGER DEFAULT 0,
    error_message TEXT,
    security_flags JSONB,
    client_ip INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_query_logs_org_id ON query_logs (org_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_execution_status ON query_logs (execution_status);
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_query_logs_query_type ON query_logs (query_type);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(20) CHECK (role IN ('admin', 'analyst', 'viewer', 'power_user')),
    resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('table', 'column', 'schema', 'function')),
    resource_name VARCHAR(255) NOT NULL,
    permission_type VARCHAR(20) NOT NULL CHECK (permission_type IN ('select', 'insert', 'update', 'delete', 'create', 'drop', 'all')),
    is_granted BOOLEAN DEFAULT TRUE,
    granted_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_permissions_org_id ON permissions (org_id);
CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON permissions (user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON permissions (role);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions (resource_type, resource_name);
CREATE INDEX IF NOT EXISTS idx_permissions_permission_type ON permissions (permission_type);
CREATE INDEX IF NOT EXISTS idx_permissions_expires_at ON permissions (expires_at);

-- Security audit logs
CREATE TABLE IF NOT EXISTS security_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    event_type VARCHAR(30) NOT NULL CHECK (event_type IN ('login_success', 'login_failed', 'query_blocked', 'permission_denied', 'suspicious_activity')),
    event_details JSONB,
    severity VARCHAR(10) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    client_ip INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_security_logs_org_id ON security_logs (org_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs (event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_severity ON security_logs (severity);
CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs (timestamp);

-- API tokens for service-to-service communication
CREATE TABLE IF NOT EXISTS api_tokens (
    token_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    token_name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_org_id ON api_tokens (org_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_token_hash ON api_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_api_tokens_is_active ON api_tokens (is_active);
CREATE INDEX IF NOT EXISTS idx_api_tokens_expires_at ON api_tokens (expires_at);

-- System settings and configurations
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(org_id) ON DELETE CASCADE,
    setting_key VARCHAR(255) NOT NULL,
    setting_value JSONB,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'number', 'boolean', 'json', 'array')),
    is_global BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(org_id, setting_key)
);

CREATE INDEX IF NOT EXISTS idx_system_settings_org_id ON system_settings (org_id);
CREATE INDEX IF NOT EXISTS idx_system_settings_setting_key ON system_settings (setting_key);
CREATE INDEX IF NOT EXISTS idx_system_settings_is_global ON system_settings (is_global);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_schema_info_updated_at BEFORE UPDATE ON schema_info FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_hdt_profiles_updated_at BEFORE UPDATE ON hdt_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial schema info
INSERT INTO schema_info (schema_version, database_type, description)
VALUES ('v1.0', 'postgresql', 'Initial root schema for Multi-Tenant NLP2SQL PostgreSQL databases')
ON CONFLICT DO NOTHING;

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, is_global, description)
VALUES
    ('max_query_timeout_seconds', '300', 'number', TRUE, 'Maximum query execution timeout in seconds'),
    ('max_result_rows', '10000', 'number', TRUE, 'Maximum number of rows to return in query results'),
    ('enable_query_caching', 'true', 'boolean', TRUE, 'Enable query result caching'),
    ('default_export_format', '"json"', 'string', TRUE, 'Default export format for query results'),
    ('security_level', '"medium"', 'string', TRUE, 'Default security level for query validation')
ON CONFLICT DO NOTHING;