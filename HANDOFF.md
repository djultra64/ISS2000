# Version 0.7 release — 2026-10-18

Original project work: **djultra64**. One worker, no agents.
GitHub: https://github.com/djultra64/ISS2000 — tag `v0.7.0`.
User-requested README status: **In development... SO-MANY-ALIGNMENT-ISSUES!**

Final Linux: `portable/ISS2000-Linux-0.7.0-final/launch.sh`.
SHA-256: `2a82788d3e69d60d83c9dda9a2573218fee4d3cb72323e1635ec21eee7efd5fa`.
Final Windows: `portable/ISS2000-Windows-0.7.0/iss2000.exe`.
SHA-256: `123c7ff51fdcc0c5f58b955b6f4cbc64ab385e7dd529c02707b00b8d33b92adb`.
Both ZIPs and combined checksums are in `portable/`. All Linux 49 / Windows 51
manifest files verify; each includes 43 notices, and fresh data is empty.
Older packages/data are preserved. Original ROM/assets are not distributed.

Windows compiled after fixing explicit roster UTF-8 decoding and a local `small`
macro collision. Focused tests pass; the macro rename left Linux byte-identical.
The final startup log now says 0.7.0. A disposable Windows copy rendered the real
3D introduction on a never-switched desktop; the exact final exe passed ROM
validation. Its normal WM_CLOSE did not finish and a post-close capture stalled;
the authenticated private test/task set was cancelled. Do not claim normal-exit,
Windows audio or full interactive gameplay acceptance. All those limits and the
general-suite/follow-up results are in `docs/releases/0.7.0.md`.

The machine recovered from the initial HA blocker. Own reservation:
`iss2000-07-resume-d4ea7d57-65ae-479e-8020-b442b47427af`.
All own Windows builds/tests ended and archives/evidence were retrieved before
requesting graceful helper-off. Windows offline, Sonoff off, 0 W and automation
idle were then confirmed; the own reservation was released. The power receipt is in
`.local/release-0.7-preparation/maquinita-final.json`; do not infer power-off
from helper-off alone. Private logs/captures remain under that ignored folder.
**Early development release; not accepted as 1.0.** Historical records follow.

---

# Version 0.7 preparation — 2026-10-18

Original project work: **djultra64**. One worker, no agents.
The user approved documented nearby-year internationals for historical roster
gaps, 2D filtering in Options, and final Windows compilation/publication as 0.7.
This latest Windows request supersedes the historical freeze below.

Linux portable: `portable/ISS2000-Linux-0.7.0/launch.sh`.
Executable SHA-256:
`5fe65bfd17b4b27595fd50bf6be1bb10e6cdccd92d7ed190cece833eb99184a1`.
All 49 manifest files and 43 notices verify; fresh data is empty.
All 2,332 real names are installed with 24 explicit period exceptions. Optional
2D Original/Bilinear filtering is saved from Graphics; Original remains default.
See `docs/releases/0.7.0.md` for exact validation and limitations.

General suite: 520 tests, 508 passed / 12 opt-in skips (489.653 s). Follow-up
private checks filled nine of these skips; only three historical NTSC diagnostics
remain unexecuted. Two initial wrapper stderr assertions were invocation errors;
they pass against the packaged executable without changing source. UI18 covered
filter save/restart and normal Exit Game; UI19 rendered actual real names and
ended after bounded inspection. Owned private processes and audio were removed.

Windows is blocked before power-on: HA Sonoff and consumption sensor unavailable,
helper off, queued automation on/current 0. No physical order or SSH was sent.
Own reservation `iss2000-0.7-9352417e-5e87-47b6-9b20-0db301b61a40`
was released; receipt in `.local/release-0.7-preparation/windows-preflight.json`.
Do not claim Windows 0.7 built or publish the combined release as complete.
Re-reserve and recheck the machine-control skill once HA recovers.

Release notes/legal/template are prepared in English. Goal-effect review retains
its earlier scope. **Not accepted as 1.0.** Historical checkpoints follow.

---

# Linux menu and shared-shadow correction — r70, 2026-10-18

Original project work: **djultra64**. Linux only, one worker, no agents.
Latest package: `portable/ISS2000-Linux-20261018-r70/launch.sh`.
Executable SHA-256: `50c405647e410b32a87bd8f192003cf277d072587b17d05205e43ee222e2dcbb`.

Euro Cup and Penalties move right by 5%; Scenario, Training and Option by 10%,
using the same current leading-edge basis as r69 and quarter-pixel rounding.
Labels, selected glow and lamps move together. Other menu composition stays.

All 22 players and the three authenticated officials use the same articulated
shadow style, including both original nighttime material variants. The ball's
independent dark texture is replaced with a rounded projected sphere using the
players' exact untextured translucent material, ground depth and light vector.
The existing two reserved banks cover all 26 owners with scoped interpolation.
No gameplay, original assets or timing are replaced.

Final general suite: 515 tests, 512 passed and 3 historical NTSC diagnostics
skipped (500.708 seconds; wrapper 501.203 seconds). The menu fixture passed
in 9.786 seconds and all six focused shadow checks in 33.777 seconds.
Exact-package hidden UI15 reviewed Main Select, a bounded day/clear friendly
field, and return to Main Select. The actual field banks contain authenticated
25 human owners and the ball with the exact shared alpha-96 material.
Explicit Yes in Exit Game exited normally with status 0; owned PIDs, runtime
and unique audio sink are gone. All 46 manifest files and 40 notices verify;
fresh portable data is empty. Older packages and user data remain intact.

Evidence: `.local/r70-verification`, `.local/r63-ui/runs/ui15`, and
`docs/research/pal-r70-menu-and-shadow-style.md`. UI14 setup stopped before game
launch for an absent SDL pkg-config path; UI15 supplied the known local path.
Night variants have CPU coverage, not a new nighttime GPU/performance claim.
Windows remains frozen. Prior goal-effect and broader gameplay acceptance
retain their earlier scope. **Not accepted as 1.0.**

---

# Linux first-item composition follow-up — r69, 2026-10-18

Original project work: **djultra64**. Linux only, one worker, no agents.
Latest package: `portable/ISS2000-Linux-20261018-r69/launch.sh`.
Executable SHA-256: `33e1ba83a4e63dace9059554ed7099ed8a77bff57c98117379a0c7a00336876e`.

Only Pre-season Match's text, selected glow and lamp move right together. The
requested 10% is relative to its r68 leading-edge position: 134 becomes 147.5
logical pixels after quarter-pixel rounding, a rigid +13.5-pixel translation
(about 65 output pixels at 1920×1080). Other item offsets and the title, row
backgrounds, ball, sizes and Exit Game retain their previous settings.

The existing original-CPU Main Select fixture first failed on the old position,
then passed in 9.348 seconds. Actual exact-package UI13 reviewed the result in a
hidden compositor and exited normally through Yes in Exit Game (status 0).
Owned processes and the unique audio sink were cleaned up. All 46 manifest
entries and 40 notices verify; fresh data is empty. Older packages and user data
are preserved. No new full-suite run is claimed for this bounded change.

Evidence: `.local/r69-verification`, `.local/r63-ui/runs/ui13`, and the r69
appendix in `docs/research/pal-main-select-r67.md`. Windows remains frozen.
Prior gameplay acceptance and pending goal-effect scope are unchanged.
**Not accepted as 1.0.**

---

# Linux menu composition follow-up — r68, 2026-10-18

Original project work: **djultra64**. Linux only, one worker, no agents.
Windows remains frozen. Latest package:
`portable/ISS2000-Linux-20261018-r68/launch.sh`.
Executable SHA-256: `5bdfd5de930cb0bb5c9de1f5001ae92af888e1202eee7fe3df0d2d8cd538af69`.

The nine Main Select items move slightly farther left, with their labels,
selected-label glow and lamps moving together. The extra original logical-pixel
insets are 6,5,4,3,2,1,1,1,1 from Pre-season Match to Option. This bends the upper
rows closer to the ball while retaining space for the lower indicators.
The heading, ball, rectangular row backgrounds and Exit Game retain r67's
positions. Original UVs, dimensions, vertical positions and task IDs are retained.

The existing original-CPU menu fixture first rejected the old placement, then
passed with the refinement (9.346 seconds). Actual exact-package UI12 reviewed
the nine visible rows and navigation through Option at 1920×1080. Confirmed Yes
in Exit Game exited normally with status 0. All owned processes and the private
audio sink were cleaned up. No full general-suite repeat is claimed for this
bounded composition adjustment. All 46 manifest files and 40 notices verify;
fresh package data remains empty. Older packages and user data are preserved.

Evidence: `.local/r68-verification`, `.local/r63-ui/runs/ui12`, and the r68
appendix in `docs/research/pal-main-select-r67.md`. Prior gameplay acceptance
and pending goal effects keep their previous scope. **Not accepted as 1.0.**

---

# Linux correction handoff — r67, 2026-10-18

Original project work: **djultra64**. One worker, no agents. Windows remains frozen.

Latest portable: `portable/ISS2000-Linux-20261018-r67/launch.sh`.
Executable SHA-256: `799f0283ec61c80b5c25d4849f2cc42c55bfaa11b3509061c4a246b82c626678`.
All 46 manifest files and 40 notices verified. Fresh package data is empty;
no ROM or saves are included. All older packages and user data are preserved.
r65 and r66 are intermediate menu checkpoints. **Not accepted as 1.0.**

Main Select now anchors the large ball and all its internal animated components
to the physical left edge. Following the user's latest capture review, MAIN
SELECT, option labels and their lamps use that same left origin, retaining their
original contour. Rectangular row backgrounds keep their previous horizontal
positions. The heading has more top margin. Exit Game uses the original larger
font with a heavier stroke and a larger active-device glyph, within the bottom
visible margin. No independent host overlay is introduced.

The prior adapter missed lamp frames and selected-label images, moved a grid
inside the ball as if it were a menu row, and switched layout at an arbitrary
whole-menu rectangle count. These are corrected with complete original image
profiles and scoped ownership. Text UVs and interpolation command identities
are retained. A further actual return from Option exposed the retained
destination byte being mistaken for current-scene identity. The final guard
recognizes the nine destinations mapped by the pinned original selector while
retaining exact live callback, resource, region and asset checks.

Verification: the general suite recorded under r66 passed 511 of 514 tests,
with 3 historical NTSC diagnostics skipped (524.780 seconds). The final r67
retained-destination correction and added selector source pin then passed the
complete original-CPU Main Select fixture (10.591 seconds), including the actual
failed return snapshot, all animation profiles, fixed backgrounds, four ports
and controller families, and foreign negative controls. This is not represented
as a second complete 514-test r67 run.

Exact r67 UI11 booted, entered Option and returned with the corrected ball/text
layout and footer preserved. The exit modal defaulted to No; cancel restored
the menu; explicit Yes then exited normally with status 0. The owned compositor,
monitor, audio sink and private runtime were cleaned up, and recorded PIDs are
absent. Actual screenshots and authenticated private video support these bounded
checks; physical controllers and sustained performance are not newly accepted.

Evidence: `docs/research/pal-main-select-r67.md`, `.local/r67-verification`,
`.local/r63-ui/runs/ui09`, `ui10` and `ui11`. UI10 retains the failed Option
return as a negative control. r65's general suite was interrupted deliberately
when the user changed the requested layout; no suite success is inferred from it.

The previous startup, title/controller text, saved-data, shadow and second-half
corrections are carried forward. Goal-replay trail and goal-overlay entrance
remain pending outside this menu correction. Gameplay and full release
acceptance remain with the user. Historical checkpoints below are superseded.

---

# Linux correction handoff — r64, 2026-10-18

Original project work: **djultra64**. One worker, no agents. Windows remains frozen.

Portable: `portable/ISS2000-Linux-20261018-r64/launch.sh`.
Executable SHA-256: `fc19000a9d714eb5629e262b6eb254926ca7fa1f5937e07882622bc1cc0588c5`.
All 46 manifest files and 40 dependency notices verified. Fresh package data is
empty; no ROM or user saves are included. Older packages/data are preserved.
r63 is an intermediate checkpoint with a retained second-half freeze; use r64
for this correction round. **Not accepted as 1.0.**

Completed corrections:

- First healthy automatic loading shortens the original presentation waits and
  batches genuine SDK file writes into one durable transaction. Errors and
  manual recovery remain real. The original font supplies `Loading game`.
- Main Select rows are raised 16 pixels with their spacing retained, following
  the user's layout choice. A separate footer uses physical north (Xbox Y /
  PlayStation Triangle / Nintendo X), or keyboard Y, for Exit Game.
  Confirmation defaults to No and uses active-device confirmation/back prompts.
  The original engine draws the text and glyphs.
- The title keeps the physical Start/Menu/Options/Plus/keyboard name through
  accepted-input animation. Select Teams' upper saved-data text fits its strip;
  direction hints use glyphs without the extra RS lettering.
- Edit Controller retains Config's Type while Cursor and Keeper show their
  original help, and preserves adapted labels through the exit transition.
- Player shadows use a simplified pose-driven ground silhouette. Daylight,
  weather and the pinned floodlight material are supported; the original
  stronger floodlight quad supplies its direction. Real pixel depth replaces
  the old constant far depth. Camera/replay cuts reset interpolation identities.
  Unrecognized owners retain original behavior; night support has CPU coverage,
  not a new GPU acceptance claim.
- Low-to-High reconfiguration reserves completion-ring capacity until original
  VI adopts the new pool. This prevents the demonstrated three-frame wrap that
  made a full completion queue look empty and froze second-half entry.
  No busy flags, queue entries, clock values or completion messages are fabricated.

Validation: **514 tests: 511 passed and 3 historical NTSC diagnostics skipped**
(542.216 seconds). The exact package booted from fresh private data and created
a real save. One complete friendly reached its final 1–0 result, including the
previously failing second-half return. The scheduler trace holds at most two
busy High slots while cached display is foreign, then cycles all three addresses;
a three-second observation confirms stage/actor/ball progression.

All game sessions used one hidden compositor and a verified unique null audio
sink. UI08 reached its 1,800-second harness deadline during a later rematch;
owned processes, monitor, sink and private runtime were cleaned up. This is
**not a normal-exit receipt**. UI02 previously verified confirmed Yes exit 0;
UI05–UI07 also exited normally. No current game session remains from this pass.
The partial rematch recording ends at harness cleanup, before the requested
goal-effect reproduction; its source-disappearance error is not a game failure.

Evidence, exact guards, benchmark limits and negative controls:
`docs/research/pal-r63-ui-and-shadows.md`, `.local/r63-verification`,
`.local/r64-verification`, `.local/r63-ui`.

**Pending:** goal-replay ball trail and goal-overlay 4:3-to-16:9 entrance.
A historical giant gold effect has not been proved to be the requested
ball-following trail, and the new recording did not capture the relevant goal.
There is no new goal-effect correction in this package. A question about which
trail is affected remains pending. Full gameplay, physical-controller and
sustained performance/audio acceptance remain with the user. These bounded
checks do not constitute release acceptance.

Older checkpoints below are historical and superseded by this handoff.

---

# Linux correction handoff — r62, 2026-10-18

Original project work: **djultra64**. One worker, no agents. Windows remains frozen.
The latest user instruction delegates all remaining functional tests to the user;
this pass starts no game and does not control the separately opened r60 process.
All older packages, private ROMs, settings, saves and dirty work are preserved.

Portable: `portable/ISS2000-Linux-20261017-r62/launch.sh`.
Executable SHA-256: `523d5e690a6a2797c1c0e0277312d2b5fa197b3ede0f8fbbc61840db5aea1cd7`.
46 manifest files /40 license notices verified. Fresh package data is empty;
no ROM or saves are included. The r61 folder is an intermediate checkpoint.
**Not accepted as1.0. Full automated r62 suite passed: 510 tests, 507 passed and 3 historical NTSC diagnostics skipped (445.732 seconds). Functional acceptance belongs to the user.**

Corrections completed in this pass:

- All six original set-play help variants are recognized, including Free Kick,
  Corner and the right-column Z prompt. Exact atlas/consumer, owner-port,
  original-font and Low/High guards remain in place.
