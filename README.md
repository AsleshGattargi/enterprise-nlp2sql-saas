# Multi-Tenant NLP2SQL Demo

A comprehensive AI-powered database query system that converts natural language to SQL with multi-tenant isolation and Human Digital Twins.

## 🚀 Quick Start

### Option 1: One-Click Demo
```bash
python run_demo.py
```

### Option 2: Manual Start
```bash
# Install dependencies
pip install fastapi uvicorn streamlit requests pandas plotly

# Start backend (Terminal 1)
python -m uvicorn src.main:app --reload --port 8000

# Start frontend (Terminal 2)
streamlit run streamlit_app.py --server.port 8501
```

## 🌟 Features

- **Natural Language to SQL**: Convert plain English to database queries
- **Multi-Tenant Architecture**: Complete data isolation between organizations
- **Human Digital Twins**: Personalized AI experience based on user roles
- **Professional UI**: Interactive chat interface with visualizations
- **Security Features**: SQL injection prevention and access controls

## 🔑 Demo Accounts

| Email | Password | Role | Organization |
|-------|----------|------|-------------|
| john.admin@techcorp.com | password123 | Admin | TechCorp |
| jane.analyst@techcorp.com | password123 | Analyst | TechCorp |
| demo@user.com | password123 | Demo | Demo Org |

## 💬 Sample Queries

Try these natural language queries:
- "Show me all products"
- "How many sales this month?"
- "What's the average product price?"
- "List recent transactions"
- "Show top customers"

## 🏗️ Architecture

```
User Query → Authentication → HDT Profile → NLP2SQL → Security → Results
```

### Components:
- **FastAPI Backend** (`src/main.py`) - REST API with demo data
- **Streamlit Frontend** (`streamlit_app.py`) - Interactive chat interface
- **Multi-Tenant Auth** - Organization detection from email domains
- **HDT System** - Role-based personalization

## 🔒 Security Features

- **Tenant Isolation**: Users only see their organization's data
- **SQL Injection Prevention**: Pattern-based query validation
- **Role-Based Access**: Different permissions by user role
- **Audit Logging**: Complete query history tracking

## 📊 Demo Data

The system includes sample data for:
- **Products**: Electronics, accessories with pricing
- **Sales**: Transaction history with customers
- **Analytics**: Performance metrics and trends

## 🤖 Human Digital Twins

Each user gets a personalized HDT profile:
- **Researcher Analyst**: Advanced analytics capabilities
- **Business Manager**: Reporting and dashboards
- **Demo User**: Basic query interface

## 🛠️ Development

### Project Structure
```
Multi-Tenant-NLP2SQL/
├── src/
│   ├── main.py          # FastAPI backend
│   └── __init__.py      # Package init
├── streamlit_app.py     # Frontend interface
├── run_demo.py          # Demo launcher
├── requirements.txt     # Dependencies
├── .env                 # Configuration
└── README.md           # Documentation
```

### API Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `POST /auth/login` - User authentication
- `POST /query/execute` - Execute NL query
- `GET /query/suggestions` - Get query suggestions

## 🎯 What Makes This Special

1. **Multi-Tenant by Design**: Complete isolation between organizations
2. **HDT Personalization**: AI adapts to user roles and preferences
3. **Natural Interface**: Ask questions in plain English
4. **Visual Results**: Automatic chart generation from query results
5. **Enterprise Ready**: Security and audit features built-in

## 🔧 Troubleshooting

**Port Issues**: If ports 8000 or 8501 are in use, modify the startup commands
**Dependencies**: Run `pip install -r requirements.txt` if modules are missing
**Browser**: Manually open http://localhost:8501 if auto-open fails

## 📈 Next Steps

This demo showcases the core concepts. Production implementation would include:
- Real database connections (MySQL, PostgreSQL, MongoDB)
- Advanced NLP models for better query understanding
- RAG integration for domain-specific knowledge
- Comprehensive security controls
- Performance monitoring and optimization

## 🤝 Contributing

This is a demonstration system. For production use:
1. Implement proper database connections
2. Add comprehensive error handling
3. Set up monitoring and alerting
4. Conduct security audits
5. Add comprehensive test coverage

## 📝 License

MIT License - See LICENSE file for details

---

**Ready to try it?** Run `python run_demo.py` and open http://localhost:8501!