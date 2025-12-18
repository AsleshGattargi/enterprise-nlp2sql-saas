import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
import logging
from sqlparse import parse, format as sql_format
from src.hdt_manager import hdt_manager
from src.auth import auth_manager
import sqlparse
import ollama

logger = logging.getLogger(__name__)

class NLP2SQLEngine:
    """Enhanced NLP-to-SQL engine with Ollama integration and local fallback"""
    
    def __init__(self):
        # Ollama configuration
        self.ollama_enabled = os.getenv('ENABLE_OLLAMA', 'false').lower() == 'true'
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'codellama:latest')
        
        if self.ollama_enabled:
            try:
                # Test Ollama connection
                ollama.Client(host=self.ollama_host).list()
                logger.info(f"Ollama client initialized successfully with model: {self.ollama_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama: {e}. Falling back to local processing.")
                self.ollama_enabled = False
        self.sql_injection_patterns = [
            r';\s*drop\s+table',
            r';\s*delete\s+from',
            r';\s*update\s+.*\s+set',
            r';\s*insert\s+into',
            r'union\s+select',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_executesql',
            r'xp_cmdshell',
            r'--\s*$',
            r'/\*.*\*/',
            r'script\s*>',
            r'<\s*script'
        ]
        
        # Enhanced NLP patterns for better query understanding including complex multi-condition queries
        # ORDER MATTERS - More specific patterns should come first
        self.query_patterns = {
            'business_intelligence': [
                # Customer-Sales Analytics (requires JOIN between customers and sales)
                r'which\s+customers?\s+bought\s+the\s+most\s+expensive\s+(products?)',  # "which customers bought the most expensive products"
                r'who\s+bought\s+the\s+most\s+expensive\s+(products?)',  # "who bought the most expensive products"
                r'top\s+(?:\d+\s+)?customers?\s+by\s+(sales?|revenue|spending)',  # "top customers by sales" or "top 5 customers by spending"
                r'customers?\s+who\s+spent\s+the\s+most',  # "customers who spent the most"
                r'customers?\s+who\s+spent\s+over\s+\$?(\d+)',  # "customers who spent over $500"
                r'show\s+me\s+top\s+(\d+)\s+customers?\s+by\s+spending',  # "show me top 5 customers by spending"
                r'which\s+customers?\s+bought\s+(products?)\s+in\s+(\w+)\s+category',  # "which customers bought products in Electronics category"
                
                # Product-Sales Analytics (requires JOIN between products and sales)
                r'(?:best|top)\s+(?:\d+\s+)?selling\s+(products?)',  # "best selling products" or "top 5 selling products"
                r'most\s+popular\s+(products?)',  # "most popular products"
                r'which\s+(products?)\s+sold\s+the\s+most',  # "which products sold the most"
                r'(products?)\s+that\s+sold\s+more\s+than\s+(\d+)\s+units?',  # "products that sold more than 10 units"
                r'top\s+(?:\d+\s+)?(products?)\s+by\s+(sales?|revenue)',  # "top products by sales" or "top 5 products by sales"
                r'(products?)\s+with\s+highest\s+(sales?|revenue)',  # "products with highest sales"
                
                # Inventory Analytics (requires JOIN between products and inventory)
                r'what\s+(products?)\s+are\s+running\s+low\s+in\s+stock',  # "what products are running low in stock"
                r'which\s+(products?)\s+have\s+low\s+(inventory|stock)',  # "which products have low inventory"
                r'(products?)\s+with\s+less\s+than\s+(\d+)\s+in\s+stock',  # "products with less than 50 in stock"
                r'show\s+me\s+low\s+stock\s+(products?)',  # "show me low stock products"
                r'(products?)\s+that\s+need\s+restocking',  # "products that need restocking"
                r'inventory\s+levels\s+for\s+(\w+)\s+category',  # "inventory levels for Electronics category"
                r'which\s+warehouse\s+has\s+the\s+most\s+inventory',  # "which warehouse has the most inventory"
                
                # Sales Performance Analytics (complex aggregations)
                r'total\s+(sales?|revenue)\s+by\s+(month|quarter|year)',  # "total sales by month"
                r'(sales?|revenue)\s+trend\s+over\s+time',  # "sales trend over time"
                r'average\s+order\s+value\s+per\s+customer',  # "average order value per customer"
                r'(sales?|revenue)\s+by\s+(\w+)\s+category',  # "sales by Electronics category"
                r'monthly\s+(sales?|revenue)\s+report',  # "monthly sales report"
                
                # Cross-table Analytics
                r'customers?\s+with\s+no\s+recent\s+(purchases?|orders?)',  # "customers with no recent purchases"
                r'(products?)\s+never\s+sold',  # "products never sold"
                r'customers?\s+who\s+bought\s+multiple\s+(products?)',  # "customers who bought multiple products"
            ],
            'count_complex_filter': [
                r'how\s+many\s+(products?)\s+cost\s+less\s+than\s+\$?(\d+)',  # Specific to products
                r'how\s+many\s+(\w+)\s+under\s+\$?(\d+)',
                r'count\s+(products?)\s+cost\s+less\s+than\s+\$?(\d+)',
                r'count\s+(\w+)\s+under\s+\$?(\d+)',
            ],
            'filter_less': [
                r'show\s+me\s+the\s+(products?)\s+cost\s+less\s+than\s+\$?(\d+)',  # "show me the products cost less than $50"
                r'show\s+(products?)\s+cost\s+less\s+than\s+\$?(\d+)',  # "show products cost less than $50"
                r'what\s+(products?)\s+cost\s+under\s+(\d+)\s+dollars?',  # "what products cost under 30 dollars"
                r'(\w+)\s+with\s+(\w+)\s+less\s+than\s+(\d+)',
                r'(\w+)\s+where\s+(\w+)\s*<\s*(\d+)',
                r'show\s+(\w+)\s+with\s+(\w+)\s+less\s+than\s+(\d+)',
                r'find\s+(\w+)\s+with\s+(\w+)\s+under\s+(\d+)',
                r'find\s+(\w+)\s+under\s+(\d+)\s+dollars?'
            ],
            'complex_multi_filter': [
                r'(\w+)\s+(\w+)\s+under\s+\$?(\d+)',  # "Electronics products under $100"
                r'(\w+)\s+(\w+)\s+over\s+\$?(\d+)', 
                r'(\w+)\s+(\w+)\s+above\s+\$?(\d+)',
                r'(\w+)\s+(\w+)\s+below\s+\$?(\d+)',
                r'(\w+)\s+(\w+)\s+less\s+than\s+\$?(\d+)',
                r'(\w+)\s+(\w+)\s+more\s+than\s+\$?(\d+)',
            ],
            'select_with_category': [
                r'show\s+me\s+(\w+)\s+in\s+(\w+)\s+category',
                r'list\s+(\w+)\s+in\s+(\w+)\s+category',
                r'find\s+(\w+)\s+in\s+(\w+)\s+category',
                r'get\s+(\w+)\s+in\s+(\w+)\s+category',
            ],
            'select_all': [
                r'show\s+me\s+all\s+(\w+)',
                r'list\s+all\s+(\w+)',
                r'get\s+all\s+(\w+)',
                r'display\s+all\s+(\w+)',
                r'what\s+are\s+all\s+the\s+(\w+)'
            ],
            'count_with_filter': [
                r'count\s+(\w+)\s+in\s+(\w+)\s+category',
                r'how\s+many\s+(\w+)\s+in\s+(\w+)\s+category',
                r'number\s+of\s+(\w+)\s+in\s+(\w+)\s+category',
                r'count\s+(\w+)\s+where\s+(\w+)\s*=\s*[\'"]?([^\'"]+)[\'"]?'
            ],
            'count': [
                r'how\s+many\s+(\w+)',
                r'count\s+(?:of\s+)?(\w+)',
                r'number\s+of\s+(\w+)',
                r'total\s+(\w+)'
            ],
            'filter_by': [
                r'(\w+)\s+where\s+(\w+)\s*=\s*[\'"]?([^\'"]+)[\'"]?',
                r'(\w+)\s+with\s+(\w+)\s*[=:]\s*[\'"]?([^\'"]+)[\'"]?',
                r'find\s+(\w+)\s+where\s+(\w+)\s+is\s+[\'"]?([^\'"]+)[\'"]?'
            ],
            'filter_greater': [
                r'show\s+(\w+)\s+with\s+(\w+)\s+greater\s+than\s+(\d+)',
                r'find\s+(\w+)\s+with\s+(\w+)\s+above\s+(\d+)',
                r'(\w+)\s+where\s+(\w+)\s*>\s*(\d+)'
            ],
            'filter_between': [
                r'find\s+(\w+)\s+with\s+(\w+)\s+between\s+(\d+)\s+and\s+(\d+)',
                r'show\s+(\w+)\s+with\s+(\w+)\s+between\s+(\d+)\s+and\s+(\d+)',
                r'(\w+)\s+with\s+(\w+)\s+from\s+(\d+)\s+to\s+(\d+)'
            ],
            'aggregate': [
                r'average\s+(\w+)',
                r'sum\s+of\s+(\w+)',
                r'total\s+(\w+)',
                r'maximum\s+(\w+)',
                r'minimum\s+(\w+)'
            ],
            'group_by': [
                r'(\w+)\s+by\s+(\w+)',
                r'group\s+(\w+)\s+by\s+(\w+)',
                r'(\w+)\s+grouped\s+by\s+(\w+)'
            ],
            'order_by': [
                r'(\w+)\s+sorted\s+by\s+(\w+)',
                r'sort\s+(\w+)\s+by\s+(\w+)',
                r'order\s+(\w+)\s+by\s+(\w+)'
            ],
            'date_range': [
                r'(\w+)\s+from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})',
                r'(\w+)\s+between\s+(\d{4}-\d{2}-\d{2})\s+and\s+(\d{4}-\d{2}-\d{2})',
                r'(\w+)\s+after\s+(\d{4}-\d{2}-\d{2})',
                r'(\w+)\s+before\s+(\d{4}-\d{2}-\d{2})'
            ]
        }
        
        # Database schema mapping (simplified for demo)
        self.schema_mapping = {
            'sqlite': {
                'techcorp_db': {
                    'products': ['product_id', 'org_id', 'name', 'category', 'price', 'sku', 'description'],
                    'inventory': ['inventory_id', 'org_id', 'product_id', 'quantity', 'warehouse'],
                    'sales': ['sale_id', 'org_id', 'product_id', 'customer_name', 'amount', 'quantity', 'sale_date'],
                    'customers': ['customer_id', 'org_id', 'name', 'email', 'phone', 'address']
                },
                'healthplus_db': {
                    'patients': ['patient_id', 'org_id', 'name', 'date_of_birth', 'gender', 'phone', 'email'],
                    'treatments': ['treatment_id', 'org_id', 'patient_id', 'treatment_name', 'cost', 'treatment_date'],
                    'appointments': ['appointment_id', 'org_id', 'patient_id', 'doctor_name', 'appointment_date'],
                    'billing': ['bill_id', 'org_id', 'patient_id', 'treatment_id', 'amount', 'status']
                },
                'financehub_db': {
                    'accounts': ['account_id', 'org_id', 'account_number', 'account_name', 'account_type', 'balance'],
                    'transactions': ['transaction_id', 'org_id', 'account_id', 'transaction_type', 'amount', 'description', 'transaction_date'],
                    'investments': ['investment_id', 'org_id', 'account_id', 'investment_name', 'investment_type', 'amount']
                },
                'retailmax_db': {
                    'products': ['product_id', 'org_id', 'name', 'category', 'price', 'sku', 'description'],
                    'sales': ['sale_id', 'org_id', 'customer_name', 'items', 'total_amount', 'sale_date'],
                    'inventory': ['inventory_id', 'org_id', 'product_id', 'total_quantity', 'warehouse'],
                    'customers': ['customer_id', 'org_id', 'name', 'email', 'loyalty_points']
                },
                'edulearn_db': {
                    'students': ['student_id', 'org_id', 'student_number', 'name', 'email', 'major', 'gpa'],
                    'courses': ['course_id', 'org_id', 'course_code', 'course_name', 'credits', 'instructor'],
                    'enrollments': ['enrollment_id', 'org_id', 'student_id', 'course_id', 'grade'],
                    'fees': ['fee_id', 'org_id', 'student_id', 'fee_type', 'amount', 'status']
                }
            },
            'postgresql': {
                'techcorp_db': {
                    'products': ['product_id', 'org_id', 'name', 'category', 'price', 'sku', 'description'],
                    'inventory': ['inventory_id', 'org_id', 'product_id', 'quantity', 'warehouse'],
                    'sales': ['sale_id', 'org_id', 'product_id', 'customer_name', 'amount', 'quantity', 'sale_date'],
                    'customers': ['customer_id', 'org_id', 'name', 'email', 'phone', 'address']
                },
                'financehub_db': {
                    'accounts': ['account_id', 'org_id', 'account_number', 'account_name', 'account_type', 'balance'],
                    'transactions': ['transaction_id', 'org_id', 'account_id', 'transaction_type', 'amount', 'description'],
                    'investments': ['investment_id', 'org_id', 'account_id', 'investment_name', 'investment_type', 'amount']
                }
            },
            'mysql': {
                'healthplus_db': {
                    'patients': ['patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'email'],
                    'treatments': ['treatment_id', 'patient_id', 'treatment_name', 'cost', 'treatment_date'],
                    'appointments': ['appointment_id', 'patient_id', 'doctor_id', 'appointment_date', 'status'],
                    'billing': ['bill_id', 'patient_id', 'treatment_id', 'amount', 'status']
                },
                'edulearn_db': {
                    'students': ['student_id', 'student_number', 'first_name', 'last_name', 'email', 'major', 'gpa', 'year_level'],
                    'courses': ['course_id', 'course_code', 'course_name', 'credits', 'instructor_id', 'semester'],
                    'enrollments': ['enrollment_id', 'student_id', 'course_id', 'grade', 'enrollment_date'],
                    'assignments': ['assignment_id', 'course_id', 'title', 'description', 'due_date'],
                    'grades': ['grade_id', 'student_id', 'assignment_id', 'points_earned', 'points_possible']
                }
            },
            'mongodb': {
                'retailmax_db': {
                    'products': ['product_id', 'org_id', 'name', 'category', 'price', 'sku'],
                    'sales': ['sale_id', 'org_id', 'customer', 'items', 'total_amount'],
                    'inventory': ['inventory_id', 'org_id', 'product_id', 'total_quantity'],
                    'customers': ['customer_id', 'org_id', 'name', 'email', 'loyalty_points']
                }
            }
        }
    
    def detect_sql_injection(self, query: str) -> bool:
        """Detect potential SQL injection attempts"""
        query_lower = query.lower()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(f"SQL injection attempt detected: {pattern}")
                return True
        return False
    
    def get_table_schema(self, database_type: str, database_name: str, table_name: str) -> List[str]:
        """Get column names for a table"""
        try:
            return self.schema_mapping.get(database_type, {}).get(database_name, {}).get(table_name, [])
        except Exception:
            return []
    
    def parse_with_ollama(self, query_text: str, database_type: str, database_name: str, org_id: str, query_approach: Dict[str, Any]) -> Dict[str, Any]:
        """Parse natural language query using Ollama with enhanced context"""
        try:
            # Get database schema for context
            available_tables = self.schema_mapping.get(database_type, {}).get(database_name, {})
            
            # Build schema context for the prompt
            schema_context = "Available tables and columns:\n"
            for table_name, columns in available_tables.items():
                schema_context += f"- {table_name}: {', '.join(columns)}\n"
            
            # Simplified and optimized prompt for better Ollama performance - using original examples
            examples = f'''Examples:
"How many products cost less than $50?" → {{"table": "products", "columns": ["COUNT(*)"], "conditions": [{{"column": "price", "operator": "<", "value": 50}}, {{"column": "org_id", "operator": "=", "value": "{org_id}"}}], "aggregation": "COUNT"}}

"Electronics products under $100" → {{"table": "products", "columns": ["*"], "conditions": [{{"column": "category", "operator": "=", "value": "Electronics"}}, {{"column": "price", "operator": "<", "value": 100}}, {{"column": "org_id", "operator": "=", "value": "{org_id}"}}], "aggregation": null}}'''
            
            # Simplified and optimized prompt for better Ollama performance
            prompt = f"""Parse this SQL query: "{query_text}"

Database: {database_type}, Tables: {', '.join(available_tables.keys()) if available_tables else 'products'}

Return JSON with:
- table: table name
- columns: ["*"] or specific columns  
- conditions: [{{"column": "name", "operator": "=|<|>|LIKE", "value": value}}]
- aggregation: COUNT|AVG|SUM|MAX|MIN or null

{examples}

Query: "{query_text}"
JSON:"""

            # Use Ollama to generate response with optimized settings
            client = ollama.Client(host=self.ollama_host)
            response = client.generate(
                model=self.ollama_model,
                prompt=prompt,
                options={
                    "temperature": 0.2,  # Low temperature for consistent results
                    "top_p": 0.8,        # Focus on most likely tokens
                    "top_k": 20,         # Limit vocabulary for faster processing
                    "num_predict": 200,  # Shorter response for JSON only
                    "repeat_penalty": 1.1,
                    "stop": ["}"]  # Stop after JSON object closes
                }
            )

            # Parse the response with enhanced error handling
            response_content = response['response'].strip()
            logger.info(f"Ollama raw response: {response_content[:200]}...")
            
            # Try to extract and parse JSON from the response
            try:
                # Since we use "}" as stop token, we may need to add it back
                if not response_content.endswith('}'):
                    response_content += '}'
                
                # Clean the response - remove any extra text and extract JSON
                if "```json" in response_content:
                    json_start = response_content.find("```json") + 7
                    json_end = response_content.find("```", json_start)
                    json_content = response_content[json_start:json_end].strip()
                elif "```" in response_content:
                    json_start = response_content.find("```") + 3
                    json_end = response_content.find("```", json_start)
                    json_content = response_content[json_start:json_end].strip()
                else:
                    # Look for JSON in the response
                    json_start = response_content.find('{')
                    json_end = response_content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_content = response_content[json_start:json_end]
                    else:
                        # If no braces found, assume the entire response is JSON
                        json_content = response_content
                
                # Ensure proper JSON closing
                if not json_content.endswith('}'):
                    json_content += '}'
                
                # Parse JSON
                parsed_query = json.loads(json_content)
                logger.info(f"Ollama parsed query: table={parsed_query.get('table', 'unknown')}, conditions={len(parsed_query.get('conditions', []))}, aggregation={parsed_query.get('aggregation', 'none')}")
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse Ollama JSON response: {e}. Response content: {response_content}")
                logger.info("Falling back to enhanced local parsing")
                return self.parse_natural_language(query_text, database_type, database_name, org_id)
            
            # Validate and enhance Ollama's response
            self._validate_and_enhance_parsed_query(parsed_query, query_text, org_id)
            
            logger.info(f"Final processed query: table={parsed_query['table']}, aggregation={parsed_query['aggregation']}, conditions={len(parsed_query['conditions'])} filters")
            return parsed_query
            
        except Exception as e:
            logger.warning(f"Ollama parsing failed: {e}. Falling back to local parsing.")
            return self.parse_natural_language(query_text, database_type, database_name, org_id)
    
    def _validate_and_enhance_parsed_query(self, parsed_query: Dict[str, Any], query_text: str, org_id: str):
        """Validate and enhance Ollama's parsed query output"""
        
        # Ensure all required fields exist with proper defaults
        required_fields = {
            'conditions': [],
            'columns': ['*'],
            'confidence': 0.7,
            'aggregation': None,
            'group_by': [],
            'order_by': [],
            'limit': None,
            'operation': 'select',
            'query_type': 'simple',
            'explanation': f'Generated query for: {query_text}'
        }
        
        for field, default_value in required_fields.items():
            if field not in parsed_query:
                parsed_query[field] = default_value
        
        # Validate and fix common issues
        
        # 1. Note: No org_id filter needed since each organization has its own database
        
        # 2. Fix aggregation consistency
        if parsed_query.get('aggregation'):
            agg_type = parsed_query['aggregation']
            if agg_type == 'COUNT' and 'COUNT(*)' not in str(parsed_query['columns']):
                parsed_query['columns'] = ['COUNT(*)']
                logger.info(f"Fixed COUNT aggregation columns")
            elif agg_type in ['SUM', 'AVG', 'MAX', 'MIN']:
                # Ensure we have the proper aggregation function in columns
                columns = parsed_query['columns']
                if not any(agg_type in str(col).upper() for col in columns):
                    # Try to infer the column from the query
                    if 'price' in query_text.lower():
                        parsed_query['columns'] = [f'{agg_type}(price)']
                    elif 'amount' in query_text.lower():
                        parsed_query['columns'] = [f'{agg_type}(amount)']
                    else:
                        parsed_query['columns'] = [f'{agg_type}(*)']
                    logger.info(f"Fixed {agg_type} aggregation columns")
        
        # 3. Normalize condition formats
        normalized_conditions = []
        for condition in parsed_query.get('conditions', []):
            if isinstance(condition, list) and len(condition) >= 3:
                # Convert array format to dict format
                normalized_conditions.append({
                    'column': condition[0],
                    'operator': condition[1],
                    'value': condition[2]
                })
            elif isinstance(condition, dict):
                # Already in dict format
                normalized_conditions.append(condition)
            else:
                logger.warning(f"Skipping invalid condition format: {condition}")
        
        parsed_query['conditions'] = normalized_conditions
        
        # 4. Validate confidence level
        if not (0.0 <= parsed_query.get('confidence', 0.7) <= 1.0):
            parsed_query['confidence'] = 0.7
            
        # 5. Ensure table name is valid
        if not parsed_query.get('table'):
            logger.warning("No table specified in parsed query")
            parsed_query['confidence'] = max(0.0, parsed_query['confidence'] - 0.3)
    
    def parse_natural_language(self, query_text: str, database_type: str, database_name: str, org_id: str) -> Dict[str, Any]:
        """Parse natural language query into structured format"""
        query_lower = query_text.lower()
        print(f"[PARSE_LOCAL] Starting enhanced parsing for: '{query_text}'")
        logger.info(f"[PARSE_LOCAL] Starting enhanced parsing for: '{query_text}'")
        
        # Initialize parsed query structure
        parsed_query = {
            'operation': 'select',
            'table': None,
            'columns': ['*'],
            'conditions': [],
            'aggregation': None,
            'group_by': [],
            'order_by': [],
            'limit': None,
            'confidence': 0.0
        }
        
        # Extract table name from available tables
        available_tables = list(self.schema_mapping.get(database_type, {}).get(database_name, {}).keys())
        print(f"[PARSE_LOCAL] Available tables: {available_tables}")
        print(f"[PARSE_LOCAL] Query lower: '{query_lower}'")
        
        for table in available_tables:
            if table in query_lower or table[:-1] in query_lower:  # singular form
                parsed_query['table'] = table
                parsed_query['confidence'] += 0.3
                print(f"[PARSE_LOCAL] Found table: {table}")
                break
        
        print(f"[PARSE_LOCAL] Final table: {parsed_query['table']}")
        if not parsed_query['table']:
            print(f"[PARSE_LOCAL] No table found - returning early!")
            return parsed_query
        
        # Pattern matching for different query types - prioritize specific patterns
        matched_pattern = None
        pattern_matched = False
        logger.info(f"[PARSE_LOCAL] Testing {len(self.query_patterns)} pattern categories")
        for pattern_type, patterns in self.query_patterns.items():
            if pattern_matched:
                break
            logger.info(f"[PARSE_LOCAL] Testing pattern category: {pattern_type}")
            for pattern in patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    logger.info(f"[PARSE_LOCAL] MATCHED pattern: {pattern_type} -> {pattern}")
                    logger.info(f"[PARSE_LOCAL] Match groups: {match.groups()}")
                    parsed_query['confidence'] += 0.2
                    matched_pattern = pattern_type
                    pattern_matched = True
                    
                    if pattern_type == 'complex_multi_filter':
                        # Handle "Electronics products under $100" format
                        if len(match.groups()) >= 3:
                            category = match.group(1)  # Electronics
                            table = match.group(2)    # products
                            price = match.group(3)    # 100
                            
                            parsed_query['table'] = table
                            parsed_query['columns'] = ['*']
                            
                            # Add category filter
                            parsed_query['conditions'].append({
                                'column': 'category',
                                'operator': '=',
                                'value': category
                            })
                            
                            # Add price filter based on the operator in the pattern
                            operator = '<' if any(op in pattern for op in ['under', 'less', 'below']) else '>'
                            parsed_query['conditions'].append({
                                'column': 'price',
                                'operator': operator,
                                'value': int(price)
                            })
                        break
                    
                    elif pattern_type == 'business_intelligence':
                        # Handle complex business intelligence queries requiring joins
                        
                        # Customer-Sales Analytics
                        if 'customers' in query_lower and ('expensive' in query_lower or 'most' in query_lower):
                            # "which customers bought the most expensive products"
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'customers_expensive_products'
                            parsed_query['table'] = 'customers'
                            parsed_query['columns'] = ['c.name', 'p.name as product_name', 'p.price', 's.amount']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'c.name = s.customer_name'},
                                {'table': 'products', 'alias': 'p', 'on': 's.product_id = p.product_id'}
                            ]
                            parsed_query['order_by'] = [{'column': 'p.price', 'direction': 'DESC'}]
                            parsed_query['limit'] = 10
                            
                        elif 'top' in query_lower and 'customers' in query_lower and ('sales' in query_lower or 'spending' in query_lower or 'revenue' in query_lower):
                            # "top customers by sales" or "show me top 5 customers by spending"
                            top_match = re.search(r'top\s+(\d+)', query_lower)
                            limit = int(top_match.group(1)) if top_match else 10
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'top_customers_by_spending'
                            parsed_query['table'] = 'customers'
                            parsed_query['columns'] = ['c.name', 'SUM(s.amount) as total_spent', 'COUNT(s.sale_id) as total_orders']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'c.name = s.customer_name'}
                            ]
                            parsed_query['group_by'] = ['c.customer_id', 'c.name']
                            parsed_query['order_by'] = [{'column': 'total_spent', 'direction': 'DESC'}]
                            parsed_query['limit'] = limit
                            
                        elif 'customers' in query_lower and 'spent over' in query_lower:
                            # "customers who spent over $500"
                            amount_match = re.search(r'over\s+\$?(\d+)', query_lower)
                            amount = int(amount_match.group(1)) if amount_match else 100
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'customers_spent_over_amount'
                            parsed_query['table'] = 'customers'
                            parsed_query['columns'] = ['c.name', 'SUM(s.amount) as total_spent']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'c.name = s.customer_name'}
                            ]
                            parsed_query['group_by'] = ['c.customer_id', 'c.name']
                            parsed_query['having'] = [{'column': 'SUM(s.amount)', 'operator': '>', 'value': amount}]
                            parsed_query['order_by'] = [{'column': 'total_spent', 'direction': 'DESC'}]
                            
                        elif 'customers' in query_lower and 'bought' in query_lower and 'category' in query_lower:
                            # "which customers bought products in Electronics category"
                            category_match = re.search(r'in\s+(\w+)\s+category', query_lower)
                            category = category_match.group(1).title() if category_match else 'Electronics'
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'customers_by_category'
                            parsed_query['table'] = 'customers'
                            parsed_query['columns'] = ['DISTINCT c.name', 'p.category', 'COUNT(s.sale_id) as purchases']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'c.name = s.customer_name'},
                                {'table': 'products', 'alias': 'p', 'on': 's.product_id = p.product_id'}
                            ]
                            parsed_query['conditions'].append({
                                'column': 'p.category',
                                'operator': '=',
                                'value': category
                            })
                            parsed_query['group_by'] = ['c.customer_id', 'c.name', 'p.category']
                            
                        # Product-Sales Analytics
                        elif 'best selling' in query_lower or 'top selling' in query_lower or 'most popular' in query_lower:
                            # "best selling products" or "top 5 products by sales"
                            top_match = re.search(r'top\s+(\d+)', query_lower)
                            limit = int(top_match.group(1)) if top_match else 10
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'best_selling_products'  
                            parsed_query['table'] = 'products'
                            parsed_query['columns'] = ['p.name', 'p.category', 'SUM(s.quantity) as total_sold', 'SUM(s.amount) as total_revenue']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'p.product_id = s.product_id'}
                            ]
                            parsed_query['group_by'] = ['p.product_id', 'p.name', 'p.category']
                            parsed_query['order_by'] = [{'column': 'total_sold', 'direction': 'DESC'}]
                            parsed_query['limit'] = limit
                            
                        elif 'products' in query_lower and 'sold more than' in query_lower:
                            # "products that sold more than 10 units"
                            units_match = re.search(r'more\s+than\s+(\d+)', query_lower)
                            units = int(units_match.group(1)) if units_match else 5
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'products_sold_over_units'
                            parsed_query['table'] = 'products'
                            parsed_query['columns'] = ['p.name', 'SUM(s.quantity) as total_sold']
                            parsed_query['joins'] = [
                                {'table': 'sales', 'alias': 's', 'on': 'p.product_id = s.product_id'}
                            ]
                            parsed_query['group_by'] = ['p.product_id', 'p.name']
                            parsed_query['having'] = [{'column': 'SUM(s.quantity)', 'operator': '>', 'value': units}]
                            parsed_query['order_by'] = [{'column': 'total_sold', 'direction': 'DESC'}]
                            
                        # Inventory Analytics
                        elif 'running low' in query_lower or 'low stock' in query_lower or 'need restocking' in query_lower:
                            # "what products are running low in stock"
                            parsed_query['operation'] = 'join_query' 
                            parsed_query['join_type'] = 'low_stock_products'
                            parsed_query['table'] = 'products'
                            parsed_query['columns'] = ['p.name', 'p.category', 'i.quantity', 'i.warehouse']
                            parsed_query['joins'] = [
                                {'table': 'inventory', 'alias': 'i', 'on': 'p.product_id = i.product_id'}
                            ]
                            parsed_query['conditions'].append({
                                'column': 'i.quantity',
                                'operator': '<',
                                'value': 100  # Low stock threshold
                            })
                            parsed_query['order_by'] = [{'column': 'i.quantity', 'direction': 'ASC'}]
                            
                        elif 'products with less than' in query_lower and 'stock' in query_lower:
                            # "products with less than 50 in stock"
                            stock_match = re.search(r'less\s+than\s+(\d+)', query_lower)
                            stock_threshold = int(stock_match.group(1)) if stock_match else 50
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'products_low_stock_threshold'
                            parsed_query['table'] = 'products'
                            parsed_query['columns'] = ['p.name', 'p.category', 'i.quantity']
                            parsed_query['joins'] = [
                                {'table': 'inventory', 'alias': 'i', 'on': 'p.product_id = i.product_id'}
                            ]
                            parsed_query['conditions'].append({
                                'column': 'i.quantity',
                                'operator': '<',
                                'value': stock_threshold
                            })
                            parsed_query['order_by'] = [{'column': 'i.quantity', 'direction': 'ASC'}]
                            
                        elif 'inventory levels' in query_lower and 'category' in query_lower:
                            # "inventory levels for Electronics category"
                            category_match = re.search(r'for\s+(\w+)\s+category', query_lower)
                            category = category_match.group(1).title() if category_match else 'Electronics'
                            
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'inventory_by_category'
                            parsed_query['table'] = 'products'
                            parsed_query['columns'] = ['p.name', 'p.category', 'i.quantity', 'i.warehouse']
                            parsed_query['joins'] = [
                                {'table': 'inventory', 'alias': 'i', 'on': 'p.product_id = i.product_id'}
                            ]
                            parsed_query['conditions'].append({
                                'column': 'p.category',
                                'operator': '=',
                                'value': category
                            })
                            parsed_query['order_by'] = [{'column': 'i.quantity', 'direction': 'DESC'}]
                            
                        elif 'warehouse' in query_lower and 'most inventory' in query_lower:
                            # "which warehouse has the most inventory"
                            parsed_query['operation'] = 'join_query'
                            parsed_query['join_type'] = 'warehouse_inventory_totals'
                            parsed_query['table'] = 'inventory'
                            parsed_query['columns'] = ['i.warehouse', 'SUM(i.quantity) as total_inventory']
                            parsed_query['group_by'] = ['i.warehouse']
                            parsed_query['order_by'] = [{'column': 'total_inventory', 'direction': 'DESC'}]
                            parsed_query['limit'] = 1
                            
                        break
                    
                    elif pattern_type == 'count_complex_filter':
                        # Handle "how many products cost less than $50" format
                        parsed_query['aggregation'] = 'COUNT'
                        parsed_query['columns'] = ['COUNT(*)']
                        
                        if len(match.groups()) >= 2:
                            table = match.group(1)  # products
                            price = match.group(2)  # 50
                            
                            # For product cost queries, always use 'products' table
                            parsed_query['table'] = 'products'
                                
                            parsed_query['conditions'].append({
                                'column': 'price',
                                'operator': '<',
                                'value': int(price)
                            })
                        break
                    
                    elif pattern_type == 'select_with_category':
                        # Handle "show me products in Electronics category" format
                        if len(match.groups()) >= 2:
                            table = match.group(1)     # products
                            category = match.group(2)  # Electronics
                            
                            parsed_query['table'] = table
                            parsed_query['columns'] = ['*']
                            parsed_query['conditions'].append({
                                'column': 'category',
                                'operator': '=',
                                'value': category
                            })
                        break
                    
                    elif pattern_type == 'select_all':
                        parsed_query['columns'] = ['*']
                        break
                    
                    elif pattern_type == 'count_with_filter':
                        parsed_query['aggregation'] = 'COUNT'
                        parsed_query['columns'] = ['COUNT(*)']
                        if len(match.groups()) >= 2:
                            # Handle "count products in Electronics category" format
                            if 'category' in pattern:
                                category_value = match.group(2)
                                parsed_query['conditions'].append({
                                    'column': 'category',
                                    'operator': '=',
                                    'value': category_value
                                })
                            elif len(match.groups()) >= 3:
                                # Handle "count products where category = Electronics" format
                                column = match.group(2)
                                value = match.group(3)
                                parsed_query['conditions'].append({
                                    'column': column,
                                    'operator': '=',
                                    'value': value
                                })
                        break
                    
                    elif pattern_type == 'count':
                        # Skip generic count if we already matched a more specific count pattern
                        if matched_pattern != 'count_with_filter':
                            parsed_query['aggregation'] = 'COUNT'
                            parsed_query['columns'] = ['COUNT(*)']
                        break
                    
                    elif pattern_type == 'filter_by':
                        if len(match.groups()) >= 3:
                            column = match.group(2)
                            value = match.group(3)
                            parsed_query['conditions'].append({
                                'column': column,
                                'operator': '=',
                                'value': value
                            })
                        break
                    
                    elif pattern_type == 'filter_greater':
                        if len(match.groups()) >= 3:
                            column = match.group(2) if len(match.groups()) >= 3 else 'price'
                            value = match.group(3) if len(match.groups()) >= 3 else match.group(2)
                            parsed_query['conditions'].append({
                                'column': column,
                                'operator': '>',
                                'value': int(value)
                            })
                    
                    elif pattern_type == 'filter_less':
                        if len(match.groups()) >= 2:
                            # Handle specific "products cost less than" patterns
                            if len(match.groups()) == 2:
                                # Patterns like "show me the products cost less than $50"
                                table = match.group(1)  # products
                                value = match.group(2)  # 50
                                parsed_query['table'] = table
                                parsed_query['columns'] = ['*']
                                parsed_query['conditions'].append({
                                    'column': 'price',
                                    'operator': '<',
                                    'value': int(value)
                                })
                            else:
                                # Original patterns with table, column, value
                                column = match.group(2)
                                value = match.group(3)
                                parsed_query['conditions'].append({
                                    'column': column,
                                    'operator': '<',
                                    'value': int(value)
                                })
                    
                    elif pattern_type == 'filter_between':
                        if len(match.groups()) >= 4:
                            column = match.group(2)
                            value1 = match.group(3)
                            value2 = match.group(4)
                            parsed_query['conditions'].extend([
                                {
                                    'column': column,
                                    'operator': '>=',
                                    'value': int(value1)
                                },
                                {
                                    'column': column,
                                    'operator': '<=',
                                    'value': int(value2)
                                }
                            ])
                    
                    elif pattern_type == 'aggregate':
                        agg_type = 'AVG' if 'average' in pattern else 'SUM' if 'sum' in pattern else 'MAX' if 'maximum' in pattern else 'MIN'
                        parsed_query['aggregation'] = agg_type
                        if len(match.groups()) >= 1:
                            column = match.group(1)
                            parsed_query['columns'] = [f'{agg_type}({column})']
                    
                    elif pattern_type == 'group_by':
                        if len(match.groups()) >= 2:
                            group_column = match.group(2)
                            parsed_query['group_by'].append(group_column)
                    
                    elif pattern_type == 'order_by':
                        if len(match.groups()) >= 2:
                            order_column = match.group(2)
                            parsed_query['order_by'].append(order_column)
        
        # Note: No org_id filter needed since each organization has its own database
        
        return parsed_query
    
    def generate_sql(self, parsed_query: Dict[str, Any], database_type: str, user_id: str) -> str:
        """Generate SQL query from parsed structure with dialect awareness"""
        
        if not parsed_query['table']:
            raise ValueError("No table identified in query")
        
        if parsed_query['confidence'] < 0.3:
            raise ValueError("Query confidence too low, please be more specific")
        
        # Check user permissions
        if not auth_manager.check_user_permission(user_id, 'table', parsed_query['table'], 'read'):
            # Get user info for better error message
            user_info = auth_manager.get_user_by_id(user_id)
            user_role = user_info.get('role', 'unknown') if user_info else 'unknown'
            
            # Create user-friendly permission error message
            permission_message = self._create_permission_error_message(
                user_role, parsed_query['table'], user_id
            )
            raise PermissionError(permission_message)
        
        # Build SQL query based on database type
        if database_type == 'mongodb':
            return self._generate_mongodb_query(parsed_query)
        else:
            return self._generate_sql_query(parsed_query, database_type)
    
    def _generate_sql_query(self, parsed_query: Dict[str, Any], database_type: str) -> str:
        """Generate SQL query for MySQL/PostgreSQL with join support"""
        
        # Handle join queries differently
        if parsed_query.get('operation') == 'join_query':
            return self._generate_join_query(parsed_query, database_type)
        
        # SELECT clause
        columns = ', '.join(parsed_query['columns'])
        sql_parts = [f"SELECT {columns}"]
        
        # FROM clause
        sql_parts.append(f"FROM {parsed_query['table']}")
        
        # WHERE clause
        if parsed_query['conditions']:
            where_conditions = []
            for condition in parsed_query['conditions']:
                column = condition['column']
                operator = condition['operator']
                value = condition['value']
                
                # Handle different data types
                if isinstance(value, str) and not value.isdigit():
                    value = f"'{value}'"
                
                where_conditions.append(f"{column} {operator} {value}")
            
            sql_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        # GROUP BY clause
        if parsed_query['group_by']:
            group_columns = ', '.join(parsed_query['group_by'])
            sql_parts.append(f"GROUP BY {group_columns}")
        
        # ORDER BY clause
        if parsed_query['order_by']:
            order_columns = ', '.join(parsed_query['order_by'])
            sql_parts.append(f"ORDER BY {order_columns}")
        
        # LIMIT clause (PostgreSQL style)
        if parsed_query['limit']:
            if database_type == 'postgresql':
                sql_parts.append(f"LIMIT {parsed_query['limit']}")
            else:  # MySQL
                sql_parts.append(f"LIMIT {parsed_query['limit']}")
        
        sql_query = ' '.join(sql_parts)
        
        # Format SQL for readability
        formatted_sql = sql_format(sql_query, reindent=True, keyword_case='upper')
        
        return formatted_sql
    
    def _generate_join_query(self, parsed_query: Dict[str, Any], database_type: str) -> str:
        """Generate complex SQL queries with joins for business intelligence"""
        
        join_type = parsed_query.get('join_type')
        org_id = next((c['value'] for c in parsed_query.get('conditions', []) if c.get('column') == 'org_id'), 'org-001')
        limit = parsed_query.get('limit', 10)
        
        
        # Customer-Sales Analytics
        if join_type == 'customers_expensive_products':
            # Customers who bought the most expensive products
            sql = f"""
            SELECT c.name as customer_name, p.name as product_name, p.price, s.amount, s.sale_date
            FROM customers c
            JOIN sales s ON c.name = s.customer_name
            JOIN products p ON s.product_id = p.product_id
            WHERE c.org_id = '{org_id}' AND s.org_id = '{org_id}' AND p.org_id = '{org_id}'
            ORDER BY p.price DESC
            LIMIT {limit}
            """
            
        elif join_type == 'top_customers_by_spending':
            # Top customers by total spending
            sql = f"""
            SELECT c.name as customer_name, SUM(s.amount) as total_spent, COUNT(s.sale_id) as total_orders
            FROM customers c
            JOIN sales s ON c.name = s.customer_name
            WHERE c.org_id = '{org_id}' AND s.org_id = '{org_id}'
            GROUP BY c.customer_id, c.name
            ORDER BY total_spent DESC
            LIMIT {limit}
            """
            
        elif join_type == 'customers_spent_over_amount':
            # Customers who spent over a certain amount
            amount = parsed_query.get('having', [{}])[0].get('value', 100)
            sql = f"""
            SELECT c.name as customer_name, SUM(s.amount) as total_spent
            FROM customers c
            JOIN sales s ON c.name = s.customer_name
            WHERE c.org_id = '{org_id}' AND s.org_id = '{org_id}'
            GROUP BY c.customer_id, c.name
            HAVING SUM(s.amount) > {amount}
            ORDER BY total_spent DESC
            """
            
        elif join_type == 'customers_by_category':
            # Customers who bought products in specific category
            category = next((c['value'] for c in parsed_query.get('conditions', []) if c.get('column') == 'p.category'), 'Electronics')
            sql = f"""
            SELECT DISTINCT c.name as customer_name, p.category, COUNT(s.sale_id) as purchases
            FROM customers c
            JOIN sales s ON c.name = s.customer_name
            JOIN products p ON s.product_id = p.product_id
            WHERE c.org_id = '{org_id}' AND s.org_id = '{org_id}' AND p.org_id = '{org_id}' AND p.category = '{category}'
            GROUP BY c.customer_id, c.name, p.category
            ORDER BY purchases DESC
            """
            
        # Product-Sales Analytics
        elif join_type == 'best_selling_products':
            # Best selling products by quantity or revenue
            sql = f"""
            SELECT p.name as product_name, p.category, SUM(s.quantity) as total_sold, SUM(s.amount) as total_revenue
            FROM products p
            JOIN sales s ON p.product_id = s.product_id
            WHERE p.org_id = '{org_id}' AND s.org_id = '{org_id}'
            GROUP BY p.product_id, p.name, p.category
            ORDER BY total_sold DESC
            LIMIT {limit}
            """
            
        elif join_type == 'products_sold_over_units':
            # Products that sold more than X units
            units = parsed_query.get('having', [{}])[0].get('value', 5)
            sql = f"""
            SELECT p.name as product_name, SUM(s.quantity) as total_sold
            FROM products p
            JOIN sales s ON p.product_id = s.product_id
            WHERE p.org_id = '{org_id}' AND s.org_id = '{org_id}'
            GROUP BY p.product_id, p.name
            HAVING SUM(s.quantity) > {units}
            ORDER BY total_sold DESC
            """
            
        # Inventory Analytics
        elif join_type == 'low_stock_products':
            # Products running low in stock
            threshold = next((c['value'] for c in parsed_query.get('conditions', []) if c.get('column') == 'i.quantity'), 100)
            sql = f"""
            SELECT p.name as product_name, p.category, i.quantity, i.warehouse
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            WHERE p.org_id = '{org_id}' AND i.org_id = '{org_id}' AND i.quantity < {threshold}
            ORDER BY i.quantity ASC
            """
            
        elif join_type == 'products_low_stock_threshold':
            # Products with less than specified amount in stock
            threshold = next((c['value'] for c in parsed_query.get('conditions', []) if c.get('column') == 'i.quantity'), 50)
            sql = f"""
            SELECT p.name as product_name, p.category, i.quantity
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            WHERE p.org_id = '{org_id}' AND i.org_id = '{org_id}' AND i.quantity < {threshold}
            ORDER BY i.quantity ASC
            """
            
        elif join_type == 'inventory_by_category':
            # Inventory levels for specific category
            category = next((c['value'] for c in parsed_query.get('conditions', []) if c.get('column') == 'p.category'), 'Electronics')
            sql = f"""
            SELECT p.name as product_name, p.category, i.quantity, i.warehouse
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            WHERE p.org_id = '{org_id}' AND i.org_id = '{org_id}' AND p.category = '{category}'
            ORDER BY i.quantity DESC
            """
            
        elif join_type == 'warehouse_inventory_totals':
            # Total inventory by warehouse
            sql = f"""
            SELECT i.warehouse, SUM(i.quantity) as total_inventory
            FROM inventory i
            WHERE i.org_id = '{org_id}'
            GROUP BY i.warehouse
            ORDER BY total_inventory DESC
            LIMIT {limit}
            """
            
        else:
            # Fallback to regular query
            return self._generate_sql_query(parsed_query, database_type)
        
        # Format and return
        from sqlparse import format as sql_format
        return sql_format(sql.strip(), reindent=True, keyword_case='upper')
    
    def _generate_mongodb_query(self, parsed_query: Dict[str, Any]) -> str:
        """Generate MongoDB query (returns JSON representation)"""
        
        # Build MongoDB query
        mongo_query = {
            'collection': parsed_query['table'],
            'operation': 'find'
        }
        
        # Build filter
        filter_obj = {}
        for condition in parsed_query['conditions']:
            filter_obj[condition['column']] = condition['value']
        
        mongo_query['filter'] = filter_obj
        
        # Projection (column selection)
        if parsed_query['columns'] != ['*']:
            projection = {}
            for col in parsed_query['columns']:
                if not col.startswith('COUNT') and not col.startswith('SUM') and not col.startswith('AVG'):
                    projection[col] = 1
            projection['_id'] = 0  # Exclude _id by default
            mongo_query['projection'] = projection
        
        # Aggregation pipeline for complex operations
        if parsed_query['aggregation'] or parsed_query['group_by']:
            mongo_query['operation'] = 'aggregate'
            pipeline = []
            
            # Match stage (WHERE clause)
            if filter_obj:
                pipeline.append({"$match": filter_obj})
            
            # Group stage
            if parsed_query['group_by'] or parsed_query['aggregation']:
                group_stage = {"$group": {"_id": {}}}
                
                if parsed_query['group_by']:
                    for col in parsed_query['group_by']:
                        group_stage["$group"]["_id"][col] = f"${col}"
                
                if parsed_query['aggregation']:
                    for col in parsed_query['columns']:
                        if 'COUNT' in col:
                            group_stage["$group"]["count"] = {"$sum": 1}
                        elif 'SUM' in col:
                            field = col.replace('SUM(', '').replace(')', '')
                            group_stage["$group"]["sum"] = {"$sum": f"${field}"}
                        elif 'AVG' in col:
                            field = col.replace('AVG(', '').replace(')', '')
                            group_stage["$group"]["average"] = {"$avg": f"${field}"}
                
                pipeline.append(group_stage)
            
            # Sort stage
            if parsed_query['order_by']:
                sort_stage = {"$sort": {}}
                for col in parsed_query['order_by']:
                    sort_stage["$sort"][col] = 1
                pipeline.append(sort_stage)
            
            # Limit stage
            if parsed_query['limit']:
                pipeline.append({"$limit": parsed_query['limit']})
            
            mongo_query['pipeline'] = pipeline
        
        return json.dumps(mongo_query, indent=2)
    
    def process_query(self, query_text: str, user_id: str, org_id: str, database_type: str, database_name: str) -> Dict[str, Any]:
        """Main entry point for processing natural language queries"""
        
        try:
            # Security check
            if self.detect_sql_injection(query_text):
                return {
                    'success': False,
                    'error': 'Potential security violation detected',
                    'blocked': True
                }
            
            # Get HDT context for personalization
            query_approach = hdt_manager.customize_query_approach(user_id, query_text)
            
            # Re-enable Ollama to test if that was interfering
            # Try Ollama first, then fallback to local parsing  
            if self.ollama_enabled:
                logger.info("Using Ollama parsing")
                parsed_query = self.parse_with_ollama(query_text, database_type, database_name, org_id, query_approach)
            else:
                print(f"[MAIN] Using enhanced local parsing for query: '{query_text}'")
                logger.info(f"Using enhanced local parsing for query: '{query_text}'")
                parsed_query = self.parse_natural_language(query_text, database_type, database_name, org_id)
                logger.info(f"Parsed result: table={parsed_query.get('table')}, conditions={len(parsed_query.get('conditions', []))}, aggregation={parsed_query.get('aggregation')}")
            
            
            if parsed_query['confidence'] < 0.3:
                return {
                    'success': False,
                    'error': 'Could not understand the query. Please be more specific.',
                    'suggestions': self._get_query_suggestions(database_type, database_name),
                    'approach': query_approach
                }
            
            # Generate SQL/MongoDB query
            generated_query = self.generate_sql(parsed_query, database_type, user_id)
            
            return {
                'success': True,
                'parsed_query': parsed_query,
                'generated_sql': generated_query,
                'database_type': database_type,
                'approach': query_approach,
                'confidence': parsed_query['confidence']
            }
            
        except PermissionError as e:
            logger.warning(f"Permission denied for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'blocked': True
            }
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': f"Query processing error: {str(e)}"
            }
    
    def _get_query_suggestions(self, database_type: str, database_name: str) -> List[str]:
        """Get query suggestions based on available tables"""
        suggestions = []
        tables = list(self.schema_mapping.get(database_type, {}).get(database_name, {}).keys())
        
        for table in tables:
            suggestions.extend([
                f"Show me all {table}",
                f"How many {table} are there?",
                f"List the {table}",
            ])
        
        return suggestions[:6]  # Limit to 6 suggestions
    
    def _create_permission_error_message(self, user_role: str, table_name: str, user_id: str) -> str:
        """Create user-friendly permission error messages"""
        
        # Table-specific messages
        table_messages = {
            'employees': {
                'viewer': "Access to employee data requires Manager or higher privileges. Contact your administrator to request elevated permissions.",
                'analyst': "Employee data access is restricted to HR and Management roles. Please contact your manager for assistance.",
                'developer': "Employee table access requires HR or Management privileges. Use available product or customer data instead.",
                'manager': "You may need specific HR permissions to access employee data. Contact your administrator.",
                'admin': "Employee data access may require additional HR role assignment. Check with your system administrator."
            },
            'customers': {
                'viewer': "Customer data access requires Analyst role or higher. Contact your supervisor to request data access permissions.",
                'analyst': "Customer data may be restricted in your department. Try using product data or contact your manager.",
                'developer': "Customer data access might require specific CRM permissions. Use available product data instead.",
                'manager': "Customer data access may require additional permissions. Contact your administrator.",
                'admin': "Customer table may not be configured for your organization. Check database setup."
            },
            'sales': {
                'viewer': "Sales data requires Analyst or Manager role. Request access from your supervisor for business reporting.",
                'analyst': "Sales data may be restricted by department or time period. Contact your manager for specific access.",
                'developer': "Sales data access might require business role privileges. Use available product data instead.",
                'manager': "Sales data access should be available. Check with your administrator if this continues.",
                'admin': "Sales table may not be configured. Verify database setup and permissions."
            },
            'inventory': {
                'viewer': "Inventory data requires operational roles. Contact your supervisor for warehouse data access.",
                'analyst': "Inventory access may be limited to operations teams. Try product data or request specific permissions.",
                'developer': "Inventory data requires operational privileges. Use available product catalog instead.",
                'manager': "Inventory data should be accessible. Contact your administrator to verify permissions.",
                'admin': "Inventory table may need configuration. Check database setup and role mappings."
            },
            'transactions': {
                'viewer': "Financial transaction data requires Finance role or higher. Contact your finance team.",
                'analyst': "Transaction data access is typically restricted to Finance department. Request access from finance manager.",
                'developer': "Financial data requires specific finance privileges. Use available non-financial data instead.",
                'manager': "Transaction data may require Finance role assignment. Contact your administrator.",
                'admin': "Transaction data access may need additional finance module permissions."
            }
        }
        
        # Get specific message or create generic one
        if table_name in table_messages and user_role in table_messages[table_name]:
            specific_message = table_messages[table_name][user_role]
        else:
            # Generic role-based messages
            role_messages = {
                'viewer': f"Your Viewer role doesn't include access to {table_name} data. Contact your supervisor to request elevated permissions for business reporting.",
                'analyst': f"The {table_name} table may require higher privileges than your current Analyst role. Contact your manager for specific data access.",
                'developer': f"Developer access to {table_name} data may be restricted. Try using available product or public datasets instead.",
                'manager': f"Manager access to {table_name} should typically be available. Contact your administrator to verify role permissions.",
                'admin': f"Admin access to {table_name} is unexpected. The table may not be configured for your organization or needs database setup."
            }
            specific_message = role_messages.get(user_role, 
                f"Access to {table_name} data is not available for your current role ({user_role}). Contact your administrator for assistance."
            )
        
        # Add helpful suggestions
        suggestion = self._get_permission_suggestions(table_name, user_role)
        
        return f"[ACCESS RESTRICTED]: {specific_message}\n\n[SUGGESTION]: {suggestion}"
    
    def _get_permission_suggestions(self, restricted_table: str, user_role: str) -> str:
        """Get alternative query suggestions when access is restricted"""
        
        suggestions = {
            'employees': "Try 'Show me all products' or 'List available inventory' for accessible data.",
            'customers': "Try 'Show product information' or 'What products do we have?' for available datasets.",
            'sales': "Try 'Show me all products' or 'Display product categories' for accessible reporting.",
            'inventory': "Try 'List all products' or 'Show product details' for available catalog data.",
            'transactions': "Try 'Show available products' or other non-financial queries.",
        }
        
        return suggestions.get(restricted_table, "Try 'Show me all products' or other available data queries.")
    
    def explain_query(self, generated_sql: str, database_type: str) -> str:
        """Generate human-readable explanation of the SQL query"""
        try:
            if database_type == 'mongodb':
                return "MongoDB query to retrieve documents from the specified collection with filters and aggregations as needed."
            
            # Parse SQL to explain
            parsed = sqlparse.parse(generated_sql)[0]
            tokens = [token for token in parsed.flatten() if not token.is_whitespace]
            
            explanation_parts = []
            
            # Basic explanation based on keywords
            if any(str(token).upper() == 'SELECT' for token in tokens):
                explanation_parts.append("This query retrieves data")
            
            if any(str(token).upper() == 'COUNT' for token in tokens):
                explanation_parts.append("and counts the number of records")
            
            if any(str(token).upper() == 'WHERE' for token in tokens):
                explanation_parts.append("with specific filtering conditions")
            
            if any(str(token).upper() == 'GROUP BY' for token in tokens):
                explanation_parts.append("grouped by certain columns")
            
            if any(str(token).upper() == 'ORDER BY' for token in tokens):
                explanation_parts.append("sorted in a specific order")
            
            explanation = ' '.join(explanation_parts) if explanation_parts else "This query performs a database operation"
            
            return f"{explanation}. The results are automatically filtered to only include data from your organization for security."
            
        except Exception as e:
            logger.error(f"Error explaining query: {e}")
            return "This query retrieves data from your organization's database with appropriate security filters."

# Global NLP2SQL engine instance
nlp2sql_engine = NLP2SQLEngine()