- Set-play Curve/Cursor names follow the applied Type1–5 or Free map; keyboard
  retains its original keys. Nintendo labels follow actual physical positions.
- The exact replay A/B/stick/C-button diagram, R/Z/C prefix image and Start text
  in Cancel use physical labels through the original font. Original panel art,
  playback indicators, action captions and replay badge remain intact.
- The exact Handicap L/Z–R footer uses active-device names and preserves both
  left actions in the original cell. No host controls overlay is introduced.

Four new behavioral regressions first failed, then passed with the corrections.
They exercise original constructors and actual font output against saved RAM,
all four ports/families, all six control schemes and negative ownership/asset
checks. The existing AddressSanitizer owner-lifetime regression also passes and
still detects its historical negative control. Full evidence and scope:
`docs/research/pal-remaining-control-prompts.md`, `.local/r62-verification`.

Preserved earlier fixes: r58 cached-VI framebuffer ownership, r59 genuine
formation persistence and r60 serialized VI publication/getters. Their evidence
remains revision-specific; no claim that the VI race exclusively explains every
historical black screen is made.

Remaining functional observations are explicitly delegated: complete matches and
halftime continuation, modes/editing/Career, physical controllers, runtime prompt
appearance, audio/endurance/performance and wider60/120 scene coverage. The red
lineup Start label alone is also present in the original PAL reference; the
native navigation retry was incomplete. Gold geometry during a goal transition
still requires original comparison. Neither receives a speculative behavior patch.

Recovered r60 pixel evidence (historical, not r62 acceptance): authenticated
private120Hz compositor capture contains241 actual frames in about2s; player/leg
ROIs differ in all241, while grass and field-line ROIs each remain byte-identical.
Five successive leg contours differ within one receiver-aligned original pose
phase. Timing is receiver-side and not atomic GPU/task identity or physical
scanout. Evidence: `audio-r60-production/runs/acceptance-02/captures/idle-high120-01`.
That earlier audio session was interrupted and lacks a clean-exit receipt; its
recorded PIDs are absent. A separate separately opened r60 game was left untouched.

All ACTIVE/session wording in older checkpoints below is historical and is
superseded by this handoff. No fresh functional pass is inferred from it.

---

# Active Linux candidate — r60, 2026-10-17

Original project work: **djultra64**. Root only, no agents, one game execution at a time. Windows remains frozen.

ACTIVE sole private session: `.local/audio-r60-production/runs/acceptance-02`, exact r60,
compositor120Hz, normal/no debugger, copied private test data, source PCM+owned
monitor and renderer metadata/statistics recorded. First owned PipeWire video
capture works with negotiated format (no forced framerate); pixel analysis is
pending. Earlier three reference-harness native r60 runs are closed0. Audio
harness acceptance-01 failed SDL header setup before any game launch; preserved.

Portable: `portable/ISS2000-Linux-20261017-r60/launch.sh`.
Executable SHA-256: `5751f6d9e24295e2f5954fb0e2979955aacb39175e66d94e12149e6f8682dfee`.
46 manifest entries /40 notices verified; fresh data empty, no ROM or saves included.
**NOT accepted as1.0. Full suite passed506 tests:503 passed,3 historical NTSC diagnostics skipped,428.684 seconds. Fresh runtime validation is in progress.**

r59 normal fresh England Free Training reproduced black twice, actor/ball frozen4;
all framebuffers busy and completed-ring read/write equal. Both runs closed0.
A parent-debugger retry and a third normal run reached the field. Frozen RAM replay
with original scheduler routines stays unable to allocate over120 simulated VIs.

A deterministic extracted-runtime regression separately proves a native lost-swap
race: VI update flips/copies outside the SDK setter mutex; a swap after flip is
erased by copy. r60 serializes update and framebuffer getters with that existing
mutex in the source-pinned immutable `pal-runtime-timing-v4` derivative. The
regression fails on original/r59, passes on r60; five related tests also pass.
This is not yet proof that every live black screen has that exclusive cause.
See `docs/research/pal-vi-state-publication.md` for evidence and sampler exclusions.
The allocator, formation-save fix and all prior rendering/input changes remain.

Runtime update: first exact r60 normal run completed four same-process field entries
(Free, Free Kick, Corner Kick, Keeper selection), with real actions in free/corner
kicks, original pause/quit/menu returns, and clean exit0. Manual goalkeeper action
remains untested. Set Play help still shows N64 Z/R names (captures14/20), now an
explicit prompt blocker. Receipt: `native-r60-training-01/functional-receipt.json`.
Second independent fresh normal run `native-r60-training-02` reached the field and passed a10s steady counter-progress window, then two additional10s idle windows, without a debugger or concurrent suite. It closed normally0; its owned compositor/sink were removed. Third independent run `native-r60-high120-03` is active alone with private compositor120Hz. Original Graphics menu changed60→120 and saved120/720p/16:9; a normal Player VS CPU friendly reached natural halftime0–3 and then closed normally0, with owned compositor/sink removed. Second-half navigation was not resolved, so no complete match is accepted. Start327ms after the recorded ball/direction choice transitioned through fade into visible kickoff (capture48), without black. Exact skip-handler execution is not inferred from timing alone. Receipt: `choice-start-input-receipt.json`. Natural halftime0–3 is visible in capture55; second-half continuation remains unverified. Held SDK packet proof shows DpadUp0800 reaches port0; selected UI row/edge consumption still needs diagnosis. A2s authenticated private audio monitor sample contains94080 stereo frames,187101 nonzero samples,peak19687; no sustained/clipping-free claim. No full match or current intermediate-pixel acceptance yet.


# Active Linux candidate — r59, 2026-10-17

Original project work: **djultra64**. One worker, no agents, one game execution at
a time. Windows remains frozen. Existing packages, ROMs, settings and saves are preserved.

Portable: `portable/ISS2000-Linux-20261017-r59/launch.sh`.
SHA-256: `39d015c77a9becb926fdb3ab9e3093d1d1a93f1f4d742dd43ae4d882cfe3fce7`.
46 manifest entries /40 license notices verified; fresh data empty, no ROM included.
This is NOT accepted as1.0. Full automated r59 suite passed:505 tests,502 passed and3 historical NTSC
diagnostics skipped,434.349 seconds. Final expanded port guards are included.

Formation persistence correction is verified on this exact package. r58's original
accessory-choice bytes[0,0] routed explicit Save to RAM-only completion; all saved
files stayed unchanged, and cold restart lost slot2. The source/ROM-pinned r59
callback instead uses the original probe, asynchronous write and SDK result/error
handling on the two valid logical ports. No choice bytes or payload are fabricated.
CPU coverage:54 route/probe combinations,8 unchanged-worker success/error cases,
ROM/source binding and immutable outputs, plus unchanged out-of-scope port routing.

Live proof: `.local/editor-r59-diagnostic/persistence-receipt.json`.
`save-01` traces the original worker and actual SDK writer returning0; only file1
and its backup change. Normal cold run `cold-02` loads slot2, then saves slot3,
loads it and executes global Save Game (Saved). Normal `cold-03-global` retains
both slots and loads slot3. All three processes exited0. Cold runs have no debugger;
dummy audio excludes them from audio/performance acceptance. See
`docs/research/pal-formation-persistence.md`. The original US Low reference has completed three10s idle and three3s steady-run windows, then closed its owned compositor/sink. One longer run was rejected after a training reset. No regional timing-equivalence verdict is claimed. Native r59 normal run `native-r59-high60-01` reached a black training field and froze at stage_tick2234, actor4, ball4; confirming did not recover. It exited0. A separate parent-debugger retry reached the field and advanced; this does not resolve the intermittent blocker. A second normal retry `native-r59-high60-02` is active alone in a private compositor. Evidence: `.local/ntsc-animation-reference-prep-01/runs`; first failure receipt retained.

Original PAL UI comparison: `.local/ntsc-animation-reference-prep-01/runs/pal-ui-reference-02/ui-reference-receipt.json`. Start game also remains red in the unchanged original after Down while Member opens. Cancel in its Member submenu selects EXIT before confirmation. Thus that appearance alone is not evidence of a port render defect; repeat the native halftime route with controlled inputs and complete transitions.

Open gates include: intermittent black field entering fresh Free Training, replay N64 R/Z/C/controller-diagram help, other remaining
physical-button prompts, native second-half navigation retry, visual followups,
actual intermediate-pixel60/120 acceptance on the current executable, exact coin
animation skip, two complete consecutive friendlies, source clipping and current
sustained performance/audio, other editor/mode paths and physical controllers.
Do not infer any of these from the storage regression or historical r58 results.

Closed r58 runtime receipt: `natural-halftime-02` exited normally (actual game
exit 0) and its owned compositor/audio sink/runtime were cleaned up. One complete
friendly passed; the second reached halftime only. Captures 66–82 show a lineup
navigation/display discrepancy requiring diagnosis; no second-half pass is claimed.
Whole-stream analysis retained 155,249,664 consecutive stereo frames unchanged
(3234.368 seconds), zero interior insertions. Exclusions: 56,320 initial silent
monitor frames and 399 queued source frames (8.3125 ms) at normal shutdown; the
remaining 2,816 monitor frames are zero. Original source saturation remains;
monitor saturation counts/runs exactly equal converted PCM, not a clipping-free
acceptance claim. See private `audio-interpretation.json`. No game remains active.

# Active framebuffer correction candidate — r58, 2026-10-17

Original project work: **djultra64**. Root only; no agents and one game execution
at a time. Windows remains frozen. All older packages/data are preserved.

New portable: `portable/ISS2000-Linux-20261017-r58/launch.sh`.
SHA-256: `ee54e4a9c32dfd844e74195cd9e8f42d775d5f85714a536136e9aa096a7f18bc`.
46 manifest entries / 40 license notices verified, data empty, no ROM included.
This is NOT 1.0: fresh runtime acceptance and other known blockers remain open.

The new ROM/source-pinned allocator derivative rejects the framebuffer still
owned by the original cached VI state, even when video reconfiguration cleared
its busy flag. It retains the original first-free ordering, busy writes, task
completion, scene coverage and VI cadence. Hook replacement requires the exact
original PAL resident symbol identity. No new interpolation or simulation changes.

Two focused regression tests pass: original scheduler stalls after three
completions in the reproduced state, corrected scheduler continues ten; all 128
pool-size/busy-mask/current-identity combinations preserve guest RAM and select
only an eligible slot. ROM/source mismatch and immutable-output guards pass.
The complete suite passed: 503 tests, 500 passed, 3 skipped historical NTSC diagnostics, 434.684 seconds. Final expanded framebuffer (2), native selection/input integration (7) and exported-symbol (1) tests also pass. Evidence is under `.local/r58-verification`.

Fresh runtime checkpoint: exact r58 completed the first natural friendly, including
both regulation halves, EX1 and a golden goal in EX2 (Germany 1–0 England).
Captures 36/37/38/39 show Game Result, scorer, Play Again and return to Main.
No debugger or guest-memory intervention was used. The same process saved the
native graphics limit from 60 to 120 and started a second Player-vs-CPU friendly.
This compositor remains 60 Hz: this is settings/transition evidence, NOT actual
120 Hz or intermediate-pixel acceptance. The second match reached natural
halftime 0–2; its second half and whole-stream audio are not yet accepted.
Replay opened and returned to gameplay, but capture 63 confirms a BLOCKER:
original N64 R/Z/C/controller-diagram help remains visible. Replace it with
correct active-device/action prompts before accepting controls. Additional visual
followups are recorded in the run's visual-followups.json. Coin-skip timing is
not proven: separate tool calls may have delivered Start after the coin finished.

The sole active run is `.local/audio-r58-production/runs/natural-halftime-02`,
exact portable r58, real isolated PipeWire audio, no debugger, 720p/60. The prior
`natural-halftime-01` attempt failed while finding SDL build headers, before any
game launch; the second uses the existing Homebrew pkg-config location.

The prior r57 debugger run is CLOSED (game/GDB/supervisor PIDs absent). Escape
initiated shutdown; audio-route inactivity triggered harness cleanup before an
actual inferior exit-code receipt was captured. Do NOT claim exit 0 for that run.
Its 6 GiB core and 8 MiB frozen RAM are retained. The later bounded transition
tracer captured no new reconfiguration before shutdown; no live initial-condition
trace is claimed. The one-word recovery changed diagnostic guest state only.

# Active Linux correction candidate — r57, 2026-10-17

Original project work: **djultra64**. Windows remains frozen. Existing packages,
ROMs, configurations, saves and dirty source changes are preserved.
Latest user steering: no further agents; continue as one worker with only one
game execution active at a time. The existing private r57 debugger run is retained.

New portable folder: `portable/ISS2000-Linux-20261017-r57/launch.sh`.
Production SHA-256: `f1a5fcd13794f3428ea86c6d4537d4092b3c4778cb67af64c002a4b5a4676480`.
All 46 manifest entries and 40 license notices verified; data is empty, with no
ROM or saves included. Input fixtures and render-evidence build option are OFF.
This is **not accepted as 1.0**. The r56 record below remains historical evidence.

## Blocking runtime finding — r57 natural halftime

The exact r57 production run `.local/audio-r57-production/runs/uncontended-production-02`
reached a natural first halftime (Germany 1–0 England) and traversed the original
halftime screens. The compositor then remained black. Display-list logging froze
at sequence 25329, time 795.005212 seconds, while real audio queues continued.
Pause/resume did not recover the picture. GfxThread, RT64Workload and Present
were observed waiting in futexes; this does not by itself identify the cause.
This is a real rendering/progress failure, distinct from the KWin XGetImage
capture artifact below. Two complete matches and sustained acceptance FAILED to
complete. No causal link to the user's earlier incident or interpolation is yet
established. Pause/resume and Alt+Enter did not recover rendering. Escape subsequently
closed the actual game normally (exit 0); no debugger was attached. The parent-debugger reproduction and isolated scheduler finding below supersede the initial deadlock suspicion; no product fix has been added yet. Existing automated passes do not override this runtime blocker.

## Second reproduction and framebuffer ownership diagnosis

The same r57 hash reproduced black immediately after a natural 1–1 halftime in
`.local/halftime-r57-gdb/runs/halftime-01`. Sequence 21822 stopped at scene 0x604.
A full core, all-thread stacks and 8 MiB guest dump were retained before recovery.
RT64 queues were idle waiting for work; the original main loop still ran. Both
original task banks and all three framebuffer slots were busy. Pending graphics
tasks had no assigned framebuffer; no SP/DP graphics task was active. The completed
framebuffer ring had equal read/write pointers, with cached/current/next VI all
0x80500000. This is guest framebuffer starvation, not evidence of an RT64 lock deadlock.

A controlled diagnostic cleared ONLY the non-current 0x80654000 busy flag. The
same process immediately resumed the second half and display-list production.
This is not a product correction or valid acceptance run; its subsequent audio,
timing and match progress cannot close unmodified production acceptance.

`.local/framebuffer-starvation-repro/run.py` compiles the original PAL allocation,
completion and VI-retirement routines, with explicit simulated VI/ownership
boundaries. With an empty ring/free pool and cached/current framebuffer equal to
the first slot, it reproduces the exact three-busy/equal-ring state after three
completions. Starting with a different current slot advances ten completions and
retains only the current slot busy. Original reconfiguration clears all pool flags,
including the displayed slot; retirement relies on a changed framebuffer address.
The live transition that creates the initial condition still needs a bounded trace.
A read-only tracer is installed in the sole private debugger run for the next video
reconfiguration. No agents may be used; only one game execution at a time.

## New audio correction and verification gate

The isolated r56 production session completed a natural friendly and reached a
second match after saving 60→120 and skipping the coin animation. Whole-stream
comparison nevertheless proved 27 inserted silent gaps totaling 2,102 stereo
frames over 1,730.8 seconds. Every converted frame was retained unchanged and in
order; no downstream clipping was introduced. This was a real continuity failure.

