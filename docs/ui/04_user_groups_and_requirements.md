# 04 — User groups, requirements and information architecture

**This is the core map for building the iPad app.** It covers who uses it, what each group must see and do (and must not be able to do), which features ship in the MVP, how the screens are organised, the key flows, the alarm model, and the upcoming "Teach a new task" feature.

Inputs: `01_precedents.md`, `02_standards_and_deployment.md` (rule IDs S-, U-, A-, L-, P-, I-, X-, D-), `03_human_factors.md` (rule IDs HF-n), and the robot contract in `docs/interfaces.md` + `hospital-sim-ui/PROTOCOL.md`.

## 1. Product definition in one paragraph

An iPad web app, delivered with the robot and served by the robot, that lets **theatre staff** use the G1 for simple jobs (go there, bring that, stop, go home), lets **operators** drive it manually and run navigation and missions, and lets **technicians** diagnose and fix it. It is calm and glanceable: it answers "what is it doing, is that OK, what next" from across a theatre. It never gets in the way of patient care, never pretends to be the emergency stop, and never stores patient data. *Upcoming:* teaching the robot a new task by demonstration.

## 2. User groups

### 2.0 Overview

| # | User group | App mode | Uses the iPad? | Frequency | Gloved | Distance | Priority |
|---|---|---|---|---|---|---|---|
| U1 | **Circulating nurse / theatre staff** | Clinical | Yes, primary | Many short touches per case, daily | Often (non-sterile nitrile) | 0.5 m to touch, 1–3 m to glance | **Primary** |
| U2 | Scrub nurse | – (via robot) | No (sterile) | Continuous during case | Sterile, double | 1–2 m from robot; iPad out of reach | Secondary (indirect) |
| U3 | Surgeon | – (glance / voice) | No | Occasional glance | Sterile | 2–4 m | Secondary (indirect) |
| U4 | Anaesthetist / anaesthesia nurse | Clinical (observer) | Rarely | Occasional | Sometimes | 1–3 m | Stakeholder with stop authority |
| U5 | **Remote / seated teleoperator** | Operator | Yes (with desk setup) | Sessions of 5–30 min | No | 0.5 m | Primary for manipulation |
| U6 | **Robot operator on the ward** (porter, robot associate) | Operator | Yes, handheld or robot-mounted | Daily, many trips | Sometimes | 0.3–0.5 m, walking | Primary for navigation |
| U7 | **Biomedical / clinical engineer, robotics technician** | Technician | Yes, plus laptop | Daily check; on call | No | 0.5 m | Primary for debugging |
| U8 | Hospital IT / security | – (admin console) | No (desktop) | Onboarding, audits | No | desk | Stakeholder |
| U9 | OR / facility manager | Manager view (desktop or iPad read-only) | Occasionally | Weekly | No | desk | Stakeholder (buyer) |
| U10 | Infection prevention & control (IPC) | – (checklists, reports) | Rarely | Audits | – | – | Stakeholder (gatekeeper) |
| U11 | Patients and visitors | – (bystanders) | Never | Incidental | – | 1–5 m from robot | Protected party |
| U12 | Task author / researcher (NTU team) | Technician + Teach | Yes, plus workstation | Development | No | 0.5 m | Primary for "Teach" (upcoming) |

### 2.1 U1 — Circulating nurse / theatre staff (primary end user)

| Aspect | Requirement |
|---|---|
| **Goals** | Get items and instruments without leaving the room. Keep the scrub nurse supplied. Keep the robot out of the way. Stop it instantly if something is wrong. Hand over cleanly at shift change. |
| **Context of use** | Non-sterile, in theatre and corridors. iPad on a mount at the theatre door or IV-pole, ≥ 1 m from the sterile field. Noise 50–75 dB(A) with peaks. Light bright or dim (laparoscopy). Interrupted ~10–16 times per hour. |
| **Frequency** | Every case: 5–20 interactions of < 10 s each, plus start-of-day and end-of-day checks. |
| **Gloved** | Often (single nitrile). No sterile gloves on the iPad. |
| **Distance** | Touches at 0.5 m; glances from 1–3 m (across-room view, HF-21). |
| **Must see** | Robot activity in words; OK / needs you / stopped; where it is (room, not coordinates); what happens next and when; who controls it; battery as "enough for ~2 h"; any alarm with what to do. |
| **Must be able to do** | Send to a named place; request an instrument or item (on behalf of the surgeon or scrub); **Stop**; Resume (slide); Come here; Go to dock; acknowledge an alarm; "Send problem to technician"; screen clean mode; switch theme; start-of-day check (guided); end-of-shift handover card. |
| **Must NOT be able to do** | Manual walking or arm teleop (unless also trained as Operator); edit maps, locations, speeds or zones; start SLAM; change calibration; view logs or topic data; record camera video; disable or suppress alarms; power the robot off except with the hold-to-confirm Power-off (allowed, see S-1). |
| **Errors to prevent** | Sending the robot to the wrong theatre (every location tile shows the room name and a photo; Theatre 1 vs 2 differ in colour stripe and number); requesting the wrong instrument (pictures + readback + undo); mistaking "Stop" for "Cancel task" (different words, places and colours); believing the robot stopped when it only paused the task; not noticing that another device took control. |
| **Success metrics** | Send-to-place ≤ 3 taps and ≤ 5 s (HF-1); first-time users complete send/stop without help ≥ 90%; zero wrong-destination sends in formative testing; SUS ≥ 80; ≤ 1 non-actionable alarm per case; weekly active nurses per theatre (utilisation). |

