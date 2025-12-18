-- Organization-specific database schemas for different database types

-- =============================================================================
-- TechCorp (PostgreSQL)
-- =============================================================================
CREATE DATABASE techcorp_db;
\c techcorp_db;

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-001',
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10,2),
    sku VARCHAR(100) UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-001',
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    warehouse VARCHAR(100),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sales (
    sale_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-001',
    product_id INTEGER REFERENCES products(product_id),
    customer_name VARCHAR(255),
    amount DECIMAL(10,2),
    quantity INTEGER,
    sale_date DATE DEFAULT CURRENT_DATE
);

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-001',
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sample data for TechCorp
INSERT INTO products (name, category, price, sku, description) VALUES
('Laptop Pro X1', 'Electronics', 1299.99, 'TECH-LP-001', 'High-performance laptop for professionals'),
('Wireless Mouse', 'Accessories', 29.99, 'TECH-MS-002', 'Ergonomic wireless mouse'),
('USB-C Hub', 'Accessories', 79.99, 'TECH-HB-003', 'Multi-port USB-C hub'),
('Monitor 27"', 'Electronics', 349.99, 'TECH-MN-004', '27-inch 4K monitor'),
('Keyboard Mechanical', 'Accessories', 129.99, 'TECH-KB-005', 'RGB mechanical keyboard');

INSERT INTO customers (name, email, phone, address) VALUES
('John Smith', 'john@example.com', '555-0101', '123 Main St, Tech City'),
('Jane Doe', 'jane@example.com', '555-0102', '456 Oak Ave, Tech City'),
('Bob Johnson', 'bob@example.com', '555-0103', '789 Pine Rd, Tech City');

INSERT INTO inventory (product_id, quantity, warehouse) VALUES
(1, 50, 'Warehouse A'),
(2, 200, 'Warehouse B'),
(3, 100, 'Warehouse A'),
(4, 75, 'Warehouse C'),
(5, 120, 'Warehouse B');

INSERT INTO sales (product_id, customer_name, amount, quantity, sale_date) VALUES
(1, 'John Smith', 1299.99, 1, '2024-01-15'),
(2, 'Jane Doe', 59.98, 2, '2024-01-16'),
(3, 'Bob Johnson', 79.99, 1, '2024-01-17'),
(4, 'John Smith', 349.99, 1, '2024-01-18'),
(5, 'Jane Doe', 129.99, 1, '2024-01-19');

-- =============================================================================
-- HealthPlus (MySQL)
-- =============================================================================
CREATE DATABASE IF NOT EXISTS healthplus_db;
USE healthplus_db;

CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    name VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    gender ENUM('M', 'F', 'Other'),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    emergency_contact VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE treatments (
    treatment_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    patient_id INT,
    treatment_name VARCHAR(255) NOT NULL,
    description TEXT,
    cost DECIMAL(10,2),
    treatment_date DATE,
    doctor_name VARCHAR(255),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    patient_id INT,
    doctor_name VARCHAR(255),
    appointment_date DATETIME,
    reason VARCHAR(500),
    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-002',
    patient_id INT,
    treatment_id INT,
    amount DECIMAL(10,2),
    paid_amount DECIMAL(10,2) DEFAULT 0,
    status ENUM('pending', 'paid', 'overdue') DEFAULT 'pending',
    bill_date DATE,
    due_date DATE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
);

-- Sample data for HealthPlus
INSERT INTO patients (name, date_of_birth, gender, phone, email, address, emergency_contact) VALUES
('Alice Johnson', '1985-03-15', 'F', '555-1001', 'alice@email.com', '123 Health St', 'Bob Johnson 555-1002'),
('Charlie Brown', '1990-07-22', 'M', '555-1003', 'charlie@email.com', '456 Care Ave', 'Diana Brown 555-1004'),
('Eva Davis', '1978-11-08', 'F', '555-1005', 'eva@email.com', '789 Wellness Rd', 'Frank Davis 555-1006');

INSERT INTO treatments (patient_id, treatment_name, description, cost, treatment_date, doctor_name) VALUES
(1, 'Annual Checkup', 'Routine annual physical examination', 150.00, '2024-01-10', 'Dr. Smith'),
(2, 'Blood Test', 'Complete blood count and chemistry panel', 85.00, '2024-01-12', 'Dr. Johnson'),
(3, 'X-Ray', 'Chest X-ray examination', 120.00, '2024-01-15', 'Dr. Wilson');

INSERT INTO appointments (patient_id, doctor_name, appointment_date, reason, status) VALUES
(1, 'Dr. Smith', '2024-02-15 09:00:00', 'Follow-up consultation', 'scheduled'),
(2, 'Dr. Johnson', '2024-02-16 14:30:00', 'Lab result review', 'scheduled'),
(3, 'Dr. Wilson', '2024-02-17 10:15:00', 'Specialist referral', 'scheduled');

