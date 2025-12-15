@echo off
REM AURA Startup Batch File for Windows

echo.
echo ============================================
echo   AURA - Intelligent Command System
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed!
    pause
    exit /b 1
)

REM Install requirements if needed
echo Checking requirements...
pip install -q speech_recognition pyaudio pyttsx3

REM Start the startup script
echo Starting AURA...
python startup.py

pause
