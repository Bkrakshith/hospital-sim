# 03 — Human factors and stress in the surgical wing

What the people using the G1 iPad app are dealing with, and the concrete UI rules that follow. Rule IDs (HF-n) are referenced from `04` and `05`.

## 1. The environment in numbers

| Factor | Evidence | Implication |
|---|---|---|
| **Interruptions** | OR teams are distracted or interrupted **9.8/h** in one observational study and **15.6/h** (one every 3 min 51 s) in another. Rates vary 2.4–114/h. The most frequent causes are people entering or leaving and phone/pager calls. Disruptions peak mid-case (16.4/h and 13.4/h in phases 2–3 vs 5.6/h and 3.5/h at start and end). Flow disruptions waste ~20% of OR time. | The robot must **not be another interruption**. It should be a way to *remove* interruptions (fetching, walking out of the room). Every robot → human message must be worth the interruption. |
| **Noise** | Mean OR noise **51–75 dB(A)**, peaks **80–119 dB(A)**, powered instruments > 100 dB. Noise is higher in harder cases and in cases with complications. | Sound alone cannot carry a message. Speech recognition degrades sharply (< 40% command recognition above 60 dB SPL in one study; modern ASR does better but is still unreliable). Visual channel first, audio second, speech third. |
| **Light** | Two regimes. (a) Open surgery: bright room light plus surgical lights (field 40–160 klx) → glare on glossy screens. (b) Laparoscopic/robotic: room lights **dimmed**, sometimes green downlights, eyes adapted to the endoscope monitor. | Two themes: **Light** (high contrast, anti-glare case) and **Theatre dim** (dark, low-luminance, no large white areas). Switching must be one tap and never flash white. |
| **Gloves** | Nitrile/latex gloves ≤ 1 mm usually register on capacitive screens, but with less precision. Loose gloves are worse. | Large targets, generous spacing, no precision gestures (see `05` §5). |
| **Distance** | Circulating nurse is at the iPad (arm's length, 0.4–0.6 m) for seconds at a time, then 1–3 m away doing other work. The surgeon is 2–4 m away and sterile. | Two reading distances: **arm's length** for controls and **across-room** for status. |
| **Handovers** | Each intraoperative scrub-nurse handoff was associated with longer operative time, and one handoff with **2.12× odds** of a surgical complication (arthroscopy cohort). A structured checklist cut information omissions between scrubs from 19.5% to 12.1%. | The robot's state must be **handover-proof**: a one-screen summary a relieving nurse can absorb in < 15 s. |
| **Colour vision** | ~5% of Singapore Chinese males and ~8% of Caucasian males have red-green deficiency. | Never red vs green alone. |
| **Alarm load** | 85–99% of clinical alarms require no action (Joint Commission). Alarm fatigue is a sentinel-event cause. | Strict alarm budget (see `04` §7). |

## 2. Who is under what stress

### 2.1 Circulating nurse — the primary user

What they actually do (AORN):
- Before and at the start of the case: room and equipment checks, opening sterile supplies, patient positioning, the **WHO time-out** (usually initiated by the circulator), **counts** with the scrub nurse.
- During the case: fetching supplies, managing phone calls and people, documenting, monitoring the patient environment, "the eyes of the room".
- At closing: counts again, specimens, dressings, transfer.

They are non-sterile. They are the only team member who can walk out of the room, which is exactly the job the robot wants to take over. **Peak load is at the start and end of the case; the middle has pockets of low load interrupted by urgent fetches.**

UI consequences:
- **HF-1.** The three most frequent clinical tasks (send the robot somewhere, request an instrument/item, stop it) are each **≤ 3 taps and ≤ 5 s** from the Home screen, including unlock.
- **HF-2.** Nothing requires the nurse to stay at the iPad. Every task is **fire-and-forget with a visible promise** ("Robot will be in Theatre 1 in ~2 min"). Progress is glanceable from across the room.
- **HF-3.** The robot must support, not duplicate, the time-out and counts. It adds one line to the time-out ("Robot: present · rack verified · stop control with circulator") and **never adds a separate count**. Instruments it hands over are logged so the nurse can reconcile them.

### 2.2 Scrub nurse — sterile, hands busy, minute to minute

They set up the back table and Mayo stand. They pass instruments handle-first, ratchets closed, curved tips oriented to the surgeon's hand, placed into the surgeon's palm so the surgeon does not need to look away from the field. They load blades and sutures, keep the field tidy, track sharps and sponges, and above all **anticipate**. Experienced scrub nurses have the next instrument ready before it is asked for. A laparoscopic-video model could anticipate 71.5% of instrument needs. Nonverbal exchange is the goal.

- **HF-4.** The scrub nurse never touches the iPad (sterile, see `02` I-1). They interact with the **robot** by voice and gesture. The iPad shows the circulator what the scrub nurse and robot are doing, so the circulator can act as the robot's "hands on the controls".
- **HF-5.** In the scrub-nurse mission, the robot **assists** the human scrub nurse (fetching from the sterile store or a secondary rack, passing to the scrub nurse, or handing lower-urgency instruments). It does not replace the scrub nurse in the critical path. The app says so: "Robot assisting — scrub nurse is primary".

### 2.3 Surgeon — glanceable, hands-free, low tolerance

The surgeon's attention is on the field or the monitor. Surgeons tolerate tools that are *invisible until needed* (Ottava's design idea, da Vinci 5's head-in menu). They resent anything that makes them look away, repeat themselves or wait. Robotic scrub-nurse research (Penelope: voice; Gestonurse: gestures, ~96% gesture recognition) shows the surgeon → robot channel is voice, gesture or gaze, and that feedback from the robot to the surgeon is the weak point.

- **HF-6.** Every request gets **closed-loop readback**, as in human OR communication (call-out and check-back). The robot says "Mayo scissors — coming", and the app shows the same words in ≥ 44 pt. A wrong readback is caught by the surgeon without anyone touching a screen.
- **HF-7.** The surgeon-facing state is on the **robot body** (status light, arm pose, speech) and on the iPad's **across-room view** (§3.3). The surgeon should never need to read a small label.
- **HF-8.** Robot-handover latency must be stated honestly in the UI ("~40 s to fetch from store"). This is opinion, not measured: a surgeon will tolerate a slow robot for *planned* requests (closure set, next tray) but not for urgent ones such as haemorrhage control. Urgent requests go to the human scrub nurse, and the app must not invite them to the robot. The instrument picker has no "urgent" button.

### 2.4 Remote / seated teleoperator

Seated at a desk with the OBSBOT camera tracking their hands. Stressors: split attention between their own camera image, the robot's view and the map; latency; fatigue in the arms; losing tracking; not being in the room (poor situation awareness of people near the robot).

- **HF-9.** In MANIP the screen is dominated by the **robot-side view plus a proximity strip** (people or objects within 1 m, from lidar/depth). The operator's own image is a small picture-in-picture with a tracking-quality ring. Tracking lost → arms hold (not drift) and the screen says why.
- **HF-10.** Show latency numerically and as a quality bar. Above 250 ms, show amber "Slow link — robot moves slower". Above 500 ms, block manual arm motion.
- **HF-11.** A **fatigue timer**: after 15 min of continuous arm teleop, suggest a break (non-blocking).

### 2.5 Ward/corridor operator (portering, navigation)

Walking alongside or ahead of the robot, iPad held or mounted on the robot, among patients on beds, visitors and cleaners. Stress: public attention, blocked corridors, lifts and doors.

- **HF-12.** One-handed use in portrait while walking: the Stop button and "Pause here" are reachable by the thumb (bottom band), and the map auto-follows the robot.
- **HF-13.** "Robot is waiting for: lift / door / path clear" is always a sentence, never an unexplained stop (the Moxi "silent spinning" failure).

### 2.6 Technician / biomedical engineer

Often called mid-case under time pressure, with an audience. They need **evidence** (what happened, when, in what mode, on which software version) more than controls.

- **HF-14.** Every fault produces an **incident bundle** (last 5 min of mode changes, commands with user, alarms, controller status, versions, map pose, optional de-identified frames) that the nurse can hand over with one tap ("Send to technician"). The technician does not have to reproduce the fault.

## 3. Cognitive principles → rules

### 3.1 Situation awareness (Endsley)

Endsley's three levels: **perceive** (what is the robot doing), **comprehend** (is that OK, does it need me), **project** (what will it do next).

- **HF-15.** The Home "hero" answers all three in one block:
  1. **Now**: mode + activity in words ("Walking to Theatre 1").
  2. **Status**: OK / needs you / stopped, with colour, icon and word.
  3. **Next**: "Arrives in ~1 min · then waits for instrument request".
- **HF-16.** Projection is shown on the map as a ghost path and on the mission stepper as the "next" step. **The robot never starts a new motion that the app did not show as "next".**

### 3.2 Mode confusion — our FSM specifically

The G1 has six modes (DAMP, STAND, LOCO, MANIP, NAV, AUTO), exclusive, with legal transitions only via STAND. Sarter & Woods' factors for mode error are all present: several modes, mode changes started by different agents (keyboard, UI, nav, mission, safety), coupling (NAV and AUTO both drive `cmd_vel`), and weak feedback. The same key (`p`) means "pause walking", "stop navigating" and "abort mission step" depending on the mode.

- **HF-17.** **Never show raw mode codes to clinical users.** The UI names modes by what the robot is doing and who is in control:

  | FSM | Clinical label | Who is driving | Mode colour family (`05`) |
  |---|---|---|---|
  | DAMP | **Powered down** (motors off) | nobody | grey |
  | STAND | **Standing by** | nobody (robot balancing) | slate |
  | LOCO | **Manual walking** | a person (name) | violet |
  | MANIP | **Manual arms** | a person (name) | violet |
  | NAV | **Going to ‹place›** | robot (autonomous) | blue |
  | AUTO | **Scrub assist: ‹step›** | robot (autonomous) | blue |

  Two families, **"a person is driving" (violet)** and **"the robot is driving" (blue)**, are the distinction that matters for safety. Technician mode shows the FSM name too.
- **HF-18.** **Say who changed the mode.** Every mode change is shown for 5 s: "Now: Standing by — stopped by Safety (fall risk)". This uses the `source` field of `/g1/mode` (`keyboard`, `ui`, `nav`, `mission`, `safety`), mapped to a person or system name.
- **HF-19.** **Goal-based buttons, not transition buttons.** The user asks for "Use arms". If the robot is walking, the app shows the sequence it will run ("Stop walking → Arms") and runs it on one confirm. The FSM rule stays (via STAND), but the human no longer does the bookkeeping. This replaces today's "reject then toast" behaviour.
- **HF-20.** **Unexpected mode change = alert.** Any mode change not requested from this iPad (by safety, mission or another device) triggers a Low (informational) cue, or Medium if it involves motion starting.

### 3.3 Distance and the across-room view

- **HF-21.** After 20 s without a touch (and no modal open), the app shows the **Across-room view**: status word, activity and next step at ≥ 88 pt, plus progress and the Stop button. It is legible at 2 m. Any touch returns to the previous screen without acting on that touch (the first tap only wakes the screen).

### 3.4 Workload, stress and error prevention

Under acute stress, attention narrows, fine motor control and working memory degrade, and people fall back on habit. So:

- **HF-22. Recognition over recall.** Locations, instruments and tasks are pictures and names in tiles, never typed. There is no free text in Clinical mode.
- **HF-23. Stable positions.** Stop is always in the same place. Primary actions are always bottom-right in landscape (the right-hand thumb zone on a mounted iPad), with a mirror option for left-handed use. Controls never move because content loaded.
- **HF-24. Friction proportional to risk** (not confirmation dialogs everywhere, which people learn to tap through):

  | Action | Friction |
  |---|---|
  | Stop | none: one tap, instant |
  | Send to a place, request an instrument | one tap + readback visible for 3 s with **Undo** |
  | Resume after stop, start manual control, take control from another device | **slide to confirm** (deliberate, glove-friendly, not a modal) with a sentence describing the consequence |
  | Power off (DAMP) | press-and-hold 1.5 s with a filling ring, label "Robot will sink to the floor" |
  | Delete map, change zone speeds, clear calibration | Technician PIN + typed-free confirm with consequence |

- **HF-25. Undo beats confirm** for non-motion actions. An instrument request can be cancelled until the robot has grasped the instrument. After that, "Cancel" becomes "Put it back".
- **HF-26. Interrupt budget.** In theatre, the robot may make **at most one non-safety audible prompt per 3 minutes**. Others queue silently in the timeline. Safety alarms are exempt.

### 3.5 Trust calibration (Lee & See)

Misuse (over-trust) and disuse (under-trust) both come from poor calibration of trust to real capability. Trust is built by **performance, process and purpose** being visible.

- **HF-27. Show performance.** Each named location and task shows a plain track record ("Theatre 1: 23 of 24 arrivals OK this week"). The OR manager sees the same.
- **HF-28. Show process.** When the robot hesitates, it says why ("Checking path — person in doorway"). When it cannot do something, it says what would help ("Move the trolley 30 cm left").
- **HF-29. Show purpose and limits.** Onboarding and the About screen state what the robot does *not* do: no patient contact, no urgent instruments, no sharps passed directly to hands (sharps go to the scrub nurse's neutral zone). Opinion: include the neutral-zone rule until handover safety is validated.
- **HF-30. Don't over-humanise.** Friendly, short speech; no jokes during cases; a neutral voice. Patients care about practical benefit more than human-likeness, and 75% in one survey were sceptical about robot empathy. The humanoid form already suggests more competence than the robot has, so the UI should under-promise.

### 3.6 Novices and experts

Many users are infrequent: relief nurses, night shift, a new rotation every few weeks. Moxi's study found infrequent users could not open its drawers.

- **HF-31. Walk-up-and-use for Clinical mode.** A nurse who has never used it can send the robot and stop it without training. Validate this in formative tests (`02` U-1).
- **HF-32. Built-in 30-second "How to" clips** per flow (BrainOS), offline, captioned, no sound needed.
- **HF-33. Expert accelerators** in Operator/Technician modes: hardware-keyboard shortcuts (the contract keys), recent destinations, saved routes. They never appear in Clinical mode.

### 3.7 Speaking up and voice

Closed-loop communication and "speaking up" are core OR safety behaviours. The robot has to be interruptible by anyone: "**Robot, stop**" must work from any team member. That is a robot-side feature, but the app must show "Stopped by voice (scrub nurse)".

- **HF-34.** Voice commands (future) are limited to a tiny, safety-first vocabulary (*stop, wait, continue, come here, go to dock*, and instrument names in the mission). The iPad never depends on voice, and every voice action appears in the timeline so it is visible and reversible.
- **HF-35.** Do not rely on iPad Safari speech recognition in theatre (noise, network dependency, permission prompts). Use the robot's microphone array for any future voice path.

### 3.8 Bystanders: patients and visitors

Patients in pre-op and PACU are awake, anxious and sometimes sedated or confused. Surveys show generally positive but conditional acceptance of humanoids in hospitals, with high privacy concern across all age groups.

- **HF-36. Quiet mode by zone.** In PACU and pre-op the robot moves slower, uses a lower voice, and the camera feed in the app is **blurred by default**.
- **HF-37.** The robot identifies itself when it approaches people ("Hello, I'm the theatre robot, passing on your left"). The app lets staff set this phrase per zone.
- **HF-38.** The app shows the operator when the robot's cameras can see a patient bed or person, so they can avoid unnecessary viewing.

### 3.9 Adoption and utilisation

Utilisation follows usefulness, convenience and ownership (Epic Rover: personal devices → +74% barcode adherence). Rejection follows interruptions and a poor cost/benefit balance (TUG on medical wards; Moxi at MultiCare).

- **HF-39.** Zero-cost start: the iPad lives docked and charged at the theatre door, unlocks with a badge tap, and opens on Home in the right room context.
- **HF-40.** Show value back to the team: an end-of-shift card ("Today the robot made 14 trips for Theatre 1 — about 38 minutes of walking saved") and a weekly summary for the OR manager (see `04`).
- **HF-41.** Delight through calm, not decoration: smooth, fast, quiet and always right about the robot's state. Celebrate only completed tasks, with a single subtle confirmation.

## Sources

- Interruptions: [Distractions in the operating theatre, Anaesthesia 2020](https://associationofanaesthetists-publications.onlinelibrary.wiley.com/doi/10.1111/anae.15217); [Effect of distractions in the OR (PMC3032204)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3032204/); [Are OR distractions, interruptions and disruptions associated with performance? Int J Qual Health Care, systematic review](https://academic.oup.com/intqhc/article-pdf/doi/10.1093/intqhc/mzab068/37487469/mzab068.pdf); [Surgical interruptions and preventable delays, Patient Safety in Surgery 2025](https://link.springer.com/article/10.1186/s13037-025-00470-y); [Integrative review of OR distractions](https://www.researchgate.net/publication/347593541_The_impact_of_distractions_and_interruptions_in_the_operating_room_on_patient_safety_and_the_operating_room_team_An_integrative_review)
- Noise: [Impact of noise in the operating theatre, Ann R Coll Surg Engl](https://publishing.rcseng.ac.uk/doi/10.1308/rcsann.2020.7001); [Noise coincides with surgical difficulty, BJS Open 2024](https://academic.oup.com/bjsopen/article/8/5/zrae098/7823788); [Leading through noise (PMC11484183)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11484183/); [Vanderbilt OR noise study](https://news.vumc.org/2019/12/19/study-tracks-impact-of-noise-in-operating-rooms/)
- Voice in the OR: [Voice control of a head-mounted display in parotid surgery (PMC9988782)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9988782/); [Voice-enabled prototype, Patient Safety in Surgery 2025](https://link.springer.com/article/10.1186/s13037-025-00460-0); [ASR in the OR survey](https://www.researchgate.net/publication/344668723_Automatic_speech_recognition_in_the_operating_room_-_An_essential_contemporary_tool_or_a_redundant_gadget_A_survey_evaluation_among_physicians_in_form_of_a_qualitative_study); [Voice control interface for surgical robot assistants (arXiv)](https://arxiv.org/pdf/2409.10225)
- Lighting: [Current state of surgical lighting (PMC7305019)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7305019/); [Lumitex surgical lighting guide](https://www.lumitex.com/blog/surgical-lighting)
- Gloves: [Capacitive touch with disposable gloves (Newhaven)](https://support.newhavendisplay.com/hc/en-us/articles/4415788835991-Capacitive-Touch-with-Disposable-Gloves-Latex-Nitrile); [Focus LCDs, capacitive panels with gloves](https://focuslcds.com/journals/using-capacitive-touch-panels-with-gloves/)
- Handovers: [Intraoperative scrub nurse handoffs and complications (PMC8365200)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8365200/); [Structured handover checklist pilot (PMC8286430)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8286430/)
- Scrub nurse / surgeon: [Jacob et al., Collaboration with a robotic scrub nurse, CACM 2013](https://dl.acm.org/doi/10.1145/2447976.2447993); [Gestonurse](https://www.researchgate.net/publication/257720642_Gestonurse_A_robotic_surgical_nurse_for_handling_surgical_instruments_in_the_operating_room); [Robotic scrub nurse anticipating instruments, Communications Medicine 2024](https://www.nature.com/articles/s43856-024-00581-0); [Scalpel, please: how surgeons communicate with robotic scrub nurses, HFES 2025](https://doi.org/10.1177/2327857925141053); [Automated scrub nurse robot, IJCARS 2025](https://link.springer.com/article/10.1007/s11548-025-03433-x); [Voice-interactive robotic scrub nurse, J Robotic Surg 2026](https://link.springer.com/article/10.1007/s11701-026-03866-9)
- Circulating nurse and sterile field: [AORN position statement on the RN circulator](https://www.aorn.org/docs/default-source/guidelines-resources/position-statements/personnel-staffing/posstat_rn_circulator.pdf?sfvrsn=642bbf4b_1); [AORN RN circulator flyer](https://www.aorn.org/docs/default-source/aorn/pdfs/rn-circulator-flyer.pdf); [AORN sterile technique](https://www.aorn.org/about-aorn/aorn-newsroom/periop-today-newsletter/periop-today-newsletter/aorn-guideline-in-focus--sterile-technique-in-the-or); [EORNA best practice](https://eorna.eu/wp-content/uploads/2020/09/EORNA-Best-Practice-for-Perioperative-Care-Edition-2020.pdf)
- Situation awareness, modes, trust: [Endsley, SA misconceptions (J Cogn Eng Decis Mak 2015)](https://journals.sagepub.com/doi/full/10.1177/1555343415572631); [Sarter & Woods, "How in the world did we ever get into that mode?"](https://www.researchgate.net/publication/258138719_How_in_the_World_Did_We_Ever_Get_into_That_Mode_Mode_Error_and_Awareness_in_Supervisory_Control); [Automation surprises](https://www.researchgate.net/publication/270960170_Automation_surprises); [NASA mode awareness methodology](https://shemesh.larc.nasa.gov/fm/papers/MethodologyForModeAwareness.pdf); [Lee & See, Trust in automation (PubMed)](https://pubmed.ncbi.nlm.nih.gov/15151155/)
- Alarm fatigue: [Joint Commission Sentinel Event Alert](https://digitalassets.jointcommission.org/api/public/content/f65e5c9df2b94000a99445e0a7877007); [AHRQ alarm fatigue review](https://www.ncbi.nlm.nih.gov/books/NBK555522/)
- Acceptance and adoption: [Patient preferences on humanoid features, Sci Eng Ethics 2024](https://link.springer.com/article/10.1007/s11948-024-00508-x); [Intergenerational views on humanoid nurse robots (PubMed 40452159)](https://pubmed.ncbi.nlm.nih.gov/40452159/); [Patient acceptance of medical service robots, HSSC 2024](https://www.nature.com/articles/s41599-024-04028-8); [Health care professionals' perceptions, JMIR 2025](https://www.jmir.org/2025/1/e79634); [Mutlu & Forlizzi 2008](https://www.researchgate.net/publication/221473546_Robots_in_organizations_The_role_of_workflow_social_and_environmental_factors_in_human-robot_interaction); [ChristianaCare cobot study](https://djph.org/wp-content/uploads/2024/12/djph-105-05.pdf); [Proof News on Moxi](https://www.proofnews.org/moxi/); [Epic Rover outcomes](https://www.mindbowser.com/epic-rover-guide/)
- Colour vision: [Red-green colour blindness in Singaporean children](https://www.researchgate.net/publication/23405735_Red-green_colour_blindness_in_Singaporean_children)