All gaps aligned with device-pull and enqueue boundaries. The output device
started empty, without a reserve. A paired real-SDL replay of the same captured
PCM/timing produced 20 gaps before and zero after priming with at least 4,096
real stereo frames; all 959,360 frames remained identical and ordered. The patch
only keeps SDL paused until that reserve exists, once per device lifetime.
Guest AI timing, sample conversion, frequency and volume are unchanged. Target
reserve is 85.33 ms of PCM; packet rounding and backend latency add to it, and
this is not a guarantee against arbitrarily long host stalls. Three production-
extracted tests failed before and passed after; independent review found no blocker.

Final r57 source suite: **501 tests in 425.924 seconds; 498 passed, 3 skipped**.
Only the historical NTSC diagnostics requiring `ISS2000_DIAGNOSTIC` are skipped.
Evidence: `.local/r57-verification/full-suite.log` and package receipt alongside it.
The exact-r57 run retained 59,723,776 consecutive output frames unchanged
(1,244.245 seconds), with zero interior insertions or substitutions. The initial
54,272 monitor frames and intentional shutdown tail (2,963 queued source frames,
61.73 ms) are excluded explicitly. Monitor clipping counts/runs match converted
PCM; saturation already exists in original source audio. This interval includes
the graphics freeze described above, so does not close complete-match or sustained
performance acceptance. Receipt: `audio-interpretation.json` in that run folder.

## Exact-package runtime checks already completed

A fresh copy in a path with spaces booted from empty data at 720p/60/16:9 using
an explicit private supported-ROM argument. Main and native Graphics worked.
Alt+Enter toggled actual SDL fullscreen; native Save persisted fullscreen and a
fresh process restored both SDL and window-manager state. All relevant private
KWin game children exited 0. These checks used dummy audio, so establish no sound
or performance result. Receipt: `.local/r57-portable-clean/acceptance-receipt.json`.

A black X11 capture was investigated before changing code: private compositor
captures showed the animated Main menu while XGetImage returned stale black/KCEO
buffers, repeatedly and without game input or resizing. This is a capture-method
artifact, not a reproduction or explanation of the user's earlier black screen.
KWin visual checks now use private compositor captures.

r57 retains all r56 interpolation/resource/radar corrections and the r55 all-22
maximum-detail matrix capacity and stick fixes. Detailed r56 GPU interpolation,
Career, Training, controls and mode evidence remains below with its exact scope.
Physical controller prompts/rumble, physical 120 Hz/4K, full NTSC/PAL wall-time
animation comparisons and remaining campaign coverage are not inferred as passed.

---

# Active Linux correction candidate — r56, 2026-10-17

Original project work: `djultra64`. Windows compilation, execution and power
actions remain forbidden. The user authorized parallel agents after the initial
solo request. Existing dirty work, packages, ROMs and saves are preserved.

New Linux candidate: `portable/ISS2000-Linux-20261017-r56/launch.sh`.
Production executable SHA256:
`4acc1f74ea76dca1536a0b57b5858933a67f792346eb1e4209ef0eb250d6deea`.
Input fixtures and render diagnostics are OFF. All46 manifest entries and40
notices verified; delivery data is empty and contains no ROM. Exact copied-folder
execution is separate from packaging and recorded below. **Not accepted1.0.**

### Confirmed causes and bounded fixes

- r55 all22-detail tasks traverse20,157–22,099 command slots, exceeding the
  metadata parser's16,384 bound. Whole-map rejection removed player/camera
  interpolation while original rendering continued. Bound131,072 retains
  cycle, malformed-command and depth rejection; actual captured tasks plus
  synthetic regressions pass. This is not a black-screen explanation.
- RT64 target-vector growth raced presentation's indexing. The emitted-block
  RED/GREEN regression verifies growth now holds the same lookup mutex,
  releasing it before waits/GPU work (workload derivativev4).
- A separate missing/empty presentation target now uses validated bounded
  event-owned original VI pixels for one frame (present derivativev2).
  Independent review and emitted-code tests cover dimensions, RGBA16/32,
  storage bounds, existing targets and lock ownership. The user's persistent
  black screen was not reproduced; its exact cause is not established.
- Radar metadata tracks actual allocation generations/roles, parent-list
  reachability, bank generations and immutable bytes. Sixteen original-callback
  parity cases cover both banks, Low/High, flat/projected and r55 wrappers,
  preserving all8MiB/CPU state and exact46 marker identities. r55 all22
  capacity, marker sampling and stick corrections remain intact.
- Optional first-quarantine diagnostics were added; permanent fail-closed
  tracker behavior was not speculatively relaxed. No quarantine was observed.

### Current verification

Final source suite: **498 tests in500.610s,495 passed,3 skipped**. Only the
three historical NTSC `tests.test_native.NativeTests` requiring unavailable
`ISS2000_DIAGNOSTIC` are skipped. The earlier489-test fixture setup error was
repaired in test-only declarations and the final suite passes. Log:
`.local/consecutive-r56-baseline/full-suite-final.log`.

Actual final development executable `54713667e512beddda0394b62f128da2e8aac3587d653b24f384f8237ceee156`
ran first friendly60 → original Pause/Quit → Graphics save120 → second friendly
with Start during entrance/coin, reaching the field without persistent black.
Real GPU radar-region captures:222 readbacks/89 distinct fractional workloads
at60 and18/5 at120. Region includes underlying field; it does not isolate
radar-dot pixels. All3242 field tasks retained snapshots;46 radar commands
were active. No fallback event occurred, so actual fallback invocation remains
unobserved. Evidence: `.local/r56-radar-gpu-final/receipt.json`. Its external
X11-window-destruction cleanup caused BadWindow/termination; launcher0 is not
a clean game exit. GPU results precede that harness shutdown.

Earlier corrected process `3009e331...` independently produced240 center256
readbacks/51 workloads,42 with distinct fractional images at120. It predates
fallbackv2, ran a partial friendly and closed normally via Escape. Evidence:
`.local/consecutive-r56-fixed`. No full-match completion is inferred.

The exact production package was copied into a path containing spaces. Clean
boot with explicit private ROM argument used720p/60/16:9 and reached Main
without storage questions. Native Graphics opened and applied/saved900,1080,
1440,1800,2160p,120 and a fullscreen preference. Alt+Enter changed the native
label; settings were restored720/60 and a fresh process booted. Both Gamescope
sessions closed via Escape. **Actual fullscreen subsequently passed under private KWin OpenGL:**
Alt+Enter toggled actual SDL and window-manager state; native Save and a fresh
process restored fullscreen. Both game children exited 0. Earlier Gamescope
and KWin painter limitations are retained in the dated evidence below.
Receipt: `.local/r56-portable-clean/acceptance-receipt.json`.

Real-audio development Training covered all four variants, original exits,
Type1–5 layouts/persistence and a saved/reopened Free binding. The concurrent
11m14s run found15 proven downstream inserted-silence boundaries totaling1372
stereo frames (28.58ms); its continuity is not accepted. Evidence:
`.local/audio-r56-acceptance/runs/training-controls-real-audio-02/acceptance-receipt.json`.
The exact-production real-PipeWire session completed a natural England 0–2
Germany friendly, returned through original menus, saved 60→120, then reached
a second friendly after Start skipped the coin animation, without persistent
black. Other project games/builds/tests were stopped during this recording.
Whole-stream comparison found all 83,078,213 converted stereo frames unchanged
and in order, but 27 inserted all-zero stretches totaling 2,102 frames
(43.792 ms; maximum 15.833 ms). Startup and tail are excluded explicitly.
There was no downstream clipping added; original-source saturation is separate.
**Audio continuity still fails and is under investigation; r56 is not accepted.**
Evidence: `.local/audio-r56-production/runs/uncontended-production-01/whole-pcm-comparison.json`.
No dummy-audio, capture or counter result establishes sustained performance.

Current remaining acceptance includes fixing/retesting real audio continuity,
sustained performance, multiple completed consecutive matches and editor/league/cup coverage,
physical controllers/prompts/rumble and physical120Hz/4K. CPU timing proofs
separate movement, skeleton, match clock and DAC; final wall-time NTSC/PAL
comparison of displacement, animation cycles and natural match duration is
still unverified. See dated research addenda; no global simulation speedup
was introduced. No finished1.0 claim is made.

## Production r56 editor and competition routes — 2026-10-17

The same verified production copy and private keyboard harness described above
ran sessions04–05 with fixtures/evidence disabled and dummy audio. World League
New Game reached the 16-team first-season schedule and prematch editor;
International Cup reached Europe qualifying (England–Sweden), and Euro Cup
reached Group 11 (England–Faroe Islands). Each original Continue route reported
NO DATA, as expected for this seed without competition saves. These are menu
and setup checks; completed competitions and competition save/reload remain
unverified.

After original Options → Data → Data load reported Loaded, the prematch
Edit Formation loader restored the genuine historical England 4-3-3 slot 1.
The original Save list accepted the same formation in previously empty slot 2,
and the same-session Load route explicitly reported Loaded for slot 2. Later
Options → Data → Data save reported Saved. However, cold session05 showed
slot 1 present and slot 2 empty. **New editor-slot persistence is unresolved and
is not accepted.** All four main Controller Pak images remained byte-identical
to the snapshot before session04; Pak 1's changed backup differs from its main
image only in the original probe's first 32-byte block. Startup snapshots also
retain the same main hash. This does not establish a disk-write failure or a
cold-start overwrite: original category/dirty-state and intervening navigation
must be traced before any fix. Session05 did not repeat explicit global Data
load, a further difference to isolate. Read-only tracing found a more specific
candidate: original formation Save `80017FEC` sets category 4 in `8012E68C`,
whereas original formation Load `800181AC` immediately clears that category
through `8001CB4C(4)`. Global save `802B22F8` gates category serialization on
that mask. A focused CPU run of seven untouched original helpers confirmed
Save sets dirty4 and Load copies identical 66-byte positions while clearing it.
This alone does not explain persistence: original editor Save also has a
separate scheduled disk worker `802A3720` calling `80019A64(selected_port)`.
Correct-overlay callback `802A3464` chooses that worker only when original
save-selection byte `8012E62B + selected_port` is 1; otherwise it takes a RAM-only
save branch. This two-entry original menu selection is separate from the four host Pak
accessories. Dynamic selected-port/selection/worker tracing remains pending.
No root cause or product fix is claimed.

Both sessions exited through Escape in an original menu, with actual game
child return code 0 recorded separately from the compositor. This verifies a
clean closure path without revising the earlier Career harness termination
limitation. Evidence: `.local/modes-r56-production-01/modes-receipt.json`,
`runs/session04/41-formation-save.png` through `45-slot2-loaded.png`,
`82-global-saved.png`, and `runs/session05/11-cold-slot2.png`. Original user
saves and delivery data remain untouched. No performance, real-audio, physical
controller, or finished Linux 1.0 claim follows from these checks.

## Production r56 Career save/reload verification — 2026-10-17

The final production candidate executable SHA-256 is
`4acc1f74ea76dca1536a0b57b5858933a67f792346eb1e4209ef0eb250d6deea`.
An isolated copy under `.local/modes-r56-production-01/ISS2000 Portable`
verified the package manifest before launch, with fixtures/evidence disabled.
Genuine older data was copied from `.local/menu-acceptance-01/data`; original
saves and the delivered empty data directory were untouched. Keyboard input
used the display discovered from each private compositor's environment and
verified the owned executable/window before every step.

The original Career file selection recognized File 1, A, Sweeper, first year
September week 2. Original Rest advanced to week 3, followed by the original
Thomas event. Options → Save End → End after saving → Save Game YES displayed
Saved. Controller Pak 1 changed from
`2b03285e75f764610720444129b64fe9b06ddb75507685ec87aac4bb97b9be47` to
`ed47710482805b36074eae4feea9c4de5b9f22e19a289a3e197bb7f8c322f620`.
After process termination and a fresh launch of the same copied package, file
selection and actual load both showed September week 3 and the weekly action
prompt. Both compositors exited, but each game child returned -6 after the
test harness used X11 window destruction: the log reports XInput BadWindow
followed by termination. This is not clean-exit acceptance; subsequent harness
closures must send SDL quit/WM_DELETE rather than destroy the window. Private evidence and
hashes are indexed by `.local/modes-r56-production-01/career-receipt.json`.

This proves the scoped real Career action/save/cold-load path. It does not
prove a Career match, full campaign, sustained performance or sound quality
(the test used dummy audio). Edit/League/Cup remain pending; GPU execution was
released for the separate uncontended audio/match session. This is not completed
1.0 acceptance.

---

# Latest Linux correction candidate — r55, 2026-10-16

Run `portable/ISS2000-Linux-20261016-r55/launch.sh`. This is a fresh correction
candidate, not completed1.0 acceptance. Older packages and user data are preserved.
No subagents were used for this pass. Windows remains completely frozen.

- Retain all22 verified field players at maximum detail. Live detail variant0
  was incorrectly excluded before; the original324-matrix pool also exhausted
  after14 retained players. Separate double-buffered field banks now hold all
  418 bone matrices, with exact original-bound/scene guards. Original GPU clipping
  handles viewport edges. Menus keep their original banks.
- Remove28 proven redundant High-radar edge strips after full original output
  validation. They double-blended the right-side pieces and caused opaque seams.
  The14 primary pieces still cover the full radar exactly once.
- Inset the exact8x8 marker atlas cell samples. Native samples are preserved;
  upscale sampling checks find32 adjacent-cell hits before and zero after.
- Gameplay left stick gets a continuous radial deadzone and gentler low/mid
  response. Full deflection and direction remain available; menu navigation is
  unchanged. Physical ROG Ally corner/free-kick feel still needs user acceptance.

Both Linux builds exited0. Scoped regressions pass:19 player/metadata/shadow,
5 original traversal/radar coverage,1 extended bank ownership,1 stick response,
1 atlas sampling, and a final6-test affected-path group. These overlap and are
not a full-suite count. Actual hidden1080p Preseason passed kickoff and ongoing
play. Two captured field frames (both banks) each have22 visible root flags,
418 distinct valid bone matrices, and zero overflow. Captures are genuine private
GPU/compositor output; dummy audio and debugger overhead do not establish audio
quality or sustained performance. No physical device test is claimed.

Production input testing/evidence areOFF. Manifest46 files and40 authentic
notices verified; fresh data empty. Executable SHA256:
`aa8296cce838e30d710047c47e1ef0372e4dc131864cb74d348fc70de589cc26`.
Private receipts: `.local/r55-package-receipt.json`,
`.local/corrections-r55/receipt.json`, and
`.local/corrections-r55/final/field-visibility.json`.
See `docs/research/pal-player-visibility-and-radar.md` for causes and guards.

Historical r54 interpolation, labels, backgrounds, HUD placement and RT64
in-flight target lifetime corrections remain included. Direct private radar
marker interpolation and complete mode/audio acceptance are still open.

# Latest Linux correction candidate — r54, 2026-10-16

Run `portable/ISS2000-Linux-20261016-r54/launch.sh`. Fresh package data is empty
and requests the supported English PAL ROM. Every older package, imported ROM,
preference and save remains preserved. Windows remains completely frozen.
All actual runs were private headless Gamescope sessions with owned DBus; all
were closed normally. No full suite or completed1.0 acceptance is claimed.

Included corrections:
- Select Teams uses only bumper glyphs beside the region title: LB/RB, L1/R1,
  L/R or Q/E for the active family. LT/Z still works internally but is not shown.
  New flat Xbox pill artwork, native RS+direction Saved Data prompts, aligned
  Menu Random footer. Original-engine labels read Saved Data/Load Saved Data.
- Menu base tiles and both decorative moving layers cover16:9. Exact original
  clipping boundaries repaired, with transactional resource/UV guards.
- Shared model interpolation now uses live allocator generations and the exact
  referenced model bank in every scene, rather than menu owner allowlists.
  Pooled2D sprite/font metadata follows the actual submitted arena and lifetime;
  rawTMEM matches only with immutable full-content hashes, never copy IDs.
  Score flags join this shared tracking. Direct radar marker interpolation is
  still a separate private-list ownership gap; see pal-direct-hud-interpolation.
- Genuine22-player CPU culling is disabled during the verified field scope;
  normal GPU clipping determines visibility. Other object kinds stay original.
