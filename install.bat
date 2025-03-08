@echo off
echo Setting up the Python project...

:: Step 1: Create virtual environment
python -m venv venv

:: Step 2: Activate virtual environment
call venv\Scripts\activate

:: Step 3: Upgrade pip
python -m pip install --upgrade pip

:: Step 4: Install requirements
pip install -r requirements.txt

:: Step 5: Run the application (uncomment if needed)
:: python app.py

echo Setup complete!
pause
