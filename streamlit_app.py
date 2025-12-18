import streamlit as st
import requests
import pandas as pd
import json
import time
from datetime import datetime
import plotly.express as px
from typing import Dict, List, Any, Optional

# Configure Streamlit page
st.set_page_config(
    page_title="Multi-Tenant NLP2SQL Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, authenticated: bool = False) -> Dict:
    """Make API request with error handling"""
    try:
        headers = {"Content-Type": "application/json"}
        
        # Add authentication header if needed
        if authenticated and st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers)
        
        # Handle authentication errors specially for login
        if response.status_code == 401 and endpoint == "/auth/login":
            # Return the error detail from the response for login attempts
            try:
                error_data = response.json()
                return {"error": error_data.get("detail", "Authentication failed")}
            except:
                return {"error": "Authentication failed"}
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        st.write(f"**DEBUG:** Request Exception: {e}")
        st.write(f"**DEBUG:** Exception type: {type(e)}")
        if "401" in str(e) and authenticated:
            st.error("Authentication expired. Please login again.")
            logout_user()
        else:
            st.error(f"API request failed: {str(e)}")
        return {"error": str(e)}

def login_user(email: str, password: str) -> bool:
    """Authenticate user"""
    login_data = {"email": email, "password": password}
    
    with st.spinner("Authenticating..."):
        result = make_api_request("/auth/login", method="POST", data=login_data)
    
    if "error" not in result:
        st.session_state.authenticated = True
        st.session_state.access_token = result["access_token"]
        st.session_state.user_info = result
        
        st.success(f"Welcome, {result['user']['full_name']}!")
        st.rerun()
        return True
    else:
        # Show specific error message from API
        error_msg = result.get("error", "Invalid credentials")
        st.error(f"Login failed: {error_msg}")
        return False

def logout_user():
    """Logout user and clear session"""
    st.session_state.authenticated = False
    st.session_state.access_token = None
    st.session_state.user_info = None
    st.session_state.chat_history = []
    st.rerun()

def execute_query(query_text: str, export_format: str = None) -> Dict:
    """Execute natural language query"""
    query_data = {"query_text": query_text}
    if export_format:
        query_data["export_format"] = export_format

    # Debug authentication
    st.write(f"**DEBUG:** Has token: {st.session_state.access_token is not None}")
    if st.session_state.access_token:
        st.write(f"**DEBUG:** Token starts with: {st.session_state.access_token[:20]}...")

    with st.spinner("Processing your query..."):
        result = make_api_request("/query/execute", method="POST", data=query_data, authenticated=True)

    return result

def render_login_page():
    """Render login page"""
    st.title("🤖 Multi-Tenant NLP2SQL Demo")
    st.markdown("### Welcome to the AI-Powered Database Query System")
    
    # Description
    st.markdown("""
    This demo showcases a multi-tenant NLP-to-SQL system with:
    - **Human Digital Twins (HDT)** for personalized experiences  
    - **Multi-database support** 📁SQLite 🐬MySQL 🐘PostgreSQL 🍃MongoDB
    - **Dialect-aware SQL generation** for each database type
    - **Enterprise security** and complete tenant isolation
    - **Industry-specific data** tailored to each organization
    """)
    
    # Sample credentials
    with st.expander("📋 Sample Login Credentials", expanded=True):
        st.markdown("**5 Organizations - 250 Users Total:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📁 TechCorp (@techcorp.com)** - SQLite")
            st.code("Email: diana.rodriguez0@techcorp.com\nPassword: password123\nRole: Admin (Full Access)")
            st.code("Email: john.smith1@techcorp.com\nPassword: password123\nRole: Manager")
            st.code("Email: alex.davis5@techcorp.com\nPassword: password123\nRole: Analyst")
            
            st.markdown("**🐬 HealthPlus (@healthplus.org)** - MySQL")
            st.code("Email: dr.rodriguez50@healthplus.org\nPassword: password123\nRole: Admin")
            st.code("Email: anna.analyst55@healthplus.org\nPassword: password123\nRole: Analyst")
            
        with col2:
            st.markdown("**🐘 FinanceHub (@financehub.net)** - PostgreSQL")
            st.code("Email: cfo.rodriguez100@financehub.net\nPassword: password123\nRole: Admin")
            
            st.markdown("**🍃 RetailMax (@retailmax.com)** - MongoDB") 
            st.code("Email: ceo.rodriguez150@retailmax.com\nPassword: password123\nRole: Admin")
            
            st.markdown("**🐬 EduLearn (@edulearn.edu)** - MySQL")
            st.code("Email: dean.rodriguez200@edulearn.edu\nPassword: password123\nRole: Admin")
        
        st.info("💡 Each organization has 50 users with different role distributions: 1 Admin, 4 Managers, 10 Analysts, 10 Developers, 25 Viewers")
        
        # Database types info
        st.markdown("### 🗄️ Database Architecture")
        db_info_cols = st.columns(5)
        
        with db_info_cols[0]:
            st.markdown("**📁 SQLite**")
            st.caption("TechCorp")
            st.caption("File-based")
            
        with db_info_cols[1]:
            st.markdown("**🐬 MySQL**")
            st.caption("HealthPlus")
            st.caption("EduLearn")
            
        with db_info_cols[2]:
            st.markdown("**🐘 PostgreSQL**")
            st.caption("FinanceHub") 
            st.caption("Advanced SQL")
            
        with db_info_cols[3]:
            st.markdown("**🍃 MongoDB**")
            st.caption("RetailMax")
            st.caption("Document DB")
            
        with db_info_cols[4]:
            st.markdown("**🔧 Docker**")
            st.caption("All services")
            st.caption("Containerized")
    
    # Login form
    st.markdown("### Login to Your Organization")
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="user@organization.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            login_submitted = st.form_submit_button("🔐 Login", use_container_width=True)
        
        if login_submitted:
            if email and password:
                login_user(email, password)
            else:
                st.error("Please enter both email and password.")

