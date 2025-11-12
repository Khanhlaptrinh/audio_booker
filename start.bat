@echo off
echo Starting Audio Book Reader...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

REM Start the application
echo.
echo Starting web server...
echo Open your browser and go to: http://localhost:5001
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
