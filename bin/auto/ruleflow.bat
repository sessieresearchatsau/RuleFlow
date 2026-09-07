@echo off
setlocal enabledelayedexpansion

:: 1. Check if uv is installed, download if missing
where uv >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] uv not found. Downloading and installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

    :: Add local bin to active PATH so the current session sees uv immediately
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"

    where uv >nul 2>nul
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to install or locate uv. Please restart your terminal.
        pause
        exit /b 1
    )
)

:: 2. Check if ruleflow tool environment exists; install or check for updates
uv tool list | findstr /i /c:"ruleflow " >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] ruleflow tool environment not found. Installing ruleflow...
    uv tool install --refresh ruleflow
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Failed to install ruleflow.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Checking for updates to ruleflow...
    uv tool upgrade ruleflow
    if !ERRORLEVEL! neq 0 (
        echo [WARNING] Update check failed. Proceeding with existing version...
    )
)

:: 3. Run RuleFlow Studio
echo [INFO] Launching RuleFlow Studio...
uv tool run --from ruleflow studio

pause
