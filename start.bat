@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "APIPORT=8010"
set "NODEPORT=8787"

rem --- enable the auto version-bump git hook (idempotent) ------------
where git >nul 2>nul && git -C "%ROOT%" rev-parse --git-dir >nul 2>nul && git -C "%ROOT%" config core.hooksPath .githooks

rem --- Python and Node.js -------------------------------------------------
rem Fetches a portable Python and/or Node.js into runtime\toolchains when no
rem working system installation is found. Optional Go, PHP and Java are
rem installed only when enabled in the app's Settings dialog. Nothing here
rem changes the global machine PATH.
echo [playground] Checking Python and Node.js dependencies ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\bootstrap-toolchains.ps1"
if errorlevel 1 (
    echo [playground] Python/Node.js bootstrap failed. See the error above.
    pause
    exit /b 1
)
set "PY=%ROOT%\runtime\python-venv\Scripts\python.exe"

rem --- Node dependencies -----------------------------------------------
rem bootstrap-toolchains.ps1 already fetched a portable Node.js LTS into
rem runtime\toolchains\node when none was found on PATH. Resolve NODE/NPM to
rem fully-qualified paths - npm.cmd's own directory detection breaks when it
rem is invoked through a bare, unqualified "npm" token.
set "NODE="
for /f "usebackq delims=" %%I in (`where node 2^>nul`) do if not defined NODE set "NODE=%%I"
if not defined NODE (
    if exist "%ROOT%\runtime\toolchains\node\node.exe" (
        set "NODE=%ROOT%\runtime\toolchains\node\node.exe"
    ) else (
        echo [playground] Node.js not found on PATH and the portable copy is missing. & pause & exit /b 1
    )
)
for %%D in ("%NODE%") do set "NPM=%%~dpDnpm.cmd"
if not exist "%NPM%" ( echo [playground] npm.cmd not found next to node.exe at "%NODE%". & pause & exit /b 1 )
if not exist "%ROOT%\node_modules\elo-playground" (
    echo [playground] Installing Node dependencies ^(npm install^) ...
    call "%NPM%" install --no-audit --no-fund || ( echo [playground] npm install failed & pause & exit /b 1 )
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
start "playground-node" cmd /k "cd /d "%ROOT%" && "%NODE%" backend-node\src\server.mjs"

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
