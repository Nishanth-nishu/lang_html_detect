#!/bin/bash
# build_cs.sh — Build script for the C# Language Detector

# Ensure we are in the project directory
PROJECT_DIR="/scratch/nishanth.r/tn/lang_html_detect_cs"
cd "$PROJECT_DIR"

echo "[info] Building C# .NET project..."

# Publish as a single-file self-contained executable for Linux
# Change -r win-x64 for Windows
dotnet publish -c Release -r linux-x64 --self-contained true /p:PublishSingleFile=true /p:PublishTrimmed=false

echo ""
echo "[success] Build complete."
echo "Executable: $PROJECT_DIR/bin/Release/net8.0/linux-x64/publish/lang_detect"
echo ""
echo "To run:"
echo "  ./bin/Release/net8.0/linux-x64/publish/lang_detect --sample 1"
