"""
Live Demo Launcher
Quick launcher for the multi-tenant demonstration.
"""

import webbrowser
import time
import os

def launch_live_demo():
    """Launch the live demonstration."""

    print("🎯 MULTI-TENANT NLP2SQL LIVE DEMO LAUNCHER")
    print("=" * 60)
    print("Setting up your live demonstration...")
    print()

    # Display demo information
    print("📋 DEMO COMPONENTS READY:")
    print("✅ Interactive Visual Demo: http://localhost:8505")
    print("✅ Full System Demo: http://localhost:8504")
    print("✅ Command Line Demo: python demo_simple.py")
    print()

    print("🎤 PRESENTATION READY!")
    print("=" * 60)
    print("1. Interactive Demo - Perfect for presentations")
    print("   URL: http://localhost:8505")
    print("   Features: Step-by-step visual demonstration")
    print()
    print("2. Full System Demo - Complete application")
    print("   URL: http://localhost:8504")
    print("   Login: admin@techcorp.com / admin123")
    print("   Login: user@healthplus.com / user123")
    print()
    print("3. Command Line Demo - Quick proof")
    print("   Command: python demo_simple.py")
    print("   Shows: Database creation and query results")
    print()

    print("🎯 DEMO SCRIPT HIGHLIGHTS:")
    print("- Onboarding process explanation")
    print("- Database replication with different datasets")
    print("- Same query returning different results")
    print("- RBAC implementation")
    print("- Tenant isolation verification")
    print()

    # Ask which demo to open
    print("Which demo would you like to open?")
    print("1. Interactive Visual Demo (Recommended for presentations)")
    print("2. Full System Demo")
    print("3. Both")
    print("4. Command Line Demo")

    choice = input("\nEnter your choice (1-4): ").strip()

    if choice == "1" or choice == "3":
        print("\n🚀 Opening Interactive Demo...")
        webbrowser.open("http://localhost:8505")

    if choice == "2" or choice == "3":
        print("\n🚀 Opening Full System Demo...")
        webbrowser.open("http://localhost:8504")

    if choice == "4":
        print("\n🚀 Running Command Line Demo...")
        os.system("python demo_simple.py")

    if choice in ["1", "2", "3"]:
        print("\n🎉 Demo launched successfully!")
        print("\nPRESENTATION TIPS:")
        print("- Start with the onboarding process")
        print("- Show database replication concept")
        print("- Execute the same query on both tenants")
        print("- Highlight the different results")
        print("- Emphasize complete tenant isolation")
        print("\n📖 Full presentation script: LIVE_DEMO_SCRIPT.md")

if __name__ == "__main__":
    launch_live_demo()