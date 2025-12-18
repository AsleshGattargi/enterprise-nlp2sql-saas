-- ============================================================================
-- Multi-Tenant NLP2SQL Central RBAC Database Schema
-- Separate metadata database for Role-Based Access Control (NOT cloned)
-- ============================================================================

-- Enable UUID generation (for MySQL 8.0)
-- For PostgreSQL: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- System metadata
CREATE TABLE IF NOT EXISTS rbac_schema_info (
    schema_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    schema_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    description TEXT DEFAULT 'Central RBAC database for multi-tenant system'
);

-- Master organizations registry (links to cloned tenant databases)
CREATE TABLE IF NOT EXISTS master_organizations (
    org_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    org_name VARCHAR(255) NOT NULL UNIQUE,
    org_code VARCHAR(50) NOT NULL UNIQUE,
    database_type ENUM('mysql', 'postgresql', 'sqlite', 'mongodb') NOT NULL,
    cloned_database_name VARCHAR(255) NOT NULL,
    clone_connection_params JSON,
    subscription_tier ENUM('basic', 'premium', 'enterprise') DEFAULT 'basic',
    max_users INT DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_org_name (org_name),
    INDEX idx_org_code (org_code),
    INDEX idx_is_active (is_active)
);

-- Role templates (system-wide role definitions)
CREATE TABLE IF NOT EXISTS role_templates (
    role_template_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    role_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    permissions JSON NOT NULL,
    inherits_from JSON NULL,
    is_system_role BOOLEAN DEFAULT TRUE,
    is_assignable BOOLEAN DEFAULT TRUE,
    metadata JSON NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (parent_role_id) REFERENCES role_templates(role_id) ON DELETE SET NULL,
    INDEX idx_role_name (role_name),
    INDEX idx_role_code (role_code),
    INDEX idx_hierarchy_level (hierarchy_level),
    INDEX idx_is_active (is_active)
);

-- Master users table (central user registry)
CREATE TABLE IF NOT EXISTS master_users (
    user_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    is_global_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255) NULL,
    last_login TIMESTAMP NULL,
    password_expires_at TIMESTAMP NULL,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_is_active (is_active),
    INDEX idx_is_global_admin (is_global_admin),
    INDEX idx_last_login (last_login)
);

-- User-tenant mappings (which users can access which tenants)
CREATE TABLE IF NOT EXISTS user_tenant_mappings (
    mapping_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    org_id VARCHAR(36) NOT NULL,
    tenant_database_name VARCHAR(255) NOT NULL,
    is_primary_tenant BOOLEAN DEFAULT FALSE,
    access_granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_granted_by VARCHAR(36) NULL,
    access_expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES master_organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (access_granted_by) REFERENCES master_users(user_id) ON DELETE SET NULL,

    UNIQUE KEY unique_user_org (user_id, org_id),
    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_is_active (is_active),
    INDEX idx_access_expires_at (access_expires_at)
);

