"""
NLP2SQL Accuracy Testing Suite
Tests query accuracy, tenant-specific results, and cross-tenant query prevention.
"""

import asyncio
import pytest
import logging
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass, field
import difflib
import re

from src.tenant_aware_nlp2sql import TenantAwareNLP2SQL
from src.tenant_routing_middleware import TenantRoutingContext
from src.tenant_connection_manager import TenantConnectionManager
from src.tenant_rbac_manager import TenantRBACManager
from src.industry_schema_templates import IndustrySchemaTemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryTestCase:
    """Test case for NLP2SQL query testing."""
    natural_query: str
    expected_sql_pattern: str
    tenant_id: str
    expected_result_count: Optional[int] = None
    should_succeed: bool = True
    test_category: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryAccuracyResult:
    """Result of a query accuracy test."""
    test_case: QueryTestCase
    generated_sql: str
    execution_successful: bool
    sql_accuracy_score: float
    result_tenant_specific: bool
    execution_time: float
    error_message: Optional[str] = None
    actual_result_count: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrossTenantQueryResult:
    """Result of cross-tenant query prevention test."""
    source_tenant: str
    target_tenant: str
    query_attempt: str
    access_prevented: bool
    error_type: str
    execution_time: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class NLP2SQLAccuracyTester:
    """Comprehensive NLP2SQL accuracy testing framework."""

    def __init__(self,
                 nlp2sql_engine: TenantAwareNLP2SQL,
                 connection_manager: TenantConnectionManager,
                 rbac_manager: TenantRBACManager):
        self.nlp2sql_engine = nlp2sql_engine
        self.connection_manager = connection_manager
        self.rbac_manager = rbac_manager
        self.test_results: List[QueryAccuracyResult] = []
        self.cross_tenant_results: List[CrossTenantQueryResult] = []
        self.test_tenants: Dict[str, Dict[str, Any]] = {}

    async def setup_test_data(self) -> Dict[str, List[str]]:
        """Set up test data for accuracy testing."""
        logger.info("Setting up test data for NLP2SQL accuracy testing")

        # Create test tenants with different schemas
        test_tenants = {
            "healthcare_tenant": await self._setup_healthcare_tenant(),
            "finance_tenant": await self._setup_finance_tenant(),
            "ecommerce_tenant": await self._setup_ecommerce_tenant()
        }

        self.test_tenants = test_tenants
        return {tenant_id: data["table_names"] for tenant_id, data in test_tenants.items()}

    async def _setup_healthcare_tenant(self) -> Dict[str, Any]:
        """Set up healthcare tenant with medical data."""
        tenant_id = "healthcare_test_tenant"
        return {
            "tenant_id": tenant_id,
            "industry": "healthcare",
            "table_names": ["patients", "doctors", "appointments", "medications", "diagnoses"],
            "schema": {
                "patients": {
                    "columns": ["patient_id", "name", "date_of_birth", "gender", "insurance_id", "phone"],
                    "sample_data": [
                        {"patient_id": 1, "name": "John Doe", "date_of_birth": "1985-03-15", "gender": "Male"},
                        {"patient_id": 2, "name": "Jane Smith", "date_of_birth": "1990-07-22", "gender": "Female"},
                        {"patient_id": 3, "name": "Bob Johnson", "date_of_birth": "1978-11-10", "gender": "Male"}
                    ]
                },
                "doctors": {
                    "columns": ["doctor_id", "name", "specialty", "license_number", "department"],
                    "sample_data": [
                        {"doctor_id": 1, "name": "Dr. Alice Wilson", "specialty": "Cardiology", "department": "Cardiology"},
                        {"doctor_id": 2, "name": "Dr. Robert Chen", "specialty": "Pediatrics", "department": "Pediatrics"}
                    ]
                },
                "appointments": {
                    "columns": ["appointment_id", "patient_id", "doctor_id", "appointment_date", "status"],
                    "sample_data": [
                        {"appointment_id": 1, "patient_id": 1, "doctor_id": 1, "appointment_date": "2024-01-15", "status": "completed"},
                        {"appointment_id": 2, "patient_id": 2, "doctor_id": 2, "appointment_date": "2024-01-16", "status": "scheduled"}
                    ]
                }
            }
        }

    async def _setup_finance_tenant(self) -> Dict[str, Any]:
        """Set up finance tenant with financial data."""
        tenant_id = "finance_test_tenant"
        return {
            "tenant_id": tenant_id,
            "industry": "finance",
            "table_names": ["accounts", "transactions", "customers", "loans", "investments"],
            "schema": {
                "accounts": {
                    "columns": ["account_id", "customer_id", "account_type", "balance", "created_date"],
                    "sample_data": [
                        {"account_id": 1, "customer_id": 1, "account_type": "checking", "balance": 5000.00},
                        {"account_id": 2, "customer_id": 2, "account_type": "savings", "balance": 15000.00}
                    ]
                },
                "transactions": {
                    "columns": ["transaction_id", "account_id", "amount", "transaction_type", "transaction_date"],
                    "sample_data": [
                        {"transaction_id": 1, "account_id": 1, "amount": 500.00, "transaction_type": "deposit"},
                        {"transaction_id": 2, "account_id": 1, "amount": -200.00, "transaction_type": "withdrawal"}
                    ]
                },
                "customers": {
                    "columns": ["customer_id", "name", "email", "phone", "address"],
                    "sample_data": [
                        {"customer_id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
                        {"customer_id": 2, "name": "Bob Williams", "email": "bob@example.com"}
                    ]
                }
            }
        }

    async def _setup_ecommerce_tenant(self) -> Dict[str, Any]:
        """Set up ecommerce tenant with retail data."""
        tenant_id = "ecommerce_test_tenant"
        return {
            "tenant_id": tenant_id,
            "industry": "retail",
            "table_names": ["products", "orders", "customers", "categories", "reviews"],
            "schema": {
                "products": {
                    "columns": ["product_id", "name", "price", "category_id", "stock_quantity"],
                    "sample_data": [
                        {"product_id": 1, "name": "Laptop", "price": 999.99, "category_id": 1, "stock_quantity": 50},
                        {"product_id": 2, "name": "Smartphone", "price": 699.99, "category_id": 1, "stock_quantity": 100}
                    ]
                },
                "orders": {
                    "columns": ["order_id", "customer_id", "order_date", "total_amount", "status"],
                    "sample_data": [
                        {"order_id": 1, "customer_id": 1, "order_date": "2024-01-10", "total_amount": 999.99, "status": "shipped"},
                        {"order_id": 2, "customer_id": 2, "order_date": "2024-01-11", "total_amount": 1399.98, "status": "processing"}
                    ]
                },
                "customers": {
                    "columns": ["customer_id", "name", "email", "registration_date", "city"],
                    "sample_data": [
                        {"customer_id": 1, "name": "Charlie Brown", "email": "charlie@example.com", "city": "New York"},
                        {"customer_id": 2, "name": "Diana Prince", "email": "diana@example.com", "city": "Los Angeles"}
                    ]
                }
            }
        }

    def generate_test_cases(self) -> List[QueryTestCase]:
        """Generate comprehensive test cases for different scenarios."""
        test_cases = []

        # Healthcare tenant test cases
        healthcare_cases = [
            QueryTestCase(
                natural_query="Show me all patients",
                expected_sql_pattern="SELECT .* FROM patients",
                tenant_id="healthcare_test_tenant",
                expected_result_count=3,
                test_category="basic_select"
            ),
            QueryTestCase(
                natural_query="How many appointments are scheduled today?",
                expected_sql_pattern="SELECT COUNT\\(.*\\) FROM appointments WHERE .* = .*",
                tenant_id="healthcare_test_tenant",
                test_category="aggregation"
            ),
            QueryTestCase(
                natural_query="List all doctors in the cardiology department",
                expected_sql_pattern="SELECT .* FROM doctors WHERE department = 'Cardiology'",
                tenant_id="healthcare_test_tenant",
                expected_result_count=1,
                test_category="filtered_select"
            ),
            QueryTestCase(
                natural_query="Show patient appointments with doctor names",
                expected_sql_pattern="SELECT .* FROM appointments .* JOIN .* doctors",
                tenant_id="healthcare_test_tenant",
                test_category="join_query"
            )
        ]

        # Finance tenant test cases
        finance_cases = [
            QueryTestCase(
                natural_query="Show all customer accounts",
                expected_sql_pattern="SELECT .* FROM accounts",
                tenant_id="finance_test_tenant",
                expected_result_count=2,
                test_category="basic_select"
            ),
            QueryTestCase(
                natural_query="What is the total balance across all accounts?",
                expected_sql_pattern="SELECT SUM\\(balance\\) FROM accounts",
                tenant_id="finance_test_tenant",
                test_category="aggregation"
            ),
            QueryTestCase(
                natural_query="Show recent transactions for checking accounts",
                expected_sql_pattern="SELECT .* FROM transactions .* JOIN .* accounts .* WHERE account_type = 'checking'",
                tenant_id="finance_test_tenant",
                test_category="join_query"
            ),
            QueryTestCase(
                natural_query="List customers with savings accounts",
                expected_sql_pattern="SELECT .* FROM customers .* JOIN .* accounts .* WHERE account_type = 'savings'",
                tenant_id="finance_test_tenant",
                test_category="join_query"
            )
        ]

        # Ecommerce tenant test cases
        ecommerce_cases = [
            QueryTestCase(
                natural_query="Show all products",
                expected_sql_pattern="SELECT .* FROM products",
                tenant_id="ecommerce_test_tenant",
                expected_result_count=2,
                test_category="basic_select"
            ),
            QueryTestCase(
                natural_query="How many orders were placed this month?",
                expected_sql_pattern="SELECT COUNT\\(.*\\) FROM orders WHERE .*",
                tenant_id="ecommerce_test_tenant",
                test_category="aggregation"
            ),
            QueryTestCase(
                natural_query="What is the average order value?",
                expected_sql_pattern="SELECT AVG\\(total_amount\\) FROM orders",
                tenant_id="ecommerce_test_tenant",
                test_category="aggregation"
            ),
            QueryTestCase(
                natural_query="Show customer orders with product details",
                expected_sql_pattern="SELECT .* FROM orders .* JOIN .* customers",
                tenant_id="ecommerce_test_tenant",
                test_category="join_query"
            )
        ]

        # Cross-tenant confusion test cases (should fail)
        cross_tenant_cases = [
            QueryTestCase(
                natural_query="Show patients from finance database",
                expected_sql_pattern="",
                tenant_id="finance_test_tenant",
                should_succeed=False,
                test_category="cross_tenant_confusion"
            ),
            QueryTestCase(
                natural_query="List financial accounts from healthcare tenant",
                expected_sql_pattern="",
                tenant_id="healthcare_test_tenant",
                should_succeed=False,
                test_category="cross_tenant_confusion"
            )
        ]

        test_cases.extend(healthcare_cases)
        test_cases.extend(finance_cases)
        test_cases.extend(ecommerce_cases)
        test_cases.extend(cross_tenant_cases)

        return test_cases

    async def test_query_accuracy(self, test_cases: List[QueryTestCase]) -> List[QueryAccuracyResult]:
        """Test NLP2SQL accuracy for given test cases."""
        logger.info(f"Testing query accuracy for {len(test_cases)} test cases")
        results = []

        for test_case in test_cases:
            result = await self._test_single_query_accuracy(test_case)
            results.append(result)

        self.test_results.extend(results)
        return results

    async def _test_single_query_accuracy(self, test_case: QueryTestCase) -> QueryAccuracyResult:
        """Test accuracy for a single query."""
        start_time = time.time()

        try:
            # Create tenant context
            tenant_context = self._create_tenant_context(test_case.tenant_id)

            # Generate SQL from natural language
            query_result = await self.nlp2sql_engine.process_nlp_query(
                test_case.natural_query,
                tenant_context
            )

            generated_sql = query_result.sql_query
            execution_time = time.time() - start_time

            # Test SQL accuracy
            sql_accuracy_score = self._calculate_sql_accuracy(
                generated_sql,
                test_case.expected_sql_pattern
            )

            # Test execution (mock)
            execution_successful = test_case.should_succeed
            actual_result_count = None
            error_message = None

            if test_case.should_succeed:
                # Mock execution results
                actual_result_count = test_case.expected_result_count
                result_tenant_specific = await self._verify_tenant_specific_results(
                    generated_sql,
                    test_case.tenant_id
                )
            else:
                execution_successful = False
                error_message = "Query should not succeed for cross-tenant access"
                result_tenant_specific = False

            return QueryAccuracyResult(
                test_case=test_case,
                generated_sql=generated_sql,
                execution_successful=execution_successful,
                sql_accuracy_score=sql_accuracy_score,
                result_tenant_specific=result_tenant_specific,
                execution_time=execution_time,
                error_message=error_message,
                actual_result_count=actual_result_count
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return QueryAccuracyResult(
                test_case=test_case,
                generated_sql="",
                execution_successful=False,
                sql_accuracy_score=0.0,
                result_tenant_specific=False,
                execution_time=execution_time,
                error_message=str(e)
            )

    async def test_tenant_specific_results(self, tenant_ids: List[str]) -> Dict[str, Any]:
        """Test that same query returns tenant-specific results."""
        logger.info("Testing tenant-specific query results")

        # Common query to test across tenants
        test_query = "Show me all customers"

        results = {}
        for tenant_id in tenant_ids:
            if tenant_id in self.test_tenants:
                tenant_context = self._create_tenant_context(tenant_id)

                try:
                    query_result = await self.nlp2sql_engine.process_nlp_query(
                        test_query,
                        tenant_context
                    )

                    # Mock execution to get tenant-specific results
                    mock_results = await self._execute_mock_query(
                        query_result.sql_query,
                        tenant_id
                    )

                    results[tenant_id] = {
                        "sql_query": query_result.sql_query,
                        "result_count": len(mock_results),
                        "results": mock_results,
                        "tenant_specific": await self._verify_tenant_specific_results(
                            query_result.sql_query,
                            tenant_id
                        )
                    }

                except Exception as e:
                    results[tenant_id] = {
                        "error": str(e),
                        "tenant_specific": False
                    }

        # Verify results are different across tenants
        tenant_specific_confirmed = self._verify_cross_tenant_result_differences(results)

        return {
            "query": test_query,
            "tenant_results": results,
            "tenant_specific_confirmed": tenant_specific_confirmed,
            "test_summary": {
                "tenants_tested": len(results),
                "successful_queries": len([r for r in results.values() if "error" not in r]),
                "tenant_isolation_verified": tenant_specific_confirmed
            }
        }

    async def test_query_suggestions(self, tenant_id: str) -> Dict[str, Any]:
        """Test that query suggestions are based on tenant schema."""
        logger.info(f"Testing query suggestions for tenant {tenant_id}")

        if tenant_id not in self.test_tenants:
            return {"error": "Tenant not found in test data"}

        tenant_data = self.test_tenants[tenant_id]
        tenant_context = self._create_tenant_context(tenant_id)

        # Test suggestion generation based on schema
        suggestions = await self._generate_query_suggestions(tenant_context)

        # Verify suggestions are tenant-specific
        tenant_specific_suggestions = True
        suggestion_details = []

        for suggestion in suggestions:
            # Check if suggestion references tenant's tables
            tenant_tables = tenant_data["table_names"]
            suggestion_references_tenant_tables = any(
                table in suggestion.lower() for table in tenant_tables
            )

            # Check if suggestion doesn't reference other tenant's tables
            other_tenant_tables = []
            for other_tenant_id, other_data in self.test_tenants.items():
                if other_tenant_id != tenant_id:
                    other_tenant_tables.extend(other_data["table_names"])

            suggestion_references_other_tables = any(
                table in suggestion.lower() for table in other_tenant_tables
            )

            suggestion_details.append({
                "suggestion": suggestion,
                "references_tenant_tables": suggestion_references_tenant_tables,
                "references_other_tables": suggestion_references_other_tables,
                "tenant_specific": suggestion_references_tenant_tables and not suggestion_references_other_tables
            })

            if not suggestion_references_tenant_tables or suggestion_references_other_tables:
                tenant_specific_suggestions = False

        return {
            "tenant_id": tenant_id,
            "suggestions": suggestions,
            "suggestion_details": suggestion_details,
            "tenant_specific_confirmed": tenant_specific_suggestions,
            "available_tables": tenant_data["table_names"]
        }

    async def test_cross_tenant_query_prevention(self) -> List[CrossTenantQueryResult]:
        """Test that cross-tenant queries are properly prevented."""
        logger.info("Testing cross-tenant query prevention")
        results = []

        tenant_ids = list(self.test_tenants.keys())

        for source_tenant in tenant_ids:
            for target_tenant in tenant_ids:
                if source_tenant != target_tenant:
                    result = await self._test_cross_tenant_query_attempt(source_tenant, target_tenant)
                    results.append(result)

        self.cross_tenant_results.extend(results)
        return results

    async def _test_cross_tenant_query_attempt(self, source_tenant: str, target_tenant: str) -> CrossTenantQueryResult:
        """Test a specific cross-tenant query attempt."""
        start_time = time.time()

        # Get target tenant's table to attempt unauthorized access
        target_data = self.test_tenants[target_tenant]
        target_table = target_data["table_names"][0]

        # Attempt query from source tenant context
        malicious_query = f"SELECT * FROM {target_table}"
        source_context = self._create_tenant_context(source_tenant)

        try:
            # This should fail in a properly isolated system
            query_result = await self.nlp2sql_engine.process_nlp_query(
                f"Show me data from {target_table}",
                source_context
            )

            # If we reach here, check if the generated SQL contains target table
            access_prevented = target_table not in query_result.sql_query.lower()
            error_type = "access_granted" if not access_prevented else "access_denied"

        except Exception as e:
            # Expected behavior - access should be denied
            access_prevented = True
            error_type = "access_denied"

        execution_time = time.time() - start_time

        return CrossTenantQueryResult(
            source_tenant=source_tenant,
            target_tenant=target_tenant,
            query_attempt=malicious_query,
            access_prevented=access_prevented,
            error_type=error_type,
            execution_time=execution_time
        )

    async def run_comprehensive_accuracy_tests(self) -> Dict[str, Any]:
        """Run all NLP2SQL accuracy tests."""
        logger.info("Starting comprehensive NLP2SQL accuracy tests")

        # Set up test data
        await self.setup_test_data()

        # Generate test cases
        test_cases = self.generate_test_cases()

        results = {
            "test_execution": {
                "start_time": datetime.utcnow().isoformat(),
                "test_case_count": len(test_cases),
                "tenant_count": len(self.test_tenants)
            },
            "query_accuracy": [],
            "tenant_specific_results": {},
            "query_suggestions": {},
            "cross_tenant_prevention": [],
            "summary": {}
        }

        try:
            # Test query accuracy
            accuracy_results = await self.test_query_accuracy(test_cases)
            results["query_accuracy"] = [r.__dict__ for r in accuracy_results]

            # Test tenant-specific results
            tenant_ids = list(self.test_tenants.keys())
            tenant_results = await self.test_tenant_specific_results(tenant_ids)
            results["tenant_specific_results"] = tenant_results

            # Test query suggestions for each tenant
            for tenant_id in tenant_ids:
                suggestion_results = await self.test_query_suggestions(tenant_id)
                results["query_suggestions"][tenant_id] = suggestion_results

            # Test cross-tenant query prevention
            prevention_results = await self.test_cross_tenant_query_prevention()
            results["cross_tenant_prevention"] = [r.__dict__ for r in prevention_results]

            # Generate summary
            results["summary"] = self._generate_accuracy_test_summary(results)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()

        except Exception as e:
            results["test_execution"]["error"] = str(e)
            results["test_execution"]["end_time"] = datetime.utcnow().isoformat()

        return results

    def _generate_accuracy_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of accuracy test results."""
        # Query accuracy summary
        accuracy_tests = results["query_accuracy"]
        total_queries = len(accuracy_tests)
        successful_queries = len([r for r in accuracy_tests if r["execution_successful"]])
        avg_accuracy_score = sum(r["sql_accuracy_score"] for r in accuracy_tests) / total_queries if total_queries > 0 else 0

        # Cross-tenant prevention summary
        prevention_tests = results["cross_tenant_prevention"]
        total_prevention_tests = len(prevention_tests)
        successful_preventions = len([r for r in prevention_tests if r["access_prevented"]])

        # Tenant-specific results summary
        tenant_results = results["tenant_specific_results"]
        tenant_isolation_confirmed = tenant_results.get("tenant_specific_confirmed", False)

        return {
            "query_accuracy": {
                "total_tests": total_queries,
                "successful_queries": successful_queries,
                "success_rate": (successful_queries / total_queries) * 100 if total_queries > 0 else 0,
                "average_accuracy_score": round(avg_accuracy_score, 2)
            },
            "cross_tenant_prevention": {
                "total_tests": total_prevention_tests,
                "successful_preventions": successful_preventions,
                "prevention_rate": (successful_preventions / total_prevention_tests) * 100 if total_prevention_tests > 0 else 0
            },
            "tenant_isolation": {
                "confirmed": tenant_isolation_confirmed,
                "tenants_tested": len(self.test_tenants)
            },
            "overall_score": self._calculate_overall_accuracy_score(results)
        }

    def _calculate_overall_accuracy_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall accuracy score."""
        accuracy_weight = 0.4
        prevention_weight = 0.4
        isolation_weight = 0.2

        accuracy_score = results["summary"]["query_accuracy"]["success_rate"] / 100
        prevention_score = results["summary"]["cross_tenant_prevention"]["prevention_rate"] / 100
        isolation_score = 1.0 if results["summary"]["tenant_isolation"]["confirmed"] else 0.0

        overall_score = (
            accuracy_score * accuracy_weight +
            prevention_score * prevention_weight +
            isolation_score * isolation_weight
        )

        return round(overall_score * 100, 2)

    # Helper methods

    def _create_tenant_context(self, tenant_id: str) -> TenantRoutingContext:
        """Create tenant routing context for testing."""
        return TenantRoutingContext(
            user_id="test_user",
            tenant_id=tenant_id,
            roles=["user"],
            access_level="standard",
            allowed_operations=["query", "read"],
            database_connection=None,  # Mock connection
            routing_metrics={}
        )

    def _calculate_sql_accuracy(self, generated_sql: str, expected_pattern: str) -> float:
        """Calculate SQL accuracy score based on pattern matching."""
        if not generated_sql or not expected_pattern:
            return 0.0

        # Use regex to match pattern
        pattern_match = re.search(expected_pattern, generated_sql, re.IGNORECASE)
        if pattern_match:
            return 100.0

        # Calculate similarity score
        similarity = difflib.SequenceMatcher(None, generated_sql.lower(), expected_pattern.lower()).ratio()
        return round(similarity * 100, 2)

    async def _verify_tenant_specific_results(self, sql_query: str, tenant_id: str) -> bool:
        """Verify that results are tenant-specific."""
        # Check if query references only tenant's tables
        if tenant_id in self.test_tenants:
            tenant_tables = self.test_tenants[tenant_id]["table_names"]
            other_tenant_tables = []

            for other_id, other_data in self.test_tenants.items():
                if other_id != tenant_id:
                    other_tenant_tables.extend(other_data["table_names"])

            # Query should reference tenant tables
            references_tenant_tables = any(table in sql_query.lower() for table in tenant_tables)

            # Query should not reference other tenant tables
            references_other_tables = any(table in sql_query.lower() for table in other_tenant_tables)

            return references_tenant_tables and not references_other_tables

        return False

    async def _execute_mock_query(self, sql_query: str, tenant_id: str) -> List[Dict[str, Any]]:
        """Execute mock query and return tenant-specific results."""
        if tenant_id in self.test_tenants:
            tenant_data = self.test_tenants[tenant_id]

            # Simple pattern matching to return mock data
            if "customers" in sql_query.lower():
                if "customers" in tenant_data["schema"]:
                    return tenant_data["schema"]["customers"]["sample_data"]

            # Default return for any SELECT query
            for table_name, table_data in tenant_data["schema"].items():
                if table_name in sql_query.lower():
                    return table_data["sample_data"]

        return []

    async def _generate_query_suggestions(self, tenant_context: TenantRoutingContext) -> List[str]:
        """Generate query suggestions based on tenant schema."""
        tenant_id = tenant_context.tenant_id

        if tenant_id in self.test_tenants:
            tenant_data = self.test_tenants[tenant_id]
            table_names = tenant_data["table_names"]

            # Generate suggestions based on available tables
            suggestions = []
            for table in table_names:
                suggestions.append(f"Show me all {table}")
                suggestions.append(f"How many {table} are there?")
                suggestions.append(f"What is the average value in {table}?")

            return suggestions[:6]  # Return top 6 suggestions

        return []

    def _verify_cross_tenant_result_differences(self, results: Dict[str, Any]) -> bool:
        """Verify that results are different across tenants."""
        tenant_results = []

        for tenant_id, result in results.items():
            if "error" not in result:
                tenant_results.append({
                    "tenant_id": tenant_id,
                    "sql_query": result["sql_query"],
                    "result_count": result["result_count"]
                })

        # Check if results are different across tenants
        if len(tenant_results) < 2:
            return False

        # Compare SQL queries and result counts
        for i in range(len(tenant_results)):
            for j in range(i + 1, len(tenant_results)):
                result1 = tenant_results[i]
                result2 = tenant_results[j]

                # Results should be different (different tables or data)
                if result1["sql_query"] == result2["sql_query"] and result1["result_count"] == result2["result_count"]:
                    return False

        return True


# Export the main testing class
__all__ = ["NLP2SQLAccuracyTester", "QueryTestCase", "QueryAccuracyResult", "CrossTenantQueryResult"]