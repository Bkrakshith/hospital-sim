# hospital-sim: layout and interface contract of the G1 teleoperation stack

This file is the contract every part of the build codes against. Change it only
deliberately, and update every consumer when you do.

Decisions: ankle + waist roll/pitch effort limit **35 N·m** (robot model / Unitree 2025-03 limits;
user 2026-09-30: the G1 mainly stands for long periods, no squatting). RL trains with
`effort_source: canonical`. The unitree_rl_gym placeholder policy alone still runs the sim at 50 N·m.

Robot: **Unitree G1 29-DoF rev 1.0** (3-DoF waist, 7-DoF arms) with **BrainCo Revo2**
hands (6 actuated DoF per hand). Chosen by the user on 2026-09-29.
Mode of use: **simulation first, real-ready** (the sim speaks the same low-level
topics as the real robot, so the stack can later point at the real G1).

## 1. Repository layout (each part owns its folder)

| Folder | GitHub repository | Owner / contents |
|---|---|---|
| `hospital-sim-env/isaac/` | hospital-sim-env | Isaac Sim hospital scene: `scene/` (generator, `layout.py`), `usd/` (`hospital_g1.usd`), `assets/`, `renders/`, `launch_isaac.sh`, `i4h_env.sh`. Moved here from the repo root on 2026-09-30 (as `sim/isaac/hospital/`); other components reference it by these paths |
| `hospital-sim-env/objects/` | hospital-sim-env | surgical instruments (meshes, MJCF, USD), `placements.yaml`, `catalog.json` (section 6) |
| `g1-brainco-description/` | g1-brainco-description | canonical G1 29-DoF rev 1.0 + BrainCo Revo2 model: URDF, MJCF, meshes, `SOURCE.md`, build script |
| `g1-whole-body-rl/` | g1-whole-body-rl | MuJoCo / MJX ULTRA-style whole-body controller: envs, configs, training, export (**no training runs yet**) |
| `g1-mujoco-sim/` | g1-mujoco-sim | MuJoCo hospital world generated from `hospital-sim-env/isaac/scene/layout.py`, scene MJCF with the G1 |
| `g1-isaac-sim/` | g1-isaac-sim | G1 placed in the Isaac hospital + Isaac ROS 2 bridge speaking this contract |
| `ros2_ws/src/hospital-sim-ros2/` | hospital-sim-ros2 | ROS 2 Humble packages (section 3); `ros2_ws/` itself is the colcon workspace and stays in the master repository |
| `g1-webcam-teleop/xr_teleoperate/` | g1-webcam-teleop | fork of unitreerobotics/xr_teleoperate with webcam hand/arm tracking input |
| `g1-webcam-teleop/obsbot/` | g1-webcam-teleop | OBSBOT Tiny 3 gimbal control + hand-following auto-framing |
| `hospital-sim-ui/` | hospital-sim-ui | web dashboard (SLAM, navigation, teleoperation) |
| (not in this assembly) | private | instrument detector training. The stack does not depend on it: `g1_perception` runs in `gt` mode in simulation and takes any YOLO-OBB ONNX export through its `model` parameter |
| `docs/` | hospital-sim (master) | design docs, this contract |
| `env.sh` | hospital-sim (master) | `source env.sh` = clean LD path + ROS 2 Humble + `.venv` + ros2_ws overlay |

2026-10-10: folders renamed to match the GitHub repositories; the master repository is hospital-sim.

Python environments:
- `.venv/` (system python 3.10, `--system-site-packages`, so rclpy works): all ROS 2 nodes,
  teleop, UI server. Install with `.venv/bin/pip`. Always `source env.sh` first (conda's
  `LD_LIBRARY_PATH` breaks rclpy otherwise).
- `g1-whole-body-rl/` uses its own conda env `g1-mjx` (JAX/MJX); never mix it into `.venv`.
- Isaac uses `~/isaacsim` python.

GPU memory: when JAX tests and Isaac Sim share one GPU, set `XLA_PYTHON_CLIENT_MEM_FRACTION=0.35` for
the JAX tests. The README of the master repository gives the computer requirements.

