@echo off
echo ==================================================
echo    STARTING HYBRID SQL E-COMMERCE ETL PIPELINE
echo ==================================================
echo.

:: 1. Activate the Python virtual environment (venv)
call venv\Scripts\activate

:: 2. Run the main ETL and analytics pipeline
python -m core.pipeline

echo.
echo ==================================================
echo    PIPELINE EXECUTION FINISHED
echo ==================================================
pause