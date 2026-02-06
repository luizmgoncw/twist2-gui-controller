# Installation Guide

This guide walks you through setting up the TWIST2 GUI Controller.

---

## Prerequisites

### 1. TWIST2 Installation

You must have TWIST2 installed and working. Follow the official instructions:

**Repository:** https://github.com/amazon-far/TWIST2

The GUI Controller is designed to work alongside TWIST2, not replace it. You need:
- TWIST2 cloned and configured
- The `twist2` conda environment set up
- Redis server installed

### 2. System Requirements

- **OS:** Ubuntu 20.04 / 22.04 (tested)
- **Python:** 3.8 (via conda)
- **Hardware:** Any modern PC (simulation) or PC connected to Unitree G1 (real robot)

### 3. Dependencies

The GUI uses standard Python libraries that should already be in your `twist2` environment:

```
tkinter (usually pre-installed with Python)
numpy
redis
pyyaml
```

---

## Installation Methods

### Method 1: Automatic Installation (Recommended)

```bash
# Clone this repository
git clone https://github.com/luizmgoncw/twist2-gui-controller.git
cd twist2-gui-controller

# Run the install script
./install.sh /path/to/your/TWIST2

# Example:
./install.sh ~/Documents/TWIST2/TWIST2
```

The script will:
1. Verify TWIST2 exists at the specified path
2. Copy `gui_joint_controller.py` to TWIST2 directory
3. Copy `run_gui_controller.sh` launcher script
4. Copy example poses and scenes to `examples/` subdirectory

### Method 2: Manual Installation

```bash
# Clone this repository
git clone https://github.com/luizmgoncw/twist2-gui-controller.git
cd twist2-gui-controller

# Copy the main script
cp src/gui_joint_controller.py /path/to/TWIST2/

# Copy the launcher
cp scripts/run_gui_controller.sh /path/to/TWIST2/

# Optionally copy examples
mkdir -p /path/to/TWIST2/examples
cp examples/*.yaml /path/to/TWIST2/examples/
```

---

## Running the GUI

### Step 1: Start Redis Server

In a terminal:
```bash
redis-server
```

Leave this running.

### Step 2: (Optional) Start TWIST2 Low-Level Server

For simulation:
```bash
cd /path/to/TWIST2
conda activate twist2
bash sim2sim.sh
```

For real robot:
```bash
cd /path/to/TWIST2
conda activate twist2
bash sim2real.sh
```

### Step 3: Launch the GUI

In a new terminal:
```bash
cd /path/to/TWIST2
conda activate twist2
bash run_gui_controller.sh
```

---

## Verifying Installation

### Check Redis Connection

When the GUI starts, you should see:
```
[OK] Redis Connected
```

If you see `[X] Redis Disconnected`, ensure Redis is running.

### Test Joint Control

1. Move any slider
2. Watch the value change in radians and degrees
3. If connected to the low-level server, the robot should respond

---

## Directory Structure After Installation

```
/path/to/TWIST2/
├── gui_joint_controller.py    # ← Installed
├── run_gui_controller.sh      # ← Installed
├── examples/                  # ← Installed
│   ├── saved_poses.yaml
│   └── saved_scenes.yaml
├── gui.py                     # Original TWIST2 GUI
├── deploy_real/
│   └── robot_control/
│       └── configs/
│           └── g1.yaml        # Required config file
└── ... (rest of TWIST2)
```

---

## Updating

To update to a newer version:

```bash
cd twist2-gui-controller
git pull
./install.sh /path/to/TWIST2
```

---

## Uninstalling

Simply remove the installed files:

```bash
rm /path/to/TWIST2/gui_joint_controller.py
rm /path/to/TWIST2/run_gui_controller.sh
rm -rf /path/to/TWIST2/examples/  # If you want to remove examples
```

---

## Troubleshooting Installation

### "TWIST2 not found" Error

Make sure you're pointing to the correct TWIST2 directory. The script looks for `gui.py` to verify the path:

```bash
# Check if this file exists:
ls /path/to/TWIST2/gui.py
```

### "Permission denied" for install.sh

```bash
chmod +x install.sh
./install.sh /path/to/TWIST2
```

### tkinter Not Found

Install tkinter for your system:

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Or within conda environment
conda install tk
```

---

## Next Steps

- Read the [main README](../README.md) for usage instructions
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Explore the example poses in `examples/saved_poses.yaml`
