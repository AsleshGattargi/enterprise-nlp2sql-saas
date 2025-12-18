#!/usr/bin/env python3
"""
Docker container startup script for Multi-Tenant NLP2SQL system
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def wait_for_databases():
    """Wait for all database containers to be ready"""
    logger.info("Waiting for database containers to be ready...")
    
    # Wait a bit for databases to fully initialize
    time.sleep(10)
    
    # Check if we can connect to databases
    databases = [
        ("HEALTHPLUS_DB_HOST", "HEALTHPLUS_DB_PORT", "MySQL - HealthPlus"),
        ("FINANCEHUB_DB_HOST", "FINANCEHUB_DB_PORT", "PostgreSQL - FinanceHub"),
        ("RETAILMAX_DB_HOST", "RETAILMAX_DB_PORT", "MongoDB - RetailMax"),
        ("EDULEARN_DB_HOST", "EDULEARN_DB_PORT", "MySQL - EduLearn")
    ]
    
    for host_env, port_env, name in databases:
        host = os.getenv(host_env, "localhost")
        port = os.getenv(port_env, "3306")
        logger.info(f"Database {name}: {host}:{port}")
    
    logger.info("Database wait complete")

def start_fastapi():
    """Start FastAPI backend"""
    logger.info("Starting FastAPI backend...")
    
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8001"))
    
    cmd = [
        "uvicorn", 
        "src.main:app", 
        "--host", host, 
        "--port", str(port),
        "--reload"
    ]
    
    return subprocess.Popen(cmd)

def start_streamlit():
    """Start Streamlit frontend"""
    logger.info("Starting Streamlit frontend...")
    
    host = os.getenv("STREAMLIT_HOST", "0.0.0.0")
    port = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    cmd = [
        "streamlit", 
        "run", 
        "streamlit_app.py",
        "--server.address", host,
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    return subprocess.Popen(cmd)

def main():
    """Main startup function"""
    logger.info("Starting Multi-Tenant NLP2SQL system in Docker...")
    
    # Wait for databases
    wait_for_databases()
    
    # Start FastAPI
    fastapi_process = start_fastapi()
    
    # Give FastAPI time to start
    time.sleep(5)
    
    # Start Streamlit
    streamlit_process = start_streamlit()
    
    logger.info("Both services started successfully!")
    logger.info("FastAPI: http://localhost:8001")
    logger.info("Streamlit: http://localhost:8501")
    
    try:
        # Keep the container running
        while True:
            # Check if processes are still running
            if fastapi_process.poll() is not None:
                logger.error("FastAPI process died, restarting...")
                fastapi_process = start_fastapi()
            
            if streamlit_process.poll() is not None:
                logger.error("Streamlit process died, restarting...")
                streamlit_process = start_streamlit()
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        logger.info("Shutting down services...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()