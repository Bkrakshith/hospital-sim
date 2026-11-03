# Physics-enabled human persona agents for human-robot interaction studies

Status: design, awaiting approval (2026-11-03). Nothing in it is built yet.

## 1. Intent and why

We want simulated people in the Isaac Sim hospital who behave like real UK hospital visitors and patients, so the
Unitree G1 can be tested against them. Each person is:

- **physical:** every joint is actuated, bodies collide with the building, chairs and the robot, and balance is real
  (the ProtoMotions SOMA-23 tracker already built in `hospital-sim-humans/`);
- **intelligent:** a LangGraph agent decides what the person does next from their persona, what they see and hear,
  and their memory;
- **independent of the robot:** a person knows nothing about the robot's task or code. They react only to what the
  robot does and says in the scene, as a real visitor would. This lets us test G1 tasks we have not thought of yet.

The person model is generalist: one persona definition can be instantiated many times with different seeds, and the
same machinery serves every scenario. Scenes run for up to one hour.

Why now: the scripted UC2 film showed that physics humans work (chair-trained tracker, epoch 2000), but scripting
every person by hand does not scale to hour-long scenes or to unknown robot tasks.

## 2. Scope of version 1

**In:** the main-entrance waiting area with **5 people**, **2 of them coughing patients**, running for up to one hour
alongside the G1 stack over ROS 2.

**Deferred to the next version (user decision):**
- benchmarking the G1 (metrics, scoring, reports on how well it handled the room);
- a configuration screen (v1 is configured by editing files);
- other areas of the hospital and larger crowds.

## 3. Goals, non-goals, anti-goals

Goals
- G1. Five physics people sit, cough, fidget, look around, use phones, read signs, stand, walk and talk in the waiting
  area for up to an hour without falling or passing through walls and chairs.
- G2. Each person's decisions follow their persona and the research notes, and change when the robot speaks to them
  or acts near them.
- G3. Everything about the people is configurable from files: personas, how many of each, seats, arrival times,
  seed, perception mode, LLM provider and models.
- G4. Memory builds up over a run and across runs, and the user can reset it or restore a snapshot.
- G5. Each user runs it on their own Claude or OpenAI account; keys are stored securely and nothing runs without one.
- G6. Two perception modes, chosen at launch, with README instructions for every service each mode needs.
- G7. Runs comfortably on one RTX 5090 (32 GB) long term; v1 development on the RTX 3070 (8 GB) in oracle mode.

Non-goals (v1)
- Scoring the robot (deferred).
- Photoreal rendering live; the hour is recorded and selected spans are rendered afterwards with the existing
  `render/render_recording.py` pipeline.
- New RL training of the human tracker unless the motion spike (section 11) shows the current tracker cannot follow
  the new behaviours; any training run needs the user's go-ahead first.

Anti-goals (would make it a failure even if it technically works)
- People that freeze, glitch or pop while waiting for an LLM reply.
- Behaviour that secretly depends on the robot's internals (shared state, cheat topics the robot could not have).
- API keys in git, logs, ROS parameters, ROS topics or recordings.
- A run that cannot be repeated: every decision must be recorded so the hour can be replayed exactly.

## 4. Constraints (from the project)

- ROS 2 **Humble** on Ubuntu 22.04, CycloneDDS, the contract in `docs/interfaces.md`. The robot side keeps that
  contract; this design only adds topics.
- Physics: Isaac Sim 6.0 / Isaac Lab 3, PhysX GPU, humans tracked at 30 Hz by the SOMA tracker (trained with 120 Hz physics)
  (`~/src/ProtoMotions/results/hg1_uc2_chairs/epoch_2000.ckpt`), the hospital collision USD
  (`hospital-sim-humans/sim/assets/hospital_collision.usd`) and the measured lobby chairs (`sim/lobby_chairs.py`).
- Host RAM: more than 2 scene objects per env in ProtoMotions blows host memory; every sim process runs under the
  memory-capped launcher (`~/src/hg1_humans/hh.sh` / `isaac_capped.sh`). ProtoMotions puts one humanoid in each
  env, so v1 uses `num_envs` = 5 with a shared origin and `filter_collisions=False` (as `run_reception.py` does);
  the chairs and the hospital are global prims, not per-env scene objects, so the per-env object limit does not bite.