### 2.2 U2 — Scrub nurse (indirect)

| Aspect | Requirement |
|---|---|
| Goals | Receive the right instrument, handle-first and in the agreed zone, without breaking sterility; have the robot fetch from the store or rack while they stay at the field. |
| Context | Sterile; hands busy; interacts with the **robot** (voice, gesture, neutral zone), never the iPad. |
| Must see (on robot / across-room view) | "Ready for request" vs "Busy fetching"; which instrument it is holding (spoken readback + large text on across-room view); arm motion about to start (light + "Arm moving"). |
| Must be able to do | Say "Robot, stop" / "wait"; request by name (future voice); ask the circulator to request on the iPad (MVP). |
| Must NOT | Touch the iPad; be handed sharps directly by the robot (neutral zone only, HF-29). |
| Errors to prevent | Wrong instrument; instrument delivered into the field from the non-sterile side; arm entering the field unannounced. |
| Success | Readback matches request 100%; zero sterility breaches attributable to the robot; scrub-nurse NASA-TLX not worse than baseline. |

### 2.3 U3 — Surgeon (indirect, glanceable)

| Aspect | Requirement |
|---|---|
| Goals | Instruments available without waiting or looking away; the robot invisible until needed. |
| Must see | Only the across-room view and robot speech: "Bringing needle driver — 30 s". |
| Must be able to do | Voice (relayed by circulator in MVP); "Robot, stop". |
| Must NOT | Be asked to confirm anything on a screen. |
| Success | Surgeon never needs to repeat a request due to robot misunderstanding; no request waits > stated ETA + 50%. |

### 2.4 U4 — Anaesthesia team (observer with stop authority)

Can read the across-room view, press **Stop** on any iPad, and say "Robot, stop". No other rights. Needs the robot never to block access to the patient's head end, airway trolley or anaesthesia machine. **Keep-out zones** around them are a technician-configured map layer, and the app shows them.

### 2.5 U5 — Remote / seated teleoperator

| Aspect | Requirement |
|---|---|
| Goals | Precisely control arms and hands (MANIP) or walk the robot (LOCO) when autonomy cannot; record demonstrations (upcoming Teach). |
| Context | Seated, OBSBOT camera framing their hands, iPad beside or in front (or laptop for keyboard). May be outside the theatre, so situational awareness of the room is limited. |
| Frequency | Sessions of 5–30 min; several per week. |
| Must see | Robot-side camera large; proximity strip (people/objects within 1 m); own-hand tracking quality (left/right, confidence); latency; control lease holder; current mode and speed caps; workspace limits (arm approaching joint limit); "who is near the robot" via room camera if installed. |
| Must be able to do | Take control (lease); enter LOCO / MANIP via goal buttons (HF-19); hold-to-move joystick with speed cap; calibrate / re-centre / auto-framing (c/h/f); gripper open/close override; pause arms (hold); hand control back; start/stop recording (with REC indicator, P-1). |
| Must NOT | Exceed zone speed caps; enter MANIP with latency > 500 ms or tracking lost; move arms while another device holds the lease; record without the indicator; bypass the robot-side proximity slow-down. |
| Errors to prevent | Arm drift when tracking is lost (hold instead); mirror confusion (own camera image is shown mirrored like a mirror, robot view un-mirrored, both labelled); forgetting to release control (auto-release after 2 min idle with warning at 90 s); mode error (walking while thinking the arms are active). |
| Success | Task completion time; interventions per session; zero unintended contacts; operator NASA-TLX; tracking dropouts shown within 200 ms. |

### 2.6 U6 — Robot operator on the ward (portering / navigation)

| Aspect | Requirement |
|---|---|
| Goals | Move the robot between wing areas; handle lifts and doors; recover when stuck; create and run routes. |
| Context | Walking with the robot among beds, patients and visitors; iPad handheld (portrait) or on the robot's back mount. |
| Must see | Map with robot, path, next waypoint, blockages; "waiting for: …" sentence; ETA; battery range; zone (quiet zone in PACU/pre-op). |
| Must be able to do | Everything in Clinical, plus: Go to point on map; waypoint routes (run, pause, resume, cancel); set initial pose / relocalise; manual walking (LOCO) with hold-to-move; "Follow me" (later); switch map (named, not raw file). |
| Must NOT | Start SLAM mapping, delete maps, edit keep-out zones or speeds (technician). |
| Errors to prevent | Wrong initial pose (show laser scan overlay match score before confirming); leaving the robot in LOCO unattended (watchdog, S-7); sending a goal into a keep-out zone (rejected with reason). |
| Success | Trips completed without intervention (%); mean time to recover when stuck; relocalisations per day. |

### 2.7 U7 — Biomedical / clinical engineer and robotics technician

| Aspect | Requirement |
|---|---|
| Goals | Daily readiness check; diagnose faults fast; restore service; maintain maps, locations, zones, calibration, software; produce incident reports. |
| Context | Workshop and on-call in theatre. iPad plus laptop; hardware keyboard likely. |
| Must see | Everything: FSM mode + source; controller status (policy name, placeholder flag, loop Hz, fall flag); joint temperatures and hottest joint; battery/BMS; topic ages; stacks (SLAM/Nav2) state; network posture (VLAN, egress blocked, BLE off, cert expiry); versions; logs; audit log; incident bundles. |
| Must be able to do | Everything the Operator can; start/stop SLAM; save/load/delete maps; edit named locations, keep-out zones and speed zones; calibrate; restart stacks; suppress a Low alarm class for the session; export incident bundle; stage software update (not during scheduled sessions); run self-tests. |
| Must NOT | Silently disable High alarms; change safety limits beyond the signed-off configuration without a second technician (two-person rule for speed/force limit changes); update software while a theatre session is scheduled. |
| Errors to prevent | Editing the live map during navigation; deleting the only map; leaving a debug suppression on (suppressions expire at session end and show a chip). |
| Success | Mean time to diagnose; % of faults diagnosed from the incident bundle alone; readiness check < 5 min. |

