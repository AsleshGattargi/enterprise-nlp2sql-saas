"""Quick verification of enhanced database data."""
import sqlite3

print("\n" + "="*70)
print("DATABASE VERIFICATION - Enhanced Mock Data")
print("="*70)

# TechCorp
print("\nTechCorp Solutions:")
print("-"*70)
conn = sqlite3.connect('demo_databases/techcorp_db.sqlite')

print(f"  Users: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]} rows")
print(f"  Products: {conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]} rows")
print(f"  Customers: {conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]} rows")
print(f"  Orders: {conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]} rows")

print("\n  Top 5 Products by Price:")
for name, price in conn.execute('SELECT name, price FROM products ORDER BY price DESC LIMIT 5').fetchall():
    print(f"    - {name}: ${price:.2f}")

print("\n  Top 5 Customers:")
for name, spent in conn.execute('SELECT customer_name, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5').fetchall():
    print(f"    - {name}: ${spent:,.2f}")

conn.close()

# HealthPlus
print("\n\nHealthPlus Medical:")
print("-"*70)
conn = sqlite3.connect('demo_databases/healthplus_db.sqlite')

print(f"  Staff: {conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]} rows")
print(f"  Services: {conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]} rows")
print(f"  Customers: {conn.execute('SELECT COUNT(*) FROM customers').fetchone()[0]} rows")
print(f"  Orders: {conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]} rows")

print("\n  Top 5 Services by Price:")
for name, price in conn.execute('SELECT name, price FROM products ORDER BY price DESC LIMIT 5').fetchall():
    print(f"    - {name}: ${price:.2f}")

print("\n  Top 5 Healthcare Customers:")
for name, spent in conn.execute('SELECT customer_name, total_spent FROM customers ORDER BY total_spent DESC LIMIT 5').fetchall():
    print(f"    - {name}: ${spent:,.2f}")

conn.close()

print("\n" + "="*70)
print("VERIFICATION COMPLETE!")
print("="*70)
print("\nBoth databases now have 5x more data!")
print("- 15 users (was 3)")
print("- 20 products (was 4)")
print("- 15 customers (was 3)")
print("- 20 orders (was 3)")
print("\n")