## 2. Joint order (Unitree hg, = motor index in LowCmd/LowState)

```
 0 left_hip_pitch   1 left_hip_roll    2 left_hip_yaw   3 left_knee   4 left_ankle_pitch   5 left_ankle_roll
 6 right_hip_pitch  7 right_hip_roll   8 right_hip_yaw  9 right_knee 10 right_ankle_pitch 11 right_ankle_roll
12 waist_yaw       13 waist_roll      14 waist_pitch
15 left_shoulder_pitch 16 left_shoulder_roll 17 left_shoulder_yaw 18 left_elbow 19 left_wrist_roll 20 left_wrist_pitch 21 left_wrist_yaw
22 right_shoulder_pitch ... 28 right_wrist_yaw   (same order as left)
```
Joint names in URDF/MJCF are `<name>_joint` (for example `left_hip_pitch_joint`). Actuators 0 to 28
follow this order in every MJCF. **qpos order:** `g1_29dof_brainco_fixedhands.xml` has
`qpos[7:36]` in this order; the full `g1_29dof_brainco.xml` follows the kinematic tree, so the
left-hand joints sit between `left_wrist_yaw` and `right_shoulder_pitch`. Never slice
`qpos[7:36]` on the full model: index by name or use `body_joint_qposadr` / `dofadr` from
`g1-brainco-description/g1_29dof_brainco/robot_spec.json`.

BrainCo Revo2 hand, 6 DoF per side, order: `thumb, thumb_aux (rotation), index, middle, ring, pinky`.
Commands are **normalised 0 (open) .. 1 (closed)**.

## 3. ROS 2 packages (`ros2_ws/src/hospital-sim-ros2/`)

| Package | Contents |
|---|---|
| `third_party/unitree_ros2` msgs | `unitree_hg`, `unitree_go`, `unitree_api` message packages only (vendored from unitreerobotics/unitree_ros2) |
| `g1_interfaces` | `msg/Mode` (incl. `HOLD=6`), `srv/SetMode`, `srv/RequestInstrument`, `srv/ControlLease` |
| `g1_description` | installs `g1-brainco-description/` URDF+meshes, `robot_state_publisher` launch |
| `g1_mujoco_sim` | MuJoCo sim node: consumes `/lowcmd`, publishes `/lowstate`, sensors, ground-truth odom |
| `g1_controller` | policy runner (ONNX + JSON sidecar) → `/lowcmd`; stand / damp / locomotion / upper-body tracking |
| `g1_teleop_manager` | mode FSM + command arbiter (the only thing that decides who drives the robot); control lease, UI heartbeat watchdog, hardware e-stop interlock, speed zones (3.4) |
| `g1_teleop_keyboard` | terminal keyboard node → `/g1/teleop/key`, `/g1/cmd_vel_teleop` |
| `g1_navigation` | slam_toolbox + Nav2 config and launches for the G1 |
| `g1_bringup` | top-level launches: `sim.launch.py`, `teleop.launch.py`, `slam.launch.py`, `nav.launch.py`, `dashboard.launch.py`, `all.launch.py` |

### 3.1 Topics

Low level (identical names/types to the real G1 through unitree_ros2 / CycloneDDS):

| Topic | Type | Pub → Sub | Rate |
|---|---|---|---|
| `/lowstate` | `unitree_hg/msg/LowState` | sim (or real robot) → controller | 500 Hz |
| `/lowcmd` | `unitree_hg/msg/LowCmd` | controller → sim (or real robot) | 500 Hz |

Hands:

| Topic | Type | Notes |
|---|---|---|
| `/g1/hand/left/cmd`, `/g1/hand/right/cmd` | `sensor_msgs/JointState` | position = 6 values 0..1 (order above); arbiter output |
| `/g1/hand/left/state`, `/g1/hand/right/state` | `sensor_msgs/JointState` | from sim / BrainCo service |

Teleop and arbitration:

