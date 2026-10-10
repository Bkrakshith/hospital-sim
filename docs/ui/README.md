# G1 iPad controller: UI research and design brief

Research and design brief for the iPad web app that ships with the Unitree G1 as its controller in the surgical wing: corridors, pre-op, PACU, sterile store, scrub room and operating theatre. It is for **end users and debugging**, covering navigation and limited functionality, with **"Teach a new task" as the next feature**. It builds on the existing G1 Console (`hospital-sim-ui/`), which is an engineering dashboard in the style of Seirios RNS. This brief turns that console into a clinical product.

| File | What it contains |
|---|---|
| [01_precedents.md](01_precedents.md) | 22 precedent systems: hospital robots, operator apps, surgical robots, clinical apps. Patterns to adopt and avoid. |
| [02_standards_and_deployment.md](02_standards_and_deployment.md) | Requirement → source → design rule (IDs S-, U-, A-, L-, P-, I-, X-, D-). What applies, what is conditional, what is analogy only. Singapore / US / EU. |
| [03_human_factors.md](03_human_factors.md) | Theatre stressors (interruptions, noise, light, gloves, handovers, mode confusion, trust, alarm fatigue) and rules HF-1…HF-41 |
| [04_user_groups_and_requirements.md](04_user_groups_and_requirements.md) | **Core map**: 12 user groups, permissions, feature × role matrix (MVP / later), information architecture, flows F1–F8, alarm model, upcoming Teach flow, backend gaps, success metrics |
| [05_design_direction.md](05_design_direction.md) | Principles, typography from viewing distance, CVD-checked colour tokens (light + theatre dim), status semantics, glove targets, grids for 11"/13", motion, iPad Safari sound/haptics limits |

> **Deployment country is not fixed.** Singapore rules (HSA, PDPA, CSA CLS(MD), public-cluster IT) are listed next to FDA/HIPAA and EU MDR/GDPR/Machinery Regulation. Choose the jurisdiction and get a formal regulatory determination (medical device or not) before any theatre trial. Until then, **design as if regulated**.

## The 15 decisions the app must implement

1. **Two stops, never one.** **Stop** = hold: cancel the task, zero velocity, **freeze the arms where they are**, keep standing. **Power off** = DAMP, and the robot sinks to the floor; it is a hold-to-confirm control labelled as such. A humanoid is not safe when unpowered (ISO 25785-1 draft; Digit uses a Category 1 stop; Unitree damping "slowly falls"). This needs a backend change: today `estop` = DAMP, and leaving MANIP blends the arms, which is motion during a handover. (`02` S-1, `04` F5)

2. **The iPad is not the emergency stop.** A touchscreen cannot meet ISO 13850, so there is no red-on-yellow e-stop styling. A **hardware latching wireless e-stop is mandatory**, and motion modes stay locked until its heartbeat is seen in the start-up check. (`02` S-2)

3. **Stop is on every screen, in the same place, for every role.** It sits in a fixed **safety rail**, is ≥ 88 pt, needs one tap with no confirmation, fires on `pointerdown`, and is never covered by anything. It works from every connected iPad regardless of who holds control. **Resume** needs a slide-to-confirm that states what will happen, and it never resumes on its own. (`02` S-3, S-4)

4. **One controller at a time (control lease), plus a comms watchdog.** One device holds manual control and others observe. Taking control is explicit and logged. If the controlling iPad goes silent for > 1 s in LOCO/MANIP, the robot drops to STAND and holds. Manual motion is hold-to-move with zone speed caps. (`02` S-5…S-7)

5. **Three role modes behind badge/PIN, enforced on the server.**
   - **Clinical** (default, walk-up-and-use): Send to…, Request instrument, Come here, Dock, Stop.
   - **Operator**: map, routes, manual walking, camera arm teleop, missions.
   - **Technician**: diagnostics, mapping, logs, audit, calibration.

   Roles drop back automatically when idle. The WebSocket must become **WSS with authenticated sessions and a per-role op allow-list**. (`04` §3, §5; `02` L-3/L-4)

6. **Plain-language modes in two safety families.** "The robot is driving" (NAV/AUTO) is **blue**. "A person is driving" (LOCO/MANIP) is **magenta with stripes and a hand icon**. Standing by is slate and powered down is grey. Raw FSM names appear only for technicians. Every mode change says **who changed it** (from the `/g1/mode` `source` field). (`03` HF-17, HF-18)

