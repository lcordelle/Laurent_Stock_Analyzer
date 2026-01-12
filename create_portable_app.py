"""
Create a Portable App Package
Bundles everything needed to run the app on any laptop
"""

import shutil
import sys
from pathlib import Path
import subprocess

def create_portable_package():
    """Create a portable package that can be run on any laptop"""
    
    print("=" * 70)
    print("📦 Creating Portable App Package")
    print("=" * 70)
    print()
    
    project_dir = Path(__file__).parent.absolute()
    package_name = "StockAnalyzer_Portable"
    package_dir = project_dir / package_name
    
    # Create package directory
    if package_dir.exists():
        print(f"⚠️  Removing existing package directory...")
        shutil.rmtree(package_dir)
    
    package_dir.mkdir()
    print(f"📁 Created package directory: {package_dir}")
    print()
    
    # Files and directories to include
    items_to_copy = [
        "main.py",
        "config.py",
        "report_generator.py",
        "requirements.txt",
        "components",
        "pages",
        "utils",
        "launch_analyzer.bat",
        "launch_analyzer.sh",
        "launch_for_ipad.py",
    ]
    
    print("📋 Copying files...")
    for item in items_to_copy:
        src = project_dir / item
        dst = package_dir / item
        
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, dst)
                print(f"   ✅ Copied directory: {item}")
            else:
                shutil.copy2(src, dst)
                print(f"   ✅ Copied file: {item}")
        else:
            print(f"   ⚠️  Skipped (not found): {item}")
    
    # Create README for portable package
    readme_content = """# VirtualFusion Stock Analyzer Pro - Portable Package

## 🚀 Quick Start

### Windows:
1. Double-click `launch_analyzer.bat`
2. App opens in browser automatically

### Mac/Linux:
1. Open Terminal in this folder
2. Run: `chmod +x launch_analyzer.sh && ./launch_analyzer.sh`
3. App opens in browser automatically

### First Time Setup:
If you get errors about missing packages, run:
```bash
pip install -r requirements.txt
```

## 📱 Using on iPad

1. Run the app on your laptop using the launcher
2. Run: `python launch_for_ipad.py`
3. On iPad, open Safari and go to the URL shown
4. Make sure laptop and iPad are on same Wi-Fi network

## 💡 Tips

- Keep the terminal/command window open while using the app
- Press Ctrl+C to stop the server
- All your data and settings are stored locally

Enjoy analyzing stocks! 📈
"""
    
    readme_file = package_dir / "README_PORTABLE.txt"
    readme_file.write_text(readme_content)
    print(f"   ✅ Created README")
    
    print()
    print("=" * 70)
    print("✅ Portable Package Created!")
    print("=" * 70)
    print()
    print(f"📦 Location: {package_dir}")
    print()
    print("📋 Package Contents:")
    print("   - All application files")
    print("   - Launch scripts for Windows/Mac/Linux")
    print("   - iPad launcher")
    print("   - README with instructions")
    print()
    print("🚀 To Use:")
    print("   1. Copy the entire folder to any laptop")
    print("   2. Run the appropriate launcher script")
    print("   3. No installation needed (except Python if not present)")
    print()
    
    # Optionally create a ZIP file
    try:
        zip_name = f"{package_name}.zip"
        zip_path = project_dir / zip_name
        if zip_path.exists():
            zip_path.unlink()
        
        print(f"📦 Creating ZIP archive...")
        shutil.make_archive(str(project_dir / package_name), 'zip', package_dir)
        print(f"   ✅ Created: {zip_path}")
        print()
        print(f"🎉 You can now distribute: {zip_name}")
    except Exception as e:
        print(f"   ⚠️  Could not create ZIP: {e}")
        print("   (Package folder is ready to use as-is)")

if __name__ == "__main__":
    create_portable_package()