def render_sidebar():
    """Render sidebar with user info"""
    if not st.session_state.authenticated:
        return
    
    with st.sidebar:
        # User info
        st.markdown("### 👤 User Profile")
        user = st.session_state.user_info['user']
        org = st.session_state.user_info['organization']
        
        st.write(f"**Name:** {user['full_name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Role:** {user['role'].title()}")
        st.write(f"**Department:** {user.get('department', 'N/A')}")
        
        st.markdown("### 🏢 Organization")
        st.write(f"**Name:** {org['org_name']}")
        st.write(f"**Industry:** {org.get('industry', 'N/A')}")
        
        # Database type with icon and color
        db_type = org['database_type'].upper()
        db_icons = {
            'SQLITE': '📁',
            'MYSQL': '🐬', 
            'POSTGRESQL': '🐘',
            'MONGODB': '🍃'
        }
        db_colors = {
            'SQLITE': '#4CAF50',
            'MYSQL': '#00758F',
            'POSTGRESQL': '#336791', 
            'MONGODB': '#47A248'
        }
        
        icon = db_icons.get(db_type, '🗄️')
        color = db_colors.get(db_type, '#666666')
        
        st.markdown(f"**Database:** {icon} <span style='color:{color}; font-weight:bold;'>{db_type}</span>", 
                   unsafe_allow_html=True)
        
        # HDT Info
        if st.session_state.user_info.get('hdt'):
            st.markdown("### 🤖 Digital Twin")
            hdt = st.session_state.user_info['hdt']
            st.write(f"**Profile:** {hdt['name'].replace('_', ' ').title()}")
            st.write(f"**Skills:** {', '.join(hdt.get('skillset', []))}")
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()

