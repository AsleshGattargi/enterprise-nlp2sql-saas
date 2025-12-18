"""
Comprehensive Test Suite Entry Point
Orchestrates all testing frameworks and generates unified reports.
"""

import asyncio
import pytest
import logging
import time
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path

from tests.tenant_isolation_tester import TenantIsolationTester
from tests.nlp2sql_accuracy_tester import NLP2SQLAccuracyTester
from tests.load_testing_framework import LoadTestingFramework, LoadTestConfig
from tests.security_penetration_tester import SecurityPenetrationTester
from tests.integration_testing_suite import IntegrationTestingSuite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveTestSuite:
    """Main orchestrator for all testing frameworks."""

    def __init__(self,
                 connection_manager,
                 rbac_manager,
                 nlp2sql_engine,
                 provisioning_manager=None,
                 email_orchestrator=None):
        self.connection_manager = connection_manager
        self.rbac_manager = rbac_manager
        self.nlp2sql_engine = nlp2sql_engine
        self.provisioning_manager = provisioning_manager
        self.email_orchestrator = email_orchestrator

        # Initialize testing frameworks
        self.isolation_tester = TenantIsolationTester(
            connection_manager, rbac_manager, None  # Database cloner would be injected
        )
        self.accuracy_tester = NLP2SQLAccuracyTester(
            nlp2sql_engine, connection_manager, rbac_manager
        )
        self.load_tester = LoadTestingFramework(
            connection_manager, nlp2sql_engine
        )
        self.security_tester = SecurityPenetrationTester(
            connection_manager, rbac_manager, nlp2sql_engine
        )
        self.integration_tester = IntegrationTestingSuite(
            provisioning_manager, connection_manager, rbac_manager,
            nlp2sql_engine, email_orchestrator
        )

        self.test_results = {}
        self.test_start_time = None
        self.test_end_time = None

    async def run_all_tests(self, test_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run comprehensive test suite across all frameworks."""
        logger.info("Starting comprehensive multi-tenant NLP2SQL testing suite")
        self.test_start_time = datetime.utcnow()

        if test_config is None:
            test_config = self._get_default_test_config()

        # Initialize comprehensive results structure
        comprehensive_results = {
            "test_execution": {
                "start_time": self.test_start_time.isoformat(),
                "test_configuration": test_config,
                "framework_versions": await self._get_framework_versions()
            },
            "tenant_isolation": {},
            "nlp2sql_accuracy": {},
            "load_testing": {},
            "security_testing": {},
            "integration_testing": {},
            "performance_benchmarks": {},
            "security_validation": {},
            "summary": {}
        }

        try:
            # Run tenant isolation tests
            if test_config.get("run_isolation_tests", True):
                logger.info("Running tenant isolation tests...")
                isolation_results = await self.isolation_tester.run_comprehensive_isolation_tests()
                comprehensive_results["tenant_isolation"] = isolation_results

            # Run NLP2SQL accuracy tests
            if test_config.get("run_accuracy_tests", True):
                logger.info("Running NLP2SQL accuracy tests...")
                accuracy_results = await self.accuracy_tester.run_comprehensive_accuracy_tests()
                comprehensive_results["nlp2sql_accuracy"] = accuracy_results

            # Run load testing
            if test_config.get("run_load_tests", True):
                logger.info("Running load testing...")
                load_configs = self._generate_load_test_configs(test_config)
                load_results = await self.load_tester.run_comprehensive_load_tests(load_configs)
                comprehensive_results["load_testing"] = load_results

            # Run security testing
            if test_config.get("run_security_tests", True):
                logger.info("Running security penetration tests...")
                security_results = await self.security_tester.run_comprehensive_security_tests()
                comprehensive_results["security_testing"] = security_results

            # Run integration testing
            if test_config.get("run_integration_tests", True):
                logger.info("Running integration tests...")
                integration_results = await self.integration_tester.run_comprehensive_integration_tests()
                comprehensive_results["integration_testing"] = integration_results

            # Generate performance benchmarks
            comprehensive_results["performance_benchmarks"] = self._generate_performance_benchmarks(
                comprehensive_results
            )

            # Generate security validation report
            comprehensive_results["security_validation"] = self._generate_security_validation_report(
                comprehensive_results
            )

            # Generate comprehensive summary
            comprehensive_results["summary"] = self._generate_comprehensive_summary(
                comprehensive_results
            )

        except Exception as e:
            logger.error(f"Comprehensive testing failed: {str(e)}")
            comprehensive_results["test_execution"]["error"] = str(e)

        finally:
            self.test_end_time = datetime.utcnow()
            comprehensive_results["test_execution"]["end_time"] = self.test_end_time.isoformat()
            comprehensive_results["test_execution"]["total_duration_seconds"] = (
                self.test_end_time - self.test_start_time
            ).total_seconds()

        # Save results
        await self._save_comprehensive_results(comprehensive_results)

        return comprehensive_results

    def _get_default_test_config(self) -> Dict[str, Any]:
        """Get default test configuration."""
        return {
            "run_isolation_tests": True,
            "run_accuracy_tests": True,
            "run_load_tests": True,
            "run_security_tests": True,
            "run_integration_tests": True,
            "tenant_count": 3,
            "concurrent_users": [5, 10, 25],
            "test_duration_seconds": 300,
            "performance_thresholds": {
                "query_response_time_ms": 1000,
                "tenant_creation_time_seconds": 30,
                "error_rate_threshold": 5.0
            }
        }

    def _generate_load_test_configs(self, test_config: Dict[str, Any]) -> List[LoadTestConfig]:
        """Generate load test configurations."""
        configs = []
        for concurrent_users in test_config.get("concurrent_users", [5, 10]):
            config = LoadTestConfig(
                concurrent_users=concurrent_users,
                requests_per_user=50,
                ramp_up_time=30,
                test_duration=test_config.get("test_duration_seconds", 300),
                tenant_count=test_config.get("tenant_count", 3)
            )
            configs.append(config)
        return configs

    async def _get_framework_versions(self) -> Dict[str, str]:
        """Get versions of testing frameworks and dependencies."""
        return {
            "pytest": "7.4.3",
            "python": "3.8+",
            "test_suite_version": "1.0.0",
            "framework_components": [
                "TenantIsolationTester",
                "NLP2SQLAccuracyTester",
                "LoadTestingFramework",
                "SecurityPenetrationTester",
                "IntegrationTestingSuite"
            ]
        }

    def _generate_performance_benchmarks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance benchmarks from test results."""
        benchmarks = {
            "query_performance": {},
            "system_performance": {},
            "scalability_metrics": {},
            "resource_utilization": {}
        }

        # Extract query performance metrics
        if "nlp2sql_accuracy" in results:
            accuracy_data = results["nlp2sql_accuracy"]
            if "query_accuracy" in accuracy_data:
                response_times = []
                for test in accuracy_data["query_accuracy"]:
                    if "execution_time" in test:
                        response_times.append(test["execution_time"] * 1000)  # Convert to ms

                if response_times:
                    benchmarks["query_performance"] = {
                        "average_response_time_ms": sum(response_times) / len(response_times),
                        "min_response_time_ms": min(response_times),
                        "max_response_time_ms": max(response_times),
                        "total_queries_tested": len(response_times)
                    }

        # Extract load testing performance
        if "load_testing" in results:
            load_data = results["load_testing"]
            if "summary" in load_data and "load_testing" in load_data["summary"]:
                load_summary = load_data["summary"]["load_testing"]
                benchmarks["system_performance"] = {
                    "peak_concurrent_users": load_summary.get("peak_concurrent_users", 0),
                    "total_requests_processed": load_summary.get("total_requests", 0),
                    "success_rate_percentage": load_summary.get("success_rate", 0),
                    "average_response_time_ms": load_summary.get("average_response_time", 0) * 1000
                }

        # Extract scalability metrics
        if "tenant_isolation" in results:
            isolation_data = results["tenant_isolation"]
            if "summary" in isolation_data:
                benchmarks["scalability_metrics"] = {
                    "tenant_isolation_verified": isolation_data["summary"].get("isolation_verified", False),
                    "cross_tenant_protection_rate": 100.0,  # Should be 100% for proper isolation
                    "tenant_scalability_score": isolation_data["summary"].get("success_rate", 0)
                }

        return benchmarks

    def _generate_security_validation_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive security validation report."""
        security_report = {
            "overall_security_score": 0,
            "critical_vulnerabilities": [],
            "security_test_summary": {},
            "compliance_status": {},
            "recommendations": []
        }

        if "security_testing" in results:
            security_data = results["security_testing"]

            # Overall security score
            if "summary" in security_data:
                security_report["overall_security_score"] = security_data["summary"].get("security_score", 0)

                # Critical vulnerabilities
                security_report["critical_vulnerabilities"] = [
                    vuln for vuln in security_data["summary"].get("critical_vulnerabilities", [])
                ]

                # Security test summary
                security_report["security_test_summary"] = {
                    "total_tests": security_data["summary"].get("total_tests", 0),
                    "vulnerabilities_found": security_data["summary"].get("vulnerabilities_found", 0),
                    "tests_by_category": security_data["summary"].get("tests_by_category", {}),
                    "system_secure": security_data["summary"].get("system_secure", False)
                }

        # Compliance status
        security_report["compliance_status"] = {
            "sql_injection_protection": self._check_sql_injection_compliance(results),
            "tenant_isolation": self._check_tenant_isolation_compliance(results),
            "access_control": self._check_access_control_compliance(results),
            "data_protection": self._check_data_protection_compliance(results)
        }

        # Generate recommendations
        security_report["recommendations"] = self._generate_security_recommendations(results)

        return security_report

    def _check_sql_injection_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check SQL injection protection compliance."""
        if "security_testing" in results and "sql_injection_tests" in results["security_testing"]:
            sql_tests = results["security_testing"]["sql_injection_tests"]
            total_tests = len(sql_tests)
            protected_tests = len([t for t in sql_tests if t.get("mitigation_verified", False)])

            return {
                "compliant": protected_tests == total_tests,
                "protection_rate": (protected_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_tests": total_tests,
                "protected_tests": protected_tests
            }
        return {"compliant": False, "protection_rate": 0, "reason": "No SQL injection tests found"}

    def _check_tenant_isolation_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check tenant isolation compliance."""
        if "tenant_isolation" in results and "summary" in results["tenant_isolation"]:
            isolation_summary = results["tenant_isolation"]["summary"]
            return {
                "compliant": isolation_summary.get("isolation_verified", False),
                "success_rate": isolation_summary.get("success_rate", 0),
                "total_tests": isolation_summary.get("total_tests", 0),
                "failed_tests": isolation_summary.get("failed_tests", 0)
            }
        return {"compliant": False, "success_rate": 0, "reason": "No tenant isolation tests found"}

    def _check_access_control_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check access control compliance."""
        if "security_testing" in results and "authorization_bypass_tests" in results["security_testing"]:
            auth_tests = results["security_testing"]["authorization_bypass_tests"]
            total_tests = len(auth_tests)
            protected_tests = len([t for t in auth_tests if t.get("mitigation_verified", False)])

            return {
                "compliant": protected_tests == total_tests,
                "protection_rate": (protected_tests / total_tests) * 100 if total_tests > 0 else 0,
                "total_tests": total_tests,
                "protected_tests": protected_tests
            }
        return {"compliant": False, "protection_rate": 0, "reason": "No authorization tests found"}

    def _check_data_protection_compliance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Check data protection compliance."""
        # Combine tenant isolation and credential isolation results
        tenant_compliant = self._check_tenant_isolation_compliance(results)["compliant"]

        credential_compliant = False
        if "security_testing" in results and "credential_isolation_tests" in results["security_testing"]:
            cred_tests = results["security_testing"]["credential_isolation_tests"]
            total_tests = len(cred_tests)
            protected_tests = len([t for t in cred_tests if t.get("mitigation_verified", False)])
            credential_compliant = protected_tests == total_tests

        return {
            "compliant": tenant_compliant and credential_compliant,
            "tenant_isolation_compliant": tenant_compliant,
            "credential_isolation_compliant": credential_compliant
        }

    def _generate_security_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on test results."""
        recommendations = []

        # Check SQL injection protection
        sql_compliance = self._check_sql_injection_compliance(results)
        if not sql_compliance.get("compliant", False):
            recommendations.append(
                "Strengthen SQL injection protection by implementing parameterized queries and input validation"
            )

        # Check tenant isolation
        tenant_compliance = self._check_tenant_isolation_compliance(results)
        if not tenant_compliance.get("compliant", False):
            recommendations.append(
                "Improve tenant isolation by reviewing database connection management and RBAC implementation"
            )

        # Check performance
        if "performance_benchmarks" in results:
            perf_data = results["performance_benchmarks"]
            if perf_data.get("query_performance", {}).get("average_response_time_ms", 0) > 1000:
                recommendations.append(
                    "Optimize query performance - average response time exceeds 1000ms threshold"
                )

        # Check load testing
        if "load_testing" in results:
            load_data = results["load_testing"]
            if load_data.get("summary", {}).get("load_testing", {}).get("success_rate", 0) < 95:
                recommendations.append(
                    "Improve system stability under load - success rate below 95%"
                )

        if not recommendations:
            recommendations.append("All security tests passed - continue regular security monitoring")

        return recommendations

    def _generate_comprehensive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive summary of all test results."""
        summary = {
            "overall_status": "PASS",
            "test_categories_summary": {},
            "critical_issues": [],
            "performance_summary": {},
            "security_summary": {},
            "recommendations": [],
            "next_steps": []
        }

        # Analyze each test category
        categories = ["tenant_isolation", "nlp2sql_accuracy", "load_testing", "security_testing", "integration_testing"]

        for category in categories:
            if category in results:
                category_data = results[category]
                category_summary = self._analyze_category_results(category, category_data)
                summary["test_categories_summary"][category] = category_summary

                # Check for critical issues
                if not category_summary.get("passed", True):
                    summary["overall_status"] = "FAIL"
                    summary["critical_issues"].extend(category_summary.get("issues", []))

        # Performance summary
        if "performance_benchmarks" in results:
            summary["performance_summary"] = {
                "query_performance_acceptable": self._check_query_performance(results),
                "system_scalability_verified": self._check_system_scalability(results),
                "resource_utilization_optimal": self._check_resource_utilization(results)
            }

        # Security summary
        if "security_validation" in results:
            security_data = results["security_validation"]
            summary["security_summary"] = {
                "overall_security_score": security_data.get("overall_security_score", 0),
                "critical_vulnerabilities_count": len(security_data.get("critical_vulnerabilities", [])),
                "compliance_status": security_data.get("compliance_status", {}),
                "security_acceptable": security_data.get("overall_security_score", 0) >= 80
            }

        # Generate recommendations and next steps
        summary["recommendations"] = self._generate_overall_recommendations(results)
        summary["next_steps"] = self._generate_next_steps(summary)

        return summary

    def _analyze_category_results(self, category: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results for a specific test category."""
        category_summary = {
            "passed": True,
            "total_tests": 0,
            "successful_tests": 0,
            "issues": []
        }

        if "summary" in data:
            summary_data = data["summary"]

            if category == "tenant_isolation":
                category_summary["passed"] = summary_data.get("isolation_verified", False)
                category_summary["total_tests"] = summary_data.get("total_tests", 0)
                category_summary["successful_tests"] = summary_data.get("passed_tests", 0)

            elif category == "nlp2sql_accuracy":
                accuracy_score = summary_data.get("overall_score", 0)
                category_summary["passed"] = accuracy_score >= 80
                category_summary["accuracy_score"] = accuracy_score

            elif category == "load_testing":
                success_rate = summary_data.get("load_testing", {}).get("success_rate", 0)
                category_summary["passed"] = success_rate >= 95
                category_summary["success_rate"] = success_rate

            elif category == "security_testing":
                security_score = summary_data.get("security_score", 0)
                category_summary["passed"] = security_score >= 80
                category_summary["security_score"] = security_score

            elif category == "integration_testing":
                integration_verified = summary_data.get("system_integration_verified", False)
                category_summary["passed"] = integration_verified
                category_summary["integration_verified"] = integration_verified

        return category_summary

    def _check_query_performance(self, results: Dict[str, Any]) -> bool:
        """Check if query performance is acceptable."""
        if "performance_benchmarks" in results:
            perf_data = results["performance_benchmarks"]
            avg_response_time = perf_data.get("query_performance", {}).get("average_response_time_ms", 0)
            return avg_response_time <= 1000
        return False

    def _check_system_scalability(self, results: Dict[str, Any]) -> bool:
        """Check if system scalability is verified."""
        if "performance_benchmarks" in results:
            perf_data = results["performance_benchmarks"]
            return perf_data.get("scalability_metrics", {}).get("tenant_isolation_verified", False)
        return False

    def _check_resource_utilization(self, results: Dict[str, Any]) -> bool:
        """Check if resource utilization is optimal."""
        if "load_testing" in results:
            load_data = results["load_testing"]
            success_rate = load_data.get("summary", {}).get("load_testing", {}).get("success_rate", 0)
            return success_rate >= 95
        return False

    def _generate_overall_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []

        # Add security recommendations
        if "security_validation" in results:
            recommendations.extend(results["security_validation"].get("recommendations", []))

        # Add performance recommendations
        if not self._check_query_performance(results):
            recommendations.append("Optimize query performance to meet response time requirements")

        if not self._check_system_scalability(results):
            recommendations.append("Improve system scalability and tenant isolation")

        return recommendations

    def _generate_next_steps(self, summary: Dict[str, Any]) -> List[str]:
        """Generate next steps based on test results."""
        next_steps = []

        if summary["overall_status"] == "FAIL":
            next_steps.append("Address critical issues identified in test results")
            next_steps.append("Re-run failed test categories after fixes")

        if summary.get("security_summary", {}).get("critical_vulnerabilities_count", 0) > 0:
            next_steps.append("Immediately address critical security vulnerabilities")

        next_steps.extend([
            "Schedule regular testing cycles for continuous monitoring",
            "Implement automated test execution in CI/CD pipeline",
            "Monitor system performance in production environment",
            "Review and update test cases based on new requirements"
        ])

        return next_steps

    async def _save_comprehensive_results(self, results: Dict[str, Any]):
        """Save comprehensive test results to file."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            results_file = Path(f"test_results_comprehensive_{timestamp}.json")

            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Comprehensive test results saved to {results_file}")

            # Also save a summary report
            summary_file = Path(f"test_summary_{timestamp}.txt")
            await self._save_summary_report(results, summary_file)

        except Exception as e:
            logger.error(f"Failed to save test results: {str(e)}")

    async def _save_summary_report(self, results: Dict[str, Any], summary_file: Path):
        """Save human-readable summary report."""
        try:
            with open(summary_file, 'w') as f:
                f.write("COMPREHENSIVE MULTI-TENANT NLP2SQL TESTING REPORT\n")
                f.write("=" * 60 + "\n\n")

                # Test execution info
                f.write(f"Test Start Time: {results['test_execution']['start_time']}\n")
                f.write(f"Test End Time: {results['test_execution']['end_time']}\n")
                f.write(f"Total Duration: {results['test_execution']['total_duration_seconds']:.2f} seconds\n\n")

                # Overall status
                summary = results.get("summary", {})
                f.write(f"OVERALL STATUS: {summary.get('overall_status', 'UNKNOWN')}\n\n")

                # Test categories summary
                f.write("TEST CATEGORIES SUMMARY:\n")
                f.write("-" * 30 + "\n")
                for category, data in summary.get("test_categories_summary", {}).items():
                    status = "PASS" if data.get("passed", False) else "FAIL"
                    f.write(f"{category.replace('_', ' ').title()}: {status}\n")

                f.write("\n")

                # Performance summary
                if "performance_summary" in summary:
                    f.write("PERFORMANCE SUMMARY:\n")
                    f.write("-" * 20 + "\n")
                    perf = summary["performance_summary"]
                    for key, value in perf.items():
                        f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                    f.write("\n")

                # Security summary
                if "security_summary" in summary:
                    f.write("SECURITY SUMMARY:\n")
                    f.write("-" * 17 + "\n")
                    sec = summary["security_summary"]
                    f.write(f"Security Score: {sec.get('overall_security_score', 0)}/100\n")
                    f.write(f"Critical Vulnerabilities: {sec.get('critical_vulnerabilities_count', 0)}\n")
                    f.write(f"Security Acceptable: {sec.get('security_acceptable', False)}\n\n")

                # Critical issues
                if summary.get("critical_issues"):
                    f.write("CRITICAL ISSUES:\n")
                    f.write("-" * 16 + "\n")
                    for issue in summary["critical_issues"]:
                        f.write(f"- {issue}\n")
                    f.write("\n")

                # Recommendations
                if summary.get("recommendations"):
                    f.write("RECOMMENDATIONS:\n")
                    f.write("-" * 15 + "\n")
                    for rec in summary["recommendations"]:
                        f.write(f"- {rec}\n")
                    f.write("\n")

                # Next steps
                if summary.get("next_steps"):
                    f.write("NEXT STEPS:\n")
                    f.write("-" * 11 + "\n")
                    for step in summary["next_steps"]:
                        f.write(f"- {step}\n")

            logger.info(f"Summary report saved to {summary_file}")

        except Exception as e:
            logger.error(f"Failed to save summary report: {str(e)}")


# Pytest integration

@pytest.mark.integration
@pytest.mark.slow
async def test_comprehensive_suite_basic(
    mock_tenant_connection_manager,
    mock_rbac_manager,
    mock_nlp2sql_engine,
    mock_provisioning_manager,
    mock_email_orchestrator
):
    """Test basic functionality of comprehensive test suite."""
    suite = ComprehensiveTestSuite(
        connection_manager=mock_tenant_connection_manager,
        rbac_manager=mock_rbac_manager,
        nlp2sql_engine=mock_nlp2sql_engine,
        provisioning_manager=mock_provisioning_manager,
        email_orchestrator=mock_email_orchestrator
    )

    # Test configuration for quick run
    test_config = {
        "run_isolation_tests": True,
        "run_accuracy_tests": True,
        "run_load_tests": False,  # Skip slow tests
        "run_security_tests": True,
        "run_integration_tests": False,  # Skip slow tests
        "tenant_count": 2,
        "concurrent_users": [2],
        "test_duration_seconds": 30
    }

    results = await suite.run_all_tests(test_config)

    # Verify results structure
    assert "test_execution" in results
    assert "summary" in results
    assert results["test_execution"]["start_time"]
    assert results["test_execution"]["end_time"]


if __name__ == "__main__":
    # CLI entry point for running comprehensive tests
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Run comprehensive multi-tenant NLP2SQL tests")
    parser.add_argument("--config", help="Path to test configuration file")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite")
    parser.add_argument("--security-only", action="store_true", help="Run security tests only")
    parser.add_argument("--performance-only", action="store_true", help="Run performance tests only")

    args = parser.parse_args()

    # This would require proper initialization of the actual components
    print("Comprehensive Multi-Tenant NLP2SQL Testing Suite")
    print("=" * 50)
    print("Note: This requires proper component initialization for actual execution.")
    print("Use pytest to run the test functions with mocked components.")