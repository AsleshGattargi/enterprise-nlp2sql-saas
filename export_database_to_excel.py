"""
Export Database to Excel
Export SQLite database tables to Excel file for demo purposes.
"""

import sqlite3
import pandas as pd
from pathlib import Path
import sys

def export_database_to_excel(db_path, output_file=None):
    """Export all tables to Excel with separate sheets."""

    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False

    # Generate output filename if not provided
    if output_file is None:
        db_name = Path(db_path).stem
        output_file = f"{db_name}_export.xlsx"

    print(f"\n{'='*70}")
    print(f"📊 EXPORTING DATABASE TO EXCEL")
    print(f"{'='*70}\n")
    print(f"📂 Source: {db_path}")
    print(f"📄 Output: {output_file}\n")

    try:
        conn = sqlite3.connect(db_path)

        # Get all tables
        tables = pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            conn
        )

        print(f"📋 Found {len(tables)} tables:")
        for table_name in tables['name']:
            print(f"   • {table_name}")

        print(f"\n🔄 Exporting...")

        # Create Excel writer
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for table_name in tables['name']:
                # Read table data
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

                # Write to Excel
                df.to_excel(writer, sheet_name=table_name, index=False)

                print(f"   ✅ {table_name}: {len(df)} rows exported")

        conn.close()

        print(f"\n✅ SUCCESS! Database exported to: {output_file}")
        print(f"{'='*70}\n")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        return False

def export_all_demo_databases():
    """Export all demo databases to Excel."""

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
    print("📊 BATCH EXPORT - ALL DEMO DATABASES")
    print(f"{'='*70}\n")

    success_count = 0
    for db_path in sorted(db_files):
        output_file = f"{db_path.stem}_export.xlsx"
        if export_database_to_excel(str(db_path), output_file):
            success_count += 1

    print(f"\n{'='*70}")
    print(f"✅ Exported {success_count}/{len(db_files)} databases successfully")
    print(f"{'='*70}\n")

def create_comparison_excel():
    """Create an Excel file comparing both databases side-by-side."""

    techcorp_db = Path("demo_databases/techcorp_db.sqlite")
    healthplus_db = Path("demo_databases/healthplus_db.sqlite")

    if not techcorp_db.exists() or not healthplus_db.exists():
        print("\n❌ Demo databases not found!")
        print("💡 Run 'python demo_simple.py' first to create the databases\n")
        return

    output_file = "Database_Comparison.xlsx"

    print(f"\n{'='*70}")
    print(f"🔍 CREATING COMPARISON EXCEL")
    print(f"{'='*70}\n")

    try:
        conn1 = sqlite3.connect(techcorp_db)
        conn2 = sqlite3.connect(healthplus_db)

        # Get common tables
        tables1 = set(pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            conn1
        )['name'])

        tables2 = set(pd.read_sql_query(
            "SELECT name FROM sqlite_master WHERE type='table'",
            conn2
        )['name'])

        common_tables = sorted(tables1.intersection(tables2))

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Create summary sheet
            summary_data = []
            for table_name in common_tables:
                count1 = pd.read_sql_query(
                    f"SELECT COUNT(*) as count FROM {table_name}",
                    conn1
                )['count'][0]

                count2 = pd.read_sql_query(
                    f"SELECT COUNT(*) as count FROM {table_name}",
                    conn2
                )['count'][0]

                summary_data.append({
                    "Table": table_name,
                    "TechCorp Rows": count1,
                    "HealthPlus Rows": count2
                })

            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            print(f"   ✅ Summary sheet created")

            # Create sheets for each table (both databases)
            for table_name in common_tables:
                # TechCorp data
                df1 = pd.read_sql_query(f"SELECT * FROM {table_name}", conn1)
                sheet_name1 = f"TC_{table_name}"[:31]  # Excel sheet name limit
                df1.to_excel(writer, sheet_name=sheet_name1, index=False)

                # HealthPlus data
                df2 = pd.read_sql_query(f"SELECT * FROM {table_name}", conn2)
                sheet_name2 = f"HP_{table_name}"[:31]
                df2.to_excel(writer, sheet_name=sheet_name2, index=False)

                print(f"   ✅ {table_name}: TechCorp ({len(df1)} rows) & HealthPlus ({len(df2)} rows)")

        conn1.close()
        conn2.close()

        print(f"\n✅ SUCCESS! Comparison file created: {output_file}")
        print(f"{'='*70}\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")

def main():
    """Main function."""

    print("\n" + "="*70)
    print("📊 DATABASE EXCEL EXPORTER - Multi-Tenant NLP2SQL Demo")
    print("="*70)

    if len(sys.argv) > 1:
        # Export specific database
        db_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        export_database_to_excel(db_path, output_file)
    else:
        # Interactive menu
        print("\nWhat would you like to do?")
        print("1. Export all demo databases")
        print("2. Export TechCorp database only")
        print("3. Export HealthPlus database only")
        print("4. Create side-by-side comparison Excel")
        print("="*70)

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            export_all_demo_databases()
        elif choice == "2":
            export_database_to_excel(
                "demo_databases/techcorp_db.sqlite",
                "TechCorp_Database.xlsx"
            )
        elif choice == "3":
            export_database_to_excel(
                "demo_databases/healthplus_db.sqlite",
                "HealthPlus_Database.xlsx"
            )
        elif choice == "4":
            create_comparison_excel()
        else:
            print("\n❌ Invalid choice\n")

if __name__ == "__main__":
    main()
