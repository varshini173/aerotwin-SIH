@echo off
REM Quick diagnostic: is anything listening on port 8000, and if so,
REM is it in hardware mode and receiving data?
echo Checking port 8000...
netstat -ano | findstr ":8000" | findstr "LISTENING"
if errorlevel 1 (
    echo   Nothing is listening on port 8000 — the backend is not running.
    echo   Start it with start_hardware.bat or manually with uvicorn.
    goto :end
)
echo.
echo Checking backend hardware status...
powershell -Command "try { Invoke-RestMethod http://127.0.0.1:8000/api/engine/hardware-status | ConvertTo-Json } catch { Write-Host 'Could not reach backend:' $_.Exception.Message }"
:end
echo.
pause
