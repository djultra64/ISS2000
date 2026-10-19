# PAL r63 startup, menu and projected-player shadow corrections

Original project work: **djultra64**. Linux only, one worker, no agents.
Windows remains frozen. Original ROMs, generated CPU inputs and `sources/` stay
unchanged. All historical packages and user data remain intact.

## Startup

The genuine PAL `osPfsReadWriteFile` wrapper stages a complete original file
write in the owning thread and publishes one durable image only after original
SDK success. Failed writes roll back; external edits, wrong threads and real
filesystem failures are rejected. Other ports remain independent. Ordinary
block writes retain their prior durability. This removes hundreds of repeated
whole-image replacements without fabricating a successful SDK result.

A same-volume private benchmark of976 block writes took3.073 seconds with
per-block publication and0.004 seconds in one file transaction. These are storage
measurements, **not total startup times**. The first healthy automatic entry's
four known UI callback waits are shortened to one frame each; subsequent manual
entries and genuine error dialogs retain original behavior. The original native
font displays `Loading game` while that owned healthy entry remains active.
Fresh private boots create a genuine save and later private boots read it back.
No claim of an instantaneous complete boot is made.

## Menus and physical prompts

Main Select's existing foreground rows are raised16 logical pixels, keeping
sizes and separation. The footer ends within the PAL visible crop. Exit is the
physical north face button: XboxY, PlayStationTriangle, NintendoX, or keyboardY.
The original engine draws the English confirmation and active-device glyphs;
No is the default. Opening, device/focus changes, closing and held input require
release before accepting another action. A confirmed Yes exits normally.

Original font objects now request an opaque native material explicitly, so an
unrelated transparent sprite cannot make the new question/footer invisible.
Actual GPU captures verify the raised rows, complete footer, visible question,
No default and cancellation. A prior private run verified clean Yes exit0.
The renderer fixture covers all four ports and controller families.

The title's real accepted-input phase keeps the physical Start/Menu/Options/Plus
or keyboard name. Select Teams' upper `Load Saved Data` label fits its88-pixel
strip with a true80-pixel text extent; direction controls use glyphs only.
Edit Controller adapts the Config row independently of the lower panel and
retains its Type while Cursor/Keeper show their original help. The original
exit callback remains a rendering owner, so custom labels persist through that
transition. Private UI05 captures confirm Type5, Cursor, Keeper and early exit.
Physical Xbox transition appearance still belongs to user acceptance.

## Projected player silhouettes

The new geometry is a simplified articulated silhouette, not a duplicated full
player model. It uses the same eleven original world-space pose joints and ten
rounded capsules:80 vertices and60 triangles. It never advances animation or
simulation. Daytime retains the original(-.5,+.5) projection. Weather uses the
lighter64 alpha instead of96. For the pinned two-quad floodlight material, the
stronger original quad supplies the light direction; its cone is replaced by
the same articulated silhouette. Scene6/16 is admitted only when the same field-player table and reciprocal
backlink guards succeed. Special introduction characters, referees and
unrecognized owners retain original behavior.

The new mesh uses real pixel depth at one tenth of a world unit above the
pitch; it does not use the old constant far-plane primitive depth. An earlier
candidate's material order cleared its own source bit, and a subsequent
far-plane candidate still gave inconsistent coverage. Neither is the packaged
material. Private UI07 field captures establish visible pose-following ground
silhouettes for the pixel-depth candidate. Night and coin-toss extensions have
CPU coverage, not a new GPU acceptance claim.

Two disjoint64KiB banks at807E0000..80800000 hold22 bounded2048-byte slots.
Reviewed original High code/BSS ends at807B4A60; existing matrix banks end at
807E0000. Original menu/field/training snapshots show the new region unused.
Each mesh has an exact owner/root/player backlink, bank, topology and material
header. Metadata recognizes only exact captured24/24/24/8 vertex loads. The
RT64 adapter adds only the two explicit new load opcodes, retaining identity
matrix, perspective, scene, immutable task, generation and address/count guards.
Original shadow depth translation and legacy topology remain independently
verified. No generic vertex-command or global depth-comparison exception exists.

Replay phase3 retains the same/next original68-entry cursor's identities.
Seeks, foreign phases, invalid cursors and camera cuts receive fresh identities
or no metadata. Submitted task snapshots remain immutable.

## Evidence and remaining observations

Focused regressions cover complete SDK transactions and failures, first-entry
startup waits, actual original font/sprite output, menu input lifetime, both
geometry banks, all22 player slots, day/weather/night materials, malformed
owners/poses/topology, replay cuts, exact RT64 vertex commands and foreign
negative controls. The first full run exposed two extracted platform fixtures
missing the new inline exit state; those fixtures now include the actual state
and preserve their existing assertions. Final full-suite result is recorded in
`.local/r63-verification/suite-exit.json`.