### 2.8 U8 — Hospital IT / security

Goals: device on the right network, no internet egress, authentication tied to hospital identity, patchable, auditable, SBOM available. Needs an **admin console** (desktop web, not the theatre iPad) for users/roles/badges, device enrolment (iPad ↔ robot pairing), certificates, audit-log export, and network posture. In Singapore public healthcare, device onboarding goes through the cluster/Synapxe process. Expect questions shaped by the SingHealth COI (segmentation, admin accounts, logging). The app must never ask the nurse to accept a certificate warning.

### 2.9 U9 — OR / facility manager

Goals: know whether the robot is worth it; plan its use; see incidents. Needs a read-only **Insights** view: trips per theatre per day, minutes of walking saved (estimate), success rate per location, interventions, alarms per case (and non-actionable ones), uptime, Mean Time Between Incidents (Agility Arc KPI), and adoption by role, not by person (P-4). Weekly email/PDF optional (later).

### 2.10 U10 — Infection prevention & control

Goals: robot and iPad cleaned per policy; sterile field respected. Needs: cleaning checklist records (who, when, which wipe) exportable; robot "cleaning pose" (arms out, hands open) available from the app; guidance on which surfaces may be wiped with what; zone rules (the robot does not enter the sterile field; its hand enters only the defined handover zone).

### 2.11 U11 — Patients and visitors (bystanders)

Not users of the app, but the app must protect them: quiet mode in PACU/pre-op (HF-36), cameras blurred by default there, robot self-announcement (HF-37), slower speeds near beds, and no recording without consent (P-1).

### 2.12 U12 — Task author / researcher (upcoming Teach)

Records demonstrations via teleop, curates them, runs sim tests, and submits a task for approval. Needs Technician rights plus the Teach workspace (§8). Cannot approve their own task for clinical use (separation of duties).

## 3. App modes, roles and sign-in

| App mode | Who | How to enter | Auto-exit | Look |
|---|---|---|---|---|
| **Clinical** (default) | U1, U4, anyone at the mount | Badge tap or 4-digit ward PIN; in theatre kiosk the app opens straight into Clinical for the configured room | Never exits; locks to "tap to wake" after 2 min idle | Largest type, fewest choices, plain words |
| **Operator** | U5, U6 (trained) | Personal badge or 6-digit PIN | Back to Clinical after 10 min idle or on "Done" | Adds map tools, manual control, missions |
| **Technician** | U7, U12 | Personal badge + PIN (2 factors) | Back to Clinical after 5 min idle | Dense, monospace values, FSM names, logs |
| **Manager / Admin** | U8, U9 | Desktop browser, hospital SSO later | – | Not on the theatre iPad |

The **current role is always visible** in the status bar ("Clinical · Theatre 1" / "Operator · R. Kumar" / "Technician · …"). Leaving a higher mode is one tap ("Done"). Role checks are enforced on the server (L-3).

## 4. Global UI chrome (every screen, every mode)

```
┌────────────────────────────────────────────────────────────────────────────┬───────────┐
│ STATUS BAR  Room · Role/name · Robot battery ~2 h · Link ●●●○ · 10:42        │  SAFETY   │
├────────────────────────────────────────────────────────────────────────────┤   RAIL    │
│ MODE RIBBON  [icon] Going to Theatre 1 · 8 m · ~40 s     Controlled by: Robot│ ┌───────┐ │
├────────────────────────────────────────────────────────────────────────────┤ │ STOP  │ │
│                                                                            │ └───────┘ │
│                                                                            │  Control: │
│                       SCREEN CONTENT                                       │  this iPad│
│                                                                            │  Alarms (1)│
│                                                                            │  ─────── │
│                                                                            │  Power off│
│                                                                            │  (hold)   │
└────────────────────────────────────────────────────────────────────────────┴───────────┘
```

- **Safety rail** (right edge in landscape, bottom band in portrait; mirror option): **Stop** (≥ 88 pt, red, steady, one tap), control-lease indicator ("Control: this iPad / iPad OR-2 / Robot / nobody"), alarm counter, and **Power off** (small, hold 1.5 s). It is never covered (S-3).
- **Mode ribbon**: colour family (blue = robot driving, violet = person driving, slate = standing by, grey = powered down, red band = stopped/alarm), icon, sentence, and who is in control (HF-17, HF-18).
- **Status bar**: room/zone, role, robot battery as time remaining, link quality, clock, theme toggle (sun/moon), sound state (speaker icon; tap = sound check).
- **Alarm banner** (when present): full-width under the ribbon, priority-coded (A-1), always with what to do and an Acknowledge button.

## 5. Feature × role matrix

Legend: **D** = can do · **C** = can do with deliberate confirm (slide / hold / PIN) · **V** = view only · **–** = hidden. MVP = first build; **L** = later.

