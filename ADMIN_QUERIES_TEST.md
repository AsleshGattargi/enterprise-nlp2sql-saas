# 🎯 Admin Queries Test Guide

## ✅ Issue Fixed!

Admin queries now return actual data. All three admin-only queries have been implemented with mock data.

---

## 🚀 How to Test

### Start the Application
```powershell
python -m streamlit run streamlit_standalone.py --server.port 8504
```

---

## 📋 Test Script

### **STEP 1: Test with Non-Admin (Should Be Blocked)**

**Login as User:**
```
Email: user@healthplus.com
Password: user123
Role: User
```

**Try Admin Queries:**

#### Query 1:
```
Show system performance metrics
```
❌ **Expected:** Permission Denied error with details

#### Query 2:
```
List all active users
```
❌ **Expected:** Permission Denied error with details

#### Query 3:
```
Display error logs from today
```
❌ **Expected:** Permission Denied error with details

---

### **STEP 2: Test with Admin (Should Show Data)**

**Logout and Login as Admin:**
```
Email: admin@techcorp.com
Password: admin123
Role: Admin
```

**Try Admin Queries - Now They Should Work:**

#### Query 1: System Performance Metrics
```
Show system performance metrics
```

✅ **Expected Result:** Table showing:
- CPU Usage: 45%
- Memory Usage: 62%
- Database Connections: 127
- Query Response Time: 85ms
- Active Users: 15
- Disk Usage: 38%

---

#### Query 2: All Users
```
List all active users
```

✅ **Expected Result:** Table showing TechCorp users:
- admin@techcorp.com (Admin, IT)
- analyst@techcorp.com (Analyst, Data Analytics)
- dev1@techcorp.com (User, Engineering)
- dev2@techcorp.com (User, Engineering)
- sales@techcorp.com (User, Sales)
- viewer@techcorp.com (Viewer, Marketing)

---

#### Query 3: Error Logs
```
Display error logs from today
```

✅ **Expected Result:** Table showing recent logs:
- Slow query detected: 2.5s execution time
- Database backup completed successfully
- Failed login attempt from IP
- High memory usage detected: 85%
- System health check passed
- Connection timeout to external API

---

### **STEP 3: Test with HealthPlus Admin**

**Logout and Login as HealthPlus Admin:**
```
Email: admin@healthplus.com
Password: admin123
```
*(Note: This account needs to be added to MOCK_USERS if not already there)*

Or test with the existing user but try the queries:

**With user@healthplus.com (blocked):**
```
Show system performance metrics
```
❌ Should be blocked

**Expected behavior:** Only Admin role can access these queries

---

## 🎭 Different Data Per Tenant

### TechCorp Admin Sees:
- **System Metrics:** TechCorp's system performance
- **Users:** TechCorp employees (developers, sales, analysts)
- **Logs:** TechCorp system events

### HealthPlus Admin Would See:
- **System Metrics:** HealthPlus's system performance
- **Users:** Healthcare staff (doctors, nurses, receptionists)
- **Logs:** Healthcare system events (patient records, appointments)

---

## 📊 Complete Admin Query List

### Queries That Return Data for Admin:

```sql
-- System Metrics
Show system performance metrics
System performance
Show system health

-- User Management
List all active users
Show all users
All active users

-- Error Logs
Display error logs from today
Show error logs
System logs

-- Standard Queries (All Roles)
Show me all products
Top customers by sales
How many users are in the system
Average order value
Show monthly revenue trends
```

---

## 🎯 Visual Confirmation

When you run an admin query successfully, you should see:

```
✅ Query Results

🔍 Generated SQL
   SELECT metric_name, current_value, status...

⏱️ Execution Time    📊 Rows Returned    ✅ Status
   155ms               6                   Success

[Data Table with Results]

📈 Data Visualization
[Auto-generated charts if applicable]

📥 Export Data
[CSV] [JSON] [View in New Tab]
```

---

## ❌ Error Handling

If admin queries don't work, check:

1. **Are you logged in as Admin?**
   - Check sidebar shows: "Role: Admin"

2. **Query pattern matching:**
   - "system performance" matches ✅
   - "performance metrics" matches ✅
   - "all users" matches ✅
   - "active users" matches ✅
   - "error log" matches ✅

3. **Permission bypass for Admin:**
   - Admin role bypasses all restrictions
   - Check: `if user_role == "admin": return {"allowed": True}`

---

## 🔍 Debugging Tips

If queries still don't return data:

1. **Check browser console** for JavaScript errors
2. **Check terminal** for Python errors
3. **Verify query pattern** matches the keys in TENANT_DATA
4. **Try exact queries** from this guide
5. **Clear browser cache** and reload

---

## ✨ What Was Fixed

### Added Mock Data For:

**1. System Performance Metrics:**
- CPU, Memory, Database Connections
- Query Response Time, Active Users, Disk Usage
- Different values per tenant

**2. User Management Data:**
- Complete user list with roles and departments
- Active users with last login times
- Tenant-specific employees

**3. Error Logs:**
- Recent system events
- Different error levels (INFO, WARNING, ERROR)
- Tenant-specific log entries

---

## 🎉 Success Criteria

✅ User role → Admin queries BLOCKED with clear error message
✅ Analyst role → Admin queries BLOCKED with clear error message
✅ Admin role → Admin queries WORK and return data tables
✅ Each tenant → Shows their own system metrics
✅ Visualizations → Auto-generate for metric data
✅ Export → CSV/JSON download works

---

## 🚀 Quick 2-Minute Test

```bash
# 1. Start app
python -m streamlit run streamlit_standalone.py --server.port 8504

# 2. Login as User
user@healthplus.com / user123

# 3. Try: "Show system performance metrics"
# Result: ❌ Permission Denied (Good!)

# 4. Logout, Login as Admin
admin@techcorp.com / admin123

# 5. Try: "Show system performance metrics"
# Result: ✅ Data table with 6 metrics (Perfect!)

# 6. Try: "List all active users"
# Result: ✅ Table with 6 users (Excellent!)

# 7. Try: "Display error logs from today"
# Result: ✅ Table with recent logs (Success!)
```

---

**🎉 All admin queries now return data! The RBAC system is fully functional.**