| Topic | Type | Pub → Sub |
|---|---|---|
| `/g1/teleop/key` | `std_msgs/String` (one key per msg, lower-case) | keyboard node → manager (identity `keyboard`); camera teleop node keys c f h u |
| `/g1/teleop/key_ui` | `std_msgs/String` JSON `{"key","holder"}` | UI server → manager (manager keys with the device identity `ui:<device_id>`) |
| `/g1/cmd_vel_teleop` | `geometry_msgs/Twist` | keyboard node, UI → manager |
| `/g1/cmd_vel_nav` | `geometry_msgs/Twist` | Nav2 (remapped from `cmd_vel`) → manager |
| `/g1/teleop/upper_body_target_raw` | `sensor_msgs/JointState` | camera teleop (xr fork) → manager; names = waist + 14 arm joints |
| `/g1/teleop/hand/{left,right}/cmd_raw` | `sensor_msgs/JointState` | camera teleop → manager |
| `/g1/teleop/camera/annotated/compressed` | `sensor_msgs/CompressedImage` (jpeg) | camera teleop → UI |
| `/g1/teleop/tracking_status` | `std_msgs/String` (JSON: `{"hands_visible":[bool,bool],"arms_visible":[..],"fps":..,"framing":"tracking|searching|off"}`) | camera teleop → UI, manager |
| `/g1/mode` | `g1_interfaces/Mode` (transient-local QoS) | manager → all |
| `/g1/teleop/manager_status` | `std_msgs/String` JSON (1 Hz + on change): mode, source, detail, cmd_vel, last_key, last_message, `hold` {since, source, from, reason}, `blending`, `lease`, `watchdog`, `estop` {ok, alive, pressed, age, dev_override, reason}, `motion_locked` [reasons], `zone` {name, cap}, `manual_cap`, `events` | manager → UI |
| `/g1/cmd_vel` | `geometry_msgs/Twist` | manager → controller (zero unless mode LOCO, NAV or AUTO; speed-zone capped) |
| `/g1/upper_body_target` | `sensor_msgs/JointState` | manager → controller (only in MANIP / AUTO and during the blend back to default; else absent → controller holds default arms; ignored in HOLD) |
| `/g1/controller/status` | `std_msgs/String` (JSON: policy name, placeholder?, fall detected, loop Hz) | controller → UI |

Perception / navigation (sim publishes these; on the real robot they come from the Livox MID-360 driver + an odometry node):

| Topic | Type |
|---|---|
| `/livox/lidar` | `sensor_msgs/PointCloud2` (MID-360 on the head, frame `mid360_link`) |
| `/scan` | `sensor_msgs/LaserScan` (2-D slice for slam_toolbox, frame `mid360_link` or `laser_link`) |
| `/odom` | `nav_msgs/Odometry` (`odom` → `pelvis`) |
| `/tf` | `map → odom` (slam/AMCL), `odom → pelvis` (sim/odometry), robot links (robot_state_publisher from `/joint_states`) |
| `/joint_states` | `sensor_msgs/JointState` (29 body + 12 hand joints, from sim/controller) |
| `/clock` | sim time (`use_sim_time:=true` for everything when running the sim) |

### 3.2 Modes (`g1_interfaces/msg/Mode`)

```
uint8 DAMP=0     # motors damped ("power off"; start state; fall)
uint8 STAND=1    # policy balancing in place, zero velocity, default arms  (= "locomotion paused")
uint8 LOCO=2     # keyboard locomotion teleop
uint8 MANIP=3    # camera upper-body + hand teleop; legs hold stance, cmd_vel forced 0
uint8 NAV=4      # Nav2 drives cmd_vel
uint8 AUTO=5     # mission/skills drive: Nav2 cmd_vel + /g1/auto/* arm & hand targets
uint8 HOLD=6     # "Stop": zero velocity, arms frozen where they are, hands keep their command, task paused,
                 # still balancing; left only by an explicit resume
uint8 mode
string source    # who: keyboard, ui:<device_id>, mission, safety, watchdog, estop_hw, lease, nav
string detail
```
`srv/SetMode`: request `uint8 mode, string source`; response `bool accepted, string message`.

