#!/usr/bin/env python3
"""
Test end-to-end functionality for all organizations
"""
import requests
import json

def test_organization_end_to_end(org_name, email, password, test_query):
    """Test login and query execution for an organization"""
    
    base_url = "http://localhost:8001"
    
    print(f"\n[{org_name}] Testing End-to-End Functionality")
    print("-" * 50)
    
    try:
        # Step 1: Login
        login_data = {"email": email, "password": password}
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            print(f"  LOGIN FAILED: {login_response.status_code} - {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result.get("access_token")
        org_info = login_result.get("organization", {})
        
        print(f"  LOGIN SUCCESS")
        print(f"    User: {login_result.get('full_name', 'Unknown')}")
        print(f"    Organization: {org_info.get('org_name')}")
        print(f"    Database: {org_info.get('database_name')} ({org_info.get('database_type')})")
        
        # Step 2: Execute Query
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        query_data = {
            "query_text": test_query,
            "export_format": None
        }
        
        query_response = requests.post(f"{base_url}/query/execute", json=query_data, headers=headers)
        
        if query_response.status_code != 200:
            print(f"  QUERY FAILED: {query_response.status_code} - {query_response.text}")
            return False
        
        query_result = query_response.json()
        
        if query_result.get("status") == "success":
            results = query_result.get("results", [])
            sql = query_result.get("generated_sql", "")
            
            print(f"  QUERY SUCCESS")
            print(f"    Query: '{test_query}'")
            print(f"    Results: {len(results)} rows")
            print(f"    SQL: {sql[:80]}...")
            
            if results:
                print(f"    Sample Result: {results[0] if len(results) > 0 else 'None'}")
            
            return True
        else:
            print(f"  QUERY FAILED: {query_result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_all_organizations():
    """Test all organizations end-to-end"""
    
    print("TESTING ALL ORGANIZATIONS - END TO END")
    print("=" * 55)
    
    # Define test cases for each organization with industry-specific queries
    test_cases = [
        {
            "org_name": "TechCorp", 
            "email": "alex.davis5@techcorp.com",
            "password": "password123",
            "query": "list all products"
        },
        {
            "org_name": "HealthPlus",
            "email": "anna.analyst55@healthplus.org", 
            "password": "password123",
            "query": "list all patients"
        },
        {
            "org_name": "FinanceHub",
            "email": "cfo.rodriguez100@financehub.net",
            "password": "password123", 
            "query": "list all accounts"
        },
        {
            "org_name": "RetailMax",
            "email": "ceo.rodriguez150@retailmax.com",
            "password": "password123",
            "query": "list all products"
        },
        {
            "org_name": "EduLearn",
            "email": "dean.rodriguez200@edulearn.edu",
            "password": "password123",
            "query": "list all students"
        }
    ]
    
    successful_tests = 0
    failed_tests = 0
    
    for test_case in test_cases:
        success = test_organization_end_to_end(
            test_case["org_name"],
            test_case["email"], 
            test_case["password"],
            test_case["query"]
        )
        
        if success:
            successful_tests += 1
        else:
            failed_tests += 1
    
    print(f"\n{'='*55}")
    print(f"END-TO-END TEST SUMMARY")
    print(f"{'='*55}")
    print(f"Total Organizations: {len(test_cases)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(successful_tests/len(test_cases))*100:.1f}%")
    
    if successful_tests == len(test_cases):
        print(f"\nALL ORGANIZATIONS WORKING END-TO-END!")
        print(f"Multi-tenant NLP2SQL system is fully functional across:")
        print(f"  - TechCorp (Technology/E-commerce)")
        print(f"  - HealthPlus (Healthcare)")  
        print(f"  - FinanceHub (Financial Services)")
        print(f"  - RetailMax (Retail/E-commerce)")
        print(f"  - EduLearn (Education)")
        print(f"\nAll users can login and execute queries successfully!")
    else:
        print(f"\nSome organizations still have issues - check failed tests above.")

if __name__ == "__main__":
    test_all_organizations()