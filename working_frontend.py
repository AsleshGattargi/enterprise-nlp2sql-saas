#!/usr/bin/env python3
"""
Simple working Streamlit frontend that definitely works
"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import io
import xlsxwriter
from openpyxl import Workbook

st.set_page_config(page_title="Working NLP2SQL Demo", layout="wide")

# Simple API base URL
API_BASE_URL = "http://127.0.0.1:8003"

# Initialize session state
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'show_json' not in st.session_state:
    st.session_state.show_json = True
if 'last_result' not in st.session_state:
    st.session_state.last_result = None

def create_download_data(results, query, generated_sql):
    """Create downloadable data in different formats"""
    if not results:
        return None

    # Create DataFrame
    df = pd.DataFrame(results)

    # Create metadata
    metadata = {
        "query": query,
        "generated_sql": generated_sql,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_rows": len(results)
    }

    download_data = {}

    # 1. CSV format
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    download_data['csv'] = csv_buffer.getvalue()

    # 2. JSON format
    json_data = {
        "metadata": metadata,
        "results": results
    }
    download_data['json'] = json.dumps(json_data, indent=2, default=str)

    # 3. Excel format
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Results', index=False)

        # Add metadata sheet
        metadata_df = pd.DataFrame(list(metadata.items()), columns=['Field', 'Value'])
        metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

    download_data['excel'] = excel_buffer.getvalue()

    # 4. HTML format
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NLP2SQL Query Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .metadata {{ background-color: #f0f0f0; padding: 15px; margin-bottom: 20px; border-radius: 5px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #4CAF50; color: white; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>NLP2SQL Query Results</h1>
        <div class="metadata">
            <h3>Query Information</h3>
            <p><strong>Original Query:</strong> {metadata['query']}</p>
            <p><strong>Generated SQL:</strong> <code>{metadata['generated_sql']}</code></p>
            <p><strong>Timestamp:</strong> {metadata['timestamp']}</p>
            <p><strong>Total Rows:</strong> {metadata['total_rows']}</p>
        </div>
        <h3>Results</h3>
        {df.to_html(index=False, escape=False)}
    </body>
    </html>
    """
    download_data['html'] = html_content

    return download_data