- Radar and markers move together for both flat/projected producers and Low/High
  field/Training. At720p the radar ends near698 and playerplates near678; timer
  moves up about8px. One-pixel High repair strips now retain the same fractional
  texel phase as the main radar pieces. Other raster/filter paths stay original.
- Confirmed r53 Preseason core is an interpolated RenderTarget use-after-free.
  Presentation holds an owner-specific lifetime pin through its last GPU fence;
  only destructive configuration cleanup takes the exclusive side and coherently
  retires counters. See render-target-lifetime.md for exact core and lock order.

Both final Linux builds compile/link. Final changed checks7+7 pass with zero
skips; earlier core/global/producer tests retain their scoped logs. Independent
reviews found no concrete unresolved defect in these changes. No full suite was
resumed. Actual hidden Preseason at requested120 passed coin toss, kickoff and
ongoing play (final3); latest HUD source at requested60 repeats that transition
and captures clean lowerHUD, raisedtimer and bumper-onlySelectTeams (final5).
Main Select GPU readbacks prove3 same-workload pairs at60 and4 at120 with distinct
pixel hashes, different fractional weights and zero3Dgroups. This is selected
indicator ROI evidence, not whole-game, performance or physical120Hz acceptance.

Final latest visual captures: `.local/select-teams-54-final5/05-teams-bumpers.png`,
`12-field-hud.png` and `13-field-hud.png`. Actual native Graphics at120 with
Apply and save worked in final3/final4. Private readback tests used dummy audio;
this pass does not expand prior audio/physical-controller/mode acceptance.

Package:46 manifest files and40 notices verified, test controller/render evidence
OFF, no ROM/assets/saves bundled. Executable SHA256:
`478d36e9d39318e387b011ae307d45e3e241ef4e6183295ba705348c4dbfd483`.
Receipts `.local/r54-package-receipt.json`, `.local/r54-runtime-receipt.json`.
Immutable derivatives: rt64-menu-interpolation-v3, rt64-present-lifetime-v1,
rt64-sprite-phase-v4. Canonical builds .local/pal-game-build and
.local/pal-production-build. See README and research notes. Source remains dirty;
no commit or Windows action was requested or performed.

---

# Latest Linux correction candidate — r53, 2026-10-15

Run `portable/ISS2000-Linux-20261015-r53/launch.sh`. All old portable folders,
imported ROMs, preferences and saves remain preserved. The fresh package data/
is empty and asks for the supported PAL ROM. Windows remains completely frozen.

Latest user steering explicitly authorized root to perform tests while the user
sleeps; all game execution in this pass used private headless Gamescope windows.
Do not resurrect the earlier stopped full integration22 without a new reason.
No full-suite pass or completed1.0 acceptance is claimed.

Type5 cause and correction:
- Saved Type5 was selected and live projection ran, but three semantic actions
  were permuted in all original guest profiles. N64 C-down is Dash0004,
  C-left is Lob0002 and C-right is OneTwo0001 in guest profile0. The actual table
  order is OneTwo, Through, Dash, Pass, Shoot, Lob. Physical presets are unchanged.
- Manual-derived expectations plus genuine downstream held-Dash code now cover
  the meaning of the actions.21 focused tests passed across schemes, normalizer,
  full processor, startup autosave and previous storage behavior; no full suite.
- Actual hidden native Training confirmed all eight Type5 held actions. RT set
  the original Dash counter/flag0400 and release reset it. The real Controller
  screen confirmed Type5 before Begin Training loaded the field. Input used the
  app-only virtual SDL controller; physical Ally button acceptance remains open.
  User confirmed they play directly on the ROG Ally. Evidence and actual GPU
  capture23-running-rt.png: `.local/type5-runtime-02/receipt.json`.

Initial automatic saving:
- The first exact original DataChange initializer gets a bounded host first-entry
  scope. Original handlers perform actual create/write/close without questions;
  the exact original UI queue derivative hides healthy startup-only artwork.
  Real probe/allocation/write failures show the existing error UI. Original SDK
  result800C1124 is checked because original2758 could label failed writes Saved.
  Later entries remain manual; no input injection or payload success stubs.
- Actual fresh hidden boot created the genuine file (directory0 NISX/A4), reached
  Main Select with only Start inputs, and drew no healthy storage sprite/text.
  `.local/startup-autosave-02/` records states5→1→2/closed and SDK success.
- A second hidden boot executed the packaged production binary with private
  existing-save copies and keyboard Enter only. Main Select appeared, all four
  primary save images stayed byte-identical, and no healthy storage art drew.
  `.local/startup-autosave-03/`. Both sessions exited normally with an owned
  private DBus session. First Type5 harness lacked DBus and its shutdown-only NFD
  assertion is recorded separately; gameplay did not abort.

Development53-autosave and production22 compile/link. All46 manifest entries and
40 notices verify; input fixtures/render evidence OFF in production. SHA256:
`72b1e7d4459cea9ca33c96b0cf9972bdae7af0888a8266fba3c048c6fe0bbd62`. Receipt `.local/r53-package-receipt.json`.
Immutable startup derivative v4 SHA256:
`29622c6ef276cf5cbb8a7e632dc67b186dbe3af787639e178a6d06f0880a0b7c`.

Carry forward r52 fixes and their visual/audio/performance limits below. The
reported black-screen failure was not seen in these scoped Training paths;
do not claim every mode/controller or that prior report exhaustively resolved.
A residual bitmap ControllerPak plate under Select Teams/Edit Data is identified:
asset19 I4 atlas+1000, English row48, live80271140; descriptors803DB408 via pooled
sprites8013D8E0/D91C. It needs a separate bounded Saved Data bitmap replacement;
ordinary text-message patches do not cover it. No asset edits in this pass.

---

# Previous Linux candidate — r52, 2026-10-15

Manual tests resume from `portable/ISS2000-Linux-20261015-r52/launch.sh`.
The user explicitly said to stop running so many automatic tests and will do
manual testing. Full integration22 was stopped at that request; do not resume
or repeat it automatically. No full-suite pass for r52 is claimed. Do not run
the game on the user's behalf. Windows remains frozen: no builds, SSH or power
work. Preserve every old portable folder, imported ROM, preference and save.
The fresh r52 folder is empty and requests the supported English PAL ROM.

Development52 and production20 both compile/link successfully; logs:
`.local/pal-build-52-final.log`, `.local/pal-production-build-20-final.log`.
All46 package manifest entries and40 authentic dependency notices verify.
Production input fixtures/render evidence OFF. Executable SHA256:
`cb6944d566452772666208056bc0ce656f532b23faf7dffd9a7b83ffe9e94cde`.
Package receipt: `.local/r52-package-receipt.json`.

Corrections included after the user's three videos:
- Invisible Graphics: genuine three-action footer occupied302px, but the guard
  counted its unused final12px gap (314px) and rejected the whole page. Only the
  unused gap is excluded now. Original font/glyph size/plate preserved. Genuine
  original sprite regression RED1 → GREEN1 across four device families, with
  actual icon bounds and oversized-footer rejection. Logs graphics-footer-52-*.
- Alt+Enter: either Alt, normal/keypad Enter; ignores repeats and consumes held
  Enter through release so it cannot send Start. Main-thread session fullscreen
  toggle changes only fullscreen and synchronizes the active draft/Cancel
  baseline. Explicit Save persists it; no implicit disk write. Four focused
  regressions plus54 related checks passed before the user stopped testing.
- Select Teams: user's60fps recording had25 actual pose/flag changes per second.
  Exact active original owner802A0C48 now authorizes the19 avatar model LOADs.
  Two optional original6x5 flag meshes have vertex interpolation, validated
  topology/UVs, live allocation tags and immutable task scope. Private group IDs
  renew on texture/palette replacement. Training/title/unknown objects remain
  excluded; stale overlay code cannot authorize flags.29 affected checks pass,
  zero skips40.793s; independent review found no concrete defect. Private receipt
  `.local/menu-fluency-r52/receipt.json`. Vertex RGB wind shades retain original
  cadence; no claim that every menu/material is verified at60fps.
- Shadow depth: genuine task proves common83AE8/2-cycle98ACE0/5049FC,
  original PRIM7FFF7FFF. RT64 mapped this to1.0; original18-bit depth is
  3FFF8/3FFFF (below max). Bounded EE adapter translates that exact scalar,
  preserving strict LESS, depth writes, alpha, geometry and guest bytes.
  Original callbacks run once; restored owned stack slot is marked dirty on
  E2/reset, foreign EE and scope exit. No LEQUAL, arbitrary bias or per-triangle
  flush. Four focused tests and actual pinned-header compilation pass; independent
  review found no concrete defect. `.local/pal-shadow-depth-01/receipt.json`.
  The depth mismatch is established; visual flicker causality remains manual.

No new game/GPU/audio execution took place. User-manual priorities are Graphics,
Alt+Enter, Select Teams movement and shadows, then the existing remaining modes.
Type5 → Begin Training black-screen freeze remains unresolved/unreproduced;
Type1 comparison is unknown. Do not infer resolution from the new videos or
repeat the unanswered comparison question. launch.sh appends data/runtime.log.
Existing audio/cadence/save evidence retains its recorded older scope. This is
not completed1.0 acceptance; physical120Hz/4K and real-controller coverage remain
pending. Canonical dev `.local/pal-game-build`; production
`.local/pal-production-build`. r51 receipt and former top note remain private.

---

# Continue ISS2000 locally


## Historical delivery — Linux r50, superseded by r51

The user explicitly said they will run the game tests and requested the newest
folder. Stop further game execution tests. A fresh production-prepared portable
folder is available at portable/ISS2000-Linux-20261015-r50; run launch.sh. It uses
source50 and production17, with input/render evidence fixtures OFF. All46 manifest
entries and the production executable hash were verified; data starts empty and
first launch requests the supported PAL ROM. The previous packages and saves
were not changed. Windows remains frozen.

Included: fitted original-cell glyph ink bounds; fractional POINT sprite viewport
phase correction for the Training button seams; authentic pre-match Controller
with Type1–Type4, adapted Type5 and Free; per-port action mapping through the
genuine normalizer; Start confirms Free; PC Settings device family/vibration
without the rejected raw remap; authentic CI4 body labels for all retained pages.
Private build logs pal-build-50-final.log and pal-production-build-17-final.log
both pass. New full integration19 was started before the user took manual tests;
check its final log rather than guessing a result. The earlier17/39/14 focused
checks and genuine original closure tests pass. Actual50 starts, autoSaveGame
question works and normal shutdown completed. No broad new GPU/manual gameplay
acceptance claim; user is handling the remaining tests.


Canonical repository: `/home/alfredo/Documents/ChatGPT/ISS2000` (actual `/var/home/alfredo/Documents/ChatGPT/ISS2000`). Branch `codex/m0-native-bootstrap`; preserve uncommitted work. Read AGENTS.md. Own attribution exclusively `djultra64 <329694832+djultra64@users.noreply.github.com>`. English docs, Spanish chat; `.local/` private ignored; mirror sources read-only.

## LATEST steering / execution checkpoint — supersedes older active paragraph below

User rejected currentfontactual012-options46 capture: rootexplained originalROWlabelsareprecomposedCI4wordimages; asset15I4headeralphabetNOTsameface. Newexactrowmodule src/runtime/pal_options_row_font.{hpp,cpp} +test RELEASED, authenticPCSettings83pxfromoriginalP/C/Setting/s sourcepixels (noinventedletters). RootWIREDcacheinlineCI4payload(unit128x16)/originalwhite+orangepalettes+customselector15; CMake/testlinkincluded, focusedrowintegration2PASS10.672s. MainrowGPUverificationpendingDEV48. Newbodylabels stillwrongheaderface; broaderglyphresearchfoundnoexactcompletealphabet (asset42+some4Fonly), adaptreasonablelabelswithprovenpixelslater, don'tclaimfinishedfont.

User NEW controlsdecision: REPLACEextensiverawN64Cleft/buttonremapUI withFOOTBALLACTIONS+actualdeviceGLYPHS, simplecompletepresetsperplayer. PreserveoriginalPS1types/numbering; latestuserALLOWS Modern asTYPE4. InitiallychoseonlyPS1thenexplicitlyaddedmodern4, latestwins. PS1exactKCEOgameSLES02550/03149, NOTKCETISSPRO/PS2. OnlysecondaryType1verified https://psxdatacenter.com/games/P/I/SLES-02550.html: DashCross/LobCircle/ShootTriangle/PassSquare/1-2L1/ThroughR1/CurveL2/CursorR2. Actualtypecount/2/3UNVERIFIED; manualarchivesandvideoframesunavailable, don'tinvent. pal_map nowmappingactualPALN64Type1logicalactions→enginebits forpresets, noeditsyet. DoNOTcontinueoldcaptureextensiveremapscreenasfinalUI.

DEV47 compiledPASS (.local/pal-build-47.log), actualUI025/026/029/030 shows palettefixGREENbars+oneORANGEbullet andfooter180nowfullyvisible, butheaderglyphbodyFONTSTILLWRONG. Rootactual47 GDB29138 nowCLOSEDinferior333277NORMALLY viaquit; debugger+privateGamescope1/DISPLAY2stillopen/noactiveGPU. Canreload48inexistingGDBafterbuild. Rootdata private .local/ui-redesign-01/data, fullscreen nowTRUE saved1080/120 fromnativeGraphicsSave028; BUTactualSDLflags0x10002624 lackedfullscreen, foundrealbug! pal_runtime OWNSplatform.cpp+renderer.cpp+newwindow_mode_sync.hpp/test_fullscreen_sync.py fixmainthreadapplication; sourceINPROGRESSnotreleasedyet. ThreeRT64fullscreen callswereonGfxthread, snapshotconfigcanalsoconsumechange. AgentmovesnativeSDLapplicationtoexistingmainplatformupdate, checksactualflags withbounded1sretry/truthfulerrors, removesrenderercalls. Needrelease+tests thenDEV48+actualflagproof. Rootnoteditingthesefiles.

AudiofinalactualDEV46cleanbundle1080/60/defaultPipeWirePASSactiveprefix:947acceptedDMAs18.944s, ZEROrejected;908999stereoframes18.937sbitexactdownstream,302finalframesonlydeliberatenormalshutdownmismatchpreservednotcalledfullmatch. Bothgame→sinkandrecorder←sinksameactualgraphverifiedbeforePCM, SDL2+SDL3mapsbundle. Noqueuefailure/poststartupemptyqueue, maxboundaryjump1504vsold23114. Receipt .local/audio-investigation-01/game-fixed-bundle-60-final/acceptance.json. Allownaudiochildrenreaped,privateSinkmodulesunloadedinclArescorecleanup; nodefaultchanges. Audio17PASS. Newsettings_persistence.hpp/.cpp transaction fixespartialgraphicscommitwheninputsavesecondfails, exactbytesrollbackincludingabsentoriginals/freshotherportmerge,4PASS+native7+others=53focusedPASS. RootCMakeaddedhelper, platformcallbackreleasedbeforecurrentfullscreenedit.

Actualnative47Training naturalHigh0604fromrealmenus, read-onlyliveprobeviaGDBparentinherited/procFD(noYamachange/noRAMwrites): IDLE126actor/ball/stage/phasechanges5.047793s, MOVING1265.045721s;medianphase1.199996948 matchesgenuineAresLOW, all19records stable andlocalposes/matrixbyteschange. All11activeAI originalvariablephase/endpointsgrounded, noforceduniversalscalar. Traces native47-idle/moving.jsonl+receipts andnative47-phase-analysis.json under .local/pal-animation-reference-01. Coreupdatestimingdoc. ActualRSPIDmetadataABIprobev2DONE3fulltasks in47(GDB7/8disabledafter); coreanalyzingnative47-limb-abi-v2.jsonl, noDWARFproductedits. Firstprobev1filterwrongKSEGstripthenfixedresearchonly; nofalseproductfailure. NoactualIDsuccessclaimuntilcoreanalysis.

