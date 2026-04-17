@echo off
REM Launcher one-click para Windows
REM Activa el venv si existe y arranca start.py (Ollama + webapp + navegador)

cd /d "%~dp0"

if exist "..\venv\Scripts\activate.bat" (
    call "..\venv\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
)

python start.py
pause
