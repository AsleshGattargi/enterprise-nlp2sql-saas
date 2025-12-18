-- ============================================================================
-- Multi-Tenant NLP2SQL Root Schema - MySQL v1.0
-- ============================================================================

-- Schema metadata table
CREATE TABLE IF NOT EXISTS schema_info (
    schema_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    schema_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    database_type ENUM('mysql', 'postgresql', 'sqlite', 'mongodb') NOT NULL DEFAULT 'mysql',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_schema_version (schema_version),
    INDEX idx_database_type (database_type)
);

-- Organizations table
CREATE TABLE IF NOT EXISTS organizations (
    org_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_name VARCHAR(255) NOT NULL UNIQUE,
    org_code VARCHAR(50) NOT NULL UNIQUE,
    database_type ENUM('mysql', 'postgresql', 'sqlite', 'mongodb') NOT NULL,
    database_name VARCHAR(255) NOT NULL,
    database_config JSON,
    subscription_tier ENUM('basic', 'premium', 'enterprise') DEFAULT 'basic',
    max_users INT DEFAULT 50,
    max_queries_per_day INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_org_name (org_name),
    INDEX idx_org_code (org_code),
    INDEX idx_database_type (database_type),
    INDEX idx_is_active (is_active)
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    department VARCHAR(100),
    role ENUM('admin', 'analyst', 'viewer', 'power_user') NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_org (username, org_id),
    UNIQUE KEY unique_email_org (email, org_id),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_org_id (org_id),
    INDEX idx_role (role),
    INDEX idx_is_active (is_active),
    INDEX idx_last_login (last_login)
);

-- Human Digital Twins (HDT) profiles
CREATE TABLE IF NOT EXISTS hdt_profiles (
    hdt_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    org_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    context JSON,
    skillset JSON,
    languages JSON,
    preferences JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE KEY unique_hdt_user (user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_name (name),
    INDEX idx_is_active (is_active)
);

-- HDT Agents
CREATE TABLE IF NOT EXISTS hdt_agents (
    agent_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    hdt_id VARCHAR(36) NOT NULL,
    agent_type ENUM('analyst', 'reporter', 'validator', 'optimizer') NOT NULL,
    agent_config JSON,
    capabilities JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (hdt_id) REFERENCES hdt_profiles(hdt_id) ON DELETE CASCADE,
    INDEX idx_hdt_id (hdt_id),
    INDEX idx_agent_type (agent_type),
    INDEX idx_is_active (is_active)
);

-- Query logs
CREATE TABLE IF NOT EXISTS query_logs (
    log_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    hdt_id VARCHAR(36),
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    query_type ENUM('nlp2sql', 'direct_sql', 'template') DEFAULT 'nlp2sql',
    execution_status ENUM('success', 'error', 'blocked', 'timeout') NOT NULL,
    execution_time_ms INT,
    result_rows INT DEFAULT 0,
    error_message TEXT,
    security_flags JSON,
    client_ip VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (hdt_id) REFERENCES hdt_profiles(hdt_id) ON DELETE SET NULL,
    INDEX idx_org_id (org_id),
    INDEX idx_user_id (user_id),
    INDEX idx_execution_status (execution_status),
    INDEX idx_timestamp (timestamp),
    INDEX idx_query_type (query_type)
);

-- Permissions table
CREATE TABLE IF NOT EXISTS permissions (
    permission_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    role ENUM('admin', 'analyst', 'viewer', 'power_user'),
    resource_type ENUM('table', 'column', 'schema', 'function') NOT NULL,
    resource_name VARCHAR(255) NOT NULL,
    permission_type ENUM('select', 'insert', 'update', 'delete', 'create', 'drop', 'all') NOT NULL,
    is_granted BOOLEAN DEFAULT TRUE,
    granted_by VARCHAR(36),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_org_id (org_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role (role),
    INDEX idx_resource (resource_type, resource_name),
    INDEX idx_permission_type (permission_type),
    INDEX idx_expires_at (expires_at)
);

-- Security audit logs
CREATE TABLE IF NOT EXISTS security_logs (
    log_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    event_type ENUM('login_success', 'login_failed', 'query_blocked', 'permission_denied', 'suspicious_activity') NOT NULL,
    event_details JSON,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    client_ip VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_org_id (org_id),
    INDEX idx_user_id (user_id),
    INDEX idx_event_type (event_type),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp)
);

-- API tokens for service-to-service communication
CREATE TABLE IF NOT EXISTS api_tokens (
    token_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36),
    token_name VARCHAR(255) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_org_id (org_id),
    INDEX idx_user_id (user_id),
    INDEX idx_token_hash (token_hash),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
);

-- System settings and configurations
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_id VARCHAR(36),
    setting_key VARCHAR(255) NOT NULL,
    setting_value JSON,
    setting_type ENUM('string', 'number', 'boolean', 'json', 'array') DEFAULT 'string',
    is_global BOOLEAN DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    UNIQUE KEY unique_org_setting (org_id, setting_key),
    INDEX idx_org_id (org_id),
    INDEX idx_setting_key (setting_key),
    INDEX idx_is_global (is_global)
);

-- Insert initial schema info
INSERT IGNORE INTO schema_info (schema_version, database_type, description)
VALUES ('v1.0', 'mysql', 'Initial root schema for Multi-Tenant NLP2SQL MySQL databases');

-- Insert default system settings
INSERT IGNORE INTO system_settings (setting_key, setting_value, setting_type, is_global, description)
VALUES
    ('max_query_timeout_seconds', '300', 'number', TRUE, 'Maximum query execution timeout in seconds'),
    ('max_result_rows', '10000', 'number', TRUE, 'Maximum number of rows to return in query results'),
    ('enable_query_caching', 'true', 'boolean', TRUE, 'Enable query result caching'),
    ('default_export_format', '"json"', 'string', TRUE, 'Default export format for query results'),
    ('security_level', '"medium"', 'string', TRUE, 'Default security level for query validation');