Storagereleasedstablegenerators: autoStoragev3 exact4/5activeflagsfix (actual47flag4 excludedold5guard),2PASS; storageTextv2 covers43profiles/all57obsoleteEnglishtermoccurrencesindependent12patternaudit,3testsPASS. RootCMakeALREADYbumpedpal-auto-storage-ui-v3 andpal-storage-text-v2. Existing47hadflowv2/textv1, sooriginalinsert15stillneededA; actualSaveGamequestion020/Saving021/Saved022 realwritesPASSprivatecopy. Need48proveautomaticnoscreenwaitwithoutA. Preserveactualfiles32KB/123pages/122pagegamepayload; nofakeinfinitecapacity. Optionalunreachedsharedtemplatecapacitydigits remainresearchnotknownregression; don'tsuppressgenericnumbers. AllvisibleencodedEnglishPak/GameNotes terms43covered, compressedbitmapfullOCRnotclaimed.

NEXT: waitpal_runtimefullscreenfixstable; buildDEV48 (alsoexactCI4PCSettings+storagev3/textv2+transaction); actualhiddenfontcapture+Saveflow/fullscreenSDLflag; implementnewControlsPRESETS onceoriginalactionsemanticsverified, NOrawremapship. CorelimbIDanalysispending. Fullsuiteafterstablesource, productionNEWLinuxcandidatepreserveuserpackages, noWindowsanyactions. Latestfocused06skinfailedonlyoldhardcodedtextureoffsetafternew1024Bpayload; rowintegrationcorrectedoffsetthen2PASS. Fullsuite367source44historical, don'treuseasnewacceptance. AGENTSupdatedlatestType4choice.

## ACTIVE correction pass — current feedback supersedes historical delivery claims

WINDOWS FROZEN until further user notice: no Windows compile/run/SSH/HA/power. Preserve existing portable folders/data. All execution HIDDEN. Latest user also requests all visible Game Notes/Save Notes/Controller Pak/Pack/Rumble Pak/capacity jargon removed throughout English game; use Save Game? Yes/No, Saving, Game Saved. Keep actual saved data and genuine recovery choices. Cable/USB audio output confirmed.

DEV46 compiled with continuous AudioDmaClock and paired High pose/stage fix, authentic original Options alphabet/green skin, native fullscreen, independent vibration and automatic four-port save storage. Existing source44 packages are OLD, not corrected acceptance. Root DEV46 under GDB execsession29138 PAUSED at prompt; private Gamescope1/DISPLAY:2, RAM pointer JSON .local/ui-redesign-01/rdram-location46.json (PID325397), $ram46. Last image010-data-save46.png is original ContinueWithoutSaving confirmation selectedNO. Next resume then LEFT+A to chooseYES -> genuineMain, inspect before navigation. MainOption index8; originalOptionsPCSettings row6. No new green GPU UI image accepted yet. RootUIaudio dummy only. Use privatepulse.py gamefixture, neverOSinput/desktop. OriginalAres owned bycore parked Gamescope0/:1.

Audio confirmed actual source44 producer drops115validDMAs/~37s =2.455s sourcePCM because FIFO progress incorrectly driven by SDL1024-frame pulls. Continuous AI DAC clock fix released src/platform.cpp+runtime/audio_fifo.hpp, meaningful RED6→GREEN8, 17audio testsPASS. FirstDEV46 actual run ZERO rejected DMAs/normalexit but downstream monitor silent due harness wrongSDL libs; receipt explicitly partial. Agentpal_runtime now final40s repeat actual copiedbundle SDL2/SDL3 maps verified, privatePipeWire sink2links failclosed beforePCM, waiting finalresults; root/Arespaused untilrelease. No claim downstream corrected untilreceipt.

Core pairedfix tools.prepare_pal_native_pace.py suppresses second31E74 at10CC under same genuineHigh0604 decision as stage10C4, preservesfirstE54 plus allcamera/input/VI/audio. CPU35-modelclosure5PASS+hookPASS. Ares148 genuine originalLOW126actor/ball/phaseupdates/~5.048s ×1.2≈30animationunits/s, originalHIGH252/~5.047s. SameROM noRAMpokes isolateddata; notphysicalN64truth. Need new native runtime phase and19stable limb transform metadata proof; corepreparing sampler.

Authenticskin backend released src/runtime/pal_options_skin.{hpp,cpp}, testoriginalCPUclosure1PASS: exact SelectOption asset15 italic alphabet resident8022CE40, originalgreenbar/selection/bullet/background, no blackscreen. Root nativeCMake/viewintegration compiled46. Need actual image size/tint/layout review, fullscreen runtime, Remap pages. Rootalsofixed ButtonMappingRestoreDefaults resettingindependentvibrationOff: regression RED2 beforefix thenGREEN. Focused04 ninePASS0skip14.683s coversactualoriginalfont, controls, v2storage, helperexports14.

Storage automatic configure_paks(dir,true) preserves oldfile/images, fourport persistence testPASS, no manualuserPakchoices; vibration persisted perport. pal_map RELEASED automatic-storage v2 tool/test: exact original1CC8 initializer plus1D84 updater true original probe, activeowner5+state15 guard, realerror10/retry3/close tests, nine hashguarded wording substitutions. Root WIRED nativeexact1D84hook +CMakepal-auto-storage-ui-v2 +helperexport14, notbuilt47yet. pal_map now owns NEWtools/prepare_pal_storage_text.py +test for remaining three exactEnglish banks (startup/Data,save/career,genericmanagement), original48660objectsource adapter, no blanketRAMscan. Need root wireadapter beforeencodedprompt; capacitydynamicnumberproducer undertrace. Actual32KBstore123pages, oneISSfile122pages contains all persistentgame+twoCareerrecords; progressiondoesnotgrowfile, donotfakeinfiniteblocks.

Root last focused04 PASS9; focused03 audio/native/lifetime/exports26PASS; settings/keyboard23PASS; preferences/autopaks/menu10PASS. Fullsuite367PASS source44 is HISTORICAL, need newalltests afterstableedits. DEV47 pendingclose46normal via GDBcall ultramodern::quit +continue, then cmakebuild .local/pal-game-build (mustwaitaudioquietend). No newproductioncandidate yet. Preserve all legitimateuncommittedwork and attributiondjultra64. Team current: pal_runtime audio finalrepeat; interpolation_core reference/nativeverification; pal_map allEnglishsavewording. Root native/CMake/settings/UI integration.

## Final source44 portable delivery — authoritative

Both separate production folders are prepared: `portable/ISS2000-1.0.0-Linux` and `portable/ISS2000-1.0.0-Windows`. The existing user-tested `portable/ISS2000-1.0-Linux` and RC2 remain untouched. RC2 predates the keyboard-arrow fix; direct the user to the new 1.0.0 folders. Both final folders contain no ROM, imported assets, configuration or private saves; each keeps40 authentic notices. All46 Linux/48 Windows manifest entries independently match.

Latest full integration17: **367PASS, zero skips,207.359s**, plus independent source44 review without blockers. Dev44/prod15 compilePASS. Linux executableSHA `a63492f4380d20ba59653bebd4f0c1d310dcdb4462545f3d7a70edd8ba747c76`; WindowsGUIexeSHA `4b8efcc6ce8c50c90dd0c761c2033dbb87a0dbdda67e62e185a896d87ccecada`. Fixtures/evidenceOFF; direct native execution; ownidentitydjultra64. No commit/publish performed.

Latest user request completed: original Low/High Resolution selector retired; row6 is native PC Settings. Genuine08C30 initialization defaults desired High from actual installed8MiB; language is preserved. PC output720..2160 and presentation are separate native Graphics options. F7/host settings UI removed. Physical keyboard Left/Right changes selected values; original-engine Remap opens via Controllers. Save writes settings; no finalproduction15post-Saverestartclaim.

Linux production15 actual copied-folder/pathwithspaces run imports PALROM, reaches title/main/Options, nativeGraphics399 selects1080/120 withkeyboard; Save400 writesgraphics.json. Remap401opens and cancellation safely returns throughparenttoTraining402. NaturalHighTraining404/405 working1/desired1/640x544/Z80700000 measures125stage+actor+ballupdates in5.005637713s, matchingLow; no2xacceleration. Receipt `.local/portable-copy-acceptance-04/acceptance-production15.json`. Inferior303484exitednormally viaEscape, GDB27417quit/compositorclosed; Escape key-up BadWindow is expected private-harness race afterwindowdestroy, notgamefault.

High interpolation actualdev43 evidence remains240GPUreadbacks/50distinctfractionalworkloadgroups, originalsimulation25Hz/virtualpresentation120. No physical120Hz/4Kclaim. Originalmode/manualcontroller limits explicitly recorded in docs/releases/1.0-acceptance.md; user assumesremainingeditor/training/leaguechecks. Windows final actual hidden first-ROMprompt+import/title passes, captured/reviewed final-rom-first.png andfinal-hidden-title.png. FreshfirstROM4900 andimport13892close normallyexit0. All12WindowsCOFFentriespass;49files/40noticesclean. Receipt `.local/windows-execution-02/acceptance.json`;283rescuedfilesverified `.local/windows-final-evidence-02`. No Windowsgameplay/fullmodesclaim. ZeroownedWindowsprocesses/tasks, all33transportchildrenreaped.

MAQUINITA: **leftON deliberately due uncertain other console use**, userasyncclarification unanswered. Helper/SonoffON, automationON/queued/current0; originalownedpowercontextunchanged. Reservation `/tmp/codex-maquinita-windows-recomps.lock`, id `ce30c29b-834d-44f5-b7f8-b6940c616582`, phasework_complete_power_preserved_pending_user_use_clarification. Allownjobsdone/artifactsrescued. NoOFFrequest. Keepreservationforrecovery; doNOTinferotheruseclearedbyelapsedtime. Ifuserclarifiesfree/off, resume sameowner, rereadskill+HAandperformoneorderlyhelperOFFwithmonitoring; neverdirectSonoff/shutdown. Projectsnapshot `.local/windows-final-power-decision.json`.

## Historical checkpoints — superseded by the final source44 record above

### Source44 final-package verification in progress — supersedes historical notes

Latest dev44 and clean production15 builds PASS. Production15 SHA256 `a63492f4380d20ba59653bebd4f0c1d310dcdb4462545f3d7a70edd8ba747c76`; fixtures/evidence OFF. Source44 adds standard Left/Right aliases for native settings values and its original-engine footer; a real package test caught the previous missing aliases. New regression failed before and passes after the fix;13 focused tests PASS. Full integration17 is running; previous stable16 passed366 tests/zero skips.

Genuine High is the original08C30 desired-enable initializer, NOT Language. See the correct mapping below; older contradictory High preference notes are historical disproved hypotheses. Runtime43 High640x544 Training125 updates/5.00412s matches Low, and240 real GPU readbacks demonstrate50 distinct interpolated workload groups. Original Resolution selector is replaced by native PC Settings; output resolution remains selectable there.

The user's existing `portable/ISS2000-1.0-Linux` remains untouched. RC2 is preserved but contains the keyboard alias issue; final folders target `portable/ISS2000-1.0.0-Linux` and `portable/ISS2000-1.0.0-Windows`. Root private copy04 was closed normally, backed up, and its executable alone replaced with production15; data preserved. Root GDB27417 now runs this copied production15 under private Gamescope0/:1; title-ready breakpoint8 is pending. Current captures393+, use key_capture.py with private keyboard (production fixtures disabled). No user desktop inputs.

Windows pal_runtime reports final source44 GUI-subsystem2 build/package PASS, executable4b8efcc6ce8c50c90dd0c761c2033dbb87a0dbdda67e62e185a896d87ccecada,49files/40notices, clean final folder. Hidden final import execution acceptance remains active; no release claim yet. Maquinita user-use/power-off async question remains unanswered, so preserve power under uncertainty. No delegated HA/power actions.


### RELEASE BLOCKED BY NEW USER FEEDBACK — highest priority

ACTUAL VERIFIED latest: dev43+production14 compiledPASS. CORRECTfixedHighgenerator08C30defaultdesired=installed memory flag, nativehook08C30/CMakev3. Genuine43startupinstalled1/desired1/currenttitle0; naturalTrainingworkingHigh1/640x544/packed20010101;125stage+actor+ballupdates5.004120655s=24.979Hz vsold38High252/5.003645(~50Hz). ActualGPU378cleanHighcenteredplates/borders; GPU3792secplayerRight yields240realROIreadbacks/50matchedworkloads withdistinctfractionalimages,target120virtual. Immutable receipt .local/high43-acceptance-01/receipt.json +gpu-readbacks.jsonl,exe32cc414e..., nophysical120claim. Fullsuite16STABLE **366PASS0skip218.486s**, independentreview8PASS0skip/noimportantbug, package46manifesthashesverified. Prodbuild14SHA1dc34cfa3a395ca3714b2a8cd0830231ed3f7aab2b3e89494fa893927b460514,fixture/evidenceOFF,DIRECT. Newuseraccessible freshcandidate `portable/ISS2000-1.0-Linux-RC2`, originaluserportable/ISS2000-1.0-LinuxUNTOUCHED.

ROOTLIVE now GDB27417 **PRODUCTION COPY** `.local/portable-copy-acceptance-04/ISS2000 Portable/iss2000` (pathwithspaces), hiddenGamescope0/:1; currentwindowdiscoverbyexacttitle (usually4194351, notold4194319), inputfixtureOFFso use NEW `.local/hidden-test-01/key_capture.py IMAGE [z/x/Return/Up/Down/Left/Right:hold:release]` privatekeyboardonly;capture_only.py fordialogsno focus. Copied47files/emptydata; actualfirstROMprompt380PASS. OriginalSDLmessageboxusedzenityprivatechild20971524, acceptedReturnthenGDBbreakNFD_Init BEFOREfilepicker, killedownpreimportprocesstoavoidportalappearinghostdesktop. FreshsameproductioncopyrunCLIownROMimport, defaultportabledatarelativelocalcorrect; actualtitle381 +keyboardReturn382/DataChangeCreateCompetitionNote383/create384 thenmain385. Currentrootbatch386MAYWRONGLYenteredPreseason becauseinitialextraZbefore8Down; inspectcapture386beforeinputs! Source44notneedednochanges. CurrentGDBallbreaksDISABLED7; $ram20CURRENTproductionpointer set. NeedactualproductionPCSettingsSave/newnativeRemapchild+TrainingHighcadence/keyframes thennormalexit. Prodimportlog .local/portable-copy-acceptance-04/import-launch.log, first-launch.log. RootGame43developmentclosednormally. Nextcapture387+.

Windows agentpal_runtimeACTIVE finalsource43 Windowsproduction02 **180targets/all12COFF/DLLclosurePASS**, noC++fixneeded. Deltas143files1.24MBmanifest9bb6787a... frozen38backupsretainedremote. Privateexecution02 logs/ledger. Agentpreparingfinalportable/hiddenGPUacceptance; topScheduledTaskharnessconsoleflashcaughtbeforelaunch, nowGUI-subsystem2no-windowbroker compiled toavoidanyvisibleconsole. No poweractionsdelegated. RootreservationOWNEDONphasefinal_windows_build43_delegated..., samece30c29b...helpercontext. UserASYNCpowerquestionstillpending(otherconsoleappsuseuncertain); afterownjobsrescuedmustpreserveONuntilreplyresolves. All source/C++stable, onlyEnglishdocs updatedcurrent366proof; tools.package_portable.pyaddedREADME Option→PCSettings/HighvsPCres guide lines, agentdeltaINCLUDES.


