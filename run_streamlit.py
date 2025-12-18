"""
Streamlit App Launcher
Easy way to launch the Streamlit app without PATH issues.
"""

import subprocess
import sys
import os

def launch_streamlit():
    """Launch the Streamlit app."""

    print("Multi-Tenant NLP2SQL Streamlit Launcher")
    print("=" * 50)
    print("Starting Streamlit application...")

    try:
        # Use Python module approach to run Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port=8502"]

        print("Command:", " ".join(cmd))
        print("Opening browser at: http://localhost:8502")
        print("Press Ctrl+C to stop the application")
        print("=" * 50)

        # Run the command
        subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

    except KeyboardInterrupt:
        print("\nStreamlit application stopped by user")
    except Exception as e:
        print(f"Error launching Streamlit: {e}")
        print("Try running directly: python -m streamlit run streamlit_app.py")

if __name__ == "__main__":
    launch_streamlit()