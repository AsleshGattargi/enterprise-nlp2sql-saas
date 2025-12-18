"""
Show Database Contents
Displays database structure and data for demo purposes.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

def show_database(db_path):
    """Display database contents in a formatted way."""

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        print(f"💡 Run 'python demo_simple.py' first to create the databases")
        return

    conn = sqlite3.connect(db_path)

    # Get all tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn
    )

    print(f"\n{'='*70}")
    print(f"🗄️  DATABASE: {Path(db_path).name}")
    print(f"{'='*70}\n")

    # Show each table
    for table_name in tables['name']:
        print(f"\n📋 TABLE: {table_name.upper()}")
        print("-" * 70)

        # Get schema
        schema = pd.read_sql_query(
            f"PRAGMA table_info({table_name})",
            conn
        )
        print("\n🔧 SCHEMA:")
        for _, row in schema.iterrows():
            pk = " (PRIMARY KEY)" if row['pk'] else ""
            print(f"   • {row['name']:<20} {row['type']:<15} {pk}")

        # Get row count
        count = pd.read_sql_query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            conn
        )['count'][0]
        print(f"\n📊 TOTAL ROWS: {count}")

        # Show sample data
        if count > 0:
            data = pd.read_sql_query(
                f"SELECT * FROM {table_name} LIMIT 5",
                conn
            )
            print(f"\n📄 SAMPLE DATA (First {min(5, count)} rows):")
            print(data.to_string(index=False, max_colwidth=40))
        else:
            print("\n📄 No data in this table")

        print("\n" + "="*70)

    conn.close()

def compare_databases(db1_path, db2_path):
    """Compare two databases side by side."""

    print(f"\n{'='*70}")
    print("🔍 DATABASE COMPARISON")
    print(f"{'='*70}\n")

    conn1 = sqlite3.connect(db1_path)
    conn2 = sqlite3.connect(db2_path)

    # Get tables from both
    tables1 = set(pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn1
    )['name'])

    tables2 = set(pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn2
    )['name'])

    common_tables = tables1.intersection(tables2)

    print(f"📋 Common Tables: {len(common_tables)}")
    print(f"   {', '.join(sorted(common_tables))}\n")

    # Compare each table
    for table_name in sorted(common_tables):
        print(f"\n🔍 Comparing table: {table_name.upper()}")
        print("-" * 70)

        # Count rows
        count1 = pd.read_sql_query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            conn1
        )['count'][0]

        count2 = pd.read_sql_query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            conn2
        )['count'][0]

        print(f"📊 {Path(db1_path).stem}: {count1} rows")
        print(f"📊 {Path(db2_path).stem}: {count2} rows")

        # Sample data from both
        if count1 > 0:
            data1 = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn1)
            print(f"\n📄 Sample from {Path(db1_path).stem}:")
            print(data1.to_string(index=False, max_colwidth=30))

        if count2 > 0:
            data2 = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 3", conn2)
            print(f"\n📄 Sample from {Path(db2_path).stem}:")
            print(data2.to_string(index=False, max_colwidth=30))

        print("\n" + "="*70)

    conn1.close()
    conn2.close()

def show_database_summary():
    """Show summary of all databases."""

    demo_dir = Path("demo_databases")

    if not demo_dir.exists():
        print("\n❌ demo_databases directory not found!")
        print("💡 Run 'python demo_simple.py' first to create the databases\n")
        return

    db_files = list(demo_dir.glob("*.sqlite"))

    if not db_files:
        print("\n❌ No database files found in demo_databases/")
        print("💡 Run 'python demo_simple.py' first to create the databases\n")
        return

    print(f"\n{'='*70}")
    print("📊 DATABASE SUMMARY")
    print(f"{'='*70}\n")

    for db_path in sorted(db_files):
        conn = sqlite3.connect(db_path)

        # Get table count
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            conn
        )

        print(f"🗄️  {db_path.name}")
        print(f"   📋 Tables: {len(tables)}")

        # Get total rows across all tables
        total_rows = 0
        for table_name in tables['name']:
            count = pd.read_sql_query(
                f"SELECT COUNT(*) as count FROM {table_name}",
                conn
            )['count'][0]
            total_rows += count
            print(f"      • {table_name}: {count} rows")

        print(f"   📊 Total Rows: {total_rows}\n")

        conn.close()

    print(f"{'='*70}\n")

def main():
    """Main function."""

    print("\n" + "="*70)
    print("🗄️  DATABASE VIEWER - Multi-Tenant NLP2SQL Demo")
    print("="*70)

    if len(sys.argv) > 1:
        # Show specific database
        db_path = sys.argv[1]
        show_database(db_path)
    else:
        # Show summary and both databases
        show_database_summary()

        techcorp_db = "demo_databases/techcorp_db.sqlite"
        healthplus_db = "demo_databases/healthplus_db.sqlite"

        if Path(techcorp_db).exists() and Path(healthplus_db).exists():
            print("\n" + "="*70)
            print("Would you like to:")
            print("1. View TechCorp database")
            print("2. View HealthPlus database")
            print("3. Compare both databases")
            print("4. View all in detail")
            print("="*70)

            choice = input("\nEnter your choice (1-4) or press Enter to skip: ").strip()

            if choice == "1":
                show_database(techcorp_db)
            elif choice == "2":
                show_database(healthplus_db)
            elif choice == "3":
                compare_databases(techcorp_db, healthplus_db)
            elif choice == "4":
                print("\n🏢 TECHCORP SOLUTIONS DATABASE")
                show_database(techcorp_db)
                print("\n\n🏥 HEALTHPLUS MEDICAL DATABASE")
                show_database(healthplus_db)
                print("\n\n🔍 COMPARISON")
                compare_databases(techcorp_db, healthplus_db)

if __name__ == "__main__":
    main()
