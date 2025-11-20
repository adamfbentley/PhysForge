@echo off
echo ========================================
echo PhysForge - Simplified Full Stack
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Activating Python environment...
call C:\Users\adamf\anaconda3\Scripts\activate.bat C:\Users\adamf\anaconda3
if errorlevel 1 (
    echo ERROR: Failed to activate conda environment
    pause
    exit /b 1
)

echo.
echo [2/3] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Starting PhysForge...
echo.
echo ========================================
echo Server will start at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo ========================================
echo.

set KMP_DUPLICATE_LIB_OK=TRUE
python app.py

pause