**Only one of LOCO / MANIP / NAV / AUTO can be active.** Legal transitions:
DAMP→STAND, STAND→{LOCO, MANIP, NAV, AUTO, DAMP}, LOCO→STAND, MANIP→STAND, NAV→STAND, AUTO→STAND, any→DAMP.
AUTO is requested by the mission executive (source `mission`) or the UI; `p` returns to STAND (operator
override) and aborts the running mission step.
LOCO→MANIP directly is **rejected**: the operator must pause locomotion first.
Leaving MANIP blends arms back to the default pose over ~1 s before STAND reports ready.
Fall detected by the controller → DAMP (source `safety`).

**HOLD ("Stop", added 2026-09-30, docs/ui/README.md decision 1).** Any mode except DAMP → HOLD, from any source, also
during an arm blend (the blend stops where it is). In HOLD the manager forwards nothing (`fsm.FORWARD`): cmd_vel 0,
no arm or hand targets. The controller keeps the policy balancing and freezes the upper body at the **measured** pose
at the moment HOLD arrives (joints whose command is moving: set-point = measured q + its low-passed static PD offset;
joints whose command is still keep it; upper-body kd ×2.5 while held, so a moving arm brakes in ~0.3 s; measured
drift 0.006-0.011 rad over 3 s after a stop at 0.17-0.26 rad/s, MuJoCo). Hands keep their
last command. The mission pauses (resumable) and cancels its Nav2 goal; the UI server pauses its own Nav2 goal. Leaving
HOLD only by an explicit resume: HOLD → STAND (arms blend from the frozen pose to default over `hold_blend_time`
2.5 s, skipped when already within 0.05 rad) or HOLD → AUTO (only when the robot was in AUTO when stopped, source
`mission`/`ui`: the paused mission continues). HOLD → DAMP always. HOLD → LOCO/MANIP/NAV is rejected. HOLD requested
in DAMP is accepted as a no-op. Leaving HOLD any other way than → AUTO aborts a paused mission.
Why a mode and not "STAND + detail": the arms-frozen / arms-at-default difference, the explicit-resume rule, the
watchdog and the red "Stopped" state must be visible to the controller, the mission, every UI and the audit log from
one field, and STAND must stay "safe to start a new motion from".
DAMP stays as the "power off" control (the UI labels it "Power off robot: it will sink to the floor").

### 3.3 Key bindings (defaults, in `g1_teleop_manager/config/keys.yaml`)

| Key | Action |
|---|---|
| `r` | ready: DAMP → STAND |
| `l` | start locomotion teleop (STAND → LOCO) |
| `w` / `s` | forward / backward (LOCO only) |
| `a` / `d` | strafe left / right |
| `q` / `e` | turn left / right |
| `space` | zero velocity |
| `p` | pause locomotion (LOCO → STAND) |
| `m` | start upper-body camera teleop (STAND → MANIP) |
| `n` | stop upper-body teleop (MANIP → STAND) |
| `g` | hand over to navigation (STAND → NAV); `p` returns to STAND |
| (UI / mission only) | STAND → AUTO; `p` returns to STAND |
| `o` | **Stop**: any → HOLD (arms frozen, task paused) |
| `r` | also HOLD → STAND (explicit resume; arms blend to rest ≥ 2 s) |
| `x` | power off: any → DAMP (developer e-stop; the robot sinks) |

Velocity limits (defaults): vx ∈ [-0.5, 0.8] m/s, vy ∈ [-0.4, 0.4] m/s, wz ∈ [-1.0, 1.0] rad/s,
key step 0.1 / 0.1 / 0.2, command times out to zero after 0.5 s without a key. `p` does **not** resume a stop
(HOLD needs `r` or a UI resume).

### 3.4 Control lease, UI heartbeat watchdog, hardware e-stop, speed zones (added 2026-09-30)

All in `g1_teleop_manager` (authoritative; pure logic in `safety.py`), config `keys.yaml` `safety:` + `zones.yaml`.

