# 05 — Design direction and visual system

A concrete, opinionated proposal for an elegant, calm clinical app that people *want* to pick up. Rules from `02` (S-, A-, X-, D-…) and `03` (HF-n) are referenced; `04` defines the screens.

## 1. Design principles

1. **Status before controls.** Every screen answers *what is it doing · is that OK · what's next* before offering buttons (Endsley levels 1–3, HF-15).
2. **Calm by default, loud only when it matters.** Quiet neutrals, one accent per state, no decoration that competes with alarms. Red and flashing are reserved for danger (A-1). Ottava's "invisible until needed" is the mood.
3. **Readable from across the room.** Large type, few words, high contrast, and an across-room view that takes over when nobody is touching (HF-21).
4. **One safe way to do each thing.** Stable positions (HF-23), goal-based buttons (HF-19), friction proportional to risk (HF-24).
5. **Honest.** ETAs, track records and "I'm waiting for…" in plain words. Never a spinner without a sentence (HF-13, HF-27, HF-28).
6. **Gloves and hurry.** Big targets, no precision gestures, nothing hidden behind hover or long-press only (I-3).
7. **Same language everywhere.** The robot's light and voice, the iPad, and the across-room view use the same colours and phrases (da Vinci 5's universal UI, Mako's state-on-the-tool).

**Mood references** (what to take from each):
- **Apple Health / iOS system apps**: typographic hierarchy with SF Pro, generous whitespace, rounded continuous corners, quiet greys.
- **Hugo / da Vinci 5 team displays**: dark, low-glare theatre UI with sparse bright accents; the team display is separate from the surgeon display.
- **BrainOS**: glanceable, symbol-led, language-light.
- **Spot app**: the always-visible status bar and top-right red STOP, but calmer and without the "Star Wars" styling.
- **Seirios RNS**: the map-centric operator pages the team already knows, cleaned up for Operator/Technician modes.
- **Aviation glass cockpits (Airbus ECAM)**: colour discipline (red = warning, amber = caution, cyan = advisory, green = OK) and the principle of the "dark cockpit": nothing lit when nothing needs attention.

## 2. Typography

**Font:** `system-ui` / `-apple-system` (SF Pro on iPad, which picks Text and Display optical sizes automatically, has excellent hinting and needs no download or CDN), with `font-variant-numeric: tabular-nums` for every changing number. **SF Mono** (`ui-monospace`) in Technician only. No web fonts: the app must work offline from the robot.

**Sizes from viewing distance.** MIL-STD-1472: character height should subtend ≥ 16 arc-minutes (20′ preferred, 21–30′ for coloured text). On a 264-ppi iPad, 1 pt ≈ 0.192 mm, and SF Pro's cap height ≈ 0.7 em.

