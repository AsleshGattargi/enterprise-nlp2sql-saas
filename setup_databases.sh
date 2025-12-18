#!/bin/bash
# Multi-Tenant NLP2SQL Database Setup Script

echo "[SETUP] Setting up Multi-Tenant NLP2SQL Database System..."

# Create exports directory
mkdir -p exports

# 1. Setup MySQL metadata database
echo "[DATA] Setting up MySQL metadata database..."
mysql -u root -ppassword -e "DROP DATABASE IF EXISTS nlp2sql_metadata;"
mysql -u root -ppassword -e "CREATE DATABASE nlp2sql_metadata;"
mysql -u root -ppassword nlp2sql_metadata < database/schema.sql
mysql -u root -ppassword nlp2sql_metadata < database/complete_sample_data.sql

# 2. Setup PostgreSQL databases (TechCorp & FinanceHub)
echo "[POSTGRES] Setting up PostgreSQL databases..."
# TechCorp
export PGPASSWORD=password
dropdb -h localhost -U postgres --if-exists techcorp_db
createdb -h localhost -U postgres techcorp_db
psql -h localhost -U postgres -d techcorp_db -c "
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
('Monitor 27', 'Electronics', 349.99, 'TECH-MN-004', '27-inch 4K monitor'),
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
"

# FinanceHub
dropdb -h localhost -U postgres --if-exists financehub_db
createdb -h localhost -U postgres financehub_db
psql -h localhost -U postgres -d financehub_db -f database/org_schemas.sql

# 3. Setup MySQL organization databases (HealthPlus & EduLearn)
echo "[HEALTH] Setting up HealthPlus MySQL database..."
mysql -u root -ppassword -e "DROP DATABASE IF EXISTS healthplus_db;"
mysql -u root -ppassword -e "CREATE DATABASE healthplus_db;"
# Run the healthplus portion of org_schemas.sql

echo "[EDU] Setting up EduLearn MySQL database..."
mysql -u root -ppassword -e "DROP DATABASE IF EXISTS edulearn_db;"
mysql -u root -ppassword -e "CREATE DATABASE edulearn_db;"
# Run the edulearn portion of org_schemas.sql

# 4. Setup MongoDB (RetailMax)
echo "[MONGO] Setting up MongoDB database..."
mongosh --eval "
use retailmax_db;
db.products.insertMany([
  {
    org_id: 'org-004',
    product_id: 'P001',
    name: 'Smart TV 55 inch',
    category: 'Electronics',
    price: 699.99,
    sku: 'RET-TV-001'
  },
  {
    org_id: 'org-004',
    product_id: 'P002',
    name: 'Wireless Headphones',
    category: 'Audio',
    price: 149.99,
    sku: 'RET-HP-002'
  },
  {
    org_id: 'org-004',
    product_id: 'P003',
    name: 'Gaming Console',
    category: 'Gaming',
    price: 499.99,
    sku: 'RET-GC-003'
  }
]);

db.sales.insertMany([
  {
    org_id: 'org-004',
    sale_id: 'S001',
    customer: 'Alice Johnson',
    items: [{product_id: 'P001', quantity: 1, price: 699.99}],
    total_amount: 699.99,
    sale_date: new Date('2024-01-20')
  },
  {
    org_id: 'org-004',
    sale_id: 'S002',
    customer: 'Bob Smith',
    items: [{product_id: 'P002', quantity: 2, price: 149.99}],
    total_amount: 299.98,
    sale_date: new Date('2024-01-21')
  }
]);

db.customers.insertMany([
  {
    org_id: 'org-004',
    customer_id: 'C001',
    name: 'Alice Johnson',
    email: 'alice@email.com',
    loyalty_points: 150
  },
  {
    org_id: 'org-004',
    customer_id: 'C002',
    name: 'Bob Smith',
    email: 'bob@email.com',
    loyalty_points: 75
  }
]);
"

echo "[OK] Database setup completed!"
echo ""
echo "[DATA] Database Summary:"
echo "- MySQL metadata: nlp2sql_metadata (Central system)"
echo "- PostgreSQL: techcorp_db, financehub_db"
echo "- MySQL: healthplus_db, edulearn_db"
echo "- MongoDB: retailmax_db"
echo ""
echo "[USERS] Sample users created (250 total across 5 organizations)"
echo "[AUTH] All passwords: password123"
