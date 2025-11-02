@echo off
::setlocal enableDelayedExpansion

set "VENV_NAME=.venv"
set "LOG_FILE=install_log.txt"
set "TIMESTAMP=%DATE% %TIME%"
set "SUCCESS_FLAG=0"

:: ----------------------------------------------------------------------
:: 1. Initialize Log File and Configuration
:: ----------------------------------------------------------------------
echo Starting installation script on %TIMESTAMP% > "%LOG_FILE%"
echo ---------------------------------------------------------------------- >> "%LOG_FILE%"

echo Starting installation process... Details will be logged in "%LOG_FILE%".

:: Check for the 'py' launcher (Python)
py -V >nul 2>&1
IF ERRORLEVEL 1 (
    echo.
    echo CRITICAL ERROR: Python Launcher 'py' not found. Please ensure Python is installed and configured.
    echo CRITICAL ERROR: Python Launcher 'py' not found. >> "%LOG_FILE%"
    GOTO ERROR_EXIT
)


:: ----------------------------------------------------------------------
:: 2. Check for VENV and Create if Missing
:: ----------------------------------------------------------------------
echo.
echo [Checking VENV]
echo [Checking VENV] >> "%LOG_FILE%"

IF EXIST "%VENV_NAME%\" (
    echo Virtual environment "%VENV_NAME%" already exists.
    echo Virtual environment "%VENV_NAME%" already exists. >> "%LOG_FILE%"
    GOTO INSTALL_REQUIREMENTS
) ELSE (
    echo Virtual environment "%VENV_NAME%" not found. Creating it...
    echo Virtual environment "%VENV_NAME%" not found. Creating it... >> "%LOG_FILE%"
    
    :: Create the virtual environment
    py -m venv "%VENV_NAME%" >> "%LOG_FILE%" 2>&1
    
    IF ERRORLEVEL 1 (
        echo.
        echo ERROR: Failed to create VENV. Check log for details: "%LOG_FILE%"
        echo ERROR: Failed to create VENV. ERRORLEVEL !ERRORLEVEL!. >> "%LOG_FILE%"
        GOTO ERROR_EXIT
    )
    echo VENV successfully created.
    echo VENV successfully created. >> "%LOG_FILE%"
)


:: ----------------------------------------------------------------------
:: 3. Install Requirements
:: ----------------------------------------------------------------------
:INSTALL_REQUIREMENTS
echo.
echo [Installing Packages]
echo [Installing Packages] >> "%LOG_FILE%"
echo Installing packages from requirements.txt...

set "PIP_PATH=%VENV_NAME%\Scripts\pip.exe"

echo Upgrading pip... >> "%LOG_FILE%"
"%PIP_PATH%" install --upgrade pip >> "%LOG_FILE%" 2>&1

:: Check if requirements.txt exists
IF NOT EXIST "requirements.txt" (
    echo.
    echo WARNING: requirements.txt not found. Installation skipped.
    echo WARNING: requirements.txt not found. >> "%LOG_FILE%"
    set "SUCCESS_FLAG=1"
    GOTO ACTIVATION_PROMPT
)

:: Install packages
echo Starting pip install -r requirements.txt... >> "%LOG_FILE%"
"%PIP_PATH%" install -r requirements.txt >> "%LOG_FILE%" 2>&1

IF ERRORLEVEL 0 (
    echo.
    echo Installation completed successfully.
    echo Installation completed successfully. >> "%LOG_FILE%"
    set "SUCCESS_FLAG=1"
    GOTO ACTIVATION_PROMPT
) ELSE (
    echo.
    echo ERROR: requirements.txt installation failed. Check log for details: "%LOG_FILE%"
    echo ERROR: requirements.txt installation failed. ERRORLEVEL !ERRORLEVEL!. >> "%LOG_FILE%"
    GOTO ERROR_EXIT
)


:: ----------------------------------------------------------------------
:: 4. Activation Prompt
:: ----------------------------------------------------------------------
:ACTIVATION_PROMPT
echo.
echo ===================================================================
set /P "CHOICE=Do you want to activate the virtual environment now? (Y/N): "

IF /I "!CHOICE!" EQU "Y" (
    echo.
    echo Activating "%VENV_NAME%" in a new command line window...
    
    :: starts a new  cmd-Instance and runs activate.bat
    start cmd /k "%VENV_NAME%\Scripts\activate.bat"
    
    echo Activation script started.
) ELSE (
    echo.
    echo Skipped activation. You can start it later on with this command:
    echo %VENV_NAME%\Scripts\activate.bat
)
echo ===================================================================


:: ----------------------------------------------------------------------
:: 5. Finish and Cleanup
:: ----------------------------------------------------------------------
:END
echo.
echo Script finished.
echo ---------------------------------------------------------------------- >> "%LOG_FILE%"
echo Ending installation script on %DATE% %TIME% >> "%LOG_FILE%"

:: Clean up log file if successful
::IF "%SUCCESS_FLAG%"=="1" (
::    echo Cleaning up log file...
::    del "%LOG_FILE%"
::)

::endlocal
pause
EXIT /B 0


:ERROR_EXIT
echo.
echo ----------------------------------------------------------------------
echo SCRIPT FAILED. Opening log file for review...
echo ----------------------------------------------------------------------

:: Open log file in Notepad for user inspection
start notepad "%LOG_FILE%"

::endlocal
pause
EXIT /B 1