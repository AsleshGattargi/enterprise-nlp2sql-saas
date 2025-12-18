"""
Standalone Streamlit App for Multi-Tenant NLP2SQL
Works without backend server - reads from SQLite databases.
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any
import sqlite3
from pathlib import Path

# Configure Streamlit page
st.set_page_config(
    page_title="Multi-Tenant NLP2SQL Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_tenant' not in st.session_state:
    st.session_state.current_tenant = "demo_tenant"
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

# Role-based permissions configuration
ROLE_PERMISSIONS = {
    "admin": {
        "queries": ["all"],
        "features": ["user_management", "system_metrics", "error_logs", "analytics", "data_export", "modify_data"],
        "description": "Full system access"
    },
    "analyst": {
        "queries": ["read", "analytics"],
        "features": ["analytics", "data_export"],
        "restricted": ["user_management", "system_metrics", "error_logs", "modify_data"],
        "description": "Data analysis and reporting"
    },
    "user": {
        "queries": ["read"],
        "features": ["basic_queries"],
        "restricted": ["user_management", "system_metrics", "error_logs", "analytics", "modify_data"],
        "description": "Basic data access"
    },
    "viewer": {
        "queries": ["read"],
        "features": [],
        "restricted": ["user_management", "system_metrics", "error_logs", "analytics", "modify_data", "data_export"],
        "description": "Read-only access"
    }
}

# Restricted query patterns by role
RESTRICTED_QUERIES = {
    "system_metrics": ["system performance", "performance metrics", "system health", "server status"],
    "user_management": ["all users", "active users", "user list", "delete user", "create user", "modify user"],
    "error_logs": ["error log", "system log", "debug log", "exception log"],
    "modify_data": ["delete", "drop", "truncate", "update", "insert", "alter", "modify"],
    "advanced_analytics": ["machine learning", "predictive", "forecast", "trend analysis"]
}

# Mock data
MOCK_USERS = {
    "admin@techcorp.com": {
        "password": "admin123",
        "user_id": "user_001",
        "username": "admin",
        "email": "admin@techcorp.com",
        "full_name": "Admin User",
        "role": "admin",
        "org_id": "techcorp",
        "org_name": "TechCorp Solutions"
    },
    "analyst@techcorp.com": {
        "password": "analyst123",
        "user_id": "user_002",
        "username": "analyst",
        "email": "analyst@techcorp.com",
        "full_name": "Data Analyst",
        "role": "analyst",
        "org_id": "techcorp",
        "org_name": "TechCorp Solutions"
    },
    "user@healthplus.com": {
        "password": "user123",
        "user_id": "user_003",
        "username": "user",
        "email": "user@healthplus.com",
        "full_name": "Regular User",
        "role": "user",
        "org_id": "healthplus",
        "org_name": "HealthPlus Medical"
    }
}

# Tenant-specific data for proper isolation demonstration
TENANT_DATA = {
    "techcorp": {
        "show me all products": {
            "sql": "SELECT product_id, name, price, category, stock FROM products ORDER BY price DESC",
            "data": [
                {"product_id": 1, "name": "Machine Learning Platform", "price": 1299.99, "category": "AI/ML", "stock": 25},
                {"product_id": 2, "name": "Enterprise Software License", "price": 999.99, "category": "Software", "stock": 50},
                {"product_id": 3, "name": "Data Warehouse Service", "price": 899.99, "category": "Analytics", "stock": 35},
                {"product_id": 4, "name": "Database Management System", "price": 799.99, "category": "Infrastructure", "stock": 40},
                {"product_id": 5, "name": "Data Analytics Suite", "price": 599.99, "category": "Analytics", "stock": 30},
                {"product_id": 6, "name": "CRM Software", "price": 599.99, "category": "Sales", "stock": 55},
                {"product_id": 7, "name": "Container Orchestration", "price": 549.99, "category": "Infrastructure", "stock": 45},
                {"product_id": 8, "name": "CI/CD Pipeline Tool", "price": 449.99, "category": "DevOps", "stock": 60},
                {"product_id": 9, "name": "Identity Management", "price": 399.99, "category": "Security", "stock": 65},
                {"product_id": 10, "name": "Security Scanner Pro", "price": 349.99, "category": "Security", "stock": 80},
                {"product_id": 11, "name": "Cloud Server Instance", "price": 299.99, "category": "Infrastructure", "stock": 100},
                {"product_id": 12, "name": "API Gateway", "price": 299.99, "category": "Development", "stock": 70},
                {"product_id": 13, "name": "Monitoring Dashboard", "price": 249.99, "category": "Analytics", "stock": 90},
                {"product_id": 14, "name": "Load Balancer Service", "price": 199.99, "category": "Infrastructure", "stock": 120},
                {"product_id": 15, "name": "Backup Solution Pro", "price": 179.99, "category": "Infrastructure", "stock": 150},
                {"product_id": 16, "name": "API Development Kit", "price": 149.99, "category": "Development", "stock": 75},
                {"product_id": 17, "name": "Email Marketing Suite", "price": 149.99, "category": "Marketing", "stock": 100},
                {"product_id": 18, "name": "Code Repository License", "price": 99.99, "category": "Development", "stock": 200},
                {"product_id": 19, "name": "Project Management Tool", "price": 99.99, "category": "Productivity", "stock": 180},
                {"product_id": 20, "name": "Documentation Portal", "price": 79.99, "category": "Productivity", "stock": 220}
            ]
        },
        "how many users": {
            "sql": "SELECT COUNT(*) as total_users FROM users",
            "data": [{"total_users": 15}]
        },
        "top customers": {
            "sql": "SELECT customer_name, total_orders, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5",
            "data": [
                {"customer_name": "Microsoft Corp", "total_orders": 45, "total_spent": 125678.90},
                {"customer_name": "Google LLC", "total_orders": 32, "total_spent": 98456.78},
                {"customer_name": "Amazon Web Services", "total_orders": 28, "total_spent": 87654.32},
                {"customer_name": "Oracle Corporation", "total_orders": 21, "total_spent": 76543.21},
                {"customer_name": "IBM Technologies", "total_orders": 19, "total_spent": 65432.10}
            ]
        },
        "system performance": {
            "sql": "SELECT metric_name, current_value, status, last_updated FROM system_metrics ORDER BY metric_name",
            "data": [
                {"metric_name": "CPU Usage", "current_value": "45%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Memory Usage", "current_value": "62%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Database Connections", "current_value": "127", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Query Response Time", "current_value": "85ms", "status": "Good", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Active Users", "current_value": "15", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Disk Usage", "current_value": "38%", "status": "Good", "last_updated": "2025-01-13 10:30:00"}
            ]
        },
        "all users": {
            "sql": "SELECT user_id, username, email, role, department, status FROM users ORDER BY username",
            "data": [
                {"user_id": 1, "username": "admin", "email": "admin@techcorp.com", "role": "admin", "department": "IT", "status": "Active"},
                {"user_id": 2, "username": "analyst1", "email": "analyst@techcorp.com", "role": "analyst", "department": "Data Analytics", "status": "Active"},
                {"user_id": 3, "username": "developer1", "email": "dev1@techcorp.com", "role": "user", "department": "Engineering", "status": "Active"},
                {"user_id": 4, "username": "developer2", "email": "dev2@techcorp.com", "role": "user", "department": "Engineering", "status": "Active"},
                {"user_id": 5, "username": "sales_user", "email": "sales@techcorp.com", "role": "user", "department": "Sales", "status": "Active"},
                {"user_id": 6, "username": "viewer1", "email": "viewer@techcorp.com", "role": "viewer", "department": "Marketing", "status": "Active"}
            ]
        },
        "active users": {
            "sql": "SELECT user_id, username, email, role, last_login FROM users WHERE status = 'Active' ORDER BY last_login DESC",
            "data": [
                {"user_id": 1, "username": "admin", "email": "admin@techcorp.com", "role": "admin", "last_login": "2025-01-13 10:15:00"},
                {"user_id": 2, "username": "analyst1", "email": "analyst@techcorp.com", "role": "analyst", "last_login": "2025-01-13 09:45:00"},
                {"user_id": 3, "username": "developer1", "email": "dev1@techcorp.com", "role": "user", "last_login": "2025-01-13 09:30:00"},
                {"user_id": 4, "username": "developer2", "email": "dev2@techcorp.com", "role": "user", "last_login": "2025-01-13 08:20:00"},
                {"user_id": 5, "username": "sales_user", "email": "sales@techcorp.com", "role": "user", "last_login": "2025-01-12 16:45:00"}
            ]
        },
        "error log": {
            "sql": "SELECT log_id, timestamp, error_level, error_message, user_id FROM error_logs ORDER BY timestamp DESC LIMIT 10",
            "data": [
                {"log_id": 1, "timestamp": "2025-01-13 10:25:00", "error_level": "WARNING", "error_message": "Slow query detected: 2.5s execution time", "user_id": 3},
                {"log_id": 2, "timestamp": "2025-01-13 10:18:00", "error_level": "INFO", "error_message": "Database backup completed successfully", "user_id": None},
                {"log_id": 3, "timestamp": "2025-01-13 09:55:00", "error_level": "ERROR", "error_message": "Failed login attempt from IP 192.168.1.45", "user_id": None},
                {"log_id": 4, "timestamp": "2025-01-13 09:30:00", "error_level": "WARNING", "error_message": "High memory usage detected: 85%", "user_id": None},
                {"log_id": 5, "timestamp": "2025-01-13 09:15:00", "error_level": "INFO", "error_message": "System health check passed", "user_id": None},
                {"log_id": 6, "timestamp": "2025-01-13 08:45:00", "error_level": "ERROR", "error_message": "Connection timeout to external API", "user_id": 5}
            ]
        }
    },
    "healthplus": {
        "show me all products": {
            "sql": "SELECT product_id, name, price, category, stock FROM products ORDER BY price DESC",
            "data": [
                {"product_id": 1, "name": "Minor Surgery", "price": 850.00, "category": "Surgery", "stock": 50},
                {"product_id": 2, "name": "MRI Scan", "price": 450.00, "category": "Radiology", "stock": 100},
                {"product_id": 3, "name": "CT Scan", "price": 350.00, "category": "Radiology", "stock": 150},
                {"product_id": 4, "name": "Emergency Visit", "price": 275.00, "category": "Emergency", "stock": 500},
                {"product_id": 5, "name": "Stress Test", "price": 225.00, "category": "Cardiology", "stock": 120},
                {"product_id": 6, "name": "X-Ray Examination", "price": 200.00, "category": "Radiology", "stock": 200},
                {"product_id": 7, "name": "Specialist Referral", "price": 200.00, "category": "Medical Service", "stock": 400},
                {"product_id": 8, "name": "Ultrasound", "price": 180.00, "category": "Radiology", "stock": 250},
                {"product_id": 9, "name": "Annual Physical", "price": 175.00, "category": "Preventive Care", "stock": 600},
                {"product_id": 10, "name": "Dermatology Consult", "price": 165.00, "category": "Specialty", "stock": 200},
                {"product_id": 11, "name": "General Consultation", "price": 150.00, "category": "Medical Service", "stock": 1000},
                {"product_id": 12, "name": "Allergy Test", "price": 135.00, "category": "Laboratory", "stock": 180},
                {"product_id": 13, "name": "Dental Cleaning", "price": 125.00, "category": "Dental", "stock": 350},
                {"product_id": 14, "name": "Physical Therapy Session", "price": 120.00, "category": "Therapy", "stock": 300},
                {"product_id": 15, "name": "Lab Work Panel", "price": 115.00, "category": "Laboratory", "stock": 450},
                {"product_id": 16, "name": "Eye Examination", "price": 110.00, "category": "Ophthalmology", "stock": 280},
                {"product_id": 17, "name": "ECG Test", "price": 95.00, "category": "Cardiology", "stock": 400},
                {"product_id": 18, "name": "Blood Test Panel", "price": 85.00, "category": "Laboratory", "stock": 500},
                {"product_id": 19, "name": "Vaccination", "price": 45.00, "category": "Preventive Care", "stock": 800},
                {"product_id": 20, "name": "Flu Shot", "price": 35.00, "category": "Preventive Care", "stock": 1000}
            ]
        },
        "how many users": {
            "sql": "SELECT COUNT(*) as total_users FROM users",
            "data": [{"total_users": 8}]
        },
        "top customers": {
            "sql": "SELECT customer_name, total_orders, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5",
            "data": [
                {"customer_name": "City General Hospital", "total_orders": 245, "total_spent": 45678.90},
                {"customer_name": "Regional Medical Center", "total_orders": 189, "total_spent": 38456.78},
                {"customer_name": "Community Health Clinic", "total_orders": 156, "total_spent": 29876.54},
                {"customer_name": "Pediatric Care Center", "total_orders": 134, "total_spent": 25765.43},
                {"customer_name": "Senior Care Facility", "total_orders": 98, "total_spent": 18654.32}
            ]
        },
        "system performance": {
            "sql": "SELECT metric_name, current_value, status, last_updated FROM system_metrics ORDER BY metric_name",
            "data": [
                {"metric_name": "CPU Usage", "current_value": "38%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Memory Usage", "current_value": "55%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Database Connections", "current_value": "89", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Query Response Time", "current_value": "92ms", "status": "Good", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Active Users", "current_value": "8", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
                {"metric_name": "Disk Usage", "current_value": "42%", "status": "Good", "last_updated": "2025-01-13 10:30:00"}
            ]
        },
        "all users": {
            "sql": "SELECT user_id, username, email, role, department, status FROM users ORDER BY username",
            "data": [
                {"user_id": 1, "username": "dr_wilson", "email": "user@healthplus.com", "role": "user", "department": "Emergency", "status": "Active"},
                {"user_id": 2, "username": "nurse_martinez", "email": "nurse@healthplus.com", "role": "user", "department": "Nursing", "status": "Active"},
                {"user_id": 3, "username": "admin_health", "email": "admin@healthplus.com", "role": "admin", "department": "IT", "status": "Active"},
                {"user_id": 4, "username": "receptionist", "email": "reception@healthplus.com", "role": "viewer", "department": "Front Desk", "status": "Active"}
            ]
        },
        "active users": {
            "sql": "SELECT user_id, username, email, role, last_login FROM users WHERE status = 'Active' ORDER BY last_login DESC",
            "data": [
                {"user_id": 1, "username": "dr_wilson", "email": "user@healthplus.com", "role": "user", "last_login": "2025-01-13 10:20:00"},
                {"user_id": 2, "username": "nurse_martinez", "email": "nurse@healthplus.com", "role": "user", "last_login": "2025-01-13 09:50:00"},
                {"user_id": 3, "username": "admin_health", "email": "admin@healthplus.com", "role": "admin", "last_login": "2025-01-13 08:30:00"}
            ]
        },
        "error log": {
            "sql": "SELECT log_id, timestamp, error_level, error_message, user_id FROM error_logs ORDER BY timestamp DESC LIMIT 10",
            "data": [
                {"log_id": 1, "timestamp": "2025-01-13 10:22:00", "error_level": "INFO", "error_message": "Patient record updated successfully", "user_id": 1},
                {"log_id": 2, "timestamp": "2025-01-13 10:15:00", "error_level": "WARNING", "error_message": "Appointment system slow response", "user_id": None},
                {"log_id": 3, "timestamp": "2025-01-13 09:45:00", "error_level": "INFO", "error_message": "Database backup completed", "user_id": None},
                {"log_id": 4, "timestamp": "2025-01-13 09:30:00", "error_level": "ERROR", "error_message": "Failed to send appointment reminder", "user_id": None}
            ]
        }
    }
}

# Fallback for generic queries (backward compatibility)
MOCK_QUERIES = {
    "show me all products": {
        "sql": "SELECT product_id, name, price, category, stock FROM products ORDER BY name",
        "data": [
            {"product_id": 1, "name": "Generic Product", "price": 99.99, "category": "General", "stock": 100}
        ]
    },
    "how many users": {
        "sql": "SELECT COUNT(*) as total_users FROM users",
        "data": [{"total_users": 1247}]
    },
    "top customers": {
        "sql": "SELECT customer_name, total_orders, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5",
        "data": [
            {"customer_name": "Acme Corp", "total_orders": 45, "total_spent": 15678.90},
            {"customer_name": "Tech Solutions Inc", "total_orders": 32, "total_spent": 12456.78},
            {"customer_name": "Global Systems", "total_orders": 28, "total_spent": 9876.54},
            {"customer_name": "Innovation Labs", "total_orders": 21, "total_spent": 8765.43},
            {"customer_name": "Digital Dynamics", "total_orders": 19, "total_spent": 7654.32}
        ]
    },
    "average order value": {
        "sql": "SELECT AVG(order_total) as avg_order_value, COUNT(*) as total_orders FROM orders",
        "data": [{"avg_order_value": 156.78, "total_orders": 3245}]
    },
    "sales last month": {
        "sql": "SELECT SUM(order_total) as total_sales, COUNT(*) as order_count FROM orders WHERE order_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)",
        "data": [{"total_sales": 458923.45, "order_count": 1234}]
    },
    "inventory levels": {
        "sql": "SELECT warehouse, product_category, SUM(quantity) as total_quantity FROM inventory GROUP BY warehouse, product_category",
        "data": [
            {"warehouse": "Main Warehouse", "product_category": "Electronics", "total_quantity": 1250},
            {"warehouse": "Main Warehouse", "product_category": "Office Supplies", "total_quantity": 890},
            {"warehouse": "Secondary Warehouse", "product_category": "Electronics", "total_quantity": 670},
            {"warehouse": "Secondary Warehouse", "product_category": "Office Supplies", "total_quantity": 445}
        ]
    },
    "monthly revenue": {
        "sql": "SELECT DATE_FORMAT(order_date, '%Y-%m') as month, SUM(order_total) as revenue FROM orders GROUP BY month ORDER BY month DESC LIMIT 6",
        "data": [
            {"month": "2024-09", "revenue": 458923.45},
            {"month": "2024-08", "revenue": 423156.78},
            {"month": "2024-07", "revenue": 398765.43},
            {"month": "2024-06", "revenue": 445678.90},
            {"month": "2024-05", "revenue": 412345.67},
            {"month": "2024-04", "revenue": 387654.32}
        ]
    },
    "system performance": {
        "sql": "SELECT metric_name, current_value, status, last_updated FROM system_metrics ORDER BY metric_name",
        "data": [
            {"metric_name": "CPU Usage", "current_value": "52%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
            {"metric_name": "Memory Usage", "current_value": "68%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
            {"metric_name": "Database Connections", "current_value": "215", "status": "High", "last_updated": "2025-01-13 10:30:00"},
            {"metric_name": "Query Response Time", "current_value": "105ms", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
            {"metric_name": "Active Users", "current_value": "23", "status": "Normal", "last_updated": "2025-01-13 10:30:00"},
            {"metric_name": "Disk Usage", "current_value": "65%", "status": "Normal", "last_updated": "2025-01-13 10:30:00"}
        ]
    },
    "all users": {
        "sql": "SELECT user_id, username, email, role, department, status FROM users ORDER BY username",
        "data": [
            {"user_id": 1, "username": "admin", "email": "admin@company.com", "role": "admin", "department": "IT", "status": "Active"},
            {"user_id": 2, "username": "analyst1", "email": "analyst@company.com", "role": "analyst", "department": "Analytics", "status": "Active"},
            {"user_id": 3, "username": "user1", "email": "user1@company.com", "role": "user", "department": "Sales", "status": "Active"},
            {"user_id": 4, "username": "user2", "email": "user2@company.com", "role": "user", "department": "Marketing", "status": "Active"},
            {"user_id": 5, "username": "viewer1", "email": "viewer@company.com", "role": "viewer", "department": "Support", "status": "Active"}
        ]
    },
    "active users": {
        "sql": "SELECT user_id, username, email, role, last_login FROM users WHERE status = 'Active' ORDER BY last_login DESC",
        "data": [
            {"user_id": 1, "username": "admin", "email": "admin@company.com", "role": "admin", "last_login": "2025-01-13 10:25:00"},
            {"user_id": 2, "username": "analyst1", "email": "analyst@company.com", "role": "analyst", "last_login": "2025-01-13 10:10:00"},
            {"user_id": 3, "username": "user1", "email": "user1@company.com", "role": "user", "last_login": "2025-01-13 09:55:00"},
            {"user_id": 4, "username": "user2", "email": "user2@company.com", "role": "user", "last_login": "2025-01-13 09:30:00"}
        ]
    },
    "error log": {
        "sql": "SELECT log_id, timestamp, error_level, error_message, user_id FROM error_logs ORDER BY timestamp DESC LIMIT 10",
        "data": [
            {"log_id": 1, "timestamp": "2025-01-13 10:28:00", "error_level": "ERROR", "error_message": "Database connection timeout", "user_id": None},
            {"log_id": 2, "timestamp": "2025-01-13 10:20:00", "error_level": "WARNING", "error_message": "High memory usage detected: 88%", "user_id": None},
            {"log_id": 3, "timestamp": "2025-01-13 10:15:00", "error_level": "INFO", "error_message": "Scheduled maintenance completed", "user_id": None},
            {"log_id": 4, "timestamp": "2025-01-13 10:05:00", "error_level": "ERROR", "error_message": "Failed API request to external service", "user_id": 3},
            {"log_id": 5, "timestamp": "2025-01-13 09:50:00", "error_level": "WARNING", "error_message": "Slow query detected: 3.2s", "user_id": 2},
            {"log_id": 6, "timestamp": "2025-01-13 09:30:00", "error_level": "INFO", "error_message": "System health check passed", "user_id": None}
        ]
    }
}

def authenticate_user(email: str, password: str) -> Dict:
    """Authenticate user with mock data."""
    if email in MOCK_USERS and MOCK_USERS[email]["password"] == password:
        user = MOCK_USERS[email].copy()
        del user["password"]  # Don't return password
        return {"success": True, "user": user, "access_token": "mock_token_" + user["user_id"]}
    return {"success": False, "error": "Invalid credentials"}

def check_query_permission(query_text: str, user_role: str) -> Dict:
    """Check if user has permission to execute the query."""
    query_lower = query_text.lower().strip()

    # Admin has access to everything
    if user_role == "admin":
        return {"allowed": True, "reason": None}

    # Get role permissions
    role_perms = ROLE_PERMISSIONS.get(user_role, {})
    restricted_features = role_perms.get("restricted", [])

    # Check against restricted query patterns
    for feature_type, patterns in RESTRICTED_QUERIES.items():
        if feature_type in restricted_features:
            for pattern in patterns:
                if pattern in query_lower:
                    # Generate appropriate error message
                    messages = {
                        "system_metrics": {
                            "title": "System Metrics Access Denied",
                            "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to access system performance metrics.",
                            "suggestion": "System metrics are restricted to administrators only. Please contact your system administrator if you need this access.",
                            "required_role": "Admin"
                        },
                        "user_management": {
                            "title": "User Management Access Denied",
                            "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to access user management data.",
                            "suggestion": "User management features are restricted to administrators. You can only view your own user profile.",
                            "required_role": "Admin"
                        },
                        "error_logs": {
                            "title": "System Logs Access Denied",
                            "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to access system logs.",
                            "suggestion": "Error logs and system logs are restricted to administrators for security purposes.",
                            "required_role": "Admin"
                        },
                        "modify_data": {
                            "title": "Data Modification Denied",
                            "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to modify data.",
                            "suggestion": "Data modification operations (DELETE, UPDATE, INSERT) are restricted to administrators only.",
                            "required_role": "Admin"
                        },
                        "advanced_analytics": {
                            "title": "Advanced Analytics Access Denied",
                            "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to run advanced analytics queries.",
                            "suggestion": "Advanced analytics features are restricted to Analyst and Admin roles.",
                            "required_role": "Analyst or Admin"
                        }
                    }

                    error_info = messages.get(feature_type, {
                        "title": "Access Denied",
                        "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) does not have permission to execute this query.",
                        "suggestion": "This operation is restricted based on your role permissions.",
                        "required_role": "Higher privileges required"
                    })

                    return {
                        "allowed": False,
                        "feature_type": feature_type,
                        "matched_pattern": pattern,
                        **error_info
                    }

    # Check for analyst-only features
    if user_role == "user" or user_role == "viewer":
        # User role can only do basic product/service queries
        restricted_user_patterns = [
            "customer", "top", "sales", "revenue", "order",
            "analytics", "aggregate", "group by", "average",
            "sum", "count", "expensive", "category"
        ]
        for pattern in restricted_user_patterns:
            if pattern in query_lower:
                return {
                    "allowed": False,
                    "feature_type": "analytics_or_customer_data",
                    "title": "Limited Access - User Role",
                    "message": f"🚫 **Access Denied**: Your role ({user_role.title()}) can only view basic product/service information.",
                    "suggestion": "User role is limited to simple product queries like 'Show me all products' or 'Show products under $100'. Customer data, analytics, and order information require Analyst or Admin role.",
                    "required_role": "Analyst or Admin",
                    "matched_pattern": pattern
                }

    return {"allowed": True, "reason": None}

def get_database_path(tenant_id: str) -> Path:
    """Get the database file path for a tenant."""
    db_map = {
        "techcorp": "demo_databases/techcorp_db.sqlite",
        "healthplus": "demo_databases/healthplus_db.sqlite"
    }
    db_path = Path(db_map.get(tenant_id, "demo_databases/techcorp_db.sqlite"))

    if not db_path.exists():
        st.error(f"Database not found: {db_path}. Please run 'python demo_simple.py' first.")
        return None

    return db_path

def execute_database_query(sql: str, tenant_id: str) -> List[Dict]:
    """Execute SQL query on tenant's database."""
    db_path = get_database_path(tenant_id)
    if not db_path:
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)

        # Convert rows to list of dictionaries
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        conn.close()
        return results
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return []

