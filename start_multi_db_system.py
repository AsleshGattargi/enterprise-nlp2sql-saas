#!/usr/bin/env python3
"""
Multi-Database NLP2SQL System Startup Script

This script helps you start the multi-tenant NLP2SQL system with support for different
database types per organization.

Usage:
    python start_multi_db_system.py [mode]
    
Modes:
    - docker: Start the full Docker-based system with all databases
    - local: Start with local development setup (SQLite fallback)
    - check: Check database connections and system health
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiDBSystemManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes: List[subprocess.Popen] = []
        
    def check_requirements(self) -> bool:
        """Check if all requirements are met"""
        logger.info("Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8 or higher is required")
            return False
            
        # Check if required directories exist
        required_dirs = ['src', 'database', 'databases']
        for dir_name in required_dirs:
            if dir_name == 'databases':
                # Create databases directory if it doesn't exist
                os.makedirs(self.project_root / dir_name, exist_ok=True)
            elif not (self.project_root / dir_name).exists():
                logger.error(f"Required directory '{dir_name}' not found")
                return False
                
        # Check if Docker is available (for docker mode)
        try:
            subprocess.run(['docker', '--version'], 
                          capture_output=True, check=True)
            logger.info("✓ Docker is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("⚠ Docker not available - will use local mode")
            
        # Check if docker-compose is available
        try:
            subprocess.run(['docker-compose', '--version'], 
                          capture_output=True, check=True)
            logger.info("✓ Docker Compose is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                subprocess.run(['docker', 'compose', 'version'], 
                              capture_output=True, check=True)
                logger.info("✓ Docker Compose (v2) is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("⚠ Docker Compose not available")
        
        logger.info("✓ System requirements check completed")
        return True
        
    def setup_environment(self):
        """Setup environment variables and configuration"""
        logger.info("Setting up environment...")
        
        # Check if .env file exists
        env_file = self.project_root / '.env'
        env_example = self.project_root / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            logger.info("Creating .env file from .env.example...")
            import shutil
            shutil.copy(env_example, env_file)
            logger.warning("⚠ Please update the .env file with your actual database credentials")
            
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
            logger.info("✓ Environment variables loaded")
        except ImportError:
            logger.warning("⚠ python-dotenv not available - using system environment")
            
    def start_docker_mode(self):
        """Start the system using Docker containers"""
        logger.info("Starting Multi-DB System in Docker mode...")
        
        try:
            # Check if docker-compose.yml exists
            compose_file = self.project_root / 'docker-compose.yml'
            if not compose_file.exists():
                logger.error("docker-compose.yml not found!")
                return False
                
            # Start Docker services
            logger.info("Starting Docker services...")
            result = subprocess.run([
                'docker-compose', 'up', '-d', '--build'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try docker compose (v2 syntax)
                result = subprocess.run([
                    'docker', 'compose', 'up', '-d', '--build'
                ], cwd=self.project_root, capture_output=True, text=True)
                
            if result.returncode != 0:
                logger.error(f"Failed to start Docker services: {result.stderr}")
                return False
                
            logger.info("✓ Docker services started successfully")
            
            # Wait for services to be ready
            self.wait_for_services()
            
            # Show service URLs
            self.show_service_urls(docker_mode=True)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting Docker mode: {e}")
            return False
            
    def start_local_mode(self):
        """Start the system in local development mode"""
        logger.info("Starting Multi-DB System in Local mode...")
        
        try:
            # Install dependencies
            logger.info("Installing Python dependencies...")
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
            ], cwd=self.project_root, check=True)
            
            # Start FastAPI backend
            logger.info("Starting FastAPI backend...")
            fastapi_process = subprocess.Popen([
                sys.executable, 'run_system.py'
            ], cwd=self.project_root)
            self.processes.append(fastapi_process)
            
            # Wait a moment for FastAPI to start
            time.sleep(3)
            
            # Start Streamlit frontend
            logger.info("Starting Streamlit frontend...")
            streamlit_process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', 'streamlit_app.py',
                '--server.port', '8501', '--server.address', '0.0.0.0'
            ], cwd=self.project_root)
            self.processes.append(streamlit_process)
            
            logger.info("✓ Local services started successfully")
            
            # Show service URLs
            self.show_service_urls(docker_mode=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting local mode: {e}")
            self.cleanup_processes()
            return False
            
    def wait_for_services(self):
        """Wait for services to be ready"""
        logger.info("Waiting for services to be ready...")
        
        services = [
            ("FastAPI", "http://localhost:8001/health"),
            ("Streamlit", "http://localhost:8501")
        ]
        
        import requests
        
        for service_name, url in services:
            for attempt in range(30):
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        logger.info(f"✓ {service_name} is ready")
                        break
                except requests.RequestException:
                    if attempt < 29:
                        time.sleep(2)
                    else:
                        logger.warning(f"⚠ {service_name} may not be ready")
                        
    def show_service_urls(self, docker_mode: bool = False):
        """Display service URLs"""
        logger.info("\n" + "="*60)
        logger.info("🚀 MULTI-TENANT NLP2SQL SYSTEM IS READY!")
        logger.info("="*60)
        
        logger.info("\n📱 APPLICATION SERVICES:")
        logger.info("• Streamlit Frontend: http://localhost:8501")
        logger.info("• FastAPI Backend: http://localhost:8001")
        logger.info("• API Documentation: http://localhost:8001/docs")
        
        if docker_mode:
            logger.info("\n🗄️ DATABASE ADMIN TOOLS:")
            logger.info("• phpMyAdmin (HealthPlus MySQL): http://localhost:8080")
            logger.info("• pgAdmin (FinanceHub PostgreSQL): http://localhost:8081")
            logger.info("• Mongo Express (RetailMax MongoDB): http://localhost:8082")
            
            logger.info("\n🔧 DATABASE CONNECTIONS:")
            logger.info("• HealthPlus MySQL: localhost:3307")
            logger.info("• FinanceHub PostgreSQL: localhost:5433")
            logger.info("• RetailMax MongoDB: localhost:27018")
            logger.info("• EduLearn MySQL: localhost:3308")
            logger.info("• TechCorp SQLite: databases/techcorp_db.sqlite")
        else:
            logger.info("\n🗄️ DATABASE INFO:")
            logger.info("• Running in LOCAL mode - using SQLite fallbacks")
            logger.info("• TechCorp SQLite: databases/techcorp_db.sqlite")
            logger.info("• Demo data available for all organizations")
            
        logger.info("\n👤 SAMPLE LOGIN CREDENTIALS:")
        logger.info("• TechCorp Admin: diana.rodriguez0@techcorp.com / password123")
        logger.info("• HealthPlus Admin: dr.rodriguez50@healthplus.org / password123")
        logger.info("• More credentials available in the Streamlit login page")
        
        logger.info("\n" + "="*60)
        
    def check_system_health(self):
        """Check system health and database connections"""
        logger.info("🏥 Checking system health...")
        
        try:
            # Import database manager
            sys.path.append(str(self.project_root / 'src'))
            from database import db_manager
            from sqlalchemy import text
            
            # Test organizations and their databases
            test_orgs = [
                ('org-001', 'sqlite', 'techcorp_db'),
                ('org-002', 'mysql', 'healthplus_db'),
                ('org-003', 'postgresql', 'financehub_db'),
                ('org-004', 'mongodb', 'retailmax_db'),
                ('org-005', 'mysql', 'edulearn_db')
            ]
            
            logger.info("\n📊 DATABASE CONNECTION TESTS:")
            for org_id, db_type, db_name in test_orgs:
                try:
                    success = db_manager.test_connection(org_id, db_type, db_name)
                    status = "✓" if success else "✗"
                    logger.info(f"{status} {org_id} ({db_type}): {'Connected' if success else 'Failed'}")
                except Exception as e:
                    logger.info(f"✗ {org_id} ({db_type}): {str(e)[:50]}...")
                    
            # Test metadata database
            try:
                with db_manager.get_metadata_db() as db:
                    db.execute(text("SELECT 1"))
                logger.info("✓ Metadata database: Connected")
            except Exception as e:
                logger.info(f"✗ Metadata database: {str(e)[:50]}...")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            
    def cleanup_processes(self):
        """Clean up running processes"""
        logger.info("Cleaning up processes...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.warning(f"Error cleaning up process: {e}")
                
    def stop_docker_services(self):
        """Stop Docker services"""
        logger.info("Stopping Docker services...")
        try:
            result = subprocess.run([
                'docker-compose', 'down'
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                # Try docker compose (v2 syntax)
                subprocess.run([
                    'docker', 'compose', 'down'
                ], cwd=self.project_root, capture_output=True, text=True)
                
            logger.info("✓ Docker services stopped")
        except Exception as e:
            logger.error(f"Error stopping Docker services: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("\nReceived shutdown signal. Cleaning up...")
        self.cleanup_processes()
        self.stop_docker_services()
        sys.exit(0)
        
def main():
    manager = MultiDBSystemManager()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else 'local'
    
    if mode not in ['docker', 'local', 'check']:
        print(f"Unknown mode: {mode}")
        print("Usage: python start_multi_db_system.py [docker|local|check]")
        sys.exit(1)
        
    # Check requirements
    if not manager.check_requirements():
        sys.exit(1)
        
    # Setup environment
    manager.setup_environment()
    
    if mode == 'check':
        manager.check_system_health()
    elif mode == 'docker':
        if manager.start_docker_mode():
            try:
                logger.info("\nSystem running. Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    elif mode == 'local':
        if manager.start_local_mode():
            try:
                logger.info("\nSystem running. Press Ctrl+C to stop.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
if __name__ == '__main__':
    main()