"""
Launcher for Standalone Executable
Opens the Streamlit app and browser automatically
"""

import subprocess
import sys
import webbrowser
import time
import os
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent.absolute()
    
    return os.path.join(base_path, relative_path)

def main():
    """Launch the Streamlit app"""
    
    print("=" * 70)
    print("🚀 VirtualFusion Stock Analyzer Pro")
    print("=" * 70)
    print()
    print("⏳ Starting application...")
    print("   This may take a few seconds...")
    print()
    
    # Get the main.py file path
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        main_file = get_resource_path('main.py')
    else:
        # Running as script
        main_file = Path(__file__).parent / 'main.py'
    
    if not os.path.exists(main_file):
        print(f"❌ Error: Cannot find main.py")
        print(f"   Expected at: {main_file}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(3)  # Wait for server to start
        webbrowser.open('http://localhost:8501')
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(main_file),
            "--server.port", "8501",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("👋 Application stopped.")
        print("Thank you for using VirtualFusion Stock Analyzer Pro!")
        print("=" * 70 + "\n")
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()

