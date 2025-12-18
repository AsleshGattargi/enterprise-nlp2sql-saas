-- Sample Data for Multi-Tenant NLP2SQL System
USE nlp2sql_metadata;

-- Insert Organizations
INSERT INTO organizations (org_id, org_name, domain, database_type, database_name, industry) VALUES
('org-001', 'TechCorp', '@techcorp.com', 'postgresql', 'techcorp_db', 'Technology'),
('org-002', 'HealthPlus', '@healthplus.org', 'mysql', 'healthplus_db', 'Healthcare'),
('org-003', 'FinanceHub', '@financehub.net', 'postgresql', 'financehub_db', 'Finance'),
('org-004', 'RetailMax', '@retailmax.com', 'mongodb', 'retailmax_db', 'Retail'),
('org-005', 'EduLearn', '@edulearn.edu', 'mysql', 'edulearn_db', 'Education');

-- Insert Human Digital Twins
INSERT INTO human_digital_twins (hdt_id, name, description, context, skillset, languages) VALUES
('hdt-001', 'researcher_analyst', 'Research and analytics expert', 'You are an analyst who works in an analytical way, focusing on data-driven insights and research methodologies', '["coding", "research", "data_analysis", "statistics"]', '["python", "sql", "r"]'),
('hdt-002', 'business_manager', 'Business operations and management', 'You are a business manager focused on operational efficiency and strategic decision making', '["management", "strategy", "operations", "finance"]', '["sql", "excel"]'),
('hdt-003', 'data_scientist', 'Advanced data science and ML', 'You are a data scientist specializing in machine learning and advanced analytics', '["machine_learning", "statistics", "programming", "visualization"]', '["python", "r", "scala", "sql"]'),
('hdt-004', 'financial_analyst', 'Financial analysis and reporting', 'You are a financial analyst focused on financial modeling and reporting', '["finance", "accounting", "modeling", "reporting"]', '["sql", "python", "excel"]'),
('hdt-005', 'basic_user', 'General business user', 'You are a general business user who needs simple data access and reporting', '["basic_analysis", "reporting"]', '["sql"]');

-- Insert Agents
INSERT INTO agents (agent_id, agent_name, agent_type, description, capabilities, config) VALUES
('agent-001', 'NLP2SQL Agent', 'nlp2sql', 'Converts natural language to SQL queries with dialect awareness', '["query_generation", "dialect_conversion", "syntax_validation"]', '{"max_query_complexity": 10, "allowed_operations": ["SELECT", "COUNT", "SUM", "AVG"]}'),
('agent-002', 'RAG Agent', 'rag', 'Retrieval Augmented Generation for contextual query enhancement', '["document_retrieval", "context_enhancement", "knowledge_base"]', '{"max_context_length": 2000, "similarity_threshold": 0.7}'),
('agent-003', 'Analytics Agent', 'analytics', 'Advanced analytics and data insights', '["statistical_analysis", "trend_analysis", "forecasting"]', '{"analysis_types": ["descriptive", "predictive", "diagnostic"]}'),
('agent-004', 'Reporting Agent', 'reporting', 'Automated report generation and visualization', '["report_generation", "data_visualization", "export_formats"]', '{"export_formats": ["csv", "pdf", "excel"], "chart_types": ["bar", "line", "pie"]}'),
('agent-005', 'Chatbot Agent', 'chatbot', 'Conversational interface for data queries', '["natural_conversation", "query_clarification", "help_assistance"]', '{"conversation_memory": 10, "clarification_prompts": true}');

