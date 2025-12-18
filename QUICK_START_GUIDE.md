# 🚀 Multi-Tenant NLP2SQL Quick Start Guide

## ✅ **WORKING QUERY EXECUTION METHODS**

### **Method 1: Standalone Streamlit App** ⭐ (RECOMMENDED)
**Perfect for testing and demo - No backend required!**

```powershell
# Launch the standalone app
python -m streamlit run streamlit_standalone.py --server.port=8504

# Or use the launcher
python run_standalone_app.py
```

**Access at:** `http://localhost:8504`

**Demo Accounts:**
- 👤 **TechCorp Admin**: `admin@techcorp.com` / `admin123`
- 📊 **TechCorp Analyst**: `analyst@techcorp.com` / `analyst123`
- 👤 **HealthPlus User**: `user@healthplus.com` / `user123`

**Features:**
- ✅ Full web interface with login
- ✅ Mock data included
- ✅ Visual charts and graphs
- ✅ Query history
- ✅ Export to CSV/JSON
- ✅ Role-based suggestions

---

### **Method 2: Simple Command Line** ⚡ (QUICK TESTING)
**For quick query testing without UI**

```powershell
# Interactive mode
python simple_query.py

# Direct execution
python simple_query.py "Show me all products"
```

**Sample Queries:**
1. "Show me all products"
2. "How many users are in the system?"
3. "List the top customers by orders"
4. "What is the average order value?"
5. "Show me sales data from last month"

---

### **Method 3: Full System with Backend** 🏢 (PRODUCTION)
**For full system testing with real database integration**

**Step 1: Start Backend Server**
```powershell
# Fix imports first
set PYTHONPATH=%cd%
python -m src.main
```

**Step 2: Start Frontend**
```powershell
python -m streamlit run streamlit_app.py
```

**Access at:** `http://localhost:8000` (API) + `http://localhost:8501` (Web)

---

## 🎯 **CURRENT STATUS**

✅ **Standalone App**: Running at `http://localhost:8504`
✅ **Simple CLI**: Ready for testing
⚠️ **Full System**: Requires database setup

## 📋 **DEMO QUERIES TO TRY**

### **Basic Queries**
- "Show me all products"
- "How many users are in the system?"
- "What is the average order value?"

### **Analytics Queries**
- "List the top customers by sales"
- "Show me sales data from last month"
- "Display inventory levels by warehouse"
- "Show monthly revenue trends"

### **Advanced Queries** (Admin/Analyst roles)
- "Show system performance metrics"
- "List all active users"
- "Display error logs from today"

## 🔧 **TROUBLESHOOTING**

### **Issue: Port Already in Use**
```powershell
# Use different port
python -m streamlit run streamlit_standalone.py --server.port=8505
```

### **Issue: Streamlit Command Not Found**
```powershell
# Use Python module approach
python -m streamlit run [app_name]

# Or install streamlit
pip install streamlit
```

### **Issue: Backend Connection Failed**
- Use the **Standalone App** instead (Method 1)
- No backend server required for testing

## 🎨 **APP FEATURES**

### **Login System**
- Demo accounts with different roles
- Role-based query suggestions
- Organization-specific data

### **Query Interface**
- Natural language input
- SQL generation display
- Real-time results
- Query history

### **Data Visualization**
- Automatic chart generation
- Interactive plots
- Export capabilities
- Responsive design

### **Security Features**
- User authentication
- Role-based access
- Query logging
- Session management

## 🌟 **QUICK START (EASIEST METHOD)**

```powershell
# 1. Open PowerShell in project directory
cd "D:\Fundae\Multi Tenant NLP2SQL"

# 2. Launch standalone app
python -m streamlit run streamlit_standalone.py --server.port=8504

# 3. Open browser to http://localhost:8504

# 4. Login with demo account:
#    Email: admin@techcorp.com
#    Password: admin123

# 5. Try sample query: "Show me all products"
```

## 📞 **SUPPORT**

If you encounter issues:

1. **Check the port**: Use different port numbers (8504, 8505, etc.)
2. **Try CLI method**: Use `python simple_query.py` for basic testing
3. **Verify Python**: Ensure Python 3.8+ is installed
4. **Install dependencies**: Run `pip install streamlit pandas plotly`

---

**🎉 Your Multi-Tenant NLP2SQL system is ready to use!**

**Current Status:**
- ✅ Standalone App: http://localhost:8504
- ✅ CLI Tool: Ready
- ✅ Testing Framework: Available
- ✅ Security Dashboard: Available