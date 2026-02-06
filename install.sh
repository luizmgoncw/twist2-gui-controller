#!/bin/bash

#######################################################################
# TWIST2 GUI Controller - Installation Script
#
# Usage: ./install.sh /path/to/TWIST2
#
# This script copies the GUI Controller files to your TWIST2 installation.
#######################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=============================================="
echo "  TWIST2 GUI Controller - Installer"
echo -e "==============================================${NC}"
echo ""

# Get TWIST2 path from argument or use default
TWIST2_PATH=${1:-"$HOME/Documents/TWIST2/TWIST2"}

# Check if TWIST2 directory exists
if [ ! -d "$TWIST2_PATH" ]; then
    echo -e "${RED}Error: Directory not found: $TWIST2_PATH${NC}"
    echo ""
    echo "Usage: ./install.sh /path/to/TWIST2"
    echo ""
    echo "Example:"
    echo "  ./install.sh ~/Documents/TWIST2/TWIST2"
    exit 1
fi

# Verify it's a TWIST2 installation by checking for gui.py
if [ ! -f "$TWIST2_PATH/gui.py" ]; then
    echo -e "${RED}Error: This doesn't appear to be a TWIST2 installation.${NC}"
    echo "Could not find: $TWIST2_PATH/gui.py"
    echo ""
    echo "Make sure you're pointing to the TWIST2 directory that contains:"
    echo "  - gui.py"
    echo "  - deploy_real/"
    echo "  - legged_gym/"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}Installing to: $TWIST2_PATH${NC}"
echo ""

# Copy main script
echo -n "  Copying gui_joint_controller.py... "
cp "$SCRIPT_DIR/src/gui_joint_controller.py" "$TWIST2_PATH/"
echo -e "${GREEN}OK${NC}"

# Copy launcher script
echo -n "  Copying run_gui_controller.sh... "
cp "$SCRIPT_DIR/scripts/run_gui_controller.sh" "$TWIST2_PATH/"
chmod +x "$TWIST2_PATH/run_gui_controller.sh"
echo -e "${GREEN}OK${NC}"

# Copy examples (optional - don't overwrite if they exist)
if [ -d "$SCRIPT_DIR/examples" ]; then
    mkdir -p "$TWIST2_PATH/examples"

    if [ ! -f "$TWIST2_PATH/examples/saved_poses.yaml" ]; then
        echo -n "  Copying example poses... "
        cp "$SCRIPT_DIR/examples/saved_poses.yaml" "$TWIST2_PATH/examples/"
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "  Example poses already exist, ${YELLOW}skipping${NC}"
    fi

    if [ ! -f "$TWIST2_PATH/examples/saved_scenes.yaml" ]; then
        echo -n "  Copying example scenes... "
        cp "$SCRIPT_DIR/examples/saved_scenes.yaml" "$TWIST2_PATH/examples/"
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "  Example scenes already exist, ${YELLOW}skipping${NC}"
    fi
fi

echo ""
echo -e "${GREEN}=============================================="
echo "  Installation Complete!"
echo -e "==============================================${NC}"
echo ""
echo "To run the GUI Controller:"
echo ""
echo -e "  ${BLUE}cd $TWIST2_PATH${NC}"
echo -e "  ${BLUE}conda activate twist2${NC}"
echo -e "  ${BLUE}bash run_gui_controller.sh${NC}"
echo ""
echo "Prerequisites:"
echo "  - Redis server running (redis-server)"
echo "  - For real robot: TWIST2 low-level server running"
echo ""
echo -e "Documentation: ${BLUE}https://github.com/YOUR_USERNAME/twist2-gui-controller${NC}"
echo ""
