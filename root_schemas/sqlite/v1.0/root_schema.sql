-- ============================================================================
-- Multi-Tenant NLP2SQL Root Schema - SQLite v1.0
-- ============================================================================

-- Enable foreign key support
PRAGMA foreign_keys = ON;

-- Schema metadata table
CREATE TABLE IF NOT EXISTS schema_info (
    schema_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    schema_version TEXT NOT NULL DEFAULT 'v1.0',
    database_type TEXT NOT NULL DEFAULT 'sqlite' CHECK (database_type IN ('mysql', 'postgresql', 'sqlite', 'mongodb')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_schema_version ON schema_info (schema_version);
CREATE INDEX IF NOT EXISTS idx_database_type ON schema_info (database_type);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_name TEXT NOT NULL UNIQUE,
    org_code TEXT NOT NULL UNIQUE,
    database_type TEXT NOT NULL CHECK (database_type IN ('mysql', 'postgresql', 'sqlite', 'mongodb')),
    database_name TEXT NOT NULL,
    database_config TEXT, -- JSON as TEXT in SQLite
    subscription_tier TEXT DEFAULT 'basic' CHECK (subscription_tier IN ('basic', 'premium', 'enterprise')),
    max_users INTEGER DEFAULT 50,
    max_queries_per_day INTEGER DEFAULT 1000,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_org_name ON organizations (org_name);
CREATE INDEX IF NOT EXISTS idx_org_code ON organizations (org_code);
CREATE INDEX IF NOT EXISTS idx_org_database_type ON organizations (database_type);
CREATE INDEX IF NOT EXISTS idx_org_is_active ON organizations (is_active);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT NOT NULL,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    department TEXT,
    role TEXT NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'analyst', 'viewer', 'power_user')),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
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
    hdt_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    context TEXT, -- JSON as TEXT in SQLite
    skillset TEXT, -- JSON as TEXT in SQLite
    languages TEXT, -- JSON as TEXT in SQLite
    preferences TEXT, -- JSON as TEXT in SQLite
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_hdt_user_id ON hdt_profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_hdt_org_id ON hdt_profiles (org_id);
CREATE INDEX IF NOT EXISTS idx_hdt_name ON hdt_profiles (name);
CREATE INDEX IF NOT EXISTS idx_hdt_is_active ON hdt_profiles (is_active);