-- Insert HDT-Agent Assignments
INSERT INTO hdt_agents (hdt_id, agent_id) VALUES
('hdt-001', 'agent-001'),  -- researcher_analyst gets NLP2SQL
('hdt-001', 'agent-002'),  -- researcher_analyst gets RAG
('hdt-001', 'agent-003'),  -- researcher_analyst gets Analytics
('hdt-002', 'agent-001'),  -- business_manager gets NLP2SQL
('hdt-002', 'agent-004'),  -- business_manager gets Reporting
('hdt-002', 'agent-005'),  -- business_manager gets Chatbot
('hdt-003', 'agent-001'),  -- data_scientist gets NLP2SQL
('hdt-003', 'agent-002'),  -- data_scientist gets RAG
('hdt-003', 'agent-003'),  -- data_scientist gets Analytics
('hdt-004', 'agent-001'),  -- financial_analyst gets NLP2SQL
('hdt-004', 'agent-004'),  -- financial_analyst gets Reporting
('hdt-005', 'agent-001'),  -- basic_user gets NLP2SQL
('hdt-005', 'agent-005');  -- basic_user gets Chatbot

-- Insert Users for TechCorp (50 users total)
-- 1 Admin, 4 Managers, 10 Analysts, 10 Developers, 25 Viewers
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role) VALUES
-- 1 Admin
('user-001', 'org-001', 'diana.admin', 'diana.rodriguez0@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Diana Rodriguez', 'IT', 'admin'),

