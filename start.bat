@echo off
REM ============================================================
REM AeroTwin - One-click start (Windows)
REM Run setup.bat once first. This opens two windows: the
REM backend (FastAPI) and the frontend (Vite dev server), then
REM opens the dashboard in your browser.
REM ============================================================

set ROOT=%~dp0

start "AeroTwin Backend" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate.bat && uvicorn main:app --reload"

timeout /t 3 /nobreak >nul

start "AeroTwin Frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

timeout /t 4 /nobreak >nul

start http://localhost:5173/

echo.
echo AeroTwin is starting in two new windows (Backend + Frontend).
echo Closing this window will NOT stop them - close the other two windows to stop the app.
echo.
pause
