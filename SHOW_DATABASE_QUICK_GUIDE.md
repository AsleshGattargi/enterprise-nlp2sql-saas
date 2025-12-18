# 🚀 Quick Guide: Show the Database

## 📊 **3 Best Methods**

---

## ✅ **METHOD 1: Python Script (Easiest)**

### **View Database in Terminal:**
```powershell
python show_database.py
```

**Interactive Menu:**
```
1. View TechCorp database
2. View HealthPlus database
3. Compare both databases
4. View all in detail
```

**What You See:**
- Table names and schemas
- Row counts
- Sample data from each table
- Side-by-side comparison

**Output Example:**
```
🗄️  DATABASE: techcorp_db.sqlite
======================================================================

📋 TABLE: PRODUCTS
----------------------------------------------------------------------
🔧 SCHEMA:
   • product_id          INTEGER         (PRIMARY KEY)
   • name                VARCHAR(100)
   • category            VARCHAR(50)
   • price               DECIMAL(10,2)
   • stock_quantity      INTEGER

📊 TOTAL ROWS: 5

📄 SAMPLE DATA (First 5 rows):
   product_id                     name  category        price  stock
            1  Enterprise Software...  Software       999.99     50
            2    Data Analytics Suite  Analytics      599.99     30
            3    Cloud Server Instance  Infrastructure 299.99    100
```

---

## ✅ **METHOD 2: Export to Excel (Best for Sharing)**

### **Export All Databases:**
```powershell
python export_database_to_excel.py
```

**Choose Option:**
```
1. Export all demo databases
2. Export TechCorp database only
3. Export HealthPlus database only
4. Create side-by-side comparison Excel
```

**Output Files:**
- `TechCorp_Database.xlsx` - All TechCorp tables
- `HealthPlus_Database.xlsx` - All HealthPlus tables
- `Database_Comparison.xlsx` - Side-by-side comparison

**Open in Excel and show during demo!**

---

## ✅ **METHOD 3: DB Browser for SQLite (Most Professional)**

### **Install:**
1. Download from: https://sqlitebrowser.org/
2. Install (free, 5MB)

### **Open Database:**
```
File → Open Database
Navigate to: demo_databases/
Select: techcorp_db.sqlite
```

### **Show During Demo:**
1. **Browse Data tab** → See actual data
2. **Database Structure tab** → See schemas
3. **Execute SQL tab** → Run queries live

### **Open Both at Once:**
- Open TechCorp in one window
- Open HealthPlus in another window
- Show side-by-side comparison

---

## 🎯 **RECOMMENDED: Use All Three!**

### **Before Demo:**
1. **Export to Excel** → Create backup files
2. **Install DB Browser** → For live showing

### **During Demo:**
1. **Start with Excel** → Show overview
2. **Switch to DB Browser** → Show live data
3. **End with Python script** → Show comparison

---

## 📋 **Demo Script**

### **STEP 1: Show Files (30 seconds)**
```powershell
# Open folder
cd demo_databases
ls
```

**Say:** "Each tenant has their own database file"
- techcorp_db.sqlite
- healthplus_db.sqlite

---

### **STEP 2: Show Database Contents (2 minutes)**

**Option A: Python Script**
```powershell
python show_database.py
# Select option 4 (View all in detail)
```

**Option B: DB Browser**
```
1. Open techcorp_db.sqlite
2. Click "Browse Data" tab
3. Select "products" table
4. Show data: Enterprise Software, Cloud Servers, etc.
```

**Say:** "This is TechCorp's data - all technology products"

---

### **STEP 3: Show Second Database (2 minutes)**

**Python Script:**
```powershell
# Already shown in comparison view
```

**DB Browser:**
```
1. Open healthplus_db.sqlite
2. Click "Browse Data" tab
3. Select "products" table
4. Show data: X-Rays, Consultations, Lab Tests
```

**Say:** "Same schema, but healthcare data instead!"

---

### **STEP 4: Show Comparison (1 minute)**

**Python Script:**
```powershell
python show_database.py
# Select option 3 (Compare both databases)
```