def generate_sql_from_nl(query_text: str, tenant_id: str) -> str:
    """Generate SQL from natural language query."""
    query_lower = query_text.lower().strip()

    # Map common queries to SQL
    if "show" in query_lower or "service" in query_lower or "product" in query_lower:
        # Handle price filtering
        if "under" in query_lower or "less than" in query_lower or "below" in query_lower:
            # Extract price value
            import re
            price_match = re.search(r'\$?(\d+)', query_lower)
            if price_match:
                price = price_match.group(1)
                return f"SELECT name, price, category, stock_quantity FROM products WHERE price < {price} ORDER BY price DESC"
        elif "over" in query_lower or "more than" in query_lower or "above" in query_lower:
            import re
            price_match = re.search(r'\$?(\d+)', query_lower)
            if price_match:
                price = price_match.group(1)
                return f"SELECT name, price, category, stock_quantity FROM products WHERE price > {price} ORDER BY price DESC"
        elif "expensive" in query_lower:
            return "SELECT name, price, category, stock_quantity FROM products ORDER BY price DESC LIMIT 10"
        elif "all" in query_lower:
            return "SELECT * FROM products ORDER BY price DESC"
        else:
            return "SELECT * FROM products ORDER BY name LIMIT 20"

    elif "user" in query_lower:
        if "count" in query_lower or "how many" in query_lower:
            return "SELECT COUNT(*) as total_users FROM users"
        elif "all" in query_lower or "list" in query_lower:
            return "SELECT username, full_name, role, department FROM users ORDER BY username"
        elif "department" in query_lower:
            return "SELECT department, COUNT(*) as count FROM users GROUP BY department ORDER BY count DESC"
        else:
            return "SELECT * FROM users LIMIT 20"

    elif "customer" in query_lower:
        if "top" in query_lower:
            return "SELECT customer_name, total_orders, total_spent FROM customers ORDER BY total_spent DESC LIMIT 10"
        elif "all" in query_lower:
            return "SELECT * FROM customers ORDER BY customer_name"
        else:
            return "SELECT customer_name, total_orders, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5"

    elif "order" in query_lower:
        if "recent" in query_lower or "latest" in query_lower:
            return "SELECT * FROM orders ORDER BY order_date DESC LIMIT 10"
        elif "pending" in query_lower:
            return "SELECT * FROM orders WHERE status = 'pending' ORDER BY order_date DESC"
        elif "completed" in query_lower:
            return "SELECT * FROM orders WHERE status = 'completed' ORDER BY order_date DESC LIMIT 10"
        else:
            return "SELECT * FROM orders ORDER BY order_date DESC LIMIT 20"

    elif "category" in query_lower or "categories" in query_lower:
        return "SELECT category, COUNT(*) as count FROM products GROUP BY category ORDER BY count DESC"

    elif "price" in query_lower and ("average" in query_lower or "avg" in query_lower):
        return "SELECT category, AVG(price) as avg_price, COUNT(*) as count FROM products GROUP BY category ORDER BY avg_price DESC"

    elif "stock" in query_lower or "inventory" in query_lower:
        return "SELECT name, category, stock_quantity, price FROM products ORDER BY stock_quantity ASC LIMIT 20"

    # System metrics (admin only)
    elif "system" in query_lower and "performance" in query_lower:
        return "SELECT 'CPU Usage' as metric_name, '45%' as current_value, 'Normal' as status UNION ALL SELECT 'Memory Usage', '62%', 'Normal'"

    elif "error" in query_lower and "log" in query_lower:
        return "SELECT 'Log entry simulated' as message, datetime('now') as timestamp"

    # Default: show products
    return "SELECT * FROM products ORDER BY price DESC LIMIT 20"

