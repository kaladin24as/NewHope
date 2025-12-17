@echo off
REM AntiGravity Installation Script for Windows

echo =========================================
echo   AntiGravity Installation
echo =========================================
echo.

REM Check Python
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.11 or higher
    exit /b 1
)
echo + Python found

REM Create virtual environment
echo.
echo Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo + Virtual environment created
) else (
    echo + Virtual environment exists
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing backend dependencies...
pip install -r backend\requirements.txt

echo.
echo Installing development dependencies...
pip install pytest pytest-cov pytest-asyncio httpx black isort flake8 mypy

REM Verify installation
echo.
echo Verifying installation...
python verify_providers.py

echo.
echo =========================================
echo   + Installation Complete!
echo =========================================
echo.
echo Quick Start:
echo   1. Activate venv: .venv\Scripts\activate
echo   2. Run API: cd backend ^&^& uvicorn main:app --reload
echo   3. Run UI: cd ui ^&^& streamlit run app.py
echo.
echo Or use Docker:
echo   docker-compose up
echo.
pause
