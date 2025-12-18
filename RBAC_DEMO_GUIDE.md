# 🔐 RBAC Demo Guide - Permission Denied Messages

## 🎯 Purpose
This guide shows you how to demonstrate the Role-Based Access Control (RBAC) system with **proper permission denied messages**.

---

## 🚀 How to Run the Demo

```powershell
python -m streamlit run streamlit_standalone.py --server.port 8504
```

---

## 📋 **DEMO SCRIPT - Show Permission Denied Messages**

### **STEP 1: Login as Regular User (Limited Access)**

**Login Credentials:**
```
Email: user@healthplus.com
Password: user123
Role: User
```

#### **Try Restricted Queries - Show Error Messages**

**Query 1: Try to Access System Metrics**
```
Show system performance metrics
```

**Expected Result:**
```
🚫 Access Denied: System Metrics Access Denied

Your role (User) does not have permission to access system performance metrics.

📋 Query Attempted: Show system performance metrics
👤 Your Role: User
🔑 Required Role: Admin
🔒 Restricted Feature: System Metrics

💡 Suggestion: System metrics are restricted to administrators only.
Please contact your system administrator if you need this access.
```

---

**Query 2: Try to Access User Management**
```
List all active users
```

**Expected Result:**
```
🚫 Access Denied: User Management Access Denied

Your role (User) does not have permission to access user management data.

📋 Query Attempted: List all active users
👤 Your Role: User
🔑 Required Role: Admin
🔒 Restricted Feature: User Management

💡 Suggestion: User management features are restricted to administrators.
You can only view your own user profile.
```

---

**Query 3: Try to Access Error Logs**
```
Display error logs from today
```

**Expected Result:**
```
🚫 Access Denied: System Logs Access Denied

Your role (User) does not have permission to access system logs.

📋 Query Attempted: Display error logs from today
👤 Your Role: User
🔑 Required Role: Admin
🔒 Restricted Feature: Error Logs

💡 Suggestion: Error logs and system logs are restricted to administrators
for security purposes.
```

---

**Query 4: Try to Delete Data**
```
Delete all products
```

**Expected Result:**
```
🚫 Access Denied: Data Modification Denied

Your role (User) does not have permission to modify data.

📋 Query Attempted: Delete all products
👤 Your Role: User
🔑 Required Role: Admin
🔒 Restricted Feature: Modify Data

💡 Suggestion: Data modification operations (DELETE, UPDATE, INSERT)
are restricted to administrators only.
```

---

### **STEP 2: Login as Analyst (Moderate Access)**

**Logout and Login:**
```
Email: analyst@techcorp.com
Password: analyst123
Role: Analyst
```

#### **Try Analyst-Restricted Queries**

**Query 1: Try System Metrics (Still Blocked)**
```
Show system performance metrics
```

**Expected Result:**
```
🚫 Access Denied: System Metrics Access Denied

Your role (Analyst) does not have permission to access system performance metrics.

👤 Your Role: Analyst
🔑 Required Role: Admin
```

---

**Query 2: Try User Management (Still Blocked)**
```
List all active users
```

**Expected Result:**
```
🚫 Access Denied: User Management Access Denied

Your role (Analyst) does not have permission to access user management data.
```

---

**Query 3: Try Data Modification (Blocked)**
```
Delete user records
```

**Expected Result:**
```
🚫 Access Denied: Data Modification Denied

Your role (Analyst) does not have permission to modify data.
```

---

**Query 4: Analytics Query (ALLOWED)**
```
Show me all products
```

**Expected Result:**
✅ **Success** - Query executes and shows TechCorp products

---

### **STEP 3: Login as Admin (Full Access)**

**Logout and Login:**
```
Email: admin@techcorp.com
Password: admin123
Role: Admin
```

#### **Try All Queries - All Should Work**

**Query 1: System Metrics (NOW ALLOWED)**
```
Show system performance metrics
```
✅ **Success** - Admin can access system metrics

**Query 2: User Management (NOW ALLOWED)**
```
List all active users
```
✅ **Success** - Admin can access user data

**Query 3: Error Logs (NOW ALLOWED)**
```
Display error logs from today
```
✅ **Success** - Admin can view logs

**Query 4: Regular Queries (ALLOWED)**
```
Show me all products
```
✅ **Success** - Admin can access all data

---

## 🎭 **COMPLETE TEST QUERY LIST**

### **❌ Queries That Should Be BLOCKED for User/Analyst**

