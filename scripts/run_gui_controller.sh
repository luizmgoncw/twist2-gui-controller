#!/bin/bash

# TWIST2 GUI Joint Controller
# Manually control Unitree G1 joints via graphical sliders
#
# Run this script from the twist2-gui-controller directory

# Use current Python environment (works with both conda and venv)
# Make sure you have activated your twist2 environment before running this script
PYTHON_PATH=python

# Change to the repository root directory
SCRIPT_DIR=$(dirname $(realpath $0))
REPO_ROOT=$(dirname $SCRIPT_DIR)
cd $REPO_ROOT

echo "=============================================="
echo "  TWIST2 GUI Joint Controller"
echo "=============================================="
echo ""
echo "  Publishing to Redis at 50Hz"
echo "  Robot type: unitree_g1_with_hands (29 DOF)"
echo ""
echo "Usage:"
echo "  - Move sliders to adjust joint positions"
echo "  - Changes are published to Redis in real-time"
echo "  - 'Reset to Default' returns to standing pose"
echo "  - 'Zero All' sets all joints to 0"
echo "  - Use Scene Creator to animate sequences"
echo ""
echo "Prerequisites:"
echo "  - Redis server running (redis-server)"
echo "  - twist2 environment activated (conda or venv)"
echo "  - tkinter installed (sudo apt install python3.8-tk)"
echo "  - TWIST2 low-level server running for real robot"
echo ""

$PYTHON_PATH src/gui_joint_controller.py