| Name | Type | Notes |
|---|---|---|
| `/g1/control/lease` | `g1_interfaces/srv/ControlLease` (`op` acquire\|release\|steal\|renew\|query, `holder`, `role`, `display`, `reason` → `ok`, `message`, `holder`, `role`, `display`, `expires_in`) | one holder at a time; steal needs a reason; a steal while in LOCO/MANIP → HOLD (source `lease`) |
| `/g1/control/lease_state` | `std_msgs/String` JSON, transient-local | `{holder, role, display, held_for, expires_in, implicit, reason, heartbeat}` |
| `/g1/ui/heartbeat` | `std_msgs/String` JSON `{"holder","seq"}` | UI server → manager, ≥ 5 Hz for the lease holder; renews the lease |
| `/g1/estop/heartbeat` | `std_msgs/Bool`, 10 Hz | hardware wireless e-stop receiver: `true` = released/healthy, `false` = pressed. Sim/mock stub in `g1_mujoco_sim/stubs.py` (`/sim/estop` SetBool presses it, `/sim/estop_link` kills it) |
| `/g1/indicator/light` | `std_msgs/String` JSON `{"colour","pattern"}` (latched) | UI server → robot light: red flash_2hz (High alarm), amber pulse_0.6hz (Medium), cyan steady (Low), else by mode (red steady HOLD, magenta LOCO/MANIP, blue NAV/AUTO, white STAND, off DAMP). Sim: log-only stub |
| `/g1/speech/say` | `std_msgs/String` | UI server → robot speaker (readbacks, "Stopped", alarms). Sim: log-only stub |

