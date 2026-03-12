@echo off
SETLOCAL
title Python GUI with Auto-Update

:: --- CONFIGURATION ---
set SCRIPT_NAME=uTTA_Postprocess_Measurement_GUI.pyw
set REQS_FILE=requirements.txt
set LOG_FILE=install_log.txt
set VENV_DIR=.venv
set VENV_PATH=%~dp0%VENV_DIR%\Scripts\activate.bat

:: ----------------------------------------------------------------------
:: 1. Initialize Log File and Configuration
:: ----------------------------------------------------------------------
echo [STEP 1] Starting installation script on %TIMESTAMP% > "%LOG_FILE%"
echo [STEP 1] Starting installation script on %TIMESTAMP%
echo ---------------------------------------------------------------------- >> "%LOG_FILE%"

:: 2. Check if the virtual environment exists. Create if it doesn'taskkill
if not exist "%VENV_PATH%" (
    echo [INFO] NO virtual environment found. > "%LOG_FILE%"
    echo [INFO] Create venv in %~dp0%VENV_DIR%... >> "%LOG_FILE%"
	echo [INFO] NO virtual environment found.
    echo [INFO] Create venv in %~dp0%VENV_DIR%...
    
    :: Create a venv (use the installed system python)
    python -m venv "%~dp0%VENV_DIR%"
    
    if errorlevel 1 (
        echo [ERROR] Error while creating venv. Is Python installed?
		echo [ERROR] Error while creating venv. Is Python installed? >> "%LOG_FILE%"
        pause
        exit /b
    )
    echo [OK] Created virtual environment. >> "%LOG_FILE%"
	echo [OK] Created virtual environment.
)

:: 3. Acitivate VENV ---
echo [INFO] Activate venv... >> "%LOG_FILE%"
echo [INFO] Activate venv...
call "%VENV_PATH%"

:: 4. Update PIP and the packages ---
echo.  >> "%LOG_FILE%"
echo --------------------------------------------------- >> "%LOG_FILE%"
echo [STEP 2] Update-Check (Pip ^& Requirements)         >> "%LOG_FILE%"
echo --------------------------------------------------- >> "%LOG_FILE%"
echo.  >> "%LOG_FILE%"

echo.
echo ---------------------------------------------------
echo [STEP 2] Update-Check (Pip ^& Requirements)        
echo ---------------------------------------------------
echo.

:: Update Pip
python -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1

:: Install requirements.txt
if exist "%REQS_FILE%" (
    echo [INFO] Install packages from %REQS_FILE%...  >> "%LOG_FILE%"
	echo [INFO] Install packages from %REQS_FILE%...
    pip install -r "%~dp0%REQS_FILE%"  >> "%LOG_FILE%" 2>&1
) else (
    echo [WARN] No %REQS_FILE%.file found. Please create a requirements file!  >> "%LOG_FILE%"
	echo [WARN] No %REQS_FILE%.file found. Please create a requirements file!
)

:: --- 4. Start the SCRIPT ---
echo.  >> "%LOG_FILE%"
echo --------------------------------------------------- >> "%LOG_FILE%"
echo [STEP 3] Starting %SCRIPT_NAME%...                     >> "%LOG_FILE%"
echo [INFO] Terminal is kept open for logging or print-outputs.  >> "%LOG_FILE%"
echo ---------------------------------------------------  >> "%LOG_FILE%"
echo.  >> "%LOG_FILE%"

echo.
echo ---------------------------------------------------
echo [STEP 3] Starting %SCRIPT_NAME%...                    
echo [INFO] Terminal is kept open for logging or print-outputs.
echo ---------------------------------------------------
echo.

python "%~dp0%SCRIPT_NAME%"

:: --- 5. Finish ---
echo.  >> "%LOG_FILE%"
echo ---------------------------------------------------  >> "%LOG_FILE%"
echo [FINISH] Quit programm.  >> "%LOG_FILE%"
echo.
echo ---------------------------------------------------
echo [FINISH] Quit programm.
pause