INSERT INTO billing (patient_id, treatment_id, amount, paid_amount, status, bill_date, due_date) VALUES
(1, 1, 150.00, 150.00, 'paid', '2024-01-10', '2024-02-10'),
(2, 2, 85.00, 0.00, 'pending', '2024-01-12', '2024-02-12'),
(3, 3, 120.00, 60.00, 'pending', '2024-01-15', '2024-02-15');

-- =============================================================================
-- FinanceHub (PostgreSQL)
-- =============================================================================
CREATE DATABASE financehub_db;
\c financehub_db;

CREATE TABLE accounts (
    account_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_number VARCHAR(50) UNIQUE NOT NULL,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50),
    balance DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INTEGER REFERENCES accounts(account_id),
    transaction_type VARCHAR(50),
    amount DECIMAL(15,2),
    description TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE investments (
    investment_id SERIAL PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-003',
    account_id INTEGER REFERENCES accounts(account_id),
    investment_name VARCHAR(255),
    investment_type VARCHAR(100),
    amount DECIMAL(15,2),
    current_value DECIMAL(15,2),
    purchase_date DATE
);

-- Sample data for FinanceHub
INSERT INTO accounts (account_number, account_name, account_type, balance) VALUES
('ACC-001-2024', 'Corporate Checking', 'Checking', 150000.00),
('ACC-002-2024', 'Investment Portfolio', 'Investment', 500000.00),
('ACC-003-2024', 'Emergency Fund', 'Savings', 100000.00);

INSERT INTO transactions (account_id, transaction_type, amount, description, transaction_date) VALUES
(1, 'Credit', 25000.00, 'Client payment received', '2024-01-15 10:30:00'),
(1, 'Debit', 8500.00, 'Office rent payment', '2024-01-16 14:00:00'),
(2, 'Credit', 15000.00, 'Investment dividend', '2024-01-17 09:15:00');

INSERT INTO investments (account_id, investment_name, investment_type, amount, current_value, purchase_date) VALUES
(2, 'Tech Stock Portfolio', 'Stocks', 200000.00, 225000.00, '2024-01-01'),
(2, 'Bond Fund', 'Bonds', 150000.00, 152000.00, '2024-01-01'),
(2, 'Real Estate Fund', 'Real Estate', 150000.00, 148000.00, '2024-01-01');

-- =============================================================================
-- EduLearn (MySQL)
-- =============================================================================
CREATE DATABASE IF NOT EXISTS edulearn_db;
USE edulearn_db;

CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    student_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    date_of_birth DATE,
    enrollment_date DATE,
    major VARCHAR(100),
    gpa DECIMAL(3,2),
    status ENUM('active', 'graduated', 'withdrawn') DEFAULT 'active'
);

CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(255) NOT NULL,
    credits INT,
    department VARCHAR(100),
    instructor VARCHAR(255),
    semester VARCHAR(20),
    year INT
);

CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    student_id INT,
    course_id INT,
    grade VARCHAR(5),
    enrollment_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);

CREATE TABLE fees (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL DEFAULT 'org-005',
    student_id INT,
    fee_type VARCHAR(100),
    amount DECIMAL(10,2),
    due_date DATE,
    paid_amount DECIMAL(10,2) DEFAULT 0,
    status ENUM('pending', 'paid', 'overdue') DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- Sample data for EduLearn
INSERT INTO students (student_number, name, email, date_of_birth, enrollment_date, major, gpa, status) VALUES
('STU-2024-001', 'Michael Chen', 'michael.chen@edulearn.edu', '2002-05-15', '2024-09-01', 'Computer Science', 3.75, 'active'),
('STU-2024-002', 'Sarah Williams', 'sarah.williams@edulearn.edu', '2001-12-08', '2024-09-01', 'Business Administration', 3.50, 'active'),
('STU-2024-003', 'David Rodriguez', 'david.rodriguez@edulearn.edu', '2003-03-22', '2024-09-01', 'Engineering', 3.85, 'active');

INSERT INTO courses (course_code, course_name, credits, department, instructor, semester, year) VALUES
('CS101', 'Introduction to Programming', 3, 'Computer Science', 'Dr. Peterson', 'Fall', 2024),
('BUS201', 'Business Analytics', 3, 'Business', 'Prof. Anderson', 'Fall', 2024),
('ENG301', 'Advanced Mathematics', 4, 'Engineering', 'Dr. Thompson', 'Fall', 2024);

INSERT INTO enrollments (student_id, course_id, grade, enrollment_date) VALUES
(1, 1, 'A', '2024-09-01'),
(2, 2, 'B+', '2024-09-01'),
(3, 3, 'A-', '2024-09-01');

INSERT INTO fees (student_id, fee_type, amount, due_date, paid_amount, status) VALUES
(1, 'Tuition', 5000.00, '2024-12-15', 5000.00, 'paid'),
(2, 'Tuition', 4800.00, '2024-12-15', 2400.00, 'pending'),
(3, 'Tuition', 5200.00, '2024-12-15', 0.00, 'pending');