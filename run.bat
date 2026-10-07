@echo off
setlocal enabledelayedexpansion
echo ========================================
echo   Bug Bounty Pipeline - Windows
echo ========================================
echo.
echo WARNING: FOR AUTHORIZED LAB USE ONLY!
echo.

:: Step 1: Find Python
cd /d "%~dp0"
if not exist "env.txt" (
    echo [1/4] Running environment diagnostic first...
    call "%~dp0diagnose_env.bat"
    if errorlevel 1 (
        echo Diagnostic failed; exiting
        pause
        exit /b 1
    )
)
set PYTHON_CMD=
if exist "env.txt" (
    for /f "delims=" %%a in (env.txt) do set %%a
)
if "%PYTHON_CMD%"=="" (
    set PYTHON_CMD=py
    echo No env.txt found; trying py
)
"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Cannot find working Python!
    pause
    exit /b 1
)
echo [1/4] Using Python: %PYTHON_CMD%

:: Step 2: Create or use venv
echo [2/4] Setting up virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    "%PYTHON_CMD%" -m venv venv
    if errorlevel 1 (
        echo Failed to create venv; will use system Python instead!
        set USE_VENV=0
    ) else (
        set USE_VENV=1
    )
) else (
    set USE_VENV=1
)

:: Set the Python we will use
if "%USE_VENV%"=="1" (
    set VENV_PY=venv\Scripts\python.exe
    if not exist "%VENV_PY%" (
        echo Venv corrupted; recreating...
        rmdir /s /q venv
        "%PYTHON_CMD%" -m venv venv
        if errorlevel 1 (
            echo Still no venv; using system Python!
            set USE_VENV=0
        )
    )
)

if "%USE_VENV%"=="1" (
    set FINAL_PY=%VENV_PY%
    echo Using virtual environment at: %FINAL_PY%
) else (
    set FINAL_PY=%PYTHON_CMD%
    echo Using system Python: %FINAL_PY%
)

:: Step 3: Try to install dependencies, but skip if it fails
echo [3/4] Trying to install dependencies...
:: Disable proxy for pip (since your connection is failing)
set NO_PROXY=*
set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=
echo Proxy settings cleared!

:: Try to install requirements
"%FINAL_PY%" -m pip install -r requirements.txt --timeout 15 --retries 1
if errorlevel 1 (
    echo.
    echo WARNING: Could not install all dependencies (maybe no internet?)
    echo Checking if required packages are already installed...
    "%FINAL_PY%" -c "import streamlit, yaml, psutil, requests, pandas, plotly, bs4, lxml, dns"
    if errorlevel 1 (
        echo Some packages are missing! Trying to install just the critical ones...
        "%FINAL_PY%" -m pip install pyyaml psutil requests --timeout 10 --retries 1
        if errorlevel 1 (
            echo Still failing! Will try to proceed anyway, but some features might not work!
        )
    ) else (
        echo All required packages already installed!
    )
)

echo.
echo [4/4] Ready to launch!
echo.
echo Choose mode:
echo 1. Interactive GUI (Recommended)
echo 2. CLI Pipeline
echo.
set /p mode="Enter your choice (1 or 2): "
if "%mode%"=="1" (
    echo.
    echo Starting GUI...
    "%FINAL_PY%" -m streamlit run app.py
) else (
    echo.
    echo Starting CLI pipeline...
    "%FINAL_PY%" run-full-pipeline.py --resume ask
)
echo.
pause
