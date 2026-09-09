@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "APIPORT=8010"
set "NODEPORT=8787"

rem --- enable the auto version-bump git hook (idempotent) ------------
where git >nul 2>nul && git -C "%ROOT%" rev-parse --git-dir >nul 2>nul && git -C "%ROOT%" config core.hooksPath .githooks

rem --- locate a Python interpreter (absolute path) -----------------------
set "PY="
if exist "%ROOT%\.venv\Scripts\python.exe" set "PY=%ROOT%\.venv\Scripts\python.exe"
if not defined PY if exist "%ROOT%\..\.venv\Scripts\python.exe" set "PY=%ROOT%\..\.venv\Scripts\python.exe"
if not defined PY (
    echo.
    echo [playground] No virtual environment found. One-time setup:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r backend-python\requirements-dev.txt
    echo.
    pause
    exit /b 1
)

rem --- Node dependencies -----------------------------------------------
where node >nul 2>nul || ( echo [playground] Node.js not found on PATH. & pause & exit /b 1 )
if not exist "%ROOT%\node_modules\elo-playground" (
    echo [playground] Installing Node dependencies ^(npm install^) ...
    call npm install --no-audit --no-fund || ( echo [playground] npm install failed & pause & exit /b 1 )
)

rem --- .env ---------------------------------------------------------
if not exist "%ROOT%\.env" if exist "%ROOT%\env.sample" (
    copy /y "%ROOT%\env.sample" "%ROOT%\.env" >nul
    echo [playground] Created .env from env.sample - review it if needed.
)

rem --- if the API port is busy, don't spawn a doomed second server -------
netstat -ano | findstr /r /c:"LISTENING" | findstr /c:":%APIPORT% " >nul 2>&1
if not errorlevel 1 (
    set "PGRUNNING="
    for /f "delims=" %%R in ('curl -s -m 2 "http://127.0.0.1:%APIPORT%/health" 2^>nul ^| findstr /c:"backend-python"') do set "PGRUNNING=1"
    if defined PGRUNNING (
        echo [playground] Already running on port %APIPORT% - opening the browser.
        start "" "http://127.0.0.1:%APIPORT%"
        endlocal
        exit /b 0
    )
    echo.
    echo [playground] ERROR: port %APIPORT% is in use by another program.
    echo             Close it, or set ELOPG_PORT in .env to a free port, then re-run.
    echo.
    pause
    exit /b 1
)

echo [playground] Starting Node runner   -> http://127.0.0.1:%NODEPORT%
start "playground-node" cmd /k "cd /d "%ROOT%" && node backend-node\src\server.mjs"

timeout /t 2 /nobreak >nul

echo [playground] Starting FastAPI app   -> http://127.0.0.1:%APIPORT%
start "playground-api" cmd /k "cd /d "%ROOT%\backend-python" && "%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port %APIPORT%"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%APIPORT%"

endlocal
