#!/usr/bin/env python3
"""
GUI Joint Controller for TWIST2 G1 Robot
Manually control robot joints and publish to Redis for testing
"""
import tkinter as tk
from tkinter import ttk
import numpy as np
import redis
import json
import yaml
import threading
import time
from pathlib import Path


class JointControllerGUI:
    def __init__(self, root, config_path=None):
        self.root = root
        self.root.title("TWIST2 G1 Joint Controller")
        self.root.geometry("1400x900")  # Wider to accommodate Scene Creator

        # Load config - use local config by default
        if config_path is None:
            # Try to find config relative to this script
            script_dir = Path(__file__).parent
            config_path = script_dir.parent / "config" / "g1.yaml"
            if not config_path.exists():
                # Fallback to current directory
                config_path = Path("config/g1.yaml")

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Connect to Redis
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)
        try:
            self.redis_client.ping()
            self.redis_connected = True
        except:
            self.redis_connected = False
            print("⚠️  Warning: Could not connect to Redis. Publishing disabled.")

        # Joint configuration
        self.num_joints = 29
        self.default_angles = np.array(self.config['default_angles'])
        self.current_angles = self.default_angles.copy()

        # Joint names and ranges (in radians)
        self.joint_names = [
            # Legs (0-11)
            "left_hip_pitch", "left_hip_roll", "left_hip_yaw",
            "left_knee", "left_ankle_pitch", "left_ankle_roll",
            "right_hip_pitch", "right_hip_roll", "right_hip_yaw",
            "right_knee", "right_ankle_pitch", "right_ankle_roll",
            # Waist (12-14)
            "waist_yaw", "waist_roll", "waist_pitch",
            # Arms (15-28)
            "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw",
            "left_elbow", "left_wrist_roll", "left_wrist_pitch", "left_wrist_yaw",
            "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw",
            "right_elbow", "right_wrist_roll", "right_wrist_pitch", "right_wrist_yaw"
        ]

        # Joint limits from URDF: g1_29dof_rev_1_0.urdf
        self.joint_limits = [
            (-2.5307, 2.8798),   # left_hip_pitch
            (-0.5236, 2.9671),   # left_hip_roll
            (-2.7576, 2.7576),   # left_hip_yaw
            (-0.0873, 2.8798),   # left_knee
            (-0.8727, 0.5236),   # left_ankle_pitch
            (-0.2618, 0.2618),   # left_ankle_roll
            (-2.5307, 2.8798),   # right_hip_pitch
            (-2.9671, 0.5236),   # right_hip_roll
            (-2.7576, 2.7576),   # right_hip_yaw
            (-0.0873, 2.8798),   # right_knee
            (-0.8727, 0.5236),   # right_ankle_pitch
            (-0.2618, 0.2618),   # right_ankle_roll
            (-2.618, 2.618),     # waist_yaw
            (-0.52, 0.52),       # waist_roll
            (-0.52, 0.52),       # waist_pitch
            (-3.0892, 2.6704),   # left_shoulder_pitch (-177° to 153°)
            (-1.5882, 2.2515),   # left_shoulder_roll (-91° to 129°)
            (-2.618, 2.618),     # left_shoulder_yaw (-150° to 150°)
            (-1.0472, 2.0944),   # left_elbow (-60° to 120°)
            (-1.9722, 1.9722),   # left_wrist_roll (-113° to 113°)
            (-1.6144, 1.6144),   # left_wrist_pitch (-92° to 92°)
            (-1.6144, 1.6144),   # left_wrist_yaw (-92° to 92°)
            (-3.0892, 2.6704),   # right_shoulder_pitch (-177° to 153°)
            (-2.2515, 1.5882),   # right_shoulder_roll (-129° to 91°)
            (-2.618, 2.618),     # right_shoulder_yaw (-150° to 150°)
            (-1.0472, 2.0944),   # right_elbow (-60° to 120°)
            (-1.9722, 1.9722),   # right_wrist_roll (-113° to 113°)
            (-1.6144, 1.6144),   # right_wrist_pitch (-92° to 92°)
            (-1.6144, 1.6144),   # right_wrist_yaw (-92° to 92°)
        ]

        # Publishing control
        self.publishing = False
        self.publish_rate = 50  # Hz

        # Symmetric mode: mirror left joints to right
        self.symmetric_mode = False

        # Joint pairs mapping: left_idx -> (right_idx, flip_sign)
        # flip_sign=True means negate the value (e.g., for roll joints)
        self.joint_pairs = {
            # Left leg -> Right leg
            0: (6, False),   # hip_pitch
            1: (7, True),    # hip_roll (flip sign)
            2: (8, True),    # hip_yaw (flip sign)
            3: (9, False),   # knee
            4: (10, False),  # ankle_pitch
            5: (11, True),   # ankle_roll (flip sign)
            # Left arm -> Right arm
            15: (22, False),  # shoulder_pitch
            16: (23, True),   # shoulder_roll (flip sign)
            17: (24, True),   # shoulder_yaw (flip sign)
            18: (25, False),  # elbow
            19: (26, False),  # wrist_roll
            20: (27, False),  # wrist_pitch
            21: (28, False),  # wrist_yaw
        }

        # Scene Creator state
        self.scene_steps = []  # List of {pose_name, hold_time, interp_time}
        self.scene_playing = False
        self.scene_loop = False
        self.current_scene_step = 0
        self.pending_interp_time = 0.0  # Interp time for arriving at next pose

        # Find saved files relative to this script
        script_dir = Path(__file__).parent
        self.saved_scenes_file = script_dir.parent / "examples" / "saved_scenes.yaml"
        self.saved_poses_file = script_dir.parent / "examples" / "saved_poses.yaml"

        self.interp_callback = None  # Callback when interpolation completes

        # Build GUI
        self.build_gui()

        # Start publishing thread
        self.start_publishing()

    def build_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights - two columns: sliders (left) and scene creator (right)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)  # Sliders get more space
        main_frame.columnconfigure(1, weight=1)  # Scene creator
        main_frame.rowconfigure(1, weight=1)

        # Control panel at top
        control_frame = ttk.LabelFrame(main_frame, text="Control", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Redis status
        status_text = "[OK] Redis Connected" if self.redis_connected else "[X] Redis Disconnected"
        status_color = "green" if self.redis_connected else "red"
        self.status_label = tk.Label(control_frame, text=status_text, fg=status_color, font=("Arial", 12, "bold"))
        self.status_label.grid(row=0, column=0, padx=10)

        # Publishing toggle
        self.publish_var = tk.BooleanVar(value=True)
        self.publish_check = ttk.Checkbutton(
            control_frame, text="Publish to Redis",
            variable=self.publish_var, command=self.toggle_publishing
        )
        self.publish_check.grid(row=0, column=1, padx=10)

        # Symmetric mode toggle
        self.symmetric_var = tk.BooleanVar(value=False)
        self.symmetric_check = ttk.Checkbutton(
            control_frame, text="Symmetric",
            variable=self.symmetric_var, command=self.toggle_symmetric
        )
        self.symmetric_check.grid(row=0, column=2, padx=10)

        # Reset button
        reset_btn = ttk.Button(control_frame, text="Reset to Default", command=self.reset_to_default)
        reset_btn.grid(row=0, column=3, padx=10)

        # Zero all button
        zero_btn = ttk.Button(control_frame, text="Zero All", command=self.zero_all)
        zero_btn.grid(row=0, column=4, padx=10)

        # Publish rate display
        self.rate_label = tk.Label(control_frame, text=f"Rate: {self.publish_rate} Hz", font=("Arial", 10))
        self.rate_label.grid(row=0, column=5, padx=10)

        # Save/Load pose controls (second row)
        save_frame = ttk.Frame(control_frame)
        save_frame.grid(row=1, column=0, columnspan=6, pady=(10, 0), sticky=(tk.W, tk.E))

        ttk.Label(save_frame, text="Pose Name:").grid(row=0, column=0, padx=5)
        self.pose_name_entry = ttk.Entry(save_frame, width=20)
        self.pose_name_entry.grid(row=0, column=1, padx=5)
        self.pose_name_entry.insert(0, "my_pose")

        save_btn = ttk.Button(save_frame, text="Save Pose", command=self.save_pose)
        save_btn.grid(row=0, column=2, padx=5)

        load_btn = ttk.Button(save_frame, text="Load Pose", command=self.show_load_dialog)
        load_btn.grid(row=0, column=3, padx=5)

        # Interpolation time control
        ttk.Label(save_frame, text="Interp Time (s):").grid(row=0, column=4, padx=5)
        self.interp_time_entry = ttk.Entry(save_frame, width=8)
        self.interp_time_entry.grid(row=0, column=5, padx=5)
        self.interp_time_entry.insert(0, "2.0")

        # Interpolation state
        self.interpolating = False
        self.interp_start_angles = None
        self.interp_target_angles = None
        self.interp_start_time = None
        self.interp_duration = 2.0

        # Canvas with scrollbar for sliders
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Create window and make it fill the canvas width
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_frame_configure(event):
            # Update scroll region
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            # Make the frame fill the canvas width
            canvas.itemconfig(canvas_window, width=event.width)

        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def on_mousewheel_linux(event):
            if event.num == 4:  # Scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                canvas.yview_scroll(1, "units")

        # Bind mouse wheel for different platforms
        canvas.bind_all("<MouseWheel>", on_mousewheel)  # Windows/Mac
        canvas.bind_all("<Button-4>", on_mousewheel_linux)  # Linux scroll up
        canvas.bind_all("<Button-5>", on_mousewheel_linux)  # Linux scroll down

        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Create sliders for each joint
        self.sliders = []
        self.value_labels = []

        # Group joints by body part
        groups = [
            ("Left Leg", 0, 6),
            ("Right Leg", 6, 12),
            ("Waist", 12, 15),
            ("Left Arm", 15, 22),
            ("Right Arm", 22, 29)
        ]

        row = 0
        for group_name, start_idx, end_idx in groups:
            # Group header
            group_frame = ttk.LabelFrame(scrollable_frame, text=group_name, padding="10")
            group_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
            group_frame.columnconfigure(1, weight=1)
            row += 1

            for i in range(start_idx, end_idx):
                # Joint name
                name_label = ttk.Label(group_frame, text=self.joint_names[i], width=20)
                name_label.grid(row=i-start_idx, column=0, sticky=tk.W, padx=5, pady=2)

                # Slider
                slider = tk.Scale(
                    group_frame,
                    from_=self.joint_limits[i][0],
                    to=self.joint_limits[i][1],
                    orient=tk.HORIZONTAL,
                    resolution=0.01,
                    length=300,
                    command=lambda val, idx=i: self.update_joint(idx, float(val))
                )
                slider.set(self.default_angles[i])
                slider.grid(row=i-start_idx, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
                self.sliders.append(slider)

                # Value label (rad and deg)
                value_label = ttk.Label(group_frame, text=self.format_value(self.default_angles[i]), width=20)
                value_label.grid(row=i-start_idx, column=2, sticky=tk.W, padx=5, pady=2)
                self.value_labels.append(value_label)

        # ==================== SCENE CREATOR PANEL (Right Side) ====================
        self.build_scene_creator(main_frame)

    def build_scene_creator(self, parent):
        """Build the Scene Creator panel on the right side"""
        scene_frame = ttk.LabelFrame(parent, text="Scene Creator", padding="10")
        scene_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        scene_frame.columnconfigure(0, weight=1)
        scene_frame.rowconfigure(2, weight=1)  # Listbox row expands

        # === Scene Steps Listbox ===
        steps_label = ttk.Label(scene_frame, text="Scene Steps:", font=("Arial", 10, "bold"))
        steps_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

        # Listbox with scrollbar
        listbox_frame = ttk.Frame(scene_frame)
        listbox_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)

        self.scene_listbox = tk.Listbox(listbox_frame, font=("Courier", 10), height=15, width=35)
        scene_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.scene_listbox.yview)
        self.scene_listbox.configure(yscrollcommand=scene_scrollbar.set)
        self.scene_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scene_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # === Add Step Controls ===
        add_frame = ttk.LabelFrame(scene_frame, text="Add Step", padding="5")
        add_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)

        # Pose selector dropdown
        ttk.Label(add_frame, text="Pose:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scene_pose_var = tk.StringVar()
        self.scene_pose_combo = ttk.Combobox(add_frame, textvariable=self.scene_pose_var, width=20, state="readonly")
        self.scene_pose_combo.grid(row=0, column=1, padx=5, pady=2)
        self.refresh_pose_combo()

        # Hold time (time to stay at pose)
        ttk.Label(add_frame, text="Hold (s):").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.scene_hold_entry = ttk.Entry(add_frame, width=10)
        self.scene_hold_entry.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.scene_hold_entry.insert(0, "0.0")

        # Interpolation time (time to go TO next pose)
        ttk.Label(add_frame, text="Interp (s):").grid(row=2, column=0, padx=5, sticky=tk.W)
        self.scene_interp_entry = ttk.Entry(add_frame, width=10)
        self.scene_interp_entry.grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)
        self.scene_interp_entry.insert(0, "1.0")

        # Add and Refresh buttons side by side
        add_btn = ttk.Button(add_frame, text="+ Add Step", command=self.add_scene_step)
        add_btn.grid(row=3, column=0, padx=2, pady=5)

        refresh_btn = ttk.Button(add_frame, text="Refresh", command=self.refresh_pose_combo)
        refresh_btn.grid(row=3, column=1, padx=2, pady=5)

        # === Step Management Buttons ===
        manage_frame = ttk.Frame(scene_frame)
        manage_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(manage_frame, text="Edit", width=4, command=self.edit_scene_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(manage_frame, text="Up", width=4, command=self.move_step_up).pack(side=tk.LEFT, padx=2)
        ttk.Button(manage_frame, text="Down", width=5, command=self.move_step_down).pack(side=tk.LEFT, padx=2)
        ttk.Button(manage_frame, text="Remove", command=self.remove_scene_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(manage_frame, text="Clear", command=self.clear_scene).pack(side=tk.LEFT, padx=2)

        # Double-click to edit (select item at click position first)
        def on_double_click(event):
            # Get the item at the click position
            idx = self.scene_listbox.nearest(event.y)
            if idx >= 0:
                self.scene_listbox.selection_clear(0, tk.END)
                self.scene_listbox.selection_set(idx)
                self.edit_scene_step()
        self.scene_listbox.bind('<Double-Button-1>', on_double_click)

        # === Playback Controls ===
        playback_frame = ttk.LabelFrame(scene_frame, text="Playback", padding="5")
        playback_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=10)

        # Loop checkbox
        self.loop_var = tk.BooleanVar(value=False)
        loop_check = ttk.Checkbutton(playback_frame, text="Loop", variable=self.loop_var, command=self.toggle_loop)
        loop_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Play/Stop buttons
        btn_frame = ttk.Frame(playback_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)

        self.play_btn = ttk.Button(btn_frame, text="Play", command=self.play_scene)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_scene, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Progress label
        self.scene_progress_label = ttk.Label(playback_frame, text="Stopped", font=("Arial", 9))
        self.scene_progress_label.grid(row=2, column=0, columnspan=2, pady=5)

        # === Save/Load Scene ===
        scene_io_frame = ttk.LabelFrame(scene_frame, text="Scene File", padding="5")
        scene_io_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(scene_io_frame, text="Name:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.scene_name_entry = ttk.Entry(scene_io_frame, width=20)
        self.scene_name_entry.grid(row=0, column=1, padx=5, pady=2)
        self.scene_name_entry.insert(0, "my_scene")

        io_btn_frame = ttk.Frame(scene_io_frame)
        io_btn_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(io_btn_frame, text="Save Scene", command=self.save_scene).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_btn_frame, text="Load Scene", command=self.show_load_scene_dialog).pack(side=tk.LEFT, padx=5)

    def refresh_pose_combo(self):
        """Refresh the pose dropdown with saved poses"""
        poses = []
        if self.saved_poses_file.exists():
            with open(self.saved_poses_file, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    poses = list(data.keys())
        self.scene_pose_combo['values'] = poses
        if poses:
            self.scene_pose_combo.current(0)

    def add_scene_step(self):
        """Add a step to the scene"""
        pose_name = self.scene_pose_var.get()
        if not pose_name:
            self.show_message("Error", "Please select a pose!")
            return

        try:
            hold_time = float(self.scene_hold_entry.get())
            if hold_time < 0:
                raise ValueError("hold")
        except ValueError:
            self.show_message("Error", "Invalid hold time!")
            return

        try:
            interp_time = float(self.scene_interp_entry.get())
            if interp_time < 0:
                raise ValueError("interp")
        except ValueError:
            self.show_message("Error", "Invalid interpolation time!")
            return

        # Add to scene steps
        self.scene_steps.append({
            'pose_name': pose_name,
            'hold_time': hold_time,
            'interp_time': interp_time
        })

        # Update listbox
        self.update_scene_listbox()
        print(f"Added step: {pose_name} (hold={hold_time}s, interp={interp_time}s)")

    def remove_scene_step(self):
        """Remove selected step from scene"""
        selection = self.scene_listbox.curselection()
        if not selection:
            self.show_message("Error", "Please select a step to remove!")
            return

        # Convert listbox index to step index (4 lines per step)
        step_idx = selection[0] // 4
        if step_idx >= len(self.scene_steps):
            return

        removed = self.scene_steps.pop(step_idx)
        self.update_scene_listbox()
        print(f"Removed step: {removed['pose_name']}")

    def edit_scene_step(self):
        """Edit the selected step's hold and interp times"""
        selection = self.scene_listbox.curselection()
        if not selection:
            self.show_message("Error", "Please select a step to edit!")
            return

        step_idx = self.listbox_to_step_index(selection[0])
        if step_idx >= len(self.scene_steps):
            return

        step = self.scene_steps[step_idx]

        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Step {step_idx + 1}")
        dialog.geometry("300x180")
        dialog.transient(self.root)
        # Wait for window to be visible before grabbing focus
        dialog.wait_visibility()
        dialog.grab_set()

        # Pose name (read-only)
        ttk.Label(dialog, text=f"Pose: {step['pose_name']}", font=("Arial", 11, "bold")).pack(pady=10)

        # Hold time
        hold_frame = ttk.Frame(dialog)
        hold_frame.pack(pady=5, padx=20, fill=tk.X)
        ttk.Label(hold_frame, text="Hold time (s):", width=15).pack(side=tk.LEFT)
        hold_entry = ttk.Entry(hold_frame, width=10)
        hold_entry.pack(side=tk.LEFT, padx=5)
        hold_entry.insert(0, str(step.get('hold_time', 0.0)))

        # Interp time
        interp_frame = ttk.Frame(dialog)
        interp_frame.pack(pady=5, padx=20, fill=tk.X)
        ttk.Label(interp_frame, text="Interp time (s):", width=15).pack(side=tk.LEFT)
        interp_entry = ttk.Entry(interp_frame, width=10)
        interp_entry.pack(side=tk.LEFT, padx=5)
        interp_entry.insert(0, str(step.get('interp_time', 1.0)))

        def save_changes():
            try:
                new_hold = float(hold_entry.get())
                new_interp = float(interp_entry.get())
                if new_hold < 0 or new_interp < 0:
                    raise ValueError("Negative values not allowed")
            except ValueError:
                self.show_message("Error", "Invalid time values!")
                return

            # Update step
            self.scene_steps[step_idx]['hold_time'] = new_hold
            self.scene_steps[step_idx]['interp_time'] = new_interp
            self.update_scene_listbox()

            # Re-select the edited step
            self.scene_listbox.selection_set(self.step_to_listbox_index(step_idx))
            dialog.destroy()
            print(f"Updated step {step_idx + 1}: hold={new_hold}s, interp={new_interp}s")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)

        # Focus on hold entry
        hold_entry.focus_set()
        hold_entry.select_range(0, tk.END)

        # Bind Enter key to save
        dialog.bind('<Return>', lambda e: save_changes())

    def listbox_to_step_index(self, listbox_idx):
        """Convert listbox selection index to step index (4 lines per step)"""
        return listbox_idx // 4

    def step_to_listbox_index(self, step_idx):
        """Convert step index to listbox index (first line of step)"""
        return step_idx * 4

    def move_step_up(self):
        """Move selected step up in the list"""
        selection = self.scene_listbox.curselection()
        if not selection:
            return

        step_idx = self.listbox_to_step_index(selection[0])
        if step_idx == 0 or step_idx >= len(self.scene_steps):
            return

        self.scene_steps[step_idx], self.scene_steps[step_idx-1] = self.scene_steps[step_idx-1], self.scene_steps[step_idx]
        self.update_scene_listbox()
        self.scene_listbox.selection_set(self.step_to_listbox_index(step_idx-1))

    def move_step_down(self):
        """Move selected step down in the list"""
        selection = self.scene_listbox.curselection()
        if not selection:
            return

        step_idx = self.listbox_to_step_index(selection[0])
        if step_idx >= len(self.scene_steps) - 1:
            return

        self.scene_steps[step_idx], self.scene_steps[step_idx+1] = self.scene_steps[step_idx+1], self.scene_steps[step_idx]
        self.update_scene_listbox()
        self.scene_listbox.selection_set(self.step_to_listbox_index(step_idx+1))

    def clear_scene(self):
        """Clear all steps from scene"""
        if self.scene_steps and self.confirm_dialog("Clear all scene steps?"):
            self.scene_steps = []
            self.update_scene_listbox()
            print("🧹 Scene cleared")

    def update_scene_listbox(self):
        """Update the scene listbox display - multi-line per step"""
        self.scene_listbox.delete(0, tk.END)
        for i, step in enumerate(self.scene_steps):
            # Get values with backwards compatibility
            hold_time = step.get('hold_time', 0.0)
            interp_time = step.get('interp_time', 1.0)

            # Line 1: Step number and pose name
            self.scene_listbox.insert(tk.END, f"{i+1}. {step['pose_name']}")
            # Line 2: Hold time
            self.scene_listbox.insert(tk.END, f"     Hold:   {hold_time:.1f}s")
            # Line 3: Interp time (to next pose)
            self.scene_listbox.insert(tk.END, f"     Interp: {interp_time:.1f}s")
            # Separator line
            self.scene_listbox.insert(tk.END, "   ----------------")

    def toggle_loop(self):
        """Toggle loop mode"""
        self.scene_loop = self.loop_var.get()

    def play_scene(self):
        """Start playing the scene"""
        if not self.scene_steps:
            self.show_message("Error", "No steps in scene! Add poses first.")
            return

        # Verify all poses exist
        if not self.saved_poses_file.exists():
            self.show_message("Error", "No saved poses file found!")
            return

        with open(self.saved_poses_file, 'r') as f:
            poses = yaml.safe_load(f) or {}

        for step in self.scene_steps:
            if step['pose_name'] not in poses:
                self.show_message("Error", f"Pose '{step['pose_name']}' not found!")
                return

        # Start playback
        self.scene_playing = True
        self.current_scene_step = 0
        self.pending_interp_time = 3.0  # First pose: 3 second transition
        self.play_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        print(f"Playing scene with {len(self.scene_steps)} steps (loop={self.scene_loop})")
        self.play_scene_step_interpolate()

    def play_scene_step_interpolate(self):
        """Phase 1: Interpolate to the current pose"""
        if not self.scene_playing:
            return

        if self.current_scene_step >= len(self.scene_steps):
            if self.scene_loop:
                self.current_scene_step = 0
                # Use last step's interp_time for loop back
                self.pending_interp_time = self.scene_steps[-1].get('interp_time', 1.0)
                print("Looping scene...")
            else:
                self.stop_scene()
                print("Scene playback complete!")
                return

        step = self.scene_steps[self.current_scene_step]
        hold_time = step.get('hold_time', 0.0)

        self.scene_progress_label.config(
            text=f"Step {self.current_scene_step + 1}/{len(self.scene_steps)}: {step['pose_name']} (moving)"
        )

        # Highlight current step in listbox (first line of the step)
        listbox_idx = self.step_to_listbox_index(self.current_scene_step)
        self.scene_listbox.selection_clear(0, tk.END)
        self.scene_listbox.selection_set(listbox_idx)
        self.scene_listbox.see(listbox_idx)

        # Load pose data
        with open(self.saved_poses_file, 'r') as f:
            poses = yaml.safe_load(f)

        pose_data = poses[step['pose_name']]
        target_angles = np.array(pose_data['angles'])

        # Set callback for when interpolation completes -> go to hold phase
        self.interp_callback = self.play_scene_step_hold

        # Use pending interp time (from previous step or 0 for first)
        self.interp_time_entry.delete(0, tk.END)
        self.interp_time_entry.insert(0, str(self.pending_interp_time))

        # Start interpolation to this pose
        self.interpolate_to_pose(target_angles, step['pose_name'])

    def play_scene_step_hold(self):
        """Phase 2: Hold at the current pose for hold_time"""
        if not self.scene_playing:
            return

        step = self.scene_steps[self.current_scene_step]
        hold_time = step.get('hold_time', 0.0)
        interp_time = step.get('interp_time', 1.0)

        self.scene_progress_label.config(
            text=f"Step {self.current_scene_step + 1}/{len(self.scene_steps)}: {step['pose_name']} (holding {hold_time:.1f}s)"
        )

        # Store this step's interp_time for the NEXT step's arrival
        self.pending_interp_time = interp_time

        # Move to next step index
        self.current_scene_step += 1

        # Wait for hold_time, then go to next step
        hold_ms = int(hold_time * 1000)
        if hold_ms > 0:
            self.root.after(hold_ms, self.play_scene_step_interpolate)
        else:
            # No hold, go immediately to next step
            self.root.after(50, self.play_scene_step_interpolate)

    def on_scene_step_complete(self):
        """Legacy callback - redirects to hold phase"""
        self.play_scene_step_hold()

    def stop_scene(self):
        """Stop scene playback"""
        self.scene_playing = False
        self.interp_callback = None
        self.pending_interp_time = 0.0
        self.play_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.scene_progress_label.config(text="Stopped")
        self.scene_listbox.selection_clear(0, tk.END)
        print("Scene stopped")

    def save_scene(self):
        """Save current scene to file"""
        scene_name = self.scene_name_entry.get().strip()
        if not scene_name:
            self.show_message("Error", "Please enter a scene name!")
            return

        if not self.scene_steps:
            self.show_message("Error", "No steps in scene to save!")
            return

        # Load existing scenes or create new dict
        if self.saved_scenes_file.exists():
            with open(self.saved_scenes_file, 'r') as f:
                scenes = yaml.safe_load(f) or {}
        else:
            scenes = {}

        # Save scene
        scenes[scene_name] = {
            'steps': self.scene_steps.copy(),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'loop': self.loop_var.get()
        }

        with open(self.saved_scenes_file, 'w') as f:
            yaml.dump(scenes, f, default_flow_style=False, sort_keys=False)

        self.show_message("Success", f"✅ Scene '{scene_name}' saved!")
        print(f"✅ Saved scene '{scene_name}' with {len(self.scene_steps)} steps")

    def show_load_scene_dialog(self):
        """Show dialog to load a saved scene"""
        if not self.saved_scenes_file.exists():
            self.show_message("Info", "No saved scenes found. Save a scene first!")
            return

        with open(self.saved_scenes_file, 'r') as f:
            scenes = yaml.safe_load(f)

        if not scenes:
            self.show_message("Info", "No saved scenes found.")
            return

        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Scene")
        dialog.geometry("400x350")

        ttk.Label(dialog, text="Select a scene to load:", font=("Arial", 12, "bold")).pack(pady=10)

        # Listbox
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        scene_names = list(scenes.keys())
        for name in scene_names:
            num_steps = len(scenes[name].get('steps', []))
            timestamp = scenes[name].get('timestamp', 'N/A')
            listbox.insert(tk.END, f"{name} ({num_steps} steps) - {timestamp}")

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def load_selected():
            selection = listbox.curselection()
            if not selection:
                self.show_message("Error", "Please select a scene!")
                return

            name = scene_names[selection[0]]
            scene_data = scenes[name]
            self.scene_steps = scene_data.get('steps', []).copy()
            self.loop_var.set(scene_data.get('loop', False))
            self.scene_loop = self.loop_var.get()
            self.update_scene_listbox()
            dialog.destroy()
            print(f"📂 Loaded scene '{name}' with {len(self.scene_steps)} steps")

        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                return

            name = scene_names[selection[0]]
            if self.confirm_dialog(f"Delete scene '{name}'?"):
                del scenes[name]
                with open(self.saved_scenes_file, 'w') as f:
                    yaml.dump(scenes, f, default_flow_style=False, sort_keys=False)
                dialog.destroy()

        ttk.Button(btn_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def format_value(self, rad_value):
        deg_value = np.rad2deg(rad_value)
        return f"{rad_value:+.3f} rad ({deg_value:+.1f}°)"

    def update_joint(self, joint_idx, value):
        """Update joint value from slider"""
        self.current_angles[joint_idx] = value
        self.value_labels[joint_idx].config(text=self.format_value(value))

        # Mirror to right side if symmetric mode is enabled and this is a left joint
        if self.symmetric_mode and joint_idx in self.joint_pairs:
            right_idx, flip_sign = self.joint_pairs[joint_idx]
            mirrored_value = -value if flip_sign else value

            # Update right slider (without triggering another update)
            self.sliders[right_idx].set(mirrored_value)
            self.current_angles[right_idx] = mirrored_value
            self.value_labels[right_idx].config(text=self.format_value(mirrored_value))

    def reset_to_default(self):
        """Reset all joints to default angles with interpolation"""
        self.interpolate_to_pose(self.default_angles, "Default Pose")

    def zero_all(self):
        """Set all joints to zero with interpolation"""
        zero_angles = np.zeros(self.num_joints)
        self.interpolate_to_pose(zero_angles, "Zero Pose")

    def interpolate_to_pose(self, target_angles, pose_name="Target Pose"):
        """Generic method to interpolate to any target pose"""
        # Get interpolation time from entry field
        try:
            interp_time = float(self.interp_time_entry.get())
            if interp_time < 0:
                raise ValueError
        except ValueError:
            print("Invalid interpolation time! Using 2.0s")
            interp_time = 2.0

        target = np.array(target_angles)

        # Handle instant transition (interp_time == 0)
        if interp_time <= 0.001:
            # Set pose immediately without interpolation
            for i, angle in enumerate(target):
                self.sliders[i].set(angle)
                self.current_angles[i] = angle
                self.value_labels[i].config(text=self.format_value(angle))
            print(f"Instant move to '{pose_name}'")
            # Call callback if set (used by scene playback)
            if self.interp_callback:
                callback = self.interp_callback
                self.interp_callback = None
                self.root.after(10, callback)  # Small delay to allow UI update
            return

        # Start interpolation
        self.interp_start_angles = self.current_angles.copy()
        self.interp_target_angles = target
        self.interp_duration = interp_time
        self.interp_start_time = time.time()
        self.interpolating = True

        print(f"Interpolating to '{pose_name}' over {interp_time:.1f}s...")

        # Start interpolation loop
        self.interpolation_step()

    def toggle_publishing(self):
        """Toggle publishing on/off"""
        self.publishing = self.publish_var.get()

    def toggle_symmetric(self):
        """Toggle symmetric mode on/off"""
        self.symmetric_mode = self.symmetric_var.get()
        if self.symmetric_mode:
            print("⚖️  Symmetric mode ENABLED: Left joints will mirror to right")
        else:
            print("⚖️  Symmetric mode DISABLED")

    def publish_to_redis(self):
        """Publish current joint angles to Redis"""
        if not self.redis_connected or not self.publishing:
            return

        try:
            # Build mimic_obs format: root_vel_xy(2) + root_pos_z(1) + roll_pitch(2) + yaw_ang_vel(1) + dof_pos(29)
            mimic_obs = np.zeros(35)  # 6 + 29
            mimic_obs[0:2] = [0.0, 0.0]      # root_vel_xy
            mimic_obs[2] = 0.75              # root_pos_z (standing height)
            mimic_obs[3:5] = [0.0, 0.0]      # roll, pitch
            mimic_obs[5] = 0.0               # yaw_ang_vel
            mimic_obs[6:35] = self.current_angles  # dof_pos

            # Publish to Redis
            self.redis_client.set("action_body_unitree_g1_with_hands", json.dumps(mimic_obs.tolist()))

        except Exception as e:
            print(f"Error publishing to Redis: {e}")

    def publishing_loop(self):
        """Background thread for publishing"""
        dt = 1.0 / self.publish_rate
        while True:
            if self.publishing:
                self.publish_to_redis()
            time.sleep(dt)

    def start_publishing(self):
        """Start background publishing thread"""
        self.publishing = self.publish_var.get()
        thread = threading.Thread(target=self.publishing_loop, daemon=True)
        thread.start()

    def save_pose(self):
        """Save current joint configuration to file"""
        pose_name = self.pose_name_entry.get().strip()
        if not pose_name:
            self.show_message("Error", "Please enter a pose name!")
            return

        # Load existing poses or create new dict
        if self.saved_poses_file.exists():
            with open(self.saved_poses_file, 'r') as f:
                poses = yaml.safe_load(f) or {}
        else:
            poses = {}

        # Save current angles with metadata
        poses[pose_name] = {
            'angles': self.current_angles.tolist(),
            'joint_names': self.joint_names,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'description': f"Custom pose: {pose_name}"
        }

        # Write to file
        with open(self.saved_poses_file, 'w') as f:
            yaml.dump(poses, f, default_flow_style=False, sort_keys=False)

        self.show_message("Success", f"✅ Pose '{pose_name}' saved to {self.saved_poses_file}")
        print(f"✅ Saved pose '{pose_name}' with {len(self.current_angles)} joint angles")

    def show_load_dialog(self):
        """Show dialog to select and load a saved pose"""
        if not self.saved_poses_file.exists():
            self.show_message("Info", "No saved poses found. Save a pose first!")
            return

        # Load poses
        with open(self.saved_poses_file, 'r') as f:
            poses = yaml.safe_load(f)

        if not poses:
            self.show_message("Info", "No saved poses found.")
            return

        # Create selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Saved Pose")
        dialog.geometry("500x400")

        # Title
        ttk.Label(dialog, text="Select a pose to load:", font=("Arial", 12, "bold")).pack(pady=10)

        # Listbox with poses
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        # Populate listbox
        pose_names = list(poses.keys())
        for name in pose_names:
            timestamp = poses[name].get('timestamp', 'N/A')
            listbox.insert(tk.END, f"{name} ({timestamp})")

        # Info label
        info_label = ttk.Label(dialog, text="", wraplength=450)
        info_label.pack(pady=5)

        def on_select(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                name = pose_names[idx]
                desc = poses[name].get('description', 'No description')
                info_label.config(text=f"Description: {desc}")

        listbox.bind('<<ListboxSelect>>', on_select)

        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def load_selected():
            selection = listbox.curselection()
            if not selection:
                self.show_message("Error", "Please select a pose!")
                return

            idx = selection[0]
            name = pose_names[idx]
            self.load_pose(name, poses[name])
            dialog.destroy()

        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                self.show_message("Error", "Please select a pose!")
                return

            idx = selection[0]
            name = pose_names[idx]

            if self.confirm_dialog(f"Delete pose '{name}'?"):
                del poses[name]
                with open(self.saved_poses_file, 'w') as f:
                    yaml.dump(poses, f, default_flow_style=False, sort_keys=False)
                dialog.destroy()
                self.show_message("Success", f"Deleted pose '{name}'")

        ttk.Button(btn_frame, text="Load", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def load_pose(self, pose_name, pose_data):
        """Load a saved pose into the GUI with smooth interpolation"""
        angles = np.array(pose_data['angles'])

        if len(angles) != self.num_joints:
            self.show_message("Error", f"Pose has {len(angles)} joints, expected {self.num_joints}")
            return

        # Use generic interpolation method
        self.interpolate_to_pose(angles, f"Saved Pose '{pose_name}'")

    def interpolation_step(self):
        """Perform one step of pose interpolation"""
        if not self.interpolating:
            return

        # Safety check: avoid division by zero
        if self.interp_duration <= 0.001:
            progress = 1.0
        else:
            # Calculate interpolation progress (0.0 to 1.0)
            elapsed = time.time() - self.interp_start_time
            progress = min(elapsed / self.interp_duration, 1.0)

        # Linear interpolation (lerp)
        interpolated_angles = (
            self.interp_start_angles * (1.0 - progress) +
            self.interp_target_angles * progress
        )

        # Update sliders and values
        for i, angle in enumerate(interpolated_angles):
            self.sliders[i].set(angle)
            self.current_angles[i] = angle
            self.value_labels[i].config(text=self.format_value(angle))

        # Check if interpolation is complete
        if progress >= 1.0:
            self.interpolating = False
            print(f"✅ Interpolation complete!")
            # Call callback if set (used by scene playback)
            if self.interp_callback:
                callback = self.interp_callback
                self.interp_callback = None  # Clear to avoid repeated calls
                callback()
        else:
            # Schedule next frame (~60 FPS = 16ms)
            self.root.after(16, self.interpolation_step)

    def show_message(self, title, message):
        """Show a message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")

        ttk.Label(dialog, text=message, wraplength=350, font=("Arial", 10)).pack(pady=20)
        ttk.Button(dialog, text="OK", command=dialog.destroy).pack(pady=10)

        # Center dialog
        dialog.transient(self.root)
        dialog.grab_set()

    def confirm_dialog(self, message):
        """Show a confirmation dialog, return True if confirmed"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirm")
        dialog.geometry("350x120")

        ttk.Label(dialog, text=message, wraplength=300).pack(pady=20)

        result = [False]

        def on_yes():
            result[0] = True
            dialog.destroy()

        def on_no():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Yes", command=on_yes).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="No", command=on_no).pack(side=tk.LEFT, padx=10)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

        return result[0]


def main():
    root = tk.Tk()
    app = JointControllerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