| Viewing distance | Rule | Cap height | Font size (pt) | Use |
|---|---|---|---|---|
| 0.5 m (arm's length) | 16′ min | 2.3 mm | **17** | body text minimum (Clinical), matches iOS body |
| 0.5 m | 20′ preferred | 2.9 mm | 22 | Clinical labels, tile captions |
| 1 m | 21′ (coloured status) | 6.1 mm | **44** | hero status word, readback card |
| 1 m | 16′ | 4.7 mm | 34 | hero activity sentence |
| 2 m | 20′ | 11.6 mm | **88** | across-room status word |
| 2 m | 16′ | 9.3 mm | 64 | across-room activity sentence |
| 3 m | 16′ | 14 mm | 104 | across-room status on 13" (optional "large" setting) |

**Type scale (pt = CSS px on iPad):**

| Token | Size / line height / weight | Use |
|---|---|---|
| `display-xl` | 88/96 semibold | Across-room status word |
| `display` | 56/64 semibold | Across-room activity |
| `hero` | 44/52 semibold | Hero status word, readback |
| `title-1` | 34/40 semibold | Hero activity, screen titles (Clinical) |
| `title-2` | 28/34 semibold | Section titles, tile titles |
| `title-3` | 22/28 medium | Tile captions, Clinical labels |
| `body` | 17/24 regular | Body (Operator/Clinical minimum) |
| `callout` | 15/20 regular | Technician body |
| `caption` | 13/16 medium | Technician metadata only; never in Clinical |

Sentence case everywhere. No all-caps except the word **STOP**. Numbers carry units in a lighter weight ("~40 **s**").

## 3. Colour tokens

Two themes: **Light** (bright theatre, corridors, workshop) and **Theatre dim** (laparoscopic/robotic cases, night). Both are specified as CSS custom properties. Contrast values below were computed with the WCAG formula against the theme's background (bg) and surface.

### 3.1 Neutrals

| Token | Light | Theatre dim | Contrast (text tokens) |
|---|---|---|---|
| `--bg` | `#F4F6F8` | `#07090C` | – |
| `--surface` | `#FFFFFF` | `#10141A` | – |
| `--surface-2` | `#EEF1F4` | `#171C24` | – |
| `--border` | `#C9D1DA` | `#2A3342` | decorative only |
| `--text` | `#0E1621` | `#D9DEE6` (not pure white, to limit glare) | 16.8:1 / 14.8:1 |
| `--text-2` | `#4A5563` | `#8E99A8` | 7.0:1 / 6.9:1 |

Theatre dim: no element brighter than `--text` except the Stop button and High alarms. **No large white surfaces.** Images and camera feeds are shown at 80% brightness with a 1-tap "full brightness".

### 3.2 State colours (semantic, never decorative)

| Token | Meaning | Light | Dim | Contrast vs bg (L / D) | Paired icon (always) |
|---|---|---|---|---|---|
| `--robot-driving` | Robot moving autonomously (NAV, AUTO) | `#1F5FD6` | `#6B9BFF` | 5.3 / 7.4 | robot-arrow glyph |
| `--person-driving` | A person controls motion (LOCO, MANIP) | `#B0307A` | `#FF7EB6` | 5.5 / 8.5 | hand glyph + diagonal stripe texture on the ribbon |
| `--standby` | Standing by (STAND) | `#516173` | `#94A3B8` | 5.9 / 7.8 | pause-circle |
| `--off` | Powered down (DAMP) | `#7A8591` | `#6B7686` | 3.5 / 4.3 (non-text only) | power glyph |
| `--ok` | Check passed, task done | `#0B7A5C` | `#3CC59A` | 4.9 / 9.2 | check-circle |
| `--alarm-high` / Stop | High alarm; Stop control | `#C81E1E` | `#FF5A4E` (text), `#D92D20` (fill) | 5.3 / 6.5 | octagon-! (alarm), hand-stop (Stop) |
| `--alarm-med` | Medium alarm | text `#8A4B00`, fill `#F5A524` | `#F5A524` | 6.3 / 9.8; dark text on fill 8.9:1 | triangle-! |
| `--alarm-low` | Low alarm | text `#0B6A80`, fill `#2CC5DD` | `#3FD0E6` | 5.7 / 10.8; dark text on fill 8.8:1 | circle-i |
| `--accent` | Brand, links, selection | = `--robot-driving` | = `--robot-driving` | | |

White text on `--alarm-high` fill: 5.7:1 (light), 4.8:1 on `#D92D20`. White on `--robot-driving`: 5.7:1. White on `--person-driving`: 5.9:1.

### 3.3 Why these colours (colour-vision check)

A Machado-2009 deuteranopia simulation of the tokens showed two collisions. Both are handled:
- **Red vs green (`--alarm-high` vs `--ok`) collapse** to near-identical olive/grey (contrast 1.2:1 between them). → They are **never used as a pair without icon and word**. OK is a check-circle + "OK"; High is an octagon + the alarm sentence. This is also why the UI never shows red/green dots as its only signal (Mako voxels, current dashboard "running/stopped" pills).
- **Blue vs violet collapse** (the first proposal for "person driving" was violet). → Replaced by **magenta** `#B0307A`, which simulates to neutral grey against a saturated blue. The distinction also has a second channel: the person-driving ribbon carries a **diagonal stripe texture and a hand icon**.
- Amber and cyan remain distinct from each other and from blue for deutan/protan viewers. Yellow/amber is the one hue that CVD users perceive reliably, which is why it is the Medium alarm colour, as the standard requires.

Rule: **every state = colour + icon + word + (for mode) texture**, so the UI stays correct in greyscale. Test every screen in greyscale and with a deuteranopia filter before merging.

## 4. Status semantics (one table the whole app uses)

| Robot state | Word (Clinical) | Colour | Icon | Ribbon | Robot light |
|---|---|---|---|---|---|
| DAMP | Powered down | `--off` | power | grey, outline only | off / slow grey breathe |
| STAND idle | Standing by | `--standby` | pause-circle | slate | white steady, dim |
| STAND after Stop | **Stopped** · by ‹name› | `--alarm-high` (steady, *not* flashing) | hand-stop | red band, steady | red steady |
| NAV | Going to ‹place› | `--robot-driving` | robot-arrow | blue | blue steady |
| AUTO | Scrub assist · ‹step› | `--robot-driving` | robot-hand | blue | blue steady; **blue pulse before arm motion** |
| LOCO | Manual walking · ‹name› | `--person-driving` | hand + walk | magenta + stripes | magenta steady |
| MANIP | Manual arms · ‹name› | `--person-driving` | hand + arm | magenta + stripes | magenta steady |
| Waiting (blocked, lift, hand) | Waiting for ‹reason› | family colour + amber chip | hourglass | family + chip | family, slow pulse |
| High alarm | ‹alarm sentence› | `--alarm-high` flashing 2 Hz (banner only) | octagon-! | red flashing band | red flashing 2 Hz |
| Medium alarm | ‹alarm sentence› | `--alarm-med` flashing 0.6 Hz | triangle-! | amber band | amber 0.6 Hz |
| Low alarm | ‹alarm sentence› | `--alarm-low` steady | circle-i | chip only | cyan steady (added) |

**Hero status word** is one of four: **OK** (check, `--ok`), **Needs you** (triangle, amber), **Stopped** (hand-stop, red steady), **Alarm** (octagon, red flashing). The mode is shown *separately* in the ribbon, so "is it OK" and "who is driving" never compete for one colour.

## 5. Touch targets and gloves

On an 11"/13" iPad, 1 pt ≈ 0.19 mm, so 44 pt ≈ 8.5 mm (Apple HIG minimum, WCAG AAA). Gloved use needs more (NN/g ≥ 10 mm; ISO 9241-9's finger-breadth guidance is up to ~22 mm).

| Target | Size (pt) | ≈ mm | Spacing |
|---|---|---|---|
| **Stop** | ≥ 88 × 88 (rail 112 wide → 96 × 112) | ≥ 17 | 24 pt clear zone, nothing else within |
| Clinical primary tiles | 144 × 144 (min 120 × 120) | 28 | 16 pt gutters |
| Clinical buttons (Undo, Acknowledge, Resume slider track) | ≥ 64 tall, ≥ 160 wide | ≥ 12 | ≥ 12 pt |
| Operator controls | ≥ 56 | 11 | ≥ 8 pt |
| Joystick | 220 diameter, thumb 88 | 42 / 17 | – |
| Technician controls | ≥ 44 | 8.5 | ≥ 8 pt |
| Absolute minimum anywhere | 44 | 8.5 | WCAG 2.5.8 spacing rule |

Interaction rules:
- **Act on release (`pointerup`) inside the target**, with a pressed state. The one exception is **Stop, which acts on `pointerdown`** so a sliding gloved finger still stops the robot.
- **Slide-to-confirm** (Resume, Take control, Start manual): track 64 pt tall, thumb 64 pt, must travel ≥ 70% of the track. Works with gloves and is not a modal.
- **Hold-to-confirm** (Power off): 1.5 s with a filling ring and a haptic-free visual tick; releasing early cancels.
- No double-tap, pinch, multi-finger or edge-swipe gestures in Clinical. Map pan/zoom (Operator) also has +/− and "Fit" buttons.
- Disable text selection, the long-press callout and tap highlight; set `touch-action: manipulation` to prevent double-tap zoom.

## 6. Layout grids

Viewports (CSS pt, Home Screen web app, landscape): iPad / iPad Air 11" **1180 × 820**; iPad Pro 11" (M4) **1210 × 834**; iPad Air 13" **1366 × 1024**; iPad Pro 13" (M4) **1376 × 1032**. In Safari with browser UI, subtract ~70–100 pt of height: design for **1180 × 740** as the worst case, and use `100dvh` and `env(safe-area-inset-*)`.

### 6.1 Landscape (primary)

```
11" (1180 × 820)
┌──────┬───────────────────────────────────────────────────────────────┬────────┐
│ nav  │ status bar 56                                                 │        │
│ rail ├───────────────────────────────────────────────────────────────┤ safety │
│ 88   │ mode ribbon 64                                                │ rail   │
│      ├───────────────────────────────────────────────────────────────┤ 112    │
│      │ content: 12 cols, margin 24, gutter 16  → col ≈ 63 pt         │        │
│      │                                                               │        │
└──────┴───────────────────────────────────────────────────────────────┴────────┘
13" (1366 × 1024): same structure, margin 32, gutter 20 → col ≈ 73 pt; type scale unchanged,
extra room goes to the map/camera and a persistent timeline column.
```

- Clinical Home (11"): hero = cols 1–7, action tiles = cols 8–12 (2 × 2 tiles of 144 pt), timeline strip below (96 pt).
- Operator Arms: camera cols 1–9, controls cols 10–12; the proximity strip overlays the top 40 pt of the camera.
- Technician: 3-column card masonry; logs full-width.

### 6.2 Portrait

```
11" portrait (820 × 1180): content 8 cols (margin 20, gutter 16) → status bar 56 · ribbon 64 · content ·
tab bar 72 · safety band 104 (Stop on the right thumb side, 96 × 88; lease + alarms on the left).
```
Portrait is for the ward operator walking with the robot (HF-12): the map is on top, Stop and "Pause here" are in the bottom thumb band.

### 6.3 Mount orientation and handedness

A setting mirrors the rail and primary action column for left-handed users or a left-side mount. The theatre-door mount is landscape; the robot back-mount is portrait.

## 7. Sound, speech and haptics on iPad Safari (limits and how we handle them)

| Capability | Reality in Safari / iPadOS | Decision |
|---|---|---|
| Haptics / `navigator.vibrate` | **Not supported** in iOS Safari; iPads have no Taptic engine for web | No haptics. Every feedback is visual (+ optional sound). |
| Autoplay audio | Blocked until a user gesture; Web Audio defaults to the **ambient** session, muted by the silent switch / silent mode | Unlock the `AudioContext` on the sign-in tap; set `navigator.audioSession.type = 'playback'` (Safari 16.4+) so alarms are not silenced by silent mode. |
| System volume | Pages cannot read or set it | **Sound check** in the start-of-day flow ("Did you hear the tone?"); speaker icon in the status bar shows an unverified state until confirmed. |
| Background tabs / locked screen | JS timers are throttled and audio stops when the screen locks | Wake Lock (Safari 16.4+; fixed for Home Screen apps in iOS 18.4) while in motion modes or with an alarm; MDM auto-lock "Never" on mounted theatre iPads. |
| Speech synthesis | `speechSynthesis` works after a gesture | Robot speaker is primary; the iPad may speak readbacks only when enabled. |
| Speech recognition | `webkitSpeechRecognition` exists but needs a secure context, a user gesture and permission, may route audio to Apple, and struggles in OR noise | **Not used in theatre.** Future voice goes through the robot's microphones (HF-35). |
| Notifications | Web Push for Home Screen apps (16.4+) needs internet-reachable push services | Not used (no internet egress, L-5). In-app only; technician paging integration later. |

Sound design: three earcon families aligned with IEC 60601-1-8 priorities (A-3), short and low-mid frequency (500–1000 Hz fundamentals, which carry through masks and noise without shrillness), plus two non-alarm earcons: *arrived* (soft two-note rise) and *done* (single note). **Max one non-safety sound per 3 minutes in theatre** (HF-26). Volume is controlled on the robot for the room; the iPad follows its own hardware buttons.

## 8. Motion

| Use | Spec |
|---|---|
| Screen push/pop | 220 ms, `cubic-bezier(0.2, 0, 0, 1)`, 24 pt slide + fade |
| Mode change | Ribbon colour sweep left→right 300 ms + icon cross-fade; the only "big" motion in the app, so it is noticed (HF-18) |
| Progress (ETA, mission steps) | Continuous, linear; the step checkmark draws in 200 ms |
| Readback card | Scale 0.96 → 1 in 160 ms; the undo ring counts down 3 s |
| Alarm | Only the IEC flash (2 Hz High, 0.6 Hz Medium) in the banner and ribbon; no shaking, bouncing or full-screen flashing (X-4) |
| Across-room transition | 400 ms cross-fade; the first tap only wakes |
| Reduced motion | `prefers-reduced-motion`: replace slides and sweeps with 120 ms fades; **alarm flashing stays** (safety signal) but is limited to the banner |

Nothing animates while idle. A calm screen is part of the "dark cockpit".

## 9. Signature components

1. **Safety rail**: the product's signature. A vertical band with a big steady-red **Stop** (white hand-stop glyph + "STOP"), the control-lease pill ("Control: this iPad"), alarm count, and a small **Power off** (hold). It is identical on every screen, so muscle memory forms.
2. **Mode ribbon**: a full-width band in the mode family colour (magenta ribbons add a subtle 45° stripe at 6% opacity), with icon, sentence, distance/ETA, and "Controlled by". It carries the only "big" motion.
3. **Hero status card**: status word (44 pt) + activity (34 pt) + next (22 pt) + progress + mini floor plan. The floor plan is **drawn from `hospital-sim-env/isaac/scene/layout.py` rooms** as clean vector shapes with room names (not the SLAM grid) in Clinical; Operator/Technician can switch to the SLAM/occupancy layer.
4. **Place and instrument tiles**: photo (or clean illustration) top, name at 22 pt, secondary line (ETA or "2 on rack"), number/colour stripe to separate similar rooms (Theatre 1 vs 2).
5. **Readback card**: large sentence of what the robot will do, with Undo and a 3-s ring. Mirrors the robot's speech.
6. **Mission stepper**: vertical, current step highlighted, next step visible, completed steps collapsed with time stamps (Mako-style workflow).
7. **Alarm banner**: priority colour, icon, sentence "what · do · who", Acknowledge (64 pt), "Send to technician".
8. **Across-room view**: status word 88 pt, activity 56–64 pt, progress arc, safety rail still present.
9. **Slide-to-confirm and hold-to-confirm** controls (§5).
10. **Timeline**: human-readable events with icons; tap for detail; the technician sees raw source/topic.

Shape language: continuous-corner radii of 20 pt (tiles, cards), 14 pt (buttons), 999 (pills); 1 pt hairline borders in light theme; elevation by surface tone (no heavy shadows) in dim theme.

Iconography: a single open-source outline set (e.g. Lucide or Phosphor, **bundled locally**, no CDN), 2 pt stroke at 28–32 pt, filled variants for active states. Custom glyphs: robot-arrow, robot-hand, hand+walk, hand+arm, hand-stop, handover (hand-to-hand).

## 10. Theatre dim mode

- One tap on the status-bar moon, **or automatic** when the room is set to "laparoscopic/robotic case" (room context from the schedule, later) or when the technician sets a room default. Never switches mid-interaction.
- Background `#07090C`, surfaces `#10141A`, text `#D9DEE6`; camera and photos at 80% brightness; the safety-rail Stop uses fill `#D92D20` (still the brightest red object on screen).
- Maps: dark basemap, room outlines `#2A3342`, labels `--text-2`, path in `--robot-driving`.
- Recommend the MDM setting "Auto-Brightness on" plus in-app "Theatre dim" rather than asking nurses to change iPad brightness.
- Transitions between themes fade over 300 ms. **There is never a white flash**: no light-themed loading states in dim mode, and the HTML background colour is set before first paint.

## 11. Voice and tone (copy)

- Plain, short, active: "Going to Theatre 1", not "Navigation goal accepted".
- Name people and places, not systems: "Stopped by Nurse Tan", not "source: ui".
- Alarms: **what · do · who** ("Path blocked at Scrub door. Clear the path or tap Help.").
- Never blame the user. Never joke during a case. No exclamation marks.
- Raw ROS names, topic paths, `placeholder`, `Hz` appear only in Technician mode.
- Robot speech uses the same strings (single source of truth in a strings file), in English first; externalise for Chinese/Malay/Tamil later (X-5).

## 12. Implementation notes for the build (from the current `hospital-sim-ui/web` stack)

- Keep the **no-build, vanilla ES modules, no CDN** approach; add a `tokens.css` holding every token above as CSS custom properties with `[data-theme="light"|"dim"]`.
- A role guard in the client **and** an op allow-list on the server (L-3).
- `manifest.json` (display: standalone, theme colours per theme), apple-touch-icon, `apple-mobile-web-app-status-bar-style: black-translucent`; register no service worker that caches robot state (stale state is dangerous), except for static assets.
- Wake Lock request/re-request on `visibilitychange`; `navigator.audioSession.type='playback'`; unlock audio on sign-in.
- Pointer Events only (`pointerdown` for Stop, `pointerup` elsewhere); `touch-action: manipulation`; `user-select: none` on controls.
- Test matrix: iPad (A16) 11", iPad Air 13", iPad Pro 11"; Safari and Home Screen mode; light/dim; nitrile gloves; greyscale and deuteranopia filter (iPadOS Settings → Accessibility → Colour Filters); reduced motion; 1 m and 2 m legibility check with a printed target sheet.

## Sources

- Legibility and targets: [MIL-STD-1472F](https://www.denix.osd.mil/soh/denix-files/sites/21/2016/03/02_MIL-STD-1472F-Human-Engineering.pdf); [FAA HFDS ch. 5 displays](https://hf.tc.faa.gov/hfds/download-hfds/hfds_pdfs/Ch5_Displays_and_printers.pdf); [NN/g touch target size](https://www.nngroup.com/articles/touch-target-size/); [Determining the optimal touch target size (ICS)](https://www.ics.com/blog/determining-optimal-touch-target-size-3d-problem); [WCAG 2.2 target size](https://w3c.github.io/wcag/understanding/target-size-minimum)
- Colour vision: [Red-green colour blindness in Singaporean children](https://www.researchgate.net/publication/23405735_Red-green_colour_blindness_in_Singaporean_children); [Worldwide prevalence of red-green colour deficiency (JOSA A 2012)](https://opg.optica.org/josaa/abstract.cfm?uri=josaa-29-3-313)
- Alarms: [IEC 60601-1-8 guidance (Digi-Key)](https://www.digikey.com/en/articles/iec-60601-1-8-guidance-for-designing-medical-equipment-alarms); [AAMI on auditory icons (2020 amendment)](https://array.aami.org/content/news/updated-iec-60601-1-8-breaks-new-ground-development-alarm-sounds); [PUI Audio IEC 60601-1-8 application guide](https://puiaudio.com/resource/iec-60601-8-application-guide/)
- iPad Safari platform: [Screen Wake Lock (caniuse)](https://caniuse.com/wake-lock); [WebKit features in Safari 16.4 (audioSession, wake lock, web push)](https://webkit.org/blog/13966/webkit-features-in-safari-16-4/); [WebKit bug: Web Audio and silent switch](https://bugs.webkit.org/show_bug.cgi?id=237322); [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition); [Apple: cleaning Apple products](https://support.apple.com/en-us/103258)
- Surgical/robot UI references: [da Vinci 5](https://www.intuitive.com/en-us/products-and-services/da-vinci/5); [Hugo RAS](https://www.medtronic.com/en-us/healthcare-professionals/specialties/surgical-robotics/hugo-robotic-assisted-surgery/products-and-system.html); [Ottava](https://www.jnjmedtech.com/en-US/products/robotics/ottava-robotic-surgical-system/overview/); [Mako](https://www.stryker.com/us/en/joint-replacement/systems/Mako_SmartRobotics_Overview.html); [BrainOS glanceable UI](https://www.braincorp.com/resources/brain-corp-announces-new-ux-design-and-reporting-capabilities-that-simplify-robotic-usage-at-scale-125cc); [Seirios appearance settings](https://docs.movel.ai/new-collection/seirios-rns/product-features/supplementary-features/behavioral-and-interface); [Rightpoint on the Spot app](https://rightpoint.com/work/boston-dynamics)
- Lighting: [Current state of surgical lighting](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7305019/)
