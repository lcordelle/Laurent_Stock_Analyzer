@echo off
REM VirtualFusion Stock Analyzer Pro - Windows Launch Script

echo ==========================================
echo VirtualFusion Stock Analyzer Pro
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [OK] Python is installed

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip not found
    echo Please install pip
    pause
    exit /b 1
)

echo [OK] pip is installed

REM Check if packages are installed
python -c "import streamlit, yfinance, pandas, plotly" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Some packages missing
    echo Installing required packages...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Package installation failed
        echo Please run: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [OK] Packages installed successfully
) else (
    echo [OK] All packages installed
)

echo.
echo ==========================================
echo Launching Stock Analyzer...
echo ==========================================
echo.
echo The application will open in your default browser
echo URL: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

REM Launch Streamlit app
streamlit run main.py

echo.
echo Application closed. Thank you for using VirtualFusion Stock Analyzer Pro!
pause
