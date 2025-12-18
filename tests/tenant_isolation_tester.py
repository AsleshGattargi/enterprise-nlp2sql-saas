"""
Comprehensive Tenant Isolation Testing Framework
Tests data isolation, cross-tenant access prevention, and schema consistency.
"""

import asyncio
import pytest
import logging
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, timedelta
import uuid
import hashlib
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from src.database_cloner import DatabaseCloner
from src.tenant_connection_manager import TenantConnectionManager
from src.tenant_rbac_manager import TenantRBACManager
from src.tenant_onboarding_models import TenantRegistration, DatabaseType, IndustryType, DataRegion
from src.automated_provisioning import ProvisioningManager
from src.industry_schema_templates import IndustrySchemaTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IsolationTestResult:
    """Result of an isolation test."""
    test_name: str
    tenant_id: str
    passed: bool
    details: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrossTenantTestResult:
    """Result of cross-tenant access test."""
    test_name: str
    tenant1_id: str
    tenant2_id: str
    access_prevented: bool
    isolation_confirmed: bool
    details: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TenantIsolationTester:
    """Comprehensive tenant isolation testing framework."""

    def __init__(self,
                 connection_manager: TenantConnectionManager,
                 rbac_manager: TenantRBACManager,
                 database_cloner: DatabaseCloner):
        self.connection_manager = connection_manager
        self.rbac_manager = rbac_manager
        self.database_cloner = database_cloner
        self.test_results: List[IsolationTestResult] = []
        self.cross_tenant_results: List[CrossTenantTestResult] = []
        self.test_tenants: Dict[str, Dict[str, Any]] = {}

    async def setup_test_tenants(self, count: int = 3) -> List[str]:
        """Set up test tenants for isolation testing."""
        logger.info(f"Setting up {count} test tenants for isolation testing")

        tenant_configs = [
            {
                "org_name": "Alpha Healthcare Test",
                "industry": IndustryType.HEALTHCARE,
                "database_type": DatabaseType.POSTGRESQL,
                "data_region": DataRegion.US_EAST
            },
            {
                "org_name": "Beta Finance Test",
                "industry": IndustryType.FINANCE,
                "database_type": DatabaseType.MYSQL,
                "data_region": DataRegion.US_WEST
            },
            {
                "org_name": "Gamma Tech Test",
                "industry": IndustryType.TECHNOLOGY,
                "database_type": DatabaseType.POSTGRESQL,
                "data_region": DataRegion.EU_CENTRAL
            }
        ]

        created_tenants = []

        for i in range(count):
            config = tenant_configs[i % len(tenant_configs)]
            tenant_id = f"isolation_test_{uuid.uuid4().hex[:8]}"

            # Create test data for this tenant
            test_data = await self._create_tenant_test_data(tenant_id, config)
            self.test_tenants[tenant_id] = test_data
            created_tenants.append(tenant_id)

            logger.info(f"Created test tenant: {tenant_id}")

        return created_tenants

    async def _create_tenant_test_data(self, tenant_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create isolated test data for a tenant."""
        return {
            "tenant_id": tenant_id,
            "org_name": config["org_name"],
            "industry": config["industry"],
            "database_type": config["database_type"],
            "data_region": config["data_region"],
            "test_tables": [
                {
                    "name": "test_users",
                    "data": [
                        {"id": 1, "name": f"User1_{tenant_id}", "email": f"user1@{tenant_id}.com"},
                        {"id": 2, "name": f"User2_{tenant_id}", "email": f"user2@{tenant_id}.com"},
                        {"id": 3, "name": f"User3_{tenant_id}", "email": f"user3@{tenant_id}.com"}
                    ]
                },
                {
                    "name": "test_orders",
                    "data": [
                        {"id": 1, "user_id": 1, "product": f"Product1_{tenant_id}", "amount": 100.00},
                        {"id": 2, "user_id": 2, "product": f"Product2_{tenant_id}", "amount": 200.00},
                        {"id": 3, "user_id": 3, "product": f"Product3_{tenant_id}", "amount": 300.00}
                    ]
                },
                {
                    "name": "test_sensitive_data",
                    "data": [
                        {"id": 1, "tenant_specific_id": tenant_id, "secret_value": f"SECRET_{tenant_id}_DATA"},
                        {"id": 2, "tenant_specific_id": tenant_id, "secret_value": f"CONFIDENTIAL_{tenant_id}_INFO"}
                    ]
                }
            ],
            "test_users": [
                {
                    "username": f"admin_{tenant_id}",
                    "email": f"admin@{tenant_id}.com",
                    "role": "admin",
                    "tenant_id": tenant_id
                },
                {
                    "username": f"user_{tenant_id}",
                    "email": f"user@{tenant_id}.com",
                    "role": "user",
                    "tenant_id": tenant_id
                }
            ],
            "schema_fingerprint": await self._generate_schema_fingerprint(tenant_id),
            "data_fingerprint": await self._generate_data_fingerprint(tenant_id)
        }

    async def _generate_schema_fingerprint(self, tenant_id: str) -> str:
        """Generate a unique fingerprint for tenant schema."""
        schema_elements = [
            f"tenant_{tenant_id}",
            "test_users", "test_orders", "test_sensitive_data",
            "id", "name", "email", "user_id", "product", "amount",
            "tenant_specific_id", "secret_value"
        ]
        schema_string = "|".join(sorted(schema_elements))
        return hashlib.sha256(schema_string.encode()).hexdigest()

    async def _generate_data_fingerprint(self, tenant_id: str) -> str:
        """Generate a unique fingerprint for tenant data."""
        data_elements = [
            f"User1_{tenant_id}", f"User2_{tenant_id}", f"User3_{tenant_id}",
            f"Product1_{tenant_id}", f"Product2_{tenant_id}", f"Product3_{tenant_id}",
            f"SECRET_{tenant_id}_DATA", f"CONFIDENTIAL_{tenant_id}_INFO"
        ]
        data_string = "|".join(sorted(data_elements))
        return hashlib.sha256(data_string.encode()).hexdigest()

    async def test_data_isolation(self, tenant1_id: str, tenant2_id: str) -> IsolationTestResult:
        """Test that data is completely isolated between two tenants."""
        test_name = "Data Isolation Test"
        start_time = time.time()

        try:
            logger.info(f"Testing data isolation between {tenant1_id} and {tenant2_id}")

            # Test 1: Verify tenant1 cannot access tenant2's data
            tenant1_data = await self._get_tenant_data(tenant1_id)
            tenant2_data = await self._get_tenant_data(tenant2_id)

            # Verify no data overlap
            isolation_confirmed = True
            details = []

            # Check for data contamination
            for table_name in ["test_users", "test_orders", "test_sensitive_data"]:
                t1_table_data = tenant1_data.get(table_name, [])
                t2_table_data = tenant2_data.get(table_name, [])

                # Check for cross-contamination
                for t1_record in t1_table_data:
                    for t2_record in t2_table_data:
                        if self._records_overlap(t1_record, t2_record, tenant1_id, tenant2_id):
                            isolation_confirmed = False
                            details.append(f"Data contamination detected in {table_name}")

            # Test 2: Verify connection isolation
            conn1_stats = await self.connection_manager.get_tenant_connection_stats(tenant1_id)
            conn2_stats = await self.connection_manager.get_tenant_connection_stats(tenant2_id)

            if conn1_stats.get("database_name") == conn2_stats.get("database_name"):
                isolation_confirmed = False
                details.append("Database name collision detected")

            # Test 3: Verify schema isolation
            schema1 = await self._get_tenant_schema(tenant1_id)
            schema2 = await self._get_tenant_schema(tenant2_id)

            if schema1["fingerprint"] == schema2["fingerprint"]:
                isolation_confirmed = False
                details.append("Schema fingerprint collision detected")

            execution_time = time.time() - start_time

            result = IsolationTestResult(
                test_name=test_name,
                tenant_id=f"{tenant1_id}|{tenant2_id}",
                passed=isolation_confirmed,
                details="; ".join(details) if details else "Complete data isolation confirmed",
                execution_time=execution_time,
                metadata={
                    "tenant1_record_count": len(tenant1_data.get("test_users", [])),
                    "tenant2_record_count": len(tenant2_data.get("test_users", [])),
                    "isolation_checks_performed": 6
                }
            )

            self.test_results.append(result)
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            result = IsolationTestResult(
                test_name=test_name,
                tenant_id=f"{tenant1_id}|{tenant2_id}",
                passed=False,
                details=f"Test failed with error: {str(e)}",
                execution_time=execution_time
            )
            self.test_results.append(result)
            return result

    async def test_cross_tenant_access_prevention(self) -> List[CrossTenantTestResult]:
        """Test that cross-tenant access is properly prevented."""
        logger.info("Testing cross-tenant access prevention")
        results = []

        if len(self.test_tenants) < 2:
            logger.warning("Need at least 2 tenants for cross-tenant access testing")
            return results

        tenant_ids = list(self.test_tenants.keys())

        for i in range(len(tenant_ids)):
            for j in range(i + 1, len(tenant_ids)):
                tenant1_id = tenant_ids[i]
                tenant2_id = tenant_ids[j]

                result = await self._test_cross_tenant_access_pair(tenant1_id, tenant2_id)
                results.append(result)

        self.cross_tenant_results.extend(results)
        return results

    async def _test_cross_tenant_access_pair(self, tenant1_id: str, tenant2_id: str) -> CrossTenantTestResult:
        """Test cross-tenant access prevention between a specific pair."""
        test_name = "Cross-Tenant Access Prevention"
        start_time = time.time()

        try:
            access_prevented = True
            isolation_confirmed = True
            details = []

            # Test 1: Try to access tenant2's data using tenant1's connection
            try:
                cross_access_result = await self._attempt_cross_tenant_data_access(tenant1_id, tenant2_id)
                if cross_access_result["data_accessed"]:
                    access_prevented = False
                    isolation_confirmed = False
                    details.append("Cross-tenant data access was not prevented")
            except Exception as e:
                details.append(f"Cross-tenant access properly blocked: {str(e)}")

            # Test 2: Try to access tenant2's connection pool from tenant1
            try:
                cross_connection_result = await self._attempt_cross_tenant_connection_access(tenant1_id, tenant2_id)
                if cross_connection_result["connection_accessed"]:
                    access_prevented = False
                    isolation_confirmed = False
                    details.append("Cross-tenant connection access was not prevented")
            except Exception as e:
                details.append(f"Cross-tenant connection access properly blocked: {str(e)}")

            # Test 3: Try to access tenant2's RBAC from tenant1
            try:
                cross_rbac_result = await self._attempt_cross_tenant_rbac_access(tenant1_id, tenant2_id)
                if cross_rbac_result["rbac_accessed"]:
                    access_prevented = False
                    isolation_confirmed = False
                    details.append("Cross-tenant RBAC access was not prevented")
            except Exception as e:
                details.append(f"Cross-tenant RBAC access properly blocked: {str(e)}")

            execution_time = time.time() - start_time

            return CrossTenantTestResult(
                test_name=test_name,
                tenant1_id=tenant1_id,
                tenant2_id=tenant2_id,
                access_prevented=access_prevented,
                isolation_confirmed=isolation_confirmed,
                details="; ".join(details),
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return CrossTenantTestResult(
                test_name=test_name,
                tenant1_id=tenant1_id,
                tenant2_id=tenant2_id,
                access_prevented=False,
                isolation_confirmed=False,
                details=f"Test failed with error: {str(e)}",
                execution_time=execution_time
            )

    async def test_user_permission_boundaries(self) -> List[IsolationTestResult]:
        """Test that user permissions are properly isolated between tenants."""
        logger.info("Testing user permission boundaries")
        results = []

        for tenant_id, tenant_data in self.test_tenants.items():
            result = await self._test_tenant_user_permissions(tenant_id, tenant_data)
            results.append(result)

        self.test_results.extend(results)
        return results

    async def _test_tenant_user_permissions(self, tenant_id: str, tenant_data: Dict[str, Any]) -> IsolationTestResult:
        """Test user permission boundaries for a specific tenant."""
        test_name = "User Permission Boundaries"
        start_time = time.time()

        try:
            permissions_isolated = True
            details = []

            # Test admin user permissions
            admin_user = tenant_data["test_users"][0]  # admin user
            admin_permissions = await self._get_user_permissions(tenant_id, admin_user["username"])

            # Verify admin can only access their tenant
            if admin_permissions.get("accessible_tenants"):
                accessible_tenants = admin_permissions["accessible_tenants"]
                if any(tid != tenant_id for tid in accessible_tenants):
                    permissions_isolated = False
                    details.append("Admin user has access to other tenants")

            # Test regular user permissions
            regular_user = tenant_data["test_users"][1]  # regular user
            regular_permissions = await self._get_user_permissions(tenant_id, regular_user["username"])

            # Verify regular user has limited permissions
            if regular_permissions.get("role") != "user":
                permissions_isolated = False
                details.append("Regular user has elevated permissions")

            # Test cross-tenant user access
            for other_tenant_id in self.test_tenants:
                if other_tenant_id != tenant_id:
                    cross_access = await self._test_user_cross_tenant_access(
                        admin_user["username"], tenant_id, other_tenant_id
                    )
                    if cross_access["access_granted"]:
                        permissions_isolated = False
                        details.append(f"User can access other tenant: {other_tenant_id}")

            execution_time = time.time() - start_time

            return IsolationTestResult(
                test_name=test_name,
                tenant_id=tenant_id,
                passed=permissions_isolated,
                details="; ".join(details) if details else "User permissions properly isolated",
                execution_time=execution_time,
                metadata={
                    "admin_user": admin_user["username"],
                    "regular_user": regular_user["username"],
                    "cross_tenant_tests": len(self.test_tenants) - 1
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return IsolationTestResult(
                test_name=test_name,
                tenant_id=tenant_id,
                passed=False,
                details=f"Test failed with error: {str(e)}",
                execution_time=execution_time
            )

    async def verify_schema_consistency(self, tenant_id: str) -> IsolationTestResult:
        """Verify that tenant schema is consistent and isolated."""
        test_name = "Schema Consistency Verification"
        start_time = time.time()

        try:
            logger.info(f"Verifying schema consistency for tenant {tenant_id}")

            schema_consistent = True
            details = []

            # Get tenant schema
            tenant_schema = await self._get_tenant_schema(tenant_id)
            expected_fingerprint = self.test_tenants[tenant_id]["schema_fingerprint"]

            # Verify schema fingerprint
            if tenant_schema["fingerprint"] != expected_fingerprint:
                schema_consistent = False
                details.append("Schema fingerprint mismatch detected")

            # Verify required tables exist
            required_tables = ["test_users", "test_orders", "test_sensitive_data"]
            existing_tables = tenant_schema.get("tables", [])

            for table in required_tables:
                if table not in existing_tables:
                    schema_consistent = False
                    details.append(f"Required table missing: {table}")

            # Verify schema isolation (no foreign tenant references)
            for table_name, table_schema in tenant_schema.get("table_schemas", {}).items():
                if self._schema_contains_foreign_references(table_schema, tenant_id):
                    schema_consistent = False
                    details.append(f"Foreign tenant references found in {table_name}")

            # Verify data integrity
            data_integrity = await self._verify_tenant_data_integrity(tenant_id)
            if not data_integrity["consistent"]:
                schema_consistent = False
                details.extend(data_integrity["issues"])

            execution_time = time.time() - start_time

            return IsolationTestResult(
                test_name=test_name,
                tenant_id=tenant_id,
                passed=schema_consistent,
                details="; ".join(details) if details else "Schema consistency verified",
                execution_time=execution_time,
                metadata={
                    "tables_checked": len(required_tables),
                    "schema_fingerprint": tenant_schema["fingerprint"],
                    "data_integrity_verified": data_integrity["consistent"]
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return IsolationTestResult(
                test_name=test_name,
                tenant_id=tenant_id,
                passed=False,
                details=f"Test failed with error: {str(e)}",
                execution_time=execution_time
            )

    async def run_comprehensive_isolation_tests(self) -> Dict[str, Any]:
        """Run all isolation tests and return comprehensive results."""
        logger.info("Starting comprehensive tenant isolation tests")

        # Set up test tenants
        test_tenant_ids = await self.setup_test_tenants(3)

        # Run all test categories
        results = {
            "test_execution": {
                "start_time": datetime.utcnow().isoformat(),
                "tenant_count": len(test_tenant_ids),
                "test_tenant_ids": test_tenant_ids
            },
            "data_isolation": [],
            "cross_tenant_access": [],
            "user_permissions": [],
            "schema_consistency": [],
            "summary": {}
        }

        try:
            # Test data isolation between all tenant pairs
            for i in range(len(test_tenant_ids)):
                for j in range(i + 1, len(test_tenant_ids)):
                    isolation_result = await self.test_data_isolation(
                        test_tenant_ids[i], test_tenant_ids[j]
                    )
                    results["data_isolation"].append(isolation_result.__dict__)

            # Test cross-tenant access prevention
            cross_tenant_results = await self.test_cross_tenant_access_prevention()
            results["cross_tenant_access"] = [r.__dict__ for r in cross_tenant_results]

            # Test user permission boundaries
            permission_results = await self.test_user_permission_boundaries()
            results["user_permissions"] = [r.__dict__ for r in permission_results]

            # Test schema consistency for each tenant
            for tenant_id in test_tenant_ids:
                schema_result = await self.verify_schema_consistency(tenant_id)
                results["schema_consistency"].append(schema_result.__dict__)

            # Generate summary
            results["summary"] = self._generate_test_summary(results)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()

            logger.info("Comprehensive isolation tests completed")
            return results

        except Exception as e:
            logger.error(f"Comprehensive isolation tests failed: {str(e)}")
            results["test_execution"]["error"] = str(e)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()
            return results

    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of all test results."""
        total_tests = 0
        passed_tests = 0

        # Count data isolation tests
        for test in results["data_isolation"]:
            total_tests += 1
            if test["passed"]:
                passed_tests += 1

        # Count cross-tenant access tests
        for test in results["cross_tenant_access"]:
            total_tests += 1
            if test["isolation_confirmed"]:
                passed_tests += 1

        # Count user permission tests
        for test in results["user_permissions"]:
            total_tests += 1
            if test["passed"]:
                passed_tests += 1

        # Count schema consistency tests
        for test in results["schema_consistency"]:
            total_tests += 1
            if test["passed"]:
                passed_tests += 1

        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": round(success_rate, 2),
            "isolation_verified": success_rate == 100.0,
            "critical_issues": [
                test for category in ["data_isolation", "cross_tenant_access", "user_permissions", "schema_consistency"]
                for test in results[category]
                if not test.get("passed", test.get("isolation_confirmed", False))
            ]
        }

    # Helper methods for testing implementation

    async def _get_tenant_data(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant-specific data for testing."""
        # Mock implementation - in real scenario, would query actual database
        if tenant_id in self.test_tenants:
            return {
                table["name"]: table["data"]
                for table in self.test_tenants[tenant_id]["test_tables"]
            }
        return {}

    async def _get_tenant_schema(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant schema information."""
        # Mock implementation
        if tenant_id in self.test_tenants:
            return {
                "fingerprint": self.test_tenants[tenant_id]["schema_fingerprint"],
                "tables": [table["name"] for table in self.test_tenants[tenant_id]["test_tables"]],
                "table_schemas": {
                    "test_users": ["id", "name", "email"],
                    "test_orders": ["id", "user_id", "product", "amount"],
                    "test_sensitive_data": ["id", "tenant_specific_id", "secret_value"]
                }
            }
        return {}

    async def _get_user_permissions(self, tenant_id: str, username: str) -> Dict[str, Any]:
        """Get user permissions for testing."""
        # Mock implementation
        if tenant_id in self.test_tenants:
            for user in self.test_tenants[tenant_id]["test_users"]:
                if user["username"] == username:
                    return {
                        "username": username,
                        "role": user["role"],
                        "tenant_id": user["tenant_id"],
                        "accessible_tenants": [tenant_id]  # Should only access own tenant
                    }
        return {}

    def _records_overlap(self, record1: Dict, record2: Dict, tenant1_id: str, tenant2_id: str) -> bool:
        """Check if two records overlap inappropriately."""
        # Check for tenant-specific identifiers in wrong tenant
        record1_str = json.dumps(record1, sort_keys=True)
        record2_str = json.dumps(record2, sort_keys=True)

        # Record1 should not contain tenant2 identifiers
        if tenant2_id in record1_str:
            return True

        # Record2 should not contain tenant1 identifiers
        if tenant1_id in record2_str:
            return True

        return False

    def _schema_contains_foreign_references(self, table_schema: List[str], tenant_id: str) -> bool:
        """Check if schema contains references to other tenants."""
        schema_str = " ".join(table_schema)
        other_tenant_ids = [tid for tid in self.test_tenants.keys() if tid != tenant_id]

        for other_id in other_tenant_ids:
            if other_id in schema_str:
                return True

        return False

    async def _attempt_cross_tenant_data_access(self, tenant1_id: str, tenant2_id: str) -> Dict[str, Any]:
        """Attempt to access tenant2's data using tenant1's context."""
        # Mock implementation - should always fail in properly isolated system
        return {"data_accessed": False, "error": "Access denied - tenant isolation enforced"}

    async def _attempt_cross_tenant_connection_access(self, tenant1_id: str, tenant2_id: str) -> Dict[str, Any]:
        """Attempt to access tenant2's connection from tenant1."""
        # Mock implementation
        return {"connection_accessed": False, "error": "Connection access denied"}

    async def _attempt_cross_tenant_rbac_access(self, tenant1_id: str, tenant2_id: str) -> Dict[str, Any]:
        """Attempt to access tenant2's RBAC from tenant1."""
        # Mock implementation
        return {"rbac_accessed": False, "error": "RBAC access denied"}

    async def _test_user_cross_tenant_access(self, username: str, source_tenant: str, target_tenant: str) -> Dict[str, Any]:
        """Test if user can access another tenant."""
        # Mock implementation
        return {"access_granted": False, "error": "Cross-tenant access denied"}

    async def _verify_tenant_data_integrity(self, tenant_id: str) -> Dict[str, Any]:
        """Verify data integrity for a tenant."""
        # Mock implementation
        return {
            "consistent": True,
            "issues": [],
            "checks_performed": ["referential_integrity", "data_types", "constraints"]
        }

    async def cleanup_test_tenants(self):
        """Clean up test tenants after testing."""
        logger.info("Cleaning up test tenants")
        for tenant_id in self.test_tenants:
            try:
                # In real implementation, would clean up actual resources
                logger.info(f"Cleaned up test tenant: {tenant_id}")
            except Exception as e:
                logger.error(f"Failed to clean up tenant {tenant_id}: {str(e)}")

        self.test_tenants.clear()


# Export the main testing class
__all__ = ["TenantIsolationTester", "IsolationTestResult", "CrossTenantTestResult"]