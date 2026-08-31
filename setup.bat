@echo off
REM ============================================================
REM AeroTwin - One-time setup (Windows)
REM Run this ONCE after extracting the project. It creates the
REM backend virtual environment, installs Python dependencies,
REM and installs frontend npm dependencies.
REM ============================================================

echo.
echo === Setting up backend (Python) ===
cd /d "%~dp0backend"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Backend dependency install failed. Is Python installed and on PATH?
    pause
    exit /b 1
)

echo.
echo === Setting up frontend (Node) ===
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 (
    echo.
    echo [ERROR] Frontend dependency install failed. Is Node.js installed and on PATH?
    pause
    exit /b 1
)

echo.
echo === Setup complete! ===
echo Run start.bat any time to launch the app.
echo.
pause
