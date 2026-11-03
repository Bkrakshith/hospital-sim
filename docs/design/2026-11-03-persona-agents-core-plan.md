# WardZero Persona Agents, Plan 1 of 3: core (minds, memory, director, panel, stub sim) Implementation Plan


**Goal:** A runnable WardZero persona system on the RTX 3070 without Isaac: five LLM-driven persona minds with
memory and research-notes RAG, reflexes, a storyboard and scenario director with a browser control panel, run
recording and three re-run modes, all talking over ROS 2 to a kinematic stub sim host that stands in for Isaac until
Plan 2.

**Architecture:** A new component `hospital-sim-agents/` (Python package `wardzero_agents`, CLI `hhumans`) holds
pure-Python cores (config, contracts, gateway, memory, knowledge base, reflexes, mind graph, director, world oracle,
stub world) wrapped by thin rclpy nodes (agent service, director with panel, stub sim, example reception robot). The
stub sim speaks exactly the topics the Isaac sim host will speak in Plan 2, so Plan 2 swaps the body without touching
the minds. Motion clips are placeholders: a clip catalogue with fallbacks, and a BONES-SEED fetch script that is
written but not run.

**Tech Stack:** Python 3.10 (`.venv`, `source env.sh`), ROS 2 Humble rclpy, CycloneDDS, LangGraph +
langgraph-checkpoint-sqlite, official `anthropic` and `openai` SDKs, pydantic 2, PyYAML, numpy, aiohttp, keyring,
SQLite, pytest.

**Spec:** `docs/design/2026-11-03-human-persona-agents-design.md` (sections 1-15) and the PRD
`docs/product/human-persona-agents-prd.html` (requirements FR-1..FR-25, NFR-1..NFR-9).

**Defaults taken for the spec's open questions (user: "rest is okay, build it out", 2026-11-03):** the G1 in v1 is a
standing robot at reception that speaks (no walking policy); main-entrance lobby; the nurse and PA are voice-only;
all three re-run modes; starter storyboard and card deck as in PRD section 05; cast P1-P5 as proposed.

**Follow-up plans (not in this plan):**
- Plan 2, Isaac sim host: spikes S1 (streaming motion source + live stitching) and S3 (5 people + G1 under a 600 Hz
  tick scheduler, tracker at 120 vs 600 Hz), physics people speaking the same topics as `stub_sim`, standing G1 with
  `/g1/speech/say`, people in the G1's lidar and head camera, line-of-sight ray casts for the oracle, sign poses exported
  from the USD into `config/signs.yaml`, body npz recording, `--sim isaac`.
- Plan 3, full perception: head cameras on events, vision-model observation adapter, scene audio mix, faster-whisper
  ASR, robot TTS, README service setup, RTX 5090 tuning.
- After the user frees disk space: run `scripts/fetch_bones_seed.sh` (Task 15) and fill `clips_v1.yaml`.

## Global Constraints

- Python 3.10 in `$HG1_ROOT/.venv`; every command starts with `source $HG1_ROOT/env.sh`. Install with `.venv/bin/pip`.
- ROS 2 Humble, `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`; every node runs with `use_sim_time:=true` and takes time from `/clock`.
- Sim-boundary messages are JSON in `std_msgs/String`; every payload carries `"schema": "wz.v1"`.
- Model ids exactly: `claude-opus-5-5` (decide, vision), `claude-haiku-5-5` (summarise), `claude-sonnet-5-5` (cheaper option). OpenAI models have no defaults: the scenario must name them.
- Claude requests: `output_config.format` json_schema (never forced `tool_choice`), `output_config.effort` (`low` for decide and summarise), no `thinking` parameter, persona card block with `cache_control {"type":"ephemeral","ttl":"1h"}`; for `claude-opus-5-5` and `claude-sonnet-5-5` also `betas=["server-side-fallback-2026-07-01"]`, `fallbacks="default"` via `client.beta.messages.create`; check `stop_reason == "refusal"` before reading content.
- Secrets never appear in ROS parameters, topics, logs, run folders or git. Keyring service name `wardzero-agents`.
- No key, no run: the only exception is `WARDZERO_TEST_FAKE_LLM=1`, which is for tests, prints `TEST MODE: no AI provider`, and sets `test_mode: true` in the run meta.
- Robot fairness: no node outside the `wardzero_` prefix may subscribe to `/humans/`, `/scenario/`, `/sim/audio/events` or `/sim/world_event`. The robot hears only `/g1/audio/heard`.
- Data directory: `$WARDZERO_DATA_DIR`, default `~/.local/share/wardzero-agents/` (memory, snapshots, kb index). Run folders: `$HG1_ROOT/hospital-sim-agents/runs/` (gitignored).
- No downloads in this plan: the default embedder is the local `HashEmbedder`; `fastembed` is an optional extra; BONES-SEED is not fetched.
- Licensed data (BONES-SEED and derived clips) is never committed. Research notes keep their citations.
- No AI attribution lines in commits, files or docs. Commits are plain messages.
- `hospital-sim-agents/` is its own git repository (`git init`, branch `main`, no remote yet), like the other components.

## Review Focus

1. The LLM call fails mid-run (refusal, invalid JSON, timeout, 429, network down): the person keeps their current intent and reflexes, the run continues, the failure is logged. Tests: Task 4 `test_refusal_maps_to_error`, `test_invalid_json`, Task 8 `test_failed_decision_keeps_intent`.
2. The key is missing, rejected, or the key file is world-readable: the run refuses to start with a fix-it message, and the key never appears in output. Tests: Task 3 `test_key_file_mode_refused`, `test_redact`, Task 14 `test_run_without_key_refuses`.
3. Scenario files with mistakes (unknown persona, two people in one seat, an unknown seat, `companion_of` pointing nowhere, OpenAI without model names): one-line error naming the field. Tests: Task 1.
4. A card or beat targets a person who has left or never existed: the card is rejected with a reason in the event log and the panel, and nothing else breaks. Test: Task 11 `test_card_for_missing_person_rejected`.
5. A memory reset or snapshot restore while a run is active: refused with a message naming the run. Test: Task 6 `test_reset_refused_during_run`.

---

## File map

```
hospital-sim-agents/
  pyproject.toml                      package wardzero_agents, script hhumans, extras [embed]
  README.md                           setup, accounts and keys, run, panel, memory, kb, replay, modes, motion data, costs
  .gitignore                          runs/, *.sqlite, __pycache__/
  scripts/gen_waiting_area.py         seats + landmarks from hospital-sim-humans/sim/lobby_chairs.py
  scripts/check_secrets.sh            pre-commit secret scan; scripts/install_hooks.sh
  config/personas.yaml  config/waiting_area.yaml  config/signs.yaml
  config/scenarios/waiting_area_v1.yaml  config/storyboards/waiting_area_day.yaml  config/cards/starter.yaml
  wardzero_agents/
    config/models.py  config/loader.py  config/sampling.py
    contracts.py
    keys.py
    llm/gateway.py  llm/anthropic_backend.py  llm/openai_backend.py  llm/fake.py  llm/pricing.py
    kb/chunker.py  kb/embed.py  kb/index.py
    memory/longterm.py  memory/snapshots.py  memory/runlock.py
    reflex.py
    world/oracle.py  world/audio.py  world/stub_world.py
    mind/prompts.py  mind/triggers.py  mind/graph.py  mind/runtime.py
    runlog.py  replay.py
    director/storyboard.py  director/cards.py  director/chaos.py
    panel/server.py  panel/static/index.html
    ros/topics.py  ros/fairness.py  ros/agent_node.py  ros/director_node.py  ros/stub_sim_node.py  ros/replay_node.py
    examples/reception_bot.py
    cli.py
  tests/ (one test file per module, plus tests/integration/test_end_to_end.py)
hospital-sim-humans/motion/clip_catalog.py  motion/clips_v1.yaml  scripts/fetch_bones_seed.sh  tests/test_clip_catalog.py
docs/interfaces.md                    new section 3.x "Persona agents"
```

---

### Task 1: Component scaffold, configuration schemas and the waiting-area configs

**Files:**
- Create: `hospital-sim-agents/pyproject.toml`, `.gitignore`, `wardzero_agents/__init__.py`, `wardzero_agents/config/{__init__,models,loader,sampling}.py`
- Create: `scripts/gen_waiting_area.py`, `config/personas.yaml`, `config/waiting_area.yaml` (generated), `config/signs.yaml`, `config/scenarios/waiting_area_v1.yaml`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces (`config/models.py`, pydantic v2, `extra="forbid"` everywhere):
  - `Range = tuple[float, float]` (validator: lo <= hi)
  - `Symptoms(cough_per_hour: Range = (0, 0), cough_severity: Literal["mild","moderate","severe"] = "mild", breathless: bool = False, fever: bool = False)`
  - `Mobility(aid: Literal["none","stick","frame","wheelchair"] = "none", walk_speed: Range, sit_to_stand_s: Range)`
  - `Persona(id, label, role: Literal["patient","companion","visitor","staff"], age: Range, sex: list[str], condition: str, symptoms: Symptoms, mobility: Mobility, hearing_loss_db: Range = (0, 0), english_fluency: Literal["native","fluent","limited"] = "native", patience_min: Range, anxiety: Range, sociability: Range, phone_use: Range, attitude_to_robots: Literal["curious","neutral","wary"], goals: list[str], backstory: str, seed_memories: list[str] = [], sources: list[str])`
  - `CastEntry(id: str, persona: str, seat: str | None = None, arrive_at_s: float = 0, entrance: str | None = None, companion_of: str | None = None, seed: int | None = None)`
  - `ModelRoles(decide: str, summarise: str, vision: str, effort_decide: Literal["low","medium","high"] = "low")`
  - `Chaos(enabled: bool = False, rate_per_hour: float = 6.0)`
  - `RobotConfig(enabled: bool = True, x: float = 1.05, y: float = 1.62, yaw: float = -1.5708)`
  - `Scenario(id, area: str, duration_min: float (0 < v <= 60), seed: int, perception: Literal["oracle","full"] = "oracle", provider: Literal["claude","openai"], models: ModelRoles | None = None, budget_usd: float = 20.0, storyboard: str, deck: str, chaos: Chaos = Chaos(), memory_snapshot: str | None = None, lockstep: bool = False, robot: RobotConfig = RobotConfig(), cast: list[CastEntry])`
  - `Seat(id, x, y, yaw, row)`, `Landmark(x, y, label)`, `WaitingArea(seats: list[Seat], landmarks: dict[str, Landmark], entrance: str, exits: list[str], nurse_call_point: str)`
  - `Sign(id, text, x, y, z, facing_yaw, read_distance_m: float = 6.0, placeholder: bool = True)`
  - `PersonInstance(person_id, persona_id, seed, memory_key, display_name, age: int, sex, cough_per_hour: float, cough_severity, breathless, walk_speed: float, sit_to_stand_s: float, hearing_loss_db: float, patience_min: float, anxiety: float, sociability: float, phone_use: float, attitude_to_robots, english_fluency, mobility_aid, goals, backstory, condition, role, seat, companion_of, arrive_at_s, entrance)`
