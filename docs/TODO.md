# Hospital_G1 to-do

Open work, newest decisions first. Each training item needs the user's go-ahead before it starts.

## Policies

- [ ] Instrument detector (separate private repository): 20k synthetic frames (about 5 h) and YOLO11n-OBB training (about 9 h), awaiting go-ahead
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
- [ ] Confirm on the real hand: BrainCo thumb motor order (docs vs xr_teleoperate)
