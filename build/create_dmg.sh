#!/bin/bash
# =============================================================================
# Create DMG installer for Strategy Monitor - macOS
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
APP_NAME="Strategy Monitor"
DMG_NAME="Strategy_Monitor_Installer"
BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$BUILD_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"
DMG_PATH="$DIST_DIR/$DMG_NAME.dmg"

echo -e "${BLUE}Creating DMG installer...${NC}"
echo ""

# Vérifier que l'app existe
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}Error: $APP_PATH not found${NC}"
    echo "Run build_macos.sh first"
    exit 1
fi

# Vérifier create-dmg
if ! command -v create-dmg &> /dev/null; then
    echo -e "${YELLOW}Installing create-dmg...${NC}"
    brew install create-dmg
fi

# Supprimer l'ancien DMG
rm -f "$DMG_PATH"

# Créer le DMG
create-dmg \
    --volname "$APP_NAME" \
    --volicon "$BUILD_DIR/icons/icon.icns" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 150 200 \
    --hide-extension "$APP_NAME.app" \
    --app-drop-link 450 200 \
    --no-internet-enable \
    "$DMG_PATH" \
    "$APP_PATH"

if [ -f "$DMG_PATH" ]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✓ DMG created successfully!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "Installer: ${BLUE}$DMG_PATH${NC}"
    
    DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
    echo -e "Size: ${YELLOW}$DMG_SIZE${NC}"
else
    echo -e "${RED}Failed to create DMG${NC}"
    exit 1
fi