| Feature | Clinical U1/U4 | Operator U5/U6 | Technician U7/U12 | Manager U8/U9 | Release |
|---|---|---|---|---|---|
| **Stop (hold)** | D | D | D | – | MVP |
| Resume after stop | C | C | C | – | MVP |
| Power off (DAMP) | C (hold) | C (hold) | C (hold) | – | MVP |
| Status hero + across-room view | D | D | D | V | MVP |
| Send to named place | D | D | D | – | MVP |
| Come here / Go to dock | D | D | D | – | MVP |
| Cancel current task | D | D | D | – | MVP |
| Request instrument (scrub-assist mission) | D | D | D | – | MVP (sim first) |
| Mission view (stepper, pause/resume/abort) | V + pause/abort | D | D | V | MVP |
| Acknowledge alarm | D | D | D | – | MVP |
| Suppress Low alarm class (session) | – | – | C | – | L |
| Send problem to technician (incident bundle) | D | D | D | V | MVP |
| Start-of-day check (guided) | D (nurse part) | D | D (full) | V | MVP |
| End-of-shift handover card + clean mode | D | D | D | V | MVP |
| Take control (lease) | – | C | C | – | MVP |
| Manual walking (LOCO, joystick, hold-to-move) | – | C | C | – | MVP |
| Manual arms (MANIP, camera teleop) | – | C | C | – | MVP |
| Camera calibrate / re-centre / framing | – | D | D | – | MVP |
| Map: go to point, set heading | – | D | D | – | MVP |
| Map: initial pose / relocalise | – | D | D | – | MVP |
| Waypoint routes: run / pause / resume | V | D | D | – | MVP |
| Routes: create / save / delete | – | D | D | – | MVP |
| SLAM mapping, save / delete map | – | – | C | – | MVP (exists) |
| Named locations, keep-out & speed zones | – | V | C (two-person for speed) | V | L |
| Live camera view | blurred thumbnail | D | D | – | MVP |
| Record video / demonstrations | – | C (REC indicator) | C | – | L |
| Diagnostics (controller, joints, battery, topics, stacks) | – | summary | D | – | MVP (exists) |
| Logs (/rosout, launch) | – | – | D | – | MVP (exists) |
| Audit log | – | – | V | V | MVP |
| Network posture card | – | – | V | V | L |
| Software versions / update | – | – | V / C | V | L |
| Insights (utilisation, reliability) | own shift card | own shift card | V | D | L |
| Users, roles, badges, device pairing | – | – | – | D | L |
| **Teach a new task** (record → review → sim → submit) | – | record only (C) | D | – | **Upcoming** |
| Approve task for clinical use | – | – | – (separate approver) | D (clinical lead + technician) | **Upcoming** |

## 6. Information architecture

### 6.1 Screen map

```
Lock / Wake ── Across-room view (auto after 20 s idle)
   │
   ├── CLINICAL
   │     Home ─┬─ Send to… (place tiles)
   │           ├─ Request instrument (tiles → readback → progress)   [when scrub-assist active]
   │           ├─ Robot status (plain-language details, battery, last events)
   │           ├─ Alerts (active + today)
   │           ├─ Checks (start-of-day nurse part, end-of-shift handover, clean mode)
   │           └─ Help (30-s clips)
   │
   ├── OPERATOR (adds)
   │     Map ─┬─ Go to point · Routes · Relocalise · Zones (view)
   │     Drive (LOCO joystick, hold-to-move, speed cap)
   │     Arms (MANIP: robot view + own-hand PiP + proximity strip + gripper)
   │     Missions (scrub assist: start / stepper / pause / abort; queue)
   │
   ├── TECHNICIAN (adds)
   │     Diagnostics (controller · joints/temps · battery · topics · stacks · network)
   │     Mapping (SLAM start/stop, save) · Maps & places (edit) · Calibration
   │     Logs · Audit · Incidents (bundles) · Software · About (versions)
   │     Teach (upcoming)
   │
   └── MANAGER / ADMIN (desktop): Insights · Users & badges · Devices · Audit export
```

**Navigation model.** A **left rail** (5 items maximum per mode, icons + labels, 88 pt wide) in landscape and a **bottom tab bar** in portrait. Clinical has only: **Home, Places, Instruments (contextual), Status, Help**. Deep screens push from the right with a large "Back". **No hamburger menus, no nested tabs.** The current page's name also sits in the mode ribbon for screenshots and incident reports.

### 6.2 Key screens

