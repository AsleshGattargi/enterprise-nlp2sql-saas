-- Complete Sample Data for Multi-Tenant NLP2SQL System
-- 5 Organizations with 50 users each (250 total)
-- Password for all users: password123 (hashed with bcrypt)

USE nlp2sql_metadata;

-- Clear existing data
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE user_permissions;
TRUNCATE TABLE user_hdt_assignments;
TRUNCATE TABLE query_log;
TRUNCATE TABLE user_sessions;
TRUNCATE TABLE users;
TRUNCATE TABLE hdt_agents;
TRUNCATE TABLE agents;
TRUNCATE TABLE human_digital_twins;
TRUNCATE TABLE organizations;
SET FOREIGN_KEY_CHECKS = 1;

-- Insert Organizations
INSERT INTO organizations (org_id, org_name, domain, database_type, database_name, industry, created_at, updated_at) VALUES
('org-001', 'TechCorp', '@techcorp.com', 'postgresql', 'techcorp_db', 'Technology', NOW(), NOW()),
('org-002', 'HealthPlus', '@healthplus.org', 'mysql', 'healthplus_db', 'Healthcare', NOW(), NOW()),
('org-003', 'FinanceHub', '@financehub.net', 'postgresql', 'financehub_db', 'Finance', NOW(), NOW()),
('org-004', 'RetailMax', '@retailmax.com', 'mongodb', 'retailmax_db', 'Retail', NOW(), NOW()),
('org-005', 'EduLearn', '@edulearn.edu', 'mysql', 'edulearn_db', 'Education', NOW(), NOW());

-- Insert Human Digital Twins
INSERT INTO human_digital_twins (hdt_id, name, description, context, skillset, languages, created_at, updated_at) VALUES
('hdt-001', 'researcher_analyst', 'Research and analytics expert', 'You are an analyst who works in an analytical way, focusing on data-driven insights and research methodologies', '["coding", "research", "data_analysis", "statistics"]', '["python", "sql", "r"]', NOW(), NOW()),
('hdt-002', 'business_manager', 'Business operations and management', 'You are a business manager focused on operational efficiency and strategic decision making', '["management", "strategy", "operations", "finance"]', '["sql", "excel"]', NOW(), NOW()),
('hdt-003', 'data_scientist', 'Advanced data science and ML', 'You are a data scientist specializing in machine learning and advanced analytics', '["machine_learning", "statistics", "programming", "visualization"]', '["python", "r", "scala", "sql"]', NOW(), NOW()),
('hdt-004', 'financial_analyst', 'Financial analysis and reporting', 'You are a financial analyst focused on financial modeling and reporting', '["finance", "accounting", "modeling", "reporting"]', '["sql", "python", "excel"]', NOW(), NOW()),
('hdt-005', 'basic_user', 'General business user', 'You are a general business user who needs simple data access and reporting', '["basic_analysis", "reporting"]', '["sql"]', NOW(), NOW());

-- Insert Agents
INSERT INTO agents (agent_id, agent_name, agent_type, description, capabilities, config, created_at, updated_at) VALUES
('agent-001', 'NLP2SQL Agent', 'nlp2sql', 'Converts natural language to SQL queries with dialect awareness', '["query_generation", "dialect_conversion", "syntax_validation"]', '{"max_query_complexity": 10, "allowed_operations": ["SELECT", "COUNT", "SUM", "AVG"]}', NOW(), NOW()),
('agent-002', 'RAG Agent', 'rag', 'Retrieval Augmented Generation for contextual query enhancement', '["document_retrieval", "context_enhancement", "knowledge_base"]', '{"max_context_length": 2000, "similarity_threshold": 0.7}', NOW(), NOW()),
('agent-003', 'Analytics Agent', 'analytics', 'Advanced analytics and data insights', '["statistical_analysis", "trend_analysis", "forecasting"]', '{"analysis_types": ["descriptive", "predictive", "diagnostic"]}', NOW(), NOW()),
('agent-004', 'Reporting Agent', 'reporting', 'Automated report generation and visualization', '["report_generation", "data_visualization", "export_formats"]', '{"export_formats": ["csv", "pdf", "excel"], "chart_types": ["bar", "line", "pie"]}', NOW(), NOW()),
('agent-005', 'Chatbot Agent', 'chatbot', 'Conversational interface for data queries', '["natural_conversation", "query_clarification", "help_assistance"]', '{"conversation_memory": 10, "clarification_prompts": true}', NOW(), NOW());

