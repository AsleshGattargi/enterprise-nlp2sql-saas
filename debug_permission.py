#!/usr/bin/env python3
"""
Debug the exact permission check that's failing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.auth import AuthManager

def debug_permission():
    auth_manager = AuthManager()

    user_id = 'user-205'
    resource_type = 'table'
    resource_name = 'courses'
    required_access = 'read'

    print(f"Testing permission for user {user_id}")
    print(f"Resource: {resource_type}/{resource_name}")
    print(f"Required access: {required_access}")
    print("=" * 50)

    # Test the exact call that should be happening in the query engine
    has_permission = auth_manager.check_user_permission(user_id, resource_type, resource_name, required_access)

    print(f"Permission result: {has_permission}")

    # Let's also test other tables
    test_tables = ['courses', 'enrollments', 'grades', 'assignments', 'students', 'instructors']

    print("\nTesting all EduLearn tables:")
    for table in test_tables:
        has_access = auth_manager.check_user_permission(user_id, 'table', table, 'read')
        print(f"  {table}: {'ALLOWED' if has_access else 'BLOCKED'}")

if __name__ == "__main__":
    debug_permission()