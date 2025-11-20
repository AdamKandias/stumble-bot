# Stumble Bot 🤖

Bot otomatis untuk game Stumble Guys yang menggunakan image recognition untuk mendeteksi dan mengklik tombol-tombol di game.

## ✨ Fitur

- ✅ **Pilih Window/Aplikasi** - Pilih aplikasi yang ingin di-detect (UTM, emulator, dll)
- ✅ Deteksi tombol otomatis menggunakan template matching
- ✅ Konfigurasi fleksibel melalui file JSON (tidak perlu edit code)
- ✅ GUI Editor untuk mengedit gambar template dan posisi klik
- ✅ Cross-platform: bisa di-build untuk Mac dan Windows
- ✅ Preview mode untuk debugging
- ✅ Pause/Resume dengan tombol 'P'
- ✅ Auto-detect window yang sudah dipilih sebelumnya

## 📋 Requirements

- Python 3.8 atau lebih baru
- Semua dependencies ada di `requirements.txt`

## 🚀 Instalasi

### 1. Clone atau download project ini

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Pastikan semua file gambar (.png) ada di folder project

## 🎮 Cara Menggunakan

### 1. Pilih Window/Aplikasi

Saat pertama kali menjalankan bot, Anda akan diminta untuk memilih window/aplikasi yang ingin di-detect:

```bash
python bot.py
```

Bot akan menampilkan list semua window yang terbuka (misalnya UTM, emulator, atau aplikasi lain). Pilih window yang ingin di-detect, dan bot akan otomatis mengatur area deteksi sesuai dengan ukuran dan posisi window tersebut.

**Tips:**
- Pastikan aplikasi yang ingin di-detect sudah terbuka sebelum menjalankan bot
- Bot akan menyimpan pilihan window ke `config.json`
- Jika window tidak ditemukan, bot akan menggunakan konfigurasi manual

### 2. Mode Normal (Tanpa Preview)

```bash
python bot.py
# Pilih window (jika belum pernah)
# Pilih opsi 1
```

### 3. Mode Preview (Dengan Preview Window)

```bash
python bot.py
# Pilih window (jika belum pernah)
# Pilih opsi 2
```

### Kontrol Bot

- **P** - Pause/Resume bot
- **Ctrl+C** - Stop bot
- **Q** (di preview window) - Quit

## 🎨 Menggunakan Button Editor

Untuk mengedit konfigurasi tombol tanpa perlu edit code:

```bash
python button_editor.py
```

Fitur Button Editor:
- ✅ Ganti gambar template (khususnya `choose_event.png`)
- ✅ Edit posisi klik (X, Y)
- ✅ Ambil screenshot dari game area
- ✅ Preview gambar template
- ✅ Edit game area (top, left, width, height)
- ✅ Edit detection threshold
- ✅ Simpan konfigurasi ke `config.json`

### Cara Edit Gambar Template

1. Buka `button_editor.py`
2. Pilih tombol yang ingin diedit (misalnya `choose_event`)
3. Klik "Ganti Gambar Template" untuk memilih file gambar baru
4. Atau klik "Ambil Screenshot" untuk mengambil screenshot dari game
5. Edit posisi klik jika perlu
6. Klik "Simpan Konfigurasi"

## 🔨 Build untuk Mac dan Windows

### Build untuk Mac

**Di Mac, gunakan script ini:**

```bash
chmod +x build_mac.sh
./build_mac.sh
```

Executable akan ada di folder `dist/StumbleBot`

### Build untuk Windows

**⚠️ Catatan: Script Windows hanya bisa dijalankan di Windows!**

Jika Anda menggunakan Mac:
- Script `build_windows.bat` **TIDAK bisa dijalankan di Mac**
- Untuk build Windows executable, Anda perlu:
  1. Gunakan Windows machine (atau Windows VM)
  2. Atau gunakan Windows di cloud/remote
  3. Atau minta teman yang pakai Windows untuk build

**Di Windows, jalankan:**

```batch
build_windows.bat
```

Atau double-click file `build_windows.bat` di Windows Explorer.

Executable akan ada di folder `dist\StumbleBot.exe`

### Catatan Build

