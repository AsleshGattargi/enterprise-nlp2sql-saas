#!/usr/bin/env python3
"""
Simple interactive query tester
"""
import requests
import json

def main():
    base_url = "http://127.0.0.1:8003"

    # Login
    print("Logging in...")
    login_data = {
        "email": "diana.rodriguez0@techcorp.com",
        "password": "password123"
    }

    response = requests.post(f"{base_url}/auth/login", json=login_data)
    if response.status_code != 200:
        print("Login failed!")
        return

    token = response.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("Login successful! You can now ask questions about TechCorp data.")
    print("Available queries:")
    print("- show me all products")
    print("- how many products do we have?")
    print("- list our product inventory")
    print("- show me all sales")
    print("- how many customers do we have?")
    print("Type 'quit' to exit.\n")

    while True:
        query = input("Enter your query: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        if not query:
            continue

        query_data = {"query_text": query}

        try:
            response = requests.post(f"{base_url}/query/execute", json=query_data, headers=headers)
            if response.status_code == 200:
                result = response.json()

                if result.get("status") == "success":
                    print(f"\nSUCCESS! Generated SQL: {result.get('generated_sql')}")
                    print(f"Results: {len(result.get('results', []))} rows")

                    # Show first few rows
                    results = result.get('results', [])
                    if results:
                        print("\nFirst few results:")
                        for i, row in enumerate(results[:3]):
                            print(f"  Row {i+1}: {row}")
                        if len(results) > 3:
                            print(f"  ... and {len(results)-3} more rows")

                elif result.get("status") == "blocked":
                    print(f"\nBLOCKED: {result.get('message')}")
                else:
                    print(f"\nFAILED: {result.get('message')}")
            else:
                print(f"\nHTTP Error: {response.status_code}")

        except Exception as e:
            print(f"\nError: {e}")

        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()