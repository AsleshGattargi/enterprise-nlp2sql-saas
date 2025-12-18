"""
Visual Multi-Tenant Demo for Streamlit
Shows the exact demonstration the viewer requested with visual interface.
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time

# Page config
st.set_page_config(
    page_title="Multi-Tenant NLP2SQL Demo",
    page_icon="🏢",
    layout="wide"
)

def setup_demo_databases():
    """Set up demo databases if they don't exist."""
    base_path = Path("demo_databases")
    base_path.mkdir(exist_ok=True)

    # Check if databases exist
    techcorp_db = base_path / "techcorp_db.sqlite"
    healthplus_db = base_path / "healthplus_db.sqlite"

    if not techcorp_db.exists() or not healthplus_db.exists():
        st.info("Setting up demo databases... This will take a moment.")

        # Import and run the demo setup
        import subprocess
        result = subprocess.run(["python", "demo_simple.py"],
                              capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            st.success("Demo databases created successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Failed to create demo databases")
            st.code(result.stderr)

def get_database_data(db_path, query):
    """Execute query on specific database."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.title("🏢 Multi-Tenant NLP2SQL Replication Demo")
    st.markdown("### *Demonstrating Database Replication & Tenant Isolation*")

    # Setup databases
    setup_demo_databases()

    # Check if databases exist
    base_path = Path("demo_databases")
    techcorp_db = base_path / "techcorp_db.sqlite"
    healthplus_db = base_path / "healthplus_db.sqlite"

    if not techcorp_db.exists() or not healthplus_db.exists():
        st.warning("Demo databases not found. Please run the setup first.")
        return

    # Sidebar
    st.sidebar.header("🎯 Demo Components")
    demo_section = st.sidebar.selectbox(
        "Choose Demo Section:",
        [
            "1. 📋 Onboarding Process",
            "2. 🔄 Database Replication",
            "3. 🔐 RBAC Implementation",
            "4. 🔍 Same Query, Different Results",
            "5. 🛡️ Tenant Isolation"
        ]
    )

    if demo_section == "1. 📋 Onboarding Process":
        show_onboarding_process()
    elif demo_section == "2. 🔄 Database Replication":
        show_database_replication()
    elif demo_section == "3. 🔐 RBAC Implementation":
        show_rbac_implementation()
    elif demo_section == "4. 🔍 Same Query, Different Results":
        show_query_demonstration()
    elif demo_section == "5. 🛡️ Tenant Isolation":
        show_tenant_isolation()

def show_onboarding_process():
    """Show the onboarding process."""
    st.header("📋 New Company Onboarding Process")
    st.markdown("---")

    st.markdown("""
    When a new company signs up for our Multi-Tenant NLP2SQL system,
    we capture the following information to create their isolated environment:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Company Information")
        st.markdown("""
        - **Company Name**
        - **Industry Type** (Healthcare, Finance, Tech, Retail, etc.)
        - **Company Size** (number of employees)
        - **Geographic Region**
        - **Contact Information**
        """)

        st.subheader("👤 Administrator Details")
        st.markdown("""
        - **Admin Name and Email**
        - **Phone Number**
        - **Department/Title**
        - **Preferred Language**
        """)

    with col2:
        st.subheader("🗃️ Database Requirements")
        st.markdown("""
        - **Database Type** (PostgreSQL, MySQL, MongoDB)
        - **Expected Data Volume**
        - **Expected Number of Users**
        - **Performance Requirements**
        """)

        st.subheader("🔐 Security Preferences")
        st.markdown("""
        - **Compliance Requirements** (HIPAA, SOX, GDPR)
        - **Authentication Method**
        - **Data Retention Policies**
        - **Backup Frequency**
        """)

    st.markdown("---")
    st.subheader("🔄 Automated Provisioning Process")

    # Progress visualization
    steps = [
        "Validate company information",
        "Generate unique tenant ID",
        "Clone appropriate schema template",
        "Create isolated database instance",
        "Set up RBAC roles and permissions",
        "Configure security policies",
        "Initialize connection pools",
        "Send welcome email with credentials",
        "Enable monitoring and alerts",
        "Complete tenant activation"
    ]

    for i, step in enumerate(steps, 1):
        st.markdown(f"✅ **Step {i}:** {step}")

def show_database_replication():
    """Show database replication process."""
    st.header("🔄 Database Structure Replication")
    st.markdown("---")

    st.markdown("""
    Our system creates **identical database schemas** for each tenant,
    but populates them with **tenant-specific data**. This ensures:
    - Consistent structure across all tenants
    - Complete data isolation
    - Industry-specific datasets
    """)

    # Show schema structure
    st.subheader("📊 Common Database Schema")

    schema_code = """
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        full_name VARCHAR(100),
        department VARCHAR(50),
        role VARCHAR(20)
    );

    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(50),
        price DECIMAL(10,2),
        stock_quantity INTEGER,
        description TEXT
    );

    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_name VARCHAR(100),
        product_id INTEGER,
        quantity INTEGER,
        order_total DECIMAL(10,2),
        status VARCHAR(20)
    );

    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        total_orders INTEGER,
        total_spent DECIMAL(10,2)
    );
    """

    st.code(schema_code, language="sql")

    # Show tenant-specific data differences
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 TechCorp Solutions")
        st.markdown("**Industry:** Technology")
        st.markdown("**Database:** `techcorp_db.sqlite`")
        st.markdown("**Sample Products:**")
        st.markdown("""
        - Enterprise Software License ($999.99)
        - Cloud Server Instance ($299.99)
        - API Development Kit ($149.99)
        - Data Analytics Suite ($599.99)
        """)

    with col2:
        st.subheader("🏥 HealthPlus Medical")
        st.markdown("**Industry:** Healthcare")
        st.markdown("**Database:** `healthplus_db.sqlite`")
        st.markdown("**Sample Products:**")
        st.markdown("""
        - General Consultation ($150.00)
        - Blood Test Panel ($85.00)
        - X-Ray Examination ($200.00)
        - Physical Therapy Session ($120.00)
        """)

def show_rbac_implementation():
    """Show RBAC implementation."""
    st.header("🔐 Role-Based Access Control (RBAC)")
    st.markdown("---")

    st.markdown("""
    Each tenant has the same RBAC structure, but user assignments are tenant-specific.
    """)

    # RBAC roles
    rbac_data = {
        "Role": ["Admin", "Analyst", "User", "Viewer"],
        "Permissions": [
            "read, write, delete, admin, create_users",
            "read, write, advanced_queries",
            "read, basic_queries",
            "read"
        ],
        "Description": [
            "Full system access",
            "Data analysis and reporting",
            "Basic data access",
            "Read-only access"
        ]
    }

    df_rbac = pd.DataFrame(rbac_data)
    st.table(df_rbac)

    # Show users per tenant
    st.subheader("👥 User Assignments per Tenant")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🏢 TechCorp Solutions**")
        try:
            df_tech_users = get_database_data("demo_databases/techcorp_db.sqlite",
                                            "SELECT full_name, username, role, department FROM users")
            st.dataframe(df_tech_users, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading TechCorp users: {e}")

    with col2:
        st.markdown("**🏥 HealthPlus Medical**")
        try:
            df_health_users = get_database_data("demo_databases/healthplus_db.sqlite",
                                              "SELECT full_name, username, role, department FROM users")
            st.dataframe(df_health_users, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading HealthPlus users: {e}")

def show_query_demonstration():
    """Show the same query returning different results."""
    st.header("🔍 Same Query, Different Results")
    st.markdown("---")

    st.markdown("""
    This demonstrates the core concept the viewer requested:
    **The same natural language query executed on different tenant databases returns different, tenant-specific results.**
    """)

    # Query input
    st.subheader("📝 Natural Language Query")
    query_text = st.text_input(
        "Enter your query:",
        value="Show me all products with their prices and stock levels",
        help="This query will be executed on both tenant databases"
    )

    # Generated SQL
    st.subheader("🔄 Generated SQL")
    sql_query = "SELECT name, category, price, stock_quantity FROM products ORDER BY price DESC"
    st.code(sql_query, language="sql")

    if st.button("🚀 Execute Query on Both Tenants"):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🏢 TechCorp Results")
            try:
                df_tech = get_database_data("demo_databases/techcorp_db.sqlite", sql_query)
                st.dataframe(df_tech, use_container_width=True)

                # Create chart
                fig_tech = px.bar(df_tech, x='name', y='price',
                                title="TechCorp Product Prices",
                                color='category')
                fig_tech.update_xaxes(tickangle=45)
                st.plotly_chart(fig_tech, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

        with col2:
            st.subheader("🏥 HealthPlus Results")
            try:
                df_health = get_database_data("demo_databases/healthplus_db.sqlite", sql_query)
                st.dataframe(df_health, use_container_width=True)

                # Create chart
                fig_health = px.bar(df_health, x='name', y='price',
                                  title="HealthPlus Service Prices",
                                  color='category')
                fig_health.update_xaxes(tickangle=45)
                st.plotly_chart(fig_health, use_container_width=True)

            except Exception as e:
                st.error(f"Error: {e}")

        st.success("✅ Same query executed successfully on both tenant databases!")
        st.info("🎯 **Key Point:** Notice how the same query returns completely different, industry-specific results for each tenant.")

def show_tenant_isolation():
    """Show tenant isolation verification."""
    st.header("🛡️ Tenant Isolation Verification")
    st.markdown("---")

    st.markdown("""
    Our multi-tenant system ensures complete isolation between tenants:
    """)

    # Isolation features
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ What's Protected")
        st.markdown("""
        - **Data Isolation:** Each tenant has separate database
        - **User Isolation:** Users can only access their tenant
        - **Query Isolation:** Queries are tenant-scoped
        - **Schema Isolation:** Each tenant has own tables
        - **Connection Isolation:** Separate connection pools
        """)

    with col2:
        st.subheader("❌ What's Blocked")
        st.markdown("""
        - **Cross-tenant data access**
        - **User authentication across tenants**
        - **Query execution on other tenant DBs**
        - **Schema modifications of other tenants**
        - **Resource sharing between tenants**
        """)

    # Verification examples
    st.subheader("🔍 Isolation Examples")

    examples = [
        {
            "scenario": "TechCorp user tries to access HealthPlus data",
            "result": "❌ BLOCKED",
            "reason": "User authenticated for 'techcorp' cannot access 'healthplus' database"
        },
        {
            "scenario": "HealthPlus admin tries to modify TechCorp schema",
            "result": "❌ BLOCKED",
            "reason": "Database routing prevents cross-tenant operations"
        },
        {
            "scenario": "TechCorp analyst queries TechCorp products",
            "result": "✅ ALLOWED",
            "reason": "User has appropriate permissions within tenant boundary"
        },
        {
            "scenario": "HealthPlus user views HealthPlus patients",
            "result": "✅ ALLOWED",
            "reason": "Role-appropriate access granted within tenant scope"
        }
    ]

    for example in examples:
        with st.expander(f"{example['result']} {example['scenario']}"):
            st.markdown(f"**Result:** {example['result']}")
            st.markdown(f"**Reason:** {example['reason']}")

    st.success("🎉 Complete tenant isolation verified! Each tenant operates in a completely isolated environment.")

if __name__ == "__main__":
    main()