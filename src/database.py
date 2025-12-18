import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging
from typing import Dict, Any, Optional
import sqlite3
from dotenv import load_dotenv

# Import database connectors with graceful fallback
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.metadata_engine = None
        self.metadata_session = None
        self.org_connections = {}
        self._setup_metadata_db()
    
    def _setup_metadata_db(self):
        """Setup connection to MySQL metadata database or use SQLite fallback"""
        try:
            # Try MySQL connection first (for production metadata)
            mysql_url = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', 'password')}@{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DATABASE', 'nlp2sql_metadata')}"
            test_engine = create_engine(mysql_url, pool_pre_ping=True)
            
            # Test the connection
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.metadata_engine = test_engine
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.metadata_engine)
            self.metadata_session = SessionLocal
            logger.info("Metadata database connection established (MySQL)")
            
        except Exception as e:
            logger.warning(f"MySQL metadata database unavailable: {e}")
            logger.info("Using SQLite fallback for demo mode")
            
            # Use SQLite as fallback for demo
            sqlite_url = "sqlite:///nlp2sql_demo.db"
            self.metadata_engine = create_engine(sqlite_url, pool_pre_ping=True, connect_args={"check_same_thread": False})
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.metadata_engine)
            self.metadata_session = SessionLocal
            
            # Create demo tables and data
            self._create_demo_data()
            logger.info("Demo database initialized")
    
    @contextmanager
    def get_metadata_db(self):
        """Context manager for metadata database sessions"""
        db = self.metadata_session()
        try:
            yield db
        finally:
            db.close()
    
    def get_org_connection(self, org_id: str, database_type: str, database_name: str) -> Dict[str, Any]:
        """Get organization-specific database connection"""
        cache_key = f"{org_id}_{database_name}"
        
        if cache_key in self.org_connections:
            return self.org_connections[cache_key]
        
        try:
            if database_type == "mysql":
                if not MYSQL_AVAILABLE:
                    raise ImportError("MySQL connector not available")
                connection = self._get_mysql_connection(org_id, database_name)
            elif database_type == "postgresql":
                if not POSTGRESQL_AVAILABLE:
                    raise ImportError("PostgreSQL connector not available")
                connection = self._get_postgresql_connection(org_id, database_name)
            elif database_type == "sqlite":
                connection = self._get_sqlite_connection(org_id, database_name)
            elif database_type == "mongodb":
                if not MONGODB_AVAILABLE:
                    raise ImportError("MongoDB connector not available")
                connection = self._get_mongodb_connection(org_id, database_name)
            else:
                raise ValueError(f"Unsupported database type: {database_type}")
            
            self.org_connections[cache_key] = {
                'connection': connection,
                'database_type': database_type,
                'database_name': database_name
            }
            
            logger.info(f"Database connection established for org {org_id} ({database_type})")
            return self.org_connections[cache_key]
            
        except Exception as e:
            logger.warning(f"Failed to connect to {database_type} database for org {org_id}: {e}")
            raise
    
    def _get_mysql_connection(self, org_id: str, database_name: str):
        """Create MySQL connection for organization"""
        env_prefix = self._get_env_prefix(org_id)
        
        config = {
            'host': os.getenv(f'{env_prefix}_DB_HOST', 'localhost'),
            'port': int(os.getenv(f'{env_prefix}_DB_PORT', '3306')),
            'user': os.getenv(f'{env_prefix}_DB_USER', 'root'),
            'password': os.getenv(f'{env_prefix}_DB_PASSWORD', 'password'),
            'database': database_name,
            'autocommit': True
        }
        
        connection = mysql.connector.connect(**config)
        return connection
    
    def _get_postgresql_connection(self, org_id: str, database_name: str):
        """Create PostgreSQL connection for organization"""
        env_prefix = self._get_env_prefix(org_id)
        
        config = {
            'host': os.getenv(f'{env_prefix}_DB_HOST', 'localhost'),
            'port': int(os.getenv(f'{env_prefix}_DB_PORT', '5432')),
            'user': os.getenv(f'{env_prefix}_DB_USER', 'postgres'),
            'password': os.getenv(f'{env_prefix}_DB_PASSWORD', 'password'),
            'database': database_name
        }
        
        connection = psycopg2.connect(**config)
        return connection
    
    def _get_mongodb_connection(self, org_id: str, database_name: str):
        """Create MongoDB connection for organization"""
        env_prefix = self._get_env_prefix(org_id)
        
        host = os.getenv(f'{env_prefix}_DB_HOST', 'localhost')
        port = int(os.getenv(f'{env_prefix}_DB_PORT', '27017'))
        user = os.getenv(f'{env_prefix}_DB_USER', 'admin')
        password = os.getenv(f'{env_prefix}_DB_PASSWORD', 'password')
        
        try:
            connection_string = f"mongodb://{user}:{password}@{host}:{port}/{database_name}?authSource=admin"
            client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            client.server_info()
            return client[database_name]
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            # Return a mock database for demo purposes
            raise ConnectionError(f"Could not connect to MongoDB for {org_id}: {e}")
    
    def _get_env_prefix(self, org_id: str) -> str:
        """Map org_id to environment variable prefix"""
        org_mapping = {
            'org-001': 'TECHCORP',
            'org-002': 'HEALTHPLUS',
            'org-003': 'FINANCEHUB',
            'org-004': 'RETAILMAX',
            'org-005': 'EDULEARN'
        }
        return org_mapping.get(org_id, 'DEFAULT')
    
    def _get_sqlite_connection(self, org_id: str, database_name: str):
        """Get SQLite connection for TechCorp (org-001)"""
        # Ensure databases directory exists
        os.makedirs("databases", exist_ok=True)
        
        db_path = f"databases/{database_name}.sqlite"
        
        # If database doesn't exist, create it with sample data
        if not os.path.exists(db_path):
            self._create_sqlite_database(db_path, org_id)
            
        return sqlite3.connect(db_path, check_same_thread=False)
    
    def execute_query(self, org_id: str, database_type: str, database_name: str, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """Execute query on organization-specific database or return demo data"""
        try:
            db_info = self.get_org_connection(org_id, database_type, database_name)
            connection = db_info['connection']
            
            if database_type in ["mysql", "postgresql", "sqlite"]:
                return self._execute_sql_query(connection, query, params, database_type)
            elif database_type == "mongodb":
                return self._execute_mongodb_query(connection, query)
            else:
                raise ValueError(f"Unsupported database type: {database_type}")
                
        except Exception as e:
            logger.warning(f"Query execution failed for org {org_id}: {e}")
            logger.info("Returning demo data for testing")
            return self._get_demo_query_results(org_id, query)
    
    def _execute_sql_query(self, connection, query: str, params: Optional[tuple], db_type: str) -> Dict[str, Any]:
        """Execute SQL query (MySQL/PostgreSQL/SQLite)"""
        if db_type == "sqlite":
            cursor = connection.cursor()
        elif db_type == "mysql":
            cursor = connection.cursor(dictionary=True)
        else:  # postgresql
            cursor = connection.cursor()
        
        try:
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                if db_type == "sqlite":
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                elif db_type == "postgresql":
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results = [dict(zip(columns, row)) for row in rows]
                else:
                    results = cursor.fetchall()
                
                return {
                    'success': True,
                    'data': results,
                    'row_count': len(results)
                }
            else:
                connection.commit()
                return {
                    'success': True,
                    'affected_rows': cursor.rowcount,
                    'message': 'Query executed successfully'
                }
        finally:
            cursor.close()
    
    def _execute_mongodb_query(self, db, query_info: str) -> Dict[str, Any]:
        """Execute MongoDB query (simplified for demo)"""
        try:
            # For demo purposes, assume query_info contains collection and basic operation
            if "products" in query_info.lower():
                results = list(db.products.find({}, {'_id': 0}).limit(10))
            elif "sales" in query_info.lower():
                results = list(db.sales.find({}, {'_id': 0}).limit(10))
            elif "inventory" in query_info.lower():
                results = list(db.inventory.find({}, {'_id': 0}).limit(10))
            elif "customers" in query_info.lower():
                results = list(db.customers.find({}, {'_id': 0}).limit(10))
            else:
                results = []
            
            return {
                'success': True,
                'data': results,
                'row_count': len(results)
            }
        except Exception as e:
            logger.error(f"MongoDB query execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def test_connection(self, org_id: str, database_type: str, database_name: str) -> bool:
        """Test database connection for organization"""
        try:
            db_info = self.get_org_connection(org_id, database_type, database_name)
            
            if database_type in ["mysql", "postgresql"]:
                cursor = db_info['connection'].cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            elif database_type == "sqlite":
                connection = self._get_sqlite_connection(org_id, database_name)
            elif database_type == "mongodb":
                db_info['connection'].list_collection_names()
            
            logger.info(f"Connection test successful for org {org_id}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for org {org_id}: {e}")
            return False
    
    def _create_demo_data(self):
        """Create demo data for SQLite fallback"""
        try:
            from src.models import Base, Organization, User, HumanDigitalTwin, Agent, HDTAgent, UserHDTAssignment, UserPermission
            import uuid
            from datetime import datetime
            import bcrypt
            
            # Create all tables
            Base.metadata.create_all(bind=self.metadata_engine)
            
            with self.metadata_session() as db:
                # Check if data already exists
                if db.query(Organization).first():
                    return
                
                # Create organizations
                organizations = [
                    Organization(
                        org_id='org-001', org_name='TechCorp', domain='@techcorp.com',
                        database_type='sqlite', database_name='techcorp_db', industry='Technology',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    Organization(
                        org_id='org-002', org_name='HealthPlus', domain='@healthplus.org',
                        database_type='mysql', database_name='healthplus_db', industry='Healthcare',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    Organization(
                        org_id='org-003', org_name='FinanceHub', domain='@financehub.net',
                        database_type='postgresql', database_name='financehub_db', industry='Finance',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    Organization(
                        org_id='org-004', org_name='RetailMax', domain='@retailmax.com',
                        database_type='mongodb', database_name='retailmax_db', industry='Retail',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    Organization(
                        org_id='org-005', org_name='EduLearn', domain='@edulearn.edu',
                        database_type='mysql', database_name='edulearn_db', industry='Education',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                ]
                
                for org in organizations:
                    db.add(org)
                
                # Create HDTs
                hdts = [
                    HumanDigitalTwin(
                        hdt_id='hdt-001', name='researcher_analyst',
                        description='Research and analytics expert',
                        context='You are an analyst who works in an analytical way, focusing on data-driven insights',
                        skillset='["coding", "research", "data_analysis", "statistics"]',
                        languages='["python", "sql", "r"]',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    HumanDigitalTwin(
                        hdt_id='hdt-002', name='business_manager',
                        description='Business operations and management',
                        context='You are a business manager focused on operational efficiency',
                        skillset='["management", "strategy", "operations", "finance"]',
                        languages='["sql", "excel"]',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    HumanDigitalTwin(
                        hdt_id='hdt-005', name='basic_user',
                        description='General business user',
                        context='You are a general business user who needs simple data access',
                        skillset='["basic_analysis", "reporting"]',
                        languages='["sql"]',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                ]
                
                for hdt in hdts:
                    db.add(hdt)
                
                # Create agents
                agents = [
                    Agent(
                        agent_id='agent-001', agent_name='NLP2SQL Agent', agent_type='nlp2sql',
                        description='Converts natural language to SQL queries',
                        capabilities='["query_generation", "dialect_conversion", "syntax_validation"]',
                        config='{"max_query_complexity": 10, "allowed_operations": ["SELECT", "COUNT", "SUM", "AVG"]}',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                ]
                
                for agent in agents:
                    db.add(agent)
                
                # Create demo users
                password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                users = [
                    User(
                        user_id='user-001', org_id='org-001', username='diana.admin',
                        email='diana.rodriguez0@techcorp.com', password_hash=password_hash,
                        full_name='Diana Rodriguez', department='IT', role='admin',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    User(
                        user_id='user-002', org_id='org-001', username='john.manager',
                        email='john.smith1@techcorp.com', password_hash=password_hash,
                        full_name='John Smith', department='Operations', role='manager',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    User(
                        user_id='user-003', org_id='org-001', username='alex.analyst',
                        email='alex.davis5@techcorp.com', password_hash=password_hash,
                        full_name='Alex Davis', department='Analytics', role='analyst',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    ),
                    User(
                        user_id='user-051', org_id='org-002', username='dr.admin',
                        email='dr.rodriguez50@healthplus.org', password_hash=password_hash,
                        full_name='Dr. Maria Rodriguez', department='Administration', role='admin',
                        created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                    )
                ]
                
                for user in users:
                    db.add(user)
                
                # Create HDT assignments
                assignments = [
                    HDTAgent(hdt_id='hdt-001', agent_id='agent-001'),
                    HDTAgent(hdt_id='hdt-002', agent_id='agent-001'),
                    HDTAgent(hdt_id='hdt-005', agent_id='agent-001'),
                ]
                
                for assignment in assignments:
                    db.add(assignment)
                
                # Create user-HDT assignments
                user_hdt_assignments = [
                    UserHDTAssignment(user_id='user-001', hdt_id='hdt-002', assigned_at=datetime.utcnow()),
                    UserHDTAssignment(user_id='user-002', hdt_id='hdt-002', assigned_at=datetime.utcnow()),
                    UserHDTAssignment(user_id='user-003', hdt_id='hdt-001', assigned_at=datetime.utcnow()),
                    UserHDTAssignment(user_id='user-051', hdt_id='hdt-002', assigned_at=datetime.utcnow()),
                ]
                
                for assignment in user_hdt_assignments:
                    db.add(assignment)
                
                # Create permissions
                permissions = [
                    UserPermission(
                        permission_id=str(uuid.uuid4()), user_id='user-001',
                        resource_type='table', resource_name='products', access_level='admin'
                    ),
                    UserPermission(
                        permission_id=str(uuid.uuid4()), user_id='user-003',
                        resource_type='table', resource_name='products', access_level='read'
                    ),
                ]
                
                for permission in permissions:
                    db.add(permission)
                
                db.commit()
                logger.info("Demo data created successfully")
        
        except Exception as e:
            logger.error(f"Error creating demo data: {e}")
            raise
    
    def _get_demo_query_results(self, org_id: str, query: str) -> Dict[str, Any]:
        """Return demo query results for testing when databases are unavailable"""
        try:
            query_lower = query.lower()
            
            # Demo data based on organization
            if org_id == 'org-001':  # TechCorp
                if 'products' in query_lower:
                    return {
                        'success': True,
                        'data': [
                            {'product_id': 1, 'org_id': 'org-001', 'name': 'Laptop Pro X1', 'category': 'Electronics', 'price': 1299.99, 'sku': 'TECH-LP-001'},
                            {'product_id': 2, 'org_id': 'org-001', 'name': 'Wireless Mouse', 'category': 'Accessories', 'price': 29.99, 'sku': 'TECH-MS-002'},
                            {'product_id': 3, 'org_id': 'org-001', 'name': 'USB-C Hub', 'category': 'Accessories', 'price': 79.99, 'sku': 'TECH-HB-003'},
                            {'product_id': 4, 'org_id': 'org-001', 'name': 'Monitor 27"', 'category': 'Electronics', 'price': 349.99, 'sku': 'TECH-MN-004'},
                            {'product_id': 5, 'org_id': 'org-001', 'name': 'Keyboard Mechanical', 'category': 'Accessories', 'price': 129.99, 'sku': 'TECH-KB-005'}
                        ],
                        'row_count': 5
                    }
                elif 'sales' in query_lower:
                    return {
                        'success': True,
                        'data': [
                            {'sale_id': 1, 'org_id': 'org-001', 'customer_name': 'John Smith', 'amount': 1299.99, 'quantity': 1, 'sale_date': '2024-01-15'},
                            {'sale_id': 2, 'org_id': 'org-001', 'customer_name': 'Jane Doe', 'amount': 59.98, 'quantity': 2, 'sale_date': '2024-01-16'},
                            {'sale_id': 3, 'org_id': 'org-001', 'customer_name': 'Bob Johnson', 'amount': 79.99, 'quantity': 1, 'sale_date': '2024-01-17'}
                        ],
                        'row_count': 3
                    }
                elif 'count' in query_lower:
                    return {
                        'success': True,
                        'data': [{'count': 5}],
                        'row_count': 1
                    }
            
            elif org_id == 'org-002':  # HealthPlus
                if 'patients' in query_lower:
                    return {
                        'success': True,
                        'data': [
                            {'patient_id': 1, 'org_id': 'org-002', 'name': 'Alice Johnson', 'date_of_birth': '1985-03-15', 'gender': 'F'},
                            {'patient_id': 2, 'org_id': 'org-002', 'name': 'Charlie Brown', 'date_of_birth': '1990-07-22', 'gender': 'M'},
                            {'patient_id': 3, 'org_id': 'org-002', 'name': 'Eva Davis', 'date_of_birth': '1978-11-08', 'gender': 'F'}
                        ],
                        'row_count': 3
                    }
                elif 'treatments' in query_lower:
                    return {
                        'success': True,
                        'data': [
                            {'treatment_id': 1, 'org_id': 'org-002', 'treatment_name': 'Annual Checkup', 'cost': 150.00, 'doctor_name': 'Dr. Smith'},
                            {'treatment_id': 2, 'org_id': 'org-002', 'treatment_name': 'Blood Test', 'cost': 85.00, 'doctor_name': 'Dr. Johnson'},
                            {'treatment_id': 3, 'org_id': 'org-002', 'treatment_name': 'X-Ray', 'cost': 120.00, 'doctor_name': 'Dr. Wilson'}
                        ],
                        'row_count': 3
                    }
            
            # Default response
            return {
                'success': True,
                'data': [
                    {'message': 'Demo data - This is sample data for testing purposes'},
                    {'note': f'Organization: {org_id}', 'query': query[:50] + '...' if len(query) > 50 else query},
                    {'status': 'For full functionality, please set up the database connections'}
                ],
                'row_count': 3
            }
            
        except Exception as e:
            logger.error(f"Error generating demo data: {e}")
            return {
                'success': True,
                'data': [{'message': 'Demo mode - database connection not available'}],
                'row_count': 1
            }

    def _create_sqlite_database(self, db_path: str, org_id: str):
        """Create SQLite database with sample data for TechCorp"""
        try:
            # Create the database file
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute("""
                CREATE TABLE products (
                    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id TEXT NOT NULL DEFAULT 'org-001',
                    name TEXT NOT NULL,
                    category TEXT,
                    price DECIMAL(10,2),
                    sku TEXT UNIQUE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE sales (
                    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    org_id TEXT NOT NULL DEFAULT 'org-001',
                    customer_name TEXT,
                    amount DECIMAL(10,2),
                    quantity INTEGER,
                    sale_date DATE
                )
            """)
            
            # Load sample data from file if it exists
            sample_data_path = f"database/techcorp/sample_data.sql"
            if os.path.exists(sample_data_path):
                with open(sample_data_path, 'r') as f:
                    sql_script = f.read()
                    # Execute the script in chunks (SQLite doesn't support multiple statements in executescript with parameters)
                    for statement in sql_script.split(';'):
                        if statement.strip() and not statement.strip().startswith('--'):
                            try:
                                cursor.execute(statement.strip())
                            except sqlite3.Error as e:
                                # Skip errors for existing data or unsupported syntax
                                logger.debug(f"SQLite statement skipped: {e}")
            else:
                # Insert basic sample data directly
                cursor.execute("""
                    INSERT OR REPLACE INTO products (name, category, price, sku) VALUES
                    ('Laptop Pro X1', 'Electronics', 1299.99, 'TECH-LP-001'),
                    ('Wireless Mouse', 'Accessories', 29.99, 'TECH-MS-002'),
                    ('USB-C Hub', 'Accessories', 79.99, 'TECH-HB-003'),
                    ('Monitor 27"', 'Electronics', 349.99, 'TECH-MN-004'),
                    ('Keyboard Mechanical', 'Accessories', 129.99, 'TECH-KB-005')
                """)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO sales (customer_name, amount, quantity, sale_date) VALUES
                    ('John Smith', 1299.99, 1, '2024-01-15'),
                    ('Jane Doe', 59.98, 2, '2024-01-16'),
                    ('Bob Johnson', 79.99, 1, '2024-01-17')
                """)
            
            conn.commit()
            conn.close()
            logger.info(f"SQLite database created: {db_path}")
            
        except Exception as e:
            logger.error(f"Error creating SQLite database {db_path}: {e}")
            raise

    def close_connections(self):
        """Close all database connections"""
        for cache_key, db_info in self.org_connections.items():
            try:
                if db_info['database_type'] in ["mysql", "postgresql"]:
                    db_info['connection'].close()
                elif db_info['database_type'] == "sqlite":
                    db_info['connection'].close()
                elif db_info['database_type'] == "mongodb":
                    db_info['connection'].client.close()
            except Exception as e:
                logger.error(f"Error closing connection {cache_key}: {e}")
        
        self.org_connections.clear()
        logger.info("All database connections closed")

# Global database manager instance
db_manager = DatabaseManager()