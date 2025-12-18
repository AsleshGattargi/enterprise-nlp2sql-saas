#!/usr/bin/env python3
"""
Test 3 organizations with 3 users each to verify working permission system
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.auth import AuthManager

def test_working_permissions():
    """Test 3 organizations with admin, manager, and analyst from each"""
    auth_manager = AuthManager()

    # Test cases: (org, user_id, email, role, should_have_access_to, should_be_blocked_from)
    test_users = [
        # TechCorp (Technology)
        ('TechCorp', 'user-001', 'diana.rodriguez0@techcorp.com', 'admin',
         ['products', 'inventory', 'sales', 'customers', 'employees'], []),
        ('TechCorp', 'user-002', 'john.smith1@techcorp.com', 'manager',
         ['products', 'inventory', 'sales', 'customers', 'employees'], ['secret_data']),
        ('TechCorp', 'user-003', 'alex.davis5@techcorp.com', 'analyst',
         ['products', 'sales', 'inventory'], ['customers', 'employees']),

        # HealthPlus (Healthcare)
        ('HealthPlus', 'user-051', 'dr.rodriguez50@healthplus.org', 'admin',
         ['patients', 'doctors', 'appointments', 'billing', 'treatments'], []),
        ('HealthPlus', 'user-052', 'sarah.nurse51@healthplus.org', 'manager',
         ['patients', 'appointments', 'doctors', 'departments', 'billing'], ['secret_data']),
        ('HealthPlus', 'user-056', 'anna.analyst55@healthplus.org', 'analyst',
         ['appointments', 'treatments', 'billing'], ['patients', 'doctors']),

        # FinanceHub (Finance)
        ('FinanceHub', 'user-201', 'cfo.rodriguez100@financehub.net', 'admin',
         ['accounts', 'transactions', 'customers', 'branches', 'loans', 'investments'], []),
        ('FinanceHub', 'user-102', 'john.vp101@financehub.net', 'manager',
         ['accounts', 'transactions', 'customers', 'branches'], ['investments']),
        ('FinanceHub', 'user-106', 'alex.quant105@financehub.net', 'analyst',
         ['accounts', 'transactions', 'investments'], ['customers', 'branches']),
    ]

    print("FINAL PERMISSION VERIFICATION")
    print("=" * 80)

    all_working = True

    for org, user_id, email, role, allowed_tables, blocked_tables in test_users:
        print(f"\n{org} - {role.upper()} ({email})")
        print("-" * 60)

        # Test allowed tables
        allowed_working = []
        allowed_failing = []
        for table in allowed_tables:
            has_access = auth_manager.check_user_permission(user_id, 'table', table, 'read')
            if has_access:
                allowed_working.append(table)
            else:
                allowed_failing.append(table)

        # Test blocked tables
        blocked_working = []
        blocked_failing = []
        for table in blocked_tables:
            has_access = auth_manager.check_user_permission(user_id, 'table', table, 'read')
            if not has_access:  # Should be blocked
                blocked_working.append(table)
            else:
                blocked_failing.append(table)

        # Test write access (should be blocked for non-admins)
        write_test = "N/A"
        if role != 'admin' and allowed_tables:
            can_write = auth_manager.check_user_permission(user_id, 'table', allowed_tables[0], 'write')
            write_test = "BLOCKED" if not can_write else "ALLOWED (ISSUE!)"

        # Display results
        print(f"ALLOWED ACCESS: {', '.join(allowed_working) if allowed_working else 'None'}")
        if allowed_failing:
            print(f"FAILED ALLOWED: {', '.join(allowed_failing)} (ISSUE!)")
            all_working = False

        print(f"BLOCKED ACCESS: {', '.join(blocked_working) if blocked_working else 'None'}")
        if blocked_failing:
            print(f"FAILED BLOCKED: {', '.join(blocked_failing)} (ISSUE!)")
            all_working = False

        if role != 'admin':
            print(f"WRITE ACCESS: {write_test}")
            if write_test != "BLOCKED":
                all_working = False

        # Overall status for this user
        user_working = not allowed_failing and not blocked_failing and (role == 'admin' or write_test == "BLOCKED")
        status = "WORKING" if user_working else "ISSUES FOUND"
        print(f"STATUS: {status}")

    print("\n" + "=" * 80)
    if all_working:
        print("SUCCESS: All users have properly working permissions!")
    else:
        print("ISSUES: Some users have permission problems that need fixing.")

    return all_working

if __name__ == "__main__":
    test_working_permissions()