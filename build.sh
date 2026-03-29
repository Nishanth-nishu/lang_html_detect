#!/usr/bin/env bash
# build.sh — Build a standalone CLI executable with PyInstaller
# Usage:  bash build.sh
# Output: dist/lang_detect   (single binary, no Python required on target)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Installing build dependencies..."
pip install pyinstaller --quiet

echo "[2/3] Building executable..."
pyinstaller \
  --onefile \
  --name lang_detect \
  --add-data "samples/input_samples.txt:samples" \
  --hidden-import lingua \
  --hidden-import fasttext \
  --hidden-import flask \
  --collect-all lingua_language_detector \
  --noconfirm \
  main.py

echo "[3/3] Done!"
echo "Executable: $(pwd)/dist/lang_detect"
echo ""
echo "Usage examples:"
echo "  ./dist/lang_detect                         # Process all 11 samples"
echo "  ./dist/lang_detect --sample 4              # Sample 4 only"
echo "  ./dist/lang_detect --text 'Merci, Gracias' # Inline text"
echo "  ./dist/lang_detect --input myfile.txt      # Custom file"