def render_query_interface():
    """Render main query interface"""
    st.title("💬 AI Database Assistant")
    st.markdown("Ask questions about your data in plain English!")
    
    # Add AI engine status indicator in sidebar
    with st.sidebar:
        st.markdown("### 🤖 AI Engine Status")
        try:
            # Check AI engine status from backend
            health_result = make_api_request("/health")
            if "services" in health_result:
                st.success("🟢 NLP Engine: Active")
                st.info("🦙 **Powered by**: Ollama (Local AI)")
            else:
                st.info("🔵 NLP Engine: Local Mode")
        except:
            st.warning("🟡 NLP Engine: Checking...")
    
    # Get suggestions
    suggestions_result = make_api_request("/query/suggestions", authenticated=True)
    suggestions = suggestions_result.get("suggestions", [])
    
    if suggestions:
        st.markdown("### 💡 Suggested Queries")
        cols = st.columns(min(3, len(suggestions)))
        
        for i, suggestion in enumerate(suggestions[:6]):
            with cols[i % 3]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    # Execute the suggested query
                    result = execute_query(suggestion)
                    if result.get('status') == 'success':
                        st.session_state.chat_history.append({
                            "timestamp": datetime.now(),
                            "query": suggestion,
                            "result": result
                        })
                        display_query_results(result, suggestion)
                    else:
                        st.error(f"Query failed: {result.get('message', 'Unknown error')}")
    
    # Query input
    st.markdown("### 🔍 Ask Your Question")
    
    with st.form("query_form", clear_on_submit=True):
        query_text = st.text_area(
            "What would you like to know?",
            height=100,
            placeholder="e.g., Show me all products, How many sales this month?, What's the average price?"
        )
        
        # Export options
        col1, col2 = st.columns([3, 1])
        with col1:
            query_submitted = st.form_submit_button("🚀 Execute Query", use_container_width=True)
        with col2:
            export_format = st.selectbox("Export as:", ["None", "CSV", "Excel", "JSON"])
    
    # Execute query
    if query_submitted and query_text:
        export_fmt = export_format.lower() if export_format != "None" else None
        result = execute_query(query_text, export_fmt)

        # Debug: Show what we received
        st.write("**DEBUG INFO:**")
        st.write(f"- Status: `{result.get('status')}`")
        st.write(f"- Result keys: `{list(result.keys())}`")
        st.write(f"- Type: `{type(result)}`")

        # Check for successful execution based on status field
        if result.get('status') == 'success':
            # Add to chat history
            st.session_state.chat_history.append({
                "timestamp": datetime.now(),
                "query": query_text,
                "result": result
            })

            # Display results
            display_query_results(result, query_text)

            # Show export link if available
            if result.get('export_url'):
                st.success(f"✅ Data exported! [Download {export_format} file]({API_BASE_URL}{result['export_url']})")

        elif result.get('status') == 'blocked':
            st.error(f"🚫 Query blocked: {result.get('message', 'Security restrictions applied')}")
            st.warning("⚠️ Query was blocked for security reasons. Please try a simpler query or contact your administrator.")

        elif result.get('status') == 'error':
            st.error(f"❌ Query failed: {result.get('message', 'Unknown error')}")

        elif "error" in result:
            st.error(f"Query failed: {result.get('detail', result.get('error', 'Unknown error'))}")

            # Show helpful suggestions for blocked queries
            if "blocked" in result.get('error', '').lower():
                st.warning("⚠️ Query was blocked for security reasons. Please try a simpler query or contact your administrator.")
        else:
            st.warning(f"Unexpected result format: {result}")

def display_query_results(result: Dict, original_query: str):
    """Display query results with visualizations"""
    st.markdown("### 📊 Query Results")
    
    # Query info
    with st.expander("🔍 Query Details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Original Query:** {original_query}")
            st.write(f"**Status:** {result['status'].title()}")
            st.write(f"**Execution Time:** {result['execution_time_ms']}ms")
        
        with col2:
            if result.get('generated_sql'):
                st.code(result['generated_sql'], language='sql')
    
    # Results data
    if result['results']:
        df = pd.DataFrame(result['results'])
        
        st.markdown(f"**Found {len(df)} records:**")
        
        # Display data table
        st.dataframe(df, use_container_width=True)
        
        # Auto-generate visualizations for numeric data
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        
        if len(numeric_columns) > 0 and len(df) > 1:
            st.markdown("### 📈 Data Visualization")
            
            viz_type = st.selectbox("Choose visualization:", ["Bar Chart", "Line Chart", "Pie Chart"])
            
            if viz_type == "Bar Chart" and len(df.columns) >= 2:
                x_col = st.selectbox("X-axis:", df.columns.tolist())
                y_col = st.selectbox("Y-axis:", numeric_columns)
                
                if x_col and y_col:
                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                    st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("No data found for your query.")
    
    st.markdown("---")