Receipts and private evidence: `.local/r63-verification`, `.local/r63-ui`.
All visual sessions use one hidden compositor and an explicitly verified unique
null audio sink; no user game or user saves are controlled. UI05 and UI06 exited
normally with code0. Later session cleanup status must be read from its receipt.

The requested goal-replay ball trail and4:3-to16:9 entrance remain **unresolved**.
A historical frame shows huge translucent gold geometry, but its original
producer has not been proved to be the requested ball trail. Earlier targeted natural-play captures reached a 0–0 halftime. Exact r64 UI08
subsequently completed a 1–0 match, but its goal entry was not captured by the
valid authenticated video windows. A later rematch recording ended during
its introduction when the bounded harness deadline was reached.
Current source deliberately contains no speculative goal-effect alteration.
The user has been asked whether the affected effect is the giant gold ribbon,
the small trail following the ball, or both. Full functional/gamepad acceptance
remains with the user. This is a correction candidate, **not accepted1.0**.


## r64 follow-up: completion-ring pressure during video reconfiguration

Private UI07, SHA06849fd8f356a3a3d7f59595e255a0c28e5063fbb610fbcc9b057e625aa2f558,
reproduced a persistent black second-half entry. Read-only sampling found600
identical stage/actor/ball counters over3s: stage_tick32659, actor4, ball4,
stage6/4 and pause0. All three new High framebuffers were busy; completion-ring
read/write both8012DCE0, cached current80500000. The prior Low menu's cached
current was8032D000, outside the new80500000/805AA000/80654000 pool. Last three
field render receipts completed within about18ms. The game exited normally0.
A debugger attachment was denied by the OS; no debugger attached or guest-memory
write occurred. The subsequent sudo attempt required a password and did not run.

The three-entry original completion ring uses read==write for empty. A focused
CPU sequence executes the real original completion producer and VI retirement:
request A while hardware still shows Low, then finish B/C before the next VI.
Both unchanged original and the earlier displayed-slot guard wrap the ring,
stop after three completions and reproduce cached80500000 with all slots busy.
The new allocator reserves capacity when the cached display is outside a genuine
three-slot pool and two slots are already busy. It returns unavailable until
original VI adopts the new pool. It writes no flags or queue pointers, retains
first-free order, and never invents SP/DP completion or changes timing. After
adoption the previous exact displayed-slot guard and original retirement run.
The new sequence completes ten frames; exhaustive pool/busy/current combinations
and the earlier ownership regression also pass. Two-slot pools are unchanged.

Generator output is immutable `pal-framebuffer-ownership-v2`. r63 is an
intermediate package with the retained black-screen failure; r64 includes this
follow-up. The prior r63 full suite passed514 tests (511 pass,3 historical NTSC
skips) before this new mechanism was added. Final r64 results and runtime scope
belong in `.local/r64-verification`; a successful CPU reproduction alone is not
claimed as complete functional acceptance.

Final r64 automated suite:514 tests,511 passed and3 historical NTSC diagnostics
skipped,542.216 seconds. Exact executable SHA-256:
`fc19000a9d714eb5629e262b6eb254926ca7fa1f5937e07882622bc1cc0588c5`.
Receipt: `.local/r64-verification/suite-exit.json`.

Exact r64 UI08 returned to the second half and continued. Its stable double-read
scheduler trace contains2744 changed rows (250 changing read pairs rejected),
including25 rows with the new High pool and a cached address still outside it.
Those rows never exceed two busy slots. The current display then cycles through
all three High addresses. A subsequent594-sample3s observation retains all real
field gates and stage_tick advances38471 to38546; actor/ball state also changes.
Actual screenshot `ui08/21-return-menu.png` shows the live2nd field. Receipt:
`.local/r64-verification/second-half-receipt.json`. This is one bounded genuine
return, not a claim that every historical black-screen mechanism is resolved.
X11 root/client recordings were rejected because they contain black Xwayland
pixels; they are not evidence of game output. Later video uses the authenticated
owned Gamescope Video/Source node and includes receiver timestamp receipts.


## Final session disposition

UI08 reached the 1,800-second harness deadline during a later rematch. Its
`session.json` records cleanup of the owned process group, monitor, null sink
and private runtime. Host verification confirms all four recorded PIDs absent
and the owned sink module unloaded. No normal application exit is claimed for
UI08. The incomplete `goal-reproduction` PipeWire clip contains 1,217 frames
ending when the owned source disappears; its encoder closed with status 0, while
the capture process reported the expected removed-source error. This partial
clip does not establish a goal-effect reproduction or a new game defect.

No further game session was started. The fresh r64 package remains separate
from all private test data. Manifest verification covers 46 files and 40 notices.
