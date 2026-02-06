#!/bin/bash

# TWIST2 GUI Joint Controller
# Manually control Unitree G1 joints via graphical sliders
#
# This script should be run from your TWIST2 installation directory
# after copying gui_joint_controller.py there.

# Use twist2 conda environment
PYTHON_PATH=~/anaconda3/envs/twist2/bin/python

# Change to the directory where this script is located
SCRIPT_DIR=$(dirname $(realpath $0))
cd $SCRIPT_DIR

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
echo "  - twist2 conda environment activated"
echo "  - TWIST2 low-level server running for real robot"
echo ""

$PYTHON_PATH gui_joint_controller.py
