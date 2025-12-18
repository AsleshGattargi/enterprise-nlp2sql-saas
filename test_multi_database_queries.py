#!/usr/bin/env python3
"""
Test script to verify different query generation for different database types and organizations
"""
import sys
import os
sys.path.append('src')

from src.database import db_manager
from src.nlp2sql_engine import nlp2sql_engine
import json

# Organization configurations
ORGANIZATIONS = {
    'org-001': {
        'name': 'TechCorp',
        'database_type': 'sqlite',
        'database_name': 'techcorp_db',
        'test_queries': [
            'Show me all employees',
            'List customers',
            'Show products under $100'
        ]
    },
    'org-002': {
        'name': 'HealthPlus', 
        'database_type': 'mysql',
        'database_name': 'healthplus_db',
        'test_queries': [
            'Show me all patients',
            'List doctors',
            'Show appointments today'
        ]
    },
    'org-003': {
        'name': 'FinanceHub',
        'database_type': 'postgresql', 
        'database_name': 'financehub_db',
        'test_queries': [
            'Show me all accounts',
            'List transactions',
            'Show investment portfolio'
        ]
    },
    'org-004': {
        'name': 'RetailMax',
        'database_type': 'mongodb',
        'database_name': 'retailmax_db', 
        'test_queries': [
            'Show me all products',
            'List customers',
            'Show sales data'
        ]
    },
    'org-005': {
        'name': 'EduLearn',
        'database_type': 'mysql',
        'database_name': 'edulearn_db',
        'test_queries': [
            'Show me all students',
            'List courses', 
            'Show student grades'
        ]
    }
}

def test_database_connections():
    """Test connections to all organization databases"""
    print("="*80)
    print("1. TESTING DATABASE CONNECTIONS")
    print("="*80)
    
    for org_id, config in ORGANIZATIONS.items():
        print(f"\n[*] {config['name']} ({org_id})")
        print(f"   Database: {config['database_type'].upper()} - {config['database_name']}")
        
        try:
            db_info = db_manager.get_org_connection(
                org_id, 
                config['database_type'], 
                config['database_name']
            )
            
            connection = db_info['connection']
            
            if config['database_type'] in ['mysql', 'postgresql']:
                cursor = connection.cursor()
                if config['database_type'] == 'mysql':
                    cursor.execute("SHOW TABLES")
                else:  # postgresql
                    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                tables = [table[0] for table in cursor.fetchall()]
                cursor.close()
                print(f"   [+] Connected - Tables: {', '.join(tables[:3])}{'...' if len(tables) > 3 else ''}")
                
            elif config['database_type'] == 'sqlite':
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [table[0] for table in cursor.fetchall()]
                cursor.close()
                print(f"   [+] Connected - Tables: {', '.join(tables[:3])}{'...' if len(tables) > 3 else ''}")
                
            elif config['database_type'] == 'mongodb':
                # MongoDB connection test
                db = connection[config['database_name']]
                collections = db.list_collection_names()
                print(f"   [+] Connected - Collections: {', '.join(collections[:3])}{'...' if len(collections) > 3 else ''}")
            
            connection.close()
            
        except Exception as e:
            print(f"   [-] Connection failed: {str(e)[:100]}...")

def test_query_generation():
    """Test SQL/NoSQL query generation for different database types"""
    print("\n" + "="*80)
    print("2. TESTING QUERY GENERATION BY DATABASE TYPE")
    print("="*80)
    
    for org_id, config in ORGANIZATIONS.items():
        print(f"\n[ORG] {config['name']} ({config['database_type'].upper()})")
        print("-" * 50)
        
        for query_text in config['test_queries']:
            print(f"\n[Q] Query: '{query_text}'")
            
            try:
                # Generate parsed query
                parsed_query = nlp2sql_engine.parse_natural_language(
                    query_text,
                    config['database_type'],
                    config['database_name'], 
                    org_id
                )
                
                # Generate SQL/NoSQL
                if config['database_type'] == 'mongodb':
                    generated_query = nlp2sql_engine.generate_mongodb_query(parsed_query)
                    print(f"   [MONGO] MongoDB Query:")
                    # Pretty print JSON
                    try:
                        query_dict = json.loads(generated_query)
                        print(f"      {json.dumps(query_dict, indent=6)}")
                    except:
                        print(f"      {generated_query}")
                else:
                    generated_sql = nlp2sql_engine.generate_sql(
                        parsed_query, 
                        config['database_type'],
                        f"user-{org_id[-3:]}"  # Generate user ID
                    )
                    print(f"   [SQL] {config['database_type'].upper()} SQL:")
                    print(f"      {generated_sql}")
                
                print(f"   [OK] Table/Collection: {parsed_query.get('table', 'N/A')}")
                print(f"   ⚡ Confidence: {parsed_query.get('confidence', 0):.2f}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}...")