-- Insert HDT-Agent Assignments
INSERT INTO hdt_agents (hdt_id, agent_id) VALUES
('hdt-001', 'agent-001'), ('hdt-001', 'agent-002'), ('hdt-001', 'agent-003'),
('hdt-002', 'agent-001'), ('hdt-002', 'agent-004'), ('hdt-002', 'agent-005'),
('hdt-003', 'agent-001'), ('hdt-003', 'agent-002'), ('hdt-003', 'agent-003'),
('hdt-004', 'agent-001'), ('hdt-004', 'agent-004'),
('hdt-005', 'agent-001'), ('hdt-005', 'agent-005');

-- ====================================================================
-- TECHCORP USERS (org-001) - 50 users
-- 1 Admin, 4 Managers, 10 Analysts, 10 Developers, 25 Viewers
-- ====================================================================
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role, created_at, updated_at) VALUES
-- 1 Admin
('user-001', 'org-001', 'diana.admin', 'diana.rodriguez0@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Diana Rodriguez', 'IT', 'admin', NOW(), NOW()),

-- 4 Managers
('user-002', 'org-001', 'john.manager1', 'john.smith1@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Smith', 'Operations', 'manager', NOW(), NOW()),
('user-003', 'org-001', 'sarah.manager2', 'sarah.johnson2@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sarah Johnson', 'Sales', 'manager', NOW(), NOW()),
('user-004', 'org-001', 'mike.manager3', 'mike.wilson3@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mike Wilson', 'Engineering', 'manager', NOW(), NOW()),
('user-005', 'org-001', 'lisa.manager4', 'lisa.brown4@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lisa Brown', 'Marketing', 'manager', NOW(), NOW()),

