"""
Security Tests for Multi-Tenant NLP2SQL System
Comprehensive test suite for security validation and tenant isolation
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.security import security_manager
from src.database import db_manager
from src.auth import auth_manager

class TestSQLInjectionDetection:
    """Test SQL injection detection capabilities"""
    
    def test_detect_union_injection(self):
        """Test detection of UNION-based SQL injection"""
        malicious_query = "Show me users'; DROP TABLE users; --"
        result = security_manager.detect_sql_injection(malicious_query)
        assert result['is_malicious'] is True
        assert 'drop' in result['threat_type'].lower()
    
    def test_detect_comment_injection(self):
        """Test detection of comment-based injection"""
        malicious_query = "SELECT * FROM products -- WHERE id = 1"
        result = security_manager.detect_sql_injection(malicious_query)
        assert result['is_malicious'] is True
    
    def test_detect_union_select(self):
        """Test detection of UNION SELECT attacks"""
        malicious_query = "show products UNION SELECT password FROM users"
        result = security_manager.detect_sql_injection(malicious_query)
        assert result['is_malicious'] is True
        assert 'union' in result['threat_type'].lower()
    
    def test_safe_query_passes(self):
        """Test that safe queries pass validation"""
        safe_query = "Show me all products in the electronics category"
        result = security_manager.detect_sql_injection(safe_query)
        assert result['is_malicious'] is False
    
    def test_detect_stacked_queries(self):
        """Test detection of stacked query injection"""
        malicious_query = "Show products; DELETE FROM inventory;"
        result = security_manager.detect_sql_injection(malicious_query)
        assert result['is_malicious'] is True

class TestTenantIsolation:
    """Test multi-tenant isolation security"""
    
    def test_org_id_validation(self):
        """Test organization ID validation"""
        # Valid org ID
        result = security_manager.validate_tenant_isolation("user-001", "org-001", "org-001")
        assert result['passed'] is True
        
        # Invalid org ID mismatch
        result = security_manager.validate_tenant_isolation("user-001", "org-001", "org-002")
        assert result['passed'] is False
        assert 'tenant isolation' in ' '.join(result['errors']).lower()
    
    def test_cross_tenant_access_prevention(self):
        """Test prevention of cross-tenant data access"""
        query = "SELECT * FROM products WHERE org_id = 'org-002'"
        result = security_manager.validate_query_scope(query, "org-001")
        assert result['passed'] is False
    
    def test_sql_org_id_injection(self):
        """Test SQL injection via org_id manipulation"""
        malicious_query = "Show products WHERE org_id = 'org-001' OR '1'='1'"
        result = security_manager.detect_sql_injection(malicious_query)
        assert result['is_malicious'] is True

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_enforcement(self):
        """Test rate limiting for queries"""
        user_id = "test-user-001"
        ip_address = "192.168.1.100"
        
        # First few requests should pass
        for i in range(5):
            result = security_manager.check_rate_limit(user_id, ip_address)
            assert result['rate_limited'] is False
        
        # Subsequent requests should be rate limited
        for i in range(10):
            security_manager.check_rate_limit(user_id, ip_address)
        
        result = security_manager.check_rate_limit(user_id, ip_address)
        assert result['rate_limited'] is True
    
    def test_rate_limit_reset(self):
        """Test rate limit reset after time window"""
        user_id = "test-user-002"
        ip_address = "192.168.1.101"
        
        # Exhaust rate limit
        for i in range(15):
            security_manager.check_rate_limit(user_id, ip_address)
        
        # Should be rate limited
        result = security_manager.check_rate_limit(user_id, ip_address)
        assert result['rate_limited'] is True
        
        # Simulate time passage (this would normally require waiting)
        # In a real test, you might mock time or use a smaller window
        security_manager.rate_limiter.clear()  # Reset for testing
        
        result = security_manager.check_rate_limit(user_id, ip_address)
        assert result['rate_limited'] is False

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_permissions(self):
        """Test admin role permissions"""
        result = security_manager.validate_role_permissions("admin", "DELETE")
        assert result['allowed'] is True
    
    def test_viewer_restrictions(self):
        """Test viewer role restrictions"""
        result = security_manager.validate_role_permissions("viewer", "DELETE")
        assert result['allowed'] is False
        
        result = security_manager.validate_role_permissions("viewer", "SELECT")
        assert result['allowed'] is True
    
    def test_analyst_permissions(self):
        """Test analyst role permissions"""
        result = security_manager.validate_role_permissions("analyst", "SELECT")
        assert result['allowed'] is True
        
        result = security_manager.validate_role_permissions("analyst", "INSERT")
        assert result['allowed'] is False

class TestQuerySanitization:
    """Test query output sanitization"""
    
    def test_sensitive_data_removal(self):
        """Test removal of sensitive data from results"""
        mock_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "password": "secret123",
                "ssn": "123-45-6789"
            }
        ]
        
        sanitized = security_manager.sanitize_query_output(mock_data, "viewer")
        
        # Check that sensitive fields are removed
        assert "password" not in sanitized[0]
        assert "ssn" not in sanitized[0]
        assert "email" in sanitized[0]  # Email might be allowed for some roles
    
    def test_admin_sees_all_data(self):
        """Test that admin users can see sensitive data"""
        mock_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "department": "Finance"
            }
        ]
        
        sanitized = security_manager.sanitize_query_output(mock_data, "admin")
        
        # Admin should see all data
        assert len(sanitized[0]) == len(mock_data[0])

class TestComprehensiveSecurityCheck:
    """Test the comprehensive security validation"""
    
    def test_malicious_query_blocked(self):
        """Test that malicious queries are completely blocked"""
        malicious_query = "Show users'; DROP TABLE users; --"
        
        result = security_manager.comprehensive_security_check(
            malicious_query, "user-001", "viewer", "org-001", "192.168.1.100"
        )
        
        assert result['passed'] is False
        assert len(result['errors']) > 0
        assert any('injection' in error.lower() for error in result['errors'])
    
    def test_safe_query_passes_all_checks(self):
        """Test that safe queries pass all security checks"""
        safe_query = "Show me all products in electronics category"
        
        result = security_manager.comprehensive_security_check(
            safe_query, "user-001", "analyst", "org-001", "192.168.1.100"
        )
        
        assert result['passed'] is True
        assert len(result['errors']) == 0
    
    def test_cross_tenant_query_blocked(self):
        """Test that cross-tenant queries are blocked"""
        cross_tenant_query = "Show products from org-002"
        
        result = security_manager.comprehensive_security_check(
            cross_tenant_query, "user-001", "admin", "org-001", "192.168.1.100"
        )
        
        assert result['passed'] is False
        assert any('tenant' in error.lower() for error in result['errors'])

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_query_length_limit(self):
        """Test query length limitations"""
        very_long_query = "SELECT * FROM products " + "WHERE name LIKE '%test%' " * 100
        
        result = security_manager.validate_input_length(very_long_query)
        assert result['valid'] is False
        assert 'length' in result['error'].lower()
    
    def test_special_character_handling(self):
        """Test handling of special characters"""
        query_with_specials = "Show products with name containing 'O'Reilly & Co.'"
        
        result = security_manager.sanitize_input(query_with_specials)
        assert result['sanitized'] is not None
        assert result['safe'] is True
    
    def test_unicode_handling(self):
        """Test handling of unicode characters"""
        unicode_query = "Show products with name 'Café'"
        
        result = security_manager.sanitize_input(unicode_query)
        assert result['safe'] is True

class TestAuditLogging:
    """Test security audit logging"""
    
    @patch('src.security.logger')
    def test_security_violation_logged(self, mock_logger):
        """Test that security violations are properly logged"""
        malicious_query = "'; DROP TABLE users; --"
        
        security_manager.comprehensive_security_check(
            malicious_query, "user-001", "viewer", "org-001", "192.168.1.100"
        )
        
        # Verify that a security event was logged
        mock_logger.warning.assert_called()
        
        # Check that the log contains relevant information
        log_calls = mock_logger.warning.call_args_list
        assert any('SQL injection' in str(call) for call in log_calls)
    
    @patch('src.security.logger')
    def test_rate_limit_violation_logged(self, mock_logger):
        """Test that rate limit violations are logged"""
        user_id = "test-user-rate-limit"
        ip_address = "192.168.1.200"
        
        # Exhaust rate limit
        for i in range(20):
            security_manager.check_rate_limit(user_id, ip_address)
        
        # Verify rate limit violation was logged
        mock_logger.warning.assert_called()

class TestDatabaseSecurityIntegration:
    """Test security integration with database operations"""
    
    @patch('src.database.db_manager')
    def test_parameterized_queries(self, mock_db):
        """Test that database queries use parameterized statements"""
        # This would test the actual database integration
        # Implementation depends on your specific database abstraction
        pass
    
    def test_connection_security(self):
        """Test database connection security"""
        # Test that connections use proper encryption and authentication
        # This is more of an integration test
        pass

# Test fixtures and utilities
@pytest.fixture
def clean_security_state():
    """Clean security manager state before each test"""
    security_manager.rate_limiter.clear()
    yield
    security_manager.rate_limiter.clear()

# Performance tests
class TestSecurityPerformance:
    """Test security validation performance"""
    
    def test_injection_detection_performance(self):
        """Test that SQL injection detection is fast enough"""
        import time
        
        query = "Show me all products in the electronics category with price less than 100"
        
        start_time = time.time()
        for i in range(100):
            security_manager.detect_sql_injection(query)
        end_time = time.time()
        
        # Should process 100 queries in less than 1 second
        assert (end_time - start_time) < 1.0
    
    def test_comprehensive_check_performance(self):
        """Test overall security check performance"""
        import time
        
        query = "Show me sales data for last month"
        
        start_time = time.time()
        for i in range(50):
            security_manager.comprehensive_security_check(
                query, "user-001", "analyst", "org-001", "192.168.1.100"
            )
        end_time = time.time()
        
        # Should process 50 comprehensive checks in less than 2 seconds
        assert (end_time - start_time) < 2.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])