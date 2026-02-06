# Installation Guide

This guide walks you through setting up the TWIST2 GUI Controller.

---

## Prerequisites

### 1. TWIST2 Installation

You must have TWIST2 installed and working. Follow the official instructions:

**Repository:** https://github.com/amazon-far/TWIST2

The GUI Controller is designed to work alongside TWIST2, not replace it. You need:
- TWIST2 cloned and configured
- The `twist2` environment set up (conda or venv)
- Redis server installed

### 2. System Requirements

- **OS:** Ubuntu 20.04 / 22.04 (tested)
- **Python:** 3.8 (via conda or venv)
- **Hardware:** Any modern PC (simulation) or PC connected to Unitree G1 (real robot)

### 3. Dependencies

The GUI uses standard Python libraries. Most should already be in your `twist2` environment, but **tkinter must be installed separately**:

**Required Python packages:**
```
tkinter (MUST be installed via system package manager - see below)
numpy
redis
pyyaml
```

**Installing tkinter:**

For **Ubuntu/Debian** with Python 3.8:
```bash
sudo apt update
sudo apt install python3.8-tk
```

For **conda** environments:
```bash
conda activate twist2
conda install tk
```

For **venv** environments:
Install the system package for your Python version (e.g., `python3.8-tk`), then tkinter will be available in your venv.

---

## Installation

```bash
# Clone this repository
git clone https://github.com/luizmgoncw/twist2-gui-controller.git
cd twist2-gui-controller

# Activate your twist2 environment
conda activate twist2  # OR: source /path/to/venv3.8/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install tkinter if needed
sudo apt install python3.8-tk  # Ubuntu/Debian
# OR
conda install tk  # conda users
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
# Activate your environment (choose one):
conda activate twist2  # OR: source /path/to/venv3.8/bin/activate
bash sim2sim.sh
```

For real robot:
```bash
cd /path/to/TWIST2
# Activate your environment (choose one):
conda activate twist2  # OR: source /path/to/venv3.8/bin/activate
bash sim2real.sh
```

### Step 3: Launch the GUI

In a new terminal:
```bash
cd twist2-gui-controller
# Activate your environment (choose one):
conda activate twist2  # OR: source /path/to/venv3.8/bin/activate
bash scripts/run_gui_controller.sh
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

## Troubleshooting Installation

### tkinter Not Found

Install tkinter for your environment:

```bash
# For venv or system Python on Ubuntu/Debian:
sudo apt-get install python3.8-tk

# For conda environments:
conda activate twist2
conda install tk
```

---

## Next Steps

- Read the [main README](../README.md) for usage instructions
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Explore the example poses in `examples/saved_poses.yaml`