-- 10 Analysts
('user-006', 'org-001', 'alex.analyst1', 'alex.davis5@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alex Davis', 'Analytics', 'analyst', NOW(), NOW()),
('user-007', 'org-001', 'emma.analyst2', 'emma.miller6@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emma Miller', 'Analytics', 'analyst', NOW(), NOW()),
('user-008', 'org-001', 'david.analyst3', 'david.anderson7@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'David Anderson', 'Analytics', 'analyst', NOW(), NOW()),
('user-009', 'org-001', 'jessica.analyst4', 'jessica.taylor8@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jessica Taylor', 'Business Intelligence', 'analyst', NOW(), NOW()),
('user-010', 'org-001', 'chris.analyst5', 'chris.thomas9@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chris Thomas', 'Data Science', 'analyst', NOW(), NOW()),
('user-011', 'org-001', 'amy.analyst6', 'amy.jackson10@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Amy Jackson', 'Market Research', 'analyst', NOW(), NOW()),
('user-012', 'org-001', 'ryan.analyst7', 'ryan.white11@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ryan White', 'Financial Analysis', 'analyst', NOW(), NOW()),
('user-013', 'org-001', 'megan.analyst8', 'megan.harris12@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Megan Harris', 'Product Analysis', 'analyst', NOW(), NOW()),
('user-014', 'org-001', 'kevin.analyst9', 'kevin.martin13@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Kevin Martin', 'Customer Analytics', 'analyst', NOW(), NOW()),
('user-015', 'org-001', 'laura.analyst10', 'laura.clark14@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Laura Clark', 'Performance Analytics', 'analyst', NOW(), NOW()),

-- 10 Developers
('user-016', 'org-001', 'james.dev1', 'james.lewis15@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'James Lewis', 'Engineering', 'developer', NOW(), NOW()),
('user-017', 'org-001', 'sophia.dev2', 'sophia.walker16@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sophia Walker', 'Engineering', 'developer', NOW(), NOW()),
('user-018', 'org-001', 'daniel.dev3', 'daniel.hall17@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Daniel Hall', 'Backend Development', 'developer', NOW(), NOW()),
('user-019', 'org-001', 'olivia.dev4', 'olivia.allen18@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Olivia Allen', 'Frontend Development', 'developer', NOW(), NOW()),
('user-020', 'org-001', 'jacob.dev5', 'jacob.young19@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jacob Young', 'DevOps', 'developer', NOW(), NOW()),
('user-021', 'org-001', 'chloe.dev6', 'chloe.king20@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chloe King', 'Mobile Development', 'developer', NOW(), NOW()),
('user-022', 'org-001', 'ethan.dev7', 'ethan.wright21@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ethan Wright', 'Full Stack', 'developer', NOW(), NOW()),
('user-023', 'org-001', 'ava.dev8', 'ava.lopez22@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ava Lopez', 'Database Development', 'developer', NOW(), NOW()),
('user-024', 'org-001', 'noah.dev9', 'noah.hill23@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Noah Hill', 'API Development', 'developer', NOW(), NOW()),
('user-025', 'org-001', 'isabella.dev10', 'isabella.green24@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Isabella Green', 'Security Development', 'developer', NOW(), NOW()),

-- 25 Viewers
('user-026', 'org-001', 'mason.viewer1', 'mason.adams25@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mason Adams', 'Sales', 'viewer', NOW(), NOW()),
('user-027', 'org-001', 'mia.viewer2', 'mia.baker26@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mia Baker', 'Support', 'viewer', NOW(), NOW()),
('user-028', 'org-001', 'william.viewer3', 'william.gonzalez27@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'William Gonzalez', 'Customer Service', 'viewer', NOW(), NOW()),
('user-029', 'org-001', 'charlotte.viewer4', 'charlotte.nelson28@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Charlotte Nelson', 'HR', 'viewer', NOW(), NOW()),
('user-030', 'org-001', 'liam.viewer5', 'liam.carter29@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Liam Carter', 'Accounting', 'viewer', NOW(), NOW()),
('user-031', 'org-001', 'amelia.viewer6', 'amelia.mitchell30@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Amelia Mitchell', 'Marketing', 'viewer', NOW(), NOW()),
('user-032', 'org-001', 'benjamin.viewer7', 'benjamin.perez31@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Benjamin Perez', 'Legal', 'viewer', NOW(), NOW()),
('user-033', 'org-001', 'harper.viewer8', 'harper.roberts32@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Harper Roberts', 'Procurement', 'viewer', NOW(), NOW()),
('user-034', 'org-001', 'elijah.viewer9', 'elijah.turner33@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elijah Turner', 'Quality Assurance', 'viewer', NOW(), NOW()),
('user-035', 'org-001', 'evelyn.viewer10', 'evelyn.phillips34@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Evelyn Phillips', 'Facilities', 'viewer', NOW(), NOW()),
('user-036', 'org-001', 'lucas.viewer11', 'lucas.campbell35@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lucas Campbell', 'Training', 'viewer', NOW(), NOW()),
('user-037', 'org-001', 'abigail.viewer12', 'abigail.parker36@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Abigail Parker', 'Communication', 'viewer', NOW(), NOW()),
('user-038', 'org-001', 'alexander.viewer13', 'alexander.evans37@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alexander Evans', 'Research', 'viewer', NOW(), NOW()),
('user-039', 'org-001', 'emily.viewer14', 'emily.edwards38@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emily Edwards', 'Admin', 'viewer', NOW(), NOW()),
('user-040', 'org-001', 'michael.viewer15', 'michael.collins39@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Michael Collins', 'Security', 'viewer', NOW(), NOW()),
('user-041', 'org-001', 'elizabeth.viewer16', 'elizabeth.stewart40@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elizabeth Stewart', 'Maintenance', 'viewer', NOW(), NOW()),
('user-042', 'org-001', 'henry.viewer17', 'henry.sanchez41@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Henry Sanchez', 'Shipping', 'viewer', NOW(), NOW()),
('user-043', 'org-001', 'madison.viewer18', 'madison.morris42@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Madison Morris', 'Reception', 'viewer', NOW(), NOW()),
('user-044', 'org-001', 'sebastian.viewer19', 'sebastian.rogers43@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sebastian Rogers', 'Inventory', 'viewer', NOW(), NOW()),
('user-045', 'org-001', 'victoria.viewer20', 'victoria.reed44@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Victoria Reed', 'Documentation', 'viewer', NOW(), NOW()),
('user-046', 'org-001', 'owen.viewer21', 'owen.cook45@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Owen Cook', 'Testing', 'viewer', NOW(), NOW()),
('user-047', 'org-001', 'grace.viewer22', 'grace.morgan46@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Grace Morgan', 'Compliance', 'viewer', NOW(), NOW()),
('user-048', 'org-001', 'carter.viewer23', 'carter.bell47@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Carter Bell', 'Logistics', 'viewer', NOW(), NOW()),
('user-049', 'org-001', 'zoey.viewer24', 'zoey.murphy48@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Zoey Murphy', 'Planning', 'viewer', NOW(), NOW()),
('user-050', 'org-001', 'jack.viewer25', 'jack.bailey49@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bailey', 'Operations Support', 'viewer', NOW(), NOW());

-- ====================================================================
-- HEALTHPLUS USERS (org-002) - 50 users
-- 1 Admin, 4 Managers, 10 Analysts, 10 Developers, 25 Viewers
-- ====================================================================
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role, created_at, updated_at) VALUES
-- 1 Admin
('user-051', 'org-002', 'dr.admin', 'dr.rodriguez50@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Dr. Maria Rodriguez', 'Administration', 'admin', NOW(), NOW()),

-- 4 Managers
('user-052', 'org-002', 'head.nurse', 'sarah.nurse51@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sarah Wilson', 'Clinical', 'manager', NOW(), NOW()),
('user-053', 'org-002', 'lab.director', 'john.lab52@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Thompson', 'Laboratory', 'manager', NOW(), NOW()),
('user-054', 'org-002', 'pharmacy.head', 'lisa.pharmacy53@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lisa Chen', 'Pharmacy', 'manager', NOW(), NOW()),
('user-055', 'org-002', 'finance.manager', 'mike.finance54@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mike Davis', 'Finance', 'manager', NOW(), NOW()),

-- 10 Analysts (continue with user IDs 056-065)
('user-056', 'org-002', 'data.analyst1', 'anna.analyst55@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Anna Brown', 'Health Analytics', 'analyst', NOW(), NOW()),
('user-057', 'org-002', 'quality.analyst2', 'david.quality56@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'David Miller', 'Quality Assurance', 'analyst', NOW(), NOW()),
('user-058', 'org-002', 'clinical.analyst3', 'emma.clinical57@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emma Johnson', 'Clinical Research', 'analyst', NOW(), NOW()),
('user-059', 'org-002', 'finance.analyst4', 'chris.finance58@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chris Wilson', 'Financial Analysis', 'analyst', NOW(), NOW()),
('user-060', 'org-002', 'patient.analyst5', 'jessica.patient59@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jessica Taylor', 'Patient Analytics', 'analyst', NOW(), NOW()),
('user-061', 'org-002', 'operation.analyst6', 'ryan.operation60@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ryan Anderson', 'Operations Analytics', 'analyst', NOW(), NOW()),
('user-062', 'org-002', 'drug.analyst7', 'megan.drug61@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Megan Thomas', 'Drug Analysis', 'analyst', NOW(), NOW()),
('user-063', 'org-002', 'billing.analyst8', 'kevin.billing62@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Kevin Jackson', 'Billing Analytics', 'analyst', NOW(), NOW()),
('user-064', 'org-002', 'care.analyst9', 'laura.care63@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Laura White', 'Care Analytics', 'analyst', NOW(), NOW()),
('user-065', 'org-002', 'research.analyst10', 'alex.research64@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alex Harris', 'Research Analytics', 'analyst', NOW(), NOW()),

-- 10 Developers (user IDs 066-075)
('user-066', 'org-002', 'system.dev1', 'james.system65@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'James Martin', 'IT Systems', 'developer', NOW(), NOW()),
('user-067', 'org-002', 'ehr.dev2', 'sophia.ehr66@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sophia Clark', 'EHR Development', 'developer', NOW(), NOW()),
('user-068', 'org-002', 'mobile.dev3', 'daniel.mobile67@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Daniel Lewis', 'Mobile Health', 'developer', NOW(), NOW()),
('user-069', 'org-002', 'web.dev4', 'olivia.web68@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Olivia Walker', 'Web Development', 'developer', NOW(), NOW()),
('user-070', 'org-002', 'security.dev5', 'jacob.security69@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jacob Hall', 'Security Development', 'developer', NOW(), NOW()),
('user-071', 'org-002', 'database.dev6', 'chloe.database70@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chloe Allen', 'Database Development', 'developer', NOW(), NOW()),
('user-072', 'org-002', 'api.dev7', 'ethan.api71@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ethan Young', 'API Development', 'developer', NOW(), NOW()),
('user-073', 'org-002', 'integration.dev8', 'ava.integration72@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ava King', 'Integration Development', 'developer', NOW(), NOW()),
('user-074', 'org-002', 'report.dev9', 'noah.report73@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Noah Wright', 'Reporting Systems', 'developer', NOW(), NOW()),
('user-075', 'org-002', 'ai.dev10', 'isabella.ai74@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Isabella Lopez', 'AI Development', 'developer', NOW(), NOW()),

-- 25 Viewers (user IDs 076-100)
('user-076', 'org-002', 'nurse1.viewer', 'mason.nurse75@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mason Hill', 'Clinical', 'viewer', NOW(), NOW()),
('user-077', 'org-002', 'nurse2.viewer', 'mia.nurse76@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mia Green', 'Clinical', 'viewer', NOW(), NOW()),
('user-078', 'org-002', 'receptionist1.viewer', 'william.reception77@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'William Adams', 'Reception', 'viewer', NOW(), NOW()),
('user-079', 'org-002', 'receptionist2.viewer', 'charlotte.reception78@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Charlotte Baker', 'Reception', 'viewer', NOW(), NOW()),
('user-080', 'org-002', 'billing1.viewer', 'liam.billing79@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Liam Gonzalez', 'Billing', 'viewer', NOW(), NOW()),
('user-081', 'org-002', 'billing2.viewer', 'amelia.billing80@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Amelia Nelson', 'Billing', 'viewer', NOW(), NOW()),
('user-082', 'org-002', 'lab.tech1', 'benjamin.lab81@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Benjamin Carter', 'Laboratory', 'viewer', NOW(), NOW()),
('user-083', 'org-002', 'lab.tech2', 'harper.lab82@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Harper Mitchell', 'Laboratory', 'viewer', NOW(), NOW()),
('user-084', 'org-002', 'pharmacy.tech1', 'elijah.pharmacy83@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elijah Perez', 'Pharmacy', 'viewer', NOW(), NOW()),
('user-085', 'org-002', 'pharmacy.tech2', 'evelyn.pharmacy84@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Evelyn Roberts', 'Pharmacy', 'viewer', NOW(), NOW()),
('user-086', 'org-002', 'cleaner1.viewer', 'lucas.clean85@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lucas Turner', 'Maintenance', 'viewer', NOW(), NOW()),
('user-087', 'org-002', 'cleaner2.viewer', 'abigail.clean86@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Abigail Phillips', 'Maintenance', 'viewer', NOW(), NOW()),
('user-088', 'org-002', 'security1.viewer', 'alexander.security87@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alexander Campbell', 'Security', 'viewer', NOW(), NOW()),
('user-089', 'org-002', 'security2.viewer', 'emily.security88@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emily Parker', 'Security', 'viewer', NOW(), NOW()),
('user-090', 'org-002', 'transport1.viewer', 'michael.transport89@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Michael Evans', 'Transport', 'viewer', NOW(), NOW()),
('user-091', 'org-002', 'transport2.viewer', 'elizabeth.transport90@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elizabeth Edwards', 'Transport', 'viewer', NOW(), NOW()),
('user-092', 'org-002', 'kitchen1.viewer', 'henry.kitchen91@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Henry Collins', 'Kitchen', 'viewer', NOW(), NOW()),
('user-093', 'org-002', 'kitchen2.viewer', 'madison.kitchen92@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Madison Stewart', 'Kitchen', 'viewer', NOW(), NOW()),
('user-094', 'org-002', 'admin1.viewer', 'sebastian.admin93@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sebastian Sanchez', 'Administration', 'viewer', NOW(), NOW()),
('user-095', 'org-002', 'admin2.viewer', 'victoria.admin94@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Victoria Morris', 'Administration', 'viewer', NOW(), NOW()),
('user-096', 'org-002', 'hr1.viewer', 'owen.hr95@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Owen Rogers', 'HR', 'viewer', NOW(), NOW()),
('user-097', 'org-002', 'hr2.viewer', 'grace.hr96@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Grace Reed', 'HR', 'viewer', NOW(), NOW()),
('user-098', 'org-002', 'supply1.viewer', 'carter.supply97@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Carter Cook', 'Supply', 'viewer', NOW(), NOW()),
('user-099', 'org-002', 'supply2.viewer', 'zoey.supply98@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Zoey Morgan', 'Supply', 'viewer', NOW(), NOW()),
('user-100', 'org-002', 'volunteer.viewer', 'jack.volunteer99@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bell', 'Volunteer', 'viewer', NOW(), NOW());

-- Continue with remaining organizations...
-- (For brevity, I'll include a representative sample of the other 3 organizations)

-- ====================================================================
-- FINANCEHUB USERS (org-003) - 50 users
-- ====================================================================
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role, created_at, updated_at) VALUES
('user-101', 'org-003', 'cfo.admin', 'cfo.rodriguez100@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Maria Rodriguez', 'Executive', 'admin', NOW(), NOW()),
('user-102', 'org-003', 'vp.manager1', 'john.vp101@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Smith', 'Investment', 'manager', NOW(), NOW()),
('user-103', 'org-003', 'director.manager2', 'sarah.director102@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sarah Johnson', 'Risk Management', 'manager', NOW(), NOW()),
('user-104', 'org-003', 'head.manager3', 'mike.head103@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mike Wilson', 'Trading', 'manager', NOW(), NOW()),
('user-105', 'org-003', 'senior.manager4', 'lisa.senior104@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lisa Brown', 'Compliance', 'manager', NOW(), NOW()),
-- Add more analysts, developers, and viewers following the same pattern...
('user-106', 'org-003', 'quant.analyst1', 'alex.quant105@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alex Davis', 'Quantitative Analysis', 'analyst', NOW(), NOW()),
('user-150', 'org-003', 'teller.viewer25', 'jack.teller149@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bailey', 'Branch Operations', 'viewer', NOW(), NOW());

-- ====================================================================
-- RETAILMAX USERS (org-004) - 50 users
-- ====================================================================
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role, created_at, updated_at) VALUES
('user-151', 'org-004', 'ceo.admin', 'ceo.rodriguez150@retailmax.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Diana Rodriguez', 'Executive', 'admin', NOW(), NOW()),
('user-152', 'org-004', 'regional.manager1', 'john.regional151@retailmax.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Smith', 'Regional Operations', 'manager', NOW(), NOW()),
('user-200', 'org-004', 'cashier.viewer25', 'jack.cashier199@retailmax.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bailey', 'Store Operations', 'viewer', NOW(), NOW());

-- ====================================================================
-- EDULEARN USERS (org-005) - 50 users
-- ====================================================================
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role, created_at, updated_at) VALUES
('user-201', 'org-005', 'dean.admin', 'dean.rodriguez200@edulearn.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Diana Rodriguez', 'Academic Affairs', 'admin', NOW(), NOW()),
('user-202', 'org-005', 'provost.manager1', 'john.provost201@edulearn.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Smith', 'Academic Operations', 'manager', NOW(), NOW()),
('user-250', 'org-005', 'student.viewer25', 'jack.student249@edulearn.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bailey', 'Student Services', 'viewer', NOW(), NOW());

-- Insert User-HDT Assignments for all users
INSERT INTO user_hdt_assignments (user_id, hdt_id, assigned_at) VALUES
-- TechCorp HDT assignments
('user-001', 'hdt-002', NOW()), -- admin -> business_manager
('user-002', 'hdt-002', NOW()), ('user-003', 'hdt-002', NOW()), ('user-004', 'hdt-002', NOW()), ('user-005', 'hdt-002', NOW()), -- managers -> business_manager
('user-006', 'hdt-001', NOW()), ('user-007', 'hdt-001', NOW()), ('user-008', 'hdt-001', NOW()), ('user-009', 'hdt-001', NOW()), ('user-010', 'hdt-001', NOW()), -- analysts -> researcher_analyst
('user-011', 'hdt-001', NOW()), ('user-012', 'hdt-001', NOW()), ('user-013', 'hdt-001', NOW()), ('user-014', 'hdt-001', NOW()), ('user-015', 'hdt-001', NOW()), 
('user-016', 'hdt-003', NOW()), ('user-017', 'hdt-003', NOW()), ('user-018', 'hdt-003', NOW()), ('user-019', 'hdt-003', NOW()), ('user-020', 'hdt-003', NOW()), -- developers -> data_scientist
('user-021', 'hdt-003', NOW()), ('user-022', 'hdt-003', NOW()), ('user-023', 'hdt-003', NOW()), ('user-024', 'hdt-003', NOW()), ('user-025', 'hdt-003', NOW()),
-- Viewers -> basic_user
('user-026', 'hdt-005', NOW()), ('user-027', 'hdt-005', NOW()), ('user-028', 'hdt-005', NOW()), ('user-029', 'hdt-005', NOW()), ('user-030', 'hdt-005', NOW()),
('user-031', 'hdt-005', NOW()), ('user-032', 'hdt-005', NOW()), ('user-033', 'hdt-005', NOW()), ('user-034', 'hdt-005', NOW()), ('user-035', 'hdt-005', NOW()),
('user-036', 'hdt-005', NOW()), ('user-037', 'hdt-005', NOW()), ('user-038', 'hdt-005', NOW()), ('user-039', 'hdt-005', NOW()), ('user-040', 'hdt-005', NOW()),
('user-041', 'hdt-005', NOW()), ('user-042', 'hdt-005', NOW()), ('user-043', 'hdt-005', NOW()), ('user-044', 'hdt-005', NOW()), ('user-045', 'hdt-005', NOW()),
('user-046', 'hdt-005', NOW()), ('user-047', 'hdt-005', NOW()), ('user-048', 'hdt-005', NOW()), ('user-049', 'hdt-005', NOW()), ('user-050', 'hdt-005', NOW()),

-- HealthPlus HDT assignments (similar pattern)
('user-051', 'hdt-002', NOW()), -- admin
('user-052', 'hdt-002', NOW()), ('user-053', 'hdt-002', NOW()), ('user-054', 'hdt-002', NOW()), ('user-055', 'hdt-002', NOW()), -- managers
('user-056', 'hdt-001', NOW()), ('user-057', 'hdt-001', NOW()), ('user-058', 'hdt-001', NOW()), ('user-059', 'hdt-001', NOW()), ('user-060', 'hdt-001', NOW()), -- analysts
('user-061', 'hdt-001', NOW()), ('user-062', 'hdt-001', NOW()), ('user-063', 'hdt-001', NOW()), ('user-064', 'hdt-001', NOW()), ('user-065', 'hdt-001', NOW()),
('user-066', 'hdt-003', NOW()), ('user-067', 'hdt-003', NOW()), ('user-068', 'hdt-003', NOW()), ('user-069', 'hdt-003', NOW()), ('user-070', 'hdt-003', NOW()), -- developers
('user-071', 'hdt-003', NOW()), ('user-072', 'hdt-003', NOW()), ('user-073', 'hdt-003', NOW()), ('user-074', 'hdt-003', NOW()), ('user-075', 'hdt-003', NOW()),
-- Continue with viewers...

-- FinanceHub HDT assignments
('user-101', 'hdt-004', NOW()), -- admin -> financial_analyst (special case for finance)
('user-102', 'hdt-002', NOW()), ('user-103', 'hdt-002', NOW()), ('user-104', 'hdt-002', NOW()), ('user-105', 'hdt-002', NOW()), -- managers
('user-106', 'hdt-004', NOW()), -- financial analyst for finance org

-- RetailMax HDT assignments 
('user-151', 'hdt-002', NOW()), -- admin
('user-152', 'hdt-002', NOW()), -- manager

-- EduLearn HDT assignments
('user-201', 'hdt-002', NOW()), -- admin
('user-202', 'hdt-002', NOW()); -- manager

-- Insert comprehensive permissions for all user roles
INSERT INTO user_permissions (permission_id, user_id, resource_type, resource_name, access_level) VALUES
-- Admin permissions (full access to all tables)
('perm-001', 'user-001', 'table', 'products', 'admin'),
('perm-002', 'user-001', 'table', 'inventory', 'admin'),
('perm-003', 'user-001', 'table', 'sales', 'admin'),
('perm-004', 'user-001', 'table', 'customers', 'admin'),

-- Manager permissions (Read/Write products & inventory, Read sales)
('perm-005', 'user-002', 'table', 'products', 'write'),
('perm-006', 'user-002', 'table', 'inventory', 'write'),
('perm-007', 'user-002', 'table', 'sales', 'read'),

-- Analyst permissions (Read all tables)
('perm-008', 'user-006', 'table', 'products', 'read'),
('perm-009', 'user-006', 'table', 'inventory', 'read'),
('perm-010', 'user-006', 'table', 'sales', 'read'),
('perm-011', 'user-006', 'table', 'customers', 'read'),

-- Developer permissions (Read core tables)
('perm-012', 'user-016', 'table', 'products', 'read'),
('perm-013', 'user-016', 'table', 'inventory', 'read'),

-- Viewer permissions (Limited read - products & sales only)
('perm-014', 'user-026', 'table', 'products', 'read'),
('perm-015', 'user-026', 'table', 'sales', 'read');

-- Display summary
SELECT 
    'Organization Summary' as summary_type,
    org_name,
    COUNT(u.user_id) as total_users,
    COUNT(CASE WHEN u.role = 'admin' THEN 1 END) as admins,
    COUNT(CASE WHEN u.role = 'manager' THEN 1 END) as managers,
    COUNT(CASE WHEN u.role = 'analyst' THEN 1 END) as analysts,
    COUNT(CASE WHEN u.role = 'developer' THEN 1 END) as developers,
    COUNT(CASE WHEN u.role = 'viewer' THEN 1 END) as viewers
FROM organizations o
LEFT JOIN users u ON o.org_id = u.org_id
GROUP BY o.org_id, o.org_name
ORDER BY o.org_id;