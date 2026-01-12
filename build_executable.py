"""
Build Script for Creating Standalone Executable
Creates a single .exe (Windows) or .app (Mac) file
"""

import PyInstaller.__main__
import os
import sys
from pathlib import Path

def build_executable():
    """Build standalone executable using PyInstaller"""
    
    print("=" * 70)
    print("🔨 Building Standalone Executable")
    print("=" * 70)
    print()
    
    # Get the project directory
    project_dir = Path(__file__).parent.absolute()
    main_file = project_dir / "main.py"
    
    if not main_file.exists():
        print(f"❌ Error: Cannot find main.py at {main_file}")
        sys.exit(1)
    
    print(f"📁 Project directory: {project_dir}")
    print(f"📄 Main file: {main_file}")
    print()
    
    # Use launcher.py as the main entry point
    launcher_file = project_dir / "launcher.py"
    
    # PyInstaller arguments
    args = [
        str(launcher_file),
        '--name=StockAnalyzer',
        '--onefile',  # Create a single executable file
        '--console',  # Show console for debugging (change to --windowed to hide)
        '--add-data=main.py:.',  # Include main.py
        '--add-data=components:components',  # Include components directory
        '--add-data=pages:pages',  # Include pages directory
        '--add-data=utils:utils',  # Include utils directory
        '--add-data=config.py:.',  # Include config
        '--add-data=report_generator.py:.',  # Include report generator
        '--hidden-import=streamlit',
        '--hidden-import=yfinance',
        '--hidden-import=pandas',
        '--hidden-import=numpy',
        '--hidden-import=plotly',
        '--hidden-import=plotly.graph_objects',
        '--hidden-import=plotly.express',
        '--hidden-import=openpyxl',
        '--hidden-import=xlsxwriter',
        '--hidden-import=reportlab',
        '--hidden-import=PIL',
        '--hidden-import=scipy',
        '--hidden-import=matplotlib',
        '--hidden-import=seaborn',
        '--collect-all=streamlit',
        '--collect-all=plotly',
        '--noconfirm',  # Overwrite output directory without asking
    ]
    
    # Platform-specific adjustments
    if sys.platform == 'win32':
        print("🪟 Building for Windows...")
        args.append('--icon=NONE')  # You can add an .ico file here if you have one
    elif sys.platform == 'darwin':
        print("🍎 Building for macOS...")
        args.append('--icon=NONE')  # You can add an .icns file here if you have one
    else:
        print("🐧 Building for Linux...")
    
    print()
    print("⏳ This may take several minutes...")
    print()
    
    try:
        PyInstaller.__main__.run(args)
        print()
        print("=" * 70)
        print("✅ Build Complete!")
        print("=" * 70)
        print()
        
        if sys.platform == 'win32':
            exe_path = project_dir / "dist" / "StockAnalyzer.exe"
            print(f"📦 Executable created at: {exe_path}")
        elif sys.platform == 'darwin':
            app_path = project_dir / "dist" / "StockAnalyzer.app"
            print(f"📦 Application created at: {app_path}")
            print()
            print("💡 To create a .dmg file for distribution:")
            print("   Use Disk Utility or create-dmg tool")
        else:
            exe_path = project_dir / "dist" / "StockAnalyzer"
            print(f"📦 Executable created at: {exe_path}")
        
        print()
        print("🚀 You can now distribute this file to other computers!")
        print("   No Python installation required on the target machine.")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Build Failed!")
        print("=" * 70)
        print(f"Error: {str(e)}")
        print()
        print("💡 Make sure PyInstaller is installed:")
        print("   pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()