CRITICAL LATEST MAPPING FIX (supersedesALL Highpref0/1 notesbelow): 8001C9A0/80133676/top2bits are LANGUAGE English0/German1, NOTResolution. Earlieragent isolatedpacking/resource tests mislabeledthosepaths; actual40AND42TrainingworkingLow0 caughtthis. TrueResolution commit802A63DC usescursor802B10F0 andwritesDESIRED-ENABLE8013B42B (High1/Low0); separateworking13B42A (High1). Bothold38snapshotspref801336760/topbits0butLowpacked20010000 vsHighpacked20010101. RootfoundgenuineBOOTdefault80008C30: osGetMemSize→frame+11installed1 iff8MiB, current+12cleared0, desired+13cleared0at8C90 thenoriginal08CBCbufferinit. Pal_mapNOWreplaceswrongfixedHighgeneratorwithSHA-pinned08C30derivativeONLY8C90defaultdesired=installed, preservingoriginalworkingrequests/buffers/language/CareerTEMPdisable13B42B0andrestore. Nativehook/CMakeMUSTswitchfrom1C9A0to08C30+newsource/v3outputonceagentreleased. DoNOTshipoldfixedHigh1or0languagepatch! Currentdev42stillwronglanguage0+paceHUD; actual42TrainingLOW125updates/5.00349s, NOTHighpostfixproof. TrueHigh25HzrealtimeSTILLPENDING. RootGDB27417PAUSEDTraining42afterprobe42.gdb, fixtureEMPTY,$ram20current. Corecoordinatesbootdefaultproof; palmapownsnewHighgenerator+realHighglyphreleasedsource; palruntimeownsedgeUV-onlyHighspritederivative (cropalternativeREJECTEDgenuinefinalcolumn). No userportablechanged.


LATEST CORRECTION: originalHigh preference0, Low1 (different fromworkingvideoHigh1). AgentearlierfixedHigh=1waswrong; actual40initializerpref1/packed40010000 ledLowTrainingworking0. ThiswasdiscoveredbyactualGPU/RAM, NEVERdelivereduserportable. Generatornowcorrect0, immutableCMakefolderpal-fixed-high-v2,2packingtestsPASS+originalselectorconsumerregressionpendingagent. Dev42PASS containscorrectHigh0+nativePCSettings+pacefix+HighHUD, noHighspritepaddingfix/glpyhHighyet. RootGDB27417live42boot23.logunderGamescope0/:1, titlebreak3pending/awaitoutput, fixtureEMPTY,$ram20OLDpointermustresetafternewbreak. Prior40exitednormally; dev40actualPCSettingsrow6replacedanddrawn369/370/371, settingssave16x9/1080p/120persisted373+graphics.json+actualGPU1920x1117log. Old40training374isLOW, notHighacceptance. Rootneedsactual42Highwalltime/completedBB8dump. Agentpal_mapownsHighprompts+correctHighoriginalsemanticsregression, pal_runtimeownsnewHighspritepaddingderivativetool/tests/docs (COPYmode0 redundantright/bottomstripovershoot); rootnative/CMakeowned. Rootdeletedobsoletehostsettings_dialog.cpp/.hpp; noF7/F6routeproduct. NativeHighfocused17PASS0skip28.504s,correctedHigh+pacecore7PASS0skip2.027s. Full356beforelatestpaceHUD. WindowsownedpowerstillONawaitinguserasyncansweraboutotheruse, allartifactsrescuedzerojobs.


AUTHORITATIVE later checkpoint: ActualHigh38 confirmed252steps/5.003645s versusLow126/5.0050165s (sameTraining0604), rootreportedconfirmed2x. Corefixedboundedduplicate stagecall800010C4 onlyHighscene0604 bothentry/current, preservesallinput/audio/render/otherstages; tools.prepare_pal_native_pace/tests/docs released4PASS androotINTEGRATEDCMake+exactregistryhook,butnotyetbuilt/realtimeverified. Dev40PASS fixedHigh(nativeinitializeractualtitleRAMpreference1/packed40010000 verified), nativePCSettings+ownerrouterfix. Fullsuite14 356PASS0skip195.941s precedespace+HighHUDpending. Rootold34298SESSIONCLOSED,GDB/game/compositorclosed(noactualboot21acceptance); newliveGDB27417 underfreshGamescope0/:1 run22.py game40 boot22.log/render22.jsonl. Break1titleDISABLED; $ram20set; fixtureEMPTY; naturalmain→Optionsroutecapture369pending. Actual Highcompletedframe stillrequestedpal_map (root40canTrainingnext), agentownsHUDmodule/testsHighsupport. Nextcapture370+.

WindowscompatibilityBUILD/LINK/DLLclosurePASS exeSHAa35e0ff210a7055427da9ccc1cb9ed7d0869b77fe5187131600bf067ad187822, artifacts+receiptsALLrescued .local/windows-compatibility-artifacts-01, agentpal_runtimeDONEzeroownprocess, noproductgame/noWindowsfinalpackage. Fivehelpergenerators correctedWIN32externinlineCOFFdrop viaTUstrongnoinline (all10exportsactualWindowsnegativebefore/positiveafter), rootmovedimmutabledevhelperdirsunderpre-coff-export-fix-39. NOMINMAX/DXCinclude/objidl fixesreleased. PowerstillOWNEDONsamecontext/lock ce30c29b..., HAautomationcurrent0, helper/SonoffON. Session1consoleActive/unlockedWTSLastInputTime0INCONCLUSIVE, BigBox/Steam/ChatGPT/codex/parsecdcouldautostartorotheruse. RootASKEDUSERASYNCwhetherusingmaquinita now (yesleaveon/nooff), skillrequirespreserveunderuncertainty; DO NOTpoweroffuntilreplyresolves. AllWindowsjobscomplete, awaitingreplywhileLinuxcontinues.


Latest root checkpoint: dev39 compiles PASS with PC Settings originalrow6 integration + fixedHigh initializer. Old live38 still underGDB34298 used tobaselineTraining. Actualnatural FreeTraining low mode4/stage6/sub4/high0:126stage+actor+ballsteps/5.0050165s (~25.17Hz), receipt `.local/training-timing-01/samples.jsonl`, untouched8MiBsnapshotfree-training-low.rdram andactualGPU352. Thus unpacedgfx speed hypothesis NOT confirmed forLow. Rootcurrently originalTrainingpauseQuitmenu354, not forcedRAM. FreshStartworkedafterconditioncorrected BE944==1 (NOTBE94C==1), expiredBE95C; originalDataChangeAthenmain→7DownTraining. FixtureEMPTY. StillneedHighcomparison/native39Optionsactualproof. New GameSettingsMenu agentreleased5PASS. NativeSettingsfocused17 has2fixturecompilefailuresinNativePromptLifetime (newOptionsgate dependencies), pal_mapownsfix+integrationtests. Router now frame.owner_token + previousowner/portrearm, pal_mapregressionpending. Windowscompatibility allC++compilednowhelperexterninlineCOFFexportsdrop; pal_runtimeproving/fixingboundedgeneratorsWIN32 (sky,maxDetail,rumble,expansion,High), nofinalpackage. Canonicaluserportablefolder untouched.


User is actively testing `portable/ISS2000-1.0-Linux`; PRESERVE that directory/data/executable while running, do not silently replace. He reports Training players/ball/animations MUCH TOO FAST (explicitanswer, not justclock). He previously assumedremainingmanualtraining/editor/leagueacceptance, but this reportedbugauthorizesfocusedhiddenrepro/fix. No1.0claim; existingfolderisCANDIDATE. Agents read-only timingfacts below, actualwall-timeprobe STILLNEEDED. Renderlogoriginal_hz25 is PRESENTATIONINFERENCE, NOT simulationproof. Rootmust measureoriginalcounters.

User ALSO explicitly rejects F7 modalsettings: ALL our options within ORIGINAL GAME Options menu usingitsownengine, nohostoverlays/popups/separateprograms. Need replacehostF7settings UIwith nativeGraphics(allres720..4K/aspect/refresh), controllers/family/remap/Paks/rumble. ExistingnativeRemap originalfonthelper canbereused. New user alsoexplicitly requires originalResolution ALWAYS HIGH and removesoriginalselector. Agentpal_map owns originalOptionsrow6(nativeResolution)→newPCSettingssemanticentryhelper/proofs +genuineHighsetter/startupflow. Current8rowOptions menu firstGoBack/GameSetting/CreatePlayer/DeleteRegisteredPlayer/Data/Transfer/Resolution/Language. Avoidappend9: descriptioncallback8wouldstackOOB. Needboundedslot6reuse, preserve8navrows.

OriginalHighflow: commit802A69E4(choice802B1100=1) sets packedword8013B428 bits3FFFFFFF|40000000, desired80133676; original8001BF18serializes. Original80001D44(1)requests8006CE71/countdown8006CE70; ordinary02A10calls80001E40 installs640x544/Z80700000/color80500000,805AA000,80654000 throughgenuine80002D08+VI. NEVER rawpoke13B42A and skipallocations. HIGHframe+12==1 enables secondstageupdate800010C4 (firstD34unconditional). Existingpromptfallback/HUD/backgroundguards mostlyLOW320x240ONLY: mustreviewadaptation ifforcingguestHigh; do notweakenguardsblindly or pretendHighfieldwhileactualLow. Agentcorewarned thisinteraction.

Timingfacts: bothdev+prod same patchedPALruntime50VI/s/get_speed_multiplier=1; portableSHAmatchesprod, noactiveMods, currentusergraphicsOriginalrefresh/Originalresolution. Originalmain80000B5C acceptsVI1 ANDGfxcomplete2→80002A10; driveradmitsfreearena800006A4 and noexplicitwallwait. Upstreamevents.cppgfx_thread_func sendsSPimmediately, send_dl,DPimmediately (CPUlistparsecompletionnotGPUcompletion); originaltaskcomplete8001E170 clearsGfxarena via8001DA94 then sendsmessage2. CouldallowunpacednativeCPUupdates, NOTYETmeasuredcause. Trainingmode4 bypasses801DC14C/NtscMatchClock, so itdoesntexplainfastmotion. Measuresteady halfcounter8013B442 (in80053DF8unpaused) plusactor/ballwords802D797C/7980 (802B7298increment); main/sub8013B446/44C, High13B42A andfade6CE70. Setuphelper8022469C has3actorcalls(originalsettling), excludetransitions. Training mainmenuindex7→mode4→commonpage6→803B2F50→803B2F74→80010080(callback802A8268, data803F18C8), originaloverlay46FC80→8029EEA0. NeedenterTrainingnaturalinputs.

RootGDB34298 currentlypausedat func80047598_resident breakpoint2 afterignore100 (querysession); `$ram20` pointerset. Break1introdisabled. RoothiddenonlyGamescope0/:1/window4194319, build38; new appfixture `.local/title-acceptance-01/buttons.txt` CURRENTLYcontainsSTARTHELD frominputdiagnostic—RELEASEITbeforecontinueforfreshbuttonedge. OriginaltitleStartisEDGE and47598countdown800BE95C mustreach<=0; previouspulsesduringcountdown/attractdemo ignored. Lastreadtitlecounter60,hostportsP1buttons1000/keyboardfalse/connectedtrue,originalpressedframe+40zero,sohostfixtureworksbutoriginalTitleedgewait. Roothasbeen cyclingintro/attractwithoutenteringmenu38; do notfabricateacceptance. Earlier36menustrue andHUD33actualpassed. SDL_GetWindowFlags268445220=10002624 showsinputfocus; helpernowexplicitlyfocusprivateonlybeforepulses. Lastcapture344attractSpainNigeria(originalHUDnotrepositionedbyguard). Next345+.

Windows ownedbuild compatibilityONLY continues old38source, NOFINALPACKAGE/acceptance until2newblockersfixed. Agentpal_runtime SSHbuild running originalCPUgame104/173 afterupstreamruntime103/103 +RT64renderer488/488PASS(DXIL/SPIRV+validator). Remote\.local/windows-production-01/build.log, local\.local/windows-execution-01/11-build-retry.log; ledgerJSONL tracksPIDs. Rootreservationce30c29b...stillOWNEDON, mustcompleteorcleanuporderly! PortabletoolsinstalledPASS23GBfree. InitialprocessRestricted, explicitlyauthorizedCHILDPROCESSRemoteSigned for ownreviewedlocalbuild/hiddenworker/scripts (notBypass/IEX/noUserMachineGPOchange), parentstillRestrictedverified. Pythonembedbootstrapcorrectedprivate._pthabsoluteRoot +quote-freeinlineassert; privatebuildscripttransferrowreceiptsupdated(agent), no productsourcechanges. HiddenDesktop C#compiledPASS; hiddenGPUacceptancenotattempted. SharedC++sourcechangesmustcoordinateWinagentrebuildaftercurrentcompatibilityjob. No independenthostwindows.

### Latest final-delivery stage

Windows SSH ONLINE/identitydesktop-svgguha\ryarcade confirmed byHAandlocalchannel. RTX2060. Freshworkspace `C:\ISS2000-20261015-1.0`, Cdrive30GBfreebeforetransfer. Sourcearchive `.local/windows-preparation-01/windows-inputs.tar` SHA17d74e5708062707accef3059bad0ed45ef6b4b31ab52915806dc1af590adbbd verified/extractedremote;4PowerShellscriptsparsePASS. Completeofficial portabletool prep (LLVM20.1.8/CMake3.31.10/Ninja1.13.1/Pythonembed3.13.7,allofficialSHA) copiedremote `.local/windows-toolchain-prep-01` (~997MB). Agentpal_runtime NOWownsSSHtoolsinstall/Build-Windows/windows-production-01/packaging/hiddenacceptance, NOT HA/power; coordinate exactjobIDs/beforestop. Rootmaintainsownedpowercleanup. Noglobalinstall/policybypass/visiblegamewindows. RoottoolprepREADMEexample removedExecutionPolicyBypass aftertransfermanifest(nonproductdoconly).

Linuxdev38PASS +cleanproduction13PASS, project_version1.0metadata nowset, acceptance stillpendingbothplatform finalchecks. FINALcandidateportablefolder `portable/ISS2000-1.0-Linux` generated47files/40notices/emptydata/noROM, rootcopied to `.local/portable-copy-acceptance-03/ISS2000 Portable` forfreshROMfirsthiddenacceptance. Fullsuite13 **340PASS0skip214.631s** coverslatestintro/palette/keyboard/activeport/HUDsource(beforeversiononlymetadata). Independentreview17PASS0skip54.49s,noP0/P1/P2finding. Actualdev38KONAMI335/KCEO336whiteintro extendswideproportionallogo preserved; one originalpixel/last2-3compositorpixels rightedgequantization visiblebutlargeblackbarsgone. Rootcaptured with exactnativewrapperbreakalpha255,noRAMinjection. RootcurrentGDB34298 game38/privateGamescope0DISPLAY1/boot20.log/render20.jsonl, break1disabled, originalmenusrouteinprogressforactualblacktintproof. PreviousGDB54244/own36closed. Nextcapture339+.

### Windows power reservation ACTIVE — preserve across compaction

User explicitly authorized maquinita skill again. Skill read and announced. Atomic lock `/tmp/codex-maquinita-windows-recomps.lock/owner.json`, reservation **ce30c29b-834d-44f5-b7f8-b6940c616582**, chat01a13f78-fcfa-7cd0-ac62-2722606c24f4/projectISS2000. Initial helperOFF/SonoffOFF/automationON queued/current0/power0W. Actual automation config hash988beeefd45358ef inspected: orderlySSH shutdown, networkoffline+fresh<50W beforecut, noforce. Authorised local default id_ed25519 +knownhost entry present; directSSHbeforepower No route tohost. HA networkdiagnostic returnedreturncode0/stdoutoffline. Own SINGLE helperturn_on called2026-10-15T21:09:03UTC and verified own transition context01M50PB9JKK4HE8KWPNJ36CET8/user15cf...; lock now encendido_por_esta_tareaTRUE/waiting_windows_ssh. NEVERcycle, forceplug/WoL/shutdown or losecleanup. SSH192.168.68.111userryarcade; use `ssh -F /var/home/alfredo/.ssh/config -o BatchMode=yes -o ConnectTimeout=8 -l ryarcade192...`. Read lockphase, HA helper/Sonoff/automationstate before any recovery. Last HA SSHreadiness query inprogress/resultinspect. AllWindowsartifacts/captures must returncanonical BEFORE ownedhelperOFF cleanup and confirmnetworkOFF/powerfresh/automationidle. HA guide read with matchingdevicecontrol+automationactions references; guide's BestPracticeKey parameter is UNSUPPORTED by actualha_call_service(validationerrornoaction), validtool calls omitthisargument and work normally. Do not pass it underdata.

