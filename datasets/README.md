# datasets/

This folder holds recorded data, not source code. Git ignores the large folders. The table below
lists the folders and their contents.

| Folder | What |
|---|---|
| `lerobot_scrub/` | 60 LeRobot-format episodes (8,626 frames) of the scripted scrub-nurse mission in MuJoCo, fixed-base, recorded 2026-10-01 at 640×480 head RGB (before the switch to 640×360). State 29-D, action 32-D, layout in `ros2_ws/src/hospital-sim-ros2/g1_mission/README.md`. Scripted demos, usable as seed data for imitation learning. |
| `mission_trial_results/` | Per-trial results and logs from the mission verification runs. |
