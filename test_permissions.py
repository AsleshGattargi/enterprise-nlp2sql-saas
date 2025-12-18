#!/usr/bin/env python3
"""
Test script to verify role-based table access permissions
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.auth import AuthManager
from src.database import db_manager

def test_user_permissions():
    """Test permissions for different user roles"""
    auth_manager = AuthManager()

    # Test cases: (user_id, expected_tables)
    test_cases = [
        # FinanceHub users
        ('user-201', 'admin', 'Finance', ['accounts', 'transactions', 'customers', 'branches', 'loans', 'investments']),
        ('user-102', 'manager', 'Finance', ['accounts', 'transactions', 'customers', 'branches']),
        ('user-106', 'analyst', 'Finance', ['accounts', 'transactions', 'investments']),

        # HealthPlus users
        ('user-051', 'admin', 'Healthcare', ['patients', 'doctors', 'appointments', 'billing', 'treatments']),
        ('user-052', 'manager', 'Healthcare', ['patients', 'appointments', 'doctors', 'departments', 'billing']),
        ('user-056', 'analyst', 'Healthcare', ['appointments', 'treatments', 'billing']),

        # TechCorp users
        ('user-001', 'admin', 'Technology', ['products', 'inventory', 'sales', 'customers', 'employees']),
        ('user-002', 'manager', 'Technology', ['products', 'inventory', 'sales', 'customers', 'employees']),
        ('user-003', 'analyst', 'Technology', ['products', 'sales', 'inventory']),
    ]

    print("ROLE-BASED PERMISSION TEST")
    print("=" * 50)

    for user_id, role, industry, test_tables in test_cases:
        print(f"\nTesting {role.upper()} in {industry}")
        print(f"   User ID: {user_id}")

        # Test each table
        accessible_tables = []
        blocked_tables = []

        for table in test_tables:
            has_access = auth_manager.check_user_permission(user_id, 'table', table, 'read')
            if has_access:
                accessible_tables.append(table)
            else:
                blocked_tables.append(table)

        # Test a table they shouldn't have access to
        restricted_table = 'secret_data'
        has_restricted_access = auth_manager.check_user_permission(user_id, 'table', restricted_table, 'read')

        print(f"   [OK] Accessible: {', '.join(accessible_tables) if accessible_tables else 'None'}")
        print(f"   [NO] Blocked: {', '.join(blocked_tables) if blocked_tables else 'None'}")
        print(f"   [X] Restricted table access: {'BLOCKED' if not has_restricted_access else 'ALLOWED (ISSUE!)'}")

        # Test write access (should be blocked for non-admins)
        if role != 'admin':
            can_write = auth_manager.check_user_permission(user_id, 'table', test_tables[0], 'write')
            print(f"   [W] Write access: {'BLOCKED' if not can_write else 'ALLOWED (ISSUE!)'}")

if __name__ == "__main__":
    test_user_permissions()