7. **Goal buttons, not transition buttons.** The user taps "Use arms", and the app shows and runs the legal path (LOCO → STAND → MANIP). It does not reject and toast. The robot never starts a motion the app did not show as "Next". (`03` HF-16, HF-19)

8. **Status first, readable from across the room.**
   - The hero card answers *now · OK? · next* at 44/34/22 pt.
   - After 20 s idle the **across-room view** takes over at 88 pt (2 m legibility per MIL-STD-1472).
   - The first tap only wakes the screen.

   (`03` HF-15, HF-21; `05` §2)

9. **IEC 60601-1-8 alarm language, by analogy.**
   - High = red flashing 2 Hz; Medium = amber 0.6 Hz; Low = cyan steady.
   - **Red and flashing are reserved for danger.**
   - Every alarm says *what · do · who*, can be acknowledged by anyone, and cannot be disabled by clinical users.
   - The budget is **< 1 non-actionable alarm per case**.
   - The robot's own speaker and light are the primary alarm channel, because iPad audio is unreliable. (`02` A-1…A-5; `04` §7)

10. **Closed-loop requests with undo.** Send-to and instrument requests show a **readback card**, which the robot speaks too ("Needle driver → surgeon, handle first"), with a 3-s Undo. There is no "urgent instrument" button: urgent requests stay with the human scrub nurse. Handed instruments are logged for the count. (`03` HF-3, HF-6, HF-8; `04` F3)

11. **Glove-first, CVD-safe visual system.**
    - Clinical targets ≥ 64 pt; tiles 144 pt; no precision gestures.
    - Every state is colour + icon + word, because red vs green and blue vs violet collapse under deuteranopia (checked by simulation; ~5% of Singapore Chinese males are affected).
    - Themes: **Light** and **Theatre dim**, with no white flashes. (`05` §3–§5, §10)

12. **Sterile-field and hygiene rules built in.**
    - The iPad is non-sterile and mounted ≥ 1 m from the table. Scrub staff and the surgeon never touch it; they use the robot (voice/gesture) and the across-room view.
    - A **Clean screen** mode gives a 30-s touch lock.
    - End-of-shift cleaning (robot pose + checklist) is logged. (`02` I-1…I-3; `04` F7)

13. **Privacy by default.**
    - Cameras are live-only: no recording in Clinical, blurred in PACU/pre-op, and a REC indicator on every device when recording.
    - **No patient data anywhere in the app.**
    - Analytics are by role and room, not by named nurse. (`02` P-1…P-4)

14. **Hospital-grade deployment.**
    - Supervised iPads via MDM in Single App Mode, preferably through a thin WKWebView wrapper.
    - Hospital-CA TLS, a dedicated device VLAN with **no internet egress** (this blocks the G1's vendor telemetry), and BLE provisioning off (UniPwn).
    - Wake Lock on during motion; audio unlocked at sign-in with `audioSession = 'playback'`.
    - An append-only audit log of every command. (`02` L-5, L-6, D-1…D-5)

15. **Handover-proof and debuggable.**
    - A guided **start-of-day check** (nurse part ≈ 60 s, including pressing Stop).
    - A **handover card** at shift change.
    - **"Send problem to technician"** builds an incident bundle: the last 5 min of modes, commands, alarms, versions and pose, with no PHI. The technician should not have to reproduce the fault.
    - **Teach a new task** (upcoming) runs: define → demonstrate (teleop) → curate → train → sim test scorecard → supervised dry run → **two-person approval** (author ≠ approver) → versioned, frozen publish. (`04` F1, F6, F8, §9)

## Backend work implied (not in this folder's scope)

The rules above need these changes to the robot contract (`docs/interfaces.md`): hold-stop distinct from DAMP with the arm freeze; a UI heartbeat and watchdog; a control lease service; authenticated WSS and a per-role op allow-list; an audit log; named places with display metadata; an instrument catalogue with rack counts; a hardware e-stop heartbeat; keep-out, quiet and speed zones; an incident ring buffer; and robot indicator light and speech topics. See `04` §10.

## Status of this brief

Written 2026-09-30 from desk research. It has not yet been tested with users. The next step is formative testing of the Clinical flows (F2, F3, F5) with 5+ theatre nurses: gloved, in dim light, with noise playback and interruptions (`02` U-1, U-2).
