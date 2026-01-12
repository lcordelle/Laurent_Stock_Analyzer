# 🚀 Quick Build Guide - Create Single Executable

## For Laptops (Windows/Mac/Linux)

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build Executable
```bash
python build_executable.py
```

### Step 3: Find Your Executable
- **Windows**: `dist/StockAnalyzer.exe`
- **Mac**: `dist/StockAnalyzer.app`
- **Linux**: `dist/StockAnalyzer`

**That's it!** Copy the executable to any laptop (same OS) and double-click to run.

---

## For iPad

iPad **cannot** run executables. Use this instead:

### Option 1: Run on Laptop, Access from iPad (Easiest)

1. **On your laptop**, run the app (executable or Python)
2. **Run iPad launcher:**
   ```bash
   python launch_for_ipad.py
   ```
3. **On iPad**, open Safari and go to the URL shown
4. **Make sure** laptop and iPad are on same Wi-Fi

### Option 2: Deploy to Cloud (Best for iPad)

Deploy to **Streamlit Cloud** (free):
1. Go to https://streamlit.io/cloud
2. Connect your GitHub repo
3. Deploy the app
4. Access from iPad via browser with the cloud URL

---

## File Size

The executable will be **100-300 MB** - this is normal because it includes:
- Python interpreter
- All libraries (Streamlit, Plotly, Pandas, etc.)
- All your code

---

## Troubleshooting

**Build fails?**
- Make sure PyInstaller is installed: `pip install pyinstaller`
- Make sure all dependencies are installed: `pip install -r requirements.txt`

**App won't start?**
- Try building with `--console` instead of `--windowed` to see errors
- Check that all files are included in the build

**Need help?**
- See `BUILD_INSTRUCTIONS.md` for detailed guide

