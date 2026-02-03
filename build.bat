@echo off
setlocal

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --noconsole --onefile --name AutoClicky main.py

echo.
echo Build complete. Find your EXE in the "dist" folder.
pause
