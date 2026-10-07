@echo off
setlocal enabledelayedexpansion
echo ========================================
echo Bug Bounty Pipeline: Environment Diagnostic
echo ========================================
echo.
echo WARNING: FOR AUTHORIZED LAB USE ONLY!
echo.

:: Step 1: Try to find a REAL Python that actually works
echo --- Scanning for WORKING Python installations...
echo.
set PYTHON_CMD=
:: List of candidates to try, in priority order
set CANDIDATES=
for %%p in (
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe
    "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe
    "C:\Python313\python.exe
    "C:\Python312\python.exe
    "C:\Python311\python.exe
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    py
    python3
    python
) do (
    set CAND=%%~p
    if "!CAND!"=="" goto :next_candidate
    echo Checking [%%~p]...
    :: Verify that this Python actually works
    "%%~p" --version >nul 2>&1
    if not errorlevel 1 (
        echo [+] WORKING: %%~p
        set PYTHON_CMD=%%~p
        goto :found_good_python
    ) else (
        echo [-] BROKEN: %%~p
    )
:next_candidate
)
:: If we get here, no auto-detected Python works. Ask user manually.
:ask_manual
echo.
echo ------------------------------------------------------
echo NO WORKING PYTHON FOUND AUTOMATICALLY!
echo ------------------------------------------------------
echo.
echo Please provide the FULL PATH to your python.exe (e.g., C:\Python313\python.exe)
echo.
echo If you don't have Python installed, get it from https://python.org/downloads/
echo Make sure to install Python 3.11 or newer.
echo.
set /p PYTHON_CMD="Enter full path to python.exe: 
if "%PYTHON_CMD%"=="" (
    echo.
    echo No path entered!
    pause
    exit /b 1
)
echo.
echo Checking your entered path: [%PYTHON_CMD%]
"%PYTHON_CMD%" --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo That path doesn't work either!
    goto :ask_manual
)

:found_good_python
echo.
echo ======================================================
echo SUCCESS! Found working Python: %PYTHON_CMD%
echo ======================================================
echo.
echo Getting version info...
"%PYTHON_CMD%" --version
echo.
echo Checking pip...
"%PYTHON_CMD%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Pip check failed!
    pause
    exit /b 1
)
"%PYTHON_CMD%" -m pip --version
echo.
echo.
echo Saving working Python path to env.txt
echo PYTHON_CMD=%PYTHON_CMD% > env.txt
echo.
echo Done with diagnostics!
echo.
echo Now you can run run.bat!
pause
