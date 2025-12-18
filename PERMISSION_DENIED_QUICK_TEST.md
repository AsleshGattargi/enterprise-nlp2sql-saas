# 🚀 Quick Test - Permission Denied Messages

## Start the Demo
```powershell
python -m streamlit run streamlit_standalone.py --server.port 8504
```

---

## ⚡ 2-Minute Quick Test

### 1. Login as User
```
Email: user@healthplus.com
Password: user123
```

### 2. Try This Query (Will Be Blocked)
```
Show system performance metrics
```

### 3. See the Error Message
You should see:
- 🚫 **Red Error Box** with title "System Metrics Access Denied"
- Your role (User) and required role (Admin)
- Clear explanation why it's blocked
- 💡 Helpful suggestion
- Expandable section showing what you CAN do

### 4. Try an Allowed Query
```
Show me all products
```
✅ This should work and show HealthPlus medical services

---

## 🎯 More Queries to Test Permission Denied

### Blocked for User/Analyst:
```
List all active users
Display error logs from today
Delete all products
Show system health
```

### Allowed for Everyone:
```
Show me all products
Top customers by sales
How many users are in the system
```

---

## 🔄 Test Different Roles

**User → Analyst → Admin**

1. Login as **User** (`user@healthplus.com`)
   - Try: `List all active users` ❌ Blocked

2. Logout, Login as **Analyst** (`analyst@techcorp.com`)
   - Try: `List all active users` ❌ Still Blocked
   - Try: `Show me all products` ✅ Allowed

3. Logout, Login as **Admin** (`admin@techcorp.com`)
   - Try: `List all active users` ✅ Now Allowed!
   - Try: `Show system performance metrics` ✅ Now Allowed!

---

## ✨ What You'll See

When a query is blocked:
1. **Error Title** - "System Metrics Access Denied"
2. **Error Message** - Clear explanation
3. **Warning Box** with:
   - Query you attempted
   - Your current role
   - Required role
   - Feature type blocked
4. **Info Box** - Helpful suggestion
5. **Expandable Section** - "What can I do with my role?"
   - Shows allowed features
   - Shows restricted features

---

## 🎉 Success!

Your RBAC system now shows **professional, clear, and helpful permission denied messages** instead of generic errors!