-- 4 Managers
('user-002', 'org-001', 'john.manager1', 'john.smith1@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'John Smith', 'Operations', 'manager'),
('user-003', 'org-001', 'sarah.manager2', 'sarah.johnson2@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sarah Johnson', 'Sales', 'manager'),
('user-004', 'org-001', 'mike.manager3', 'mike.wilson3@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mike Wilson', 'Engineering', 'manager'),
('user-005', 'org-001', 'lisa.manager4', 'lisa.brown4@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lisa Brown', 'Marketing', 'manager'),

-- 10 Analysts
('user-006', 'org-001', 'alex.analyst1', 'alex.davis5@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alex Davis', 'Analytics', 'analyst'),
('user-007', 'org-001', 'emma.analyst2', 'emma.miller6@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emma Miller', 'Analytics', 'analyst'),
('user-008', 'org-001', 'david.analyst3', 'david.anderson7@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'David Anderson', 'Analytics', 'analyst'),
('user-009', 'org-001', 'jessica.analyst4', 'jessica.taylor8@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jessica Taylor', 'Business Intelligence', 'analyst'),
('user-010', 'org-001', 'chris.analyst5', 'chris.thomas9@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chris Thomas', 'Data Science', 'analyst'),
('user-011', 'org-001', 'amy.analyst6', 'amy.jackson10@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Amy Jackson', 'Market Research', 'analyst'),
('user-012', 'org-001', 'ryan.analyst7', 'ryan.white11@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ryan White', 'Financial Analysis', 'analyst'),
('user-013', 'org-001', 'megan.analyst8', 'megan.harris12@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Megan Harris', 'Product Analysis', 'analyst'),
('user-014', 'org-001', 'kevin.analyst9', 'kevin.martin13@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Kevin Martin', 'Customer Analytics', 'analyst'),
('user-015', 'org-001', 'laura.analyst10', 'laura.clark14@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Laura Clark', 'Performance Analytics', 'analyst'),

-- 10 Developers
('user-016', 'org-001', 'james.dev1', 'james.lewis15@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'James Lewis', 'Engineering', 'developer'),
('user-017', 'org-001', 'sophia.dev2', 'sophia.walker16@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sophia Walker', 'Engineering', 'developer'),
('user-018', 'org-001', 'daniel.dev3', 'daniel.hall17@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Daniel Hall', 'Backend Development', 'developer'),
('user-019', 'org-001', 'olivia.dev4', 'olivia.allen18@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Olivia Allen', 'Frontend Development', 'developer'),
('user-020', 'org-001', 'jacob.dev5', 'jacob.young19@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jacob Young', 'DevOps', 'developer'),
('user-021', 'org-001', 'chloe.dev6', 'chloe.king20@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Chloe King', 'Mobile Development', 'developer'),
('user-022', 'org-001', 'ethan.dev7', 'ethan.wright21@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ethan Wright', 'Full Stack', 'developer'),
('user-023', 'org-001', 'ava.dev8', 'ava.lopez22@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Ava Lopez', 'Database Development', 'developer'),
('user-024', 'org-001', 'noah.dev9', 'noah.hill23@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Noah Hill', 'API Development', 'developer'),
('user-025', 'org-001', 'isabella.dev10', 'isabella.green24@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Isabella Green', 'Security Development', 'developer'),

-- 25 Viewers
('user-026', 'org-001', 'mason.viewer1', 'mason.adams25@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mason Adams', 'Sales', 'viewer'),
('user-027', 'org-001', 'mia.viewer2', 'mia.baker26@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Mia Baker', 'Support', 'viewer'),
('user-028', 'org-001', 'william.viewer3', 'william.gonzalez27@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'William Gonzalez', 'Customer Service', 'viewer'),
('user-029', 'org-001', 'charlotte.viewer4', 'charlotte.nelson28@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Charlotte Nelson', 'HR', 'viewer'),
('user-030', 'org-001', 'liam.viewer5', 'liam.carter29@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Liam Carter', 'Accounting', 'viewer'),
('user-031', 'org-001', 'amelia.viewer6', 'amelia.mitchell30@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Amelia Mitchell', 'Marketing', 'viewer'),
('user-032', 'org-001', 'benjamin.viewer7', 'benjamin.perez31@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Benjamin Perez', 'Legal', 'viewer'),
('user-033', 'org-001', 'harper.viewer8', 'harper.roberts32@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Harper Roberts', 'Procurement', 'viewer'),
('user-034', 'org-001', 'elijah.viewer9', 'elijah.turner33@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elijah Turner', 'Quality Assurance', 'viewer'),
('user-035', 'org-001', 'evelyn.viewer10', 'evelyn.phillips34@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Evelyn Phillips', 'Facilities', 'viewer'),
('user-036', 'org-001', 'lucas.viewer11', 'lucas.campbell35@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lucas Campbell', 'Training', 'viewer'),
('user-037', 'org-001', 'abigail.viewer12', 'abigail.parker36@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Abigail Parker', 'Communication', 'viewer'),
('user-038', 'org-001', 'alexander.viewer13', 'alexander.evans37@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Alexander Evans', 'Research', 'viewer'),
('user-039', 'org-001', 'emily.viewer14', 'emily.edwards38@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Emily Edwards', 'Admin', 'viewer'),
('user-040', 'org-001', 'michael.viewer15', 'michael.collins39@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Michael Collins', 'Security', 'viewer'),
('user-041', 'org-001', 'elizabeth.viewer16', 'elizabeth.stewart40@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Elizabeth Stewart', 'Maintenance', 'viewer'),
('user-042', 'org-001', 'henry.viewer17', 'henry.sanchez41@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Henry Sanchez', 'Shipping', 'viewer'),
('user-043', 'org-001', 'madison.viewer18', 'madison.morris42@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Madison Morris', 'Reception', 'viewer'),
('user-044', 'org-001', 'sebastian.viewer19', 'sebastian.rogers43@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Sebastian Rogers', 'Inventory', 'viewer'),
('user-045', 'org-001', 'victoria.viewer20', 'victoria.reed44@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Victoria Reed', 'Documentation', 'viewer'),
('user-046', 'org-001', 'owen.viewer21', 'owen.cook45@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Owen Cook', 'Testing', 'viewer'),
('user-047', 'org-001', 'grace.viewer22', 'grace.morgan46@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Grace Morgan', 'Compliance', 'viewer'),
('user-048', 'org-001', 'carter.viewer23', 'carter.bell47@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Carter Bell', 'Logistics', 'viewer'),
('user-049', 'org-001', 'zoey.viewer24', 'zoey.murphy48@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Zoey Murphy', 'Planning', 'viewer'),
('user-050', 'org-001', 'jack.viewer25', 'jack.bailey49@techcorp.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Jack Bailey', 'Operations Support', 'viewer');

-- Insert Users for HealthPlus (10 users)
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role) VALUES
('user-005', 'org-002', 'dr.smith', 'dr.smith@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Dr. Smith', 'Administration', 'admin'),
('user-006', 'org-002', 'nurse.johnson', 'nurse.johnson@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Nurse Johnson', 'Clinical', 'manager'),
('user-007', 'org-002', 'analyst.brown', 'analyst.brown@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Data Analyst Brown', 'Analytics', 'analyst'),
('user-008', 'org-002', 'tech.wilson', 'tech.wilson@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Tech Wilson', 'IT', 'developer'),
('user-009', 'org-002', 'receptionist.davis', 'receptionist.davis@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Receptionist Davis', 'Front Office', 'viewer'),
('user-010', 'org-002', 'lab.tech', 'lab.tech@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Lab Technician', 'Laboratory', 'analyst'),
('user-011', 'org-002', 'billing.clerk', 'billing.clerk@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Billing Clerk', 'Finance', 'viewer'),
('user-012', 'org-002', 'pharmacy.mgr', 'pharmacy.mgr@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Pharmacy Manager', 'Pharmacy', 'manager'),
('user-013', 'org-002', 'quality.assurance', 'quality.assurance@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Quality Assurance', 'QA', 'analyst'),
('user-014', 'org-002', 'security.guard', 'security.guard@healthplus.org', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Security Guard', 'Security', 'viewer');

-- Add more users for other organizations (abbreviated for brevity)
INSERT INTO users (user_id, org_id, username, email, password_hash, full_name, department, role) VALUES
('user-015', 'org-003', 'cfo.finance', 'cfo.finance@financehub.net', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'CFO Finance', 'Executive', 'admin'),
('user-016', 'org-004', 'store.manager', 'store.manager@retailmax.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Store Manager', 'Operations', 'manager'),
('user-017', 'org-005', 'dean.education', 'dean.education@edulearn.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeS.AyfYBDQcXkTc6', 'Dean Education', 'Academic', 'admin');

-- Insert User-HDT Assignments
INSERT INTO user_hdt_assignments (user_id, hdt_id) VALUES
('user-001', 'hdt-002'),  -- admin gets business_manager
('user-002', 'hdt-001'),  -- analyst gets researcher_analyst
('user-003', 'hdt-003'),  -- developer gets data_scientist
('user-004', 'hdt-005'),  -- viewer gets basic_user
('user-005', 'hdt-002'),  -- healthcare admin gets business_manager
('user-006', 'hdt-002'),  -- nurse manager gets business_manager
('user-007', 'hdt-001'),  -- healthcare analyst gets researcher_analyst
('user-008', 'hdt-003'),  -- healthcare tech gets data_scientist
('user-009', 'hdt-005'),  -- receptionist gets basic_user
('user-010', 'hdt-001'),  -- lab tech gets researcher_analyst
('user-011', 'hdt-005'),  -- billing clerk gets basic_user
('user-012', 'hdt-002'),  -- pharmacy manager gets business_manager
('user-013', 'hdt-001'),  -- quality assurance gets researcher_analyst
('user-014', 'hdt-005'),  -- security guard gets basic_user
('user-015', 'hdt-004'),  -- CFO gets financial_analyst
('user-016', 'hdt-002'),  -- store manager gets business_manager
('user-017', 'hdt-002');  -- dean gets business_manager

-- Insert Sample Permissions
INSERT INTO user_permissions (permission_id, user_id, resource_type, resource_name, access_level) VALUES
-- Admin permissions
('perm-001', 'user-001', 'table', 'products', 'admin'),
('perm-002', 'user-001', 'table', 'inventory', 'admin'),
('perm-003', 'user-001', 'table', 'sales', 'admin'),
('perm-004', 'user-001', 'table', 'customers', 'admin'),

-- Analyst permissions
('perm-005', 'user-002', 'table', 'products', 'read'),
('perm-006', 'user-002', 'table', 'inventory', 'read'),
('perm-007', 'user-002', 'table', 'sales', 'read'),
('perm-008', 'user-002', 'table', 'customers', 'read'),

-- Developer permissions
('perm-009', 'user-003', 'table', 'products', 'write'),
('perm-010', 'user-003', 'table', 'inventory', 'write'),

-- Viewer permissions
('perm-011', 'user-004', 'table', 'products', 'read'),
('perm-012', 'user-004', 'table', 'sales', 'read');