"""
Pytest configuration file with fixtures and test setup for multi-tenant NLP2SQL testing.
"""

import asyncio
import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = Path(tempfile.mkdtemp(prefix="nlp2sql_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_database_connection():
    """Mock database connection for testing."""
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = Mock()
    mock_conn.fetch.return_value = []
    mock_conn.fetchone.return_value = None
    return mock_conn


@pytest.fixture
def mock_tenant_connection_manager():
    """Mock tenant connection manager."""
    manager = AsyncMock()
    manager.get_connection.return_value = Mock()
    manager.test_tenant_connection.return_value = True
    manager.get_tenant_connection_stats.return_value = {
        "pool_size": 10,
        "active_connections": 2,
        "peak_connections": 5
    }
    manager.get_tenant_query_stats.return_value = {
        "avg_response_time_ms": 150,
        "total_queries": 1000
    }
    manager.create_tenant_connection_pool.return_value = True
    manager.close_tenant_connections.return_value = True
    return manager


@pytest.fixture
def mock_rbac_manager():
    """Mock RBAC manager."""
    manager = AsyncMock()
    manager.test_tenant_rbac.return_value = True
    manager.validate_user_permissions.return_value = True
    manager.get_user_roles.return_value = ["user"]
    return manager


@pytest.fixture
def mock_nlp2sql_engine():
    """Mock NLP2SQL engine."""
    engine = AsyncMock()

    # Mock query result
    mock_result = Mock()
    mock_result.sql_query = "SELECT * FROM products WHERE category = 'electronics'"
    mock_result.success = True
    mock_result.execution_time = 0.15

    engine.process_nlp_query.return_value = mock_result
    return engine


@pytest.fixture
def mock_provisioning_manager():
    """Mock provisioning manager."""
    manager = AsyncMock()
    manager.execute_onboarding_workflow.return_value = True
    return manager


@pytest.fixture
def mock_email_orchestrator():
    """Mock email orchestrator."""
    orchestrator = AsyncMock()
    orchestrator.send_welcome_email.return_value = True
    return orchestrator


@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing."""
    return {
        "tenant_id": "test_tenant_123",
        "org_name": "Test Organization",
        "industry": "technology",
        "database_type": "postgresql",
        "admin_email": "admin@testorg.com",
        "admin_name": "Test Admin",
        "expected_users": 50,
        "expected_queries_per_day": 10000
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "test_user",
        "email": "user@testorg.com",
        "role": "user",
        "tenant_id": "test_tenant_123",
        "permissions": ["read", "query"]
    }


@pytest.fixture
def security_test_payloads():
    """Common security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
    }


@pytest.fixture
def test_queries():
    """Sample test queries for different complexity levels."""
    return {
        "simple": [
            "Show me all users",
            "List all products",
            "Display recent orders"
        ],
        "medium": [
            "Show customer orders with product details",
            "What is the average order value?",
            "List users with their recent purchases"
        ],
        "complex": [
            "Show me users who placed orders in the last 30 days with total spend",
            "Find products with inventory below threshold and pending orders",
            "Generate monthly sales report by category"
        ]
    }


# Pytest hooks for test customization

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as security test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on test file names
        if "security" in item.fspath.basename:
            item.add_marker(pytest.mark.security)
        elif "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        elif "load" in item.fspath.basename:
            item.add_marker(pytest.mark.load)
        elif "isolation" in item.fspath.basename:
            item.add_marker(pytest.mark.isolation)
        elif "nlp2sql" in item.fspath.basename:
            item.add_marker(pytest.mark.nlp2sql)

        # Mark slow tests
        if "load" in item.fspath.basename or "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def cleanup_test_resources():
    """Automatically clean up test resources after each test."""
    yield
    # Cleanup code would go here if needed
    pass


# Performance testing fixtures

@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "query_response_time_ms": 1000,
        "tenant_creation_time_seconds": 30,
        "backup_time_minutes": 5,
        "restore_time_minutes": 3,
        "concurrent_users": 100,
        "queries_per_second": 1000
    }


# Mock external services

@pytest.fixture
def mock_external_apis():
    """Mock external API responses."""
    return {
        "email_service": {
            "send_email": {"status": "success", "message_id": "12345"},
            "validate_email": {"valid": True, "deliverable": True}
        },
        "monitoring_service": {
            "log_metric": {"status": "success"},
            "create_alert": {"alert_id": "alert_123"}
        },
        "backup_service": {
            "create_backup": {"backup_id": "backup_123", "status": "completed"},
            "restore_backup": {"restore_id": "restore_123", "status": "completed"}
        }
    }


# Database fixtures for testing

@pytest.fixture
def mock_database_schemas():
    """Mock database schemas for different industries."""
    return {
        "healthcare": {
            "tables": ["patients", "doctors", "appointments", "medications"],
            "relationships": [
                {"from": "appointments", "to": "patients", "key": "patient_id"},
                {"from": "appointments", "to": "doctors", "key": "doctor_id"}
            ]
        },
        "finance": {
            "tables": ["accounts", "transactions", "customers", "loans"],
            "relationships": [
                {"from": "accounts", "to": "customers", "key": "customer_id"},
                {"from": "transactions", "to": "accounts", "key": "account_id"}
            ]
        },
        "ecommerce": {
            "tables": ["products", "orders", "customers", "categories"],
            "relationships": [
                {"from": "products", "to": "categories", "key": "category_id"},
                {"from": "orders", "to": "customers", "key": "customer_id"}
            ]
        }
    }


# Test data generators

@pytest.fixture
def generate_test_tenant():
    """Function to generate test tenant data."""
    def _generate(tenant_count: int = 1, industry: str = "technology"):
        tenants = []
        for i in range(tenant_count):
            tenant = {
                "tenant_id": f"test_tenant_{i+1}",
                "org_name": f"Test Organization {i+1}",
                "industry": industry,
                "database_type": "postgresql",
                "admin_email": f"admin{i+1}@testorg.com",
                "created_at": "2024-01-01T00:00:00Z"
            }
            tenants.append(tenant)
        return tenants if tenant_count > 1 else tenants[0]

    return _generate


@pytest.fixture
def generate_test_users():
    """Function to generate test user data."""
    def _generate(user_count: int = 1, tenant_id: str = "test_tenant_1"):
        users = []
        roles = ["admin", "user", "viewer", "analyst"]

        for i in range(user_count):
            user = {
                "user_id": f"test_user_{i+1}",
                "username": f"testuser{i+1}",
                "email": f"user{i+1}@testorg.com",
                "role": roles[i % len(roles)],
                "tenant_id": tenant_id,
                "permissions": ["read"] if roles[i % len(roles)] == "viewer" else ["read", "write"],
                "created_at": "2024-01-01T00:00:00Z"
            }
            users.append(user)
        return users if user_count > 1 else users[0]

    return _generate


# Async context managers for testing

@pytest.fixture
async def async_test_context():
    """Async context manager for tests requiring async setup/teardown."""
    # Setup
    test_context = {
        "initialized": True,
        "resources": []
    }

    try:
        yield test_context
    finally:
        # Cleanup
        for resource in test_context.get("resources", []):
            try:
                if hasattr(resource, "close"):
                    await resource.close()
            except Exception:
                pass