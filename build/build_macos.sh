#!/bin/bash
# =============================================================================
# Build Script for Strategy Monitor - macOS
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Strategy Monitor"
BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$BUILD_DIR")"
DIST_DIR="$PROJECT_ROOT/dist"
SPEC_FILE="$BUILD_DIR/strategy_monitor.spec"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   Building $APP_NAME for macOS${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 1. Vérifier Python
echo -e "${YELLOW}[1/5] Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}  ✓ $PYTHON_VERSION${NC}"

# 2. Vérifier/installer PyInstaller
echo -e "${YELLOW}[2/5] Checking PyInstaller...${NC}"
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "  Installing PyInstaller..."
    pip install pyinstaller
fi
echo -e "${GREEN}  ✓ PyInstaller ready${NC}"

# 3. Vérifier les dépendances
echo -e "${YELLOW}[3/5] Checking dependencies...${NC}"
cd "$PROJECT_ROOT"
pip install -r requirements.txt -q
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

# 4. Nettoyer les anciens builds
echo -e "${YELLOW}[4/5] Cleaning previous builds...${NC}"
rm -rf "$PROJECT_ROOT/build/temp" 2>/dev/null || true
rm -rf "$DIST_DIR/$APP_NAME.app" 2>/dev/null || true
rm -rf "$DIST_DIR/$APP_NAME" 2>/dev/null || true
echo -e "${GREEN}  ✓ Cleaned${NC}"

# 5. Build avec PyInstaller
echo -e "${YELLOW}[5/5] Building application...${NC}"
echo ""

cd "$PROJECT_ROOT"
python3 -m PyInstaller \
    --clean \
    --noconfirm \
    --workpath "$BUILD_DIR/temp" \
    --distpath "$DIST_DIR" \
    "$SPEC_FILE"

echo ""

# Vérifier le résultat
if [ -d "$DIST_DIR/$APP_NAME.app" ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}   ✓ Build successful!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo -e "Application: ${BLUE}$DIST_DIR/$APP_NAME.app${NC}"
    echo ""
    
    # Taille de l'app
    APP_SIZE=$(du -sh "$DIST_DIR/$APP_NAME.app" | cut -f1)
    echo -e "Size: ${YELLOW}$APP_SIZE${NC}"
    echo ""
    
    # Instructions
    echo -e "${YELLOW}To run:${NC}"
    echo "  open \"$DIST_DIR/$APP_NAME.app\""
    echo ""
    echo -e "${YELLOW}To create DMG:${NC}"
    echo "  ./create_dmg.sh"
    echo ""
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}   ✗ Build failed!${NC}"
    echo -e "${RED}================================================${NC}"
    exit 1
fi
