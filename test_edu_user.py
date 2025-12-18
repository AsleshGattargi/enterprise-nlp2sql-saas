#!/usr/bin/env python3
"""
Test EduLearn analyst permissions specifically
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.auth import AuthManager

def test_edu_analyst():
    auth_manager = AuthManager()

    user_id = 'user-205'
    tables_to_test = ['courses', 'enrollments', 'grades', 'assignments', 'students', 'instructors']

    print(f"Testing EduLearn Analyst (user-205): alex.academic205@edulearn.edu")
    print("=" * 60)

    for table in tables_to_test:
        has_read_access = auth_manager.check_user_permission(user_id, 'table', table, 'read')
        has_write_access = auth_manager.check_user_permission(user_id, 'table', table, 'write')

        print(f"Table '{table}': Read={has_read_access}, Write={has_write_access}")

if __name__ == "__main__":
    test_edu_analyst()