def process_query(query_text: str, user_info: Dict = None) -> Dict:
    """Process natural language query and return tenant-specific results from actual database."""
    query_lower = query_text.lower().strip()

    # Check permissions first
    if user_info and "role" in user_info:
        permission_check = check_query_permission(query_text, user_info["role"])
        if not permission_check["allowed"]:
            return {
                "success": False,
                "error": "permission_denied",
                "permission_details": permission_check,
                "query_text": query_text,
                "user_role": user_info["role"]
            }

    # Determine tenant
    tenant_id = "techcorp"
    if user_info and "org_id" in user_info:
        tenant_id = user_info["org_id"]

    # Generate SQL from natural language
    start_time = time.time()
    generated_sql = generate_sql_from_nl(query_text, tenant_id)

    # Execute query on actual database
    results = execute_database_query(generated_sql, tenant_id)
    execution_time = int((time.time() - start_time) * 1000)

    if results is None:
        results = []

    return {
        "success": True,
        "query_id": f"query_{int(time.time())}",
        "generated_sql": generated_sql,
        "results": results,
        "execution_time_ms": execution_time,
        "status": "success",
        "message": f"Query executed successfully. Returned {len(results)} rows from {tenant_id} database.",
        "tenant": tenant_id,
        "tenant_specific": True
    }