- Produces (`config/loader.py`): `class ConfigError(Exception)`; `load_scenario(path: str | Path) -> LoadedScenario` where `LoadedScenario(scenario, personas: dict[str, Persona], area: WaitingArea, signs: list[Sign], storyboard: Storyboard, deck: dict[str, CardDef], instances: list[PersonInstance], root: Path)` (Storyboard and CardDef models are added in Task 11; until then the loader leaves those two fields `None`); `default_models(provider) -> ModelRoles` (claude only; raises `ConfigError` for openai).
- Produces (`config/sampling.py`): `sample_instance(persona: Persona, cast: CastEntry, scenario_seed: int, index: int) -> PersonInstance`. Instance seed = `cast.seed` if given else `scenario_seed * 1000 + index`; `memory_key = f"{persona.id}#{seed}"`; every range sampled uniformly from `numpy.random.default_rng(seed)` in field order; `display_name` from a fixed list of 40 common UK first names plus 40 surnames, seeded.

- [ ] **Step 1: Create the repo and package.** `git init -b main hospital-sim-agents`; pyproject with deps `anthropic>=1.0`, `openai>=1.40`, `langgraph`, `langgraph-checkpoint-sqlite`, `pydantic>=2`, `pyyaml`, `numpy`, `aiohttp`, `keyring`; extra `embed = ["fastembed"]`; script `hhumans = "wardzero_agents.cli:main"`. Install: `.venv/bin/pip install -e hospital-sim-agents` (not the extra). `.gitignore`: `runs/`, `*.sqlite`, `__pycache__/`, `.pytest_cache/`.

- [ ] **Step 2: Write `scripts/gen_waiting_area.py`.** It imports `$HG1_ROOT/hospital-sim-humans/sim/lobby_chairs.py` and writes `config/waiting_area.yaml`:
  - **Seats:** 12, ids `A1..D3`, where rows A-D follow `ROWS` order and numbers follow `ARM_X` order from armrest 0.
    - x is the midpoint between adjacent armrests, mirrored for north rows (south row: `x0 + (ARM_X[k] + ARM_X[k+1])/2`; north row: `x1 - (...)`).
    - y is `y0 + 0.30` for `FACES_SOUTH` rows and `y1 - 0.30` for `FACES_NORTH` rows.
    - yaw is -pi/2 for south rows and +pi/2 for north rows.
  - **Landmarks:**
    - `reception_g1 (1.05, 1.62)`
    - `reception_front (1.00, 0.57)`
    - `entrance (-1.24, -2.30)`
    - `clinic_corridor (5.60, 5.40)`
    - `ward_doors (11.20, 7.25)`
    - `toilets (-11.50, 1.20)` (placeholder)
    - `nurse_call_point (5.60, 3.00)` (placeholder)
  - `entrance: entrance`; `exits: [entrance, clinic_corridor, ward_doors]`; `nurse_call_point: nurse_call_point`.
  - Run it and commit the output.

- [ ] **Step 3: Write `config/personas.yaml` (5 personas, values cited in `sources`).**

  | id | role | age | cough_per_hour | severity | walk_speed | sit_to_stand_s | hearing_loss_db | patience_min | aid |
  |---|---|---|---|---|---|---|---|---|---|
  | `coughing_adult` | patient | 25-55 | 20-40 | moderate | 1.2-1.4 | 1.5-2.5 | 0-5 | 30-60 | none |
  | `coughing_older_adult` | patient | 68-82 | 30-60 (breathless) | severe | 0.7-0.9 | 3-5 | 10-20 | 40-80 | none |
  | `companion` | companion | 40-65 | 0 | mild | 1.1-1.3 | 1.5-2.5 | 0-5 | 25-45 | none |
  | `older_outpatient_stick` | patient | 72-88 | 0 | mild | 0.6-0.8 | 4-7 | 25-40 | 45-90 | stick |
  | `anxious_first_timer` | patient | 20-40 | 0 | mild | 1.2-1.4 | 1.5-2.5 | 0-5 | 15-30 | none |

  - **Sources:** each persona lists paths under `research_notes/UK hospital visitor personas/`: `patient_personas.md`, `ae_outpatient_flows.md`, `mobility_aids.md`, `movement_mobility.md`, `robot_interaction.md`, `visitor_behaviour.md`.
  - **Other fields:**
    - anxiety, sociability and phone_use are ranges in 0..1;
    - attitude: `anxious_first_timer` is curious, `older_outpatient_stick` is wary, the others are neutral;
    - each persona has 2-3 goals and 1-2 seed memories.

- [ ] **Step 4: Write `config/signs.yaml`.** Use the 6 placeholder signs below, all with `placeholder: true`. Plan 2 replaces them with poses exported from the USD.

  | id | text | x, y, z |
  |---|---|---|
  | `sign_reception` | "Reception" | 1.7, 4.3, 2.4 |
  | `sign_clinics` | "Outpatient clinics 1-6 →" | 5.0, 2.0, 2.3 |
  | `sign_wards` | "Wards A-D and lifts →" | 10.5, 6.0, 2.3 |
  | `sign_toilets` | "← Toilets" | -9.5, 1.8, 2.3 |
  | `sign_exit` | "Way out" | -1.2, -2.4, 2.6 |
  | `sign_wait` | "Please take a seat. You will be called." | -6.3, 1.9, 2.0 |

- [ ] **Step 5: Write `config/scenarios/waiting_area_v1.yaml`.**
  - Settings: `id: waiting_area_v1`, `area: waiting_area`, `duration_min: 60`, `seed: 7`, `provider: claude`, `storyboard: ../storyboards/waiting_area_day.yaml`, `deck: ../cards/starter.yaml`.
  - Cast:
    - P1 `coughing_adult` seat B2
    - P2 `coughing_older_adult` seat C1
    - P3 `companion` seat C2, `companion_of: P2`
    - P4 `older_outpatient_stick` seat A3
    - P5 `anxious_first_timer` seat D2
  - The storyboard and deck files are created in Task 11, so the loader tolerates their absence until then.

- [ ] **Step 6: Write the failing tests in `tests/test_config.py`.**

```python
def test_loads_v1(): ls = load_scenario(CFG/"scenarios/waiting_area_v1.yaml"); assert [i.person_id for i in ls.instances] == ["P1","P2","P3","P4","P5"]; assert len(ls.area.seats) == 12
def test_sampling_is_deterministic(): a = load_scenario(V1).instances; b = load_scenario(V1).instances; assert a == b
def test_ranges_respected(): p2 = inst("P2"); assert 68 <= p2.age <= 82 and 30 <= p2.cough_per_hour <= 60 and p2.memory_key == "coughing_older_adult#7001"
def test_default_models_claude(): assert load_scenario(V1).scenario.models == ModelRoles(decide="claude-opus-5-5", summarise="claude-haiku-5-5", vision="claude-opus-5-5")
@pytest.mark.parametrize("patch,msg", [
  ({"cast.2.persona": "nobody"}, "cast[2].persona: unknown persona 'nobody'"),
  ({"cast.1.seat": "B2"}, "cast[1].seat: seat 'B2' already taken by P1"),
  ({"cast.0.seat": "Z9"}, "cast[0].seat: unknown seat 'Z9'"),
  ({"cast.2.companion_of": "P9"}, "cast[2].companion_of: unknown person 'P9'"),
  ({"provider": "openai"}, "models: OpenAI needs model names for decide, summarise and vision"),
  ({"duration_min": 90}, "duration_min"),
])
def test_config_errors(tmp_path, patch, msg): with pytest.raises(ConfigError, match=re.escape(msg)): load_scenario(write_patched(tmp_path, V1, patch))
def test_persona_sources_exist(): for p in load_scenario(V1).personas.values(): assert all((HG1_ROOT/"research_notes"/s).exists() for s in p.sources)
```

- [ ] **Step 7: Run and confirm the tests fail.** Run `source env.sh && cd hospital-sim-agents && pytest tests/test_config.py -q`. Expected: FAIL (import error).
- [ ] **Step 8: Implement `models.py`, `sampling.py` and `loader.py`.** The loader resolves storyboard and deck paths relative to the scenario file. Cross-reference checks live in the loader. Error messages use the exact text from the tests, formatted `<field path>: <problem>`.
- [ ] **Step 9: Run and confirm the tests pass.** Same command. Expected: PASS.
- [ ] **Step 10: Commit.** `git add -A && git commit -m "Scaffold wardzero_agents with config schemas and waiting-area configs"`

---

### Task 2: Sim-boundary contracts and topic names

**Files:**
- Create: `wardzero_agents/contracts.py`, `wardzero_agents/ros/topics.py`
- Test: `tests/test_contracts.py`

