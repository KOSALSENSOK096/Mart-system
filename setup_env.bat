@echo off
echo Setting up Mart Application environment...

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies one by one in the correct order
echo Installing dependencies...

REM Install base dependencies first
pip install customtkinter==5.2.1
pip install mysql-connector-python==8.2.0
pip install bcrypt==4.1.2
pip install fpdf==1.7.2

REM Install numpy and pandas
pip install numpy==1.26.3
pip install pandas==2.1.4

REM Install imaging libraries
pip install pillow==10.2.0
pip install python-barcode==0.15.1

REM Run database setup
echo Setting up database...
python setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Setup completed successfully!
    echo.
    echo To run the application:
    echo 1. Make sure MySQL server is running
    echo 2. Run: python main.py
) else (
    echo.
    echo Setup failed. Please check the error messages above.
    pause
) 