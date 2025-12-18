#!/usr/bin/env python3
"""
Test script for Ollama filtering improvements
"""
import requests
import json

# Test the enhanced filtering with the API
def test_ollama_filtering():
    """Test the fine-tuned Ollama filtering for complex queries"""
    
    
    api_base = "http://localhost:8000"
    
    # Test login first (using existing user from the system)
    login_data = {
        "email": "john.doe@techcorp.com",
        "password": "password123"
    }
    
    print("[LOGIN] Testing login...")
    login_response = requests.post(f"{api_base}/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print(f"[ERROR] Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    auth_data = login_response.json()
    print(f"[SUCCESS] Login successful for {auth_data['user']['email']}")
    
    # Get the token
    token = auth_data['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test the problematic query: "How many products cost less than $50?"
    print("\n[TEST] Testing enhanced filtering query...")
    
    test_queries = [
        "How many products cost less than $50?",
        "Count products in Electronics category",
        "Show me all products",
        "How many total products do we have?"
    ]
    
    for query_text in test_queries:
        print(f"\n[QUERY] Testing query: '{query_text}'")
        
        query_data = {
            "query_text": query_text
        }
        
        response = requests.post(f"{api_base}/query/execute", json=query_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"[SUCCESS] Query successful!")
            print(f"   Status: {result['status']}")
            print(f"   Generated SQL: {result['generated_sql']}")
            print(f"   Results: {len(result['results'])} rows")
            
            # For count queries, show the actual count
            if result['results'] and len(result['results']) > 0:
                if 'COUNT(*)' in str(result['results'][0]) or 'count' in str(result['results'][0]).lower():
                    print(f"   Count Result: {result['results'][0]}")
        else:
            print(f"[ERROR] Query failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_ollama_filtering()