**Interfaces:**
- Produces (`contracts.py`): `SCHEMA = "wz.v1"`; `class ContractError(ValueError)`; `IntentKind = Literal["sit_idle","use_phone","fidget","look_at","read_sign","stand_up","sit_down","walk_to","approach","wait_standing","talk","gesture","cough","leave"]`; models (pydantic, each with `schema_: Literal["wz.v1"] = Field("wz.v1", alias="schema")`):
  - `Intent(id: str, person: str, t: float, kind: IntentKind, target: str | None = None, point: tuple[float, float] | None = None, speed: float | None = None, style: str | None = None, text: str | None = None, addressee: str | None = None, overlay: bool = False)`
  - `Status(person, t, x, y, yaw, posture: Literal["seated","standing","walking","fallen","gone"], intent_id: str | None, intent_kind: IntentKind | None, progress: float, state: Literal["running","done","failed","idle"], reason: str | None = None)`
  - `Seen(kind: Literal["person","robot","sign","seat"], id, distance, bearing_deg, detail: str | None = None)`; `Heard(source_kind: Literal["robot","person","pa","cough","alarm"], source_id, text: str | None, received_db: float, partial: bool, addressed_to_me: bool)`; `Observation(person, t, visible: list[Seen], heard: list[Heard])`
  - `AudioEvent(id, t, source_kind, source_id, x, y, z, loudness_db, text: str | None = None, addressee: str | None = None)`
  - `Say(person, t, text, addressee: str | None = None)`
  - `Nudge(person, t, card: str, message: str)`; `ReflexOverride(person, t, kind: Literal["cough_bout"], duration_s: float, severity: Literal["mild","moderate","severe"])`
  - `WorldEvent(id, t, kind: Literal["pa_announcement","alarm","wet_floor","arrival","person_exit"], text: str | None = None, x: float | None = None, y: float | None = None, persona: str | None = None, person: str | None = None)`
  - `RosterEntry(id, persona, display_name, seat: str | None, companion_of: str | None)`; `Roster(t, people: list[RosterEntry])`; `Control(action: Literal["start","pause","resume","stop","reset"])`
  - `to_json(m) -> str` (by_alias); `from_json(cls, s: str) -> model` (raises `ContractError` on bad JSON, wrong schema or validation error)
- Produces (`ros/topics.py`): `ROSTER="/humans/roster"`, `status(pid)`, `intent(pid)`, `observation(pid)`, `say(pid)`, `nudge(pid)`, `reflex(pid)` → `/humans/{pid}/<name>`; `AUDIO_EVENTS="/sim/audio/events"`, `G1_HEARD="/g1/audio/heard"`, `G1_SAY="/g1/speech/say"`, `WORLD_EVENT="/sim/world_event"`, `TIMELINE="/scenario/timeline"`, `SCEN_EVENTS="/scenario/events"`, `CONTROL="/scenario/control"`, `PENDING="/agents/pending"`, `FORBIDDEN_FOR_ROBOT=("/humans/","/scenario/","/sim/audio/events","/sim/world_event")`.

- [ ] **Step 1: Write the failing tests.**

```python
def test_roundtrip_intent(): i = Intent(id="a", person="P5", t=1.0, kind="walk_to", target="clinic_corridor"); assert from_json(Intent, to_json(i)) == i; assert json.loads(to_json(i))["schema"] == "wz.v1"
def test_wrong_schema_rejected(): with pytest.raises(ContractError): from_json(Intent, '{"schema":"wz.v0","id":"a","person":"P1","t":0,"kind":"sit_idle"}')
def test_unknown_intent_kind_rejected(): with pytest.raises(ContractError): from_json(Intent, to_json_dict_with(kind="dance"))
def test_topic_names(): assert intent("P1") == "/humans/P1/intent" and G1_HEARD == "/g1/audio/heard"
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_contracts.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `contracts.py` and `topics.py`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add wz.v1 sim-boundary contracts and topic names"`

---

### Task 3: Keys, redaction and secret scan

**Files:**
- Create: `wardzero_agents/keys.py`, `scripts/check_secrets.sh`, `scripts/install_hooks.sh`
- Test: `tests/test_keys.py`

**Interfaces:**
- Produces:
  - `SERVICE = "wardzero-agents"`
  - Exceptions: `KeyMissing(Exception)`, `KeyRejected(Exception)`, `ModelUnavailable(Exception)`. Each message gives the fix: "No working Claude key. Run `hhumans keys set claude` or `ant auth login`."
  - `set_key(provider: Literal["claude","openai"], secret: str) -> None` stores the key in the keyring.
  - `clear_key(provider) -> None`.
  - `get_key(provider) -> str | None` checks in order:
    1. the keyring;
    2. the JSON file at `$WARDZERO_KEY_FILE` (`{"claude": "...", "openai": "..."}`). If `stat.st_mode & 0o077`, it raises `KeyMissing("... key file must be mode 600 ...")`;
    3. otherwise `None`.
  - `make_client(provider) -> anthropic.AsyncAnthropic | openai.AsyncOpenAI`:
    - **claude:** `AsyncAnthropic(api_key=key)` if `get_key` returns one, else `AsyncAnthropic()`, which lets the SDK resolve `ANTHROPIC_API_KEY` or the `ant auth login` profile.
    - **openai:** the key, or `OPENAI_API_KEY`, else `KeyMissing`.
  - `async check(provider, client, model: str) -> None` calls `client.models.retrieve(model)`. Authentication errors map to `KeyRejected`, not-found to `ModelUnavailable`, and a missing credential to `KeyMissing`.
  - `redact(text: str) -> str` replaces `sk-ant-[A-Za-z0-9_\-]{8,}` and `sk-[A-Za-z0-9_\-]{16,}` with `[redacted]`.
  - `install_log_redaction() -> None` adds a `logging.Filter` to the root logger that redacts `record.msg` and `record.args`.
- `scripts/check_secrets.sh`: greps staged files (`git diff --cached --name-only`) for the two patterns and exits 1, naming the file but not the match. `install_hooks.sh` links it as `.git/hooks/pre-commit` in this repo.

- [ ] **Step 1: Write the failing tests.** Use `keyring.backends.null` swapped for an in-memory backend fixture, and `monkeypatch` the environment.

```python
def test_set_get_clear(memkeyring): set_key("claude","sk-ant-test-123456789"); assert get_key("claude")=="sk-ant-test-123456789"; clear_key("claude"); assert get_key("claude") is None
def test_key_file_mode_refused(tmp_path, monkeypatch): f=tmp_path/"k.json"; f.write_text('{"claude":"sk-ant-x-123456789"}'); f.chmod(0o644); monkeypatch.setenv("WARDZERO_KEY_FILE", str(f)); with pytest.raises(KeyMissing, match="mode 600"): get_key("claude")
def test_key_file_600_ok(...): f.chmod(0o600) ... assert get_key("claude").startswith("sk-ant-")
def test_redact(): assert "sk-ant" not in redact("key sk-ant-api03-abcdefghijk end") and "[redacted]" in redact("sk-proj-abcdefghijklmnopqrstu")
def test_log_redaction(caplog): install_log_redaction(); logging.getLogger("x").warning("got %s", "sk-ant-api03-abcdefghijk"); assert "abcdefghijk" not in caplog.text
async def test_check_maps_auth_error(): client = FakeModels(raises=anthropic.AuthenticationError(...)); with pytest.raises(KeyRejected): await check("claude", client, "claude-opus-5-5")
def test_check_secrets_script(tmp_git_repo): stage file containing "sk-ant-api03-abcdefghijk"; assert subprocess.run(["bash", SCRIPT], cwd=tmp_git_repo).returncode == 1
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_keys.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `keys.py` and the two scripts.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS. Then run `bash scripts/install_hooks.sh`.
- [ ] **Step 5: Commit.** `git commit -am "Add key storage, start-up check, log redaction and secret scan hook"`

---

### Task 4: LLM gateway (Claude, OpenAI, fake), pricing and budget

**Files:**
- Create: `wardzero_agents/llm/{__init__,gateway,anthropic_backend,openai_backend,fake,pricing}.py`
- Test: `tests/test_gateway.py`

**Interfaces:**
- Produces (`gateway.py`):
  - `LLMRequest(role: Literal["decide","summarise","vision"], person: str, system_fixed: str, persona_card: str, user: str, schema: dict, images: list[bytes] = [])`
  - `LLMResult(ok: bool, data: dict | None, error: Literal["refusal","invalid_json","timeout","rate_limited","budget","provider_error"] | None, model: str, input_tokens: int, output_tokens: int, cache_read_tokens: int, cache_write_tokens: int, cost_usd: float | None, latency_s: float)`
  - `class Gateway(Protocol): async def complete(self, req: LLMRequest) -> LLMResult`
  - `class Budget(limit_usd: float)`: `charge(usd: float | None)`, `exhausted -> bool`, `spent -> float`
  - `make_gateway(provider, roles: ModelRoles, budget: Budget, on_usage: Callable[[LLMRequest, LLMResult], None]) -> Gateway` returns `FakeGateway` when `WARDZERO_TEST_FAKE_LLM=1`, otherwise the provider backend built on `keys.make_client`.
- Produces (`pricing.py`): `PRICES = {"claude-opus-5-5": (4.00, 20.00, 0.20), "claude-sonnet-5-5": (2.00, 10.00, 0.20), "claude-haiku-5-5": (0.10, 0.50, 0.01)}`, given in $ per MTok as (input, output, cache read); cache writes are billed at 1.25 × input. `cost(model, usage) -> float | None` returns `None` for unknown models (OpenAI), which get tokens only.
- Produces (`anthropic_backend.py`): `AnthropicGateway(client, roles, budget, on_usage, timeout_s=30.0)`.
  - **Request (exact shape):** `client.beta.messages.create(model=M, max_tokens=4096 if decide else 1024, system=[{"type":"text","text":system_fixed},{"type":"text","text":persona_card,"cache_control":{"type":"ephemeral","ttl":"1h"}}], messages=[{"role":"user","content":user_blocks}], output_config={"effort": roles.effort_decide if decide else "low", "format":{"type":"json_schema","schema":schema}}, **FALLBACK)`
    - `FALLBACK = {"betas":["server-side-fallback-2026-07-01"],"fallbacks":"default"}` applies only when M is `claude-opus-5-5` or `claude-sonnet-5-5`; otherwise it is `{}`.
    - Images go in as base64 image blocks before the text.
  - **Errors:** a refusal returns `error="refusal"`. The first text block goes through `json.loads`, and a failure returns `invalid_json`. `anthropic.RateLimitError` maps to `rate_limited`, `APITimeoutError` or `asyncio.TimeoutError` to `timeout`, and other `APIStatusError` or `APIConnectionError` to `provider_error`.
  - **Budget:** `budget.exhausted` is checked before the call and returns `error="budget"` with no call made.
- Produces (`openai_backend.py`): `OpenAIGateway(client, roles, budget, on_usage)`, calling `client.responses.create(model=M, instructions=system_fixed + "\n\n" + persona_card, input=user, text={"format":{"type":"json_schema","name":req.role,"schema":schema,"strict":True}})` and parsing `response.output_text`. **Verify** this shape against the installed `openai` package docs (`pip show openai`, and the README in site-packages) before writing it, and adjust only the call syntax.
- Produces (`fake.py`): `FakeGateway(policy: Callable[[LLMRequest], dict] | None = None)`. The default policy is rule-based and deterministic, and is used by tests and the end-to-end test:
  - If the user text contains "ROBOT SAID TO YOU", it replies `say: "Thank you"` and walks to the landmark named in the robot speech if one matches, else `wait_standing`.
  - If it contains "NUDGE:", it follows the nudge: walk to a named landmark, or approach `g1` and say "Excuse me, can you help us?" when the nudge contains "help".
  - Otherwise it returns `sit_idle`.
  - Usage is all zero, and the cost is 0.

- [ ] **Step 1: Write the failing tests.** Use a `FakeAnthropicClient` that records kwargs and returns canned `Message`-like objects.

```python
async def test_request_shape_opus(): gw, client = make_anthropic(model="claude-opus-5-5"); await gw.complete(REQ_DECIDE)
    kw = client.calls[0]; assert kw["output_config"]["format"]["type"] == "json_schema" and kw["output_config"]["effort"] == "low"
    assert kw["system"][1]["cache_control"] == {"type":"ephemeral","ttl":"1h"} and kw["fallbacks"] == "default" and "tool_choice" not in kw and "thinking" not in kw
