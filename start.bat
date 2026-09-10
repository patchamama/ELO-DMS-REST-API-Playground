@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "APIPORT=8010"
set "NODEPORT=8787"

rem --- enable the auto version-bump git hook (idempotent) ------------
where git >nul 2>nul && git -C "%ROOT%" rev-parse --git-dir >nul 2>nul && git -C "%ROOT%" config core.hooksPath .githooks

rem --- portable toolchains + Python dependencies -------------------------
rem They are installed below runtime/ only.  This never changes global PATH.
echo [playground] Checking portable toolchains and Python dependencies ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\bootstrap-toolchains.ps1"
if errorlevel 1 (
    echo [playground] Portable bootstrap failed. See the error above.
    pause
    exit /b 1
)
set "PY=%ROOT%\runtime\python-venv\Scripts\python.exe"
set "PATH=%ROOT%\runtime\toolchains\go\bin;%ROOT%\runtime\toolchains\php;%ROOT%\runtime\toolchains\jdk\bin;%PATH%"

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

rem --- free the API port if something is already on it -------------------
call :free_port %APIPORT%
call :free_port %NODEPORT%

echo [playground] Starting Node runner   -> http://127.0.0.1:%NODEPORT%
start "playground-node" cmd /k "cd /d "%ROOT%" && node backend-node\src\server.mjs"

timeout /t 2 /nobreak >nul

echo [playground] Starting FastAPI app   -> http://127.0.0.1:%APIPORT%
start "playground-api" cmd /k "cd /d "%ROOT%\backend-python" && "%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port %APIPORT%"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:%APIPORT%"

endlocal
exit /b 0

rem ====================================================================
rem :free_port <port>  - if a process is LISTENING on <port>, kill it so
rem this launch can take the port over. Uses Get-NetTCPConnection so it is
rem independent of the (localized) netstat state column.
:free_port
set "_PORT=%~1"
for /f "usebackq tokens=*" %%P in (`powershell -NoProfile -Command "(Get-NetTCPConnection -LocalPort %_PORT% -State Listen -ErrorAction SilentlyContinue).OwningProcess | Select-Object -Unique"`) do (
    if not "%%P"=="" if not "%%P"=="0" (
        echo [playground] port %_PORT% is in use by PID %%P - stopping it...
        taskkill /F /PID %%P >nul 2>&1
    )
)
timeout /t 1 /nobreak >nul
goto :eof
