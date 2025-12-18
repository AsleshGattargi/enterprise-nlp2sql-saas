-- MySQL Metadata Database Schema
CREATE DATABASE IF NOT EXISTS nlp2sql_metadata;
USE nlp2sql_metadata;

-- Table 1: Organizations/Tenants
CREATE TABLE IF NOT EXISTS organizations (
    org_id VARCHAR(36) PRIMARY KEY,
    org_name VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NOT NULL UNIQUE,
    database_type ENUM('mysql', 'postgresql', 'mongodb', 'sqlite') NOT NULL,
    database_name VARCHAR(100) NOT NULL,
    industry VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 2: Users
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    department VARCHAR(50),
    role ENUM('admin', 'manager', 'analyst', 'developer', 'viewer') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id) ON DELETE CASCADE,
    INDEX idx_org_email (org_id, email),
    INDEX idx_email (email)
);

-- Table 3: Human Digital Twins (HDT)
CREATE TABLE IF NOT EXISTS human_digital_twins (
    hdt_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    context TEXT,
    skillset JSON,
    languages JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 4: Agents
CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(36) PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    agent_type ENUM('nlp2sql', 'rag', 'analytics', 'reporting', 'chatbot') NOT NULL,
    description TEXT,
    capabilities JSON,
    config JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table 5: HDT-Agent Assignments
CREATE TABLE IF NOT EXISTS hdt_agents (
    hdt_id VARCHAR(36),
    agent_id VARCHAR(36),
    PRIMARY KEY (hdt_id, agent_id),
    FOREIGN KEY (hdt_id) REFERENCES human_digital_twins(hdt_id) ON DELETE CASCADE,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id) ON DELETE CASCADE
);

-- Table 6: User-HDT Assignments (Many users can have same HDT)
CREATE TABLE IF NOT EXISTS user_hdt_assignments (
    user_id VARCHAR(36),
    hdt_id VARCHAR(36),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (hdt_id) REFERENCES human_digital_twins(hdt_id) ON DELETE CASCADE
);

-- Table 7: User Permissions
CREATE TABLE IF NOT EXISTS user_permissions (
    permission_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_name VARCHAR(100) NOT NULL,
    access_level ENUM('read', 'write', 'admin') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_resource (user_id, resource_type, resource_name)
);

-- Table 8: Query Log
CREATE TABLE IF NOT EXISTS query_log (
    log_id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    query_text TEXT NOT NULL,
    generated_sql TEXT,
    query_type VARCHAR(50),
    execution_status ENUM('success', 'error', 'blocked') NOT NULL,
    execution_time_ms INT,
    error_message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organizations(org_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_org_timestamp (org_id, timestamp),
    INDEX idx_user_timestamp (user_id, timestamp)
);

-- Table 9: Session Management
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_session (user_id, expires_at)
);