-- HDT Agents
CREATE TABLE IF NOT EXISTS hdt_agents (
    agent_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    hdt_id TEXT NOT NULL,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('analyst', 'reporter', 'validator', 'optimizer')),
    agent_config TEXT, -- JSON as TEXT in SQLite
    capabilities TEXT, -- JSON as TEXT in SQLite
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (hdt_id) REFERENCES hdt_profiles(hdt_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agents_hdt_id ON hdt_agents (hdt_id);
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON hdt_agents (agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_is_active ON hdt_agents (is_active);

-- Query logs
CREATE TABLE IF NOT EXISTS query_logs (
    log_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    hdt_id TEXT,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    query_type TEXT DEFAULT 'nlp2sql' CHECK (query_type IN ('nlp2sql', 'direct_sql', 'template')),
    execution_status TEXT NOT NULL CHECK (execution_status IN ('success', 'error', 'blocked', 'timeout')),
    execution_time_ms INTEGER,
    result_rows INTEGER DEFAULT 0,
    error_message TEXT,
    security_flags TEXT, -- JSON as TEXT in SQLite
    client_ip TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (hdt_id) REFERENCES hdt_profiles(hdt_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_query_logs_org_id ON query_logs (org_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_user_id ON query_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_query_logs_execution_status ON query_logs (execution_status);
CREATE INDEX IF NOT EXISTS idx_query_logs_timestamp ON query_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_query_logs_query_type ON query_logs (query_type);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    permission_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT NOT NULL,
    user_id TEXT,
    role TEXT CHECK (role IN ('admin', 'analyst', 'viewer', 'power_user')),
    resource_type TEXT NOT NULL CHECK (resource_type IN ('table', 'column', 'schema', 'function')),
    resource_name TEXT NOT NULL,
    permission_type TEXT NOT NULL CHECK (permission_type IN ('select', 'insert', 'update', 'delete', 'create', 'drop', 'all')),
    is_granted INTEGER DEFAULT 1 CHECK (is_granted IN (0, 1)),
    granted_by TEXT,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_permissions_org_id ON permissions (org_id);
CREATE INDEX IF NOT EXISTS idx_permissions_user_id ON permissions (user_id);
CREATE INDEX IF NOT EXISTS idx_permissions_role ON permissions (role);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions (resource_type, resource_name);
CREATE INDEX IF NOT EXISTS idx_permissions_permission_type ON permissions (permission_type);
CREATE INDEX IF NOT EXISTS idx_permissions_expires_at ON permissions (expires_at);

-- Security audit logs
CREATE TABLE IF NOT EXISTS security_logs (
    log_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT NOT NULL,
    user_id TEXT,
    event_type TEXT NOT NULL CHECK (event_type IN ('login_success', 'login_failed', 'query_blocked', 'permission_denied', 'suspicious_activity')),
    event_details TEXT, -- JSON as TEXT in SQLite
    severity TEXT DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    client_ip TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_security_logs_org_id ON security_logs (org_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_user_id ON security_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_security_logs_event_type ON security_logs (event_type);
CREATE INDEX IF NOT EXISTS idx_security_logs_severity ON security_logs (severity);
CREATE INDEX IF NOT EXISTS idx_security_logs_timestamp ON security_logs (timestamp);

-- API tokens for service-to-service communication
CREATE TABLE IF NOT EXISTS api_tokens (
    token_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT NOT NULL,
    user_id TEXT,
    token_name TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    permissions TEXT, -- JSON as TEXT in SQLite
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_tokens_org_id ON api_tokens (org_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_user_id ON api_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_api_tokens_token_hash ON api_tokens (token_hash);
CREATE INDEX IF NOT EXISTS idx_api_tokens_is_active ON api_tokens (is_active);
CREATE INDEX IF NOT EXISTS idx_api_tokens_expires_at ON api_tokens (expires_at);

-- System settings and configurations
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    org_id TEXT,
    setting_key TEXT NOT NULL,
    setting_value TEXT, -- JSON as TEXT in SQLite
    setting_type TEXT DEFAULT 'string' CHECK (setting_type IN ('string', 'number', 'boolean', 'json', 'array')),
    is_global INTEGER DEFAULT 0 CHECK (is_global IN (0, 1)),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE(org_id, setting_key)
);

CREATE INDEX IF NOT EXISTS idx_system_settings_org_id ON system_settings (org_id);
CREATE INDEX IF NOT EXISTS idx_system_settings_setting_key ON system_settings (setting_key);
CREATE INDEX IF NOT EXISTS idx_system_settings_is_global ON system_settings (is_global);

-- Triggers for updated_at columns
CREATE TRIGGER IF NOT EXISTS update_schema_info_updated_at
    AFTER UPDATE ON schema_info
    BEGIN
        UPDATE schema_info SET updated_at = CURRENT_TIMESTAMP WHERE schema_id = NEW.schema_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_organizations_updated_at
    AFTER UPDATE ON organizations
    BEGIN
        UPDATE organizations SET updated_at = CURRENT_TIMESTAMP WHERE org_id = NEW.org_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_users_updated_at
    AFTER UPDATE ON users
    BEGIN
        UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_hdt_profiles_updated_at
    AFTER UPDATE ON hdt_profiles
    BEGIN
        UPDATE hdt_profiles SET updated_at = CURRENT_TIMESTAMP WHERE hdt_id = NEW.hdt_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_system_settings_updated_at
    AFTER UPDATE ON system_settings
    BEGIN
        UPDATE system_settings SET updated_at = CURRENT_TIMESTAMP WHERE setting_id = NEW.setting_id;
    END;

-- Insert initial schema info
INSERT OR IGNORE INTO schema_info (schema_version, database_type, description)
VALUES ('v1.0', 'sqlite', 'Initial root schema for Multi-Tenant NLP2SQL SQLite databases');

-- Insert default system settings
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, is_global, description)
VALUES
    ('max_query_timeout_seconds', '300', 'number', 1, 'Maximum query execution timeout in seconds'),
    ('max_result_rows', '10000', 'number', 1, 'Maximum number of rows to return in query results'),
    ('enable_query_caching', 'true', 'boolean', 1, 'Enable query result caching'),
    ('default_export_format', 'json', 'string', 1, 'Default export format for query results'),
    ('security_level', 'medium', 'string', 1, 'Default security level for query validation');