async def test_haiku_has_no_fallbacks(): ... role="summarise" -> model "claude-haiku-5-5"; assert "fallbacks" not in kw and "betas" not in kw
async def test_refusal_maps_to_error(): client returns stop_reason="refusal"; r = await gw.complete(REQ); assert not r.ok and r.error == "refusal"
async def test_invalid_json(): text block "not json" -> r.error == "invalid_json"
async def test_rate_limit(): client raises anthropic.RateLimitError -> r.error == "rate_limited"
async def test_budget_blocks_call(): budget = Budget(0.0); r = await gw.complete(REQ); assert r.error == "budget" and client.calls == []
def test_pricing(): assert cost("claude-opus-5-5", Usage(input=1_000_000, output=0, cache_read=0, cache_write=0)) == pytest.approx(4.0); assert cost("gpt-x", ...) is None
async def test_fake_policy_robot_speech(): r = await FakeGateway().complete(req(user="ROBOT SAID TO YOU: clinic_corridor is down there")); assert r.data["intent"]["kind"] == "walk_to" and r.data["say"] == "Thank you"
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_gateway.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the five modules.** `on_usage` is called for every completed or failed call.
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add LLM gateway with Claude and OpenAI backends, pricing, budget and fake policy"`

---

### Task 5: Knowledge base (chunker, embedders, index)

**Files:**
- Create: `wardzero_agents/kb/{__init__,chunker,embed,index}.py`
- Test: `tests/test_kb.py`

**Interfaces:**
- Produces (`chunker.py`): `Chunk(id: str, file: str, heading_path: list[str], text: str, links: list[str])`; `chunk_markdown(path: Path, root: Path, max_chars: int = 1200) -> list[Chunk]`.
  - Split on `#`/`##`/`###` headings and keep the heading path.
  - Split oversized sections at paragraph boundaries.
  - `id = f"{relpath}#{n}"`.
  - `links` holds the `https?://` URLs found in that chunk.
- Produces (`embed.py`): `class Embedder(Protocol): name: str; dim: int; def embed(self, texts: list[str]) -> np.ndarray` (float32, L2-normalised rows). Two implementations:
  - `HashEmbedder(dim=384)`, the default: lower-cased word unigrams and bigrams, `blake2b` → index and sign, then summed and normalised.
  - `FastEmbedder(model="BAAI/bge-small-en-v1.5")`: imported lazily, raising a clear error if `fastembed` is not installed.
  - `get_embedder(name: str) -> Embedder`.
- Produces (`index.py`): `KnowledgeBase.build(chunks, embedder) -> KnowledgeBase`; `.save(dir)` writes `chunks.jsonl`, `vectors.npy` and `meta.json {embedder, dim, built_at, sources_sha256}`; `KnowledgeBase.load(dir, embedder)` raises if the embedder name or dim differs; `.search(query: str, k: int = 4) -> list[tuple[Chunk, float]]` uses cosine similarity.
- Produces: `build_default_kb(hg1_root: Path, loaded: LoadedScenario, embedder) -> KnowledgeBase`. Sources:
  - every `*.md` under `research_notes/`;
  - one synthetic chunk per persona card (`persona_card(instance)` from Task 8, or a plain YAML dump until then);
  - one chunk listing the landmarks and sign texts.

- [ ] **Step 1: Write the failing tests.**

```python
def test_chunks_keep_headings_and_links(tmp_path): md = "# A\n## B\ntext https://x.org/a\n"; c = chunk_markdown(write(md), tmp_path)[0]; assert c.heading_path == ["A","B"] and c.links == ["https://x.org/a"]
def test_hash_embedder_normalised(): v = HashEmbedder().embed(["cough in waiting room"]); assert v.shape == (1,384) and abs(np.linalg.norm(v[0]) - 1) < 1e-5
def test_search_finds_relevant(): kb = KnowledgeBase.build(chunks_of(["outpatients wait 15-45 minutes seated", "dialysis three times a week"]), HashEmbedder()); assert "wait" in kb.search("how long do outpatients wait", k=1)[0][0].text
def test_save_load_roundtrip(tmp_path): kb.save(tmp_path); kb2 = KnowledgeBase.load(tmp_path, HashEmbedder()); assert kb2.search("dialysis",1)[0][0].id == kb.search("dialysis",1)[0][0].id
def test_load_rejects_other_embedder(tmp_path): kb.save(tmp_path); with pytest.raises(ValueError, match="embedder"): KnowledgeBase.load(tmp_path, HashEmbedder(dim=128))
def test_default_kb_covers_research_notes(): kb = build_default_kb(HG1_ROOT, load_scenario(V1), HashEmbedder()); assert any("patient_personas.md" in c.file for c in kb.chunks)
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_kb.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the three modules and `build_default_kb`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add research-notes knowledge base with local hash embedder"`

---

### Task 6: Long-term memory, snapshots and the run lock

**Files:**
- Create: `wardzero_agents/memory/{__init__,longterm,snapshots,runlock}.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Produces (`longterm.py`): `MemoryHit(text, kind, importance, run_index, score)`; `LongTermMemory(path: Path, embedder: Embedder)`:
  - **Schema:** `memories(id INTEGER PRIMARY KEY, person_key TEXT, run_id TEXT, run_index INTEGER, t REAL, kind TEXT CHECK(kind IN ('seed','episode','fact')), text TEXT, importance REAL, vector BLOB)` and `runs(run_id TEXT PRIMARY KEY, run_index INTEGER, started_at TEXT)`.
  - **Methods:**
    - `begin_run(run_id) -> int` returns the next run index;
    - `add(person_key, run_id, t, kind, text, importance)`;
    - `search(person_key, query, k=5, run_index: int) -> list[MemoryHit]`;
    - `ensure_seed(person_key, seed_texts)` writes seed rows (importance 0.5, run index 0) only if the person has no rows;
    - `reset(person_keys: list[str], seeds: dict[str, list[str]])` deletes every row for those keys, then re-seeds them;
    - `all_keys() -> list[str]`.
  - **Search score:** `0.6*cos + 0.25*exp(-(run_index - row.run_index)/5) + 0.15*importance`. Within the current run, newer rows win ties by `t`.
- Produces (`snapshots.py`): `save_snapshot(mem_path, name) -> Path` uses the sqlite backup API into `snapshots/<name>.sqlite` plus `<name>.json {created, rows, keys}`; `restore_snapshot(mem_path, name)`; `list_snapshots(data_dir) -> list[dict]`. Names must match `^[A-Za-z0-9_.-]{1,64}$`.
- Produces (`runlock.py`): `RunLock(data_dir)`, a context manager that writes `active_run.json {run_id, pid}`; `active_run(data_dir) -> str | None` returns `None` if the pid is dead; `class RunActive(Exception)`. `reset`, `restore_snapshot` and `ensure_seed` callers in the CLI must check `active_run` and raise `RunActive(f"run {run_id} is active; stop it first")`.

- [ ] **Step 1: Write the failing tests.**

```python
def test_seed_then_search(mem): mem.ensure_seed("anxious_first_timer#7005", ["I have never been to this hospital before."]); hits = mem.search("anxious_first_timer#7005", "first visit hospital", k=1, run_index=1); assert hits[0].kind == "seed"
def test_recency_beats_old(mem): r1 = mem.begin_run("r1"); mem.add(K,"r1",10,"fact","The robot said clinic 3 is upstairs",0.5); r9 = ...run 9 adds "The robot said clinic 3 is down the corridor"; assert "corridor" in mem.search(K,"where is clinic 3",1,run_index=9)[0].text
def test_reset_restores_seed(mem): mem.add(K,"r1",1,"episode","shouted at robot",0.9); mem.reset([K], {K: ["seed text"]}); assert [h.text for h in mem.search(K,"robot",5,run_index=2)] == ["seed text"]
def test_reset_other_person_untouched(mem): ...
def test_snapshot_roundtrip(mem, tmp_path): save_snapshot(mem.path,"before"); mem.add(...); restore_snapshot(mem.path,"before"); assert count_rows(mem) == rows_before
def test_bad_snapshot_name(): with pytest.raises(ValueError): save_snapshot(p, "../x")
def test_reset_refused_during_run(tmp_path): with RunLock(tmp_path, "run-1"): with pytest.raises(RunActive, match="run-1"): guarded_reset(tmp_path, ...)
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_memory.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the three modules.** `guarded_reset(data_dir, keys, seeds)` and `guarded_restore(data_dir, name)` live in `snapshots.py`, and the CLI uses them.
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add long-term memory with recency and importance, snapshots and run lock"`

---

### Task 7: World oracle, audio routing and reflexes

**Files:**
- Create: `wardzero_agents/world/{__init__,oracle,audio}.py`, `wardzero_agents/reflex.py`
- Test: `tests/test_oracle_audio.py`, `tests/test_reflex.py`

**Interfaces:**
- Produces (`oracle.py`): `Pose(x, y, yaw)`; `Entity(kind, id, x, y, detail: str | None)`.
  - `visible(viewer: Pose, entities: list[Entity], signs: list[Sign], fov_deg=120.0, range_m=12.0, los: Callable[[tuple, tuple], bool] = lambda a, b: True) -> list[Seen]`.
  - Signs are seen only within `sign.read_distance_m`, and their detail is the sign text. `bearing_deg` is signed, with left positive.
