#!/usr/bin/env python3
"""
Test different users and query patterns to understand role-based control
"""
import requests
import json

def test_user(email, password, org_name, test_queries):
    base_url = "http://127.0.0.1:8003"

    print(f"\n{'='*60}")
    print(f"Testing {email}")
    print(f"{'='*60}")

    # Login
    login_data = {"email": email, "password": password}

    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            print("SUCCESS - Login successful!")
            print(f"   User: {login_result['user']['full_name']}")
            print(f"   Role: {login_result['user']['role']}")
            print(f"   Org: {login_result['organization']['org_name']}")
            print(f"   DB Type: {login_result['organization']['database_type']}")
        else:
            print(f"FAILED - Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"FAILED - Login failed: {e}")
        return

    # Test queries
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    for query in test_queries:
        print(f"\nTesting: '{query}'")
        query_data = {"query_text": query}

        try:
            response = requests.post(f"{base_url}/query/execute", json=query_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')

                if status == 'success':
                    print(f"   SUCCESS - {len(result.get('results', []))} rows")
                    print(f"   SQL: {result.get('generated_sql', 'N/A')[:60]}...")
                elif status == 'blocked':
                    print(f"   BLOCKED - {result.get('message', 'No message')}")
                else:
                    print(f"   ERROR - {result.get('message', 'Unknown error')}")

            else:
                print(f"   HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"   Exception: {e}")

def main():
    # Test different users and scenarios

    # TechCorp Users (have products data)
    techcorp_queries = [
        "show me all products",
        "list products under $100",
        "show products with price less than 100",
        "find cheap products",
        "how many products cost under 100 dollars",
        "show me all customers",
        "show me all employees",
        "show employee salaries"
    ]

    test_user("diana.rodriguez0@techcorp.com", "password123", "TechCorp", techcorp_queries)
    test_user("manager.smith1@techcorp.com", "password123", "TechCorp", techcorp_queries)
    test_user("analyst.jones2@techcorp.com", "password123", "TechCorp", techcorp_queries)

    # FinanceHub Users (have accounts/transactions data)
    financehub_queries = [
        "show me all accounts",
        "show me all transactions",
        "list products under $100",  # Should fail - no products
        "show account balances"
    ]

    test_user("cfo.rodriguez100@financehub.net", "password123", "FinanceHub", financehub_queries)

if __name__ == "__main__":
    main()