def get_query_suggestions() -> List[str]:
    """Get query suggestions based on current user."""
    base_suggestions = [
        "Show me all products",
        "How many users are in the system?",
        "List the top customers by sales",
        "What is the average order value?",
        "Show me sales data from last month",
        "Display inventory levels by warehouse",
        "Show monthly revenue trends"
    ]

    if st.session_state.user_info and st.session_state.user_info["role"] == "admin":
        base_suggestions.extend([
            "Show system performance metrics",
            "List all active users",
            "Display error logs from today"
        ])

    return base_suggestions

def login_page():
    """Display login page."""
    st.title("🤖 Multi-Tenant NLP2SQL System")
    st.markdown("### Welcome to the AI-Powered Data Query Interface")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("#### Login to Your Account")

        # Demo accounts info
        with st.expander("📋 Demo Accounts", expanded=True):
            st.markdown("""
            **Available Demo Accounts:**

            **TechCorp Solutions:**
            - 👤 Admin: `admin@techcorp.com` / `admin123`
            - 📊 Analyst: `analyst@techcorp.com` / `analyst123`

            **HealthPlus Medical:**
            - 👤 User: `user@healthplus.com` / `user123`
            """)

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("🚀 Login", use_container_width=True)

            if submit_button:
                if email and password:
                    auth_result = authenticate_user(email, password)

                    if auth_result["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user_info = auth_result["user"]
                        st.session_state.current_tenant = auth_result["user"]["org_id"]  # Set tenant from user's org_id
                        st.rerun()
                    else:
                        st.error(f"❌ {auth_result['error']}")
                else:
                    st.warning("⚠️ Please enter both email and password")

def main_app():
    """Main application interface."""
    user = st.session_state.user_info

    # Header
    st.title(f"🤖 Multi-Tenant NLP2SQL - {user['org_name']}")

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {user['full_name']}")
        st.markdown(f"**Role:** {user['role'].title()}")
        st.markdown(f"**Organization:** {user['org_name']}")
        st.markdown(f"**Tenant:** {st.session_state.current_tenant}")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.session_state.chat_history = []
            st.rerun()

        st.markdown("---")

        # Query suggestions
        st.markdown("### 💡 Quick Queries")
        suggestions = get_query_suggestions()

        for suggestion in suggestions[:5]:
            if st.button(f"📝 {suggestion}", key=f"suggest_{suggestion}", use_container_width=True):
                st.session_state.current_query = suggestion
                st.rerun()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 💬 Ask Your Data")

        # Query input
        query_text = st.text_area(
            "Enter your natural language query:",
            height=100,
            placeholder="e.g., Show me all products with low inventory",
            value=st.session_state.get('current_query', '')
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)

        with col_btn2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.current_query = ""
                st.session_state.last_result = None
                st.rerun()

        # Execute query
        if execute_button and query_text:
            with st.spinner("🔄 Processing your query..."):
                result = process_query(query_text, st.session_state.user_info)
                st.session_state.last_result = result

        # Display last result if exists
        if st.session_state.last_result:
            result = st.session_state.last_result

            if result.get("success"):
                # Display results
                st.markdown("#### ✅ Query Results")

                # Show generated SQL
                with st.expander("🔍 Generated SQL", expanded=False):
                    st.code(result["generated_sql"], language="sql")

                # Show execution info
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("⏱️ Execution Time", f"{result['execution_time_ms']}ms")
                with col_info2:
                    st.metric("📊 Rows Returned", len(result["results"]))
                with col_info3:
                    st.metric("✅ Status", result["status"].title())

                # Display data
                if result["results"]:
                    df = pd.DataFrame(result["results"])
                    st.dataframe(df, use_container_width=True)

                    # Generate visualizations for certain types of data
                    if len(df) > 1 and len(df.columns) >= 2:
                        try:
                            numeric_cols = df.select_dtypes(include=['number']).columns
                            if len(numeric_cols) > 0:
                                st.markdown("#### 📈 Data Visualization")

                                if 'revenue' in df.columns or 'total_sales' in df.columns:
                                    # Revenue/sales chart
                                    y_col = 'revenue' if 'revenue' in df.columns else 'total_sales'
                                    x_col = df.columns[0]
                                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col.title()} by {x_col.title()}")
                                    st.plotly_chart(fig, use_container_width=True)

                                elif 'price' in df.columns:
                                    # Price distribution
                                    fig = px.histogram(df, x='price', title="Price Distribution")
                                    st.plotly_chart(fig, use_container_width=True)

                                elif len(numeric_cols) >= 2:
                                    # Generic scatter plot
                                    fig = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1],
                                                   title=f"{numeric_cols[1]} vs {numeric_cols[0]}")
                                    st.plotly_chart(fig, use_container_width=True)
                        except Exception:
                            pass  # Skip visualization if there's an error

                    # Export options
                    st.markdown("#### 📥 Export Data")
                    col_exp1, col_exp2, col_exp3 = st.columns(3)

                    with col_exp1:
                        csv = df.to_csv(index=False)
                        st.download_button("📄 Download CSV", csv, "query_results.csv", "text/csv")

                    with col_exp2:
                        json_str = df.to_json(orient='records', indent=2)
                        st.download_button("📋 Download JSON", json_str, "query_results.json", "application/json")

                    with col_exp3:
                        if st.button("📊 View in New Tab"):
                            st.balloons()

                # Show tenant-specific message
                tenant_name = result.get("tenant", "generic")
                if result.get("tenant_specific", False):
                    if tenant_name == "techcorp":
                        st.success(f"✅ {result['message']} (TechCorp Solutions Data)")
                    elif tenant_name == "healthplus":
                        st.success(f"✅ {result['message']} (HealthPlus Medical Data)")
                    else:
                        st.success(f"✅ {result['message']} (Tenant: {tenant_name})")
                else:
                    st.success(result["message"])
            else:
                # Check if it's a permission denied error
                if result.get("error") == "permission_denied":
                    perm_details = result.get("permission_details", {})

                    # Display permission denied error with detailed information
                    st.error(f"### {perm_details.get('title', 'Access Denied')}")
                    st.markdown(perm_details.get('message', 'You do not have permission to execute this query.'))

                    # Show details in a warning box
                    st.warning(f"""
                    **📋 Query Attempted:** `{result.get('query_text', 'N/A')}`

                    **👤 Your Role:** `{result.get('user_role', 'N/A').title()}`

                    **🔑 Required Role:** `{perm_details.get('required_role', 'Higher privileges')}`

                    **🔒 Restricted Feature:** `{perm_details.get('feature_type', 'N/A').replace('_', ' ').title()}`
                    """)

                    # Show suggestion in an info box
                    if perm_details.get('suggestion'):
                        st.info(f"💡 **Suggestion:** {perm_details.get('suggestion')}")

                    # Show what the user CAN do
                    user_role = result.get('user_role', 'user')
                    role_info = ROLE_PERMISSIONS.get(user_role, {})

                    with st.expander("ℹ️ What can I do with my current role?"):
                        st.markdown(f"**Your Role:** {user_role.title()}")
                        st.markdown(f"**Description:** {role_info.get('description', 'N/A')}")
                        st.markdown("**Allowed Features:**")
                        for feature in role_info.get('features', []):
                            st.markdown(f"- ✅ {feature.replace('_', ' ').title()}")

                        if role_info.get('restricted'):
                            st.markdown("**Restricted Features:**")
                            for feature in role_info.get('restricted', []):
                                st.markdown(f"- ❌ {feature.replace('_', ' ').title()}")
                else:
                    st.error(f"❌ Query failed: {result.get('error', 'Unknown error')}")

    with col2:
        st.markdown("### 📜 Query History")

        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history[-10:])):  # Show last 10
                with st.expander(f"📝 {chat['query'][:30]}...", expanded=False):
                    st.markdown(f"**Time:** {chat['timestamp'][:19]}")
                    st.markdown(f"**Query:** {chat['query']}")
                    if chat['result']['success']:
                        st.markdown(f"**Rows:** {len(chat['result']['results'])}")
                        st.markdown(f"**Time:** {chat['result']['execution_time_ms']}ms")

                    if st.button(f"🔄 Re-run", key=f"rerun_{i}"):
                        st.session_state.current_query = chat['query']
                        st.rerun()
        else:
            st.info("No queries executed yet. Try asking something!")

        # Clear history button
        if st.session_state.chat_history and st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

def main():
    """Main application entry point."""
    # Custom CSS
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stButton > button {
        border-radius: 10px;
        border: none;
        transition: all 0.3s;
    }
    .stTextArea > div > div > textarea {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()