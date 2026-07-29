@echo off
REM EDAPGui Startup Script
REM Creates Python venv and runs EDAPGui

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    echo This may take a moment, please wait...
    
    set PYTHON_CMD=
    
    REM Try py launcher (uses latest Python)
    py --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=py
        echo Found Python via py launcher
        goto create_venv
    )
    
    REM Fallback to python command
    python --version >nul 2>&1
    if %errorlevel% == 0 (
        set PYTHON_CMD=python
        echo Found Python
        goto create_venv
    )
    
    echo Error: No suitable Python installation found.
    pause
    exit /b 1
    
    :create_venv
    %PYTHON_CMD% -m venv venv
    
    if not exist "venv\Scripts\python.exe" (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    
    echo Installing requirements...
    venv\Scripts\python -m pip install --upgrade pip
    venv\Scripts\python -m pip install -r requirements.txt

    if %errorlevel% neq 0 (
        echo Error: Failed to install requirements
        pause
        exit /b 1
    )
    
    echo Virtual environment setup complete!
)

REM Run EDAPGui with venv python
echo Starting EDAPGui...
venv\Scripts\python.exe EDAPGui.py