- Produces (`audio.py`): constants `SPEECH_DB=60`, `ROBOT_SPEECH_DB=65`, `COUGH_DB={"mild":62,"moderate":68,"severe":74}`, `PA_RECEIVED_DB=62`, `ALARM_RECEIVED_DB=85`, `BASE_THRESHOLD_DB=30`, `PARTIAL_MARGIN_DB=6`, `PARTIAL_KEEP=0.6`.
  - `received_db(loudness, distance) = loudness - 20*log10(max(distance, 1.0))`. PA and alarm events use their fixed received level everywhere.
  - `route(ev: AudioEvent, listener: Pose, listener_id: str, hearing_loss_db: float, rng: np.random.Generator) -> Heard | None`:
    - Returns `None` below `BASE_THRESHOLD_DB + loss`.
    - Marks the event `partial` below `threshold + PARTIAL_MARGIN_DB`. A partial event keeps each word with probability `PARTIAL_KEEP` and replaces dropped words with "…".
    - `addressed_to_me = ev.addressee == listener_id`.
- Produces (`reflex.py`): `ReflexAction(kind: Literal["cough","fidget","look_at"], target: str | None, duration_s: float, severity: str | None)`; `ReflexEngine(instance: PersonInstance, seed: int)`:
  - `tick(t: float, status: Status, heard: list[Heard], idle: bool) -> list[ReflexAction]`.
  - `start_bout(t, duration_s, severity)`.
  - **Cough:** a Poisson process at `cough_per_hour` (exponential gaps from the seeded rng). During a bout, the person coughs every 2-4 s until `t >= bout_end`.
  - **Fidget:** while seated and idle, every 45-120 s.
  - **Gaze:** `look_at(source_id)` on the first tick after any heard event at or above threshold, and at most once per 3 s.

- [ ] **Step 1: Write the failing tests.**

```python
def test_behind_viewer_not_seen(): assert visible(Pose(0,0,0), [Entity("robot","g1",-3,0,None)], []) == []
def test_sign_text_only_when_close(): far = Sign(id="s",text="Toilets",x=8,y=0,z=2,facing_yaw=3.14); assert visible(Pose(0,0,0), [], [far]) == []; near = far.model_copy(update={"x":4}); assert visible(Pose(0,0,0),[],[near])[0].detail == "Toilets"
def test_los_blocks(): assert visible(Pose(0,0,0), [Entity("person","P2",2,0,None)], [], los=lambda a,b: False) == []
def test_quiet_speech_partial_for_hearing_loss(): h = route(ev(ROBOT_SPEECH_DB, at=(4,0), text="clinic three is down the corridor"), Pose(0,0,0), "P4", 25, rng(1)); assert h.partial and "…" in h.text
def test_far_speech_not_heard(): assert route(ev(60, at=(40,0)), Pose(0,0,0), "P1", 0, rng(1)) is None
def test_pa_heard_everywhere(): assert route(pa_ev, Pose(-8,0,0), "P1", 0, rng(1)).received_db == 62
def test_cough_rate(): e = ReflexEngine(inst(cough_per_hour=30), seed=3); n = count_coughs(e, hours=10); assert 240 <= n <= 360
def test_bout(): e.start_bout(100.0, 40, "severe"); coughs = [a for t in frange(100,140,0.1) for a in e.tick(t, seated, [], True) if a.kind=="cough"]; assert 10 <= len(coughs) <= 20
def test_gaze_on_voice(): acts = e.tick(5.0, seated, [heard(source_id="g1")], True); assert any(a.kind=="look_at" and a.target=="g1" for a in acts)
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_oracle_audio.py tests/test_reflex.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `oracle.py`, `audio.py` and `reflex.py`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add oracle visibility, audio routing with hearing loss, and reflexes"`

---

### Task 8: The mind (prompts, triggers, LangGraph graph, runtime)

**Files:**
- Create: `wardzero_agents/mind/{__init__,prompts,triggers,graph,runtime}.py`
- Test: `tests/test_mind.py`

**Interfaces:**
- Consumes: `LoadedScenario`, `PersonInstance` (Task 1); contracts (Task 2); `Gateway`, `LLMRequest`, `LLMResult` (Task 4); `KnowledgeBase` (Task 5); `LongTermMemory` (Task 6).
- Produces (`prompts.py`):
  - `SYSTEM_FIXED: str`, the instructions:
    - you are one person in a UK hospital main-entrance waiting area;
    - choose only from the listed intents;
    - stay in character;
    - say short lines in British English;
    - you only know what the situation tells you.
  - `persona_card(inst: PersonInstance, area: WaitingArea) -> str`.
  - `render_situation(inst, obs: Observation, status: Status, triggers: list[str], nudges: list[Nudge], clock_min: float) -> str`. Robot speech addressed to the person or heard nearby is rendered as `ROBOT SAID TO YOU: <text>` or `ROBOT SAID NEARBY: <text>`, and nudges as `NUDGE: <message>`.
  - `DECISION_SCHEMA`, strict-compatible:
    - top level: `{"intent": {"kind": enum IntentKind, "target": ["string","null"], "text": ["string","null"]}, "say": ["string","null"], "addressee": ["string","null"], "mood": enum ["calm","anxious","frustrated","distressed"], "patience_delta": number, "reason": string}`;
    - every property is required and `additionalProperties: false` applies at every level.
  - `SUMMARY_SCHEMA = {"memories": [{"text": string, "importance": number}]}`, also strict.
- Produces (`triggers.py`): `TriggerGate(min_interval_s=4.0, robot_near_m=2.0, patience_check_s=180.0)` with `.check(t, obs, status, nudges, last_obs) -> list[str]` and `.mark(t)`, which records the time of a decision.
  - The reasons are `"addressed_speech","speech_nearby","robot_near","new_sign","new_person","intent_done","intent_failed","cough_nearby","patience_timer","nudge"`.
  - It returns `[]` within `min_interval_s` of the last decision unless the reasons include `addressed_speech` or `nudge`.
- Produces (`graph.py`): `MindState(TypedDict)` with fields `person, t, triggers, situation, kb_hits, ltm_hits, short_term: list[str], current_intent: dict | None, mood, patience_left: float, decision: dict | None, last_summary_t: float`.
  - `build_graph(deps: MindDeps) -> CompiledGraph` with nodes `observe → recall → decide → (act | keep) → remember → (summarise | END)`.
  - **Recall:** `kb.search(situation, 4)` and `ltm.search(memory_key, situation, 5, run_index)`.
  - **Decide:** calls the gateway with role `decide`. `validate_decision(data, area, signs, roster, robot_id="g1") -> dict | None` requires the target to be a known seat, landmark, sign, person or `"g1"`, and requires `talk` to have text.
  - **Keep:** reached when the result is not ok or validation fails. It logs and keeps the current intent.
  - **Remember:** appends one line to `short_term`, capped at 30.
  - **Summarise:** runs when `len(short_term) >= 30` or `t - last_summary_t >= 300`. It calls the gateway with role `summarise` and `SUMMARY_SCHEMA`, writes `ltm.add(kind="episode")` and clears `short_term` to its last 5 lines.
  - Compile with `SqliteSaver` at `<run>/shortterm.sqlite`, `thread_id = person`.
- Produces (`runtime.py`): `MindDeps(inst, loaded, gateway, kb, ltm, run_id, run_index, effects: Effects, runlog)`; `class Effects(Protocol): publish_intent(Intent); publish_say(Say)`; `Mind(deps)`:
  - `async on_tick(t, obs, status, nudges: list[Nudge]) -> None` runs at most one decision in flight and ignores triggers while one is pending.
  - `pending -> bool`.
  - Every decision writes `runlog.write("decisions", {...prompt hash, situation, result data, error, reason, latency})`.

- [ ] **Step 1: Write the failing tests.** Use `FakeGateway`, an in-memory KB, a temp LTM, and a `RecordingEffects`.

```python
def test_schema_is_strict(): assert_strict(DECISION_SCHEMA)  # every object: additionalProperties False and all props required
def test_situation_marks_robot_speech(): s = render_situation(P5, obs(heard=[heard("robot","g1","Clinics are down the corridor",addressed=True)]), seated, ["addressed_speech"], [], 12.0); assert "ROBOT SAID TO YOU: Clinics are down the corridor" in s
def test_gate_debounce(): g = TriggerGate(); assert g.check(10, obs_new_person, ...) ; g.mark(10); assert g.check(12, obs_new_person2, ...) == []; assert "addressed_speech" in g.check(12, obs_addressed, ...)
async def test_robot_speech_leads_to_walk_and_thanks(): m = mind(P5, FakeGateway()); await m.on_tick(30, obs_addressed("clinic_corridor is down there"), seated, []); await m.drain(); assert effects.intents[-1].kind == "walk_to" and effects.intents[-1].target == "clinic_corridor" and effects.says[-1].text == "Thank you"
async def test_failed_decision_keeps_intent(): m = mind(P1, FakeGateway(policy=lambda r: raise_refusal())); ...; assert effects.intents == [] and runlog.last("decisions")["error"] == "refusal"
async def test_invalid_target_rejected(): policy returns walk_to target "narnia" -> no intent published, decision logged with error "invalid_target"
async def test_summarise_writes_ltm(): run 30 remembered events -> ltm.search(P1.memory_key, "...", 5, run_index) has an "episode" row
async def test_nudge_triggers_decision_inside_debounce(): ...
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_mind.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the prompts, triggers, graph and runtime.** Install first: `.venv/bin/pip install langgraph langgraph-checkpoint-sqlite`. In `runtime.py`, `drain()` awaits any in-flight decision (used by tests and on shutdown).
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add LangGraph persona mind with triggers, recall, structured decisions and summaries"`

---

### Task 9: Run folder, recorder and replay readers

**Files:**
- Create: `wardzero_agents/runlog.py`, `wardzero_agents/replay.py`
- Test: `tests/test_runlog.py`

