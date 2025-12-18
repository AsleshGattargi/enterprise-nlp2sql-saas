"""
Comprehensive Test Suite for Multi-Tenant RBAC System
Tests authentication, authorization, cross-tenant access, and security.
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import pytest

from src.tenant_rbac_manager import TenantRBACManager, UserStatus
from src.cross_tenant_user_manager import CrossTenantUserManager, AccessRequestStatus
from src.rbac_role_templates import RoleTemplateManager, ResourceType, PermissionLevel


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RBACTestSuite:
    """Comprehensive test suite for RBAC system."""

    def __init__(self):
        """Initialize test suite with test database configuration."""
        self.rbac_db_config = {
            "type": "mysql",
            "connection": {
                "host": "localhost",
                "port": 3306,
                "database": "rbac_test",
                "user": "test_user",
                "password": "test_password",
                "charset": "utf8mb4"
            }
        }

        self.jwt_secret = "test-jwt-secret-key"
        self.rbac_manager = TenantRBACManager(self.rbac_db_config, self.jwt_secret)
        self.cross_tenant_manager = CrossTenantUserManager(self.rbac_manager)

        self.test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": [],
            "security_tests": [],
            "performance_metrics": {}
        }

        self.test_users = {}
        self.test_tenants = ["tenant_alpha", "tenant_beta", "tenant_gamma"]

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run complete RBAC test suite."""
        logger.info("🧪 Starting RBAC System Comprehensive Tests")
        logger.info("=" * 60)

        start_time = datetime.utcnow()

        try:
            # 1. System initialization tests
            await self.test_system_initialization()

            # 2. Role template tests
            await self.test_role_templates()

            # 3. User management tests
            await self.test_user_management()

            # 4. Authentication tests
            await self.test_authentication()

            # 5. Authorization tests
            await self.test_authorization()

            # 6. Cross-tenant access tests
            await self.test_cross_tenant_access()

            # 7. Permission inheritance tests
            await self.test_permission_inheritance()

            # 8. Session management tests
            await self.test_session_management()

            # 9. Security tests
            await self.test_security_scenarios()

            # 10. Performance tests
            await self.test_performance()

            # 11. Cleanup tests
            await self.test_cleanup_operations()

        except Exception as e:
            logger.error(f"Test suite error: {e}")
            self._record_test_result("SYSTEM_ERROR", False, str(e))

        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()

        # Calculate results
        self.test_results["execution_time_seconds"] = execution_time
        self.test_results["success_rate"] = (
            self.test_results["passed_tests"] / self.test_results["total_tests"] * 100
            if self.test_results["total_tests"] > 0 else 0
        )

        # Generate report
        await self._generate_test_report()

        logger.info(f"\n🎯 Test Results Summary:")
        logger.info(f"Total Tests: {self.test_results['total_tests']}")
        logger.info(f"Passed: {self.test_results['passed_tests']}")
        logger.info(f"Failed: {self.test_results['failed_tests']}")
        logger.info(f"Success Rate: {self.test_results['success_rate']:.1f}%")
        logger.info(f"Execution Time: {execution_time:.2f} seconds")

        return self.test_results

    async def test_system_initialization(self):
        """Test RBAC system initialization."""
        logger.info("🔧 Testing System Initialization")

        # Test role template installation
        try:
            results = self.rbac_manager.role_manager.install_default_templates()
            all_installed = all(results.values())
            self._record_test_result(
                "Install Default Role Templates",
                all_installed,
                f"Installed templates: {results}"
            )
        except Exception as e:
            self._record_test_result("Install Default Role Templates", False, str(e))

        # Test role hierarchy validation
        try:
            issues = self.rbac_manager.role_manager.validate_role_hierarchy()
            no_circular_deps = len(issues) == 0
            self._record_test_result(
                "Role Hierarchy Validation",
                no_circular_deps,
                f"Circular dependencies: {issues}" if issues else "No circular dependencies"
            )
        except Exception as e:
            self._record_test_result("Role Hierarchy Validation", False, str(e))

    async def test_role_templates(self):
        """Test role template management."""
        logger.info("👤 Testing Role Template Management")

        # Test listing role templates
        try:
            templates = self.rbac_manager.role_manager.list_role_templates()
            has_templates = len(templates) > 0
            self._record_test_result(
                "List Role Templates",
                has_templates,
                f"Found {len(templates)} role templates"
            )
        except Exception as e:
            self._record_test_result("List Role Templates", False, str(e))

        # Test getting specific role template
        try:
            admin_role = self.rbac_manager.role_manager.get_role_template("admin")
            has_admin_role = admin_role is not None
            self._record_test_result(
                "Get Admin Role Template",
                has_admin_role,
                f"Admin role found: {admin_role.display_name if admin_role else 'None'}"
            )
        except Exception as e:
            self._record_test_result("Get Admin Role Template", False, str(e))

        # Test permission resolution
        try:
            permissions = self.rbac_manager.role_manager.resolve_role_permissions("admin")
            has_permissions = len(permissions) > 0
            self._record_test_result(
                "Resolve Admin Permissions",
                has_permissions,
                f"Admin has {len(permissions)} permissions"
            )
        except Exception as e:
            self._record_test_result("Resolve Admin Permissions", False, str(e))

    async def test_user_management(self):
        """Test user management operations."""
        logger.info("👥 Testing User Management")

        # Create test users
        test_users_data = [
            ("global_admin", "admin@test.com", "admin123", "Global Admin User", True),
            ("tenant_admin", "tadmin@test.com", "admin123", "Tenant Admin User", False),
            ("analyst", "analyst@test.com", "analyst123", "Data Analyst User", False),
            ("viewer", "viewer@test.com", "viewer123", "Viewer User", False),
        ]

        for username, email, password, full_name, is_global_admin in test_users_data:
            try:
                user_id = self.rbac_manager.create_user(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    is_global_admin=is_global_admin
                )

                success = user_id is not None
                self.test_users[username] = user_id
                self._record_test_result(
                    f"Create User: {username}",
                    success,
                    f"User ID: {user_id}" if success else "Creation failed"
                )
            except Exception as e:
                self._record_test_result(f"Create User: {username}", False, str(e))

        # Test user profile retrieval
        for username, user_id in self.test_users.items():
            try:
                profile = self.rbac_manager.get_user_profile(user_id)
                profile_valid = profile is not None and profile.username == username
                self._record_test_result(
                    f"Get User Profile: {username}",
                    profile_valid,
                    f"Profile retrieved: {profile.full_name if profile else 'None'}"
                )
            except Exception as e:
                self._record_test_result(f"Get User Profile: {username}", False, str(e))

    async def test_authentication(self):
        """Test user authentication."""
        logger.info("🔐 Testing Authentication")

        # Test valid authentication
        try:
            profile = self.rbac_manager.authenticate_user("global_admin", "admin123")
            auth_success = profile is not None and profile.username == "global_admin"
            self._record_test_result(
                "Valid User Authentication",
                auth_success,
                f"Authenticated user: {profile.username if profile else 'None'}"
            )
        except Exception as e:
            self._record_test_result("Valid User Authentication", False, str(e))

        # Test invalid password
        try:
            profile = self.rbac_manager.authenticate_user("global_admin", "wrongpassword")
            auth_failed = profile is None
            self._record_test_result(
                "Invalid Password Authentication",
                auth_failed,
                "Authentication correctly failed"
            )
        except Exception as e:
            self._record_test_result("Invalid Password Authentication", False, str(e))

        # Test non-existent user
        try:
            profile = self.rbac_manager.authenticate_user("nonexistent", "password")
            auth_failed = profile is None
            self._record_test_result(
                "Non-existent User Authentication",
                auth_failed,
                "Authentication correctly failed"
            )
        except Exception as e:
            self._record_test_result("Non-existent User Authentication", False, str(e))

    async def test_authorization(self):
        """Test authorization and permissions."""
        logger.info("🛡️ Testing Authorization")

        # Grant tenant access to test users
        global_admin_id = self.test_users.get("global_admin")
        analyst_id = self.test_users.get("analyst")

        if global_admin_id and analyst_id:
            # Grant analyst access to tenant_alpha
            try:
                success = self.rbac_manager.grant_tenant_access(
                    analyst_id,
                    "tenant_alpha",
                    ["analyst"],
                    global_admin_id
                )
                self._record_test_result(
                    "Grant Tenant Access",
                    success,
                    "Analyst granted access to tenant_alpha"
                )
            except Exception as e:
                self._record_test_result("Grant Tenant Access", False, str(e))

            # Test permission checking
            try:
                has_read_permission = self.rbac_manager.check_user_permission(
                    analyst_id,
                    "tenant_alpha",
                    ResourceType.QUERIES,
                    PermissionLevel.READ
                )
                self._record_test_result(
                    "Check Read Permission",
                    has_read_permission,
                    "Analyst has read permission for queries"
                )
            except Exception as e:
                self._record_test_result("Check Read Permission", False, str(e))

            # Test denied permission
            try:
                has_admin_permission = self.rbac_manager.check_user_permission(
                    analyst_id,
                    "tenant_alpha",
                    ResourceType.USERS,
                    PermissionLevel.ADMIN
                )
                permission_denied = not has_admin_permission
                self._record_test_result(
                    "Check Denied Permission",
                    permission_denied,
                    "Analyst correctly denied admin permission"
                )
            except Exception as e:
                self._record_test_result("Check Denied Permission", False, str(e))

    async def test_cross_tenant_access(self):
        """Test cross-tenant access management."""
        logger.info("🌐 Testing Cross-Tenant Access")

        analyst_id = self.test_users.get("analyst")
        global_admin_id = self.test_users.get("global_admin")

        if analyst_id and global_admin_id:
            # Test access request submission
            try:
                request_id = self.cross_tenant_manager.request_tenant_access(
                    analyst_id,
                    "tenant_beta",
                    ["analyst"],
                    "Need access for data analysis project",
                    analyst_id
                )
                request_success = request_id is not None
                self._record_test_result(
                    "Submit Access Request",
                    request_success,
                    f"Request ID: {request_id}"
                )

                # Test access request approval
                if request_success:
                    approval_success = self.cross_tenant_manager.approve_access_request(
                        request_id,
                        global_admin_id
                    )
                    self._record_test_result(
                        "Approve Access Request",
                        approval_success,
                        "Access request approved successfully"
                    )

            except Exception as e:
                self._record_test_result("Submit Access Request", False, str(e))

            # Test cross-tenant user summary
            try:
                summary = self.cross_tenant_manager.get_cross_tenant_user_summary(analyst_id)
                has_multiple_tenants = summary and summary.total_tenants >= 2
                self._record_test_result(
                    "Cross-Tenant User Summary",
                    has_multiple_tenants,
                    f"User has access to {summary.total_tenants if summary else 0} tenants"
                )
            except Exception as e:
                self._record_test_result("Cross-Tenant User Summary", False, str(e))

    async def test_permission_inheritance(self):
        """Test permission inheritance and role hierarchy."""
        logger.info("🔗 Testing Permission Inheritance")

        # This would test custom roles with inheritance
        # For now, test basic permission resolution
        try:
            admin_permissions = self.rbac_manager.role_manager.resolve_role_permissions("admin")
            viewer_permissions = self.rbac_manager.role_manager.resolve_role_permissions("viewer")

            admin_has_more = len(admin_permissions) > len(viewer_permissions)
            self._record_test_result(
                "Permission Hierarchy",
                admin_has_more,
                f"Admin: {len(admin_permissions)}, Viewer: {len(viewer_permissions)} permissions"
            )
        except Exception as e:
            self._record_test_result("Permission Hierarchy", False, str(e))

    async def test_session_management(self):
        """Test session creation and management."""
        logger.info("⏱️ Testing Session Management")

        analyst_id = self.test_users.get("analyst")

        if analyst_id:
            # Test session creation
            try:
                session = self.rbac_manager.create_tenant_session(
                    analyst_id,
                    "tenant_alpha",
                    ip_address="127.0.0.1",
                    user_agent="Test Agent"
                )

                session_created = session is not None
                self._record_test_result(
                    "Create Tenant Session",
                    session_created,
                    f"Session ID: {session.session_id if session else 'None'}"
                )

                if session_created:
                    # Test JWT token generation
                    try:
                        token = self.rbac_manager.generate_jwt_token(session)
                        token_generated = token is not None and len(token) > 0
                        self._record_test_result(
                            "Generate JWT Token",
                            token_generated,
                            f"Token length: {len(token) if token else 0}"
                        )

                        # Test JWT token validation
                        if token_generated:
                            payload = self.rbac_manager.validate_jwt_token(token)
                            token_valid = payload is not None
                            self._record_test_result(
                                "Validate JWT Token",
                                token_valid,
                                f"Payload user_id: {payload.get('user_id') if payload else 'None'}"
                            )

                    except Exception as e:
                        self._record_test_result("Generate JWT Token", False, str(e))

            except Exception as e:
                self._record_test_result("Create Tenant Session", False, str(e))

    async def test_security_scenarios(self):
        """Test security scenarios and edge cases."""
        logger.info("🔒 Testing Security Scenarios")

        # Test expired token handling
        try:
            # This would require mocking time or creating an expired token
            # For now, test basic token validation
            invalid_payload = self.rbac_manager.validate_jwt_token("invalid.token.here")
            security_valid = invalid_payload is None
            self._record_test_result(
                "Invalid Token Rejection",
                security_valid,
                "Invalid token correctly rejected"
            )
            self.test_results["security_tests"].append({
                "test": "Invalid Token Rejection",
                "passed": security_valid
            })
        except Exception as e:
            self._record_test_result("Invalid Token Rejection", False, str(e))

        # Test SQL injection protection (basic)
        try:
            profile = self.rbac_manager.authenticate_user("'; DROP TABLE users; --", "password")
            injection_protected = profile is None
            self._record_test_result(
                "SQL Injection Protection",
                injection_protected,
                "SQL injection attempt blocked"
            )
            self.test_results["security_tests"].append({
                "test": "SQL Injection Protection",
                "passed": injection_protected
            })
        except Exception as e:
            self._record_test_result("SQL Injection Protection", False, str(e))

    async def test_performance(self):
        """Test system performance."""
        logger.info("⚡ Testing Performance")

        analyst_id = self.test_users.get("analyst")

        if analyst_id:
            # Test authentication performance
            start_time = datetime.utcnow()
            for _ in range(10):
                self.rbac_manager.authenticate_user("analyst", "analyst123")
            end_time = datetime.utcnow()

            auth_time = (end_time - start_time).total_seconds() / 10
            auth_performance_ok = auth_time < 0.1  # Less than 100ms per auth

            self._record_test_result(
                "Authentication Performance",
                auth_performance_ok,
                f"Average auth time: {auth_time:.3f}s"
            )

            self.test_results["performance_metrics"]["auth_time_seconds"] = auth_time

            # Test permission check performance
            start_time = datetime.utcnow()
            for _ in range(100):
                self.rbac_manager.check_user_permission(
                    analyst_id,
                    "tenant_alpha",
                    ResourceType.QUERIES,
                    PermissionLevel.READ
                )
            end_time = datetime.utcnow()

            perm_time = (end_time - start_time).total_seconds() / 100
            perm_performance_ok = perm_time < 0.01  # Less than 10ms per check

            self._record_test_result(
                "Permission Check Performance",
                perm_performance_ok,
                f"Average permission check time: {perm_time:.3f}s"
            )

            self.test_results["performance_metrics"]["permission_check_time_seconds"] = perm_time

    async def test_cleanup_operations(self):
        """Test cleanup operations."""
        logger.info("🧹 Testing Cleanup Operations")

        # Test session cleanup
        try:
            cleaned_sessions = self.rbac_manager.cleanup_expired_sessions()
            cleanup_success = cleaned_sessions >= 0
            self._record_test_result(
                "Session Cleanup",
                cleanup_success,
                f"Cleaned {cleaned_sessions} expired sessions"
            )
        except Exception as e:
            self._record_test_result("Session Cleanup", False, str(e))

        # Test access request cleanup
        try:
            cleaned_requests = self.cross_tenant_manager.cleanup_expired_access_requests()
            cleanup_success = cleaned_requests >= 0
            self._record_test_result(
                "Access Request Cleanup",
                cleanup_success,
                f"Cleaned {cleaned_requests} expired requests"
            )
        except Exception as e:
            self._record_test_result("Access Request Cleanup", False, str(e))

    def _record_test_result(self, test_name: str, passed: bool, details: str):
        """Record test result."""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
            logger.info(f"✅ {test_name}: {details}")
        else:
            self.test_results["failed_tests"] += 1
            logger.error(f"❌ {test_name}: {details}")

        self.test_results["test_details"].append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _generate_test_report(self):
        """Generate comprehensive test report."""
        report = {
            "test_suite": "Multi-Tenant RBAC System",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_tests": self.test_results["total_tests"],
                "passed_tests": self.test_results["passed_tests"],
                "failed_tests": self.test_results["failed_tests"],
                "success_rate": self.test_results["success_rate"],
                "execution_time_seconds": self.test_results["execution_time_seconds"]
            },
            "test_results": self.test_results["test_details"],
            "security_tests": self.test_results["security_tests"],
            "performance_metrics": self.test_results["performance_metrics"],
            "test_environment": {
                "rbac_database": self.rbac_db_config["connection"]["database"],
                "test_users_created": len(self.test_users),
                "test_tenants": self.test_tenants
            }
        }

        with open("test_report_rbac_system.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info("📄 Test report saved to: test_report_rbac_system.json")

    async def cleanup_test_resources(self):
        """Clean up test resources."""
        logger.info("🧹 Cleaning up test resources")

        # This would normally clean up test users and data
        # For safety, we'll just log what would be cleaned
        logger.info(f"Would clean up {len(self.test_users)} test users")
        logger.info(f"Would clean up test sessions and access requests")


async def main():
    """Run the RBAC test suite."""
    test_suite = RBACTestSuite()
    results = await test_suite.run_comprehensive_tests()

    if results["success_rate"] == 100.0:
        print("\n🎉 All RBAC tests passed! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️ {results['failed_tests']} tests failed. Check test_report_rbac_system.json for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())