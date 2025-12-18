#!/usr/bin/env python3
"""
Test login functionality for all users
"""
import requests
import json

def test_user_login():
    """Test login for all users"""
    
    print("TESTING USER LOGIN FUNCTIONALITY")
    print("=" * 45)
    
    base_url = "http://localhost:8001"
    
    # Test users with default password
    test_users = [
        {
            "email": "alex.davis5@techcorp.com",
            "password": "password123",
            "org": "TechCorp"
        },
        {
            "email": "ceo.rodriguez150@retailmax.com", 
            "password": "password123",
            "org": "RetailMax"
        },
        {
            "email": "dean.rodriguez200@edulearn.edu",
            "password": "password123", 
            "org": "EduLearn"
        },
        {
            "email": "cfo.rodriguez100@financehub.net",
            "password": "password123",
            "org": "FinanceHub"  
        },
        {
            "email": "anna.analyst55@healthplus.org",
            "password": "password123",
            "org": "HealthPlus"
        }
    ]
    
    successful_logins = 0
    failed_logins = 0
    
    for user in test_users:
        print(f"\n[TEST] {user['org']} - {user['email']}")
        print("-" * 50)
        
        login_data = {
            "email": user['email'],
            "password": user['password']
        }
        
        try:
            response = requests.post(f"{base_url}/auth/login", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"  SUCCESS: Login successful")
                print(f"  Token: {result.get('access_token', '')[:20]}...")
                print(f"  User ID: {result.get('user_id')}")
                print(f"  Organization: {result.get('organization', {}).get('org_name')}")
                print(f"  Role: {result.get('role')}")
                successful_logins += 1
            else:
                print(f"  FAILED: Status {response.status_code}")
                print(f"  Error: {response.text}")
                failed_logins += 1
                
        except Exception as e:
            print(f"  ERROR: {e}")
            failed_logins += 1
    
    print(f"\n{'='*45}")
    print(f"LOGIN TEST SUMMARY")
    print(f"{'='*45}")
    print(f"Total Tests: {len(test_users)}")
    print(f"Successful: {successful_logins}")
    print(f"Failed: {failed_logins}")
    print(f"Success Rate: {(successful_logins/len(test_users))*100:.1f}%")
    
    if successful_logins == len(test_users):
        print(f"\nALL USERS CAN NOW LOGIN SUCCESSFULLY!")
        print(f"Multi-tenant authentication is working properly.")
    elif failed_logins > 0:
        print(f"\nSome login issues remain - check failed logins above.")

if __name__ == "__main__":
    test_user_login()