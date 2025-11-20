@echo off
REM Script untuk copy assets setelah build

echo 📦 Copying assets ke dist folder...

REM Copy semua PNG files
copy *.png dist\ 2>nul

REM Copy config.json jika ada
copy config.json dist\ 2>nul

echo ✅ Assets berhasil di-copy!
pause

