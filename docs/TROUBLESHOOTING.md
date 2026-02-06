# Troubleshooting Guide

Common issues and solutions for the TWIST2 GUI Controller.

---

## GUI Issues

### GUI won't start

**Symptom:** Error when running `run_gui_controller.sh`

**Solutions:**

1. **Check your environment is activated:**
   ```bash
   # For conda:
   conda activate twist2

   # For venv:
   source /path/to/venv3.8/bin/activate

   python --version  # Should be 3.8.x
   ```

2. **Check tkinter installation:**
   ```bash
   python -c "import tkinter; print('OK')"
   ```

   If this fails:
   ```bash
   # For venv/system Python on Ubuntu:
   sudo apt-get install python3.8-tk

   # For conda:
   conda install tk
   ```

3. **Check config file exists:**
   ```bash
   ls deploy_real/robot_control/configs/g1.yaml
   ```
   The GUI needs this file for joint configuration.

### GUI is slow or laggy

**Symptom:** Sliders respond slowly, UI feels unresponsive

**Solutions:**

1. Close other heavy applications
2. Check if Redis is overloaded:
   ```bash
   redis-cli info | grep used_memory
   ```
3. Reduce the number of scene steps if playing a complex scene

---

## Redis Issues

### "Redis Disconnected" message

**Symptom:** GUI shows `[X] Redis Disconnected`

**Solutions:**

1. **Start Redis server:**
   ```bash
   redis-server
   ```

2. **Check if Redis is running:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. **Check Redis port (default 6379):**
   ```bash
   netstat -tlnp | grep 6379
   ```

### Robot doesn't respond to GUI

**Symptom:** Sliders move but robot stays still

**Solutions:**

1. **Verify TWIST2 low-level server is running:**
   - For simulation: `bash sim2sim.sh`
   - For real robot: `bash sim2real.sh`

2. **Check Redis key is being published:**
   ```bash
   redis-cli
   > GET action_body_unitree_g1_with_hands
   ```
   Should show JSON array of joint values.

3. **Verify low-level server is reading from Redis:**
   Check the terminal running the low-level server for messages.

---

## DDS Library Conflict (Real Robot)

### `free(): invalid pointer` Crash

**Symptom:** Program crashes with memory error when connecting to real robot.

**Cause:** Conflict between ROS2 and Unitree SDK2 DDS libraries.

**Solution:**

Add to your shell script (before running Python):

```bash
export LD_LIBRARY_PATH=$HOME/Documents/TWIST2/unitree_sdk2/thirdparty/lib/x86_64:$LD_LIBRARY_PATH
```

**Why it works:**

- Both ROS2 and Unitree SDK2 use CycloneDDS
- Different versions with incompatible ABIs
- Prepending Unitree's path ensures correct library loads first

**Verification:**

```bash
# Find where unitree_interface.so is located:
python -c "import unitree_interface; import os; print(os.path.dirname(unitree_interface.__file__))"

# Then check its dependencies (replace <path> with output from above):
ldd <path>/unitree_interface.so | grep libddsc
# Should show: .../unitree_sdk2/thirdparty/lib/x86_64/libddsc.so
```

---

## Pose & Scene Issues

### Pose won't save

**Symptom:** Click "Save Pose" but nothing happens

**Solutions:**

1. **Enter a pose name:** The name field cannot be empty
2. **Check file permissions:**
   ```bash
   touch saved_poses.yaml
   # If this fails, check directory permissions
   ```

### Scene won't play

**Symptom:** "No steps in scene" error

**Solutions:**

1. **Add steps first:** Use the Scene Creator panel to add poses
2. **Verify poses exist:** All poses referenced in scene must be saved

### Poses deleted after reinstall

**Issue:** Your saved poses are gone after updating

**Prevention:**
- The GUI stores poses in `saved_poses.yaml` in the TWIST2 directory
- Back up this file before reinstalling:
  ```bash
  cp saved_poses.yaml saved_poses.yaml.backup
  ```

---

## Joint Limit Issues

### Slider won't go to desired value

**Symptom:** Slider stops before reaching the value you want

**Explanation:** This is intentional! The GUI enforces joint limits from the G1 URDF to prevent:
- Motor damage
- Self-collision
- Unsafe robot positions

**What to do:**
- Work within the displayed limits
- The limits are shown in the slider range (min to max)

### Robot behaves differently than GUI shows

**Symptom:** Joint values in GUI don't match actual robot position

**Possible causes:**

1. **Low-level control latency:** There's a ~20ms delay between GUI and robot
2. **Policy smoothing:** TWIST2's low-level controller may smooth movements
3. **Physical constraints:** Real robot has friction, gravity, load that simulation doesn't

---

## Performance Issues

### High CPU usage

**Symptom:** CPU usage spikes when GUI is running

**Solutions:**

1. **Normal behavior:** The GUI runs at 50Hz publish rate + 60 FPS UI updates
2. **Reduce publish rate:** Edit `self.publish_rate = 50` in source to lower value
3. **Close scene playback:** Looping scenes consume more resources

### Memory usage grows over time

**Symptom:** RAM usage increases the longer GUI runs

**Solutions:**

1. Generally not an issue with normal use
2. If running for very long sessions, restart the GUI periodically
3. Clear scene steps you're not using

---

## Getting Help

If your issue isn't listed here:

1. **Check TWIST2 issues:** https://github.com/amazon-far/TWIST2/issues
2. **Open an issue:** https://github.com/luizmgoncw/twist2-gui-controller/issues

When reporting issues, include:
- Operating system version
- Python version (`python --version`)
- Error messages (full traceback)
- Steps to reproduce

---

*Last updated: February 2026*
