"""
Standalone App Launcher
Launch the standalone Streamlit app that works without backend dependencies.
"""

import subprocess
import sys
import os
import webbrowser
import time

def launch_standalone_app():
    """Launch the standalone Streamlit app."""

    print("🤖 Multi-Tenant NLP2SQL Standalone App Launcher")
    print("=" * 60)
    print("Starting standalone application...")
    print("This app includes mock data and works without backend servers.")
    print("=" * 60)

    try:
        # Use Python module approach to run Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            "streamlit_standalone.py",
            "--server.port=8504",
            "--server.headless=true"
        ]

        print("Command:", " ".join(cmd))
        print("App will open at: http://localhost:8504")
        print("Press Ctrl+C to stop the application")
        print("=" * 60)

        # Start the process
        process = subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))

        # Wait a moment then open browser
        time.sleep(3)
        print("Opening browser...")
        webbrowser.open("http://localhost:8504")

        # Wait for process to complete
        process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        try:
            process.terminate()
        except:
            pass
    except Exception as e:
        print(f"❌ Error launching app: {e}")
        print("\n💡 Try running manually:")
        print("python -m streamlit run streamlit_standalone.py --server.port=8504")

if __name__ == "__main__":
    launch_standalone_app()