**Interfaces:**
- Produces (`runlog.py`):
  - `STREAMS = ("decisions","intents","says","nudges","reflex","world","cards","audio","status","tokens","fairness")`.
  - `RunLog(dir: Path)`:
    - `.write(stream, record: dict)` appends JSONL with keys sorted and passes every string value through `keys.redact`;
    - `.write_meta(meta: dict)` writes `meta.json`;
    - `.copy_configs(loaded)` copies the scenario, personas, storyboard, deck, signs and area YAML into `config/`.
  - `new_run_dir(root: Path, scenario_id: str, now: datetime) -> Path` returns `runs/<YYYYmmdd-HHMMSS>_<scenario_id>/`.
  - **Meta keys:** `run_id, scenario_id, seed, provider, models, perception, sim ("stub"|"isaac"), lockstep, time_scale, test_mode, git_rev, host, snapshot_in, snapshot_out, started, ended, cost_usd, mode ("live"|"rerun"|"replay-intents"|"replay-exact")`.
- Produces (`replay.py`): `iter_stream(run_dir, stream) -> Iterator[dict]` in `t` order; `load_meta(run_dir) -> dict`; `IntentScript(run_dir)` with `.due(t) -> list[Intent | Say | WorldEvent]`, which returns records with `t <= now` not yet returned; `ExactScript(run_dir)` with `.due(t) -> list[tuple[str, dict]]` covering the `status`, `audio` and `cards` streams.

- [ ] **Step 1: Write the failing tests.**

```python
def test_write_and_iterate(tmp_path): rl = RunLog(tmp_path); rl.write("intents", {"t": 2.0, "person":"P1"}); rl.write("intents", {"t": 1.0, "person":"P2"}); assert [r["person"] for r in iter_stream(tmp_path,"intents")] == ["P2","P1"]
def test_redacts_secrets(tmp_path): RunLog(tmp_path).write("decisions", {"t":0,"note":"sk-ant-api03-abcdefghijk"}); assert "abcdefghijk" not in (tmp_path/"decisions.jsonl").read_text()
def test_intent_script_due(tmp_path): ... intents at t=1,5; s = IntentScript(tmp_path); assert len(s.due(2.0)) == 1 and len(s.due(2.0)) == 0 and len(s.due(6.0)) == 1
def test_run_dir_name(): assert new_run_dir(Path("/r"), "waiting_area_v1", datetime(2026,11,3,14,5,9)).name == "20261103-140509_waiting_area_v1"
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_runlog.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `runlog.py` and `replay.py`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add run folder recorder and replay scripts"`

---

### Task 10: Stub world (kinematic stand-in for the Isaac sim host)

**Files:**
- Create: `wardzero_agents/world/stub_world.py`
- Test: `tests/test_stub_world.py`

**Interfaces:**
- Consumes: contracts, oracle, audio (Tasks 2 and 7); `LoadedScenario` (Task 1).
- Produces: `StubWorld(loaded: LoadedScenario, seed: int)`:
  - **Methods:**
    - `step(t: float) -> None`;
    - `apply_intent(Intent) -> None`;
    - `apply_world_event(WorldEvent) -> list[AudioEvent]`;
    - `say(person, text, addressee, t) -> AudioEvent`;
    - `robot_say(text, t) -> AudioEvent`, whose source is `g1` at robot x, y, z = 1.25;
    - `cough(person, severity, t) -> AudioEvent`;
    - `statuses() -> list[Status]`;
    - `observation(person, t, recent_audio: list[AudioEvent]) -> Observation`;
    - `robot_heard(ev: AudioEvent) -> Heard | None`, which routes to the robot's head with 0 dB loss;
    - `roster(t) -> Roster`;
    - `spawn(persona_id, t) -> str`, which returns new ids `N1, N2…` at the entrance, using an instance sampled with seed `scenario_seed*1000 + 100 + n`.
  - **Kinematics:**
    - `walk_to` and `approach` move in a straight line at `inst.walk_speed`;
    - `approach` stops 1.0 m short of the target (a person or `g1`);
    - `sit_down(seat)` walks to the seat, then becomes seated after `sit_to_stand_s`, and fails with reason `"seat occupied"` if the seat is taken;
    - `stand_up` takes `sit_to_stand_s`;
    - `leave(exit)` walks to the exit, then the posture becomes `"gone"`;
    - `cough`, `fidget` and `look_at` overlays do not change position (`look_at` sets yaw);
    - `talk` returns its audio event through `say`;
    - an unknown target fails with reason `"unknown target"`.
  - `wet_floor` adds a sign `"Caution: wet floor"` at the event x, y. `arrival` spawns a person. `person_exit` makes that person `leave(entrance)`.

- [ ] **Step 1: Write the failing tests.**

```python
def test_initial_seated(): w = StubWorld(load_scenario(V1), 7); assert {s.person: s.posture for s in w.statuses()}["P1"] == "seated"
def test_walk_speed(): w.apply_intent(Intent(id="i",person="P5",t=0,kind="walk_to",target="clinic_corridor")); step_until(w, 5.0); assert distance_moved("P5") == pytest.approx(5.0 * inst("P5").walk_speed, rel=0.05)  # after stand-up time
def test_approach_stops_short(): ... kind="approach", target="g1" -> final distance to robot == pytest.approx(1.0, abs=0.1) and state "done"
def test_seat_occupied_fails(): P5 sit_down B2 (P1's seat) -> status state "failed", reason "seat occupied"
def test_robot_say_heard_by_near_person_only(): ev = w.robot_say("Hello", 1.0); assert w.observation("P5",1.0,[ev]).heard == [] or ...  # P5 at D2 is ~7 m away: heard; P1 at B2: check both by computed distance
def test_wet_floor_adds_sign(): w.apply_world_event(WorldEvent(id="w",t=0,kind="wet_floor",x=-2,y=0)); assert any(s.text=="Caution: wet floor" for s in w.signs)
def test_spawn_arrival(): pid = w.spawn("anxious_first_timer", 10.0); assert pid == "N1" and w.roster(10).people[-1].id == "N1"
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_stub_world.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `stub_world.py`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add kinematic stub world for running without Isaac"`

---

### Task 11: Storyboard, cards and chaos (director core)

**Files:**
- Create: `wardzero_agents/director/{__init__,storyboard,cards,chaos}.py`, `config/storyboards/waiting_area_day.yaml`, `config/cards/starter.yaml`
- Modify: `wardzero_agents/config/models.py` (add `Condition`, `Beat`, `Storyboard`, `CardDef`), `config/loader.py` (load and cross-check)
- Test: `tests/test_director.py`

**Interfaces:**
- Produces (models):
  - `Condition(kind: Literal["robot_within","waited_longer_than","posture_is"], person: str, value: float | str)`.
  - `Beat(id, at: str | None, when: Condition | None, after: str | None, card: str, target: str | None = None, params: dict = {})`:
    - exactly one of `at`, `when` or `after`;
    - `at` matches `^t\+\d{2}:\d{2}$`;
    - the loader checks that every card and target exists, and that every `after` names an earlier beat.
  - `Storyboard(id, beats: list[Beat])`.
  - `CardDef(id, label, channels: list[Literal["nudge","reflex","world"]], target_kind: Literal["person","none","new","all"], nudge: str | None, companion_nudge: str | None, reflex: dict | None, world: dict | None, tests: str, weight: float = 1.0)`. Nudge templates may use `{name}`, `{companion}` and `{params.*}`.
- Produces (`storyboard.py`):
  - `WorldView(t, statuses: dict[str, Status], robot_xy, seated_since: dict[str, float], present: set[str])`;
  - `CardFiring(id, t, card, target: str | None, params: dict, source: Literal["storyboard","panel","chaos"])`;
  - `StoryboardEngine(storyboard, deck)` with `.tick(view) -> list[CardFiring]`, `.skip(beat_id)`, `.rerun(beat_id)`, and `.timeline() -> list[dict]`, where each entry is `{id, card, target, state: "pending"|"fired"|"skipped", fired_t}`.
- Produces (`cards.py`): `class CardRejected(Exception)`; `CardExecutor(deck, instances_by_id)` with `.execute(firing, view, roster) -> list[Nudge | ReflexOverride | WorldEvent]`:
  - it raises `CardRejected("target P9 is not in the room")` if a person-target is not in `view.present`;
  - `companion_nudge` goes to whoever has `companion_of == target`;
  - `all` sends the nudge to everyone present;
  - `new` emits `WorldEvent(kind="arrival", persona=params.get("persona"))`.
- Produces (`chaos.py`): `Chaos(rate_per_hour, deck, seed)` with `.tick(t, view) -> list[CardFiring]`. It uses a Poisson process. Cards are weighted by `weight` among those whose `target_kind` can be satisfied, and the target is drawn uniformly from people present. Everything is seeded.
- **Config content:**
  - `starter.yaml` holds the 9 PRD section 05 cards plus `clinic_delay` (world `pa_announcement` "Clinics are running about 30 minutes late. We apologise for the wait."). The cards are: `lost_visitor`, `coughing_fit` (reflex `cough_bout` 40 s severe, plus `companion_nudge` "{name} is struggling to breathe. Get help."), `hard_of_hearing`, `name_called` (PA "Could {name} please go to clinic 3", plus the nudge "You just heard your name called for clinic 3. Go to clinic_corridor."), `impatient_patient`, `blocked_path`, `wet_floor`, `new_arrival` and `fire_alarm` (world alarm, plus an `all` nudge "The fire alarm is sounding. Leave by the nearest exit.").
  - `waiting_area_day.yaml` beats:
    - `b1` at `t+05:00` clinic_delay
    - `b2` at `t+12:00` lost_visitor → P5
    - `b3` at `t+20:00` name_called → P1
    - `b4` after b3 new_arrival
    - `b5` at `t+35:00` coughing_fit → P2
    - `b6` when `waited_longer_than` P4 3000 s, impatient_patient → P4

- [ ] **Step 1: Write the failing tests.**

```python
def test_v1_storyboard_loads(): ls = load_scenario(V1); assert [b.id for b in ls.storyboard.beats] == ["b1","b2","b3","b4","b5","b6"] and len(ls.deck) == 10
def test_beat_at_time(): e = engine(); assert [f.card for f in e.tick(view(t=299))] == []; assert [f.card for f in e.tick(view(t=300))] == ["clinic_delay"]; assert e.tick(view(t=301)) == []
def test_after_beat(): fire b3 at 1200 -> next tick fires b4 new_arrival
def test_condition_beat(): view(t=3001, seated_since={"P4": 0}) fires b6 once
def test_coughing_fit_outputs(): outs = ex.execute(firing("coughing_fit","P2"), view_all_present, roster); assert any(isinstance(o, ReflexOverride) and o.person=="P2" and o.duration_s==40 for o in outs); assert any(isinstance(o, Nudge) and o.person=="P3" and "struggling to breathe" in o.message for o in outs)
def test_card_for_missing_person_rejected(): with pytest.raises(CardRejected, match="P9 is not in the room"): ex.execute(firing("lost_visitor","P9"), view, roster)
def test_chaos_deterministic(): a = run_chaos(seed=7, hours=1); b = run_chaos(seed=7, hours=1); assert a == b and 2 <= len(a) <= 14
def test_bad_beat_rejected(tmp_path): beat with both at and after -> ConfigError "storyboard.beats[0]: exactly one of at, when, after"
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_director.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the models, loader checks, three modules and two YAML files.**
- [ ] **Step 4: Run and confirm the tests pass.** Run `pytest -q` (the whole suite). Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add storyboard engine, scenario cards, chaos mode and the starter deck"`

