#!/usr/bin/env python3
"""
Test script for Multi-Database Setup

This script tests the multi-database architecture to ensure all components work correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent / 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connections():
    """Test connections to all organization databases"""
    logger.info("🧪 Testing Multi-Database Setup")
    
    try:
        from database import db_manager
        from sqlalchemy import text
        
        # Test metadata database
        logger.info("\n1️⃣  Testing Metadata Database...")
        try:
            with db_manager.get_metadata_db() as db:
                result = db.execute(text("SELECT COUNT(*) as org_count FROM organizations")).fetchone()
                logger.info(f"✅ Metadata DB: Found {result.org_count if result else 0} organizations")
        except Exception as e:
            logger.error(f"❌ Metadata DB Error: {e}")
            
        # Test organization databases
        test_cases = [
            {
                'org_id': 'org-001',
                'org_name': 'TechCorp',
                'db_type': 'sqlite',
                'db_name': 'techcorp_db',
                'test_query': 'SELECT COUNT(*) as product_count FROM products'
            },
            {
                'org_id': 'org-002', 
                'org_name': 'HealthPlus',
                'db_type': 'mysql',
                'db_name': 'healthplus_db',
                'test_query': 'SELECT COUNT(*) as patient_count FROM patients'
            },
            {
                'org_id': 'org-003',
                'org_name': 'FinanceHub', 
                'db_type': 'postgresql',
                'db_name': 'financehub_db',
                'test_query': 'SELECT COUNT(*) as account_count FROM accounts'
            },
            {
                'org_id': 'org-004',
                'org_name': 'RetailMax',
                'db_type': 'mongodb',
                'db_name': 'retailmax_db',
                'test_query': 'products'  # Collection name for MongoDB
            },
            {
                'org_id': 'org-005',
                'org_name': 'EduLearn',
                'db_type': 'mysql',
                'db_name': 'edulearn_db',
                'test_query': 'SELECT COUNT(*) as student_count FROM students'
            }
        ]
        
        logger.info("\n2️⃣  Testing Organization Databases...")
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n{i}. {test_case['org_name']} ({test_case['db_type'].upper()})")
            
            try:
                # Test connection
                connection_success = db_manager.test_connection(
                    test_case['org_id'], 
                    test_case['db_type'], 
                    test_case['db_name']
                )
                
                if connection_success:
                    logger.info(f"   ✅ Connection: SUCCESS")
                    
                    # Test query execution
                    try:
                        result = db_manager.execute_query(
                            test_case['org_id'],
                            test_case['db_type'],
                            test_case['db_name'],
                            test_case['test_query']
                        )
                        
                        if result.get('success'):
                            row_count = result.get('row_count', len(result.get('data', [])))
                            logger.info(f"   ✅ Query: SUCCESS - {row_count} records found")
                            
                            # Show sample data
                            if result.get('data') and len(result['data']) > 0:
                                sample = result['data'][0]
                                if isinstance(sample, dict):
                                    keys = list(sample.keys())[:3]  # Show first 3 columns
                                    logger.info(f"   📊 Sample columns: {', '.join(keys)}")
                        else:
                            logger.warning(f"   ⚠️ Query: {result.get('error', 'Unknown error')}")
                            
                    except Exception as e:
                        logger.warning(f"   ⚠️ Query Error: {str(e)[:100]}...")
                        
                else:
                    logger.error(f"   ❌ Connection: FAILED")
                    
            except Exception as e:
                logger.error(f"   ❌ Error: {str(e)[:100]}...")
                
        logger.info("\n3️⃣  Testing Sample Queries...")
        
        sample_queries = [
            ('org-001', 'Show me all products'),
            ('org-002', 'How many patients do we have?'),
            ('org-003', 'What is the total balance across all accounts?'),
            ('org-004', 'List all products'),
            ('org-005', 'How many students are enrolled?')
        ]
        
        for org_id, query in sample_queries:
            try:
                # This would normally go through the NLP2SQL engine
                # For now, just test basic connectivity
                org_info = {
                    'org-001': ('sqlite', 'techcorp_db'),
                    'org-002': ('mysql', 'healthplus_db'), 
                    'org-003': ('postgresql', 'financehub_db'),
                    'org-004': ('mongodb', 'retailmax_db'),
                    'org-005': ('mysql', 'edulearn_db')
                }
                
                if org_id in org_info:
                    db_type, db_name = org_info[org_id]
                    connected = db_manager.test_connection(org_id, db_type, db_name)
                    status = "✅" if connected else "❌"
                    logger.info(f"   {status} {org_id}: \"{query}\" - Connection {'OK' if connected else 'Failed'}")
                    
            except Exception as e:
                logger.error(f"   ❌ {org_id}: Query test failed - {str(e)[:50]}...")
                
        logger.info("\n🎉 Multi-Database Test Complete!")
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}")
        logger.info("Make sure all required packages are installed: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")

def test_environment_setup():
    """Test environment configuration"""
    logger.info("\n🔧 Testing Environment Setup...")
    
    # Check for required environment variables
    required_vars = [
        'HEALTHPLUS_DB_HOST', 'HEALTHPLUS_DB_PASSWORD',
        'FINANCEHUB_DB_HOST', 'FINANCEHUB_DB_PASSWORD', 
        'RETAILMAX_DB_HOST', 'RETAILMAX_DB_PASSWORD',
        'EDULEARN_DB_HOST', 'EDULEARN_DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            
    if missing_vars:
        logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        logger.info("   Create .env file from .env.example and set your database credentials")
    else:
        logger.info("✅ All required environment variables are set")
        
    # Check for required files
    required_files = [
        'docker-compose.yml',
        'src/database.py',
        'src/models.py',
        'streamlit_app.py'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            logger.info(f"✅ {file_path} - Found")
        else:
            logger.error(f"❌ {file_path} - Missing")
            
    # Check database directories
    db_dirs = ['database/healthplus', 'database/financehub', 'database/retailmax', 
              'database/edulearn', 'database/techcorp']
    
    for db_dir in db_dirs:
        if Path(db_dir).exists():
            logger.info(f"✅ {db_dir} - Found") 
        else:
            logger.warning(f"⚠️ {db_dir} - Missing")

def main():
    """Main test function"""
    logger.info("="*60)
    logger.info("🚀 MULTI-TENANT NLP2SQL DATABASE TEST")
    logger.info("="*60)
    
    # Test environment setup
    test_environment_setup()
    
    # Test database connections
    test_database_connections()
    
    logger.info("\n" + "="*60)
    logger.info("✨ Test completed! Check the logs above for any issues.")
    logger.info("="*60)
    
    # Instructions
    logger.info("""
Next steps:
1. If you see connection errors, start the databases with:
   python start_multi_db_system.py docker
   
2. To start the application:
   python start_multi_db_system.py local   (for development)
   python start_multi_db_system.py docker  (for full system)
   
3. Open the Streamlit app at: http://localhost:8501
""")

if __name__ == '__main__':
    main()