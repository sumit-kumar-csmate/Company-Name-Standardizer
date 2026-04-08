@echo off
echo Cleaning old builds...
rmdir /s /q build dist >nul 2>&1

echo Building Streamlit App with PyInstaller...
.\venv\Scripts\pyinstaller.exe --noconfirm --onedir --windowed --name "CleaningTool" ^
  --add-data "app.py;." ^
  --add-data "company_normalizer;company_normalizer" ^
  --add-data ".env;." ^
  --copy-metadata streamlit ^
  --copy-metadata openpyxl ^
  --copy-metadata openai ^
  --copy-metadata pyspellchecker ^
  --copy-metadata inflect ^
  run_app.py

echo Build finished.
