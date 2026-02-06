# TWIST2 GUI Controller

> A graphical interface for manual joint control of the Unitree G1 humanoid robot, built as an extension to the [TWIST2](https://github.com/amazon-far/TWIST2) teleoperation system.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![TWIST2](https://img.shields.io/badge/Built%20on-TWIST2-blue?style=for-the-badge)](https://github.com/amazon-far/TWIST2)

---

## Demo Video

<video src="media/twistjointgit.mp4" controls width="100%"></video>

---

## Features

| Feature | Description |
|---------|-------------|
| **29-DOF Joint Control** | Direct slider control of all Unitree G1 joints with real-time feedback |
| **Pose Management** | Save, load, and organize robot poses in YAML format |
| **Scene Creator** | Create animated motion sequences with configurable interpolation and hold times |
| **Symmetric Mode** | Automatically mirror left-side joint movements to the right side |
| **Real-time Publishing** | 50Hz Redis publishing for immediate robot response |
| **Joint Limits** | Built-in safety limits from the G1 URDF specification |

### Joint Groups

The GUI organizes the 29 degrees of freedom into intuitive groups:

- **Left Leg** (6 DOF): Hip pitch/roll/yaw, knee, ankle pitch/roll
- **Right Leg** (6 DOF): Hip pitch/roll/yaw, knee, ankle pitch/roll
- **Waist** (3 DOF): Yaw, roll, pitch
- **Left Arm** (7 DOF): Shoulder pitch/roll/yaw, elbow, wrist roll/pitch/yaw
- **Right Arm** (7 DOF): Shoulder pitch/roll/yaw, elbow, wrist roll/pitch/yaw

---

## Prerequisites

This GUI is designed to work with the TWIST2 system. Before using, ensure you have:

1. **[TWIST2](https://github.com/amazon-far/TWIST2)** installed and configured
2. **Redis server** running (`redis-server`)
3. **Python 3.8** with the `twist2` conda environment
4. **TWIST2 low-level server** running (for real robot control)

See [docs/INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions.

---

## Quick Start

### 1. Clone this repository

```bash
git clone https://github.com/luizmgoncw/twist2-gui-controller.git
cd twist2-gui-controller
```

### 2. Install to your TWIST2 directory

```bash
# Automatic installation
./install.sh /path/to/your/TWIST2

# Or manual copy
cp src/gui_joint_controller.py /path/to/TWIST2/
cp scripts/run_gui_controller.sh /path/to/TWIST2/
```

### 3. Run the GUI

```bash
cd /path/to/TWIST2
conda activate twist2
bash run_gui_controller.sh
```

---

## Usage

### Basic Joint Control

1. Launch the GUI with `bash run_gui_controller.sh`
2. Use sliders to adjust individual joint angles
3. Values are displayed in both radians and degrees
4. Changes publish to Redis in real-time (if connected)

### Saving & Loading Poses

1. Adjust joints to desired position
2. Enter a name in "Pose Name" field
3. Click **Save Pose**
4. Load saved poses with **Load Pose** button

### Scene Creator

Create animated motion sequences:

1. Save several poses first
2. In Scene Creator panel, select a pose from dropdown
3. Set **Hold time** (pause at pose) and **Interp time** (transition duration)
4. Click **+ Add Step** to add to sequence
5. Use **Play** to execute the scene, **Loop** for continuous playback

### Symmetric Mode

Enable "Symmetric" checkbox to automatically mirror:
- Left leg movements → Right leg
- Left arm movements → Right arm

*Note: Roll joints are automatically negated for proper mirroring.*

---

## Architecture

This GUI integrates with TWIST2's two-process architecture:

```
┌─────────────────────────────────────────────────────────┐
│                  High-Level Control                      │
├─────────────────────────────────────────────────────────┤
│  VR Teleoperation  │  Motion Library  │  GUI Controller │
│  (PICO headset)    │  (pre-recorded)  │  (this tool)    │
└─────────────────────────────────────────────────────────┘
                            │
                      Redis (50-100Hz)
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Low-Level Control                       │
├─────────────────────────────────────────────────────────┤
│  Policy Inference (ONNX)  │  Robot Control (Unitree G1) │
└─────────────────────────────────────────────────────────┘
```

The GUI publishes joint targets to Redis key `action_body_unitree_g1_with_hands`, which the low-level server reads to control the robot.

---

## Example Poses Included

The `examples/` directory includes pre-made poses:

| Pose | Description |
|------|-------------|
| `em_pe` | Standing position |
| `semi_agachado` | Semi-crouched position |
| `tchau_direita/esquerda` | Waving gestures |
| `olhada_direita/esquerda` | Looking left/right |
| `maos_juntas` | Hands together |
| `its_fact` | Expressive gesture |

---

## Attribution

This project extends the excellent **TWIST2** system developed by researchers at Stanford University.

### Original TWIST2

- **Repository:** [amazon-far/TWIST2](https://github.com/amazon-far/TWIST2)
- **Paper:** [arXiv:2511.02832](https://arxiv.org/abs/2511.02832)
- **Authors:** Yanjie Ze, Siheng Zhao, Weizhuo Wang, Angjoo Kanazawa, Rocky Duan, Pieter Abbeel, Guanya Shi, Jiajun Wu, C. Karen Liu

If you use this tool in your research, please cite both projects:

```bibtex
@misc{marques2026twist2gui,
  title={TWIST2 GUI Controller: A Graphical Interface for Humanoid Joint Control},
  author={Marques, Luiz},
  year={2026},
  url={https://github.com/luizmgoncw/twist2-gui-controller}
}

@article{ze2025twist2,
  title={TWIST2: Scalable, Portable, and Holistic Humanoid Data Collection System},
  author={Ze, Yanjie and Zhao, Siheng and Wang, Weizhuo and Kanazawa, Angjoo and Duan, Rocky and Abbeel, Pieter and Shi, Guanya and Wu, Jiajun and Liu, C. Karen},
  year={2025},
  journal={arXiv preprint arXiv:2511.02832}
}
```

---

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

TWIST2 is also MIT licensed. See [NOTICE.md](NOTICE.md) for full attribution.

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

**Quick fixes:**

- **Redis not connected:** Start Redis with `redis-server`
- **GUI won't launch:** Ensure `twist2` conda environment is activated
- **Robot not moving:** Check that TWIST2 low-level server is running

---

*Built with tkinter and Redis for the Unitree G1 humanoid robot.*
