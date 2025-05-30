@echo off
echo Starting Mart Application...

REM Activate virtual environment if it exists
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    echo Virtual environment not found. Please run setup_env.bat first.
    pause
    exit /b 1
)

REM Run the application
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error. Please check the error messages above.
    pause
) 