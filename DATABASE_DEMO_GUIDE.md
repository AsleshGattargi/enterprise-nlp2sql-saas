# 🗄️ How to Show the Database - Complete Demo Guide

## 🎯 **Multiple Ways to Show Database**

You can demonstrate the database structure and data in several ways:

---

## 📊 **OPTION 1: Show Database Schema in the App**

### **Add a "Show Database Schema" Feature**

Let me create a simple script that displays the database structure:

**Query to show tables:**
```
Show database schema
Show all tables
List database structure
```

This would display:
- Table names
- Column names and types
- Relationships
- Sample data counts

---

## 📊 **OPTION 2: SQLite Browser (Best for Demo)**

### **Install DB Browser for SQLite**

1. **Download:**
   - Visit: https://sqlitebrowser.org/
   - Download for Windows
   - Install (it's free and portable)

2. **Open Demo Databases:**
   ```
   File → Open Database
   Navigate to: D:\Fundae\Multi Tenant NLP2SQL\demo_databases\
   Open: techcorp_db.sqlite
   ```

3. **Show the Audience:**
   - **Browse Data tab** → See actual data in tables
   - **Database Structure tab** → See table schemas
   - **Execute SQL tab** → Run queries manually

### **What to Show:**
- ✅ Tables: users, products, orders, customers
- ✅ Data: Real rows with tech vs healthcare data
- ✅ Schema: Column names and types
- ✅ Relationships: How tables connect

---

## 📊 **OPTION 3: Add Database Viewer to Streamlit App**

I can add a "Database Explorer" section to your app that shows:
- List of all tables
- Schema for each table
- Sample data from each table
- Row counts

Would you like me to implement this?

---

## 📊 **OPTION 4: Visual Database Diagram**

### **Use dbdiagram.io**

Create a visual diagram showing:
- All tables
- Column names
- Primary/Foreign keys
- Relationships

**Quick ERD Diagram:**
```
┌─────────────────┐       ┌─────────────────┐
│     USERS       │       │    PRODUCTS     │
├─────────────────┤       ├─────────────────┤
│ user_id (PK)    │       │ product_id (PK) │
│ username        │       │ name            │
│ email           │       │ category        │
│ role            │       │ price           │
│ department      │       │ stock_quantity  │
└─────────────────┘       └─────────────────┘
        │                         │
        │                         │
        ↓                         ↓
┌─────────────────┐       ┌─────────────────┐
│     ORDERS      │       │   CUSTOMERS     │
├─────────────────┤       ├─────────────────┤
│ order_id (PK)   │       │ customer_id(PK) │
│ customer_name   │       │ customer_name   │
│ product_id (FK) │───→   │ email           │
│ quantity        │       │ total_orders    │
│ order_total     │       │ total_spent     │
└─────────────────┘       └─────────────────┘
```

---

## 📊 **OPTION 5: Python Script to Show Database**

Create a simple script to display database contents:

**File: `show_database.py`**
```python
import sqlite3
import pandas as pd
from pathlib import Path

def show_database(db_path):
    """Display database contents."""
    conn = sqlite3.connect(db_path)

    # Get all tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn
    )

    print(f"\n{'='*60}")
    print(f"Database: {Path(db_path).name}")
    print(f"{'='*60}\n")

    # Show each table
    for table_name in tables['name']:
        print(f"\n📋 Table: {table_name.upper()}")
        print("-" * 60)

        # Get schema
        schema = pd.read_sql_query(
            f"PRAGMA table_info({table_name})",
            conn
        )
        print("\n🔧 Schema:")
        print(schema[['name', 'type']].to_string(index=False))

        # Get row count
        count = pd.read_sql_query(
            f"SELECT COUNT(*) as count FROM {table_name}",
            conn
        )['count'][0]
        print(f"\n📊 Total Rows: {count}")

        # Show sample data
        data = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT 5",
            conn
        )
        print(f"\n📄 Sample Data (First 5 Rows):")
        print(data.to_string(index=False))
        print("\n" + "="*60)

    conn.close()

# Show both databases
if __name__ == "__main__":
    print("\n🏢 TECHCORP SOLUTIONS DATABASE")
    show_database("demo_databases/techcorp_db.sqlite")

    print("\n\n🏥 HEALTHPLUS MEDICAL DATABASE")
    show_database("demo_databases/healthplus_db.sqlite")
```

**Run it:**
```powershell
python show_database.py
```

---

## 📊 **OPTION 6: Live Demo Queries**

### **Show Database Contents Through Queries**

Run these queries in your app to show the database:

#### **1. Show All Tables**
```sql
SELECT name, type FROM sqlite_master WHERE type='table'
```

#### **2. Show Table Schema**
```sql
PRAGMA table_info(products)
```

#### **3. Show Data Counts**
```sql
SELECT
    'Products' as table_name, COUNT(*) as row_count FROM products
UNION ALL
SELECT 'Users', COUNT(*) FROM users
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Customers', COUNT(*) FROM customers
```

#### **4. Show Sample Data from Each Table**
```sql
-- Products
SELECT * FROM products LIMIT 5

-- Users
SELECT * FROM users LIMIT 5

-- Orders
SELECT * FROM orders LIMIT 5

-- Customers
SELECT * FROM customers LIMIT 5
```

---

## 📊 **OPTION 7: Create Database Screenshot/Export**

### **Export Database Contents to Excel**

```python
import sqlite3
import pandas as pd

def export_database_to_excel(db_path, output_file):
    """Export all tables to Excel with separate sheets."""
    conn = sqlite3.connect(db_path)

    # Get all tables
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table'",
        conn
    )

    # Create Excel writer
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for table_name in tables['name']:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            df.to_excel(writer, sheet_name=table_name, index=False)

    conn.close()
    print(f"✅ Database exported to: {output_file}")

# Export both databases
export_database_to_excel(
    "demo_databases/techcorp_db.sqlite",
    "TechCorp_Database.xlsx"
)

export_database_to_excel(
    "demo_databases/healthplus_db.sqlite",
    "HealthPlus_Database.xlsx"
)
```

Then open the Excel file during your demo!

---

## 🎭 **RECOMMENDED DEMO FLOW**

### **5-Minute Database Demo:**

**Minute 1: Overview**
- "Let me show you the actual database structure"
- Open DB Browser for SQLite

**Minute 2: Show TechCorp Database**
- Open `techcorp_db.sqlite`
- Show Products table → Technology products
- Show Users table → Tech employees
- Show Customers table → Tech companies

**Minute 3: Show HealthPlus Database**
- Open `healthplus_db.sqlite`
- Show Products table → Medical services
- Show Users table → Healthcare staff
- Show Customers table → Healthcare facilities

**Minute 4: Compare Side-by-Side**
- Open both databases in separate windows
- Show same table (products) in both
- **Point out:** "Same schema, different data!"

**Minute 5: Live Query**
- Go back to Streamlit app
- Run query on both tenants
- "The app queries these databases in real-time"

---

## 🎯 **BEST METHOD FOR YOUR DEMO**

I recommend **OPTION 2** (SQLite Browser) because:

✅ **Visual and Professional**
- Clean interface
- Easy to navigate
- Shows structure and data clearly

✅ **Interactive**
- Can browse tables live
- Can run queries manually
- Can show relationships

✅ **No Code Required**
- No programming during demo
- Just point and click
- Less chance of errors

✅ **Side-by-Side Comparison**
- Open both databases at once
- Compare schemas
- Compare data

---

## 🚀 **Quick Setup (1 Minute)**

1. **Download DB Browser:**
   ```
   https://sqlitebrowser.org/dl/
   ```

2. **Create Demo Databases:**
   ```powershell
   python demo_simple.py
   ```

3. **Open in Browser:**
   ```
   File → Open Database
   Select: demo_databases/techcorp_db.sqlite
   ```

4. **Ready to Demo!**

---

## 📋 **What to Show Your Audience**

### **1. Database Files**
```
demo_databases/
├── techcorp_db.sqlite     ← TechCorp's database
└── healthplus_db.sqlite   ← HealthPlus's database
```

**Say:** "Each tenant has their own isolated database file"

### **2. Table Structure**
Show that both have identical schemas:
```
✅ users
✅ products
✅ orders
✅ customers
```

**Say:** "Same structure, but different data"

### **3. Data Differences**

**TechCorp Products:**
- Enterprise Software License ($999.99)
- Cloud Server Instance ($299.99)
- API Development Kit ($149.99)

**HealthPlus Products:**
- X-Ray Examination ($200.00)
- General Consultation ($150.00)
- Physical Therapy ($120.00)

**Say:** "See how the data is industry-specific?"

### **4. User Tables**

**TechCorp Users:**
- Departments: IT, Engineering, Sales
- Roles: Admin, Analyst, Developer

**HealthPlus Users:**
- Departments: Emergency, Nursing, Reception
- Roles: Admin, Doctor, Nurse

**Say:** "Even the users are tenant-specific"

---

## 💡 **Pro Demo Tips**

1. **Prepare Screenshots**
   - Take screenshots of both databases
   - Create a PowerPoint with comparisons
   - Use as backup if live demo fails

2. **Pre-open Everything**
   - Open DB Browser before demo
   - Load both databases
   - Position windows side-by-side

3. **Highlight Key Points**
   - Use cursor to point to data
   - Zoom in on important columns
   - Circle/highlight differences

4. **Tell a Story**
   - "When TechCorp signs up..."
   - "We create their database..."
   - "Populate with relevant data..."
   - "Completely isolated from HealthPlus..."

5. **Show the Files**
   - Open Windows Explorer
   - Navigate to demo_databases folder
   - Show the .sqlite files
   - "Physical separation at file level"

---

## 🎪 **Alternative: Add to Your App**

Would you like me to add a "Database Explorer" page to your Streamlit app?

It would show:
- 📋 List of all tables
- 🔧 Schema for each table
- 📊 Row counts
- 📄 Sample data
- 🔍 Search functionality

This would let you show the database without leaving the app!

---

**Which method would you like to use? I can help implement any of these options!** 🚀