**Clinical Home (landscape, 11")**
1. **Hero status card** (left 7 columns): mode-family colour band; status word ("OK", "Needs you", "Stopped") with icon at 44 pt; activity sentence at 28–34 pt; "Next: …" at 22 pt; progress bar with ETA when moving; mini floor plan of the wing (rooms as shapes, robot as a dot, not a SLAM occupancy grid).
2. **Primary actions** (right 5 columns, 2 × 2 tiles, 144 × 144 pt): *Send to…*, *Request instrument* (only when scrub-assist is active in this theatre, otherwise *Bring item*), *Come here*, *Go to dock*. Disabled tiles say why ("Robot is charging — 20 min to ready").
3. **Timeline strip** (bottom): the last 3 events in words, e.g. "10:31 Arrived Theatre 1 · 10:33 Handed Mayo scissors".

**Send to…**: grid of place tiles with photo, room name, number stripe and ETA from the current position. Tap → robot starts, readback for 3 s with **Undo**, and the Home hero shows progress. Places come from `locations.yaml` with display names, photos and allowed roles (e.g. "Theatre 1 — surgeon side" is Operator-only).

**Request instrument**: tiles with photo + name + count available on the rack (from perception / sim ground truth), grouped as in the tray layout. A requester chip ("For: Surgeon / Scrub nurse") defaults to Surgeon. Tap → readback card ("Mayo scissors → surgeon, handle first") + **Undo** for 3 s → mission stepper (Fetch → Grasp → Carry → Present → Released).

**Robot status**: plain-language sections: Power (time left), Location (room), Health ("All systems OK" or a list), Control (who), Today (trips). Technician adds raw values.

**Across-room view**: black (dim theme) or white card; status word + icon at 88–120 pt; activity at 56 pt; next step at 40 pt; progress arc; Stop still on the rail.

**Operator → Arms (MANIP)**: robot head-camera view (≥ 60% of the screen); proximity strip across the top (distance bars left / centre / right, turns amber < 1 m, red < 0.5 m, and the robot slows); own-hand PiP bottom-left with tracking rings (L/R); latency pill; gripper open/close buttons (64 pt); "Hold arms" (pause); lease indicator; REC indicator when recording.

**Operator → Drive (LOCO)**: joystick (220 pt, hold-to-move, spring return), turn slider or dual-stick option, speed cap selector (Slow 0.2 / Normal 0.3 / technician-unlocked Fast 0.5 m/s), map mini-view, forward camera. Hardware keyboard (w/a/s/d/q/e/space) works when "Keyboard" is on.

**Technician → Diagnostics**: today's dashboard content (controller, joints, battery, topics, stacks), tidied into cards with thresholds and sparkline history; "Copy for incident".

## 7. Alarm and notification model

Priorities follow IEC 60601-1-8 by analogy (A-1…A-5). Channels: **robot** (status light + speaker + speech), **iPad** (banner + sound on the controlling device), **timeline** (always).

| Class | Visual (iPad) | Audio | Robot | Latching | Who can acknowledge | Escalation |
|---|---|---|---|---|---|---|
| **High** | Red banner, **flashing 2 Hz** (50% duty) in the banner only; ribbon turns red; across-room view shows the alarm | High pattern (10-pulse burst), repeats until acknowledged | Red light flashing; speech "Robot alarm: …" | Yes | Any role | Unacknowledged 30 s → all connected iPads + technician on-call notification (later: Vocera/pager integration) |
| **Medium** | Amber banner, flashing 0.6 Hz | Medium pattern (3 pulses), repeats every 30 s | Amber pulsing light; one spoken phrase | No (clears when resolved) | Any role (silences 2 min) | Unresolved 3 min → High if a task is time-critical, else notify Operator/Technician |
| **Low** | Cyan steady chip in the status bar + banner collapsed to one line | Single soft tone, **once** (not in theatre-quiet: silent) | Cyan steady | No | Any role | None; appears in shift handover card |
| **Info** (not an alarm) | Timeline entry; transient toast 3 s max | None | None / optional short earcon for task completion | – | – | – |

### 7.1 Condition catalogue (initial)

| Condition | Class | Message (what / do / who) |
|---|---|---|
| Fall detected (controller → DAMP, source safety) | High | "Robot has fallen. Keep clear. Call technician." |
| Unexpected contact / collision detected | High | "Robot touched something at left arm. It has stopped. Check the area." |
| Arm moving and person within 0.3 m outside the handover zone | High | "Arm stopped — person too close." |
| Hardware e-stop pressed | High (latched) | "Emergency stop pressed on remote. Release it when safe, then Resume." |
| Robot link lost > 2 s during NAV/AUTO | Medium | "Lost contact with robot. It will stop. Check Wi-Fi / move closer." |
| Controlling iPad heartbeat lost (manual) → STAND | Medium | "Manual control lost. Robot is holding still." |
| Stuck/blocked > 30 s (NAV) | Medium | "Robot is waiting — path blocked at Scrub door. Clear the path or tap Help." |
| Localisation uncertain (AMCL σ > 0.5 m) | Medium | "Robot is unsure where it is. Operator: relocalise." |
| Instrument not found on rack / grasp failed twice | Medium | "Can't pick Mayo scissors. Hand it to the scrub nurse manually." |
| Battery < 15% during task | Medium | "Battery low — finishing this task, then docking." |
| Joint temperature high (> threshold) | Medium → High at hard limit | "Right knee hot. Robot will stand still to cool." |
| Placeholder policy loaded (sim/dev) | Low (tech only) | "Development policy running." |
| Battery < 30% idle | Low | "Charge soon (~40 min left)." |
| Camera frames stale > 2 s (when not in MANIP) | Low | "Robot camera paused." |
| Task completed, arrival | Info | "Arrived at Theatre 1." (arrival chime: once, robot side) |
| Mode changed by another source | Info (Low if motion starts) | "Now: Going to Dock — started by iPad OR-2." |

### 7.2 Budget and hygiene rules

- Every alarm text has **what happened · what to do · who**. No codes in Clinical (the code is shown in Technician).
- **< 1 non-actionable alarm per theatre case**, tracked in Insights; any alarm type with > 20% "acknowledged without action" is reviewed.
- **Theatre-quiet**: during a case, Low and Info are silent; Medium plays on the robot only if the robot is in the theatre, else on the iPad.
- The iPad cannot guarantee sound (see `05` §7), so the **robot's speaker is the primary audible channel**.

## 8. Key user flows

Notation: **User** action → *System* response. [ ] = failure branch.

### F1 — Morning start-up and checks (technician + nurse, ~5 min)

1. Technician powers the robot on the gantry/stand. *iPad (docked at theatre door) shows "Robot starting — 45 s" with a progress ring.*
2. Technician signs in (badge + PIN) → **Checks → Start-of-day**. *Automatic checks run and tick in a list:* link quality ≥ 3 bars; hardware e-stop heartbeat OK (**test: press and release it, the app must see it**); battery ≥ 80% or "time left ≥ 4 h"; controller loop OK, non-placeholder policy; joints within temperature; lidar and cameras streaming; map loaded + localisation OK (scan-match score); network posture OK; date/time synced; software version as approved.
   [Any fail → red item with fix instructions; motion modes stay locked; "Send to technician" creates the incident.]
3. **Stand-up test**: technician slides "Stand up" → DAMP → STAND; *app shows "Standing by" and the robot says "Ready".* Robot takes one step forward and back (optional test pattern).
4. Nurse part (Clinical, ~60 s): *app asks three yes/no questions with big buttons:* "Instrument rack loaded and in place?", "Robot path to the theatre clear?", "Stop control understood? (tap the Stop button now)". The nurse taps Stop → *robot holds, app shows "Stopped by you — that's right"* → Resume slide.
5. *App records the check (who, when, results) and shows "Ready for today" on the Home hero.* The robot goes to its standby spot (Send to: "Theatre 1 standby").

### F2 — Send robot to the theatre (nurse, ≤ 5 s)

1. Nurse taps the iPad (wakes to Home; the first tap does not act, HF-21).
2. **Send to…** → tile **Theatre 1**.
3. *Readback card: "Going to Theatre 1 · ~2 min" with Undo (3 s).* The robot says "Going to Theatre 1".
4. *Hero: blue family, "Going to Theatre 1", progress, "Next: waits at standby spot".* After 20 s the across-room view appears.
   [Robot in manual mode by another device → tile disabled with "Operator R. Kumar is driving — ask them or Take control".]
   [Blocked > 30 s → Medium alarm "path blocked at …"; options: *Wait*, *Try another way*, *Cancel*.]
5. Arrival → Info "Arrived", single chime on the robot; hero returns to "Standing by at Theatre 1".

### F3 — Request an instrument (circulator on behalf of surgeon; scrub-assist mission active)

Precondition: mission "Scrub assist — Theatre 1" started by an Operator (Missions → Start) or by the nurse from Home ("Start scrub assist" tile, which appears when the robot is at Theatre 1 standby and the rack check passed).

1. Surgeon: "Needle driver." Scrub nurse or circulator relays.
2. Nurse taps **Request instrument** → tile **Needle driver** (photo, "2 on rack"). Requester defaults to Surgeon.
3. *Readback card (44 pt): "Needle driver → surgeon, handle first" + Undo 3 s.* The robot says "Needle driver, coming." (HF-6). Calls `/g1/mission/request_instrument` with `requester`.
4. *Mission stepper:* Walk to rack ✓ → Find instrument ✓ → Grasp (in progress) → Carry → Present to scrub zone → Wait for take → Release → Return.
   *Across-room view:* "Bringing needle driver · ~25 s".
   [Grasp fails twice → Medium "Can't pick needle driver — hand it manually" + options *Retry*, *Skip*, *Operator take over (arms)*.]
   [Surgeon's hand not detected in the handover zone for 20 s → robot holds the pose; Info "Waiting for hand"; after 60 s it returns the instrument to the rack.]
5. Release → Info "Handed needle driver 10:52" (timeline entry, for the count record, HF-3). The robot returns to "Ready for request".
6. Cancel at any time before grasp = clean cancel. After grasp → "Put it back" (the robot returns it to the rack).

### F4 — Take over manually

**F4a Manual walking (Operator)**
1. Operator signs in → **Drive**. If the robot is in NAV/AUTO: *"Take over? Robot will stop its task and stand still. Slide to take control."*
2. Slide → *NAV/AUTO → STAND (task paused and remembered) → lease acquired → LOCO.* Ribbon turns violet: "Manual walking — R. Kumar".
3. Hold joystick to move (released = zero). Speed cap shown. Hardware keyboard optional.
   [Heartbeat lost > 1 s → STAND, Medium alarm on this device when it reconnects.]
4. **Done** → LOCO → STAND → *"Resume the paused task 'Going to Theatre 1'?"* (slide) or *"Leave standing"*.

**F4b Manual arms / camera teleop (Operator, seated)**
1. **Arms** → pre-flight: tracking both hands ✓, latency < 250 ms ✓, calibrated ✓ (else "Calibrate: stand with arms relaxed, tap Calibrate"), proximity clear ✓.
2. Goal button **Use arms** → if walking, the app runs LOCO → STAND → MANIP with the sequence shown (HF-19). Ribbon violet: "Manual arms — R. Kumar".
3. The robot view dominates; the proximity strip slows arms automatically near people.
   [Tracking lost → arms hold, banner "Hands not visible — arms holding"; resumes when tracking returns and the operator taps **Continue**.]
4. **Hold arms** (pause) keeps the pose. **Finish** → *"Arms will return to rest over 1 s — area clear?"* (slide) → MANIP → STAND.

### F5 — Stop, power-off and recovery

1. **Anyone** taps **Stop** (any iPad, any role; or says "Robot, stop"; or presses the hardware e-stop).
2. *Server immediately:* cancels Nav2 goal / pauses mission step / zeroes cmd_vel / **freezes arms in place** / mode → STAND (hold). *All iPads:* red ribbon "Stopped by Nurse Tan (iPad OR-1) 10:42". Robot light red steady; robot says "Stopped".
3. *App asks (non-blocking, dismissible):* "Why? — Person in the way · Wrong task · Robot behaving oddly · Other". The reason goes into the audit log.
4. Recovery options on the hero:
   - **Resume** "Continue to Theatre 1 (12 m)" → slide.
   - **Cancel task** → robot stays standing.
   - **Send to technician** (if "behaving oddly").
5. **Power off** (hold 1.5 s, label "Robot will sink to the floor"): → DAMP. *High alarm latched: "Robot powered down by …"*. Recovery requires the technician to stand it up (F1 step 3). The Clinical role cannot stand the robot up from DAMP (it needs a gantry or supervision).
6. Hardware e-stop: same as 5 plus "Release the e-stop when safe"; Resume is disabled until released.

### F6 — Fault → handover to technician

1. Medium/High alarm, or the nurse feels something is wrong.
2. **Send problem to technician** (on alarm banner, Status page, or after Stop).
3. *App builds the incident bundle* (HF-14): last 5 min of mode changes with sources, commands with user/device, alarms, controller status, joint temps, battery, pose + map name, versions, network status, optional 10-s de-identified camera clip (only if recording is permitted in this zone). No PHI.
4. Nurse adds one tap of context (chips: "Stuck", "Fell", "Wrong place", "Wrong instrument", "Noise/smell", "Other") and optionally a 10-s voice note (later).
5. *Sent → incident ID shown ("INC-0930-07"), the technician's device notified;* the hero shows "Technician notified 10:44 — robot holding".
6. Technician opens **Incidents → INC-0930-07** and sees the timeline replay (mode ribbon history, map track). They take control (lease) or instruct the nurse through Clinical actions only.
7. Technician closes the incident with a cause category; the manager's Insights counts MTBI.

### F7 — End-of-shift cleaning and docking

1. Nurse or operator: **Checks → End of shift**.
2. *Handover card:* trips today, instruments handed, open alarms/incidents, battery, anything suppressed, next scheduled use. **Share** shows it big for a verbal handover (15 s read, HF-15).
3. **Go to dock** → robot walks to the dock (or to the gantry/stand for a technician to power down; G1 docking depends on hardware).
4. **Robot cleaning pose** (Operator/Tech): robot at dock, arms out, hands open, mode STAND then DAMP on the stand. *App shows the surfaces to wipe and the approved agent.* Checklist: hands, forearms, torso front, head, handles. Tick → logged (who/when).
5. **iPad clean mode**: 30-s touch lock with countdown (Stop is still reachable with a 2-s long-press) → wipe → done → logged.
6. Sign out → Clinical lock screen.

### F8 — Control transfer and shift handover mid-case

1. The relieving circulator signs in on the same iPad (badge tap). *App shows the handover card first* (what the robot is doing, open requests, who holds control), then Home.
2. If the outgoing user held a lease (Operator), the app asks them to **Hand over control to …** (tap) or release. Lease transfers are logged.

## 9. Upcoming: Teach a new task (clearly marked as not in MVP)

**Goal:** a trained operator teaches the G1 a new, bounded task by demonstration, and a clinical lead and a technician approve it before anyone can run it in a clinical area. Models: Spot Autowalk (record → replay, supervised), BrainOS teach-and-repeat, Figure/Tesla demonstration curation. EU 2023/1230 treats self-evolving behaviour as high-risk, so approved behaviour must be **versioned and frozen** (rule T-1).

```
 1 Define ──► 2 Demonstrate ──► 3 Review & curate ──► 4 Train ──► 5 Test in sim ──► 6 Dry-run on robot ──► 7 Approve ──► 8 Publish
 (Tech)        (Operator,          (Task author)        (offline,    (auto test suite,   (empty theatre,          (Clinical lead +   (appears as a
               teleop)                                    workstation) scorecard)          supervised)             Technician, 2 people) tile for roles)
```

| Step | Screen | What the user does | Gate to next step |
|---|---|---|---|
| 1 Define | Teach → New task | Name, purpose sentence, start and end location, objects involved (from catalogue), **where it may run** (rooms/zones), who may run it, max speed/force profile, success criterion (e.g. "instrument in handover zone, gripper open") | All fields; risk questions answered ("Near patient? Sharps? Sterile field?"); "Sharps" or "patient contact" = blocked in this version |
| 2 Demonstrate | Arms/Drive screens with a **REC** bar | Operator performs the task via teleop (existing camera arm teleop + locomotion), 5–20 times; each take is tagged good/bad on the spot; take counter and variation hints ("Try with the rack rotated") | ≥ N good takes (default 10); no take contains a proximity violation |
| 3 Review & curate | Teach → Takes | Scrub through each take: robot-view video, joint plot, contact events; trim start/end; mark bad; see coverage (positions of objects across takes) | Author confirms the dataset; the dataset gets a version number |
| 4 Train | Teach → Training (status only on iPad) | Kick off training on the workstation (policy via the same `g1-whole-body-rl/` export contract); progress and ETA | Training job finished; policy + sidecar exported |
| 5 Test in sim | Teach → Sim test | Run the auto test suite in the MuJoCo/Isaac hospital: M randomised trials; scorecard: success %, time, min distance to people, peak force, joint limit margins; watch any trial | Success ≥ threshold (e.g. 95% over 100 trials) and zero safety violations |
| 6 Dry-run | Teach → Dry run | Supervised run on the real robot in an empty theatre; operator holds Stop; 10 runs | 10/10 success, no interventions |
| 7 Approve | Teach → Approvals (two signatures) | Clinical lead (e.g. theatre nurse manager) and technician review the scorecard, the video of the dry run and the risk answers; sign with badge + PIN | Both approvals; approver ≠ author |
| 8 Publish | Places/Tasks tiles | The task appears as a tile for the chosen roles and rooms, with version and track record | Any later change → new version, back to step 5; rollback to the previous version is one tap for the technician |

Design notes for Teach:
- The **recording indicator** and consent rules from P-1 apply. Demonstrations in theatre need IRB consent if staff or patients are visible. The default is to record only in an empty theatre or the sim.
- The iPad is for *capture, review and approval*. Heavy editing and training live on the workstation.
- Every task tile shows its version and "taught by … approved by … on …" (trust through purpose/process, HF-27–29).
- Clinical users never see unapproved tasks.

## 10. Backend and contract gaps this design needs

Not to be done in this document (it does not edit `docs/interfaces.md`), but the app cannot meet the rules without them:

| Need | Why | Suggested shape |
|---|---|---|
| **Hold-stop** distinct from DAMP; arms freeze (no 1-s blend) on stop | S-1, F5 | `SetMode(STAND, source=ui_stop)` handled as "hold" by manager + controller; or new `srv/Stop` |
| UI heartbeat + manager watchdog for manual modes | S-7 | `/g1/ui/heartbeat` (4 Hz, device id); manager drops LOCO/MANIP → STAND after 1 s |
| Control lease | S-6 | `srv/AcquireControl`, `srv/ReleaseControl`, `/g1/control_owner` (latched) |
| Authenticated WSS + server-side permission check | L-3, L-4 | Session token per user/role/device; op allow-list per role |
| Append-only audit log | L-6 | Server-side JSONL with rotation; `audit_list` op |
| Named places with display metadata | F2 | `locations.yaml` + display name, photo, zone, allowed roles |
| Instrument catalogue with images and rack counts | F3 | From perception / `/sim/objects` in sim |
| Hardware e-stop heartbeat topic | S-2, F1 | Wireless e-stop receiver state published |
| Zones (keep-out, quiet, speed) | HF-36, U4 | Nav2 keepout/speed filter masks + UI metadata |
| Incident bundle | F6 | Server-side ring buffer + `incident_create` op |
| Robot status light + speech | S-8, HF-6 | `/g1/indicator` (colour, pattern), `/g1/say` (text) |

## 11. Overall success metrics (what to measure in pilots)

| Metric | Target |
|---|---|
| Time from wake to "robot moving" for Send to place | ≤ 5 s median |
| First-use success (send + stop, untrained nurse) | ≥ 90% |
| Wrong-destination / wrong-instrument requests reaching the robot | 0 in summative testing |
| Stop reaction (tap → robot holding, measured) | ≤ 300 ms UI → command; robot to still ≤ 1 s |
| Non-actionable alarms per case | < 1 |
| SUS (Clinical mode) | ≥ 80 |
| Nurses using the robot at least once per shift in pilot theatres | ≥ 70% by week 4 |
| Incidents diagnosable from the bundle alone | ≥ 80% |

## Sources

(Key sources for this file; the full lists are in `01`–`03`.)
- [docs/interfaces.md](../interfaces.md) and [hospital-sim-ui/PROTOCOL.md](../../hospital-sim-ui/PROTOCOL.md) (robot contract, modes, mission interfaces)
- [IEC 60601-1-8 alarm guidance (Digi-Key)](https://www.digikey.com/en/articles/iec-60601-1-8-guidance-for-designing-medical-equipment-alarms); [Joint Commission alarm fatigue alert](https://digitalassets.jointcommission.org/api/public/content/f65e5c9df2b94000a99445e0a7877007)
- [FDA human factors guidance](https://www.fda.gov/media/80481/download)
- [AORN RN circulator](https://www.aorn.org/docs/default-source/guidelines-resources/position-statements/personnel-staffing/posstat_rn_circulator.pdf?sfvrsn=642bbf4b_1); [AORN sterile technique](https://www.aorn.org/about-aorn/aorn-newsroom/periop-today-newsletter/periop-today-newsletter/aorn-guideline-in-focus--sterile-technique-in-the-or)
- [Spot user guide (Autowalk, stop, comms loss)](https://www.generationrobots.com/media/spot-boston-dynamics/spot-user-guide-r2.0-va.pdf); [Spot SDK lease](https://github.com/boston-dynamics/spot-sdk/blob/master/docs/python/understanding_spot_programming.md)
- [BrainOS teach and repeat](https://www.braincorp.com/resources/how-brainos-delivers-simple-robot-solutions-anyone-can-use-3e952); [Seirios Task Manager](https://docs.movel.ai/new-collection/seirios-rns/product-features/core/task-manager); [MiR user groups / PIN](https://supportportal.mobile-industrial-robots.com/support-files/manuals/html/en/ref_guide_robots_2.2/content/_resources/pdf/mir%C2%A0robot%20reference%20guide%202.2_en.pdf); [Agility Arc KPIs](https://www.agilityrobotics.com/content/agility-robotics-brings-operational-visibility-to-deployment-of-digit-fleets-with-the-launch-of-agility-arc-tm)
- [ChristianaCare cobot study (iPad kiosks, arrival ambiguity)](https://djph.org/wp-content/uploads/2024/12/djph-105-05.pdf)
- [Intraoperative scrub nurse handoffs](https://pmc.ncbi.nlm.nih.gov/articles/PMC8365200/); [Structured intraoperative handover checklist](https://pmc.ncbi.nlm.nih.gov/articles/PMC8286430/)
- [EU Machinery Regulation 2023/1230 (self-evolving behaviour)](https://digital.nemko.com/regulations/eu-machinery-regulation); [PDPC advisory guidelines](https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/ag-on-selected-topics/advisory-guidelines-on-the-pdpa-for-selected-topics-(revised-may-2024).pdf)
