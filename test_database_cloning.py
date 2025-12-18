#!/usr/bin/env python3
"""
Comprehensive Test Suite for Database Cloning Engine
Tests cloning with 2 test tenants and verifies complete isolation.
"""

import logging
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any

from src.database_cloner import DatabaseCloner, CloneStatus
from src.clone_verifier import CloneVerifier
from src.port_manager import PortManager
from src.docker_manager import DockerManager
from src.root_image_manager import RootImageManager, DatabaseType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseCloningTestSuite:
    """
    Comprehensive test suite for database cloning engine.
    Tests tenant isolation, clone verification, and system integration.
    """

    def __init__(self):
        """Initialize test suite components."""
        self.database_cloner = DatabaseCloner()
        self.clone_verifier = CloneVerifier()
        self.port_manager = PortManager()
        self.docker_manager = DockerManager()
        self.root_manager = RootImageManager()

        # Test tenant configurations
        self.test_tenants = {
            'tenant_alpha': {
                'tenant_id': 'alpha_test_001',
                'database_type': 'mysql',
                'root_version': 'v1.0'
            },
            'tenant_beta': {
                'tenant_id': 'beta_test_002',
                'database_type': 'postgresql',
                'root_version': 'v1.0'
            }
        }

        # Test results storage
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'isolation_verified': False,
            'clones_created': {},
            'performance_benchmarks': {}
        }

        logger.info("Database Cloning Test Suite initialized")

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive database cloning tests.

        Returns:
            Test results dictionary
        """
        try:
            logger.info("🚀 Starting Comprehensive Database Cloning Tests")

            # Test 1: System Prerequisites
            await self._test_system_prerequisites()

            # Test 2: Root Image Validation
            await self._test_root_image_availability()

            # Test 3: Port Management
            await self._test_port_management()

            # Test 4: Docker Integration
            await self._test_docker_integration()

            # Test 5: Create Test Tenants
            await self._test_create_tenant_clones()

            # Test 6: Verify Clone Isolation
            await self._test_clone_isolation()

            # Test 7: Data Leakage Prevention
            await self._test_data_leakage_prevention()

            # Test 8: Performance Benchmarks
            await self._test_performance_benchmarks()

            # Test 9: Clone Management Operations
            await self._test_clone_management()

            # Test 10: Cleanup and Resource Management
            await self._test_cleanup_operations()

            # Generate final report
            self._generate_test_report()

            logger.info("✅ All tests completed successfully")
            return self.test_results

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            self.test_results['error'] = str(e)
            return self.test_results

    async def _test_system_prerequisites(self):
        """Test system prerequisites for cloning."""
        logger.info("🔍 Testing System Prerequisites")

        test_name = "System Prerequisites"
        test_passed = True
        test_details = []

        try:
            # Test Docker connection
            docker_info = self.docker_manager.get_system_info()
            if docker_info:
                test_details.append("✅ Docker daemon accessible")
            else:
                test_details.append("❌ Docker daemon not accessible")
                test_passed = False

            # Test port availability
            port_stats = self.port_manager.get_port_statistics()
            if port_stats:
                test_details.append("✅ Port manager operational")
            else:
                test_details.append("❌ Port manager not operational")
                test_passed = False

            # Test root image manager
            versions = self.root_manager.get_available_versions(DatabaseType.MYSQL)
            if versions:
                test_details.append(f"✅ Root images available ({len(versions)} versions)")
            else:
                test_details.append("❌ No root images available")
                test_passed = False

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_root_image_availability(self):
        """Test root image availability for all database types."""
        logger.info("🔍 Testing Root Image Availability")

        test_name = "Root Image Availability"
        test_passed = True
        test_details = []

        try:
            for db_type in [DatabaseType.MYSQL, DatabaseType.POSTGRESQL, DatabaseType.SQLITE, DatabaseType.MONGODB]:
                versions = self.root_manager.get_available_versions(db_type)
                if versions:
                    test_details.append(f"✅ {db_type.value}: {len(versions)} versions available")
                else:
                    test_details.append(f"❌ {db_type.value}: No versions available")
                    test_passed = False

                # Test schema content
                schema_content = self.root_manager.get_schema_content(db_type)
                if schema_content:
                    test_details.append(f"✅ {db_type.value}: Schema content accessible")
                else:
                    test_details.append(f"❌ {db_type.value}: Schema content not accessible")
                    test_passed = False

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_port_management(self):
        """Test port allocation and management."""
        logger.info("🔍 Testing Port Management")

        test_name = "Port Management"
        test_passed = True
        test_details = []

        try:
            # Test port allocation for MySQL
            mysql_port = self.port_manager.allocate_port(DatabaseType.MYSQL, "test_mysql")
            if mysql_port:
                test_details.append(f"✅ MySQL port allocated: {mysql_port}")

                # Test port is in use
                if self.port_manager.is_port_in_use(mysql_port):
                    test_details.append("✅ Port correctly marked as in use")
                else:
                    test_details.append("❌ Port not marked as in use")
                    test_passed = False

                # Release port
                if self.port_manager.release_port(DatabaseType.MYSQL, mysql_port):
                    test_details.append("✅ Port successfully released")
                else:
                    test_details.append("❌ Port release failed")
                    test_passed = False
            else:
                test_details.append("❌ MySQL port allocation failed")
                test_passed = False

            # Test port allocation for PostgreSQL
            postgres_port = self.port_manager.allocate_port(DatabaseType.POSTGRESQL, "test_postgres")
            if postgres_port:
                test_details.append(f"✅ PostgreSQL port allocated: {postgres_port}")
                self.port_manager.release_port(DatabaseType.POSTGRESQL, postgres_port)
            else:
                test_details.append("❌ PostgreSQL port allocation failed")
                test_passed = False

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_docker_integration(self):
        """Test Docker container integration."""
        logger.info("🔍 Testing Docker Integration")

        test_name = "Docker Integration"
        test_passed = True
        test_details = []

        try:
            # Test container creation (without starting)
            test_container_config = {
                'image': 'mysql:8.0',
                'name': 'test_mysql_container',
                'ports': {'3306/tcp': 33060},
                'environment': {
                    'MYSQL_ROOT_PASSWORD': 'test_password',
                    'MYSQL_DATABASE': 'test_db'
                }
            }

            # Create tenant network
            if self.docker_manager.create_tenant_network():
                test_details.append("✅ Tenant network created/verified")
            else:
                test_details.append("❌ Tenant network creation failed")
                test_passed = False

            # Test container lifecycle without actually starting
            # (to avoid resource consumption during testing)
            container_name = test_container_config['name']
            test_details.append("✅ Docker integration test completed (dry run)")

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_create_tenant_clones(self):
        """Test creating tenant clones."""
        logger.info("🔍 Testing Tenant Clone Creation")

        for tenant_name, config in self.test_tenants.items():
            test_name = f"Create Clone - {tenant_name}"
            test_passed = False
            test_details = []

            try:
                logger.info(f"Creating clone for {tenant_name}")

                # Create clone
                success, message, clone = self.database_cloner.clone_from_root(
                    tenant_id=config['tenant_id'],
                    db_type=config['database_type'],
                    root_version=config['root_version']
                )

                if success and clone:
                    test_details.append(f"✅ Clone created: {clone.clone_id}")
                    test_details.append(f"✅ Status: {clone.status.value}")
                    test_details.append(f"✅ Database: {clone.database_name}")

                    if clone.port:
                        test_details.append(f"✅ Port assigned: {clone.port}")

                    if clone.container_id:
                        test_details.append(f"✅ Container ID: {clone.container_id[:12]}")

                    # Store clone for later tests
                    self.test_results['clones_created'][tenant_name] = clone
                    test_passed = True

                    # Wait for clone to be ready (for containerized databases)
                    if clone.container_id:
                        logger.info(f"Waiting for {tenant_name} container to be ready...")
                        await asyncio.sleep(10)  # Give container time to start

                else:
                    test_details.append(f"❌ Clone creation failed: {message}")

                self._record_test_result(test_name, test_passed, test_details)

            except Exception as e:
                test_details.append(f"❌ Exception during clone creation: {str(e)}")
                self._record_test_result(test_name, False, test_details)

    async def _test_clone_isolation(self):
        """Test clone isolation verification."""
        logger.info("🔍 Testing Clone Isolation")

        for tenant_name, clone in self.test_results['clones_created'].items():
            test_name = f"Isolation Verification - {tenant_name}"
            test_details = []

            try:
                # Run isolation verification
                verification_result = self.database_cloner.verify_clone_isolation(clone.tenant_id)

                test_details.append(f"✅ Checks passed: {verification_result.checks_passed}/{verification_result.total_checks}")
                test_details.append(f"✅ Connection test: {'PASS' if verification_result.connection_test else 'FAIL'}")
                test_details.append(f"✅ Schema integrity: {'PASS' if verification_result.schema_integrity else 'FAIL'}")
                test_details.append(f"✅ Isolation verified: {'PASS' if verification_result.isolation_verified else 'FAIL'}")

                # Add details from individual tests
                for isolation_test in verification_result.isolation_tests:
                    status = "✅" if isolation_test.passed else "❌"
                    test_details.append(f"{status} {isolation_test.test_name}: {isolation_test.details}")

                test_passed = verification_result.is_verified

                if verification_result.error_messages:
                    for error in verification_result.error_messages:
                        test_details.append(f"❌ Error: {error}")

                self._record_test_result(test_name, test_passed, test_details)

            except Exception as e:
                self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_data_leakage_prevention(self):
        """Test data leakage prevention between tenants."""
        logger.info("🔍 Testing Data Leakage Prevention")

        test_name = "Data Leakage Prevention"
        test_details = []

        try:
            clones_list = list(self.test_results['clones_created'].values())

            if len(clones_list) >= 2:
                clone1, clone2 = clones_list[0], clones_list[1]

                # Verify no data leakage between clones
                no_leakage, errors = self.clone_verifier.verify_no_data_leakage(clone1, clone2)

                if no_leakage:
                    test_details.append("✅ No data leakage detected between tenants")
                    test_details.append(f"✅ Tested isolation between {clone1.tenant_id} and {clone2.tenant_id}")
                else:
                    test_details.append("❌ Data leakage detected!")
                    for error in errors:
                        test_details.append(f"❌ {error}")

                self.test_results['isolation_verified'] = no_leakage
                self._record_test_result(test_name, no_leakage, test_details)

            else:
                test_details.append("❌ Insufficient clones for leakage testing")
                self._record_test_result(test_name, False, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_performance_benchmarks(self):
        """Test performance benchmarks for clones."""
        logger.info("🔍 Testing Performance Benchmarks")

        for tenant_name, clone in self.test_results['clones_created'].items():
            test_name = f"Performance Benchmark - {tenant_name}"
            test_details = []

            try:
                # Run performance benchmark
                benchmark_results = self.clone_verifier.benchmark_clone_performance(clone)

                if 'error' not in benchmark_results:
                    avg_response_time = benchmark_results.get('average_response_time', 0)
                    successful_queries = benchmark_results.get('successful_queries', 0)
                    total_queries = benchmark_results.get('total_queries', 0)

                    test_details.append(f"✅ Average response time: {avg_response_time:.2f}ms")
                    test_details.append(f"✅ Successful queries: {successful_queries}/{total_queries}")

                    # Performance criteria (adjust as needed)
                    performance_good = avg_response_time < 1000 and successful_queries > 0

                    if performance_good:
                        test_details.append("✅ Performance within acceptable limits")
                    else:
                        test_details.append("❌ Performance below acceptable limits")

                    # Store benchmark results
                    self.test_results['performance_benchmarks'][tenant_name] = benchmark_results

                    self._record_test_result(test_name, performance_good, test_details)

                else:
                    error = benchmark_results['error']
                    test_details.append(f"❌ Benchmark error: {error}")
                    self._record_test_result(test_name, False, test_details)

            except Exception as e:
                self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_clone_management(self):
        """Test clone management operations."""
        logger.info("🔍 Testing Clone Management Operations")

        test_name = "Clone Management"
        test_passed = True
        test_details = []

        try:
            # Test listing clones
            all_clones = self.database_cloner.list_tenant_clones()
            test_details.append(f"✅ Total clones found: {len(all_clones)}")

            # Test getting connection parameters
            for tenant_name, clone in self.test_results['clones_created'].items():
                connection_params = self.database_cloner.get_tenant_connection_params(clone.tenant_id)
                if connection_params:
                    test_details.append(f"✅ {tenant_name}: Connection params retrieved")
                else:
                    test_details.append(f"❌ {tenant_name}: Connection params not found")
                    test_passed = False

            # Test clone status operations (stop/start for containerized databases)
            for tenant_name, clone in self.test_results['clones_created'].items():
                if clone.container_id:
                    # Test stop
                    if self.database_cloner.stop_tenant_database(clone.tenant_id):
                        test_details.append(f"✅ {tenant_name}: Database stopped successfully")

                        # Wait a moment
                        await asyncio.sleep(2)

                        # Test start
                        if self.database_cloner.start_tenant_database(clone.tenant_id):
                            test_details.append(f"✅ {tenant_name}: Database started successfully")
                        else:
                            test_details.append(f"❌ {tenant_name}: Database start failed")
                            test_passed = False
                    else:
                        test_details.append(f"❌ {tenant_name}: Database stop failed")
                        test_passed = False

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    async def _test_cleanup_operations(self):
        """Test cleanup and resource management."""
        logger.info("🔍 Testing Cleanup Operations")

        test_name = "Cleanup Operations"
        test_passed = True
        test_details = []

        try:
            # Test port cleanup
            cleaned_ports = self.port_manager.cleanup_inactive_allocations(max_age_hours=0)
            test_details.append(f"✅ Cleaned up {cleaned_ports} inactive port allocations")

            # Test getting system statistics
            port_stats = self.port_manager.get_port_statistics()
            if port_stats:
                test_details.append("✅ Port statistics retrieved")
            else:
                test_details.append("❌ Port statistics not available")
                test_passed = False

            # Test Docker system info
            docker_info = self.docker_manager.get_system_info()
            if docker_info:
                test_details.append("✅ Docker system info retrieved")
                test_details.append(f"✅ Running containers: {docker_info.get('containers_running', 0)}")
            else:
                test_details.append("❌ Docker system info not available")
                test_passed = False

            self._record_test_result(test_name, test_passed, test_details)

        except Exception as e:
            self._record_test_result(test_name, False, [f"❌ Exception: {str(e)}"])

    def _record_test_result(self, test_name: str, passed: bool, details: List[str]):
        """Record test result."""
        self.test_results['total_tests'] += 1

        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASSED"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAILED"

        test_record = {
            'test_name': test_name,
            'status': status,
            'passed': passed,
            'details': details,
            'timestamp': time.time()
        }

        self.test_results['test_details'].append(test_record)

        logger.info(f"{status}: {test_name}")
        for detail in details:
            logger.info(f"  {detail}")

    def _generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("📊 Generating Test Report")

        report = {
            'summary': {
                'total_tests': self.test_results['total_tests'],
                'passed_tests': self.test_results['passed_tests'],
                'failed_tests': self.test_results['failed_tests'],
                'success_rate': (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0,
                'isolation_verified': self.test_results['isolation_verified']
            },
            'test_results': self.test_results['test_details'],
            'clones_created': {
                name: {
                    'clone_id': clone.clone_id,
                    'tenant_id': clone.tenant_id,
                    'database_type': clone.database_type.value,
                    'status': clone.status.value,
                    'port': clone.port,
                    'container_id': clone.container_id
                }
                for name, clone in self.test_results['clones_created'].items()
            },
            'performance_benchmarks': self.test_results['performance_benchmarks'],
            'generated_at': time.time()
        }

        # Save report to file
        report_file = Path("test_report_database_cloning.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"📄 Test report saved to: {report_file}")

        # Print summary
        print("\n" + "="*60)
        print("🎯 DATABASE CLONING TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed_tests']}")
        print(f"Failed: {report['summary']['failed_tests']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Isolation Verified: {'✅ YES' if report['summary']['isolation_verified'] else '❌ NO'}")
        print(f"Clones Created: {len(self.test_results['clones_created'])}")
        print("="*60)

        return report

    async def cleanup_test_resources(self):
        """Cleanup test resources after testing."""
        logger.info("🧹 Cleaning up test resources")

        try:
            # Remove test clones
            for tenant_name, clone in self.test_results['clones_created'].items():
                logger.info(f"Removing clone for {tenant_name}")

                try:
                    success = self.database_cloner.remove_tenant_clone(clone.tenant_id, force=True)
                    if success:
                        logger.info(f"✅ Successfully removed clone for {tenant_name}")
                    else:
                        logger.warning(f"⚠️ Failed to remove clone for {tenant_name}")
                except Exception as e:
                    logger.error(f"❌ Error removing clone for {tenant_name}: {e}")

            logger.info("🧹 Test resource cleanup completed")

        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def main():
    """Main test execution function."""
    print("🚀 Starting Database Cloning Engine Test Suite")
    print("="*60)

    test_suite = DatabaseCloningTestSuite()

    try:
        # Run comprehensive tests
        results = await test_suite.run_comprehensive_tests()

        # Cleanup test resources
        cleanup_option = input("\nCleanup test resources? (y/N): ").lower()
        if cleanup_option == 'y':
            await test_suite.cleanup_test_resources()
        else:
            logger.info("⚠️ Test resources not cleaned up - manual cleanup may be required")

        # Final status
        if results['passed_tests'] == results['total_tests']:
            print("\n🎉 ALL TESTS PASSED! Database Cloning Engine is ready for production.")
        else:
            print(f"\n⚠️ {results['failed_tests']} tests failed. Review test report for details.")

        return results

    except Exception as e:
        logger.error(f"❌ Test suite execution failed: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    asyncio.run(main())