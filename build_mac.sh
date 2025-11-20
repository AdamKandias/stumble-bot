#!/bin/bash
# Build script untuk Mac

echo "🔨 Building Stumble Bot untuk Mac..."
echo "======================================"

# Cek apakah virtual environment ada
if [ ! -d "venv" ]; then
    echo "📦 Membuat virtual environment..."
    python3 -m venv venv
fi

# Aktifkan virtual environment
echo "🔌 Mengaktifkan virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Menginstall dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Build dengan PyInstaller
echo "🔨 Building executable dengan PyInstaller..."
pyinstaller --onefile \
    --name "StumbleBot" \
    --icon=NONE \
    bot.py

# Build button editor juga
echo "🔨 Building Button Editor..."
pyinstaller --onefile \
    --windowed \
    --name "ButtonEditor" \
    --icon=NONE \
    button_editor.py

# Copy assets
echo "📦 Copying assets..."
chmod +x copy_assets.sh
./copy_assets.sh

echo ""
echo "✅ Build selesai!"
echo "📁 Executable ada di: dist/StumbleBot"
echo "📁 Button Editor ada di: dist/ButtonEditor"
echo ""
echo "💡 Tips:"
echo "   - Semua file .png dan config.json sudah di-copy ke folder dist/"
echo "   - File config.json akan otomatis dibuat jika tidak ada saat run"