Rules:
- **Lease.** While a lease is held only its holder may enter LOCO/MANIP/NAV (SetMode source `ui:<device_id>` or
  `keyboard`) or send velocity keys; `mission` (the robot's own executive) and the safety sources are not gated.
  Stop (HOLD) and power off (DAMP) are accepted from everyone. Entering LOCO/MANIP with the lease free takes an
  **implicit** lease for the requester (terminal keyboard, v1 console), dropped when manual motion ends. Leases lapse
  after `lease_ttl` 30 s without heartbeat/renew.
- **Watchdog.** In LOCO/MANIP, if the holder is a UI device (`ui:*`) and its `/g1/ui/heartbeat` is older than
  `heartbeat_timeout` 1.0 s → HOLD (source `watchdog`). Measured trip 0.92 s (sim). The terminal keyboard is exempt.
- **Hardware e-stop.** LOCO/MANIP/NAV/AUTO are refused while `/g1/estop/heartbeat` is missing (> 0.5 s) or pressed
  ("motion locked"); pressed → HOLD (source `estop_hw`), resume refused until released; heartbeat lost while moving →
  HOLD. DAMP → STAND stays allowed. DEV override: node param `DEV_ONLY_ignore_estop_heartbeat:=true` (reported as
  `estop.dev_override` in manager_status and shown by the UI).
- **Arms hold inside MANIP.** `/g1/teleop/arms_hold` (String JSON `{"on","holder"}`, UI server → manager; lease
  rule): the manager stops forwarding the camera-teleop arm/hand streams and publishes `/g1/arms_hold` (Bool,
  transient-local) → the controller freezes the arms exactly as in HOLD while the mode stays MANIP. Cleared by any mode
  change. `manager_status.arms_hold`.
- **Gripper override.** `/g1/teleop/hand_override` (String JSON `{"side","close","holder"}`) → `/g1/hand/<side>/cmd`
  with all six DoF = `close`; accepted only in HOLD or in MANIP with arms held (else the camera stream owns the
  hands), lease rule; `manager_status.hand_override` / `hand_override_allowed`.
- **Speed zones.** `zones.yaml`: polygons in the map frame with `max_speed`; the planar speed of `/g1/cmd_vel` is
  scaled down to the cap while TF map→pelvis is inside (first match); `manual_cap` applies in LOCO everywhere.

## 4. Policy artefacts (`g1-whole-body-rl/` → `g1_controller`)

`g1-whole-body-rl/exports/<policy_name>/policy.onnx` + `policy.json` sidecar:
```json
{ "name": "...", "control_dt": 0.02, "sim_dt": 0.002,
  "joint_names": [29 names in section 2 order], "controlled_joints": [indices the policy outputs],
  "default_qpos": [29], "action_scale": ..., "kp": [29], "kd": [29], "torque_limit": [29],
  "obs": [{"name": "...", "dim": N, "scale": s}, ...], "history_len": H,
  "commands": {"cmd_vel": [3], "upper_body_target": [17] }, "placeholder": false }
```
`g1_controller` must build the observation from the sidecar only (no hard-coded layout). Until a
trained policy exists it runs a **placeholder**: Unitree's pre-trained G1 12-DoF locomotion policy
(`~/ntu_dev/unitree_rl_gym/deploy/pre_train/g1/motion.pt`, converted to ONNX + sidecar with
`"placeholder": true`), with waist/arms held by PD at the default or `/g1/upper_body_target`.

## 5. Ports

| Port | Service |
|---|---|
| 8443 | UI server HTTPS + WSS: iPad app at `/`, engineering console at `/console/` (hospital-sim-ui/PROTOCOL.md v2) |
| 8080 | UI server plain HTTP, bound to 127.0.0.1 when TLS is set up (localhost development) |

## 6. Autonomy: missions, skills, perception (added 2026-09-30)

Scrub-nurse mission = behaviour tree in `ros2_ws/src/hospital-sim-ros2/g1_mission` driving skills through the same command
topics teleop uses, so recorded teleop / scripted demos are directly imitation-learning data.

In mode **AUTO** the manager forwards:

| Input (mission/skills) | → Output |
|---|---|
| `/g1/cmd_vel_nav` (Nav2) | `/g1/cmd_vel` |
| `/g1/auto/upper_body_target` (`sensor_msgs/JointState`, waist 3 + 14 arm joints) | `/g1/upper_body_target` |
| `/g1/auto/hand/{left,right}/cmd` (`sensor_msgs/JointState`, 6 × 0..1) | `/g1/hand/{left,right}/cmd` |

Mission interfaces (`g1_interfaces`):

| Name | Type | Notes |
|---|---|---|
| `/g1/mission/request_instrument` | `srv/RequestInstrument` (`string instrument, string requester` → `bool accepted, string message`) | UI / voice → mission |
| `/g1/mission/command` | `std_msgs/String` (`start`, `abort`, `pause`, `resume`, `goto:<location>`) | UI → mission |
| `/g1/mission/status` | `std_msgs/String` JSON `{"state","step","instrument","tree":[{name,status}],"message"}` (+ `paused_by_hold`; `history[]` entries carry `t`, unix s) | mission → UI |
| `/g1/perception/detections` | `std_msgs/String` JSON `[{"label","score","bbox_obb":[cx,cy,w,h,angle],"pose":{"frame","xyz","yaw"}}]` | perception → mission |
| `/g1/perception/surgeon_hand` | `geometry_msgs/PoseStamped` | perception → handover skill |
| `/sim/objects` | `std_msgs/String` JSON `{name: {"pose":[x,y,z,qw,qx,qy,qz], "type"}}` in `map`/world frame | **ground truth**, sim only; step-1 "cheat" source for object poses |
| `/g1/head_camera/{image_raw,depth,camera_info}` | `sensor_msgs/Image`, `CameraInfo` | sim head RGB-D (D435i, frame `d435_link`) |

Mission and HOLD: AUTO → HOLD pauses the mission (skills frozen, Nav2 goal cancelled, `paused_by_hold`); `resume`
on `/g1/mission/command` then requests HOLD → AUTO and continues; leaving HOLD to STAND/DAMP aborts it.

Named locations: `ros2_ws/src/hospital-sim-ros2/g1_mission/config/locations.yaml` (map frame; display names, icons and allowed roles in
`hospital-sim-ui/server/config/places.yaml`): `theatre_instrument_table`,
`theatre_surgeon_side`, `sterile_store`, `corridor_west`, …
Instrument set (step 1): whatever meshes exist (i4h AngledTweezers, PneumoperitoneumNeedle, Trocar, scissors
from the i4h scissor workflow) + clearly-labelled procedural stand-ins (scalpel handle, forceps, needle driver)
held upright in a **tool rack** on the instrument table.
Until the Stage B policy exists, arm skills are developed with the sim's **fixed-base option** (pelvis welded),
because the placeholder policy falls on large reaches.
