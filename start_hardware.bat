@echo off
REM ============================================================
REM AeroTwin — One-click hardware-mode launcher (Windows)
REM Run this by double-clicking it, from wherever this file lives.
REM It will:
REM   1. Kill anything already stuck on port 8000 (fixes "zombie
REM      backend from a crashed terminal" problems)
REM   2. Set up the backend venv if it doesn't exist yet
REM   3. Start the backend in hardware mode (USE_HARDWARE=1) in
REM      its own window
REM   4. Ask you for your Arduino's COM port and start the serial
REM      bridge in its own window
REM   5. Start the frontend in its own window
REM ============================================================

cd /d "%~dp0"
echo Project root: %cd%
echo.

REM --- Step 1: clear anything already on port 8000 -------------
echo [1/5] Checking for existing processes on port 8000...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo   Found process %%P on port 8000 — stopping it.
    taskkill /PID %%P /F >nul 2>&1
)
echo   Done.
echo.

REM --- Step 2: backend venv -------------------------------------
echo [2/5] Setting up backend virtual environment...
cd backend
if not exist venv (
    echo   Creating venv...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo   Installing/checking dependencies (this may take a minute the first time)...
pip install -q -r requirements.txt
cd ..
echo   Done.
echo.

REM --- Step 3: start backend in its own window ------------------
echo [3/5] Starting backend in hardware mode (new window)...
start "AeroTwin Backend (hardware mode)" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate.bat && set USE_HARDWARE=1 && uvicorn main:app --reload"

echo   Waiting a few seconds for the backend to boot...
timeout /t 5 /nobreak >nul
echo.

REM --- Step 4: ask for COM port and start the bridge -------------
echo [4/5] Starting the serial bridge.
set /p COMPORT="   Enter your Arduino's COM port (check Device Manager, e.g. COM6): "
start "AeroTwin Serial Bridge" cmd /k "cd /d "%~dp0backend\hardware\serial_bridge" && pip install -q -r requirements.txt && python bridge.py --port %COMPORT%"
echo.

REM --- Step 5: start frontend --------------------------------------
echo [5/5] Starting frontend (new window)...
start "AeroTwin Frontend" cmd /k "cd /d "%~dp0frontend" && npm install && npm run dev"

echo.
echo ============================================================
echo All 3 processes are starting in their own windows:
echo   - AeroTwin Backend (hardware mode)
echo   - AeroTwin Serial Bridge
echo   - AeroTwin Frontend
echo.
echo Once the frontend window shows a localhost link, open it in
echo your browser. On the Overview page, the Hardware Status panel
echo should say RECEIVING LIVE DATA within a few seconds.
echo.
echo IMPORTANT: close the Arduino IDE's Serial Monitor before this
echo runs, or the bridge window will fail to open the COM port.
echo ============================================================
pause
