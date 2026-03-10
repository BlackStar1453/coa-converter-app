#!/usr/bin/env bash
# Package the .app into a .dmg for distribution
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

APP_PATH="$PROJECT_DIR/dist/COA Converter/COA Converter.app"
DMG_NAME="COA_Converter.dmg"
DMG_PATH="$PROJECT_DIR/dist/$DMG_NAME"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    echo "Run build_macos.sh first."
    exit 1
fi

echo "=== Creating DMG ==="

# Remove existing DMG
rm -f "$DMG_PATH"

# Check if create-dmg is available
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "COA Converter" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "COA Converter.app" 150 190 \
        --app-drop-link 450 190 \
        "$DMG_PATH" \
        "$APP_PATH"
else
    # Fallback: use hdiutil directly
    echo "create-dmg not found, using hdiutil..."
    STAGING="$PROJECT_DIR/dist/dmg_staging"
    rm -rf "$STAGING"
    mkdir -p "$STAGING"
    cp -R "$APP_PATH" "$STAGING/"
    ln -s /Applications "$STAGING/Applications"

    hdiutil create -volname "COA Converter" \
        -srcfolder "$STAGING" \
        -ov -format UDZO \
        "$DMG_PATH"

    rm -rf "$STAGING"
fi

echo ""
echo "=== DMG created ==="
echo "Output: $DMG_PATH"
echo ""
echo "Note: First launch on a new Mac requires right-click → Open (Gatekeeper bypass)"
