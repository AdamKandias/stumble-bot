@echo off
REM Build script untuk Windows

echo 🔨 Building Stumble Bot untuk Windows...
echo ======================================

REM Cek apakah virtual environment ada
if not exist "venv" (
    echo 📦 Membuat virtual environment...
    python -m venv venv
)

REM Aktifkan virtual environment
echo 🔌 Mengaktifkan virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Menginstall dependencies...
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

REM Cek apakah pyinstaller terinstall
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller tidak terinstall. Menginstall...
    pip install pyinstaller
)

REM Build dengan PyInstaller
echo 🔨 Building executable dengan PyInstaller...
pyinstaller --onefile ^
    --name "StumbleBot" ^
    --icon=NONE ^
    bot.py

REM Build button editor juga
echo 🔨 Building Button Editor...
pyinstaller --onefile ^
    --windowed ^
    --name "ButtonEditor" ^
    --icon=NONE ^
    button_editor.py

REM Copy assets
echo 📦 Copying assets...
call copy_assets.bat

echo.
echo ✅ Build selesai!
echo 📁 Executable ada di: dist\StumbleBot.exe
echo 📁 Button Editor ada di: dist\ButtonEditor.exe
echo.
echo 💡 Tips:
echo    - Semua file .png dan config.json sudah di-copy ke folder dist\
echo    - File config.json akan otomatis dibuat jika tidak ada saat run
pause