User delegated remaining editing/training/league manualtests to himself: no longerreleaseblockers. Agentpal_runtime stopped, closed own game239665/249041 and GDB55201/compositor231488cleanly, preservingCareer acceptance. Actualeditor4-4-2→4-3-3 +Saved observed beforedelegation, privateeditorcopyPak2b03285...; NOreloadclaimed. Agent nowowns ONLY privateWindowshiddenacceptanceprepscripts. NoWindowsexecutiononuserdesktopallowed.

Dev37PASS latestsource includesactiveinputport, blacktint4 regionhints, keyboardLSalias,8backgroundfamilies+neworiginalCI8introcavaspostadapter (nativeexact801ADD44guard). Helperoriginalparent→actualnativewrapper→originalleaf tested7focusedPASS0skip27s, preservesCPUcontext/privatecursor/4:3. Dev37freshvisualintro+blacktextpending. Fullsuite12 **338PASS0skip222.495s** beforelatestintro/palette/keyboardline; focusednewfont5PASS0skip13s. CleanLinuxproduction12building now fixture/evidenceOFF. Rootgame36 GDB54244 Gamescope0/:1 currentlypausedsetplay333, actualfieldStartMenu332 and actualnative8px LT/RB +logicalPassrows333PASS images; latestHUD329PASS. RootcaptureNext334+.

### Latest HUD refinement and source36

The user now requests player-name panels centered in each radar-to-screen-edge space. Root updated PalHud placements using quarter origins0x100/0x300 and offsets-372/-904 in RDP quarter-pixels, vertical-28 unchanged. Original radar spans120..200, complete panel envelopes26..120 /199..293. Tests now execute BOTH actual upstream RDP movedFromOrigin and convertViewportRect; the initial incomplete viewport-only test missed the native80/240 origin addition, which actual agent35 field047 exposed. The corrected regression failed before the final offsets and now passes allsix profile scales. Root10 focused testsPASS0skip; build36PASS. Actual36 visual HUD acceptance PASS: captures328(KICKOFF)/329(moving field) show panels centered, realreceipt.local/pal-hud-center-acceptance-01/receipt.json. Capture328embeddedchat. Rootstilltestingcurrent36originalmatch, root GDB54244, own Gamescope0/DISPLAY1, run19.py/boot19.log/render19.jsonl; capturesnext325+. Old49336/10552closed deliberately. Every restart must explicitly focus only privatewindow4194319; xprop focus alone does not guarantee SDL keyboard focus. All app-only input remains hidden.

Source36 includes8 exact background families (pal_map RELEASED allfiles) plus PalScreenFillScope; actual whiteKONAMI318 still has blacksidebars despite fill scope, so need direct-emitter boundedside extension investigation (see pal_map inventory). Root fresh36capture322 region row8px no longer collidesEUROPE B/A, but white text abovebrightbackdrop has poor contrast; glyphagent investigating existing originalfont palette/tint. Field Start/pause8px helpers integrated, selectedpauseport propagatesnative/allrequests; rootfont8bearing bounds corrected(y+9<=240),12pxbearingunchanged. Glyphagent now owns activeinputport tracker in platform.cpp/.hpp and optional activeport resolver for exactglobalfieldStart; rootnative must pass thirdactiveportargument after release and update extracted lifetimefixture stubs. No compile while sourcesowned; coordinate handoff. Devfixture now explicit dpad_* in test_controller.cpp,13focusedPASS and testingOFFinert. pal_runtime testing modes extra35 on Gamescope1/:2, actualCareer acceptance retained separately. Query agent before process changes.

### New accepted evidence (supersedes pending statements below)

- **Real GPU interpolation PASS**: `.local/pal-interpolation-gpu-01/receipt.json` and immutable capture.jsonl:214 actual Vulkan ROI readbacks,42 matched workloads with different pixel hashes at different weights; one workload has five distinct images at0.125/0.333333/0.541667/0.75/0.958333. Actual model/camera tagging restored (591/6 per representative636-call task). Original25Hz simulation, virtual120Hz Gamescope output; physical120Hz remains unproven. Capture gate removed after1.8s of original player movement while agent's other game was paused.
- **Career create/progress/save/restart/reload/furtherweek PASS**: `.local/career-acceptance-02/acceptance.json`, exact pinned build32 SHA22748b269c502a41b3773540e83369b9473fd75fa00d82be35b94922e65484ab. Agent's isolated A/Sweeper File1: September1→RestSeptember2→genuineSaved/PakSHAda7a9a036e8d067a113ed9219660b44c657f7680101ee87c1edcd101d810bb81→cleanexit→freshsamebinary→occupiedsameFile1/date→furtherRestSeptember3. Actualcaptures098/105/108 independently inspected byroot. MainrootunsavedCEdata untouched. Agent now tests Editor/Training/League independently from another copy; query actual liveagent state before process changes.
- **All six actual resolution profiles PASS**: `.local/pal-resolution-execution-01/receipt.json`. Real paused field32, actual F7 native settings saved each preset720/900/1080/1440/1800/2160; actualGPUtarget1280x745/1600x931/1920x1117/2560x1490/3200x1862/3840x2234 (PALVI crop gives exact visible720..2160). Savedsettings16:9/120 retained. Rootstillpaused via ORIGINAL game menu on4K profile; not GDBpaused. Compositor output1280x720, so snapshots downsample actualhigher target; no physical4Kmonitor claim. Root owns privateDisplay:1 and gamescope-0; privatehostdialogclick helpers only act inside that display. Do NOT send inputs on desktop:0.
- Build33 PASS now contains root exactoriginal019FC full-frame color-clear scoped widen hook; agent's helper handles originalwhiteintro canvases. Needs fresh actual33+whiteintro verification. Source since33 includes agent team-region physicalfont fallback guarded ONLY proven singleplayer mode8012DE56==1; sixargAPI unchanged. Promptagent currently implements actual Start/Z/R fieldhints (completed genuine dumps field16-tooltip-completed.rdram and field16-pause-controls-completed.rdram). Do not compile until its release notice. No continuation pointer API planned forStart: replaceonlyStartobject with physical label, preserve separateoriginalGameControls actionobject. RegionCPUadapteractualGPUacceptance pending.
- Agentrelease_review performing independent read-only cross-feature source review. Root native/CMake owned; pal_map backgroundhelper releasedstable with sixfamilies+PalScreenFillScope. Source fullsuite repeat, finalproduction/package refresh and actual finalWindows remain.


Latest user instructions: continue autonomously to native PAL English1.0, use agents as needed, extend ALL backgrounds to16:9, preserve original simulation/NTSC match pace, native-engine controller glyphs/remap, maximum detail, remove informational EnhancedExpansionPak/Rumble notices. **All remaining execution tests must now use HIDDEN windows** (explicit latest user instruction, supersedes old visible mandates). Do not open/activate game windows on desktop:0. Windows builds/runs remain final-stage only.

HEAD8d67354 on codex/m0-native-bootstrap; many uncommitted reviewed fixes must be preserved. Own identity exclusively djultra64. Canonical actual folder /var/home/alfredo/Documents/ChatGPT/ISS2000; all private ROM/generated sources/assets/saves/captures remain ignored under.local. Latest full suite332PASS, zero skips134.118s (.local/tests-pal-integration-11.log); this preceded the corrected whole-frame title hook and additional fifth/sixth background profiles. Repeat after pending edits settle. Development32 and production11 compile successfully; source has additional background sixth/cache cases since those builds.

Root hidden GPU execution: Gamescope --backend headless -W1280 -H720 -w1280 -h720 -r120, private Xwayland DISPLAY=:1, control gamescope-0. GDB PTY49336, original boot16 on binary32, isolated .local/title-acceptance-01/data and buttons.txt. Compositor/run wrapper/logs .local/hidden-test-01. Real renderer is RADV PHOENIX; original25Hz simulation with virtual120Hz target has4/5 planned frames per workload. This is a virtual output, NOT physical120Hz proof. Actual GPU intermediate distinct-pixel proof still pending on moving field. Capture gate .local/hidden-test-01/capture.flag ABSENT; enable only while moving field. GPU ROI256 and log render16.jsonl configured; gate avoids exhausting240-readback limit in menus. Genuine compositor captures: GAMESCOPE_WAYLAND_DISPLAY=gamescope-0 gamescopectl screenshot /ABS.png (asynchronous file write). X/Pillow/ImageMagick capture returns black/BadMatch because Vulkan backing is not Xroot pixels. Never substitute that for actualgame evidence. Private app-only fixture uses ISS2000_TEST_CONTROLLER=ABS/buttons.txt tokens a,b,start,up,down,left,right; empty releases. SDL input requires own private window focus; gamescope normally focuses it, xdotool windowfocus ONLY on private display is allowed. Do NOT send desktop:0 key events or bypass KDE permissions. No product rendering/input behavior was changed for hidden tests. Xvfb lacks DRI3 and cannot present RT64; do not retry blindly. Private headless Gamescope works with actual GPU.

Actual title260 confirms corrected original-engine PRESS Return and16:9 preserved-center background. New prompt_title_model module validates exact normalized original228 model (all60 relocations),20actual DE calls, originalfont0D/palette/frame/root ownership. Root initially wrapped8002B618 (never executed by real title): superseded. Correct implementation adapt_physical_title_model runs AFTER original80000BB8 completeframe and BEFORE originaltasksubmission; scans only currentarena.begin..cursor. Draw original48660 first, then suppress exactly20 original prompt DEs. Leaves original animation/model work intact and preserves post-original context. tests/test_native_title_prompt.py proves real production wrapper+ordering/failures; original call-chain ROM evidence .local/pal-prompt-research-05/title-frame-boundary-proof.json. Root owns native/CMake, agent interpolation_core owns module/prompt sources. Commercialtitle now visibly correct; some additional instructions still need exactprofile coverage.

Background helper now has six exact families: CommonMenu(320canvas alignment-4 fixed), Career blue, ScriptedImage(center unchanged+edge columns), ScreenCover(original150tile black scene transition), SceneImage(bank64/id28 football/net art with baked text), GlobeImage(bank53/id0 globe/football with baked logo, two owners/seven palette variants). All original constructors/full draw chains tested, foreign metadata/owner/scale rejected,4:3 untouched. Agentpal_map owns helper/tests/docs and is finishing cached-material variant then continuing bounded bank102 inventory; wait for handoff before finalbuild. No blanket all-scenes acceptance yet. Existing sky110/cleanball-arrows113/KICKOFF114 and cornerHUD193/nativeRemap180 were embedded. Numeric periodlabel+clock bothright verified actualCareer218. Maximum detail stable through natural halftime196. Full natural Preseason match138 was on older15, not current32.

Career: root boot10/binary25 created CE/clubCE/England/goalkeeper, completed original trial naturally218, progressed via original story/training to October1stWeek259. Previous801F9CE0 unmapped-tail failure fixed and trial no longer fails. Main process202397 then exited normally (no runtime fault); no SaveEnd occurred, Paksha2aad1054ee91163580053fa65cd14129859d531ed207fc8d80f36c3886e02dbf unchanged. Do not claim CE persistence. Read-only snapshots including career-week04-10.rdram retained. Agentpal_runtime now owns genuine Career save/reload acceptance in separate.local/career-acceptance-02/data copied from main, own buttons.txt, private gamescope-1/DISPLAY=:2, GDB55201/game231522 at latest report. Captures300–399 reserved for agent. Never mutate/fabricate guest saves or force original callbacks. Need originalweeklymenu, Rest/Trainingweek, Options→SaveEnd→EndafterSaving, genuinePakwrite, hash, restart/loadsamefile/date/furtheraction. Root normal capture numbers next263+.

Career navigation: RPG dialog initially UNSELECTED; firstDOWN selects FIRST(Yes/PlayGame), thenA. RepeatedA can immediately choose defaultTraining when weeklymenu appears, so stop at actualmenu or use read-only breakpoint originalfunc_802145F0_overlay_523120_80212700 before builder then release fixture. David September4thWeek Yes is short path; No adds long tutorial. Callback04AC waits script,052C starts root43,0560 builds weeklymenu. First primaryindex0Training. Options event5 is last ordinary item but lists vary; follow labels. Options submenu cursor starts0; DOWN once selectsSECOND SaveEnd/event21. ConfirmationFIRST EndafterSaving, secondEndwithoutSaving, thirdReturn. Actual firsttrialPlayGame is realfield andcompleted naturally218. ViewResults is an original alternate choice, not a forcedcallback.

Registry and interpolation fixes: metadata04 includes complete original per-function body spans plus335 folded-table dependencies/319 functions, exact original BSS clear observer8005CD50 (all58 genuine calls audited), initial full-load prerequisite and exact interval subtraction/restoration. Original surviving Career tail801F7100..9DB0 stays executable across overlappingheadloads. Originalpositive int32 length/unaligned address observed around genuineclear once; no SDKsuccessstubs or fabricatedactivation. Metadata UTF8 bytewrites fix WindowsCRLF mismatch. New graphics_task_bank parser accepts only magic-gated known RT64 noncontrol metadata02/05/06/17/18/33; originalskyopcode33 previously prevented detecting actualprojection, yielding model/camera groups0 and identical intermediates. Realfield snapshots prove correctedbank extraction; liveGPU field proof pending. ROI256 capture diagnostic avoids expensivefull8MBreadback; production disables it.

Controls: authentic greatdocbrown CC0 glyphs, family-correct Xbox/PS/Nintendo logical14actions/fourports, nativeRemap Save/Cancel actual180–183. Physicalcontroller/rumble acceptance only where available, not synthetic fixture claim. Additional AB/C Career/name bank105 and LZR country hints fixed incl owning string lifetimes and country fontY151 (not135 overlap); source32 contains these. StartRandomI4 correctly ignores unusedpalette. DataChangePressA screenshot may have been correctXboxlastdevice, so no speculativefix: agentinterpolation_core analyzing actualsource/object/hash and physicaldevice before changing prompt_encoded. CareerfieldStartButton=GameControls hint still needs completed original post80000BB8 frame dump (old field snapshot had reset spritepool). No independent controls overlay.

Linux candidate02 and path-with-spaces copy .local/portable-copy-acceptance-02/ISS2000 Portable contain47files/40notices/3libs, noROM/saves in basecandidate, fixture/evidenceOFF, noRPATH/homepaths. Actual240ROM-first prompt and242title after CLIimport passed copiedfolder; these predate newest prompt/background sources, final refresh pending. Main projectversion remains0.0.1native-development; no1.0claim. Final folders must be canonical portable Linux+Windows, ROM supplied at firstlaunch, all config/saves beside executable.

Windows private preparation .local/windows-preparation-01 uses metadata04 and regenerate/hashcheck,6prep tests and transfer--check24829files531MBpassed before newesthelpers. NO Windowsarchive/SSH/power/build/run yet. At finalstage use maquinita-windows-recomps exactskill/lock/HAhelper ownership flow, SSH192.168.68.111 userryarcade. No directpowerplug/WoL/shutdown. Recheck transfer source manifest after allhelper changes, archive onlyfinalsource. All artifacts/captures returncanonicalbefore ownedpoweroff. Latest hidden-window userinstruction also applies Windowsremainingtests; plan isolatedhidden desktop/session capture without opening visiblewindows on userdesktop.

Future rosterpacks researched/planned, not implemented1.0loader promise.100ordinaryselectable countries; factory106×22×56includes6unresolvedextras. PAL English original50VI/25simulation; movementalreadyPALcompensated, no global60speedup. Bounded matchclock corrects26vs31inclusive reload rounding; physicalNTSCmotion/audio/controller comparisons remain limited. Six upstream viewportprofile tests720..2160 pass, actual4K acceptance pending.

## Historical notes below (may describe superseded checkpoints)

## Latest steering — PAL Career mode base review

The user has paused rendering implementation to consider the attached European ROM as the base in order to retain Career/RPG mode. Recommendation: use PAL as the principal base if Career is a 1.0 requirement, retaining the US work as a preserved reference. No base replacement or PAL runtime migration has been performed. No game execution is authorized by this review; the earlier test deferral remains in force.

