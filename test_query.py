#!/usr/bin/env python3
"""
Simple test script to verify API connectivity and query execution
"""
import requests
import json

def test_api():
    base_url = "http://127.0.0.1:8003"

    print("Testing Multi-Tenant NLP2SQL API...")

    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("Health check passed")
        else:
            print(f"Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # Test 2: Login
    print("\n2. Testing login...")
    login_data = {
        "email": "diana.rodriguez0@techcorp.com",
        "password": "password123"
    }

    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            print("Login successful")
            print(f"   User: {login_result['user']['full_name']}")
            print(f"   Role: {login_result['user']['role']}")
            print(f"   Org: {login_result['organization']['org_name']}")
        else:
            print(f"Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Test 3: Query execution
    print("\n3. Testing query execution...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    test_queries = [
        "show me all products",
        "how many products do we have?",
        "list our product inventory"
    ]

    for query in test_queries:
        print(f"\n   Testing: '{query}'")
        query_data = {"query_text": query}

        try:
            response = requests.post(f"{base_url}/query/execute", json=query_data, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "success":
                    print(f"   SUCCESS - {len(result.get('results', []))} rows returned")
                    print(f"   SQL: {result.get('generated_sql', 'N/A')[:50]}...")
                elif result.get("status") == "blocked":
                    print(f"   BLOCKED - {result.get('message', 'No message')}")
                else:
                    print(f"   FAILED - {result.get('message', 'Unknown error')}")
            else:
                print(f"   HTTP Error: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"   Error: {response.text}")
        except Exception as e:
            print(f"   Exception: {e}")

    print("\nTest completed!")

if __name__ == "__main__":
    test_api()