def test_actual_query_execution():
    """Test actual query execution on different databases"""
    print("\n" + "="*80)
    print("3. TESTING ACTUAL QUERY EXECUTION")
    print("="*80)
    
    # Test one query per organization
    test_cases = [
        ('org-001', 'Show me all employees'),
        ('org-002', 'Show me all patients'), 
        ('org-003', 'Show me all accounts'),
        ('org-005', 'Show me all students')  # Skip MongoDB for now
    ]
    
    for org_id, query_text in test_cases:
        config = ORGANIZATIONS[org_id]
        print(f"\n🚀 Executing: '{query_text}' on {config['name']} ({config['database_type'].upper()})")
        
        try:
            # Process query through NLP2SQL engine
            query_result = nlp2sql_engine.process_query(
                query_text,
                f"user-{org_id[-3:]}", 
                org_id,
                config['database_type'],
                config['database_name']
            )
            
            if query_result['success']:
                generated_sql = query_result['generated_sql']
                print(f"   [Q] Generated SQL: {generated_sql}")
                
                # Execute on database
                db_result = db_manager.execute_query(
                    org_id,
                    config['database_type'], 
                    config['database_name'],
                    generated_sql
                )
                
                if db_result['success']:
                    row_count = db_result.get('row_count', len(db_result.get('data', [])))
                    print(f"   [OK] Execution SUCCESS - {row_count} rows returned")
                    
                    # Show sample data
                    data = db_result.get('data', [])
                    if data and len(data) > 0:
                        first_row = data[0]
                        if isinstance(first_row, dict):
                            # Show first few keys/values
                            sample_keys = list(first_row.keys())[:4]
                            sample_data = {k: first_row[k] for k in sample_keys}
                            print(f"   📄 Sample data: {sample_data}")
                else:
                    print(f"   ❌ DB Execution failed: {db_result.get('error', 'Unknown error')}")
            else:
                print(f"   ❌ NLP Processing failed: {query_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:100]}...")

def show_database_differences():
    """Show key differences between database types"""
    print("\n" + "="*80)
    print("4. DATABASE TYPE DIFFERENCES")
    print("="*80)
    
    differences = {
        'SQLite': {
            'Syntax': 'Standard SQL with some limitations',
            'Connection': 'File-based, lightweight',
            'Example': 'SELECT * FROM employees LIMIT 10'
        },
        'MySQL': {
            'Syntax': 'Standard SQL with MySQL extensions', 
            'Connection': 'Network-based, full RDBMS',
            'Example': 'SELECT * FROM patients LIMIT 10'
        },
        'PostgreSQL': {
            'Syntax': 'Advanced SQL with PostgreSQL features',
            'Connection': 'Network-based, enterprise RDBMS', 
            'Example': 'SELECT * FROM accounts LIMIT 10'
        },
        'MongoDB': {
            'Syntax': 'NoSQL JSON queries',
            'Connection': 'Document database',
            'Example': '{"products": {"$limit": 10}}'
        }
    }
    
    for db_type, info in differences.items():
        print(f"\n🗄️  {db_type}")
        for key, value in info.items():
            print(f"   {key}: {value}")

def main():
    """Run all tests"""
    print("MULTI-DATABASE QUERY GENERATION TEST")
    print("This script will show you how different database types generate different queries")
    print()
    
    try:
        test_database_connections()
        test_query_generation() 
        test_actual_query_execution()
        show_database_differences()
        
        print("\n" + "="*80)
        print("[OK] TESTING COMPLETE")
        print("="*80)
        print("Key Observations:")
        print("• Each organization uses a different database type")
        print("• SQL syntax varies between MySQL, PostgreSQL, and SQLite")
        print("• MongoDB generates JSON queries instead of SQL")
        print("• Each database has organization-specific table/collection names")
        print("• No org_id filters are added (each org has its own database)")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()