The private candidate is `.local/inputs/pal-en-de/rom.z64` with `identity.json`: 16 MiB, SHA-256 `6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`, NISX revision 0, entry 0x80000400, CRC 336364A0/06C8D5BF. Imported from the user attachment with byte-order normalization only. Active `.local/rom.z64`, US configuration, generated functions and saves remain unchanged. The supplied edition is English/German; Spanish support would require separate investigation/work.

US evidence: settled main menu has eight entries and original handler 0x803C34B8 explicitly guards indices <8, dispatching [0,6,7,13,2,3,4,1] to game mode 0x80130854. Career is not exposed by that menu. US ROM nevertheless contains RPG narrative remnants; do not claim every Career asset/function was removed or unlock it by inventing a ninth menu case. See `docs/research/regional-base.md` and `docs/research/pal-migration-rendering.md` when available. The online manual labeled USA describes Career and English/German but contains American warranty material; it is not reliable regional proof by filename alone.

Migration must establish PAL-specific section/overlay maps, SDK bindings, timing/VI/audio behavior, private resource tables, game/save identity and layouts. Reuse portable host infrastructure where independently valid. Verify original PAL timing instead of retaining US 60 Hz assumptions; 120 fps is a presentation/interpolation target, not permission to accelerate simulation. Do not transfer US roster/texture offsets or saves blindly.

Rendering checkpoint before this pause: build 18 passed and includes resolution profiles and widescreen culling, but there has been no enhanced game run. Later transform-tracker/runtime/RT64 bridge integration in the working tree is incomplete and has not been rebuilt as a whole. Before resuming it, wire TransformMatrixBuilder and post-call flags_after into transform_runtime observations (the final tracker rejects their current default values), and retain frame_mutex through tracker.submit_task to prevent scene/frame token invalidation. Full camera-cut/replay/teleport epochs remain unresolved. Do not describe interpolated 120 fps as implemented or verified.

## User requirements and current status

Continue autonomously to a playable 1.0; parallel agents are authorized. Intermediate builds/runs Linux only. Build/package/test Windows only at the final stage; no Windows machine action has occurred. Separate final portable Linux/Windows folders remain pending. All actual game tests use visible desktop windows with real captures embedded in chat. No hidden game executions, fake screenshots or substitute gameplay.

Actual native original CPU and audio RSP render the introduction, title and original menus through RT64. Boot 12 reached a controllable match, original pause and Replay before the user deferred further game executions. **Release 1.0, a completed match and enhanced rendering remain unverified.** Acceptance record: `docs/releases/1.0-acceptance.md`.

New user request: plan selectable roster/team/flag/kit/jersey packages for later updates while keeping 1.0 first. Research is in [roster-database.md](docs/research/roster-database.md) and [team-visual-assets.md](docs/research/team-visual-assets.md). The future proposal is [roster-pack-plan.md](docs/research/roster-pack-plan.md); it is not an approved implementation specification. No package loader/selector is implemented. The factory player database is verified at 106 × 22 × 56 bytes; edited teams/save CRCs and team-to-visual consumer routes are documented. Do not assume 106 individually selectable national teams or identify unconfirmed texture banks as flags/3D jerseys.

## Current generation and build

- `.local/game-build/iss2000`, build 17: `.local/runtime-map-04/functions` plus `.local/native-metadata-09`. Generated 12,134 original CPU bodies plus one uniquely retained original SDK function; 66 registered sections and 53 reviewed host-service bindings.
- Strict compiler `.local/toolchain/N64Recomp`, pristine pinned source `.local/deps/N64Recomp`; strict full map still rejects `0x800031AC -> 0x801EFED0`. Separately receipted diagnostic compiler changes only all-call lookup policy. Unknown/inactive calls remain fatal; do not invent an entry or success stub.
- Map 04 includes three explicitly reviewed merged function extents from original jump-table guards/targets. Boot 09 team selection fault was a truncated function at `0x802A81F4`; actual selector 5 target `0x802A8288` is now compiled. Audit of 332 switches found no additional concretely truncated extent.
- Pinned runtime/RT64 source `.local/deps/N64ModernRuntime`, `.local/deps/rt64`; archives `.local/runtime-deps-build`, `.local/rt64-build`; original audio `.local/runtime-research-rsp/audio.cpp`. Linux SDL2-compat depends on SDL3.
- CMake uses `ISS2000_ENABLE_INPUT_TESTING=ON` for the app-only virtual SDL controller. MUST turn it OFF for final binaries.
- Build 17 predates the small MotorInit result-priority fix now in source; rebuild before claiming that fix is in the game binary.

Reproducible metadata generation MUST include retained original source:

```sh
python3 -m tools.prepare_native --rom .local/rom.z64 --sections .local/runtime-map-04/section-analysis.json --runtime-symbols config/recomp/runtime-symbols.json --retained-source .local/runtime-map-02/functions/func_80060550_resident.c --output .local/native-metadata-FRESH
```

The manifest binding for `0x80060550` pins original ROM bounds/hash and generated-source hash. `native_retained.cpp` exports `iss2000_original_80060550`; root calls that unique symbol. Boots 10/11 regressed because fresh mapping replaced the old public `func_80060550_resident` symbol with upstream's honest no-Pak wrapper. Both runs were alive and received A, but Data Change stage 14 looped on game storage error 8. Do not misdiagnose this as VI deadlock or bypass the save failure. Metadata 09 fixes the collision; independent review checked provenance, aliases, generated hashes and compilation.

## Live execution and evidence

At the earlier boot 12 checkpoint the game was running under GDB PTY session 6706 (PID may differ; inspect session). Close/resume it deliberately before another launch. Original save file from boot 09 was preserved. Boot 12 passes Data Change to the main menu and settled team selection after the retained-SDK fix. `PFS 0x801A2CCC.status = 1`; original note-state counters captured. Actual editor/mode save changes surviving another restart are still unverified.

Important captures under `.local/captures/`:

- 01 first-run ROM prompt.
- 07 original intro; 11 title sustained for 277 seconds after real AI FIFO fix.
- 14 original Expansion Pak enhanced-memory notice.
- 20 original game Saved confirmation (boot 09); original .mpk creation receipt `.local/runtime-research-pak/actual-menu-save-01.json`.
- 40 boot 12 main menu after reload, embedded in chat.
- 41 menu with actual procedural physical A/B icons; 44 settled USA/Canada team selection, embedded.
- 46 original Handicap. Subsequent captures continue from 47; inspect before making claims.
- 04 is NOT game evidence (app had crashed); 09 is desktop input permission, not gameplay. Earlier 25 was incomplete team transition and must not be used to classify asset pixels.

Fresh settled 8 MiB native-word-swapped RAM: `.local/team-visual-assets-01/settled-team-selection.rdram`. Earlier snapshots `.local/switch-research-01/team-select.rdram` and `.local/prompt-research-01/player-number.rdram` remain fixed historical evidence. Do not overwrite them.

## Implemented host work and limits

Verified ROM import ZIP/Z64/N64/V64, exact canonical SHA, portable first-run selector and atomic preservation of invalid stored input. Default data beside executable. CPU overlays activate after real bounded ROM DMA copy and before PI completion; strict 8 MiB validation and SRAM direction checks. Raw unimplemented DP/yield requests fail explicitly. RT64 home discovery disabled.

AI adapter models current+next descriptors and reports current length only, using actual SDL consumed-output frames; prevents negative original buffer sizes. Original audio/title stability captured; match timing and full interrupt fidelity still require testing.

Four logical ports, hotplug, optional per-action remapping, correct Xbox/PS/Switch labels and manual family fallback. `input-preferences.json`, `graphics.json` and Controller Pak settings persist portably. F5 footer, F6 family, F7 modal settings; no runtime pause API, so settings instruct pausing in original game first. Real physical-controller prompts/actions and rumble are not yet verified. Native menu A/B textures replace only guarded known CI4 icons while retaining original palette/draw routine; additional original instruction textures still require coverage.

Four persistent 32 KiB Controller Paks under `data/saves` use original SDK filesystem algorithms over reviewed block/status adapters; original isolated allocation/write/read/reopen/delete tested. Accessory selection is independent per port (Controller/None/Rumble) and defaults to a Controller Pak on P1. Never automatically format imported corrupt images; startup snapshots and backups preserved. The game cartridge save type is None; do not claim SRAM support is used. The source MotorInit adapter remaps only upstream NOPACK (1) to DEVICE (11) for a selected Controller Pak; preserves disconnected (4).

Graphics settings for 4:3/16:9, Original/720/1080/1440/2160 resolution and Original/60/120 refresh rate are wired to RT64. Current data profile original 4:3. Actual proper field projection, target dimensions up to 4K and scene-safe interpolation are pending. Primary display is 60 Hz, so actual 120 Hz measurement is unavailable here; do not report that as verified.

## Commands and verification

```sh
cmake -S . -B .local/game-build -DISS2000_GAME_GENERATED="$PWD/.local/runtime-map-04/functions" -DISS2000_NATIVE_METADATA="$PWD/.local/native-metadata-09"
cmake --build .local/game-build --target iss2000 -j4
ISS2000_ROM=.local/rom.z64 ISS2000_GAME=.local/game-build/iss2000 ISS2000_DIAGNOSTIC=.local/clean-native-build/iss2000-diagnostic python3 -m unittest discover -s tests -v
```

Latest full suite: 166 tests passed with all integration environment variables set, zero skips; log `.local/tests-integration-boot12.log`. Tests do not establish a controllable match.

Actual desktop/GPU runs require approved escalated tool environment with `DISPLAY=:0`, `GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb SDL_VIDEODRIVER=x11`. Redirect inferior logs to private file under GDB. Historical LD_LIBRARY_PATH points to RT64 `dxc/lib/x64`; actual Linux uses embedded SPIRV and final packaging should verify it without developer paths. Activate exact window `ISS2000 | djultra64` then Spectacle capture, inspect and embed. Attaching to another process is restricted; launch GDB child instead.

KDE remote input-control permission appeared when sending X11 keys. User was asked to accept; never click/bypass that permission. App-only SDL virtual-controller test fixture controls only this app with `.local/input-test/buttons.txt` tokens start/a/b/up/down/left/right; release with empty file. This does not verify physical input. Fixture is prioritized as P1.

## Remaining

Reach and control a match; verify save changes/restart, original modes, audio transitions and full controller-family prompts. Validate graphics/interpolation with actual scene evidence. Produce portable Linux package with explicit runtime libs and notices, clean ROM-first import and copied-path verification. Only then use maquinita Windows skill for final Windows build/package/run; portable lookup bridge preparation is in `cmake/runtime_lookup_bridge.cmake` and `docs/runtime-lookup-bridge.md`, integration not complete. No Windows machine action yet.

All private ROM, extracted assets, generated original CPU code, builds, save files and captures remain ignored under `.local/`. Do not publish them. Source checkpoint pending; verify actual Git author and committer are `djultra64` before committing.

## Latest user priority — rendering work, execution tests deferred

The user now requests16:9 first, then720p through4K profiles, then120fps interpolation, and explicitly defers further game execution tests. Boot12 was closed deliberately; GDBsession6706 and gamePID95869 exited. Do not launch new game runs or Windows work while these tests are deferred. Compilation, unit checks and static original-data analysis continue.

Before closure boot12 reached actual field gameplay, responded to movement/action input, opened original P1pause and rendered Replay. Actual captures54(field),55(movement/action),56(P1pause),57(Replay). Captures54and56 were embedded in chat. This establishes the first controllable native match; it does not establish full match completion, graphicsenhancements or a finished1.0.

New paused original field snapshot `.local/team-visual-assets-01/paused-match.rdram` supports static rendering research. Rosterpack research now documents exact USA/Canada flag data matches in original compressed asset2A3 and palettes2A1;3Djersey/material ownership remains incomplete. Futurepackage implementation remains deferred.

Agent tasks: overlay_research implements guarded horizontalCPU-culling and rotated-worldcorner widening helpers after original22E58/243E0, based on exact originalcamera axes, with tests only. overlay_probe extends resolution profiles900p/1800p and accurateaspect-aware dimensions/default16:9 fornewsettings. runtime_research recovers stablecamera/entity/bone identities for scene-safeRT64interpolation. Root owns renderer/nativebridge/CMake. No one runs the game.

Root integrated new titleprompt adapter source/hook039F4 afterbuild17; not yetrebuilt/visuallyverified. It edits only original12-bytePRESSSTART storage toactualphysicalStartname; popupA encodedstrings discoveredbutnoadapterimplemented. See agents' docs for completedresearch.


## Authoritative controls update — 2026-10-15 latest user decision

This update supersedes the earlier manual wait and Type 4 Modern proposal;
retain all historical notes as evidence. The user supplied primary PS1 videos
2026-10-15 18-59-43.mp4 and 2026-10-15 19-00-47.mp4 in Downloads.
Adapt the authentic pre-match/Training Controller screen; remove the extensive
raw N64 remapping and its Options entry. Keep Type 1 through Type 4 from PS1,
add Type 5 as an adapted current eFootball layout, then Free: six choices total.
Free edits football actions with actual device glyphs; Start confirms, with an
explicit English footer. All UI text remains English. The supplied stretched
videos are references only, never replacement UI assets.

Map by physical positions, accounting for Nintendo face-button swaps. Type 5
basic positions: Pass South, Shoot West, Lob East, Through North, Dash R2,
Cursor L1. OneTwo R1 and Curve L2 are ISS-specific adaptations, not a claim of
identical modern compound mechanics. Official reference:
https://img.konami.com/efootball/s/img/manual/efootball2023_ps5_en.pdf
Keep six host choices separate from the genuine N64 three-profile table.
Preserve four ports, original Cursor/Keeper behavior, saves, and real errors.
Windows remains frozen; game tests remain hidden; old portable folders and
user data remain preserved.

## Exact r56 fullscreen verification in private KWin — 2026-10-17

The production executable `4acc1f74ea76dca1536a0b57b5858933a67f792346eb1e4209ef0eb250d6deea` ran under an isolated virtual KWin OpenGL compositor, with real SDL/Xwayland window management and dummy audio. Alt+Enter changed SDL's actual fullscreen bit from 0 to 1 and `_NET_WM_STATE_FULLSCREEN` appeared; a second Alt+Enter returned the bit to 0 and removed that property. Native Graphics Settings then applied and saved Fullscreen, again acknowledged by SDL. A fresh game process loaded the saved preference and both SDL and the window manager reported fullscreen. Both game children and compositors exited normally with code 0 through Escape. The private keyboard helper's final keyup failed because the correctly closed display was already gone.

This closes the earlier actual-fullscreen uncertainty for the tested Linux virtual-window-manager path. Gamescope's lack of fullscreen acknowledgement and the earlier painter-backend failure remain harness-specific observations; neither is discarded. No physical monitor, audio or sustained performance result is inferred. Evidence: `.local/r56-fullscreen-kwin-gl/acceptance-receipt.json` and `.local/r56-fullscreen-kwin-gl-restart/`.

## r57 capture-method control — 2026-10-17

During exact r57 clean boot under virtual KWin, ImageMagick X11 window captures appeared black after the title. A controlled repeat compared XGetImage against Spectacle on the same private KWin bus/output, without intervening game input or resize. The compositor showed the animated Main menu while XGetImage returned black or an older KCEO frame; repeated compositor→X11→compositor captures retained this discrepancy. This is a demonstrated stale-window-capture artifact. It does not explain the user's earlier reported black screen. Future KWin visual acceptance uses private compositor captures.

The exact r57 executable (`f1a5fcd13794f3428ea86c6d4537d4092b3c4778cb67af64c002a4b5a4676480`) reached Main from empty data, with default 720p/60/16:9 and explicit private ROM argument. Native Graphics saved fullscreen; Alt+Enter toggled actual SDL state; cold restart restored SDL and window-manager fullscreen. All three relevant game children and compositors exited 0. Dummy audio and simultaneous test activity exclude sound/performance claims. Receipt: `.local/r57-portable-clean/acceptance-receipt.json`; controlled captures: `.local/kwin-compare57/`.
