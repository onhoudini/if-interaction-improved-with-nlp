@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" src\main.py
) else if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" src\main.py
) else (
    echo Nao encontrei um ambiente virtual do Windows.
    pause
    exit /b 1
)

pause