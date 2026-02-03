#!/bin/bash

# RDP Scroll Fixer - Builder Script
# Run this script in terminal: sh build_installer.sh

# Ensure we are in the script's directory
cd "$(dirname "$0")"

echo "========================================"
echo "   RDP Scroll Fixer - DMG Builder"
echo "========================================"

# 1. Create Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "[*] Using existing virtual environment."
fi

# 2. Activate Virtual Environment
source venv/bin/activate

# 3. Install Dependencies
echo "[*] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Clean previous builds
echo "[*] Cleaning previous builds..."
rm -rf build dist

# 5. Build App
echo "[*] Building 'RDP Scroll Fixer.app'..."
python setup.py py2app

# 5.1 Sign App (Ad-hoc)
echo "[*] Signing application (Ad-hoc)..."
codesign --force --deep --sign - "dist/RDP Scroll Fixer.app"

# 6. Create DMG
if [ -d "dist/RDP Scroll Fixer.app" ]; then
    echo "[*] Creating DMG Installer..."
    
    # Create temp folder for DMG content
    mkdir -p dist/dmg_content
    
    # Copy App
    cp -r "dist/RDP Scroll Fixer.app" dist/dmg_content/
    
    # Create /Applications shortcut
    ln -s /Applications dist/dmg_content/Applications
    
    # Generate DMG
    hdiutil create -volname "RDP Scroll Fixer" \
                   -srcfolder dist/dmg_content \
                   -ov -format UDZO \
                   "dist/RDP_Scroll_Fixer_Installer.dmg"
                   
    # Cleanup
    rm -rf dist/dmg_content
    
    echo "========================================"
    echo "SUCCESS!"
    echo "Installer created at:"
    echo "   dist/RDP_Scroll_Fixer_Installer.dmg"
    echo ""
else
    echo "ERROR: Build failed."
    exit 1
fi
echo "========================================"
