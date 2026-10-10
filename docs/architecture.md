# Hospital_G1 system architecture

Mermaid source for the architecture diagrams. The same diagrams, with the UnifoLM-WLA assessment and the node
catalogue, are published as the "Hospital G1 Architecture" page. Dashed boxes are planned, not built.

## UnifoLM-WLA in one paragraph

Unitree's 6B vision-language-action model (UnifoLM-ER-1 4B reasoning backbone + MMDiT action expert, Apache-2.0,
github.com/unitreerobotics/unifolm-wla). Inputs: head + wrist cameras, robot state, a sentence. Output: 1 s chunks of
30 actions at 30 Hz in a 54-value space (both end-effector poses, 6 BrainCo finger values per hand, waist, base
vx/vy/yaw rate, height, legs). Trained partly on a G1 with BrainCo hands (`unitree_g1_brainco`; datasets include
Adjust Sickbed, Pick Up Medicine, Make Bed). Fits our stack as the skill layer, driving only in AUTO through a
`wla_bridge` node. Needs a >= 24 GB GPU (12.5 GB weights), wrist cameras, an extended model server (the released one
only speaks the two-finger-gripper action space), our trained student policy with a height input, and a fine-tune on
hospital demonstrations.

## System map: every node, server and device

```mermaid
flowchart LR
  %% ---------------- people and devices ----------------
  subgraph DEV["People and devices"]
    direction TB
    IPAD["iPad controller app<br/>PWA · Clinical / Operator / Technician<br/>Stop · Power off · readback + undo"]
    CONSOLE["Engineering console<br/>browser /console"]
    KB["Keyboard teleop<br/>g1_teleop_keyboard"]
    CAM["OBSBOT Tiny 3 webcam<br/>seated operator"]
    ESTOP["Hardware wireless e-stop<br/>latching, mandatory"]
  end

  %% ---------------- hospital workstation ----------------
  subgraph WS["Hospital-network workstation · ROS 2 Humble · CycloneDDS"]
    direction TB
    UISRV["hospital-sim-ui/server · aiohttp + rclpy<br/>HTTPS/WSS :8443<br/>auth + roles · control lease · alarms<br/>audit log · incidents · 3 s undo"]
    subgraph TELE["Teleoperation"]
      direction TB
      WEBTEL["webcam teleop · xr_teleoperate fork<br/>MediaPipe pose + hands · IK pinocchio<br/>BrainCo retarget · OBSBOT auto-framing"]
    end
    MGR["g1_teleop_manager<br/>mode FSM DAMP STAND LOCO MANIP NAV AUTO HOLD<br/>arbiter · watchdog · e-stop gate · speed zones"]
    subgraph AUTO["Autonomy"]
      direction TB
      MISSION["g1_mission · py_trees<br/>scrub-nurse behaviour tree<br/>skills: GoTo FineAlign Locate Pick Handover"]
      WLAB["wla_bridge node<br/>obs packer · chunk executor 30 Hz<br/>EE pose to IK · fig6d to hand 0..1"]:::planned
      PERC["g1_perception<br/>detector_node YOLO-OBB ONNX<br/>surgeon_hand_node MediaPipe"]
    end
    subgraph NAV["Navigation · g1_navigation"]
      direction TB
      SLAM["slam_toolbox<br/>online async"]
      AMCL["map_server + AMCL"]
      NAV2["Nav2 · planner + MPPI omni<br/>velocity smoother · behaviours"]
    end
    RSP["robot_state_publisher<br/>g1_description URDF"]
  end

  %% ---------------- inference ----------------
  subgraph GPU["Inference GPU ≥ 24 GB · planned"]
    direction TB
    WLASRV["UnifoLM-WLA model server<br/>6B · websocket + msgpack :8600<br/>language + images + state to 1 s action chunk"]:::planned
  end

  %% ---------------- robot ----------------
  subgraph ROBOT["Robot onboard · G1 PC2 or sim"]
    direction TB
    CTRL["g1_controller<br/>whole-body student policy ONNX 50 Hz<br/>PD targets to lowcmd 500 Hz"]
    subgraph SENS["Sensor drivers"]
      direction TB
      LIDAR["Livox MID-360<br/>livox/lidar · scan"]
      HEAD["Head D435i RGB-D<br/>head_camera"]
      WRIST["Wrist cameras L R"]:::planned
      ODOM["Odometry · IMU<br/>odom · tf"]
    end
    HANDS["BrainCo hand service<br/>g1/hand/left right"]
    LOW["Unitree low level · DDS<br/>rt/lowcmd · rt/lowstate<br/>motor drivers PD 500 Hz"]
  end

  subgraph SIMS["Simulators · stand in for the robot"]
    direction TB
    MJ["g1_mujoco_sim · MuJoCo 500 Hz<br/>hospital world · theatre set"]
    IS["g1-isaac-sim · Isaac Sim 6<br/>hospital USD · DDS bridge"]
  end

  %% ---------- device links ----------
  IPAD -- "WSS JSON protocol v2.1" --> UISRV
  CONSOLE -- "WSS" --> UISRV
  KB -- "g1/teleop/key" --> MGR
  CAM -- "USB UVC video + PTZ" --> WEBTEL
  ESTOP -- "g1/estop/heartbeat" --> MGR

  %% ---------- workstation links ----------
  UISRV -- "teleop/key_ui · ui/heartbeat<br/>set_mode · control/lease" --> MGR
  UISRV -- "mission/command<br/>request_instrument" --> MISSION
  UISRV -- "start stop SLAM + Nav2<br/>maps · goals" --> NAV
  MGR -- "g1/mode · lease_state" --> UISRV
  WEBTEL -- "teleop/upper_body_target_raw<br/>teleop/hand cmd_raw" --> MGR
  WEBTEL -- "annotated camera JPEG<br/>tracking_status" --> UISRV
  MISSION -- "NavigateToPose action" --> NAV2
  MISSION -- "auto/upper_body_target<br/>auto/hand cmd" --> MGR
  MISSION -- "instruction + start stop" --> WLAB
  WLAB -- "auto/upper_body_target · auto/hand cmd<br/>auto/cmd_vel + height" --> MGR
  WLAB -- "msgpack observation" --> WLASRV
  WLASRV -- "1 s action chunk" --> WLAB
  PERC -- "perception/detections<br/>surgeon_hand" --> MISSION
  NAV2 -- "g1/cmd_vel_nav" --> MGR
  SLAM --> NAV2
  AMCL --> NAV2

  %% ---------- to the robot ----------
  MGR -- "g1/cmd_vel · upper_body_target<br/>g1/hand cmd · mode" --> CTRL
  MGR -- "g1/hand left right cmd" --> HANDS
  CTRL -- "lowcmd" --> LOW
  LOW -- "lowstate" --> CTRL
  LIDAR --> SLAM
  LIDAR --> AMCL
  LIDAR --> NAV2
  ODOM --> AMCL
  HEAD --> PERC
  HEAD --> WLAB
  WRIST --> WLAB
  CTRL -- "joint_states" --> RSP
  MJ -. "same topics as the robot<br/>lowstate lowcmd scan odom cameras" .- LOW
  IS -. "same topics via DDS" .- LOW

  classDef planned stroke-dasharray: 6 4
```

