"""
Direct Query Execution Script
Execute NLP2SQL queries directly without the web interface.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.tenant_aware_nlp2sql import TenantAwareNLP2SQL
from src.tenant_connection_manager import TenantConnectionManager
from src.tenant_routing_middleware import TenantRoutingContext
from src.database_cloner import DatabaseCloner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DirectQueryExecutor:
    """Direct query executor for testing and development."""

    def __init__(self):
        # Initialize components
        self.database_cloner = DatabaseCloner()
        self.connection_manager = TenantConnectionManager(self.database_cloner)
        self.nlp2sql_engine = TenantAwareNLP2SQL(self.connection_manager)

    async def execute_query(self,
                           natural_query: str,
                           tenant_id: str = "demo_tenant",
                           user_id: str = "demo_user"):
        """Execute a natural language query directly."""

        try:
            # Create tenant context
            tenant_context = TenantRoutingContext(
                user_id=user_id,
                tenant_id=tenant_id,
                roles=["user"],
                access_level="standard",
                allowed_operations=["query"],
                database_connection=None,
                routing_metrics={}
            )

            print(f"🤖 Processing query: '{natural_query}'")
            print(f"👤 User: {user_id}")
            print(f"🏢 Tenant: {tenant_id}")
            print("-" * 50)

            # Process the query
            result = await self.nlp2sql_engine.process_nlp_query(natural_query, tenant_context)

            if result.success:
                print(f"✅ Generated SQL: {result.sql_query}")
                print(f"⏱️  Execution Time: {result.execution_time:.3f}s")
                print(f"📊 Query Complexity: {result.metadata.get('complexity', 'unknown')}")

                if result.data:
                    print(f"📈 Results ({len(result.data)} rows):")
                    for i, row in enumerate(result.data[:5]):  # Show first 5 rows
                        print(f"  Row {i+1}: {row}")
                    if len(result.data) > 5:
                        print(f"  ... and {len(result.data) - 5} more rows")
                else:
                    print("📭 No data returned")

            else:
                print(f"❌ Query failed: {result.error_message}")
                if result.error_details:
                    print(f"🔍 Details: {result.error_details}")

            return result

        except Exception as e:
            print(f"💥 Exception occurred: {str(e)}")
            return None


async def main():
    """Main execution function."""

    print("🔍 Multi-Tenant NLP2SQL Direct Query Executor")
    print("=" * 60)

    executor = DirectQueryExecutor()

    # Example queries to try
    sample_queries = [
        "Show me all products",
        "How many users are in the system?",
        "List the top 10 customers by sales",
        "What is the average order value?",
        "Show me sales data from last month"
    ]

    if len(sys.argv) > 1:
        # Use query from command line
        query = " ".join(sys.argv[1:])
        await executor.execute_query(query)
    else:
        # Interactive mode
        print("Sample queries you can try:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query}")
        print()

        while True:
            try:
                user_query = input("📝 Enter your query (or 'quit' to exit): ").strip()

                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if user_query.isdigit() and 1 <= int(user_query) <= len(sample_queries):
                    user_query = sample_queries[int(user_query) - 1]
                    print(f"Using sample query: {user_query}")

                if user_query:
                    print()
                    await executor.execute_query(user_query)
                    print("\n" + "=" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"💥 Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())