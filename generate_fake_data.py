#!/usr/bin/env python3
"""
Generate realistic fake data for all organizations in their respective databases
"""
import sys
import os
sys.path.append('src')

import random
import json
from datetime import datetime, timedelta
from database import DatabaseManager
import sqlite3
import mysql.connector
import psycopg2
from pymongo import MongoClient
from faker import Faker

# Initialize Faker
fake = Faker()
fake.seed_instance(42)  # For reproducible data

class DataGenerator:
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    def generate_techcorp_data(self):
        """Generate TechCorp (SQLite) data - Technology company"""
        print("[SQLITE] Generating TechCorp data...")
        
        try:
            conn = self.db_manager.get_org_connection('org-001', 'sqlite', 'techcorp_db')['connection']
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS order_items")
            cursor.execute("DROP TABLE IF EXISTS orders")
            cursor.execute("DROP TABLE IF EXISTS products")
            cursor.execute("DROP TABLE IF EXISTS customers")
            cursor.execute("DROP TABLE IF EXISTS employees")
            
            # Create tables
            cursor.execute('''
            CREATE TABLE employees (
                employee_id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                position TEXT NOT NULL,
                salary REAL NOT NULL,
                hire_date DATE NOT NULL,
                manager_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                contact_first_name TEXT NOT NULL,
                contact_last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                address TEXT,
                city TEXT,
                country TEXT,
                company_size TEXT,
                industry TEXT,
                created_date DATE NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                cost REAL NOT NULL,
                stock_quantity INTEGER NOT NULL,
                supplier TEXT,
                created_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT 1
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                order_date DATE NOT NULL,
                ship_date DATE,
                status TEXT NOT NULL,
                total_amount REAL NOT NULL,
                payment_method TEXT,
                shipping_address TEXT,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE order_items (
                item_id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                discount REAL DEFAULT 0,
                FOREIGN KEY (order_id) REFERENCES orders(order_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
            ''')
            
            # Generate employees
            departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance', 'Support', 'Product']
            positions = {
                'Engineering': ['Software Engineer', 'Senior Engineer', 'Tech Lead', 'DevOps Engineer', 'QA Engineer'],
                'Sales': ['Sales Rep', 'Account Manager', 'Sales Director', 'Business Development'],
                'Marketing': ['Marketing Manager', 'Content Creator', 'SEO Specialist', 'Social Media Manager'],
                'HR': ['HR Manager', 'Recruiter', 'HR Business Partner'],
                'Finance': ['Accountant', 'Financial Analyst', 'Controller'],
                'Support': ['Support Engineer', 'Customer Success Manager', 'Technical Writer'],
                'Product': ['Product Manager', 'UX Designer', 'Product Analyst']
            }
            
            employees_data = []
            for i in range(150):
                dept = random.choice(departments)
                pos = random.choice(positions[dept])
                salary = random.randint(40000, 150000)
                hire_date = fake.date_between(start_date='-5y', end_date='today')
                
                employees_data.append((
                    fake.first_name(), fake.last_name(), fake.email(),
                    dept, pos, salary, hire_date,
                    random.choice([None] + list(range(1, min(i, 10) + 1))) if i > 0 else None,
                    random.choice([True] * 9 + [False])  # 90% active
                ))
            
            cursor.executemany(
                "INSERT INTO employees (first_name, last_name, email, department, position, salary, hire_date, manager_id, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                employees_data
            )
            
            # Generate customers
            company_sizes = ['Startup', 'Small', 'Medium', 'Large', 'Enterprise']
            industries = ['Technology', 'Healthcare', 'Finance', 'Education', 'Retail', 'Manufacturing', 'Consulting']
            
            customers_data = []
            for i in range(200):
                customers_data.append((
                    fake.company(), fake.first_name(), fake.last_name(),
                    fake.email(), fake.phone_number(), fake.address(),
                    fake.city(), fake.country(), random.choice(company_sizes),
                    random.choice(industries), fake.date_between(start_date='-3y', end_date='today')
                ))
            
            cursor.executemany(
                "INSERT INTO customers (company_name, contact_first_name, contact_last_name, email, phone, address, city, country, company_size, industry, created_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                customers_data
            )
            
            # Generate products
            tech_products = [
                ('Laptop Pro X1', 'Laptops', 'High-performance business laptop', 1299.99, 800.00),
                ('Desktop Workstation Z1', 'Desktops', 'Powerful desktop for development', 1899.99, 1200.00),
                ('Wireless Mouse Pro', 'Accessories', 'Ergonomic wireless mouse', 29.99, 15.00),
                ('Mechanical Keyboard RGB', 'Accessories', 'Gaming mechanical keyboard', 129.99, 75.00),
                ('Monitor 27" 4K', 'Monitors', '4K professional monitor', 349.99, 220.00),
                ('USB-C Hub Elite', 'Accessories', 'Multi-port USB-C hub', 79.99, 45.00),
                ('Webcam HD Pro', 'Accessories', 'HD webcam for video calls', 89.99, 50.00),
                ('Headset Noise-Cancel', 'Audio', 'Noise-cancelling headset', 199.99, 120.00),
                ('Tablet Business 10"', 'Tablets', '10-inch business tablet', 499.99, 300.00),
                ('Smartphone Enterprise', 'Mobile', 'Enterprise smartphone', 699.99, 400.00),
                ('Server Rack Unit', 'Servers', '1U rack server', 2999.99, 2000.00),
                ('Network Switch 24-Port', 'Networking', '24-port network switch', 299.99, 180.00),
                ('Router WiFi 6', 'Networking', 'WiFi 6 enterprise router', 199.99, 120.00),
                ('SSD Drive 1TB', 'Storage', '1TB SSD drive', 149.99, 90.00),
                ('RAM 32GB Kit', 'Memory', '32GB DDR4 RAM kit', 199.99, 120.00)
            ]
            
            suppliers = ['TechSupplier Inc', 'GlobalTech', 'ComponentWorld', 'ElectronicsPlus', 'TechDistributor']
            
            products_data = []
            for name, category, desc, price, cost in tech_products:
                stock = random.randint(5, 500)
                supplier = random.choice(suppliers)
                created = fake.date_between(start_date='-2y', end_date='-6m')
                products_data.append((name, category, desc, price, cost, stock, supplier, created, True))
            
            cursor.executemany(
                "INSERT INTO products (product_name, category, description, price, cost, stock_quantity, supplier, created_date, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                products_data
            )
            
            # Generate orders and order items
            statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
            payment_methods = ['Credit Card', 'Bank Transfer', 'PayPal', 'Corporate Account']
            
            for i in range(500):
                customer_id = random.randint(1, 200)
                employee_id = random.randint(1, 150)
                order_date = fake.date_between(start_date='-1y', end_date='today')
                ship_date = order_date + timedelta(days=random.randint(1, 10)) if random.random() > 0.3 else None
                status = random.choice(statuses)
                payment = random.choice(payment_methods)
                
                # Generate order items
                num_items = random.randint(1, 5)
                total_amount = 0
                order_items = []
                
                for j in range(num_items):
                    product_id = random.randint(1, len(tech_products))
                    quantity = random.randint(1, 10)
                    # Get product price
                    cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
                    unit_price = cursor.fetchone()[0]
                    discount = random.choice([0, 0, 0, 5, 10, 15]) / 100  # Most items no discount
                    item_total = quantity * unit_price * (1 - discount)
                    total_amount += item_total
                    order_items.append((i+1, product_id, quantity, unit_price, discount))
                
                cursor.execute(
                    "INSERT INTO orders (customer_id, employee_id, order_date, ship_date, status, total_amount, payment_method, shipping_address, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (customer_id, employee_id, order_date, ship_date, status, round(total_amount, 2), payment, fake.address(), fake.text(max_nb_chars=100) if random.random() > 0.7 else None)
                )
                
                cursor.executemany(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount) VALUES (?, ?, ?, ?, ?)",
                    order_items
                )
            
            conn.commit()
            print(f"SUCCESS: TechCorp: Created {len(employees_data)} employees, {len(customers_data)} customers, {len(tech_products)} products, 500 orders")
            
        except Exception as e:
            print(f"FAILED: TechCorp data generation failed: {e}")

    def generate_healthplus_data(self):
        """Generate HealthPlus (MySQL) data - Healthcare organization"""
        print("[MYSQL] Generating HealthPlus data...")
        
        try:
            conn = self.db_manager.get_org_connection('org-002', 'mysql', 'healthplus_db')['connection']
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS billing")
            cursor.execute("DROP TABLE IF EXISTS appointments") 
            cursor.execute("DROP TABLE IF EXISTS treatments")
            cursor.execute("DROP TABLE IF EXISTS patients")
            cursor.execute("DROP TABLE IF EXISTS doctors")
            cursor.execute("DROP TABLE IF EXISTS departments")
            
            # Create tables
            cursor.execute('''
            CREATE TABLE departments (
                dept_id INT PRIMARY KEY AUTO_INCREMENT,
                dept_name VARCHAR(100) NOT NULL,
                description TEXT,
                head_doctor_id INT,
                location VARCHAR(100),
                phone VARCHAR(50),
                budget DECIMAL(12,2),
                created_date DATE NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE doctors (
                doctor_id INT PRIMARY KEY AUTO_INCREMENT,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(50),
                specialization VARCHAR(100) NOT NULL,
                dept_id INT,
                license_number VARCHAR(50) UNIQUE NOT NULL,
                years_experience INT,
                education VARCHAR(200),
                hire_date DATE NOT NULL,
                salary DECIMAL(10,2),
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE patients (
                patient_id INT PRIMARY KEY AUTO_INCREMENT,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                date_of_birth DATE NOT NULL,
                gender ENUM('Male', 'Female', 'Other') NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(100),
                address TEXT,
                city VARCHAR(50),
                state VARCHAR(50),
                zip_code VARCHAR(10),
                insurance_provider VARCHAR(100),
                insurance_id VARCHAR(50),
                emergency_contact_name VARCHAR(100),
                emergency_contact_phone VARCHAR(50),
                blood_type VARCHAR(5),
                allergies TEXT,
                medical_history TEXT,
                registration_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE treatments (
                treatment_id INT PRIMARY KEY AUTO_INCREMENT,
                treatment_name VARCHAR(200) NOT NULL,
                description TEXT,
                department VARCHAR(100),
                base_cost DECIMAL(10,2) NOT NULL,
                duration_minutes INT,
                requires_anesthesia BOOLEAN DEFAULT FALSE,
                created_date DATE NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE appointments (
                appointment_id INT PRIMARY KEY AUTO_INCREMENT,
                patient_id INT NOT NULL,
                doctor_id INT NOT NULL,
                appointment_date DATETIME NOT NULL,
                duration_minutes INT DEFAULT 30,
                appointment_type VARCHAR(50) NOT NULL,
                status ENUM('Scheduled', 'Confirmed', 'In Progress', 'Completed', 'Cancelled', 'No Show') DEFAULT 'Scheduled',
                notes TEXT,
                diagnosis TEXT,
                prescription TEXT,
                follow_up_required BOOLEAN DEFAULT FALSE,
                follow_up_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE billing (
                bill_id INT PRIMARY KEY AUTO_INCREMENT,
                patient_id INT NOT NULL,
                appointment_id INT,
                treatment_id INT,
                bill_date DATE NOT NULL,
                due_date DATE NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                insurance_covered DECIMAL(10,2) DEFAULT 0,
                patient_responsibility DECIMAL(10,2) NOT NULL,
                status ENUM('Pending', 'Paid', 'Partially Paid', 'Overdue', 'Cancelled') DEFAULT 'Pending',
                payment_method VARCHAR(50),
                payment_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
                FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
                FOREIGN KEY (treatment_id) REFERENCES treatments(treatment_id)
            )
            ''')
            
            # Generate departments
            departments_data = [
                ('Cardiology', 'Heart and cardiovascular system care', None, 'Building A, Floor 3', '555-0101', 2500000, '2020-01-15'),
                ('Neurology', 'Brain and nervous system treatment', None, 'Building B, Floor 2', '555-0102', 1800000, '2020-01-15'),
                ('Orthopedics', 'Bone, joint and muscle care', None, 'Building A, Floor 1', '555-0103', 2200000, '2020-01-15'),
                ('Pediatrics', 'Children healthcare services', None, 'Building C, Floor 1', '555-0104', 1500000, '2020-01-15'),
                ('Emergency', '24/7 emergency medical services', None, 'Building A, Ground Floor', '555-0105', 3000000, '2020-01-15'),
                ('Oncology', 'Cancer treatment and care', None, 'Building B, Floor 3', '555-0106', 2800000, '2020-01-15'),
                ('Radiology', 'Medical imaging services', None, 'Building B, Floor 1', '555-0107', 1200000, '2020-01-15'),
                ('Surgery', 'Surgical procedures', None, 'Building A, Floor 2', '555-0108', 3200000, '2020-01-15')
            ]
            
            cursor.executemany(
                "INSERT INTO departments (dept_name, description, head_doctor_id, location, phone, budget, created_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                departments_data
            )
            
            # Generate doctors
            specializations = {
                1: ['Cardiologist', 'Interventional Cardiologist', 'Cardiac Surgeon'],
                2: ['Neurologist', 'Neurosurgeon', 'Neuropsychologist'],
                3: ['Orthopedic Surgeon', 'Sports Medicine', 'Joint Replacement Specialist'],
                4: ['Pediatrician', 'Neonatologist', 'Pediatric Cardiologist'],
                5: ['Emergency Medicine', 'Trauma Surgeon', 'Critical Care'],
                6: ['Oncologist', 'Radiation Oncologist', 'Surgical Oncologist'],
                7: ['Radiologist', 'Nuclear Medicine', 'Interventional Radiologist'],
                8: ['General Surgeon', 'Plastic Surgeon', 'Vascular Surgeon']
            }
            
            universities = [
                'Harvard Medical School', 'Johns Hopkins University', 'Stanford Medical School',
                'Mayo Clinic School of Medicine', 'University of Pennsylvania', 'Duke University',
                'Washington University', 'Yale School of Medicine', 'UCLA Medical School'
            ]
            
            doctors_data = []
            for i in range(80):
                dept_id = random.randint(1, 8)
                spec = random.choice(specializations[dept_id])
                license_num = f"MD{random.randint(100000, 999999)}"
                experience = random.randint(1, 30)
                education = f"MD from {random.choice(universities)}"
                hire_date = fake.date_between(start_date='-10y', end_date='today')
                salary = random.randint(200000, 800000)
                
                doctors_data.append((
                    fake.first_name(), fake.last_name(), fake.email(),
                    fake.phone_number(), spec, dept_id, license_num,
                    experience, education, hire_date, salary,
                    random.choice([True] * 19 + [False])  # 95% active
                ))
            
            cursor.executemany(
                "INSERT INTO doctors (first_name, last_name, email, phone, specialization, dept_id, license_number, years_experience, education, hire_date, salary, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                doctors_data
            )
            
            # Generate patients
            blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            insurance_providers = ['Blue Cross', 'Aetna', 'Cigna', 'UnitedHealth', 'Kaiser', 'Humana', 'Medicare', 'Medicaid']
            common_allergies = ['None', 'Penicillin', 'Peanuts', 'Shellfish', 'Latex', 'Aspirin', 'Sulfa drugs']
            
            patients_data = []
            for i in range(1000):
                birth_date = fake.date_of_birth(minimum_age=0, maximum_age=95)
                gender = random.choice(['Male', 'Female', 'Other'])
                blood_type = random.choice(blood_types)
                insurance = random.choice(insurance_providers)
                allergies = random.choice(common_allergies)
                reg_date = fake.date_between(start_date='-3y', end_date='today')
                
                patients_data.append((
                    fake.first_name(), fake.last_name(), birth_date, gender,
                    fake.phone_number(), fake.email(), fake.address(),
                    fake.city(), fake.state(), fake.zipcode(),
                    insurance, f"INS{random.randint(100000, 999999)}",
                    fake.name(), fake.phone_number(), blood_type,
                    allergies, fake.text(max_nb_chars=200) if random.random() > 0.6 else None,
                    reg_date, True
                ))
            
            cursor.executemany(
                "INSERT INTO patients (first_name, last_name, date_of_birth, gender, phone, email, address, city, state, zip_code, insurance_provider, insurance_id, emergency_contact_name, emergency_contact_phone, blood_type, allergies, medical_history, registration_date, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                patients_data
            )
            
            # Generate treatments
            treatments_data = [
                ('Annual Physical Exam', 'Comprehensive yearly health checkup', 'General Medicine', 150.00, 60, False, '2020-01-01'),
                ('Blood Test - Complete Panel', 'Comprehensive blood work analysis', 'Laboratory', 85.00, 15, False, '2020-01-01'),
                ('X-Ray - Chest', 'Chest X-ray imaging', 'Radiology', 120.00, 20, False, '2020-01-01'),
                ('MRI - Brain', 'Magnetic resonance imaging of brain', 'Radiology', 1200.00, 45, False, '2020-01-01'),
                ('Cardiac Catheterization', 'Heart catheter procedure', 'Cardiology', 5500.00, 120, True, '2020-01-01'),
                ('Knee Replacement Surgery', 'Total knee joint replacement', 'Orthopedics', 25000.00, 180, True, '2020-01-01'),
                ('Chemotherapy Session', 'Cancer treatment session', 'Oncology', 3500.00, 240, False, '2020-01-01'),
                ('Emergency Room Visit', 'Emergency medical evaluation', 'Emergency', 450.00, 90, False, '2020-01-01'),
                ('Colonoscopy', 'Colon examination procedure', 'Gastroenterology', 800.00, 60, True, '2020-01-01'),
                ('Pediatric Vaccination', 'Childhood vaccination', 'Pediatrics', 75.00, 15, False, '2020-01-01')
            ]
            
            cursor.executemany(
                "INSERT INTO treatments (treatment_name, description, department, base_cost, duration_minutes, requires_anesthesia, created_date) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                treatments_data
            )
            
            # Generate appointments
            appointment_types = ['Consultation', 'Follow-up', 'Emergency', 'Surgery', 'Procedure', 'Screening']
            statuses = ['Scheduled', 'Confirmed', 'In Progress', 'Completed', 'Cancelled', 'No Show']
            
            for i in range(2000):
                patient_id = random.randint(1, 1000)
                doctor_id = random.randint(1, 80)
                appt_date = fake.date_time_between(start_date='-6m', end_date='+3m')
                duration = random.choice([30, 45, 60, 90, 120])
                appt_type = random.choice(appointment_types)
                status = random.choice(statuses)
                
                cursor.execute(
                    "INSERT INTO appointments (patient_id, doctor_id, appointment_date, duration_minutes, appointment_type, status, notes, diagnosis, prescription, follow_up_required, follow_up_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (patient_id, doctor_id, appt_date, duration, appt_type, status,
                     fake.text(max_nb_chars=100) if random.random() > 0.5 else None,
                     fake.text(max_nb_chars=150) if status == 'Completed' and random.random() > 0.3 else None,
                     fake.text(max_nb_chars=100) if status == 'Completed' and random.random() > 0.4 else None,
                     random.choice([True, False]) if status == 'Completed' else False,
                     fake.future_date(end_date='+30d') if status == 'Completed' and random.random() > 0.7 else None)
                )
            
            # Generate billing records
            payment_methods = ['Cash', 'Credit Card', 'Insurance', 'Check', 'Bank Transfer']
            bill_statuses = ['Pending', 'Paid', 'Partially Paid', 'Overdue', 'Cancelled']
            
            for i in range(1500):
                patient_id = random.randint(1, 1000)
                treatment_id = random.randint(1, len(treatments_data))
                bill_date = fake.date_between(start_date='-1y', end_date='today')
                due_date = bill_date + timedelta(days=30)
                
                # Get treatment cost
                cursor.execute("SELECT base_cost FROM treatments WHERE treatment_id = %s", (treatment_id,))
                base_amount = cursor.fetchone()[0]
                
                # Add some variation to the amount
                amount = float(base_amount) * random.uniform(0.8, 1.3)
                insurance_covered = amount * random.uniform(0.6, 0.9) if random.random() > 0.2 else 0
                patient_responsibility = amount - insurance_covered
                
                status = random.choice(bill_statuses)
                payment_date = bill_date + timedelta(days=random.randint(1, 45)) if status in ['Paid', 'Partially Paid'] else None
                
                cursor.execute(
                    "INSERT INTO billing (patient_id, treatment_id, bill_date, due_date, amount, insurance_covered, patient_responsibility, status, payment_method, payment_date, notes) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (patient_id, treatment_id, bill_date, due_date, round(amount, 2),
                     round(insurance_covered, 2), round(patient_responsibility, 2), status,
                     random.choice(payment_methods) if payment_date else None,
                     payment_date, fake.text(max_nb_chars=50) if random.random() > 0.8 else None)
                )
            
            conn.commit()
            print(f"SUCCESS: HealthPlus: Created {len(departments_data)} departments, {len(doctors_data)} doctors, {len(patients_data)} patients, 2000 appointments, 1500 bills")
            
        except Exception as e:
            print(f"FAILED: HealthPlus data generation failed: {e}")

    def generate_financehub_data(self):
        """Generate FinanceHub (PostgreSQL) data - Financial services"""
        print("[POSTGRESQL] Generating FinanceHub data...")
        
        try:
            conn = self.db_manager.get_org_connection('org-003', 'postgresql', 'financehub_db')['connection']
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS loan_payments CASCADE")
            cursor.execute("DROP TABLE IF EXISTS loans CASCADE")
            cursor.execute("DROP TABLE IF EXISTS investment_transactions CASCADE")
            cursor.execute("DROP TABLE IF EXISTS investments CASCADE")
            cursor.execute("DROP TABLE IF EXISTS transactions CASCADE")
            cursor.execute("DROP TABLE IF EXISTS accounts CASCADE")
            cursor.execute("DROP TABLE IF EXISTS customers CASCADE")
            cursor.execute("DROP TABLE IF EXISTS branches CASCADE")
            
            # Create tables
            cursor.execute('''
            CREATE TABLE branches (
                branch_id SERIAL PRIMARY KEY,
                branch_name VARCHAR(100) NOT NULL,
                branch_code VARCHAR(10) UNIQUE NOT NULL,
                address TEXT NOT NULL,
                city VARCHAR(50) NOT NULL,
                state VARCHAR(50) NOT NULL,
                zip_code VARCHAR(10) NOT NULL,
                phone VARCHAR(50),
                manager_name VARCHAR(100),
                established_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE customers (
                customer_id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                date_of_birth DATE NOT NULL,
                ssn VARCHAR(11) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(50),
                address TEXT,
                city VARCHAR(50),
                state VARCHAR(50),
                zip_code VARCHAR(10),
                occupation VARCHAR(100),
                annual_income DECIMAL(12,2),
                credit_score INTEGER,
                branch_id INTEGER REFERENCES branches(branch_id),
                customer_since DATE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE accounts (
                account_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                account_number VARCHAR(50) UNIQUE NOT NULL,
                account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Checking', 'Savings', 'Business', 'CD', 'Money Market')),
                balance DECIMAL(15,2) NOT NULL DEFAULT 0,
                interest_rate DECIMAL(5,4) DEFAULT 0,
                opened_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Closed', 'Frozen', 'Dormant')),
                minimum_balance DECIMAL(10,2) DEFAULT 0,
                monthly_fee DECIMAL(6,2) DEFAULT 0
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE transactions (
                transaction_id SERIAL PRIMARY KEY,
                account_id INTEGER NOT NULL REFERENCES accounts(account_id),
                transaction_date TIMESTAMP NOT NULL,
                transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Fee', 'Interest', 'Check', 'ATM', 'Online')),
                amount DECIMAL(12,2) NOT NULL,
                balance_after DECIMAL(15,2) NOT NULL,
                description TEXT,
                reference_number VARCHAR(100),
                branch_id INTEGER REFERENCES branches(branch_id),
                is_cleared BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE investments (
                investment_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                investment_type VARCHAR(50) NOT NULL,
                symbol VARCHAR(10),
                investment_name VARCHAR(100) NOT NULL,
                shares DECIMAL(15,6),
                purchase_price DECIMAL(10,4),
                current_price DECIMAL(10,4),
                purchase_date DATE NOT NULL,
                maturity_date DATE,
                annual_return DECIMAL(5,4),
                risk_level VARCHAR(10) CHECK (risk_level IN ('Low', 'Medium', 'High')),
                status VARCHAR(20) DEFAULT 'Active'
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE investment_transactions (
                transaction_id SERIAL PRIMARY KEY,
                investment_id INTEGER NOT NULL REFERENCES investments(investment_id),
                transaction_date DATE NOT NULL,
                transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Buy', 'Sell', 'Dividend', 'Split', 'Merger')),
                shares DECIMAL(15,6),
                price_per_share DECIMAL(10,4),
                total_amount DECIMAL(12,2) NOT NULL,
                fees DECIMAL(8,2) DEFAULT 0,
                description TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE loans (
                loan_id SERIAL PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
                loan_type VARCHAR(30) NOT NULL CHECK (loan_type IN ('Mortgage', 'Personal', 'Auto', 'Business', 'Student', 'Home Equity')),
                loan_amount DECIMAL(12,2) NOT NULL,
                interest_rate DECIMAL(5,4) NOT NULL,
                term_months INTEGER NOT NULL,
                monthly_payment DECIMAL(10,2) NOT NULL,
                balance_remaining DECIMAL(12,2) NOT NULL,
                origination_date DATE NOT NULL,
                maturity_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Paid Off', 'Default', 'Delinquent')),
                collateral_description TEXT,
                purpose TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE loan_payments (
                payment_id SERIAL PRIMARY KEY,
                loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
                payment_date DATE NOT NULL,
                payment_amount DECIMAL(10,2) NOT NULL,
                principal_amount DECIMAL(10,2) NOT NULL,
                interest_amount DECIMAL(10,2) NOT NULL,
                balance_after DECIMAL(12,2) NOT NULL,
                payment_method VARCHAR(20),
                late_fee DECIMAL(6,2) DEFAULT 0,
                is_late BOOLEAN DEFAULT FALSE
            )
            ''')
            
            # Generate branches
            branch_cities = [
                ('New York', 'NY'), ('Los Angeles', 'CA'), ('Chicago', 'IL'),
                ('Houston', 'TX'), ('Phoenix', 'AZ'), ('Philadelphia', 'PA'),
                ('San Antonio', 'TX'), ('San Diego', 'CA'), ('Dallas', 'TX'),
                ('San Jose', 'CA'), ('Austin', 'TX'), ('Jacksonville', 'FL')
            ]
            
            branches_data = []
            for i, (city, state) in enumerate(branch_cities[:10]):
                branch_code = f"FH{i+1:03d}"
                branches_data.append((
                    f"FinanceHub {city}", branch_code, fake.address(),
                    city, state, fake.zipcode(), fake.phone_number(),
                    fake.name(), fake.date_between(start_date='-20y', end_date='-1y'), True
                ))
            
            cursor.executemany(
                "INSERT INTO branches (branch_name, branch_code, address, city, state, zip_code, phone, manager_name, established_date, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                branches_data
            )
            
            # Generate customers
            occupations = [
                'Software Engineer', 'Teacher', 'Nurse', 'Manager', 'Sales Rep',
                'Accountant', 'Lawyer', 'Doctor', 'Engineer', 'Consultant',
                'Marketing Manager', 'Analyst', 'Designer', 'Chef', 'Mechanic'
            ]
            
            customers_data = []
            for i in range(800):
                birth_date = fake.date_of_birth(minimum_age=18, maximum_age=80)
                ssn = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
                income = random.randint(30000, 250000)
                credit_score = random.randint(300, 850)
                branch_id = random.randint(1, 10)
                customer_since = fake.date_between(start_date='-10y', end_date='today')
                
                customers_data.append((
                    fake.first_name(), fake.last_name(), birth_date, ssn,
                    f"{fake.user_name()}{i}@{fake.domain_name()}", fake.phone_number(), fake.address(),
                    fake.city(), fake.state(), fake.zipcode(),
                    random.choice(occupations), income, credit_score,
                    branch_id, customer_since, True
                ))
            
            cursor.executemany(
                "INSERT INTO customers (first_name, last_name, date_of_birth, ssn, email, phone, address, city, state, zip_code, occupation, annual_income, credit_score, branch_id, customer_since, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                customers_data
            )
            
            # Generate accounts
            account_types = [
                ('Checking', 0.01, 25.0, 5.00),
                ('Savings', 0.15, 100.0, 0.00),
                ('Business', 0.05, 500.0, 15.00),
                ('CD', 2.5, 1000.0, 0.00),
                ('Money Market', 1.2, 2500.0, 10.00)
            ]
            
            accounts_data = []
            for i in range(1200):
                customer_id = random.randint(1, 800)
                account_type, interest_rate, min_balance, monthly_fee = random.choice(account_types)
                account_number = f"{random.randint(10000000, 99999999)}"
                
                # Generate realistic initial balance
                if account_type == 'CD':
                    balance = random.randint(1000, 50000)
                elif account_type == 'Business':
                    balance = random.randint(500, 100000)
                elif account_type == 'Money Market':
                    balance = random.randint(2500, 75000)
                else:
                    balance = random.randint(50, 25000)
                
                opened_date = fake.date_between(start_date='-5y', end_date='today')
                status = random.choices(['Active', 'Closed', 'Frozen', 'Dormant'], 
                                      weights=[85, 10, 3, 2])[0]
                
                accounts_data.append((
                    customer_id, account_number, account_type, balance,
                    interest_rate, opened_date, status, min_balance, monthly_fee
                ))
            
            cursor.executemany(
                "INSERT INTO accounts (customer_id, account_number, account_type, balance, interest_rate, opened_date, status, minimum_balance, monthly_fee) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                accounts_data
            )
            
            # Generate transactions
            transaction_types = ['Deposit', 'Withdrawal', 'Transfer', 'Fee', 'Interest', 'Check', 'ATM', 'Online']
            
            for account_id in range(1, 1201):
                # Get account info
                cursor.execute("SELECT balance, opened_date FROM accounts WHERE account_id = %s", (account_id,))
                current_balance, opened_date = cursor.fetchone()
                
                # Generate 10-50 transactions per account
                num_transactions = random.randint(10, 50)
                balance = float(current_balance) * 0.1  # Start with lower balance
                
                for j in range(num_transactions):
                    transaction_date = fake.date_time_between(
                        start_date=opened_date, 
                        end_date='now'
                    )
                    
                    transaction_type = random.choice(transaction_types)
                    
                    # Generate realistic transaction amounts
                    if transaction_type in ['Deposit', 'Transfer']:
                        amount = random.uniform(50, 2000)
                        balance += amount
                    elif transaction_type == 'Interest':
                        amount = balance * 0.001  # Small interest
                        balance += amount
                    elif transaction_type == 'Fee':
                        amount = random.uniform(5, 35)
                        balance -= amount
                    else:  # Withdrawal, Check, ATM, Online
                        amount = random.uniform(20, min(500, balance * 0.3))
                        balance -= amount
                    
                    balance = max(balance, -100)  # Allow small overdrafts
                    
                    cursor.execute(
                        "INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, balance_after, description, reference_number, branch_id, is_cleared) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (account_id, transaction_date, transaction_type, 
                         round(amount, 2), round(balance, 2),
                         fake.text(max_nb_chars=50) if random.random() > 0.6 else None,
                         f"REF{random.randint(10000, 99999)}" if random.random() > 0.5 else None,
                         random.randint(1, 10) if random.random() > 0.3 else None,
                         random.choice([True] * 9 + [False]))
                    )
                
                # Update account balance
                cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", 
                             (round(balance, 2), account_id))
            
            conn.commit()
            print(f"SUCCESS: FinanceHub: Created {len(branches_data)} branches, {len(customers_data)} customers, {len(accounts_data)} accounts, ~30,000 transactions")
            
        except Exception as e:
            print(f"FAILED: FinanceHub data generation failed: {e}")

    def generate_retailmax_data(self):
        """Generate RetailMax (MongoDB) data - E-commerce retail"""
        print("[MONGODB] Generating RetailMax data...")
        
        try:
            db_conn = self.db_manager.get_org_connection('org-004', 'mongodb', 'retailmax_db')['connection']
            
            # Clear existing collections
            db_conn.drop_collection('customers')
            db_conn.drop_collection('products') 
            db_conn.drop_collection('orders')
            db_conn.drop_collection('reviews')
            db_conn.drop_collection('inventory')
            db_conn.drop_collection('suppliers')
            
            # Generate suppliers
            suppliers_data = []
            supplier_names = [
                'Global Electronics Ltd', 'Fashion Forward Inc', 'SportsTech Supply',
                'Home & Garden Direct', 'Beauty Products Co', 'Tech Innovations LLC',
                'Outdoor Adventures Supply', 'Kitchen Masters Inc', 'Auto Parts Express',
                'Book Publishers United'
            ]
            
            for i, name in enumerate(supplier_names):
                suppliers_data.append({
                    'supplier_id': i + 1,
                    'company_name': name,
                    'contact_person': fake.name(),
                    'email': fake.email(),
                    'phone': fake.phone_number(),
                    'address': {
                        'street': fake.address(),
                        'city': fake.city(),
                        'state': fake.state(),
                        'country': fake.country(),
                        'zip_code': fake.zipcode()
                    },
                    'payment_terms': random.choice(['Net 30', 'Net 60', 'COD', '2/10 Net 30']),
                    'rating': round(random.uniform(3.0, 5.0), 1),
                    'established_date': fake.date_between(start_date='-20y', end_date='-1y').isoformat(),
                    'is_active': True
                })
            
            db_conn.suppliers.insert_many(suppliers_data)
            
            # Generate products
            categories = {
                'Electronics': ['Smartphone', 'Laptop', 'Tablet', 'Headphones', 'Speaker', 'TV', 'Camera'],
                'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Jacket', 'Shoes', 'Hat', 'Accessories'],
                'Home & Garden': ['Furniture', 'Decor', 'Tools', 'Garden', 'Kitchen', 'Bedding'],
                'Sports': ['Fitness Equipment', 'Outdoor Gear', 'Team Sports', 'Water Sports'],
                'Books': ['Fiction', 'Non-Fiction', 'Educational', 'Children', 'Comics'],
                'Beauty': ['Skincare', 'Makeup', 'Hair Care', 'Fragrances', 'Tools'],
                'Automotive': ['Parts', 'Accessories', 'Tools', 'Maintenance', 'Electronics'],
                'Toys': ['Educational', 'Action Figures', 'Dolls', 'Games', 'Outdoor'],
                'Health': ['Supplements', 'Fitness', 'Personal Care', 'Medical Devices']
            }
            
            products_data = []
            product_id = 1
            
            for category, subcategories in categories.items():
                for subcategory in subcategories:
                    # Generate 15-25 products per subcategory
                    num_products = random.randint(15, 25)
                    
                    for i in range(num_products):
                        price = round(random.uniform(9.99, 999.99), 2)
                        cost = round(price * random.uniform(0.4, 0.7), 2)
                        
                        product = {
                            'product_id': product_id,
                            'sku': f"RTL{product_id:06d}",
                            'name': f"{fake.catch_phrase()} {subcategory}",
                            'description': fake.text(max_nb_chars=200),
                            'category': category,
                            'subcategory': subcategory,
                            'brand': fake.company(),
                            'price': price,
                            'cost': cost,
                            'currency': 'USD',
                            'dimensions': {
                                'length': round(random.uniform(5, 50), 2),
                                'width': round(random.uniform(5, 50), 2),
                                'height': round(random.uniform(2, 30), 2),
                                'weight': round(random.uniform(0.1, 20), 2)
                            },
                            'specifications': {
                                'color': fake.color_name(),
                                'material': random.choice(['Plastic', 'Metal', 'Wood', 'Fabric', 'Glass', 'Composite']),
                                'warranty_months': random.choice([6, 12, 24, 36])
                            },
                            'supplier_id': random.randint(1, len(supplier_names)),
                            'tags': [fake.word() for _ in range(random.randint(3, 8))],
                            'rating': {
                                'average': round(random.uniform(2.0, 5.0), 1),
                                'count': random.randint(0, 500)
                            },
                            'images': [
                                f"https://images.retailmax.com/products/{product_id}/main.jpg",
                                f"https://images.retailmax.com/products/{product_id}/alt1.jpg"
                            ],
                            'seo': {
                                'meta_title': f"Buy {subcategory} Online - RetailMax",
                                'meta_description': fake.text(max_nb_chars=150),
                                'keywords': [subcategory.lower(), category.lower(), 'buy online', 'retailmax']
                            },
                            'is_active': random.choice([True] * 9 + [False]),  # 90% active
                            'featured': random.choice([True] + [False] * 9),  # 10% featured
                            'created_date': fake.date_between(start_date='-2y', end_date='today').isoformat(),
                            'last_updated': fake.date_between(start_date='-30d', end_date='today').isoformat()
                        }
                        
                        products_data.append(product)
                        product_id += 1
            
            db_conn.products.insert_many(products_data)
            
            # Generate inventory
            inventory_data = []
            for product in products_data[:500]:  # Add inventory for first 500 products
                inventory_data.append({
                    'product_id': product['product_id'],
                    'sku': product['sku'],
                    'warehouse_location': random.choice(['Warehouse A', 'Warehouse B', 'Warehouse C']),
                    'quantity_on_hand': random.randint(0, 1000),
                    'quantity_reserved': random.randint(0, 50),
                    'reorder_point': random.randint(10, 100),
                    'reorder_quantity': random.randint(50, 500),
                    'last_restocked': fake.date_between(start_date='-90d', end_date='today').isoformat(),
                    'last_sold': fake.date_between(start_date='-30d', end_date='today').isoformat()
                })
            
            db_conn.inventory.insert_many(inventory_data)
            
            # Generate customers
            customers_data = []
            for i in range(1500):
                registration_date = fake.date_between(start_date='-3y', end_date='today')
                
                customer = {
                    'customer_id': i + 1,
                    'email': fake.email(),
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'phone': fake.phone_number(),
                    'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                    'gender': random.choice(['Male', 'Female', 'Other', 'Prefer not to say']),
                    'addresses': [
                        {
                            'type': 'billing',
                            'street': fake.address(),
                            'city': fake.city(),
                            'state': fake.state(),
                            'country': 'USA',
                            'zip_code': fake.zipcode(),
                            'is_default': True
                        },
                        {
                            'type': 'shipping',
                            'street': fake.address() if random.random() > 0.3 else None,
                            'city': fake.city() if random.random() > 0.3 else None,
                            'state': fake.state() if random.random() > 0.3 else None,
                            'country': 'USA',
                            'zip_code': fake.zipcode() if random.random() > 0.3 else None,
                            'is_default': random.choice([True, False])
                        }
                    ],
                    'preferences': {
                        'newsletter_subscribed': random.choice([True, False]),
                        'sms_notifications': random.choice([True, False]),
                        'preferred_categories': random.sample(list(categories.keys()), k=random.randint(1, 4)),
                        'language': 'English',
                        'currency': 'USD'
                    },
                    'loyalty': {
                        'tier': random.choice(['Bronze', 'Silver', 'Gold', 'Platinum']),
                        'points': random.randint(0, 5000),
                        'total_spent': round(random.uniform(0, 5000), 2)
                    },
                    'registration_date': registration_date.isoformat(),
                    'last_login': fake.date_between(start_date=registration_date, end_date='today').isoformat(),
                    'is_active': random.choice([True] * 9 + [False]),  # 90% active
                    'marketing_opt_in': random.choice([True, False])
                }
                
                customers_data.append(customer)
            
            db_conn.customers.insert_many(customers_data)
            
            # Generate orders
            orders_data = []
            order_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled', 'Returned']
            payment_methods = ['Credit Card', 'PayPal', 'Apple Pay', 'Google Pay', 'Bank Transfer']
            
            for i in range(3000):
                customer = random.choice(customers_data)
                order_date = fake.date_between(start_date='-1y', end_date='today')
                
                # Generate order items
                num_items = random.randint(1, 8)
                order_items = []
                subtotal = 0
                
                for j in range(num_items):
                    product = random.choice(products_data[:500])  # Use products with inventory
                    quantity = random.randint(1, 5)
                    unit_price = product['price']
                    discount = round(random.choice([0, 0, 0, 5, 10, 15, 20]) / 100 * unit_price, 2)
                    item_total = (unit_price - discount) * quantity
                    subtotal += item_total
                    
                    order_items.append({
                        'product_id': product['product_id'],
                        'sku': product['sku'],
                        'name': product['name'],
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'discount': discount,
                        'total': round(item_total, 2)
                    })
                
                # Calculate totals
                tax_rate = 0.08  # 8% tax
                shipping_cost = round(random.uniform(5.99, 15.99), 2) if subtotal < 50 else 0
                tax_amount = round(subtotal * tax_rate, 2)
                total_amount = round(subtotal + tax_amount + shipping_cost, 2)
                
                status = random.choice(order_statuses)
                
                order = {
                    'order_id': i + 1,
                    'order_number': f"ORD{i+1:06d}",
                    'customer_id': customer['customer_id'],
                    'customer_email': customer['email'],
                    'order_date': order_date.isoformat(),
                    'status': status,
                    'items': order_items,
                    'pricing': {
                        'subtotal': round(subtotal, 2),
                        'tax_amount': tax_amount,
                        'shipping_cost': shipping_cost,
                        'discount_amount': sum(item['discount'] * item['quantity'] for item in order_items),
                        'total_amount': total_amount
                    },
                    'shipping_address': random.choice(customer['addresses']),
                    'billing_address': next(addr for addr in customer['addresses'] if addr['type'] == 'billing'),
                    'payment': {
                        'method': random.choice(payment_methods),
                        'status': 'Completed' if status != 'Cancelled' else 'Refunded',
                        'transaction_id': f"TXN{random.randint(100000, 999999)}",
                        'processed_date': order_date.isoformat() if status != 'Pending' else None
                    },
                    'shipping': {
                        'carrier': random.choice(['FedEx', 'UPS', 'USPS', 'DHL']),
                        'service': random.choice(['Ground', 'Express', 'Overnight', '2-Day']),
                        'tracking_number': f"TRACK{random.randint(100000000, 999999999)}" if status in ['Shipped', 'Delivered'] else None,
                        'shipped_date': (order_date + timedelta(days=random.randint(1, 3))).isoformat() if status in ['Shipped', 'Delivered'] else None,
                        'estimated_delivery': (order_date + timedelta(days=random.randint(3, 10))).isoformat(),
                        'delivered_date': (order_date + timedelta(days=random.randint(3, 7))).isoformat() if status == 'Delivered' else None
                    },
                    'notes': fake.text(max_nb_chars=100) if random.random() > 0.7 else None,
                    'created_at': order_date.isoformat(),
                    'updated_at': fake.date_between(start_date=order_date, end_date='today').isoformat()
                }
                
                orders_data.append(order)
            
            db_conn.orders.insert_many(orders_data)
            
            # Generate reviews
            reviews_data = []
            for i in range(2000):
                customer = random.choice(customers_data)
                product = random.choice(products_data[:500])
                
                review = {
                    'review_id': i + 1,
                    'product_id': product['product_id'],
                    'customer_id': customer['customer_id'],
                    'customer_name': f"{customer['first_name']} {customer['last_name'][0]}.",
                    'rating': random.randint(1, 5),
                    'title': fake.sentence(nb_words=6),
                    'review_text': fake.text(max_nb_chars=300),
                    'verified_purchase': random.choice([True] * 7 + [False] * 3),  # 70% verified
                    'helpful_votes': random.randint(0, 50),
                    'total_votes': random.randint(0, 60),
                    'review_date': fake.date_between(start_date='-1y', end_date='today').isoformat(),
                    'is_approved': random.choice([True] * 9 + [False]),  # 90% approved
                    'response': {
                        'text': fake.text(max_nb_chars=150),
                        'response_date': fake.date_between(start_date='-6m', end_date='today').isoformat(),
                        'responder': 'RetailMax Customer Service'
                    } if random.random() > 0.8 else None
                }
                
                reviews_data.append(review)
            
            db_conn.reviews.insert_many(reviews_data)
            
            print(f"SUCCESS: RetailMax: Created {len(suppliers_data)} suppliers, {len(products_data)} products, 500 inventory records, {len(customers_data)} customers, {len(orders_data)} orders, {len(reviews_data)} reviews")
            
        except Exception as e:
            print(f"FAILED: RetailMax data generation failed: {e}")

    def generate_edulearn_data(self):
        """Generate EduLearn (MySQL) data - Education institution"""
        print("[MYSQL] Generating EduLearn data...")
        
        try:
            conn = self.db_manager.get_org_connection('org-005', 'mysql', 'edulearn_db')['connection']
            cursor = conn.cursor()
            
            # Drop existing tables
            cursor.execute("DROP TABLE IF EXISTS assignment_submissions")
            cursor.execute("DROP TABLE IF EXISTS assignments")
            cursor.execute("DROP TABLE IF EXISTS grades")
            cursor.execute("DROP TABLE IF EXISTS enrollments")
            cursor.execute("DROP TABLE IF EXISTS courses")
            cursor.execute("DROP TABLE IF EXISTS instructors")
            cursor.execute("DROP TABLE IF EXISTS students")
            cursor.execute("DROP TABLE IF EXISTS departments")
            
            # Create tables
            cursor.execute('''
            CREATE TABLE departments (
                dept_id INT PRIMARY KEY AUTO_INCREMENT,
                dept_name VARCHAR(100) NOT NULL,
                dept_code VARCHAR(10) UNIQUE NOT NULL,
                description TEXT,
                head_instructor_id INT,
                building VARCHAR(50),
                phone VARCHAR(50),
                budget DECIMAL(12,2),
                established_year YEAR,
                is_active BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE instructors (
                instructor_id INT PRIMARY KEY AUTO_INCREMENT,
                employee_id VARCHAR(20) UNIQUE NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(50),
                title VARCHAR(50) NOT NULL,
                dept_id INT,
                office_location VARCHAR(50),
                education_level VARCHAR(20),
                specialization VARCHAR(100),
                hire_date DATE NOT NULL,
                salary DECIMAL(10,2),
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE students (
                student_id INT PRIMARY KEY AUTO_INCREMENT,
                student_number VARCHAR(20) UNIQUE NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(50),
                date_of_birth DATE NOT NULL,
                gender ENUM('Male', 'Female', 'Other') NOT NULL,
                address TEXT,
                city VARCHAR(50),
                state VARCHAR(50),
                zip_code VARCHAR(10),
                major VARCHAR(100),
                minor VARCHAR(100),
                year_level ENUM('Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate') NOT NULL,
                enrollment_date DATE NOT NULL,
                graduation_date DATE,
                gpa DECIMAL(3,2),
                credits_completed INT DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE courses (
                course_id INT PRIMARY KEY AUTO_INCREMENT,
                course_code VARCHAR(20) UNIQUE NOT NULL,
                course_name VARCHAR(200) NOT NULL,
                description TEXT,
                dept_id INT NOT NULL,
                credits INT NOT NULL,
                max_enrollment INT DEFAULT 30,
                prerequisite_course_id INT,
                difficulty_level ENUM('Beginner', 'Intermediate', 'Advanced', 'Graduate') DEFAULT 'Beginner',
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
                FOREIGN KEY (prerequisite_course_id) REFERENCES courses(course_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE enrollments (
                enrollment_id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                instructor_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL,
                year YEAR NOT NULL,
                enrollment_date DATE NOT NULL,
                grade VARCHAR(2),
                status ENUM('Enrolled', 'Completed', 'Dropped', 'Withdrawn') DEFAULT 'Enrolled',
                final_score DECIMAL(5,2),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id),
                UNIQUE KEY unique_enrollment (student_id, course_id, semester, year)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE assignments (
                assignment_id INT PRIMARY KEY AUTO_INCREMENT,
                course_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                assignment_type ENUM('Homework', 'Quiz', 'Exam', 'Project', 'Lab', 'Essay') NOT NULL,
                total_points INT NOT NULL,
                due_date DATETIME NOT NULL,
                created_date DATE NOT NULL,
                instructions TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE assignment_submissions (
                submission_id INT PRIMARY KEY AUTO_INCREMENT,
                assignment_id INT NOT NULL,
                student_id INT NOT NULL,
                submission_date DATETIME NOT NULL,
                score DECIMAL(5,2),
                max_score DECIMAL(5,2),
                feedback TEXT,
                is_late BOOLEAN DEFAULT FALSE,
                attempt_number INT DEFAULT 1,
                file_path VARCHAR(500),
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE grades (
                grade_id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                course_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL,
                year YEAR NOT NULL,
                midterm_score DECIMAL(5,2),
                final_score DECIMAL(5,2),
                total_assignments_score DECIMAL(5,2),
                participation_score DECIMAL(5,2),
                final_grade VARCHAR(2),
                grade_points DECIMAL(3,2),
                recorded_date DATE NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
            ''')
            
            # Generate departments
            departments_data = [
                ('Computer Science', 'CS', 'Computer Science and Software Engineering', None, 'Science Building', '555-0201', 2500000, 1995),
                ('Mathematics', 'MATH', 'Mathematics and Statistics Department', None, 'Math Building', '555-0202', 1800000, 1990),
                ('English', 'ENG', 'English Literature and Writing', None, 'Liberal Arts Building', '555-0203', 1200000, 1985),
                ('Business', 'BUS', 'Business Administration and Management', None, 'Business Center', '555-0204', 2000000, 1988),
                ('Psychology', 'PSY', 'Psychology and Human Behavior', None, 'Social Sciences Building', '555-0205', 1500000, 1992),
                ('Biology', 'BIO', 'Biology and Life Sciences', None, 'Science Building', '555-0206', 2200000, 1987),
                ('History', 'HIST', 'History and Social Studies', None, 'Liberal Arts Building', '555-0207', 1100000, 1983),
                ('Physics', 'PHYS', 'Physics and Astronomy', None, 'Physics Building', '555-0208', 1900000, 1989),
                ('Chemistry', 'CHEM', 'Chemistry and Chemical Engineering', None, 'Chemistry Building', '555-0209', 2100000, 1991),
                ('Art', 'ART', 'Fine Arts and Visual Design', None, 'Arts Center', '555-0210', 1300000, 1994)
            ]
            
            cursor.executemany(
                "INSERT INTO departments (dept_name, dept_code, description, head_instructor_id, building, phone, budget, established_year, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)",
                departments_data
            )
            
            # Generate instructors
            instructor_titles = ['Professor', 'Associate Professor', 'Assistant Professor', 'Lecturer', 'Adjunct Professor']
            education_levels = ['PhD', 'Masters', 'EdD', 'JD']
            
            instructors_data = []
            for i in range(120):
                dept_id = random.randint(1, 10)
                employee_id = f"EMP{i+1:05d}"
                title = random.choice(instructor_titles)
                education = random.choice(education_levels)
                
                # Get department name for specialization
                cursor.execute("SELECT dept_name FROM departments WHERE dept_id = %s", (dept_id,))
                dept_name = cursor.fetchone()[0]
                
                specializations = {
                    'Computer Science': ['Software Engineering', 'Data Science', 'AI/Machine Learning', 'Cybersecurity', 'Web Development'],
                    'Mathematics': ['Calculus', 'Statistics', 'Linear Algebra', 'Applied Mathematics', 'Pure Mathematics'],
                    'English': ['Literature', 'Creative Writing', 'Composition', 'Linguistics', 'British Literature'],
                    'Business': ['Marketing', 'Finance', 'Management', 'Accounting', 'International Business'],
                    'Psychology': ['Clinical Psychology', 'Cognitive Psychology', 'Social Psychology', 'Developmental Psychology'],
                    'Biology': ['Molecular Biology', 'Ecology', 'Genetics', 'Microbiology', 'Marine Biology'],
                    'History': ['American History', 'World History', 'European History', 'Ancient History', 'Modern History'],
                    'Physics': ['Quantum Physics', 'Astrophysics', 'Nuclear Physics', 'Applied Physics', 'Theoretical Physics'],
                    'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Biochemistry'],
                    'Art': ['Painting', 'Sculpture', 'Digital Art', 'Art History', 'Graphic Design']
                }
                
                specialization = random.choice(specializations.get(dept_name, ['General']))
                salary = random.randint(45000, 120000)
                hire_date = fake.date_between(start_date='-15y', end_date='today')
                
                instructors_data.append((
                    employee_id, fake.first_name(), fake.last_name(), f"{fake.user_name()}{i}@{fake.domain_name()}",
                    fake.phone_number(), title, dept_id, f"Room {random.randint(100, 999)}",
                    education, specialization, hire_date, salary, True
                ))
            
            cursor.executemany(
                "INSERT INTO instructors (employee_id, first_name, last_name, email, phone, title, dept_id, office_location, education_level, specialization, hire_date, salary, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                instructors_data
            )
            
            # Generate students
            majors = [
                'Computer Science', 'Mathematics', 'English Literature', 'Business Administration',
                'Psychology', 'Biology', 'History', 'Physics', 'Chemistry', 'Fine Arts',
                'Engineering', 'Pre-Med', 'Economics', 'Political Science', 'Sociology'
            ]
            
            minors = [
                'Mathematics', 'Computer Science', 'English', 'Business', 'Psychology',
                'Art', 'Music', 'Philosophy', 'Statistics', 'Communications'
            ]
            
            year_levels = ['Freshman', 'Sophomore', 'Junior', 'Senior', 'Graduate']
            
            students_data = []
            for i in range(2500):
                student_number = f"STU{i+1:06d}"
                birth_date = fake.date_of_birth(minimum_age=17, maximum_age=35)
                gender = random.choice(['Male', 'Female', 'Other'])
                major = random.choice(majors)
                minor = random.choice(minors + [None, None, None])  # Some students don't have minors
                year_level = random.choice(year_levels)
                enrollment_date = fake.date_between(start_date='-6y', end_date='today')
                
                # Generate realistic GPA and credits based on year level
                if year_level == 'Freshman':
                    credits = random.randint(0, 30)
                    gpa = round(random.uniform(2.0, 4.0), 2)
                elif year_level == 'Sophomore':
                    credits = random.randint(25, 60)
                    gpa = round(random.uniform(2.2, 4.0), 2)
                elif year_level == 'Junior':
                    credits = random.randint(55, 90)
                    gpa = round(random.uniform(2.3, 4.0), 2)
                elif year_level == 'Senior':
                    credits = random.randint(85, 120)
                    gpa = round(random.uniform(2.4, 4.0), 2)
                else:  # Graduate
                    credits = random.randint(120, 180)
                    gpa = round(random.uniform(3.0, 4.0), 2)
                
                graduation_date = None
                if year_level == 'Senior' and random.random() > 0.7:
                    graduation_date = fake.future_date(end_date='+1y')
                
                students_data.append((
                    student_number, fake.first_name(), fake.last_name(), f"{fake.user_name()}{i}@{fake.domain_name()}",
                    fake.phone_number(), birth_date, gender, fake.address(),
                    fake.city(), fake.state(), fake.zipcode(), major, minor,
                    year_level, enrollment_date, graduation_date, gpa, credits, True
                ))
            
            cursor.executemany(
                "INSERT INTO students (student_number, first_name, last_name, email, phone, date_of_birth, gender, address, city, state, zip_code, major, minor, year_level, enrollment_date, graduation_date, gpa, credits_completed, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                students_data
            )
            
            # Generate courses
            course_templates = {
                1: [  # Computer Science
                    ('CS101', 'Introduction to Programming', 'Basic programming concepts in Python', 3),
                    ('CS102', 'Data Structures', 'Arrays, lists, stacks, queues, trees', 3),
                    ('CS201', 'Algorithms', 'Algorithm design and analysis', 3),
                    ('CS301', 'Database Systems', 'Relational databases and SQL', 3),
                    ('CS401', 'Software Engineering', 'Large-scale software development', 3),
                    ('CS405', 'Machine Learning', 'Introduction to ML algorithms', 3)
                ],
                2: [  # Mathematics
                    ('MATH101', 'College Algebra', 'Algebraic functions and equations', 3),
                    ('MATH102', 'Trigonometry', 'Trigonometric functions', 3),
                    ('MATH201', 'Calculus I', 'Differential calculus', 4),
                    ('MATH202', 'Calculus II', 'Integral calculus', 4),
                    ('MATH301', 'Linear Algebra', 'Matrix operations and vector spaces', 3),
                    ('MATH401', 'Statistics', 'Probability and statistical inference', 3)
                ],
                3: [  # English
                    ('ENG101', 'English Composition', 'Academic writing skills', 3),
                    ('ENG102', 'Literature Survey', 'Introduction to world literature', 3),
                    ('ENG201', 'American Literature', 'American authors and themes', 3),
                    ('ENG301', 'Shakespeare', 'Works of William Shakespeare', 3),
                    ('ENG401', 'Creative Writing', 'Fiction and poetry writing', 3)
                ],
                4: [  # Business
                    ('BUS101', 'Introduction to Business', 'Business fundamentals', 3),
                    ('BUS201', 'Marketing Principles', 'Marketing strategies and concepts', 3),
                    ('BUS301', 'Financial Management', 'Corporate finance principles', 3),
                    ('BUS401', 'Strategic Management', 'Business strategy formulation', 3),
                    ('BUS405', 'International Business', 'Global business operations', 3)
                ]
            }
            
            courses_data = []
            for dept_id in range(1, 11):
                if dept_id in course_templates:
                    for course_code, name, desc, credits in course_templates[dept_id]:
                        max_enrollment = random.randint(20, 50)
                        difficulty = random.choice(['Beginner', 'Intermediate', 'Advanced'])
                        courses_data.append((course_code, name, desc, dept_id, credits, max_enrollment, None, difficulty, True))
                else:
                    # Generate generic courses for other departments
                    for i in range(5):
                        cursor.execute("SELECT dept_code FROM departments WHERE dept_id = %s", (dept_id,))
                        dept_code = cursor.fetchone()[0]
                        course_code = f"{dept_code}{random.randint(101, 499)}"
                        name = f"{fake.catch_phrase()} {random.choice(['Fundamentals', 'Principles', 'Advanced Topics', 'Survey', 'Methods'])}"
                        desc = fake.text(max_nb_chars=200)
                        credits = random.choice([3, 3, 3, 4, 4, 1, 2])
                        max_enrollment = random.randint(15, 40)
                        difficulty = random.choice(['Beginner', 'Intermediate', 'Advanced'])
                        courses_data.append((course_code, name, desc, dept_id, credits, max_enrollment, None, difficulty, True))
            
            cursor.executemany(
                "INSERT INTO courses (course_code, course_name, description, dept_id, credits, max_enrollment, prerequisite_course_id, difficulty_level, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                courses_data
            )
            
            # Generate enrollments
            semesters = ['Fall', 'Spring', 'Summer']
            years = [2021, 2022, 2023, 2024, 2025]
            
            for i in range(8000):
                student_id = random.randint(1, 2500)
                course_id = random.randint(1, len(courses_data))
                instructor_id = random.randint(1, 120)
                semester = random.choice(semesters)
                year = random.choice(years)
                enrollment_date = fake.date_between(start_date='-2y', end_date='today')
                
                status = random.choices(
                    ['Enrolled', 'Completed', 'Dropped', 'Withdrawn'],
                    weights=[20, 70, 7, 3]
                )[0]
                
                if status == 'Completed':
                    grade = random.choices(
                        ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F'],
                        weights=[15, 10, 15, 15, 10, 10, 10, 8, 3, 2, 2]
                    )[0]
                    final_score = random.uniform(60, 100) if grade != 'F' else random.uniform(0, 59)
                else:
                    grade = None
                    final_score = None
                
                try:
                    cursor.execute(
                        "INSERT INTO enrollments (student_id, course_id, instructor_id, semester, year, enrollment_date, grade, status, final_score) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (student_id, course_id, instructor_id, semester, year, enrollment_date, grade, status, final_score)
                    )
                except:
                    # Skip duplicate enrollments
                    continue
            
            conn.commit()
            print(f"SUCCESS: EduLearn: Created {len(departments_data)} departments, {len(instructors_data)} instructors, {len(students_data)} students, {len(courses_data)} courses, ~8000 enrollments")
            
        except Exception as e:
            print(f"FAILED: EduLearn data generation failed: {e}")

    def run_all(self):
        """Generate data for all organizations"""
        print("Starting realistic fake data generation for all organizations...")
        print("=" * 80)
        
        self.generate_techcorp_data()
        print()
        
        self.generate_healthplus_data()
        print()
        
        self.generate_financehub_data()
        print()
        
        self.generate_retailmax_data()
        print()
        
        self.generate_edulearn_data()
        print()
        
        print("=" * 80)
        print("Completed: Data generation completed for all organizations!")

if __name__ == "__main__":
    generator = DataGenerator()
    generator.run_all()