#!/usr/bin/env python3
"""
Local startup script that forces SQLite mode
"""
import os
import sys

# Force SQLite mode by clearing MySQL environment variables
os.environ['MYSQL_HOST'] = ''
os.environ['MYSQL_USER'] = ''
os.environ['MYSQL_PASSWORD'] = ''
os.environ['MYSQL_DATABASE'] = ''
os.environ['MYSQL_PORT'] = ''

print("Starting Multi-Tenant NLP2SQL System in LOCAL MODE")
print("Using SQLite databases for all organizations")
print("Backend API: http://127.0.0.1:8001")
print("Streamlit UI: http://127.0.0.1:8501")
print("")

# Start the backend server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app", 
        host="127.0.0.1", 
        port=8003, 
        reload=True,
        log_level="info"
    )