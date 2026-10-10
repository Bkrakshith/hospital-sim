# Hospital_G1 to-do

Open work, newest decisions first. Each training item needs the user's go-ahead before it starts.

## Policies

- [ ] **Train the deployable student policy** (`g1-whole-body-rl/`). Distil the privileged teacher (Stage A stand, Stage B
      loco + upper-body teleop) into the history-based student with ULTRA's CVAE recipe (DAgger, teacher labels on
      clean observations, student on noisy history), export ONNX + sidecar, pass the ONNX battery, then replace the
      placeholder Unitree policy in `g1_controller`. This is the controller the real G1 runs; ULTRA's released
      teacher (`g1-whole-body-rl/ultra_eval/`) can serve as an extra expert for motion tracking. Includes the optional
      base-height command (needed by VLA planners such as UnifoLM-WLA and GR00T, which command `height`).
  - [ ] Stage A teacher: stand and stabilise (≈ 7 h on the 3070) — awaiting go-ahead
  - [ ] Stage B teacher: velocity locomotion + upper-body targets (≈ 26 h) — awaiting go-ahead
  - [ ] Student distillation + ONNX export + battery (≈ 3 h per stage)
  - [ ] Decide: stronger standing energy/torque penalty for long standing in theatre
  - [ ] Stage C (ULTRA motion tracking) — data already in `datasets/ultra/`
- [ ] **Instrument detector** (`hospital-sim-perception/`): 20k synthetic frames (≈ 5 h) + YOLO11n-OBB (≈ 9 h) — awaiting go-ahead
- [ ] **UnifoLM-WLA evaluation** (see `docs/architecture.md`): fine-tune / LoRA the action expert on our
      G1 + BrainCo data on a ≥ 24 GB GPU; extend Unitree's model server to the whole-body + dexterous-hand
      (WBT, `fig6d`) action space; add a `wla_bridge` ROS 2 node.

## Mission / manipulation

- [ ] Trocar grasp drops during carry offline (`g1_mission/config/grasp_overrides.yaml`)
- [ ] Adson forceps pick is marginal (1 miss in a long session)
- [ ] Replace sim ground-truth "cheats" with perception (table alignment, instrument poses, surgeon hand)

## Hardware / deployment

- [ ] Wrist cameras on the G1 (UnifoLM-WLA and most VLA data use head + two wrist cameras)
- [ ] Hardware wireless e-stop, robot light and speaker (sim stubs today)
- [ ] Test the iPad app on a real iPad (gloves, VoiceOver, silent switch)
- [ ] Confirm on the real hand: BrainCo thumb motor order (docs vs xr_teleoperate)
