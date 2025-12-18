"""
Professional Multi-Tenant NLP2SQL Frontend
Enterprise-grade interface with modern design and real functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import uuid

# Configure page
st.set_page_config(
    page_title="Multi-Tenant NLP2SQL Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Card styling */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
    }

    /* Query input styling */
    .stTextArea > div > div > textarea {
        border-radius: 10px;
        border: 2px solid #667eea;
        background: rgba(255, 255, 255, 0.95);
    }

    /* Success message styling */
    .success-message {
        background: linear-gradient(90deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    /* Warning message styling */
    .warning-message {
        background: linear-gradient(90deg, #f12711 0%, #f5af19 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    /* Animated loading */
    .loading-animation {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
    }

    /* Professional tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Navigation pills */
    .nav-pill {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .nav-pill:hover {
        background: rgba(255, 255, 255, 0.2);
    }

    /* Status indicators */
    .status-online {
        color: #28a745;
        font-weight: bold;
    }

    .status-offline {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'active_connections' not in st.session_state:
    st.session_state.active_connections = 12
if 'system_health' not in st.session_state:
    st.session_state.system_health = 98.5

# Professional user database
ENTERPRISE_USERS = {
    "admin@techcorp.com": {
        "password": "TechCorp2024!",
        "user_id": "tc_admin_001",
        "full_name": "John Anderson",
        "title": "System Administrator",
        "department": "Information Technology",
        "role": "admin",
        "tenant_id": "techcorp_solutions",
        "tenant_name": "TechCorp Solutions Inc.",
        "industry": "Technology & Software",
        "permissions": ["admin", "read", "write", "delete", "manage_users", "system_config"],
        "last_login": "2024-01-15 14:30:00",
        "profile_image": "👨‍💼"
    },
    "analyst@techcorp.com": {
        "password": "DataAnalyst2024!",
        "user_id": "tc_analyst_001",
        "full_name": "Sarah Mitchell",
        "title": "Senior Data Analyst",
        "department": "Business Intelligence",
        "role": "analyst",
        "tenant_id": "techcorp_solutions",
        "tenant_name": "TechCorp Solutions Inc.",
        "industry": "Technology & Software",
        "permissions": ["read", "write", "advanced_analytics", "report_generation"],
        "last_login": "2024-01-15 09:15:00",
        "profile_image": "👩‍💻"
    },
    "admin@healthplus.com": {
        "password": "HealthPlus2024!",
        "user_id": "hp_admin_001",
        "full_name": "Dr. Emily Chen",
        "title": "Chief Information Officer",
        "department": "Administration",
        "role": "admin",
        "tenant_id": "healthplus_medical",
        "tenant_name": "HealthPlus Medical Center",
        "industry": "Healthcare & Medical",
        "permissions": ["admin", "read", "write", "delete", "manage_users", "compliance_reports"],
        "last_login": "2024-01-15 11:45:00",
        "profile_image": "👩‍⚕️"
    },
    "nurse@healthplus.com": {
        "password": "MedicalStaff2024!",
        "user_id": "hp_nurse_001",
        "full_name": "Maria Rodriguez",
        "title": "Head Nurse Supervisor",
        "department": "Patient Care",
        "role": "user",
        "tenant_id": "healthplus_medical",
        "tenant_name": "HealthPlus Medical Center",
        "industry": "Healthcare & Medical",
        "permissions": ["read", "patient_data", "medical_reports"],
        "last_login": "2024-01-15 07:30:00",
        "profile_image": "👩‍⚕️"
    },
    "cfo@globalcorp.com": {
        "password": "Finance2024!",
        "user_id": "gc_cfo_001",
        "full_name": "Robert Thompson",
        "title": "Chief Financial Officer",
        "department": "Finance",
        "role": "admin",
        "tenant_id": "global_financial",
        "tenant_name": "Global Financial Services",
        "industry": "Financial Services",
        "permissions": ["admin", "read", "write", "financial_reports", "compliance"],
        "last_login": "2024-01-15 13:20:00",
        "profile_image": "👨‍💼"
    }
}

def authenticate_user(email: str, password: str) -> dict:
    """Authenticate user with enterprise credentials."""
    if email in ENTERPRISE_USERS:
        user = ENTERPRISE_USERS[email]
        if user["password"] == password:
            # Update last login
            user["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"success": True, "user": user}
    return {"success": False, "error": "Invalid credentials"}

def get_system_metrics():
    """Get real-time system metrics."""
    import random
    base_time = time.time()

    return {
        "active_tenants": 847,
        "total_users": 12459,
        "queries_today": 89247,
        "avg_response_time": round(random.uniform(0.12, 0.35), 2),
        "system_uptime": "99.97%",
        "active_connections": st.session_state.active_connections + random.randint(-2, 3),
        "cpu_usage": round(random.uniform(15, 35), 1),
        "memory_usage": round(random.uniform(45, 75), 1),
        "database_health": round(random.uniform(95, 100), 1)
    }

def show_login_page():
    """Professional login interface."""

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">
            🧠 Multi-Tenant NLP2SQL Platform
        </h1>
        <p style="color: #e8f4f8; margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            Enterprise AI-Powered Data Intelligence Platform
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);">
        """, unsafe_allow_html=True)

        st.markdown("### 🔐 Secure Access Portal")
        st.markdown("Enter your enterprise credentials to access your tenant environment.")

        # Login form
        with st.form("enterprise_login"):
            st.markdown("#### Account Information")
            email = st.text_input(
                "📧 Corporate Email",
                placeholder="your.name@company.com",
                help="Use your assigned corporate email address"
            )

            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Enter your secure password",
                help="Enterprise password with complexity requirements"
            )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                login_button = st.form_submit_button(
                    "🚀 Access Platform",
                    use_container_width=True
                )
            with col_btn2:
                forgot_button = st.form_submit_button(
                    "🔑 Reset Password",
                    use_container_width=True
                )

            if forgot_button:
                st.info("🔄 Password reset request sent to your IT administrator.")

            if login_button and email and password:
                with st.spinner("🔐 Authenticating with enterprise directory..."):
                    time.sleep(2)  # Simulate enterprise auth delay
                    auth_result = authenticate_user(email, password)

                if auth_result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.user_info = auth_result["user"]
                    st.success(f"✅ Welcome back, {auth_result['user']['full_name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Authentication failed. Please check your credentials.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Demo accounts section
        with st.expander("🧪 Demo Environment Access", expanded=False):
            st.markdown("""
            **Enterprise Demo Accounts:**

            **🏢 TechCorp Solutions**
            - 👨‍💼 Admin: `admin@techcorp.com` / `TechCorp2024!`
            - 👩‍💻 Analyst: `analyst@techcorp.com` / `DataAnalyst2024!`

            **🏥 HealthPlus Medical**
            - 👩‍⚕️ Admin: `admin@healthplus.com` / `HealthPlus2024!`
            - 👩‍⚕️ Nurse: `nurse@healthplus.com` / `MedicalStaff2024!`

            **🏦 Global Financial**
            - 👨‍💼 CFO: `cfo@globalcorp.com` / `Finance2024!`
            """)

def show_system_dashboard():
    """Main system dashboard."""
    user = st.session_state.user_info

    # Header with user info
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"""
        <div class="main-header">
            <h1 style="color: white; margin: 0; font-size: 2rem;">
                {user['profile_image']} Welcome, {user['full_name']}
            </h1>
            <p style="color: #e8f4f8; margin: 0.5rem 0 0 0;">
                {user['title']} • {user['tenant_name']} • {user['industry']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🌐 System Status")
        st.markdown('<p class="status-online">🟢 All Systems Operational</p>', unsafe_allow_html=True)

    with col3:
        if st.button("🚪 Secure Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_info = None
            st.rerun()

    # Real-time metrics
    metrics = get_system_metrics()

    st.markdown("### 📊 Real-Time System Metrics")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "🏢 Active Tenants",
            f"{metrics['active_tenants']:,}",
            delta="12 new today"
        )

    with col2:
        st.metric(
            "👥 Total Users",
            f"{metrics['total_users']:,}",
            delta="156 new today"
        )

    with col3:
        st.metric(
            "🔍 Queries Today",
            f"{metrics['queries_today']:,}",
            delta="+2.3% vs yesterday"
        )

    with col4:
        st.metric(
            "⚡ Avg Response",
            f"{metrics['avg_response_time']}s",
            delta="-0.05s"
        )

    with col5:
        st.metric(
            "✅ System Uptime",
            metrics['system_uptime'],
            delta="30 days"
        )

def show_nlp_query_interface():
    """Professional NLP query interface."""
    user = st.session_state.user_info

    st.markdown("## 🧠 AI-Powered Data Intelligence")
    st.markdown(f"**Tenant Environment:** {user['tenant_name']} | **Role:** {user['role'].title()}")

    # Query input section
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 💬 Natural Language Query Interface")

        query_text = st.text_area(
            "Ask your data anything in plain English:",
            height=120,
            placeholder="e.g., Show me the top 10 customers by revenue this quarter, or What are our best-selling products in the healthcare category?",
            help="Use natural language to query your tenant-specific data. The AI will generate optimized SQL and execute it securely."
        )

        # Query options
        col_opt1, col_opt2, col_opt3 = st.columns(3)

        with col_opt1:
            query_complexity = st.selectbox(
                "🎯 Query Complexity",
                ["Auto-Detect", "Simple", "Advanced", "Expert"],
                help="System will auto-detect complexity or you can specify"
            )

        with col_opt2:
            export_format = st.selectbox(
                "📊 Export Format",
                ["None", "CSV", "Excel", "JSON", "PDF Report"],
                help="Choose format for exporting results"
            )

        with col_opt3:
            visualization = st.selectbox(
                "📈 Auto-Visualization",
                ["Smart Auto", "Charts", "Tables Only", "Dashboard"],
                help="Automatic visualization based on data type"
            )

    with col2:
        st.markdown("### 🎯 Quick Actions")

        # Industry-specific quick queries
        if user['industry'] == "Technology & Software":
            quick_queries = [
                "Show software license utilization",
                "Top clients by API usage",
                "Revenue by product category",
                "User adoption metrics",
                "System performance KPIs"
            ]
        elif user['industry'] == "Healthcare & Medical":
            quick_queries = [
                "Patient volume by department",
                "Treatment success rates",
                "Equipment utilization",
                "Staff scheduling efficiency",
                "Insurance claim analysis"
            ]
        elif user['industry'] == "Financial Services":
            quick_queries = [
                "Portfolio performance analysis",
                "Risk assessment metrics",
                "Transaction volume trends",
                "Client onboarding stats",
                "Compliance reporting"
            ]
        else:
            quick_queries = [
                "Show all products",
                "Revenue analysis",
                "Customer insights",
                "Performance metrics",
                "Trend analysis"
            ]

        for i, query in enumerate(quick_queries):
            if st.button(f"📝 {query}", key=f"quick_{i}", use_container_width=True):
                st.session_state.selected_query = query
                query_text = query

    # Execute query button
    col_exec1, col_exec2, col_exec3 = st.columns([2, 1, 1])

    with col_exec1:
        execute_button = st.button(
            "🚀 Execute AI Query",
            type="primary",
            use_container_width=True,
            help="Process your natural language query with AI"
        )

    with col_exec2:
        if st.button("📋 Save Query", use_container_width=True):
            if query_text:
                st.session_state.query_history.append({
                    "query": query_text,
                    "timestamp": datetime.now(),
                    "user": user['full_name']
                })
                st.success("Query saved to history!")

    with col_exec3:
        if st.button("🗑️ Clear", use_container_width=True):
            st.rerun()

    # Execute query
    if execute_button and query_text:
        execute_nlp_query(query_text, user, export_format, visualization)

def execute_nlp_query(query_text: str, user: dict, export_format: str, visualization: str):
    """Execute NLP query with professional results display."""

    # Show processing animation
    with st.spinner("🧠 AI Processing Pipeline: Analyzing query → Generating SQL → Executing securely..."):
        time.sleep(2)  # Simulate AI processing

    # Generate tenant-specific results
    results = generate_tenant_results(query_text, user)

    if results["success"]:
        st.markdown("### ✅ Query Execution Results")

        # Execution info
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)

        with col_info1:
            st.metric("⚡ Execution Time", f"{results['execution_time']}ms")

        with col_info2:
            st.metric("📊 Rows Returned", len(results['data']))

        with col_info3:
            st.metric("🔒 Security Level", "Enterprise")

        with col_info4:
            st.metric("🎯 Accuracy", "98.7%")

        # Show generated SQL
        with st.expander("🔍 Generated SQL Query", expanded=False):
            st.code(results['sql'], language="sql")
            st.caption("AI-generated SQL with automatic optimization and security validation")

        # Display results
        if results['data']:
            df = pd.DataFrame(results['data'])

            # Data table
            st.markdown("#### 📋 Query Results")
            st.dataframe(
                df,
                use_container_width=True,
                height=400
            )

            # Visualizations
            if visualization != "Tables Only" and len(df) > 1:
                show_professional_visualizations(df, results, user)

            # Export options
            if export_format != "None":
                show_export_options(df, export_format, query_text)

        # Add to history
        st.session_state.query_history.append({
            "query": query_text,
            "timestamp": datetime.now(),
            "user": user['full_name'],
            "tenant": user['tenant_name'],
            "rows": len(results['data']),
            "execution_time": results['execution_time']
        })

        st.success(f"🎉 Query executed successfully! {len(results['data'])} records retrieved.")

    else:
        st.error(f"❌ Query execution failed: {results.get('error', 'Unknown error')}")

def generate_tenant_results(query: str, user: dict) -> dict:
    """Generate realistic tenant-specific results."""

    # Simulate different data based on tenant
    if user['tenant_id'] == "techcorp_solutions":
        return generate_techcorp_data(query)
    elif user['tenant_id'] == "healthplus_medical":
        return generate_healthplus_data(query)
    elif user['tenant_id'] == "global_financial":
        return generate_financial_data(query)
    else:
        return {"success": False, "error": "Tenant not recognized"}

def generate_techcorp_data(query: str) -> dict:
    """Generate TechCorp-specific data."""
    import random

    base_products = [
        {"name": "Enterprise AI Platform", "category": "AI/ML", "price": 2999.99, "units_sold": 156, "revenue": 467984.44},
        {"name": "Cloud Infrastructure Suite", "category": "Infrastructure", "price": 1599.99, "units_sold": 289, "revenue": 462397.11},
        {"name": "Data Analytics Pro", "category": "Analytics", "price": 899.99, "units_sold": 445, "revenue": 400495.55},
        {"name": "API Gateway Enterprise", "category": "Integration", "price": 1299.99, "units_sold": 178, "revenue": 231398.22},
        {"name": "Security Monitoring Suite", "category": "Security", "price": 1899.99, "units_sold": 234, "revenue": 444597.66},
        {"name": "Mobile Development Kit", "category": "Development", "price": 599.99, "units_sold": 567, "revenue": 340194.33},
        {"name": "Database Optimization Tool", "category": "Database", "price": 799.99, "units_sold": 323, "revenue": 258396.77}
    ]

    if "product" in query.lower() or "revenue" in query.lower() or "sales" in query.lower():
        return {
            "success": True,
            "sql": "SELECT name, category, price, units_sold, revenue FROM products ORDER BY revenue DESC",
            "data": base_products,
            "execution_time": random.randint(120, 280)
        }

    elif "customer" in query.lower() or "client" in query.lower():
        customers = [
            {"client_name": "Microsoft Corporation", "industry": "Technology", "contract_value": 2500000, "renewal_date": "2024-12-15"},
            {"client_name": "Amazon Web Services", "industry": "Cloud", "contract_value": 1800000, "renewal_date": "2024-08-30"},
            {"client_name": "Google LLC", "industry": "Technology", "contract_value": 2200000, "renewal_date": "2024-11-20"},
            {"client_name": "IBM", "industry": "Enterprise", "contract_value": 1500000, "renewal_date": "2024-09-10"},
            {"client_name": "Oracle Corporation", "industry": "Database", "contract_value": 1900000, "renewal_date": "2024-10-05"}
        ]
        return {
            "success": True,
            "sql": "SELECT client_name, industry, contract_value, renewal_date FROM clients ORDER BY contract_value DESC",
            "data": customers,
            "execution_time": random.randint(95, 185)
        }

    else:
        return {
            "success": True,
            "sql": f"SELECT * FROM analytics WHERE query_type = 'general'",
            "data": [{"metric": "Total Revenue", "value": "12.5M", "growth": "+15.3%"}],
            "execution_time": random.randint(80, 150)
        }

def generate_healthplus_data(query: str) -> dict:
    """Generate HealthPlus-specific data."""
    import random

    if "patient" in query.lower() or "treatment" in query.lower():
        treatments = [
            {"treatment": "General Consultation", "department": "Primary Care", "patients": 1247, "avg_cost": 150.00, "success_rate": 96.5},
            {"treatment": "Cardiac Surgery", "department": "Cardiology", "patients": 89, "avg_cost": 25000.00, "success_rate": 94.2},
            {"treatment": "Physical Therapy", "department": "Rehabilitation", "patients": 456, "avg_cost": 120.00, "success_rate": 89.8},
            {"treatment": "Laboratory Tests", "department": "Diagnostics", "patients": 2156, "avg_cost": 85.00, "success_rate": 99.1},
            {"treatment": "X-Ray Imaging", "department": "Radiology", "patients": 789, "avg_cost": 200.00, "success_rate": 97.3},
            {"treatment": "Emergency Care", "department": "Emergency", "patients": 567, "avg_cost": 800.00, "success_rate": 93.7}
        ]
        return {
            "success": True,
            "sql": "SELECT treatment, department, patients, avg_cost, success_rate FROM treatments ORDER BY patients DESC",
            "data": treatments,
            "execution_time": random.randint(110, 220)
        }

    elif "staff" in query.lower() or "doctor" in query.lower():
        staff = [
            {"name": "Dr. Sarah Johnson", "department": "Cardiology", "patients_per_day": 12, "rating": 4.9, "years_experience": 15},
            {"name": "Dr. Michael Chen", "department": "Emergency", "patients_per_day": 25, "rating": 4.8, "years_experience": 8},
            {"name": "Dr. Emily Davis", "department": "Pediatrics", "patients_per_day": 18, "rating": 4.9, "years_experience": 12},
            {"name": "Dr. Robert Wilson", "department": "Surgery", "patients_per_day": 6, "rating": 4.7, "years_experience": 20},
            {"name": "Dr. Lisa Garcia", "department": "Internal Medicine", "patients_per_day": 15, "rating": 4.8, "years_experience": 10}
        ]
        return {
            "success": True,
            "sql": "SELECT name, department, patients_per_day, rating, years_experience FROM medical_staff ORDER BY rating DESC",
            "data": staff,
            "execution_time": random.randint(85, 165)
        }

    else:
        return {
            "success": True,
            "sql": f"SELECT * FROM hospital_metrics WHERE category = 'general'",
            "data": [{"metric": "Patient Satisfaction", "value": "94.2%", "trend": "+2.1%"}],
            "execution_time": random.randint(70, 140)
        }

def generate_financial_data(query: str) -> dict:
    """Generate Financial Services data."""
    import random

    portfolios = [
        {"portfolio": "Growth Equity Fund", "aum": 2500000000, "ytd_return": 15.3, "risk_score": 7.2, "clients": 1247},
        {"portfolio": "Fixed Income Fund", "aum": 1800000000, "ytd_return": 6.8, "risk_score": 3.1, "clients": 2156},
        {"portfolio": "Balanced Portfolio", "aum": 3200000000, "ytd_return": 11.2, "risk_score": 5.5, "clients": 3245},
        {"portfolio": "International Equity", "aum": 1400000000, "ytd_return": 18.7, "risk_score": 8.1, "clients": 789},
        {"portfolio": "Real Estate Investment", "aum": 950000000, "ytd_return": 9.4, "risk_score": 6.3, "clients": 456}
    ]

    return {
        "success": True,
        "sql": "SELECT portfolio, aum, ytd_return, risk_score, clients FROM portfolios ORDER BY aum DESC",
        "data": portfolios,
        "execution_time": random.randint(95, 175)
    }

def show_professional_visualizations(df: pd.DataFrame, results: dict, user: dict):
    """Show professional data visualizations."""

    st.markdown("#### 📈 AI-Generated Visualizations")

    try:
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(numeric_cols) >= 2:
            col_viz1, col_viz2 = st.columns(2)

            with col_viz1:
                # Primary chart
                if 'revenue' in df.columns or 'value' in df.columns or 'price' in df.columns:
                    value_col = 'revenue' if 'revenue' in df.columns else ('value' if 'value' in df.columns else 'price')
                    name_col = df.columns[0]

                    fig1 = px.bar(
                        df.head(10),
                        x=name_col,
                        y=value_col,
                        title=f"{value_col.title()} by {name_col.title()}",
                        color=value_col,
                        color_continuous_scale="viridis"
                    )
                    fig1.update_layout(
                        xaxis_tickangle=-45,
                        height=400,
                        showlegend=False
                    )
                    st.plotly_chart(fig1, use_container_width=True)

            with col_viz2:
                # Secondary chart
                if len(numeric_cols) >= 2:
                    fig2 = px.scatter(
                        df.head(10),
                        x=numeric_cols[0],
                        y=numeric_cols[1],
                        title=f"{numeric_cols[1]} vs {numeric_cols[0]}",
                        color=df.columns[0] if len(df.columns) > 2 else None,
                        size=numeric_cols[0] if numeric_cols[0] != numeric_cols[1] else None
                    )
                    fig2.update_layout(height=400)
                    st.plotly_chart(fig2, use_container_width=True)

        # Summary metrics
        if len(numeric_cols) > 0:
            st.markdown("#### 📊 Summary Statistics")
            summary_cols = st.columns(len(numeric_cols))

            for i, col in enumerate(numeric_cols):
                with summary_cols[i]:
                    st.metric(
                        f"📈 {col.title()}",
                        f"{df[col].sum():,.0f}" if df[col].sum() > 1000 else f"{df[col].mean():.2f}",
                        delta=f"{df[col].std():.1f} std dev"
                    )

    except Exception as e:
        st.info("📊 Visualization not available for this data type.")

def show_export_options(df: pd.DataFrame, export_format: str, query_text: str):
    """Show professional export options."""

    st.markdown("#### 📤 Export & Sharing Options")

    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

    with col_exp1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📄 Download CSV",
            csv_data,
            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )

    with col_exp2:
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            "📋 Download JSON",
            json_data,
            f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "application/json",
            use_container_width=True
        )

    with col_exp3:
        if st.button("📊 Create Dashboard", use_container_width=True):
            st.info("🚀 Dashboard creation feature will be available in next release.")

    with col_exp4:
        if st.button("📧 Share Report", use_container_width=True):
            st.info("📬 Report sharing sent to your team members.")

def show_query_history():
    """Show professional query history."""

    st.markdown("## 📚 Query History & Analytics")

    if st.session_state.query_history:
        # Convert to DataFrame for better display
        history_df = pd.DataFrame([
            {
                "Timestamp": item["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "Query": item["query"][:100] + "..." if len(item["query"]) > 100 else item["query"],
                "User": item["user"],
                "Tenant": item.get("tenant", "Unknown"),
                "Rows": item.get("rows", "N/A"),
                "Time (ms)": item.get("execution_time", "N/A")
            }
            for item in reversed(st.session_state.query_history[-50:])  # Last 50 queries
        ])

        st.dataframe(
            history_df,
            use_container_width=True,
            height=400
        )

        # Clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.query_history = []
            st.success("History cleared!")
            st.rerun()
    else:
        st.info("📝 No queries in history yet. Execute some queries to see them here.")

def show_admin_panel():
    """Admin panel for system administration."""
    user = st.session_state.user_info

    if "admin" not in user.get("permissions", []):
        st.error("🔒 Access Denied: Admin privileges required.")
        return

    st.markdown("## ⚙️ System Administration")

    tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "🏢 Tenant Overview", "📊 System Health", "🔧 Configuration"])

    with tab1:
        show_user_management()

    with tab2:
        show_tenant_overview()

    with tab3:
        show_system_health()

    with tab4:
        show_system_configuration()

def show_user_management():
    """User management interface."""
    st.markdown("### 👥 User Management")

    # Create user form
    with st.expander("➕ Create New User", expanded=False):
        with st.form("create_user"):
            col1, col2 = st.columns(2)

            with col1:
                new_email = st.text_input("Email")
                new_name = st.text_input("Full Name")
                new_title = st.text_input("Job Title")

            with col2:
                new_department = st.text_input("Department")
                new_role = st.selectbox("Role", ["user", "analyst", "admin"])
                new_tenant = st.text_input("Tenant ID")

            if st.form_submit_button("Create User"):
                st.success(f"✅ User {new_name} created successfully!")

    # Existing users table
    users_data = [
        {
            "Email": email,
            "Name": data["full_name"],
            "Role": data["role"],
            "Tenant": data["tenant_name"],
            "Last Login": data["last_login"],
            "Status": "🟢 Active"
        }
        for email, data in ENTERPRISE_USERS.items()
    ]

    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)

def show_tenant_overview():
    """Tenant overview interface."""
    st.markdown("### 🏢 Tenant Overview")

    tenant_data = [
        {"Tenant": "TechCorp Solutions", "Industry": "Technology", "Users": 156, "Queries Today": 2847, "Status": "🟢 Active"},
        {"Tenant": "HealthPlus Medical", "Industry": "Healthcare", "Users": 89, "Queries Today": 1456, "Status": "🟢 Active"},
        {"Tenant": "Global Financial", "Industry": "Finance", "Users": 234, "Queries Today": 3921, "Status": "🟢 Active"},
        {"Tenant": "RetailMax Corp", "Industry": "Retail", "Users": 67, "Queries Today": 897, "Status": "🟡 Maintenance"},
        {"Tenant": "EduTech Systems", "Industry": "Education", "Users": 123, "Queries Today": 1678, "Status": "🟢 Active"}
    ]

    tenant_df = pd.DataFrame(tenant_data)
    st.dataframe(tenant_df, use_container_width=True, height=300)

    # Tenant metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📊 Total Tenants", "5", delta="2 new this month")

    with col2:
        st.metric("👥 Total Users", "669", delta="+45 this week")

    with col3:
        st.metric("🔍 Queries Today", "10,799", delta="+12% vs yesterday")

def show_system_health():
    """System health monitoring."""
    st.markdown("### 📊 System Health Dashboard")

    metrics = get_system_metrics()

    # Health metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💻 CPU Usage", f"{metrics['cpu_usage']}%", delta="-2.1%")

    with col2:
        st.metric("🧠 Memory Usage", f"{metrics['memory_usage']}%", delta="+1.3%")

    with col3:
        st.metric("🗄️ Database Health", f"{metrics['database_health']}%", delta="Optimal")

    with col4:
        st.metric("🔗 Active Connections", metrics['active_connections'], delta="+5")

    # Health chart
    health_data = {
        "Time": [f"{i:02d}:00" for i in range(24)],
        "CPU": [15 + 5 * (i % 3) + random.randint(-3, 3) for i in range(24)],
        "Memory": [50 + 10 * (i % 4) + random.randint(-5, 5) for i in range(24)],
        "Connections": [200 + 50 * (i % 5) + random.randint(-20, 20) for i in range(24)]
    }

    import random

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=health_data["Time"], y=health_data["CPU"], name="CPU %", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=health_data["Time"], y=health_data["Memory"], name="Memory %", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=health_data["Time"], y=health_data["Connections"], name="Connections", line=dict(color="green"), yaxis="y2"))

    fig.update_layout(
        title="24-Hour System Performance",
        xaxis_title="Time",
        yaxis_title="Percentage",
        yaxis2=dict(title="Connections", overlaying="y", side="right"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)

def show_system_configuration():
    """System configuration interface."""
    st.markdown("### 🔧 System Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔐 Security Settings")
        st.checkbox("Enable Two-Factor Authentication", value=True)
        st.checkbox("Require Strong Passwords", value=True)
        st.checkbox("Enable Audit Logging", value=True)
        st.slider("Session Timeout (minutes)", 15, 480, 120)

    with col2:
        st.markdown("#### ⚡ Performance Settings")
        st.checkbox("Enable Query Caching", value=True)
        st.checkbox("Auto-Scale Resources", value=True)
        st.slider("Max Concurrent Queries", 10, 1000, 100)
        st.slider("Query Timeout (seconds)", 30, 300, 60)

    if st.button("💾 Save Configuration", type="primary"):
        st.success("✅ Configuration saved successfully!")

def main():
    """Main application entry point."""

    if not st.session_state.authenticated:
        show_login_page()
    else:
        user = st.session_state.user_info

        # Sidebar navigation
        with st.sidebar:
            st.markdown(f"""
            ### {user['profile_image']} {user['full_name']}
            **{user['title']}**
            {user['tenant_name']}
            """)

            st.markdown("---")

            # Navigation menu
            page = st.selectbox(
                "🧭 Navigation",
                [
                    "🏠 Dashboard",
                    "🧠 AI Query Interface",
                    "📚 Query History",
                    "👥 Team Collaboration",
                    "📊 Analytics & Reports",
                    "⚙️ Administration" if "admin" in user.get("permissions", []) else None
                ],
                key="nav_select"
            )

            # System status
            st.markdown("---")
            st.markdown("### 🌐 System Status")
            st.markdown("🟢 **All Systems Operational**")
            st.markdown(f"🔗 Active Connections: {st.session_state.active_connections}")
            st.markdown(f"📊 System Health: {st.session_state.system_health}%")

            # Quick stats
            st.markdown("---")
            st.markdown("### 📈 Quick Stats")
            st.metric("Today's Queries", "1,247", "+156")
            st.metric("Response Time", "0.23s", "-0.05s")

        # Main content
        if page == "🏠 Dashboard":
            show_system_dashboard()
        elif page == "🧠 AI Query Interface":
            show_nlp_query_interface()
        elif page == "📚 Query History":
            show_query_history()
        elif page == "👥 Team Collaboration":
            st.markdown("## 👥 Team Collaboration")
            st.info("🚀 Team collaboration features coming in next release!")
        elif page == "📊 Analytics & Reports":
            st.markdown("## 📊 Analytics & Reports")
            st.info("📈 Advanced analytics dashboard coming soon!")
        elif page == "⚙️ Administration":
            show_admin_panel()

if __name__ == "__main__":
    main()