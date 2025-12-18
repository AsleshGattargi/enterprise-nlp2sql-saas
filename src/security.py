import re
import hashlib
import hmac
import time
from typing import Dict, List, Any, Optional, Set
from sqlalchemy.orm import Session
from src.models import QueryLog, User, Organization
from src.database import db_manager
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SecurityManager:
    """Comprehensive security management for multi-tenant NLP2SQL system"""
    
    def __init__(self):
        # SQL injection patterns (expanded)
        self.sql_injection_patterns = [
            # Basic injection patterns
            r';\s*drop\s+table',
            r';\s*delete\s+from',
            r';\s*update\s+.*\s+set',
            r';\s*insert\s+into',
            r';\s*create\s+table',
            r';\s*alter\s+table',
            
            # Union-based injection
            r'union\s+select',
            r'union\s+all\s+select',
            
            # Comment-based injection
            r'--\s*$',
            r'/\*.*\*/',
            r'#.*$',
            
            # Function-based injection
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_executesql',
            r'xp_cmdshell',
            r'sp_makewebtask',
            
            # Information schema attacks
            r'information_schema',
            r'sys\.tables',
            r'sys\.columns',
            
            # Time-based injection
            r'waitfor\s+delay',
            r'sleep\s*\(',
            r'benchmark\s*\(',
            
            # Boolean-based injection
            r'and\s+1\s*=\s*1',
            r'or\s+1\s*=\s*1',
            r'and\s+.*\s*=\s*.*',
            
            # File system access
            r'load_file\s*\(',
            r'into\s+outfile',
            r'into\s+dumpfile',
            
            # Script injection
            r'<\s*script',
            r'javascript\s*:',
            r'vbscript\s*:',
            
            # Database function abuse
            r'substring\s*\(',
            r'ascii\s*\(',
            r'char\s*\(',
            r'concat\s*\(',
            
            # Blind injection patterns
            r'and\s+\(select\s+count',
            r'and\s+\(select\s+top',
            r'having\s+1\s*=\s*1'
        ]
        
        # Suspicious keywords that might indicate data exfiltration attempts
        self.suspicious_keywords = [
            'password', 'pwd', 'secret', 'key', 'token', 'session',
            'credit_card', 'ssn', 'social_security', 'bank_account',
            'admin', 'root', 'superuser', 'privileged'
        ]
        
        # Role-based restricted keywords
        self.role_restricted_keywords = {
            'viewer': ['salary', 'wage', 'bonus', 'delete', 'update', 'insert', 'drop'],
            'developer': ['salary', 'wage', 'bonus', 'delete', 'drop'],
            'analyst': ['delete', 'drop', 'alter'],
            'manager': ['drop', 'alter', 'admin', 'user_permissions'],
        }
        
        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage = {}
        
        # Blocked IP addresses
        self.blocked_ips = set()
        
        # Maximum query complexity scores
        self.max_query_complexity = {
            'viewer': 5,
            'developer': 10,
            'analyst': 15,
            'manager': 20,
            'admin': 50
        }
    
    def detect_sql_injection(self, query: str, user_id: str, ip_address: str, user_role: str = None) -> Dict[str, Any]:
        """Enhanced SQL injection detection with logging"""
        query_lower = query.lower()
        detected_patterns = []
        risk_score = 0
        
        # Check against injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE | re.MULTILINE):
                detected_patterns.append(pattern)
                risk_score += 10
        
        # Check for suspicious keywords with enhanced detection
        for keyword in self.suspicious_keywords:
            if keyword in query_lower:
                detected_patterns.append(f"suspicious_keyword: {keyword}")
                risk_score += 15  # Increased from 5 to make sure it triggers
        
        # Check for role-based restricted keywords
        if user_role and user_role in self.role_restricted_keywords:
            restricted_for_role = self.role_restricted_keywords[user_role]
            for keyword in restricted_for_role:
                if keyword in query_lower:
                    detected_patterns.append(f"role_restricted: {keyword} (not allowed for {user_role})")
                    risk_score += 20  # High score for role violations
        
        # Check for excessive special characters
        special_chars = len(re.findall(r'[;\'"\(\)\[\]{}]', query))
        if special_chars > 10:
            detected_patterns.append("excessive_special_characters")
            risk_score += 3
        
        # Check query length (extremely long queries might be suspicious)
        if len(query) > 1000:
            detected_patterns.append("excessive_query_length")
            risk_score += 2
        
        is_suspicious = risk_score > 10
        
        if is_suspicious:
            logger.warning(f"SQL injection attempt detected from user {user_id} at IP {ip_address}")
            logger.warning(f"Detected patterns: {detected_patterns}")
            logger.warning(f"Risk score: {risk_score}")
            
            # Log the security incident
            self._log_security_incident(user_id, ip_address, query, detected_patterns, risk_score)
        
        return {
            'is_suspicious': is_suspicious,
            'risk_score': risk_score,
            'detected_patterns': detected_patterns,
            'blocked': is_suspicious
        }
    
    def check_rate_limit(self, user_id: str, ip_address: str) -> Dict[str, Any]:
        """Check rate limiting for user and IP"""
        current_time = time.time()
        window_size = 60  # 1 minute window
        max_requests_per_user = 30  # per minute
        max_requests_per_ip = 50  # per minute
        
        # Clean old entries
        self._clean_rate_limit_storage(current_time, window_size)
        
        # Check user rate limit
        user_key = f"user:{user_id}"
        user_requests = self.rate_limit_storage.get(user_key, [])
        user_requests = [req_time for req_time in user_requests if current_time - req_time < window_size]
        
        # Check IP rate limit
        ip_key = f"ip:{ip_address}"
        ip_requests = self.rate_limit_storage.get(ip_key, [])
        ip_requests = [req_time for req_time in ip_requests if current_time - req_time < window_size]
        
        # Check if limits exceeded
        user_exceeded = len(user_requests) >= max_requests_per_user
        ip_exceeded = len(ip_requests) >= max_requests_per_ip
        
        if not user_exceeded and not ip_exceeded:
            # Add current request
            user_requests.append(current_time)
            ip_requests.append(current_time)
            self.rate_limit_storage[user_key] = user_requests
            self.rate_limit_storage[ip_key] = ip_requests
        
        rate_limited = user_exceeded or ip_exceeded
        
        if rate_limited:
            logger.warning(f"Rate limit exceeded for user {user_id} from IP {ip_address}")
            self._log_security_incident(
                user_id, ip_address, "RATE_LIMIT_EXCEEDED", 
                ["rate_limit"], 15
            )
        
        return {
            'rate_limited': rate_limited,
            'user_requests': len(user_requests),
            'ip_requests': len(ip_requests),
            'user_limit': max_requests_per_user,
            'ip_limit': max_requests_per_ip,
            'window_seconds': window_size
        }
    
    def validate_tenant_isolation(self, query: str, user_org_id: str) -> Dict[str, Any]:
        """Ensure query only accesses data from user's organization"""
        
        # For natural language queries, trust the NLP2SQL engine to add tenant isolation
        # Only validate actual SQL queries that should already have tenant filters
        
        # Check if this looks like a SQL query (has SQL keywords)
        sql_keywords = ['select', 'insert', 'update', 'delete', 'create', 'drop', 'alter']
        is_sql_query = any(keyword in query.lower() for keyword in sql_keywords)
        
        if not is_sql_query:
            # This is a natural language query - allow it to pass to NLP2SQL engine
            logger.info(f"Natural language query detected, allowing for NLP2SQL processing")
            return {'valid': True, 'natural_language': True}
        
        # For SQL queries, enforce strict tenant isolation
        if 'where' not in query.lower():
            return {
                'valid': False,
                'error': 'SQL query must include WHERE clause for tenant isolation'
            }
        
        # Check for org_id filter in SQL queries
        org_filter_patterns = [
            rf'org_id\s*=\s*[\'"]?{re.escape(user_org_id)}[\'"]?',
            rf'organization_id\s*=\s*[\'"]?{re.escape(user_org_id)}[\'"]?'
        ]
        
        has_org_filter = any(
            re.search(pattern, query, re.IGNORECASE) 
            for pattern in org_filter_patterns
        )
        
        if not has_org_filter:
            return {
                'valid': False,
                'error': 'SQL query must include organization filter for security'
            }
        
        # Check for attempts to bypass org filter
        bypass_patterns = [
            r'org_id\s*!=',
            r'org_id\s*<>',
            r'or\s+org_id',
            r'union.*org_id',
            r'org_id\s*in\s*\([^)]*[\'"][^\'"]*[\'"][^)]*\)'  # org_id in multiple values
        ]
        
        for pattern in bypass_patterns:
            if re.search(pattern, query.lower()):
                return {
                    'valid': False,
                    'error': 'Potential tenant isolation bypass detected'
                }
        
        return {'valid': True}
    
    def calculate_query_complexity(self, query: str) -> int:
        """Calculate query complexity score"""
        complexity_score = 0
        query_lower = query.lower()
        
        # Base complexity for different operations
        if 'select' in query_lower:
            complexity_score += 1
        if 'join' in query_lower:
            complexity_score += 3
        if 'union' in query_lower:
            complexity_score += 4
        if 'subquery' in query_lower or '(' in query and 'select' in query_lower:
            complexity_score += 5
        
        # Aggregate functions
        aggregates = ['count', 'sum', 'avg', 'max', 'min', 'group_concat']
        complexity_score += sum(2 for agg in aggregates if agg in query_lower)
        
        # Clauses
        clauses = ['where', 'group by', 'having', 'order by']
        complexity_score += sum(1 for clause in clauses if clause in query_lower)
        
        # Functions and expressions
        functions = ['substring', 'concat', 'date', 'cast', 'convert']
        complexity_score += sum(1 for func in functions if func in query_lower)
        
        # Window functions (advanced)
        window_functions = ['row_number', 'rank', 'lead', 'lag', 'first_value', 'last_value']
        complexity_score += sum(3 for func in window_functions if func in query_lower)
        
        return complexity_score
    
    def check_query_permission(self, user_id: str, user_role: str, query: str) -> Dict[str, Any]:
        """Check if user has permission to execute query based on complexity and role"""
        
        complexity = self.calculate_query_complexity(query)
        max_allowed = self.max_query_complexity.get(user_role, 5)
        
        if complexity > max_allowed:
            logger.warning(f"Query complexity {complexity} exceeds limit {max_allowed} for role {user_role}")
            return {
                'allowed': False,
                'complexity': complexity,
                'max_allowed': max_allowed,
                'error': f'Query too complex for role {user_role}. Complexity: {complexity}, Max allowed: {max_allowed}'
            }
        
        return {
            'allowed': True,
            'complexity': complexity,
            'max_allowed': max_allowed
        }
    
    def sanitize_query_output(self, results: List[Dict[str, Any]], user_role: str) -> List[Dict[str, Any]]:
        """Sanitize query results based on user role and data sensitivity"""
        
        if not results:
            return results
        
        # Fields that should be hidden/masked for non-admin users
        sensitive_fields = {
            'password', 'password_hash', 'secret', 'token', 'key',
            'credit_card', 'ssn', 'social_security', 'bank_account'
        }
        
        # Fields to mask for viewers and developers
        restricted_fields = {
            'email', 'phone', 'address', 'salary', 'wage'
        }
        
        sanitized_results = []
        
        for row in results:
            sanitized_row = {}
            
            for key, value in row.items():
                key_lower = key.lower()
                
                # Always hide sensitive fields for non-admin
                if key_lower in sensitive_fields and user_role != 'admin':
                    sanitized_row[key] = '[HIDDEN]'
                
                # Mask restricted fields for viewer/developer roles
                elif key_lower in restricted_fields and user_role in ['viewer', 'developer']:
                    if isinstance(value, str) and value:
                        # Partial masking
                        if '@' in value:  # Email
                            parts = value.split('@')
                            sanitized_row[key] = f"{parts[0][:2]}***@{parts[1]}"
                        elif len(value) > 4:  # Other fields
                            sanitized_row[key] = f"{value[:2]}***{value[-2:]}"
                        else:
                            sanitized_row[key] = "***"
                    else:
                        sanitized_row[key] = value
                
                else:
                    sanitized_row[key] = value
            
            sanitized_results.append(sanitized_row)
        
        return sanitized_results
    
    def _log_security_incident(self, user_id: str, ip_address: str, query: str, patterns: List[str], risk_score: int):
        """Log security incident to database"""
        try:
            with db_manager.get_metadata_db() as db:
                # Get user info
                user = db.query(User).filter(User.user_id == user_id).first()
                
                log_entry = QueryLog(
                    log_id=str(uuid.uuid4()),
                    org_id=user.org_id if user else 'unknown',
                    user_id=user_id,
                    query_text=query[:500],  # Truncate for storage
                    generated_sql=None,
                    query_type='SECURITY_INCIDENT',
                    execution_status='blocked',
                    execution_time_ms=0,
                    error_message=f"Security violation detected. Patterns: {', '.join(patterns)}. Risk score: {risk_score}. IP: {ip_address}",
                    timestamp=datetime.utcnow()
                )
                
                db.add(log_entry)
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to log security incident: {e}")
    
    def _clean_rate_limit_storage(self, current_time: float, window_size: int):
        """Clean old rate limit entries"""
        for key in list(self.rate_limit_storage.keys()):
            self.rate_limit_storage[key] = [
                req_time for req_time in self.rate_limit_storage[key]
                if current_time - req_time < window_size
            ]
            
            # Remove empty entries
            if not self.rate_limit_storage[key]:
                del self.rate_limit_storage[key]
    
    def check_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP address reputation (placeholder for real IP reputation service)"""
        
        # Check if IP is in blocked list
        if ip_address in self.blocked_ips:
            return {
                'blocked': True,
                'reason': 'IP address is blocked due to previous violations'
            }
        
        # Allow localhost for development/demo mode
        if ip_address in ['127.0.0.1', '::1', 'localhost']:
            return {'clean': True, 'localhost': True}
        
        # In production, integrate with IP reputation services
        # For demo, check for obviously suspicious patterns (excluding localhost)
        suspicious_patterns = [
            r'^10\.', r'^192\.168\.', r'^172\.',  # Internal networks from external
            r'^0\.', r'^169\.254\.',   # Link-local (excluding 127.x.x.x localhost)
        ]
        
        # Check for suspicious IP patterns
        for pattern in suspicious_patterns:
            if re.match(pattern, ip_address):
                logger.info(f"Internal network IP detected: {ip_address} (allowed for development)")
                return {'clean': True, 'internal': True}
        
        return {'clean': True}
    
    def comprehensive_security_check(self, query: str, user_id: str, user_role: str, user_org_id: str, ip_address: str) -> Dict[str, Any]:
        """Perform comprehensive security check"""
        
        security_results = {
            'passed': True,
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # 1. IP reputation check
        ip_check = self.check_ip_reputation(ip_address)
        security_results['checks']['ip_reputation'] = ip_check
        if ip_check.get('blocked'):
            security_results['passed'] = False
            security_results['errors'].append(ip_check['reason'])
            return security_results
        
        # 2. Rate limiting check
        rate_check = self.check_rate_limit(user_id, ip_address)
        security_results['checks']['rate_limit'] = rate_check
        if rate_check['rate_limited']:
            security_results['passed'] = False
            security_results['errors'].append('Rate limit exceeded')
            return security_results
        
        # 3. SQL injection detection (with role-based restrictions)
        injection_check = self.detect_sql_injection(query, user_id, ip_address, user_role)
        security_results['checks']['sql_injection'] = injection_check
        if injection_check['is_suspicious']:
            security_results['passed'] = False
            # Check if it's due to access control restrictions
            if any('suspicious_keyword:' in pattern for pattern in injection_check['detected_patterns']):
                security_results['errors'].append('🚫 Access Denied: You do not have permission to access sensitive information like passwords, credentials, or administrative data. Please contact your administrator if you need access to this information.')
            elif any('role_restricted:' in pattern for pattern in injection_check['detected_patterns']):
                role_pattern = next((pattern for pattern in injection_check['detected_patterns'] if 'role_restricted:' in pattern), '')
                security_results['errors'].append(f'🚫 Access Denied: Your role ({user_role}) does not have permission to perform this operation. {role_pattern}')
            else:
                security_results['errors'].append('Query blocked for security reasons: Potential malicious pattern detected.')
            return security_results
        
        # 4. Tenant isolation validation
        isolation_check = self.validate_tenant_isolation(query, user_org_id)
        security_results['checks']['tenant_isolation'] = isolation_check
        if not isolation_check['valid']:
            security_results['passed'] = False
            security_results['errors'].append(isolation_check['error'])
            return security_results
        
        # 5. Query complexity and permission check
        permission_check = self.check_query_permission(user_id, user_role, query)
        security_results['checks']['query_permission'] = permission_check
        if not permission_check['allowed']:
            security_results['passed'] = False
            security_results['errors'].append(permission_check['error'])
            return security_results
        
        # Add warnings for high complexity
        if permission_check['complexity'] > 10:
            security_results['warnings'].append(f"High query complexity: {permission_check['complexity']}")
        
        return security_results

# Global security manager instance
security_manager = SecurityManager()