"""
Simple Query Executor - No Database Dependencies
Execute NLP2SQL queries with mock data for testing.
"""

import sys
import time
from datetime import datetime


class SimpleQueryExecutor:
    """Simple query executor with mock responses."""

    def __init__(self):
        self.mock_responses = {
            "show me all products": {
                "sql": "SELECT * FROM products",
                "data": [
                    {"product_id": 1, "name": "Laptop", "price": 999.99, "category": "Electronics"},
                    {"product_id": 2, "name": "Mouse", "price": 29.99, "category": "Electronics"},
                    {"product_id": 3, "name": "Keyboard", "price": 79.99, "category": "Electronics"}
                ]
            },
            "how many users": {
                "sql": "SELECT COUNT(*) as user_count FROM users",
                "data": [{"user_count": 150}]
            },
            "top customers": {
                "sql": "SELECT customer_name, total_orders FROM customers ORDER BY total_orders DESC LIMIT 5",
                "data": [
                    {"customer_name": "John Doe", "total_orders": 25},
                    {"customer_name": "Jane Smith", "total_orders": 18},
                    {"customer_name": "Bob Johnson", "total_orders": 15}
                ]
            },
            "average order value": {
                "sql": "SELECT AVG(order_total) as avg_value FROM orders",
                "data": [{"avg_value": 156.78}]
            },
            "sales last month": {
                "sql": "SELECT SUM(order_total) as total_sales FROM orders WHERE order_date >= DATE_SUB(NOW(), INTERVAL 1 MONTH)",
                "data": [{"total_sales": 45678.90}]
            }
        }

    def execute_query(self, query_text):
        """Execute a natural language query and return mock results."""

        print(f"Multi-Tenant NLP2SQL Query Executor")
        print("=" * 50)
        print(f"Query: {query_text}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 50)

        # Simulate processing time
        print("Processing natural language query...")
        time.sleep(0.5)

        # Find matching mock response
        query_lower = query_text.lower()
        response = None

        for key, value in self.mock_responses.items():
            if key in query_lower:
                response = value
                break

        if not response:
            # Generic response for unknown queries
            response = {
                "sql": f"-- Generated SQL for: {query_text}\nSELECT * FROM data_table WHERE condition = 'example';",
                "data": [{"message": "This is a mock response", "status": "success"}]
            }

        print(f"Generated SQL: {response['sql']}")
        print(f"Execution time: 0.5 seconds")
        print(f"Results ({len(response['data'])} rows):")
        print("-" * 50)

        # Display results
        for i, row in enumerate(response['data'], 1):
            print(f"Row {i}: {row}")

        print("=" * 50)
        return response


def main():
    """Main execution function."""

    executor = SimpleQueryExecutor()

    # Sample queries
    sample_queries = [
        "Show me all products",
        "How many users are in the system?",
        "List the top customers by orders",
        "What is the average order value?",
        "Show me sales data from last month"
    ]

    if len(sys.argv) > 1:
        # Use query from command line
        query = " ".join(sys.argv[1:])
        executor.execute_query(query)
    else:
        # Interactive mode
        print("Multi-Tenant NLP2SQL Simple Query Executor")
        print("=" * 50)
        print("Sample queries you can try:")
        for i, query in enumerate(sample_queries, 1):
            print(f"  {i}. {query}")
        print()

        while True:
            try:
                user_query = input("Enter your query (or 'quit' to exit): ").strip()

                if user_query.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break

                if user_query.isdigit() and 1 <= int(user_query) <= len(sample_queries):
                    user_query = sample_queries[int(user_query) - 1]
                    print(f"Using sample query: {user_query}")

                if user_query:
                    print()
                    executor.execute_query(user_query)
                    print()

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()