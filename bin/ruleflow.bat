@echo off
REM Get the directory of this script
set SCRIPT_DIR=%~dp0

REM Move to the src directory relative to the script
cd "%SCRIPT_DIR%..\src"

REM Run RuleFlow Studio
uv run python -m studio.view
@pause
