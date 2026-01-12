#!/usr/bin/env python3
"""
VirtualFusion Stock Analyzer Pro - iPad Accessible Launcher
This script launches the Streamlit app with network access enabled
so it can be accessed from your iPad on the same network.

TO USE ON IPAD:
1. Run this script on your Mac/PC
2. Note the IP address shown (e.g., http://192.168.1.105:8501)
3. Open Safari on your iPad (same Wi-Fi network)
4. Enter that URL
5. Bookmark it for easy access!
"""

import subprocess
import sys
import socket
import os
from pathlib import Path

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            # Fallback: get hostname IP
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except:
            return "localhost"

def check_dependencies():
    """Check if required packages are installed"""
    missing = []
    try:
        import streamlit
    except ImportError:
        missing.append("streamlit")
    
    try:
        import yfinance
    except ImportError:
        missing.append("yfinance")
    
    try:
        import pandas
    except ImportError:
        missing.append("pandas")
    
    try:
        import plotly
    except ImportError:
        missing.append("plotly")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("\n📦 Installing required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print("✅ Packages installed successfully!\n")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install packages.")
            print("Please run manually: pip3 install -r requirements.txt")
            return False
    
    return True

def main():
    """Launch Streamlit app for iPad access"""
    
    print("\n" + "=" * 70)
    print("📱 VirtualFusion Stock Analyzer Pro - iPad Launcher")
    print("=" * 70 + "\n")
    
    # Check dependencies
    print("🔍 Checking dependencies...", end=" ")
    if not check_dependencies():
        sys.exit(1)
    print("✅ Ready\n")
    
    # Get local IP address
    local_ip = get_local_ip()
    port = 8501
    
    # Get script directory
    script_dir = Path(__file__).parent.absolute()
    main_file = script_dir / "main.py"
    
    if not main_file.exists():
        print(f"❌ Error: Cannot find main.py at {main_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("🚀 LAUNCHING STOCK ANALYZER")
    print("=" * 70)
    print()
    print("📱 TO ACCESS FROM YOUR IPAD:")
    print("   " + "─" * 66)
    print(f"   1. Make sure iPad is on the SAME Wi-Fi network as this computer")
    print(f"   2. Open Safari on your iPad")
    print(f"   3. Enter this URL: http://{local_ip}:{port}")
    print(f"   4. Bookmark it for easy future access!")
    print()
    print("💻 TO ACCESS FROM THIS COMPUTER:")
    print("   " + "─" * 66)
    print(f"   http://localhost:{port}")
    print()
    print("⚠️  IMPORTANT:")
    print("   - Keep this window open while using the app")
    print("   - To stop the server, press Ctrl+C")
    print("   - Make sure your firewall allows connections on port", port)
    print()
    print("=" * 70)
    print()
    
    # Launch Streamlit with network access
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(main_file),
            "--server.port", str(port),
            "--server.address", "0.0.0.0",  # Listen on all interfaces
            "--server.headless", "true",      # Don't auto-open browser
            "--browser.gatherUsageStats", "false",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ], cwd=str(script_dir))
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("👋 Application stopped.")
        print("Thank you for using VirtualFusion Stock Analyzer Pro!")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

