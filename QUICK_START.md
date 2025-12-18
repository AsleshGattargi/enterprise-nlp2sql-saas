# 🚀 Quick Start Guide

## Step-by-Step Demo Launch

### Option 1: Windows Batch File (Easiest)
```cmd
# Double-click start_demo.bat
# OR run from command prompt:
start_demo.bat
```

### Option 2: Manual Commands (Recommended)

**Step 1: Install Dependencies**
```bash
pip install fastapi uvicorn streamlit requests pandas plotly
```

**Step 2: Start Backend (Terminal 1)**
```bash
cd "D:\Fundae\Multi Tenant NLP2SQL"
python -m uvicorn src.main:app --reload --port 8000
```

**Step 3: Start Frontend (Terminal 2)**
```bash
cd "D:\Fundae\Multi Tenant NLP2SQL"
streamlit run streamlit_app.py --server.port 8501
```

**Step 4: Open Browser**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

## 🔑 Login Credentials

| Email | Password | Role |
|-------|----------|------|
| john.admin@techcorp.com | password123 | Admin |
| jane.analyst@techcorp.com | password123 | Analyst |
| demo@user.com | password123 | Demo User |

## 💬 Sample Queries

Once logged in, try these queries:
- "Show me all products"
- "How many sales this month?"
- "What's the average product price?"
- "List recent transactions"
- "Show top customers"

## 🎯 What You'll See

1. **Multi-Tenant Login**: Different users see different organizations
2. **HDT Personalization**: UI adapts based on user role (Admin vs Analyst)
3. **Natural Language Processing**: Plain English converts to SQL
4. **Visual Results**: Automatic charts and tables
5. **Security**: Each user only sees their organization's data

## 🔧 Troubleshooting

**Port Already in Use?**
- Backend: Change `--port 8000` to `--port 8001`
- Frontend: Change `--server.port 8501` to `--server.port 8502`

**Dependencies Missing?**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Browser Doesn't Open?**
- Manually navigate to http://localhost:8501

## 🎉 Success!

If you see the login page at http://localhost:8501, you're ready to demo the Multi-Tenant NLP2SQL system!

The system showcases:
- ✅ Multi-tenant authentication
- ✅ Human Digital Twin personalization  
- ✅ Natural language to SQL conversion
- ✅ Professional chat interface
- ✅ Automatic data visualizations
- ✅ Role-based access control