- Physics rate: one world shared by people and the G1 at **600 Hz** (the LCM of the tracker's 120 Hz and the G1's
  200 Hz training rates; `research_notes/physics_humans/integration.md` §2), people acting every 20 ticks (30 Hz),
  the G1 every 12 ticks (50 Hz), via the tick scheduler planned there. The tracker was trained at 120 Hz and must be
  re-validated at 600 Hz (fallback 300 Hz). No trained G1 walking policy exists yet (`g1-whole-body-rl/exports`
  is empty), so what drives the G1 in v1 is an open question (section 14).
- Licences: BONES-SEED clips and anything derived stay local, never redistributed; SMPL-based models are not used.
- Confidential project content stays out of this component (see the master README rules).
- No AI attribution lines in commits or files.

## 5. Architecture overview

```
 ┌───────────────────── Sim host (Isaac Sim / Isaac Lab, one process, GPU) ─────────────────────┐
 │  PhysX world: hospital collision USD, lobby chairs, G1 articulation, 5 SOMA people           │
 │  Human bodies: SOMA tracker (30 Hz)  ◄─ reference motion ◄─ Motion composer (per person)     │
 │  G1 body: existing /lowcmd → PD → /lowstate bridge (g1-isaac-sim run_sim.py pattern)          │
 │  Scene oracle: who/what is visible, signs in view, speech + coughs in earshot                │
 │  Optional cameras: one head camera per person (full perception mode)                         │
 │  Recorder: body states, events, intents → run folder                                         │
 └───────────────▲──────────────────────────────┬──────────────────────────────────────────────┘
                 │ /humans/<id>/intent           │ /humans/<id>/observation, /humans/<id>/status,
                 │ /humans/<id>/say              │ /sim/audio/events, /clock
 ┌───────────────┴──────────── Agent service (one Python process, .venv, rclpy) ────────────────┐
 │  One LangGraph graph per person:  observe → recall → decide → act → remember                 │
 │  Body reflexes (no LLM): cough timer, fidget, breathing idle, gaze follow                    │
 │  Memory: short-term (LangGraph checkpointer) + long-term (store with vector index)           │
 │  Knowledge base (RAG): research notes, persona cards, hospital map + sign registry           │
 │  LLM gateway: Claude or OpenAI, the only holder of the key                                   │
 │  Full-perception adapters: local ASR (speech→text), VLM calls on camera frames               │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
                 ▲ /g1/speech/say (existing)           │ /sim/audio/events (people's speech, coughs)
 ┌───────────────┴──────────── G1 stack (unchanged contract, real robot or sim) ────────────────┐
 │  controller, manager, Nav2, mission, perception, UI …  (knows nothing of the agents)         │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

Three layers per person, from slow to fast:

1. **Mind (agent service, ~0.2–2 s per decision, event-driven):** picks the next *intent*, e.g. "stay seated, look
   at phone", "stand up and go to reception", "answer the robot: 'Yes, I've been waiting 40 minutes'". LLM-backed.
2. **Reflexes (agent service, 10 Hz, no LLM):** things a person does without deciding: coughing on a persona-set
   schedule, shifting in the seat, glancing at movement, turning the head towards a voice. These keep people alive
   while the mind is thinking, and run identically in replay.
3. **Body (sim host, 30 Hz policy / 600 Hz shared physics):** the motion composer turns the current intent plus reflex
   overlays into a reference motion; the SOMA tracker follows it physically.

People never wait for an LLM: the body keeps executing the last intent (with its idle loop) until a new intent arrives.

## 6. The body: from intent to physics

### 6.1 Intent vocabulary (v1, waiting area)

`sit_idle`, `use_phone`, `fidget`, `look_at(target)`, `read_sign(sign_id)`, `stand_up`, `sit_down(seat_id)`,
`walk_to(point|landmark)`, `approach(person|robot|desk)`, `wait_standing`, `talk(text, addressee)`,
`gesture(kind)`, `cough(severity)` (also issued by the reflex layer), `leave(exit)`.

Each intent has parameters (target, speed, style) and a completion status reported back on `/humans/<id>/status`
(running, done, failed + reason, e.g. "seat occupied", "path blocked").

### 6.2 Motion composer (per person, in the sim host)

Builds the reference the tracker follows, a few seconds ahead, from the current physical state:

- **Clip library:** motion clips indexed by intent and style (seated idle, phone, fidget, stand-up, sit-down, walk
  cycles at several speeds, turn-in-place, gestures, cough seated/standing with hand or elbow to mouth). Sources:
  BONES-SEED (already licensed and on the server), the UC2 clips, and synthetic overlays like the existing
  `compose_uc2.visitor_nod` head pitch.
- **Stitching:** each new segment starts from the person's current simulated pose (not the old reference), with a
  short blend, so a mid-motion change of mind does not yank the tracker. Walks are warped onto paths planned on the
  waiting-area navigation grid (the Chaikin-smoothed path code from `compose_uc2.walk_path`).
- **Overlays:** head/gaze and cough are layered on top of the base motion (upper-body additive), so a person can
  cough or turn their head while seated in any idle.
- **Seats:** `sit_down(seat_id)` places the hips with the backrest-distance rule already used in `place_by_seat`;
  seats come from `lobby_chairs.py`.

Text-to-motion (NVIDIA Kimodo, SOMA output) is the planned way to get clips the library lacks; it is optional in v1
and plugs in behind the same composer interface.

### 6.3 Physical people in the scene

- 5 SOMA people (one per env, shared origin, inter-person collisions on) with the G1, the hospital collision USD and
  the full lobby chair rows (`lobby_chairs.all_rows`, fabric/wood friction). The `run_reception.py` scene patching
  is the starting point.
- **Live reference streaming is plumbing work, not only a stability question:** the tracker reads future frames from
  a preloaded MotionLib and freezes on the last frame. The composer needs a streaming motion source (a patched or
  replaced motion manager that serves a rolling window per person). Spike S1 tests this as well as stability.
- **The robot's sensors must see the people.** `g1-isaac-sim`'s lidar ray-casts a snapshot of static geometry; v1
  adds the people's bodies to the lidar ray-cast and the head camera render so the robot perceives them as a real
  robot would (the fairness rule means sensors and audio are its only view of them).
- Coughs also produce a sound event (section 7.3) so the robot's microphones can hear them.
- A fall is reported on `/humans/<id>/status`; the person's agent is told they fell; the sim host respawns them
  standing at the nearest free spot after a configurable delay (v1 does not simulate getting up from the floor).

## 7. ROS 2 interface (additions to `docs/interfaces.md`)

Sim-boundary messages are **standard types carrying JSON** (`std_msgs/String`), like `manager_status` already does.
Reason: the sim host runs on Isaac Sim's bundled Python and ROS libraries, where custom message packages need a
separate build; JSON avoids that in v1. Every JSON payload has a documented schema and a `schema` version field.

| Topic | Type | Pub → Sub | Content |
|---|---|---|---|
| `/humans/roster` | String JSON, transient-local | sim → all | ids, persona, display name, seat |
| `/humans/<id>/intent` | String JSON | agent → sim | intent + parameters + intent id |
| `/humans/<id>/status` | String JSON, 10 Hz + on change | sim → agent | pose, posture, current intent + progress, fell? |
| `/humans/<id>/observation` | String JSON, 2 Hz + on event | sim → agent | oracle mode only (7.2) |
| `/humans/<id>/camera/image/compressed` | CompressedImage | sim → agent | full mode only, head camera, low rate |
| `/humans/<id>/say` | String JSON | agent → sim | text the person says out loud |
| `/sim/audio/events` | String JSON | sim → all | speech and coughs with position, loudness, source |
| `/sim/audio/stream` | audio (full mode) | sim → robot, agents | mixed scene audio near each listener |
| `/g1/speech/say` | String (existing) | G1 stack → sim | robot speech; today a log-only stub, becomes a sound source at the robot's head |
| `/clock` | rosgraph Clock | sim → all | sim time |
| `/scenario/control` | service | UI/CLI → sim, agents | start, pause, stop, reset |

**Robot fairness rule:** the robot stack may subscribe to `/sim/audio/*` (it hears what a microphone would hear) and
to its own sensors. It must not read `/humans/*` topics; those are the people's private senses and minds. A launch
check warns if a G1-stack node subscribes to `/humans/*`.

### 7.1 Two perception modes (chosen at launch, `perception: oracle | full`)

| | Oracle (fast, default) | Full (realistic) |
|---|---|---|
| Sight | sim computes what is in each person's view cone with line of sight: people, robot, signs (with their text), seats free/taken | head camera frame sent to a vision-capable LLM on events and every N seconds |
| Hearing | speech events within earshot arrive as text, with speaker and distance; coughs as events | scene audio → local speech-to-text (faster-whisper on GPU); coughs detected from audio |
| Cost / speed | cheap, runs on the RTX 3070 | more LLM calls (images), GPU for cameras + ASR; target the RTX 5090 |
| Needs | nothing extra | ASR model download, camera rendering on; README section lists setup |

Both modes produce the same observation schema for the agent graph, so the mind does not change between modes.

### 7.2 Signs

A sign registry (`config/signs.yaml`) lists each sign in the waiting area: id, prim path, text, pose. The scene
already has door signs (`SignSideWall`) and a sign board (`SignBoard`) from `hospital-sim-env/isaac/scene/layout.py`;
their text is defined in the registry and, for the full mode, rendered onto the sign textures so a camera can read it.

### 7.3 Speech and sound

- Robot speech: `/g1/speech/say` text → the sim creates a sound event at the robot head; in oracle mode each person
  within earshot (distance, loudness, the person's hearing from the persona) receives the text, possibly marked as
  partly heard; in full mode a TTS voice is mixed into the scene audio and goes through ASR.
- People's speech (`/humans/<id>/say`) goes the same way, so people can talk to each other and to the robot, and the
  robot hears them on `/sim/audio/events` (text) or `/sim/audio/stream` (audio).

## 8. The mind: one LangGraph graph per person

```
 trigger ─► observe ─► recall ─► decide ─► act ─► remember
```

- **Triggers** (event-driven, never a fixed fast loop): heard speech addressed to them or nearby, the robot came
  within N m, a new sign or person in view, own intent finished or failed, a cough nearby, a timer from the persona
  (e.g. patience check every few minutes), scenario events. Debounced so a person makes at most one decision every
  few seconds.
- **observe:** turns the latest observation (oracle JSON, or VLM/ASR output) into a short situation text.
- **recall:** retrieves from three places: the knowledge base (research notes relevant to the situation, e.g. how
  outpatients behave after a 30-minute wait), the person's long-term memory, and their short-term state.
- **decide:** one LLM call with the persona card, recalled snippets and the situation. Output is **structured**
  (schema-validated JSON): intent + parameters, optional words to say, updated mood/patience, and a one-line reason.
  Invalid output falls back to the current intent.
- **act:** publishes the intent and speech.
- **remember:** appends the event to short-term memory; every few minutes, or when short-term memory fills, a cheaper
  model summarises it into long-term memory entries.

One agent-service process runs all five graphs concurrently (asyncio), with rclpy for ROS.

### 8.1 Personas and scenario configuration (files)

`config/personas.yaml`: every persona, each field with a range so instances differ by seed, and a `sources` list
pointing at the research notes the values came from. Fields include: age band, sex, role (patient, companion,
visitor), condition and symptoms (cough rate, severity, fever), mobility and aids, hearing, language and English
fluency, patience, anxiety, sociability, phone use, attitude to robots, goals and schedule (e.g. waiting for a named
clinic), companion links.

`config/scenarios/waiting_area_v1.yaml`: which personas, how many of each, seats or arrival times, duration (up to
60 min), seed, perception mode, LLM provider and model per role, memory snapshot to start from, record on/off.

v1 waiting-area cast (the 3 non-coughing people are proposals drawn from the research notes, to confirm):

| # | Persona | Notes |
|---|---|---|
| 1 | Coughing patient A | adult with a persistent cough (A&E chief complaint "cough" ~436k/yr in England), waiting |
| 2 | Coughing patient B | older adult, cough plus breathlessness, accompanied by #3 |
| 3 | Companion of B | relative; talks for B, asks staff and robot questions |
| 4 | Older outpatient with a walking stick | slow sit-to-stand, hearing reduced |
| 5 | Anxious first-time patient | checks signs and the time, likely to approach the robot |

### 8.2 Memory

| Layer | What | Store | Lifetime |
|---|---|---|---|
| Knowledge base | research notes in `research_notes/` chunked with headings and source links; persona cards; hospital map and sign registry | local vector index (built by a command), read-only during runs | rebuilt when notes change |
| Short-term | last few minutes of observations, what was said, current goal, mood | LangGraph checkpointer (SQLite) per person per run | the run |
| Long-term | summarised episodes and facts ("the robot said clinic 3 is down the corridor", "waited 40 min last time"), with timestamps and importance | LangGraph store (SQLite) with a vector index, one namespace per person | across runs until reset |

- **Standardised:** every person retrieves from the same knowledge base with the same retrieval settings, and
  long-term entries use one schema.
- **Embeddings:** a small local embedding model on CPU/GPU (Claude has no embedding service, and this avoids a second
  key).
- **Identity across runs:** a person's long-term memory is keyed by `persona + instance seed`, so the same seed is the
  same person next run.
- **Reset and snapshots (CLI, mirrored later in the configuration screen):**
  - `hhumans memory reset --person <id> | --persona <name> | --all` → back to the seed state from `personas.yaml`;
  - `hhumans memory snapshot save <name>` / `restore <name>` / `list`;
  - each run records the snapshot it started from and the one it ended with.

### 8.3 LLM providers and models

- Providers: **Claude (Anthropic API)** or **OpenAI API**, chosen per scenario; LangChain chat-model wrappers, so the
  graph code is the same for both.
- Default model roles (configurable per role):

  | Role | Claude default | Why |
  |---|---|---|
  | Person decisions (`decide`) | `claude-opus-5-5`, effort `low` | best persona consistency and judgement; low effort keeps replies to about a second or two |
  | Memory summaries, observation parsing | `claude-haiku-5-5` | frequent, simple, cheap |
  | Full-mode vision (camera frames) | `claude-opus-5-5` | reads signs and scenes |

  `claude-sonnet-5-5` is the cheaper option for decisions if cost matters. OpenAI model names are set in the
  scenario file; defaults are chosen at build time from what the OpenAI API offers then.
- Prompt caching: the persona card and fixed instructions come first in every request so they are cached; only the
  situation and recalled snippets change. Use the 1-hour cache lifetime: decisions can be minutes apart, longer
  than the default 5-minute cache.
- Structured output: use the API's native structured-output mode (`output_config.format` on Claude, the equivalent on
  OpenAI). Do not use a forced tool call: Claude Opus 5.5 and Sonnet 5.5 reject forced `tool_choice` with a 400, and
  LangChain's Anthropic structured-output helper forces one by default. Check that the wrapper passes
  `output_config.effort`; call the Anthropic SDK directly inside the graph node if it does not.
- Latency: thinking cannot be switched off on Opus 5.5, so even at `low` effort a decision may take a few seconds.
  Phase 1 measures Opus 5.5 (low) against Sonnet 5.5 for latency and persona quality and sets the default from the
  measurement. Reflexes give the immediate reaction (head turn to the speaker) so a slow reply still looks natural.
- Rough cost (estimate, to be measured in the first run): 5 people × ~60–120 decisions an hour, ~8k input tokens
  mostly cached, ~300 output tokens → a few dollars to ~$15 per hour-long oracle run on Claude Opus 5.5; full mode
  adds image calls.

### 8.4 API keys (requirement)

- Each user runs on their own developer account (Claude Console or OpenAI Platform, pay-as-you-go). A Claude Pro/Max
  or ChatGPT subscription cannot be used for API calls; the README says so and walks through creating a key and a
  monthly spend limit.
- Storage, in order of preference:
  1. Claude: `ant auth login` (Anthropic CLI OAuth profile, short-lived tokens under `~/.config/anthropic/`);
  2. a key entered once with `hhumans keys set claude|openai`, stored in the OS keyring (GNOME Keyring / Secret
     Service via Python `keyring`);
  3. headless servers: a key file outside the repo, mode 600, path given by an environment variable.
- Only the agent service's LLM gateway reads the key. It never goes into ROS parameters, topics, launch files, logs,
  recordings or the run folder. A pre-commit secret scan guards the repo.
- Start-up check: the agent service makes one tiny authenticated call to the chosen provider; if there is no working
  key it exits with instructions. The scenario does not start.

## 9. Running, recording and replay

- `hhumans run config/scenarios/waiting_area_v1.yaml` starts the sim host, the agent service and (optionally) the G1
  bringup; `--no-robot` runs people only.
- Time: at 600 Hz with 5 people and the G1, the research notes estimate a real-time factor of 0.5-0.8 on the
  RTX 3070 (to measure in spike S3). Where the sim keeps up (RTX 5090 target) it runs locked to the wall clock so LLM
  latency is realistic; where it cannot, it runs on sim time and `--lockstep` pauses the sim while a decision is
  pending, so slow hardware changes speed, not behaviour.
- Three ways to re-run (which ones v1 needs is open, section 14):
  - `replay --exact`: recorded body states and robot commands, for rendering and inspection;
  - `replay --intents`: the people play their recorded intents open loop against a new robot build (a fixed crowd
    that no longer reacts; useful as a regression baseline);
  - `rerun`: same scenario, seed and memory snapshot, live minds; the people react to the new robot, at API cost.
  Exact physical repeat holds only on the same machine and software build (GPU PhysX determinism).
- Every run writes a run folder: scenario + persona files as used, seed, model ids, memory snapshot in/out, every
  observation, prompt, LLM reply and intent, body states (npz like `run_reception.py`), audio events.
- **Replay:** `hhumans replay <run>` re-runs the hour using the recorded decisions instead of calling the LLM (no key
  needed, no cost, exact repeat), e.g. to test a new robot build against the same human behaviour or to render a film.
- Rendering: the existing photoreal pipeline renders chosen spans from the recording.

## 10. Where it lives

- New component folder `hospital-sim-agents/` (agent service, memory, knowledge base, LLM gateway, CLI, config,
  README), its own repository like the other components.
- Sim-host additions (multi-person live scene, motion composer, oracle, audio events, ROS bridge) in
  `hospital-sim-humans/sim/`.
- Topic additions documented in `docs/interfaces.md`.
- Python: the agent service uses `.venv` (Python 3.10, Humble rclpy); the sim host uses Isaac's Python.

## 11. Risks and the first spike

1. **Live motion stitching (highest risk).** The tracker was trained on whole clips; switching intents mid-motion,
   from the current physical state, may make people stumble. *Spike first:* one person in the waiting area cycling
   sit → cough → stand → walk → sit with random switch times, counting falls and seat accuracy, with a video. If it
   fails, options are: longer blends, transition clips from BONES-SEED, or a short fine-tune (needs the user's
   go-ahead).
2. **Cough clips:** BONES-SEED may or may not have seated/standing coughs; fallback is a synthetic overlay (torso and
   head flexion, hand to mouth) like the nod.
3. **Five people + robot on 8 GB:** at 600 Hz with the 2.7 M-triangle collision world, real time is unlikely on the
   RTX 3070 (estimate 0.5-0.8 real-time factor); spike S3 measures it. Full mode is a 5090 target.
5. **Tracker at 600 Hz:** trained at 120 Hz; S3 compares tracking at 120 and 600 Hz (fallback 300 Hz).
6. **Clip access:** the full BONES-SEED library is on the Paperspace server, whose SSH host key changed and has not
   been accepted; locally there are only 61 sample clips. Spikes S1 and S2 need that access restored.
4. **LLM latency spikes / rate limits:** bodies keep the last intent; reflexes keep them alive; decisions are
   debounced.

## 12. Calls made by me (not decided by the user)

- JSON-in-`std_msgs/String` at the sim boundary instead of custom messages (v1).
- Three-layer person (mind / reflexes / body) and the intent vocabulary.
- Default models per role and effort levels; Sonnet 5.5 as the cheaper alternative.
- Local embeddings, local SQLite stores, local ASR (faster-whisper).
- Long-term memory carries across runs, keyed by persona + seed; snapshots for repeatable studies.
- Real-time clock by default, lockstep optional; full decision recording and replay.
- Robot fairness rule (robot may not read `/humans/*`).
- Fall handling by respawn in v1.
- The three non-coughing cast members.

## 13. Left to the builder

- Exact JSON schemas, field names and rates within the shapes above.
- Choice of vector index and embedding model, chunk sizes, retrieval top-k.
- Clip selection and blend lengths in the motion composer.
- Navigation grid and path planning details for the waiting area.
- CLI layout and README structure.

## 14. Storyboard and scenario control (added 2026-11-03, user request)

- **Storyboard:** when WardZero launches, a storyboard (`config/storyboards/*.yaml`) plays from t = 0. Its beats fire
  at a time, on a condition (for example "robot within 2 m of P5") or when the previous beat ends.
- **Scenario cards** (`config/cards/*.yaml`) are ready-made situations that test the robot: a lost visitor, a coughing
  fit, a person hard of hearing, a name called, an impatient patient, a blocked path, a wet floor, a new arrival, a
  fire alarm (starter deck, proposals). A card acts through three channels only:
  - a mind nudge (a goal or feeling given to a person, who decides how to act);
  - a reflex override (for example a 40 s coughing bout);
  - a world event (a PA call, an alarm sound, a wet-floor sign, a person arriving or leaving).
  Cards never address the robot. The robot meets only the consequences, through its sensors and microphones.
- **Scenario director:** a ROS 2 node that runs the storyboard, triggers and an optional seeded chaos mode (random cards
  from a weighted deck). Topics: `/scenario/timeline`, `/scenario/events`, `/humans/{id}/nudge`,
  `/humans/{id}/reflex`, `/sim/world_event`. Every beat and card firing (who, when, parameters) goes into the run
  folder, so replays reproduce hand-fired cards.
- **Scenario control panel:** a local browser page served by the director. It shows the timeline, a floor map with
  each person's position, posture and mood, their last decision, its reason and their last words, an event log, the
  cost and the recording status. It can start, pause, stop and reset the run, fire any card at a chosen person with
  parameters, toggle chaos mode and save memory snapshots. It is for the experimenter, so it may show the people's
  minds; the robot may not read `/scenario/*` or `/humans/*`. Authoring personas and cards in the panel is v2.

## 15. Decisions and open questions (updated 2026-11-03)

Decided by the user:
- slower than real time is acceptable on the RTX 3070;
- long-term memory carries across runs by default, with reset;
- the repository must not depend on the Paperspace server: motion data is fetched locally from Hugging Face by a repo
  script. The `soma_uniform.tar.gz` archive is 45.2 GB and cannot be partly downloaded (gzip), so the script streams it
  through `tar` and keeps only the listed clips, then converts and deletes BVH files in batches
  (`server/convert_stream.sh` pattern). The PC has about 24 GB free;
- a storyboard plus a scenario control panel (section 14).

Still open:
1. What does the G1 do during the hour, and who drives it: a teleoperator, a scripted mission, or a standing robot
   that only speaks? No trained G1 walking policy exists yet.
2. Main-entrance lobby or the A&E waiting area? Is the nurse who calls names a visible person or a voice only?
3. Which re-run modes does v1 need: exact replay, open-loop intents, live re-run, or all three?
4. Confirm the starter storyboard beats and card deck.
5. Confirm the three non-coughing cast members.