## Control layers: who decides what, and how fast

```mermaid
flowchart TB
  L5["Mission layer · about 1 Hz<br/>g1_mission behaviour tree<br/>which room, which instrument, which step"]
  subgraph L4["Skill layer · one source at a time"]
    direction LR
    H1["Person · keyboard<br/>cmd_vel"]
    H2["Person · webcam teleop<br/>arm + hand targets 30 Hz"]
    N1["Nav2 · 20 Hz<br/>cmd_vel between rooms"]
    S1["Scripted skills · IK<br/>pick, handover"]
    W1["UnifoLM-WLA · VLA<br/>1 s chunks of 30 actions<br/>server at 2 to 5 Hz"]:::planned
    A1["ACT or Diffusion Policy<br/>imitation-learned skill"]:::planned
  end
  L3["Mode manager · g1_teleop_manager<br/>picks the one source for the current mode<br/>Stop = HOLD and Power off = DAMP always win<br/>watchdog 1 s · speed zones · control lease"]
  L2["Whole-body policy · g1_controller · 50 Hz<br/>student RL policy ONNX, from g1-whole-body-rl/<br/>input cmd_vel, height, upper-body targets, IMU, joints<br/>output 29 joint position targets"]
  L1["Motor layer · 500 Hz<br/>PD torque in Unitree motor drivers<br/>lowcmd, lowstate over DDS"]
  L0["G1 29-DoF + BrainCo Revo2 hands<br/>or MuJoCo / Isaac"]

  L5 --> L4
  H1 --> L3
  H2 --> L3
  N1 --> L3
  S1 --> L3
  W1 --> L3
  A1 --> L3
  L3 --> L2
  L2 --> L1
  L1 --> L0
  L0 -. "state: IMU, joints, cameras, lidar" .-> L2
  L0 -. "images + state" .-> W1

  classDef planned stroke-dasharray: 6 4
```

## Modes: only one thing drives at a time