---

### Task 12: Control panel (aiohttp + single page)

**Files:**
- Create: `wardzero_agents/panel/{__init__,server}.py`, `wardzero_agents/panel/static/index.html`
- Test: `tests/test_panel.py`

**Interfaces:**
- Consumes: `CardFiring`, timeline dicts (Task 11).
- Produces: `class DirectorAPI(Protocol)`, which the panel uses. Methods:
  - `state() -> dict`, with keys `t, running, paused, timeline, cast, events, chaos, cost_usd, budget_usd, recording, run_id`;
    - `cast` is a list of `{id, display_name, persona, x, y, posture, mood, last_decision, reason, last_said}`;
  - `control(action: str) -> None`;
  - `fire(card: str, target: str | None, params: dict) -> dict`, which returns `{ok, firing_id}` or `{ok: False, error}`;
  - `set_chaos(enabled: bool, rate_per_hour: float) -> None`;
  - `beat(action: Literal["skip","rerun"], beat_id: str) -> None`;
  - `snapshot(name: str) -> dict`.
- Produces: `make_app(api: DirectorAPI) -> aiohttp.web.Application` with these routes:
  - `GET /` serves `index.html`;
  - `GET /api/state`;
  - `POST /api/control {action}`;
  - `POST /api/cards/fire {card, target, params}`;
  - `POST /api/chaos {enabled, rate_per_hour}`;
  - `POST /api/beat {action, beat_id}`;
  - `POST /api/snapshot {name}`;
  - `GET /ws` pushes `state()` at 2 Hz.
  - Bad input returns 400 with `{error}`. The server binds `127.0.0.1` only (default port 8765, `--panel-port`).
- `index.html`: one self-contained file (no external scripts). It has:
  - a timeline strip;
  - a floor-map `<canvas>` with the seats, landmarks, signs, people and robot, scaled from `waiting_area.yaml` (bounds x -10..12, y -3..8);
  - a cast table;
  - an event log;
  - the card deck with a target picker and "Fire" button;
  - start, pause, resume and stop controls;
  - a chaos toggle with a rate field;
  - a snapshot form;
  - a cost meter and recording badge.

  Errors appear inline in plain words. It must work at 1280 px and 400 px wide.

- [ ] **Step 1: Write the failing tests** using `aiohttp.test_utils.TestClient` and a `FakeDirectorAPI`.

```python
async def test_state(client): r = await client.get("/api/state"); assert r.status == 200 and "timeline" in await r.json()
async def test_fire_card(client, api): r = await client.post("/api/cards/fire", json={"card":"coughing_fit","target":"P2","params":{}}); assert (await r.json())["ok"] and api.fired[-1][0] == "coughing_fit"
async def test_fire_rejected_shows_error(client, api): api.reject = "target P9 is not in the room"; j = await (await client.post("/api/cards/fire", json={"card":"lost_visitor","target":"P9","params":{}})).json(); assert j == {"ok": False, "error": "target P9 is not in the room"}
async def test_bad_control_400(client): assert (await client.post("/api/control", json={"action":"explode"})).status == 400
async def test_index_has_no_external_scripts(client): html = await (await client.get("/")).text(); assert "<script src=" not in html
async def test_ws_pushes_state(client): ws = await client.ws_connect("/ws"); msg = await ws.receive_json(timeout=2); assert "cast" in msg
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_panel.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `server.py` and `index.html`.**
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -am "Add scenario control panel"`

---

### Task 13: ROS 2 nodes (agent service, director, stub sim, replay, fairness, reception bot)

**Files:**
- Create: `wardzero_agents/ros/{__init__,fairness,agent_node,director_node,stub_sim_node,replay_node}.py`, `wardzero_agents/examples/reception_bot.py`
- Test: `tests/test_fairness.py`, `tests/integration/test_end_to_end.py`

**Interfaces:**
- Consumes everything above. Each node is a module with `main(argv=None)`, launched by the CLI as `python -m wardzero_agents.ros.<node> --run-dir DIR [...]`.
- `fairness.py`: `audit(subs_by_node: dict[str, list[str]], allowed_prefix="wardzero_") -> list[dict]` returns `[{node, topic}]` for every non-allowed node subscribed to a `FORBIDDEN_FOR_ROBOT` prefix. `live_audit(node: rclpy.node.Node) -> list[dict]` uses `get_node_names_and_namespaces()` and `get_subscriber_names_and_types_by_node`.
- `stub_sim_node` (node name `wardzero_stub_sim`, params `--time-scale` (default 1.0), `--lockstep`, `--scenario`):
  - **Clock:** publishes `/clock` at 100 Hz. It advances `time_scale × wall dt`, and does not advance in lockstep while `/agents/pending > 0` or while paused (`/scenario/control`).
  - **Publishes:**
    - `ROSTER`, transient-local QoS, on every change;
    - `status(pid)` at 10 Hz;
    - `observation(pid)` at 2 Hz, plus immediately on audio;
    - `AUDIO_EVENTS` for every event;
    - `G1_HEARD` (`Heard` JSON) for events the robot hears.
  - **Subscribes:** `intent(pid)`, `say(pid)`, `G1_SAY` (`std_msgs/String` plain text, as in today's contract), `WORLD_EVENT`, `CONTROL`.
  - Writes the `status` stream at 2 Hz and the `audio` stream to the run log.
- `agent_node` (node name `wardzero_agents`):
  - **Start-up:** key check first (`keys.check`; it exits with code 2 and prints the fix-it message on failure). It then loads `LoadedScenario`, the KB index (building it if missing), and LTM with `begin_run`. It saves snapshot `run-<id>-start`, or restores `scenario.memory_snapshot` first if one is set. It holds `RunLock` for the whole run.
  - **Minds:** one `Mind` and one `ReflexEngine` per roster person, with new people (`N*`) spawned on roster change. The asyncio loop ticks at 10 Hz sim time; rclpy spins in a background thread with a `MultiThreadedExecutor`.
  - **Publishing:** reflex actions go out as overlay intents, and cough reflexes publish `say`-less cough intents (the sim makes the sound). Intents and says are published.
  - **Pending count:** published on `PENDING` (`std_msgs/Int32`).
  - **Shutdown:** saves `run-<id>-end`, writes meta, and releases the lock.
- `director_node` (node name `wardzero_director`):
  - Runs `StoryboardEngine`, `CardExecutor` and `Chaos` on sim time.
  - **Publishes:** `nudge(pid)`, `reflex(pid)`, `WORLD_EVENT`, `TIMELINE` at 1 Hz and `SCEN_EVENTS`.
  - Implements `DirectorAPI` over ROS state and serves the panel. Control actions go to `CONTROL`.
  - Records the `cards` stream (including rejections, with `error`).
  - Runs `live_audit` at start and every 30 s, writing to the `fairness` stream and logging a warning.
- `replay_node` (`wardzero_replay`), in one of two modes:
  - `--intents` publishes `IntentScript` items on the people's topics and `WORLD_EVENT`. Use it with `stub_sim_node`, without the agents or director.
  - `--exact` republishes the status, audio and timeline from `ExactScript`, without the stub. It is used by the panel and, later, by renders.
- `examples/reception_bot.py` (node name `reception_bot`, outside the `wardzero_` prefix on purpose, since it plays the robot under test). It subscribes only to `G1_HEARD` and publishes `G1_SAY`:
  - it greets speech containing "hello" or "excuse me";
  - for "where" plus a known landmark word (clinic, ward, toilet, exit), it gives directions from `config/waiting_area.yaml` and `signs.yaml`;
  - after 3 loud coughs (received at 50 dB or more) heard within 20 s, it says "Can I get some help for you? I'll let the nurse know." with a 60 s cool-down;
  - it is clearly labelled in the file docstring as a placeholder robot behaviour for exercising the system.

- [ ] **Step 1: Write the failing tests.**

```python
def test_audit_flags_robot_reading_minds(): v = audit({"reception_bot": ["/g1/audio/heard", "/humans/P1/intent"], "wardzero_director": ["/humans/P1/status"]}); assert v == [{"node":"reception_bot","topic":"/humans/P1/intent"}]
def test_audit_clean(): assert audit({"reception_bot": ["/g1/audio/heard"]}) == []
```
`tests/integration/test_end_to_end.py`, marked `@pytest.mark.ros` and skipped unless `ROS_DISTRO=humble`. It runs with `WARDZERO_TEST_FAKE_LLM=1`, `--time-scale 30`, a 3-minute scenario variant written to a temp dir (with `b1` moved to `t+00:20`, `b2` to `t+00:40`, `b5` to `t+01:00`), a temp `WARDZERO_DATA_DIR`, and a unique `ROS_DOMAIN_ID`. It launches `hhumans run <tmp scenario> --no-panel` (Task 14) as a subprocess with the reception bot, and waits for exit. Asserts:
```python
assert meta["test_mode"] is True and meta["snapshot_in"].startswith("run-") and meta["snapshot_out"].endswith("-end")
assert any(c["card"] == "clinic_delay" for c in cards) and any(c["card"] == "coughing_fit" for c in cards)
assert any(r["kind"] == "cough" for r in intents if r["person"] == "P2")                        # reflex + bout
assert any(s["person"] == "P3" for s in says)                                                  # companion asked for help (fake policy approaches robot on "help")
assert any(a["source_kind"] == "robot" and "nurse" in (a["text"] or "") for a in audio)          # robot heard the coughs
assert fairness == [] or all(v["node"] != "reception_bot" for v in fairness)
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_fairness.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement the five nodes and the reception bot.**
- [ ] **Step 4: Run the unit tests.** Run `pytest tests/test_fairness.py -q`. Expected: PASS. (The integration test runs after Task 14.)
- [ ] **Step 5: Commit.** `git commit -am "Add ROS 2 nodes: agent service, director with panel, stub sim, replay, fairness audit, reception bot"`

---

### Task 14: The `hhumans` CLI and the end-to-end run

**Files:**
- Create: `wardzero_agents/cli.py`
- Test: `tests/test_cli.py`; run `tests/integration/test_end_to_end.py`

**Interfaces:**
- Produces `main(argv=None) -> int` (argparse). Subcommands:
  - `run SCENARIO [--sim stub|isaac] [--time-scale F] [--lockstep] [--no-robot] [--no-panel] [--panel-port N] [--bot reception|none]`:
    - it refuses `--sim isaac` with "The Isaac sim host arrives in Plan 2. Use --sim stub." (exit 2);
    - it runs the key check in-process first and exits 2 on failure;
    - it creates the run dir, then spawns `stub_sim_node`, `agent_node`, `director_node` and (unless `--bot none`) `reception_bot` as subprocesses sharing `ROS_DOMAIN_ID`;
    - it prints the panel URL;
    - it stops all children at scenario end, on Ctrl+C, or when any child exits non-zero, and returns that code.
  - `rerun RUN_DIR [same flags]`: the run's copied scenario with `memory_snapshot = meta.snapshot_in`, live minds, `mode: rerun`.
  - `replay RUN_DIR --intents|--exact [--time-scale F]`: `--intents` spawns the stub sim, the replay node and the robot bot; `--exact` spawns the replay node and serves the panel read-only.
  - `memory reset (--person ID --scenario S | --persona NAME --scenario S | --all) [--yes]`: it prints what will be reset and asks for "yes" unless `--yes`. It uses `guarded_reset`, so it refuses during a run.
  - `memory snapshot save|restore|list [NAME]`.
  - `kb build [--embedder hash|fastembed] [--scenario S]`.
  - `keys set|clear|status claude|openai`: `set` reads with `getpass` and never echoes; `status` prints only "stored in keyring", "from key file", "from ant profile or environment" or "not set".
  - `audit` runs the live fairness audit once.

- [ ] **Step 1: Write the failing tests.**

```python
def test_isaac_not_yet(capsys): assert main(["run", V1, "--sim", "isaac"]) == 2 and "Plan 2" in capsys.readouterr().err
def test_run_without_key_refuses(monkeypatch, capsys, memkeyring): monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False); monkeypatch.setattr(keys, "check", raise_keymissing); assert main(["run", V1]) == 2; err = capsys.readouterr().err; assert "hhumans keys set claude" in err and "sk-" not in err
def test_keys_status_never_prints_secret(memkeyring, capsys): keys.set_key("claude","sk-ant-api03-abcdefghijk"); main(["keys","status","claude"]); out = capsys.readouterr().out; assert "keyring" in out and "abcdefghijk" not in out
def test_memory_reset_needs_confirmation(monkeypatch, capsys): monkeypatch.setattr("builtins.input", lambda _: "no"); assert main(["memory","reset","--all"]) == 1
def test_kb_build(tmp_path, monkeypatch): monkeypatch.setenv("WARDZERO_DATA_DIR", str(tmp_path)); assert main(["kb","build"]) == 0 and (tmp_path/"kb"/"meta.json").exists()
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `pytest tests/test_cli.py -q`. Expected: FAIL.
- [ ] **Step 3: Implement `cli.py`.**
- [ ] **Step 4: Run the unit tests and the end-to-end test.** Run `pytest -q` and then `source env.sh && pytest -m ros tests/integration -q`. Expected: all PASS.
- [ ] **Step 5: Run a real short check by hand, with the user's key and their go-ahead for the API spend.** Run `hhumans run config/scenarios/waiting_area_v1.yaml --time-scale 1` for 5 minutes, then stop it. Report:
  - the decision count;
  - the median decision latency, from the `decisions` stream;
  - the cost, from `meta.json`;
  - three example decisions with their reasons.