def simple_login():
    """Simple login function"""
    st.title("🤖 Simple NLP2SQL Demo")

    with st.form("login_form"):
        email = st.text_input("Email", value="diana.rodriguez0@techcorp.com")
        password = st.text_input("Password", type="password", value="password123")
        submit = st.form_submit_button("Login")

        if submit:
            try:
                response = requests.post(f"{API_BASE_URL}/auth/login", json={
                    "email": email,
                    "password": password
                })

                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.user_info = data["user"]
                    st.session_state.org_info = data["organization"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Login failed!")
            except Exception as e:
                st.error(f"Login error: {e}")

def simple_query_interface():
    """Simple query interface"""
    st.title("💬 Working NLP2SQL Demo")

    # Enhanced user info display
    if st.session_state.user_info:
        # Get full user data from login response
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.get(f"{API_BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()

                # Create columns for better layout
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown("### 👤 User Information")
                    st.write(f"**Name:** {user_data['full_name']}")
                    st.write(f"**Email:** {user_data['email']}")
                    st.write(f"**Role:** {user_data['role'].title()}")
                    st.write(f"**Department:** {user_data.get('department', 'N/A')}")

                with col2:
                    # Get organization info from the login response stored in session
                    if hasattr(st.session_state, 'org_info'):
                        org = st.session_state.org_info
                    else:
                        # Fallback - get org info from user data
                        org = {
                            'org_name': 'Unknown',
                            'database_type': 'Unknown',
                            'industry': 'Unknown'
                        }

                    # Database type icons
                    db_icons = {
                        'sqlite': '📁',
                        'mysql': '🐬',
                        'postgresql': '🐘',
                        'mongodb': '🍃'
                    }

                    db_type = org.get('database_type', 'unknown').lower()
                    icon = db_icons.get(db_type, '🗄️')

                    st.markdown("### 🏢 Organization")
                    st.write(f"**Company:** {org.get('org_name', 'Unknown')}")
                    st.write(f"**Industry:** {org.get('industry', 'Unknown')}")
                    st.write(f"**Database:** {icon} {org.get('database_type', 'Unknown').upper()}")

                with col3:
                    st.markdown("### ⚙️ Actions")
                    if st.button("🚪 Logout", use_container_width=True):
                        st.session_state.token = None
                        st.session_state.user_info = None
                        if hasattr(st.session_state, 'org_info'):
                            delattr(st.session_state, 'org_info')
                        st.rerun()

        except Exception as e:
            st.error(f"Error getting user info: {e}")
            # Fallback to basic info
            st.write(f"**Logged in as:** {st.session_state.user_info['full_name']}")
            st.write(f"**Role:** {st.session_state.user_info['role']}")
            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.user_info = None
                st.rerun()

    st.markdown("---")

    # Query form
    with st.form("query_form"):
        query = st.text_area("Enter your query:", value="show me all products")
        submit = st.form_submit_button("Execute Query")

    # Process query outside the form
    if submit and query:
        try:
            headers = {
                "Authorization": f"Bearer {st.session_state.token}",
                "Content-Type": "application/json"
            }

            st.write("**Making API request...**")

            response = requests.post(
                f"{API_BASE_URL}/query/execute",
                json={"query_text": query},
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                # Store result for downloads
                st.session_state.last_result = {
                    'result': result,
                    'query': query,
                    'timestamp': datetime.now()
                }

                # Control buttons row
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    st.write(f"**Response status:** {response.status_code}")

                with col2:
                    if st.button("🔍 Toggle JSON" if st.session_state.show_json else "📋 Show JSON"):
                        st.session_state.show_json = not st.session_state.show_json
                        st.rerun()

                with col3:
                    json_visible_text = "Hide" if st.session_state.show_json else "Show"
                    st.caption(f"JSON: {json_visible_text}")

                # Show JSON conditionally
                if st.session_state.show_json:
                    st.write("**Raw API Response:**")
                    st.json(result)

                # Display results
                if result.get('status') == 'success' and result.get('results'):
                    st.success(f"✅ Success! Found {len(result['results'])} rows")

                    # Show SQL
                    if result.get('generated_sql'):
                        st.code(result['generated_sql'], language='sql')

                    # Show data
                    df = pd.DataFrame(result['results'])
                    st.dataframe(df, use_container_width=True)

                    # Download section
                    st.markdown("---")
                    st.subheader("📥 Download Results")

                    # Create download data
                    download_data = create_download_data(
                        result['results'],
                        query,
                        result.get('generated_sql', 'N/A')
                    )

                    if download_data:
                        # Download buttons in columns
                        col1, col2, col3, col4 = st.columns(4)

                        with col1:
                            st.download_button(
                                label="📊 CSV",
                                data=download_data['csv'],
                                file_name=f"nlp2sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                help="Download as CSV file"
                            )

                        with col2:
                            st.download_button(
                                label="📋 JSON",
                                data=download_data['json'],
                                file_name=f"nlp2sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                help="Download as JSON file with metadata"
                            )

                        with col3:
                            st.download_button(
                                label="📈 Excel",
                                data=download_data['excel'],
                                file_name=f"nlp2sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                help="Download as Excel file with metadata sheet"
                            )

                        with col4:
                            st.download_button(
                                label="🌐 HTML",
                                data=download_data['html'],
                                file_name=f"nlp2sql_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                                mime="text/html",
                                help="Download as HTML report"
                            )

                elif result.get('status') == 'blocked':
                    st.error(f"🚫 Query blocked: {result.get('message', 'No message')}")

                elif result.get('status') == 'error':
                    st.error(f"❌ Query failed: {result.get('message', 'No message')}")

                else:
                    st.warning(f"Unexpected status: {result.get('status', 'Unknown')}")

            else:
                st.error(f"HTTP Error: {response.status_code}")
                st.text(response.text)

        except Exception as e:
            st.error(f"Request failed: {e}")

def main():
    if st.session_state.token:
        simple_query_interface()
    else:
        simple_login()

if __name__ == "__main__":
    main()