```mermaid
stateDiagram-v2
  direction LR
  [*] --> DAMP
  DAMP --> STAND: r · ready
  STAND --> LOCO: l · keyboard walking
  LOCO --> STAND: p · pause
  STAND --> MANIP: m · webcam arm teleop
  MANIP --> STAND: n · stop, arms blend back
  STAND --> NAV: g · Nav2 drives
  NAV --> STAND: p
  STAND --> AUTO: mission or iPad · WLA / skills drive
  AUTO --> STAND: p · operator takes over
  LOCO --> HOLD: Stop
  MANIP --> HOLD: Stop
  NAV --> HOLD: Stop
  AUTO --> HOLD: Stop · task paused
  STAND --> HOLD: Stop
  HOLD --> STAND: resume, slide to confirm
  HOLD --> AUTO: continue task
  HOLD --> DAMP: Power off, hold 1.5 s
  note right of HOLD
    Stop = hold still, arms frozen.
    Also entered by the 1 s watchdog
    when the controlling iPad goes silent.
  end note
```

## One instrument request, end to end, with UnifoLM-WLA as the skill

```mermaid
sequenceDiagram
  autonumber
  actor Nurse as Circulating nurse
  participant App as iPad app
  participant UI as hospital-sim-ui/server
  participant M as g1_mission
  participant Nav as Nav2
  participant B as wla_bridge
  participant S as WLA server GPU
  participant Mgr as mode manager
  participant C as g1_controller
  participant R as G1 robot

  Nurse->>App: Request instrument · Needle driver for surgeon
  App->>UI: instrument_request
  UI-->>App: readback card + 3 s undo
  UI->>R: speech · "Needle driver to surgeon, handle first"
  UI->>M: request_instrument after undo window
  M->>Mgr: set_mode AUTO
  M->>Nav: NavigateToPose · theatre_instrument_table
  Nav->>Mgr: cmd_vel_nav 20 Hz
  Mgr->>C: cmd_vel
  C->>R: lowcmd 500 Hz · walk
  Nav-->>M: arrived
  M->>B: instruction · "pick up the needle driver from the rack"
  loop every chunk, about 3 per second
    B->>S: head + wrist images, EE poses, fingers, waist, IMU
    S-->>B: 30 actions · 1 s at 30 Hz
    B->>Mgr: auto/upper_body_target, auto/hand cmd, cmd_vel + height
    Mgr->>C: targets, only while mode is AUTO
    C->>R: balance + track targets
  end
  B-->>M: success · instrument in hand
  M->>B: instruction · "hand the needle driver to the surgeon, handle first"
  Note over B,S: same loop, with the surgeon's hand position from perception
  B-->>M: released
  M->>UI: status · handed, count updated
  UI-->>App: handed list + time
  opt Stop at any moment
    Nurse->>App: Stop
    App->>UI: stop
    UI->>Mgr: HOLD
    Mgr->>C: freeze arms, zero velocity
    Mgr-->>M: paused, resumable
  end
```

## Data and training: how the policies get made

```mermaid
flowchart LR
  subgraph RL["Balance policy · reinforcement learning · g1-whole-body-rl/"]
    direction TB
    MJX["MuJoCo MJX · 2048 envs<br/>G1 + BrainCo model, 35 N·m"]
    TEA["PPO teacher · privileged<br/>Stage A stand · Stage B loco + arm targets"]
    ULT["ULTRA teacher · released weights<br/>motion-tracking expert"]
    STU["Student · CVAE on history<br/>DAgger distillation"]:::todo
    ONNX["policy.onnx + sidecar<br/>ONNX battery 11 scenarios"]
    MJX --> TEA --> STU
    ULT -. "extra expert" .-> STU
    STU --> ONNX
  end

  subgraph DATA["Demonstrations · LeRobot format"]
    direction TB
    TEL["Webcam teleop<br/>MANIP mode, real or Isaac"]
    SCR["Scripted skills in sim<br/>60 episodes recorded"]
    UNI["Unitree WBT BrainCo datasets<br/>Adjust Sickbed, Pick Up Medicine…"]
    MIM["Isaac Lab Mimic<br/>multiply demos"]
    TEL --> MIM
    SCR --> MIM
  end

  subgraph VLA["Skill policy · imitation learning"]
    direction TB
    BASE["UnifoLM-WLA-1.0-Base<br/>6B, Apache-2.0"]
    FT["Fine-tune action expert or LoRA<br/>VLM frozen · one 24 GB GPU"]:::planned
    EVAL["Evaluate in Isaac hospital<br/>success rate per task"]:::planned
    BASE --> FT --> EVAL
  end

  ONNX --> CTRL2["g1_controller on the robot"]
  MIM --> FT
  UNI --> FT
  EVAL --> SRV2["WLA model server"]:::planned
  CTRL2 -. "the student must follow WLA targets<br/>so Stage B trains on them" .- SRV2

  classDef planned stroke-dasharray: 6 4
  classDef todo stroke-width: 3px
```