- [ ] **Step 6: Commit.** `git commit -am "Add hhumans CLI: run, rerun, replay, memory, kb, keys, audit"`

---

### Task 15: Motion clip placeholder and the BONES-SEED fetch script (written, not run)

**Files:**
- Create: `hospital-sim-humans/motion/clip_catalog.py`, `hospital-sim-humans/motion/clips_v1.yaml`, `hospital-sim-humans/scripts/fetch_bones_seed.sh`
- Test: `hospital-sim-humans/tests/test_clip_catalog.py`

**Interfaces:**
- Produces: `ClipRef(source: Literal["bones_seed","sample","synthetic"], name: str, path: str | None)`; `ClipCatalog.load(yaml_path, seed_dir: Path | None, sample_pt: Path) -> ClipCatalog`.
  - `.resolve(intent: str, style: str | None = None) -> ClipRef` tries, in order: the BONES-SEED `move_name` patterns, if `seed_dir` holds the converted `.motion` files; the named clips in the 61-clip sample (`~/src/ProtoMotions/data/motion_for_trackers/soma23_bones_seed_mini.pt`); then `synthetic:<generator>`.
  - `.missing() -> list[str]` lists intents that only have synthetic fallbacks.
- `clips_v1.yaml`: one entry per `IntentKind`, plus `cough_seated`, `cough_standing`, `phone_seated`, `walk_slow` and `walk_stick`. Each entry has `seed_patterns` (search terms for `select_seed_clips.py`), `sample` (sample clip names, which may be empty) and `synthetic` (the generator name: `nod`, `cough_overlay`, `look_at`, `idle_breath`, `fidget_shift`).
- `fetch_bones_seed.sh [--dry-run] --list FILE --out DIR`:
  - checks that `huggingface-cli`/`hf` is logged in and that at least 10 GB is free on the target;
  - streams `https://huggingface.co/datasets/bones-studio/seed/resolve/main/soma_uniform.tar.gz` with the user's token through `tar -xzf - -T FILE` (the archive is 45.2 GB, nothing is stored whole);
  - then converts in batches with ProtoMotions `data/scripts/convert_soma23_bvh_to_proto.py --input-fps 120 --output-fps 30`, deleting BVH after each batch (the `server/convert_stream.sh` pattern, local paths);
  - `--dry-run` prints the plan, the free space and the clip count, and downloads nothing.

- [ ] **Step 1: Write the failing tests.**

```python
def test_falls_back_to_synthetic_without_seed(): c = ClipCatalog.load(YAML, seed_dir=None, sample_pt=FAKE_SAMPLE); assert c.resolve("cough").source == "synthetic"
def test_prefers_sample_when_named(): assert c.resolve("sit_idle").source in ("sample","synthetic")  # sample if the mini set names a seated idle
def test_missing_lists_synthetic_only(): assert "cough" in c.missing()
def test_fetch_script_syntax(): assert subprocess.run(["bash","-n",SCRIPT]).returncode == 0
def test_fetch_dry_run_downloads_nothing(tmp_path): r = subprocess.run(["bash",SCRIPT,"--dry-run","--list",str(LIST),"--out",str(tmp_path)],capture_output=True,text=True); assert r.returncode == 0 and "45.2 GB" in r.stdout and not any(tmp_path.iterdir())
```
- [ ] **Step 2: Run and confirm the tests fail.** Run `cd hospital-sim-humans && ~/src/hg1_humans/hh.sh -m pytest tests/test_clip_catalog.py -q`, or plain `.venv/bin/pytest` if the catalogue avoids torch. Expected: FAIL.
- [ ] **Step 3: Implement the catalogue, the YAML and the script.** Read the sample clip names once from the mini `.pt` (`motion_files`) and write them into `clips_v1.yaml` by hand; tests use a small fake file.
- [ ] **Step 4: Run and confirm the tests pass.** Expected: PASS. Do **not** run the script without `--dry-run`.
- [ ] **Step 5: Commit** in the hospital-sim-humans tree (untracked in the master repo today). Commit only if the user asks; otherwise leave the files staged and report them.

---

### Task 16: README, interface contract and project docs

**Files:**
- Create: `hospital-sim-agents/README.md`
- Modify: `docs/interfaces.md` (new section "3.x Persona agents (hospital-sim-agents)"); `hospital-sim-humans/CONTEXT.md` (pointer to the new component and the clip placeholder)
- Test: `tests/test_readme.py`

**Interfaces:** none (docs only).

- [ ] **Step 1: Write the failing test.** `test_readme_sections`: the README contains the headings `## Accounts and API keys`, `## Running`, `## Control panel`, `## Memory`, `## Knowledge base`, `## Re-running and replay`, `## Perception modes`, `## Motion data`, `## Costs`, and the sentence "A Claude Pro or Max subscription cannot be used for API calls".
- [ ] **Step 2: Run and confirm it fails.** Expected: FAIL.
- [ ] **Step 3: Write the README.** It covers:
  - Setup (`source env.sh`, `pip install -e`).
  - **Accounts and keys:** the Claude Console or OpenAI Platform, a spend limit, `ant auth login`, `hhumans keys set`, and the key-file rule for headless servers.
  - **Running:** stub sim, lockstep, time scale.
  - **Control panel:** URL, cards, chaos.
  - **Memory:** carries across runs; reset; snapshots.
  - **Knowledge base:** hash embedder by default; `pip install -e .[embed]` for fastembed, which downloads a model.
  - **Re-running and replay:** the three modes, and the same-machine caveat.
  - **Perception modes:** oracle now; full mode in Plan 3, with the services it will need.
  - **Motion data:** placeholder clips now; `fetch_bones_seed.sh` after freeing disk; licence rules.
  - **Costs:** the estimates from the PRD, and the `budget_usd` cap.
  - **Robot fairness**, and how to point a real G1 stack at `/g1/audio/heard` and `/g1/speech/say`.
- [ ] **Step 4: Update `docs/interfaces.md`** with the topic table (Task 2 names, types, publishers and subscribers, rates), the `wz.v1` envelope, and the fairness rule. Note that `/g1/speech/say` now becomes a sound source in the stub sim.
- [ ] **Step 5: Run and confirm the test passes, then run the whole suite.** Run `pytest -q`. Expected: PASS.
- [ ] **Step 6: Commit** `hospital-sim-agents`: `git commit -am "Add README"`. Leave the master-repo doc changes uncommitted for the user to review, as the master repo is on branch v2 with other untracked work.
