#!/usr/bin/env python3
"""
Test query generation for different database types
"""
import requests
import json
import time

def test_database_types():
    """Test query generation across different database types"""
    
    print("TESTING QUERY GENERATION FOR DIFFERENT DATABASE TYPES")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    
    # Test organizations with different database types
    test_orgs = [
        {
            "name": "TechCorp",
            "email": "alex.davis5@techcorp.com",
            "password": "password123",
            "db_type": "SQLite",
            "test_queries": [
                "show all products",
                "total products by category", 
                "products with price greater than 100"
            ]
        },
        {
            "name": "FinanceHub", 
            "email": "cfo.rodriguez100@financehub.net",
            "password": "password123",
            "db_type": "PostgreSQL",
            "test_queries": [
                "show all transactions",
                "total transactions by type",
                "transactions from last month"
            ]
        },
        {
            "name": "RetailMax",
            "email": "ceo.rodriguez150@retailmax.com", 
            "password": "password123",
            "db_type": "MongoDB",
            "test_queries": [
                "show all products",
                "products by category",
                "top selling products"
            ]
        }
    ]
    
    for org in test_orgs:
        print(f"\n[{org['name']}] ({org['db_type']})")
        print("-" * 40)
        
        # Login
        try:
            login_response = requests.post(f"{base_url}/auth/login", json={
                "email": org['email'],
                "password": org['password']
            })
            
            if login_response.status_code != 200:
                print(f"Login failed: {login_response.text}")
                continue
                
            token = login_response.json()['access_token']
            org_info = login_response.json()['organization']
            print(f"Logged in successfully")
            print(f"   Database: {org_info['database_name']} ({org_info['database_type']})")
            
            # Test queries
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            
            for query in org['test_queries']:
                print(f"\nQuery: '{query}'")
                
                try:
                    response = requests.post(f"{base_url}/query/execute", 
                                           headers=headers,
                                           json={"query_text": query})
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result['status'] == 'success' and result['generated_sql']:
                            print(f"   Generated SQL:")
                            # Format SQL for better display
                            sql = result['generated_sql'].strip()
                            for line in sql.split('\n'):
                                print(f"      {line}")
                            print(f"   Returned {len(result.get('results', []))} rows")
                        else:
                            print(f"   Warning: {result.get('message', 'Could not generate SQL')}")
                    else:
                        print(f"   API Error: {response.status_code}")
                        
                except Exception as e:
                    print(f"   Error: {e}")
                
                time.sleep(0.5)  # Small delay between requests
                    
        except Exception as e:
            print(f"Error with {org['name']}: {e}")
    
    print(f"\n{'=' * 60}")
    print("DATABASE TYPE TESTING COMPLETE")
    print("\nKey Differences:")
    print("- SQLite: Simple SQL with standard syntax")
    print("- PostgreSQL: SQL with PostgreSQL-specific features") 
    print("- MongoDB: NoSQL queries (may not generate SQL)")
    print("- MySQL: SQL with MySQL-specific syntax")

if __name__ == "__main__":
    test_database_types()