- Pastikan semua file `.png` ada di folder yang sama dengan executable
- File `config.json` akan otomatis dibuat jika tidak ada saat pertama kali run
- Untuk distribusi, copy semua file `.png` dan `config.json` ke folder yang sama dengan executable

## 📁 Struktur File

```
stumble-bot/
├── bot.py                 # Main bot script
├── button_editor.py       # GUI editor untuk konfigurasi
├── config.json            # Konfigurasi tombol dan settings
├── requirements.txt       # Python dependencies
├── build_mac.sh           # Build script untuk Mac
├── build_windows.bat      # Build script untuk Windows
├── *.png                  # Template gambar untuk deteksi tombol
└── README.md              # Dokumentasi ini
```

## ⚙️ Konfigurasi

Semua konfigurasi ada di file `config.json`:

```json
{
  "game_area": {
    "top": 40,
    "left": 0,
    "width": 1024,
    "height": 768
  },
  "button_templates": {
    "choose_event": {
      "image": "choose_event.png",
      "click_pos": [232, 423]
    },
    ...
  },
  "settings": {
    "detection_threshold": 0.8,
    "choose_event_timeout": 70,
    ...
  }
}
```

### Game Area

Area layar yang akan di-scan untuk deteksi tombol. Sesuaikan dengan posisi window game Anda.

### Button Templates

Setiap tombol memiliki:
- `image`: Nama file gambar template
- `click_pos`: Posisi [X, Y] untuk klik (relatif terhadap game area)

### Settings

- `detection_threshold`: Threshold untuk template matching (0.0 - 1.0)
- `choose_event_timeout`: Timeout untuk recovery mode (detik)
- `esc_press_interval`: Interval tekan ESC untuk recovery (detik)
- `event_menu_click_threshold`: Threshold untuk klik ok2 (jumlah deteksi berturut-turut)
- `leave_game_esc_threshold`: Threshold untuk tekan ESC (jumlah deteksi berturut-turut)

## 🐛 Troubleshooting

### Bot tidak mendeteksi tombol

1. Cek apakah gambar template sesuai dengan tampilan game saat ini
2. Cek `detection_threshold` di `config.json` (coba turunkan ke 0.7)
3. Gunakan mode preview untuk melihat deteksi real-time
4. Pastikan `game_area` sesuai dengan posisi window game

### Window tidak terdeteksi (Mac)

Jika window tidak muncul di list:

1. **Berikan permission Accessibility:**
   - Buka **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
   - Tambahkan Terminal (atau aplikasi yang menjalankan Python)
   - Centang checkbox untuk memberikan akses
   - Restart Terminal/Python

2. **Atau gunakan manual input:**
   - Saat diminta pilih window, pilih opsi manual
   - Masukkan nama aplikasi (misalnya "UTM")
   - Bot akan mencoba mendapatkan ukuran window otomatis

3. **Atau set manual di config.json:**
   - Edit `game_area` di `config.json` secara manual
   - Set `top`, `left`, `width`, `height` sesuai window Anda

### Gambar template tidak update

1. Pastikan file gambar sudah diganti di folder project
2. Restart bot setelah mengganti gambar
3. Gunakan Button Editor untuk memastikan konfigurasi tersimpan

### Build error

1. Pastikan semua dependencies terinstall: `pip install -r requirements.txt`
2. Pastikan PyInstaller terinstall: `pip install pyinstaller`
3. Untuk Mac, mungkin perlu install Xcode Command Line Tools
4. Jika error "Cannot import 'setuptools.build_meta'":
   - Pastikan setuptools terinstall: `pip install --upgrade setuptools wheel`
   - Rebuild virtual environment jika perlu
5. Jika numpy error dengan Python 3.13:
   - Versi requirements.txt sudah diupdate untuk kompatibel dengan Python 3.13
   - Pastikan menggunakan versi numpy >= 1.26.0

## 📝 Catatan

- Bot ini menggunakan image recognition, jadi pastikan tampilan game konsisten
- Jika game update dan UI berubah, update gambar template menggunakan Button Editor
- Bot ini hanya untuk keperluan edukasi dan personal use

## 📄 License

Free to use for personal projects.

