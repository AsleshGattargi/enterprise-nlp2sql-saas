"""
Dashboard Runner Script
Launches the security validation dashboard using Streamlit.
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_streamlit_installation():
    """Check if Streamlit is installed."""
    try:
        import streamlit
        logger.info(f"Streamlit version: {streamlit.__version__}")
        return True
    except ImportError:
        logger.error("Streamlit is not installed. Please install it with: pip install streamlit")
        return False


def run_dashboard():
    """Run the security validation dashboard."""
    if not check_streamlit_installation():
        return False

    dashboard_path = Path(__file__).parent / "security_validation_dashboard.py"

    if not dashboard_path.exists():
        logger.error(f"Dashboard file not found: {dashboard_path}")
        return False

    try:
        logger.info("Starting Multi-Tenant NLP2SQL Security Validation Dashboard...")
        logger.info(f"Dashboard will be available at: http://localhost:8501")
        logger.info("Press Ctrl+C to stop the dashboard")

        # Run Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port=8501"]
        subprocess.run(cmd, check=True)

    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start dashboard: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🔒 Multi-Tenant NLP2SQL Security Validation Dashboard")
    print("=" * 60)
    print("Starting security validation dashboard...")
    print("The dashboard will open in your web browser automatically.")
    print("If it doesn't open, navigate to: http://localhost:8501")
    print("=" * 60)

    success = run_dashboard()
    if not success:
        print("Failed to start dashboard. Please check the error messages above.")
        sys.exit(1)