#!/bin/bash
# Script untuk copy assets setelah build

echo "📦 Copying assets ke dist folder..."

# Copy semua PNG files
cp *.png dist/ 2>/dev/null || true

# Copy config.json jika ada
cp config.json dist/ 2>/dev/null || true

echo "✅ Assets berhasil di-copy!"