-- User role assignments per tenant
CREATE TABLE IF NOT EXISTS user_tenant_roles (
    assignment_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    org_id VARCHAR(36) NOT NULL,
    role_id VARCHAR(36) NOT NULL,
    assigned_by VARCHAR(36) NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES master_organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES role_templates(role_id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES master_users(user_id) ON DELETE SET NULL,

    UNIQUE KEY unique_user_org_role (user_id, org_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_role_id (role_id),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
);

-- Permission matrix (fine-grained permissions per user per tenant)
CREATE TABLE IF NOT EXISTS user_permissions (
    permission_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    org_id VARCHAR(36) NOT NULL,
    resource_type ENUM('database', 'table', 'column', 'query', 'export', 'admin') NOT NULL,
    resource_name VARCHAR(255) NULL,
    permission_type ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'EXECUTE', 'EXPORT', 'MANAGE') NOT NULL,
    is_granted BOOLEAN DEFAULT TRUE,
    granted_by VARCHAR(36) NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    conditions JSON NULL, -- Additional permission conditions
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES master_organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES master_users(user_id) ON DELETE SET NULL,

    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_resource_type (resource_type),
    INDEX idx_permission_type (permission_type),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_org_resource (user_id, org_id, resource_type)
);

-- Tenant access sessions (track user sessions per tenant)
CREATE TABLE IF NOT EXISTS tenant_access_sessions (
    session_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    roles JSON NOT NULL,
    status ENUM('ACTIVE', 'EXPIRED', 'REVOKED', 'INVALID') DEFAULT 'ACTIVE',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP NULL,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,

    INDEX idx_user_id (user_id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_tenant_active (user_id, tenant_id, status)
);

-- Tenant access requests (for approval workflow)
CREATE TABLE IF NOT EXISTS tenant_access_requests (
    request_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NOT NULL,
    tenant_id VARCHAR(36) NOT NULL,
    requested_roles JSON NOT NULL,
    justification TEXT NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED') DEFAULT 'PENDING',
    requested_by VARCHAR(36) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(36) NULL,
    reviewed_at TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL,
    rejection_reason TEXT NULL,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (requested_by) REFERENCES master_users(user_id) ON DELETE RESTRICT,
    FOREIGN KEY (reviewed_by) REFERENCES master_users(user_id) ON DELETE SET NULL,

    INDEX idx_user_id (user_id),
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_status (status),
    INDEX idx_requested_by (requested_by),
    INDEX idx_expires_at (expires_at),
    UNIQUE KEY uk_user_tenant_pending (user_id, tenant_id, status)
);

-- Bulk operations tracking
CREATE TABLE IF NOT EXISTS bulk_operations (
    operation_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    operation_type ENUM('GRANT_ACCESS', 'REVOKE_ACCESS', 'UPDATE_ROLES', 'MIGRATE_USERS') NOT NULL,
    user_ids JSON NOT NULL,
    tenant_ids JSON NOT NULL,
    parameters JSON NOT NULL,
    initiated_by VARCHAR(36) NOT NULL,
    status ENUM('INITIATED', 'RUNNING', 'COMPLETED', 'COMPLETED_WITH_ERRORS', 'FAILED') DEFAULT 'INITIATED',
    progress INT DEFAULT 0,
    total_items INT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    errors JSON NULL,

    FOREIGN KEY (initiated_by) REFERENCES master_users(user_id) ON DELETE RESTRICT,

    INDEX idx_initiated_by (initiated_by),
    INDEX idx_status (status),
    INDEX idx_operation_type (operation_type),
    INDEX idx_started_at (started_at)
);

-- Audit log for RBAC operations
CREATE TABLE IF NOT EXISTS rbac_audit_log (
    log_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id VARCHAR(36) NULL,
    org_id VARCHAR(36) NULL,
    action_type ENUM('USER_LOGIN', 'USER_LOGOUT', 'ROLE_ASSIGNED', 'ROLE_REVOKED', 'PERMISSION_GRANTED', 'PERMISSION_REVOKED', 'TENANT_ACCESS_GRANTED', 'TENANT_ACCESS_REVOKED', 'ADMIN_ACTION') NOT NULL,
    target_user_id VARCHAR(36) NULL,
    target_org_id VARCHAR(36) NULL,
    action_details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (org_id) REFERENCES master_organizations(org_id) ON DELETE SET NULL,
    FOREIGN KEY (target_user_id) REFERENCES master_users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (target_org_id) REFERENCES master_organizations(org_id) ON DELETE SET NULL,

    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_target_user_id (target_user_id)
);

-- API keys for service-to-service authentication
CREATE TABLE IF NOT EXISTS api_keys (
    api_key_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    key_name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(36) NULL,
    org_id VARCHAR(36) NULL,
    permissions JSON,
    allowed_origins JSON,
    rate_limit_per_hour INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(36) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    last_used_at TIMESTAMP NULL,

    FOREIGN KEY (user_id) REFERENCES master_users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (org_id) REFERENCES master_organizations(org_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES master_users(user_id) ON DELETE SET NULL,

    INDEX idx_key_hash (key_hash),
    INDEX idx_user_id (user_id),
    INDEX idx_org_id (org_id),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
);

-- System settings for RBAC
CREATE TABLE IF NOT EXISTS rbac_settings (
    setting_id VARCHAR(36) PRIMARY KEY DEFAULT (UUID()),
    setting_key VARCHAR(255) NOT NULL UNIQUE,
    setting_value JSON,
    setting_type ENUM('string', 'number', 'boolean', 'json', 'array') DEFAULT 'string',
    description TEXT,
    is_global BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_setting_key (setting_key),
    INDEX idx_is_global (is_global)
);

-- ============================================================================
-- INSERT DEFAULT DATA
-- ============================================================================

-- Insert schema info
INSERT IGNORE INTO rbac_schema_info (schema_version, description)
VALUES ('v1.0', 'Central RBAC database for multi-tenant NLP2SQL system');

-- Insert default role templates
INSERT IGNORE INTO role_templates (role_name, role_code, description, permissions, hierarchy_level) VALUES
('Global Admin', 'GLOBAL_ADMIN', 'System-wide administrator with all permissions',
 JSON_OBJECT(
     'database', JSON_ARRAY('CREATE', 'READ', 'UPDATE', 'DELETE'),
     'admin', JSON_ARRAY('MANAGE_USERS', 'MANAGE_ROLES', 'MANAGE_TENANTS', 'SYSTEM_CONFIG'),
     'query', JSON_ARRAY('EXECUTE', 'CREATE', 'MODIFY', 'DELETE'),
     'export', JSON_ARRAY('ALL_FORMATS', 'BULK_EXPORT'),
     'monitoring', JSON_ARRAY('VIEW_LOGS', 'SYSTEM_METRICS')
 ), 0),

('Organization Admin', 'ORG_ADMIN', 'Administrator for specific organization',
 JSON_OBJECT(
     'database', JSON_ARRAY('CREATE', 'READ', 'UPDATE'),
     'admin', JSON_ARRAY('MANAGE_USERS', 'MANAGE_ROLES'),
     'query', JSON_ARRAY('EXECUTE', 'CREATE', 'MODIFY', 'DELETE'),
     'export', JSON_ARRAY('ALL_FORMATS'),
     'monitoring', JSON_ARRAY('VIEW_ORG_LOGS')
 ), 1),

('Data Analyst', 'ANALYST', 'Advanced user with query and analysis capabilities',
 JSON_OBJECT(
     'database', JSON_ARRAY('READ'),
     'query', JSON_ARRAY('EXECUTE', 'CREATE', 'MODIFY'),
     'export', JSON_ARRAY('CSV', 'EXCEL', 'JSON'),
     'analysis', JSON_ARRAY('CREATE_DASHBOARDS', 'ADVANCED_QUERIES')
 ), 2),

('Power User', 'POWER_USER', 'User with extended query capabilities',
 JSON_OBJECT(
     'database', JSON_ARRAY('READ'),
     'query', JSON_ARRAY('EXECUTE', 'CREATE'),
     'export', JSON_ARRAY('CSV', 'EXCEL'),
     'analysis', JSON_ARRAY('BASIC_QUERIES')
 ), 3),

('Viewer', 'VIEWER', 'Read-only access to reports and dashboards',
 JSON_OBJECT(
     'database', JSON_ARRAY('READ'),
     'query', JSON_ARRAY('EXECUTE'),
     'export', JSON_ARRAY('CSV'),
     'analysis', JSON_ARRAY('VIEW_REPORTS')
 ), 4),

('Guest', 'GUEST', 'Limited read-only access',
 JSON_OBJECT(
     'database', JSON_ARRAY('READ'),
     'query', JSON_ARRAY('EXECUTE'),
     'analysis', JSON_ARRAY('VIEW_BASIC_REPORTS')
 ), 5);

-- Insert default RBAC settings
INSERT IGNORE INTO rbac_settings (setting_key, setting_value, setting_type, description) VALUES
('jwt_secret_key', '"your-super-secret-jwt-key-change-in-production"', 'string', 'JWT token signing secret'),
('jwt_algorithm', '"HS256"', 'string', 'JWT signing algorithm'),
('jwt_access_token_expire_minutes', '60', 'number', 'Access token expiration in minutes'),
('jwt_refresh_token_expire_days', '30', 'number', 'Refresh token expiration in days'),
('max_concurrent_sessions', '3', 'number', 'Maximum concurrent sessions per user'),
('password_min_length', '8', 'number', 'Minimum password length'),
('password_require_special_chars', 'true', 'boolean', 'Require special characters in password'),
('two_factor_enabled', 'false', 'boolean', 'Enable two-factor authentication'),
('session_timeout_minutes', '480', 'number', 'Session timeout in minutes'),
('max_failed_login_attempts', '5', 'number', 'Maximum failed login attempts before lockout'),
('account_lockout_duration_minutes', '30', 'number', 'Account lockout duration in minutes'),
('audit_log_retention_days', '365', 'number', 'Audit log retention period in days'),
('api_rate_limit_per_minute', '100', 'number', 'Default API rate limit per minute'),
('cross_tenant_access_enabled', 'true', 'boolean', 'Allow users to access multiple tenants'),
('role_inheritance_enabled', 'true', 'boolean', 'Enable role inheritance from parent roles'),
('auto_assign_default_role', 'true', 'boolean', 'Automatically assign default role to new users'),
('default_role_code', '"VIEWER"', 'string', 'Default role code for new users');

-- Create triggers for updated_at columns
DELIMITER //

CREATE TRIGGER update_master_organizations_updated_at
    BEFORE UPDATE ON master_organizations
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_role_templates_updated_at
    BEFORE UPDATE ON role_templates
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_master_users_updated_at
    BEFORE UPDATE ON master_users
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_user_tenant_mappings_updated_at
    BEFORE UPDATE ON user_tenant_mappings
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_user_tenant_roles_updated_at
    BEFORE UPDATE ON user_tenant_roles
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_user_permissions_updated_at
    BEFORE UPDATE ON user_permissions
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

CREATE TRIGGER update_rbac_settings_updated_at
    BEFORE UPDATE ON rbac_settings
    FOR EACH ROW
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//

DELIMITER ;

-- Create indexes for performance optimization
CREATE INDEX idx_user_tenant_active ON user_tenant_mappings (user_id, is_active);
CREATE INDEX idx_user_role_active ON user_tenant_roles (user_id, org_id, is_active);
CREATE INDEX idx_user_permission_active ON user_permissions (user_id, org_id, is_active);
CREATE INDEX idx_session_user_active ON tenant_access_sessions (user_id, is_active);
CREATE INDEX idx_audit_user_time ON rbac_audit_log (user_id, timestamp);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- View for user tenant access summary
CREATE VIEW user_tenant_access_summary AS
SELECT
    u.user_id,
    u.username,
    u.email,
    o.org_id,
    o.org_name,
    o.org_code,
    utm.is_primary_tenant,
    utm.access_granted_at,
    utm.access_expires_at,
    GROUP_CONCAT(rt.role_name SEPARATOR ', ') as roles,
    utm.is_active as access_active
FROM master_users u
JOIN user_tenant_mappings utm ON u.user_id = utm.user_id
JOIN master_organizations o ON utm.org_id = o.org_id
LEFT JOIN user_tenant_roles utr ON u.user_id = utr.user_id AND o.org_id = utr.org_id AND utr.is_active = TRUE
LEFT JOIN role_templates rt ON utr.role_id = rt.role_id
WHERE u.is_active = TRUE AND utm.is_active = TRUE
GROUP BY u.user_id, o.org_id, utm.is_primary_tenant, utm.access_granted_at, utm.access_expires_at, utm.is_active;

-- View for role permissions matrix
CREATE VIEW role_permissions_matrix AS
SELECT
    rt.role_id,
    rt.role_name,
    rt.role_code,
    rt.hierarchy_level,
    rt.permissions,
    COUNT(utr.user_id) as users_with_role,
    rt.is_active
FROM role_templates rt
LEFT JOIN user_tenant_roles utr ON rt.role_id = utr.role_id AND utr.is_active = TRUE
WHERE rt.is_active = TRUE
GROUP BY rt.role_id, rt.role_name, rt.role_code, rt.hierarchy_level, rt.permissions, rt.is_active;

-- View for active user sessions per tenant
CREATE VIEW active_user_sessions AS
SELECT
    u.user_id,
    u.username,
    o.org_id,
    o.org_name,
    tas.session_id,
    tas.ip_address,
    tas.created_at,
    tas.last_activity,
    tas.expires_at
FROM tenant_access_sessions tas
JOIN master_users u ON tas.user_id = u.user_id
JOIN master_organizations o ON tas.org_id = o.org_id
WHERE tas.is_active = TRUE AND tas.expires_at > NOW();