def render_chat_history():
    """Render chat history"""
    if st.session_state.chat_history:
        st.markdown("### 📚 Query History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history[-5:])):
            with st.expander(f"🕐 {chat['timestamp'].strftime('%H:%M:%S')} - {chat['query'][:50]}...", expanded=False):
                st.write(f"**Query:** {chat['query']}")
                st.write(f"**Status:** {chat['result']['status']}")
                st.write(f"**Results:** {len(chat['result']['results'])} rows")
                
                if chat['result'].get('generated_sql'):
                    st.code(chat['result']['generated_sql'], language='sql')

def main():
    """Main application"""
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_sidebar()
        
        # Main content tabs
        tab1, tab2 = st.tabs(["💬 Query Assistant", "📊 Analytics"])
        
        with tab1:
            render_query_interface()
            render_chat_history()
        
        with tab2:
            render_analytics_dashboard()

def render_analytics_dashboard():
    """Render analytics dashboard"""
    st.markdown("### 📈 Analytics Dashboard")
    
    # Check if user is authenticated
    if not st.session_state.get('authenticated', False) or not st.session_state.get('user_info'):
        st.warning("Please log in to view analytics dashboard.")
        return
    
    # Admin-only features
    user_role = st.session_state.user_info['user']['role']
    if user_role in ['admin', 'manager']:
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Queries Today", "23", "+5")
        with col2:
            st.metric("Avg Response Time", "156ms", "-12ms")
        with col3:
            st.metric("Success Rate", "98.5%", "+1.2%")
        with col4:
            st.metric("Active Users", "12", "+2")
        
        # Query logs for admins
        if user_role == 'admin':
            st.markdown("### 📋 Recent Query Logs")
            
            # Fetch query logs
            logs_result = make_api_request("/admin/query-logs?limit=20", authenticated=True)
            
            if "error" not in logs_result and logs_result.get('logs'):
                logs_df = pd.DataFrame(logs_result['logs'])
                
                # Display in a nice format
                st.dataframe(
                    logs_df[['timestamp', 'username', 'query_text', 'execution_status', 'execution_time_ms']]
                    .rename(columns={
                        'timestamp': 'Time',
                        'username': 'User',
                        'query_text': 'Query',
                        'execution_status': 'Status',
                        'execution_time_ms': 'Time (ms)'
                    }),
                    use_container_width=True
                )
                
                # Status distribution chart
                if len(logs_df) > 0:
                    st.markdown("### 📊 Query Status Distribution")
                    status_counts = logs_df['execution_status'].value_counts()
                    try:
                        fig = px.pie(values=status_counts.values, names=status_counts.index, 
                                   title="Query Execution Status")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Chart rendering error: {str(e)}")
                        # Fallback to simple bar chart
                        fig = px.bar(x=status_counts.index, y=status_counts.values,
                                   title="Query Execution Status")
                        st.plotly_chart(fig, use_container_width=True)
            
            # Organization users management
            st.markdown("### 👥 Organization Users")
            users_result = make_api_request("/admin/users", authenticated=True)
            
            if "error" not in users_result and users_result.get('users'):
                users_df = pd.DataFrame(users_result['users'])
                
                # Role distribution
                role_counts = users_df['role'].value_counts()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Role Distribution")
                    fig = px.bar(x=role_counts.index, y=role_counts.values, 
                               title="Users by Role")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("#### Department Distribution")
                    dept_counts = users_df['department'].value_counts()
                    try:
                        fig = px.pie(values=dept_counts.values, names=dept_counts.index, 
                                   title="Users by Department")
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Chart rendering error: {str(e)}")
                        # Fallback to bar chart
                        fig = px.bar(x=dept_counts.index, y=dept_counts.values,
                                   title="Users by Department")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Users table
                st.dataframe(
                    users_df[['username', 'email', 'full_name', 'department', 'role', 'is_active']]
                    .rename(columns={
                        'username': 'Username',
                        'email': 'Email',
                        'full_name': 'Full Name',
                        'department': 'Department',
                        'role': 'Role',
                        'is_active': 'Active'
                    }),
                    use_container_width=True
                )
    
    else:
        # Limited analytics for non-admin users
        st.info("📊 Personal Analytics")
        
        # User's own query history analytics
        if st.session_state.chat_history:
            user_queries = len(st.session_state.chat_history)
            successful_queries = sum(1 for q in st.session_state.chat_history 
                                   if q['result']['status'] == 'success')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Your Queries Today", str(user_queries))
            with col2:
                success_rate = (successful_queries / user_queries * 100) if user_queries > 0 else 0
                st.metric("Your Success Rate", f"{success_rate:.1f}%")
        
        else:
            st.info("No query history available yet. Try running some queries!")

if __name__ == "__main__":
    main()
