-- TechCorp SQLite Database Sample Data
-- This will be used to populate the existing SQLite database

-- Note: SQLite database structure should already exist
-- This script provides additional sample data for TechCorp

INSERT OR REPLACE INTO products (product_id, org_id, name, category, price, sku) VALUES
(1, 'org-001', 'Laptop Pro X1', 'Electronics', 1299.99, 'TECH-LP-001'),
(2, 'org-001', 'Wireless Mouse', 'Accessories', 29.99, 'TECH-MS-002'),
(3, 'org-001', 'USB-C Hub', 'Accessories', 79.99, 'TECH-HB-003'),
(4, 'org-001', 'Monitor 27"', 'Electronics', 349.99, 'TECH-MN-004'),
(5, 'org-001', 'Keyboard Mechanical', 'Accessories', 129.99, 'TECH-KB-005'),
(6, 'org-001', 'Webcam HD', 'Electronics', 89.99, 'TECH-WC-006'),
(7, 'org-001', 'Wireless Charger', 'Accessories', 39.99, 'TECH-WCH-007'),
(8, 'org-001', 'Bluetooth Speaker', 'Electronics', 199.99, 'TECH-BS-008');

INSERT OR REPLACE INTO sales (sale_id, org_id, customer_name, amount, quantity, sale_date) VALUES
(1, 'org-001', 'John Smith', 1299.99, 1, '2024-01-15'),
(2, 'org-001', 'Jane Doe', 59.98, 2, '2024-01-16'),
(3, 'org-001', 'Bob Johnson', 79.99, 1, '2024-01-17'),
(4, 'org-001', 'Alice Brown', 349.99, 1, '2024-01-18'),
(5, 'org-001', 'Charlie Wilson', 129.99, 1, '2024-01-19'),
(6, 'org-001', 'Diana Martinez', 289.98, 2, '2024-01-20'),
(7, 'org-001', 'Emma Davis', 39.99, 1, '2024-01-21'),
(8, 'org-001', 'Frank Garcia', 199.99, 1, '2024-01-22');

-- Additional tables for TechCorp
CREATE TABLE IF NOT EXISTS employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL DEFAULT 'org-001',
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    department TEXT NOT NULL,
    position TEXT,
    hire_date DATE,
    salary DECIMAL(10,2),
    manager_id INTEGER,
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
);

INSERT OR REPLACE INTO employees (first_name, last_name, email, department, position, hire_date, salary) VALUES
('Diana', 'Rodriguez', 'diana.rodriguez@techcorp.com', 'IT', 'IT Director', '2020-01-15', 125000.00),
('John', 'Smith', 'john.smith@techcorp.com', 'Operations', 'Operations Manager', '2021-03-01', 95000.00),
('Alex', 'Davis', 'alex.davis@techcorp.com', 'Analytics', 'Senior Analyst', '2022-06-15', 85000.00),
('Sarah', 'Johnson', 'sarah.johnson@techcorp.com', 'Sales', 'Sales Representative', '2023-01-20', 65000.00),
('Michael', 'Brown', 'michael.brown@techcorp.com', 'Engineering', 'Software Engineer', '2022-09-10', 95000.00);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
    org_id TEXT NOT NULL DEFAULT 'org-001',
    product_id INTEGER NOT NULL,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    reorder_level INTEGER DEFAULT 10,
    last_updated DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT OR REPLACE INTO inventory (product_id, quantity_available, quantity_reserved, reorder_level) VALUES
(1, 25, 3, 5),
(2, 150, 10, 20),
(3, 75, 5, 15),
(4, 40, 2, 8),
(5, 60, 8, 12),
(6, 90, 5, 15),
(7, 120, 15, 25),
(8, 35, 3, 10);