@echo off
echo ========================================
echo Bug Bounty Pipeline: Manual Setup
echo ========================================
echo.
echo WARNING: FOR AUTHORIZED LAB USE ONLY!
echo.
echo This script will help you create env.txt manually.
echo.
echo Please enter the FULL PATH to your working python.exe, e.g.,
echo C:\Python313\python.exe
echo OR
echo C:\Users\YourName\AppData\Local\Programs\Python\Python313\python.exe
echo.
:ask
set /p PYTHON="Enter full path to python.exe:
echo.
echo Checking: %PYTHON%
echo.
"%PYTHON%" --version
if errorlevel 1 (
    echo.
    echo That path does NOT work! Try again!
    goto :ask
)
echo.
echo SUCCESS! That Python works!
echo.
echo Saving to env.txt
echo PYTHON_CMD=%PYTHON% > env.txt
echo.
echo Done! Now run run.bat now!
pause