```sql
-- System Metrics (Admin Only)
Show system performance metrics
System health check
Show server status
Display system performance

-- User Management (Admin Only)
List all active users
Show all users
Create new user
Delete user account
Modify user permissions

-- Error Logs (Admin Only)
Display error logs from today
Show system logs
View debug logs
Show exception logs

-- Data Modification (Admin Only)
Delete all products
Update product prices
Insert new records
Drop table users
Truncate orders table
Alter database schema
```

### **✅ Queries That Should WORK for All Roles**

```sql
-- Basic Data Queries
Show me all products
How many users are in the system
Top customers by sales
What is the average order value
List product categories

-- Analytics (Analyst & Admin)
Show monthly revenue trends
Calculate total sales
Average customer spending
Inventory levels by warehouse
```

---

## 🎪 **INTERACTIVE DEMO FLOW**

### **5-Minute Permission Demo**

**Minute 1: Introduction**
- "I'll show you how our RBAC system protects sensitive data"
- "Each role has different permissions"

**Minute 2: User Role Demo**
- Login as User
- Try: `Show system performance metrics`
- Show the detailed error message
- Point out: Query attempted, role, required role, suggestion

**Minute 3: Analyst Role Demo**
- Logout, login as Analyst
- Try: `List all active users` (blocked)
- Try: `Show me all products` (allowed)
- Explain: "Analysts can analyze data but not manage users"

**Minute 4: Admin Role Demo**
- Logout, login as Admin
- Try: `Show system performance metrics` (now works!)
- Try: `List all active users` (now works!)
- Explain: "Admins have full access"

**Minute 5: Show Permission Details**
- Click "What can I do with my current role?"
- Show allowed and restricted features
- Demonstrate the expandable permission info

---

## 📊 **Permission Matrix**

| Query Type | User | Analyst | Admin |
|------------|------|---------|-------|
| View Products | ✅ | ✅ | ✅ |
| View Customers | ✅ | ✅ | ✅ |
| Basic Analytics | ✅ | ✅ | ✅ |
| Advanced Analytics | ❌ | ✅ | ✅ |
| System Metrics | ❌ | ❌ | ✅ |
| User Management | ❌ | ❌ | ✅ |
| Error Logs | ❌ | ❌ | ✅ |
| Modify Data | ❌ | ❌ | ✅ |

---

## 🎯 **Key Features to Highlight**

1. **Clear Error Messages**
   - Shows exactly what was attempted
   - Explains why it was blocked
   - Shows required role

2. **Helpful Suggestions**
   - Guides users on what to do
   - Explains who to contact
   - Shows alternative actions

3. **Permission Information**
   - Expandable "What can I do?" section
   - Lists allowed features
   - Lists restricted features

4. **Role Hierarchy**
   - User < Analyst < Admin
   - Clear permission progression
   - No ambiguity

5. **Security by Design**
   - Permissions checked before query execution
   - Cannot bypass restrictions
   - All attempts logged

---

## 💡 **Talking Points for Demo**

1. **"Clear Communication"**
   - "Notice how the error message tells you exactly what happened"

2. **"Helpful, Not Frustrating"**
   - "The system doesn't just say 'no' - it explains why and what you can do"

3. **"Role-Appropriate Access"**
   - "Each role sees only what they need for their job"

4. **"Security Without Complexity"**
   - "Users understand their permissions without reading documentation"

5. **"Enterprise-Grade RBAC"**
   - "This is production-ready access control"

---

## 🔥 **Pro Demo Tips**

1. **Show the Error First**
   - Start with a blocked query to get attention
   - Error messages are more impressive than success

2. **Compare Side-by-Side**
   - Open two browser windows
   - User in one, Admin in other
   - Run same query on both

3. **Click the Expander**
   - Show the "What can I do?" section
   - Demonstrate self-service permission info

4. **Explain the Colors**
   - Red (error) = Blocked
   - Yellow (warning) = Details
   - Blue (info) = Suggestions
   - Green (success) = Allowed features

5. **Tell a Story**
   - "Imagine you're a new employee..."
   - "You accidentally try to access HR data..."
   - "The system guides you appropriately..."

---

## 📋 **Quick Reference**

### **Test Accounts**
```
User:    user@healthplus.com / user123
Analyst: analyst@techcorp.com / analyst123
Admin:   admin@techcorp.com / admin123
```

### **Blocked Queries for Testing**
```
Show system performance metrics
List all active users
Display error logs from today
Delete all products
```

### **Allowed Queries for Testing**
```
Show me all products
Top customers by sales
How many users are in the system
```

---

**🎉 Your RBAC system now provides clear, helpful, and professional permission denied messages!**