**Shows:**
```
🔍 Comparing table: PRODUCTS
----------------------------------------------------------------------
📊 techcorp_db: 5 rows
📊 healthplus_db: 5 rows

📄 Sample from techcorp_db:
   Enterprise Software License    $999.99
   Data Analytics Suite           $599.99
   Cloud Server Instance          $299.99

📄 Sample from healthplus_db:
   X-Ray Examination              $200.00
   General Consultation           $150.00
   Physical Therapy Session       $120.00
```

**Say:** "See? Same structure, different data - complete isolation!"

---

## 💡 **Pro Tips**

### **Tip 1: Pre-Export to Excel**
Before your demo, create Excel files:
```powershell
python export_database_to_excel.py
# Select option 4 (Create comparison Excel)
```

Open `Database_Comparison.xlsx` - perfect for screenshots!

### **Tip 2: Side-by-Side Windows**
- Open DB Browser twice
- Load both databases
- Arrange windows side-by-side
- Switch between them live

### **Tip 3: Use Big Font**
In DB Browser:
```
Edit → Preferences → Data Browser
→ Font size: 14pt
```

Audience can see better!

### **Tip 4: Prepare Queries**
In DB Browser's "Execute SQL" tab, prepare:
```sql
-- Show all products
SELECT * FROM products;

-- Show users by role
SELECT username, role, department FROM users;

-- Show customer totals
SELECT customer_name, total_spent FROM customers
ORDER BY total_spent DESC;
```

Run them live during demo!

---

## 🎭 **Complete Demo Flow (5 Minutes)**

### **Minute 1: Files**
```
→ Open Windows Explorer
→ Show demo_databases folder
→ Point to both .sqlite files
→ "Physical file separation"
```

### **Minute 2: TechCorp Database**
```
→ Open in DB Browser (or run Python script)
→ Show Products table → Tech products
→ Show Users table → Tech employees
→ "This is TechCorp's isolated data"
```

### **Minute 3: HealthPlus Database**
```
→ Open in DB Browser (or show in script)
→ Show Products table → Medical services
→ Show Users table → Healthcare staff
→ "Completely different data set"
```

### **Minute 4: Comparison**
```
→ Run python show_database.py (option 3)
→ Or arrange DB Browser windows side-by-side
→ "Same schema, different data"
→ Point out key differences
```

### **Minute 5: Live Query**
```
→ Go back to Streamlit app
→ Login as TechCorp admin
→ Query: "Show me all products"
→ Results: Tech products
→ Logout, login as HealthPlus user
→ Same query → Medical services
→ "The app queries these databases in real-time"
```

---

## 🚀 **Quick Commands**

```powershell
# Create demo databases
python demo_simple.py

# View databases in terminal
python show_database.py

# Export to Excel
python export_database_to_excel.py

# Start the app
python -m streamlit run streamlit_standalone.py --server.port 8504
```

---

## 📊 **What the Audience Sees**

### **Database Files:**
```
demo_databases/
├── techcorp_db.sqlite     (24 KB)
└── healthplus_db.sqlite   (22 KB)
```

### **Table Structure (Same for Both):**
```
✅ products     → Product catalog
✅ users        → User accounts
✅ orders       → Order history
✅ customers    → Customer list
```

### **Data Differences:**
```
TechCorp          vs          HealthPlus
-------------                 ---------------
Software                      Medical Services
Cloud Servers                 Consultations
API Kits                      Lab Tests
Tech Companies                Hospitals
IT Staff                      Healthcare Staff
```

---

## ✅ **Checklist Before Demo**

- [ ] Demo databases created (`python demo_simple.py`)
- [ ] DB Browser installed (if using)
- [ ] Excel exports created (if using)
- [ ] Python script tested (`python show_database.py`)
- [ ] Windows arranged (if using DB Browser)
- [ ] Font size increased (for visibility)
- [ ] Queries prepared (if running live SQL)
- [ ] Streamlit app tested
- [ ] Screenshots taken (as backup)

---

**You're ready to show the database! 🎉**
