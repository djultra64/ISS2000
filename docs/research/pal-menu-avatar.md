# PAL Training preparation and Select Teams avatar interpolation

Original project work: **djultra64**.

This profile covers the original articulated player on the Training preparation
and Select Teams pages. It does not authorize interpolation of every object in scene `0x0607`.
The original camera, the separate Training preparation 3D title, other menus, unknown matrix loads,
and all menu matrix multiplies remain excluded. Simulation and animation updates
are unchanged; host metadata identifies the original rendered limb matrices.
No game execution was performed for this correction pass.

## Original owner and allocation evidence

The completed original frame is private
`.local/ui-redesign-01/training-prep49-completed.rdram`. Scene bytes are `6/7/0`,
working resolution is Low, and the original canvas is `320×240`. The corresponding
Controller and Select Training snapshots use the same common scene but fail this
profile: they do not own this complete player rig and active callback.

The scheduler's original bounded 220-node pool starts at `801E7070`, stride
`0x74`; its active list starts at `80077390`. The preparation avatar's callback
is `802BDA2C`, in original overlay ROM `401910 → 802B8500`. Its full 60-byte body
is ROM `406E3C`, SHA-256
`cc33ac8edbdc4f39c5ce9a8ab8afcea489014419e388c19c04919b6fef9f4853`.
It writes the fixed preparation position to model-state zero at `801A081C`.
The helper compares all 15 original instruction words, traverses the bounded
scheduler list, and requires this callback to be active.

Model-state zero's 19 original pointers start at `801A07CC`. In the completed
frame the root is `8014FE2C`, with its reciprocal model-state pointer at `+84`;
its first child is `8016507C`. The root belongs to the original 285-record pool
`80145624`, stride `0x98`; the 18 limbs belong to the 900-record pool `8014FF5C`,
stride `0x60`. All records must be distinct, allocated, and matrix-built; limb
links must remain inside this exact rig. Both matrix pointer columns (`+18/+1C`)
must fit the genuine two `0x5100`-byte arenas starting at `800A7848`.

A different allocated root, `8014FEC4`, renders a separate title. It is captured
by the existing generic observers but explicitly absent from this 19-record
scope, so it receives no menu interpolation group.

## Task bank and lifetime

The completed frame uses model bank zero while its Gfx arena is bank one.
Neither the current bank global nor the Gfx arena is therefore a substitute for
reading the submitted task. Original `8002B9B4` emits perspective
`800C1AC0 + bank × 0x40`; this is verified by executing the original producer in
both banks, rather than treating the perspective as an unbanked constant.

The new task walker nevertheless requires all 19 owned **model LOAD** addresses
to identify one consistent bank. It follows the genuine nested lists and segment
updates, bounds traversal to 16,384 commands and 32 list levels, and rejects a
missing joint, mixed banks, unknown conditional control flow, or unknown microcode
switch. Only the two original F3DEX2/F3DLX2 code/data pairs are allowed. Pinned
RT64 classifies both as `F3DEX2` and caches their shared opcode map by that type;
its original microcode switches therefore retain the scoped matrix callback.

Publication copies the whitelist only when every record has a captured current
frame tag with the same live allocation ID, generation, and scene epoch. A cut
or reallocation renews IDs. Reallocation after capture without another genuine
matrix build cannot publish the old scope. Already submitted snapshots retain
their immutable previous scope and tags. Model/camera IDs remain below
`0x60000000`, preserving the separately reserved shadow range.

## Verification and limits

`tests/test_pal_menu_avatar.py` executes the genuine original chain
`8002B30C → 80025910 → 80025958/80025D70`, then
`80002824 → 8002B9B4` and their required original CPU callees. Privileged or
unexpected unresolved branches terminate the fixture; there are no successful
SDK substitutes. Four consecutive frames exercise both matrix banks, all 19
limb tags, stable IDs, a cut, and a root reallocation. Every instrumented frame's
entire 8 MiB RAM equals the same original chain without observers.

The completed-frame test additionally checks both unrelated original menus,
foreign owners/code/frame layouts, invalid links, missing or mixed-bank joints,
unknown microcode, bounded cycles, and canonical task addresses. Model multiplies,
all projections and the recorded title model are asserted to remain ignored.
Existing field transform tests remain required. These are CPU and metadata
proofs; visual smoothness and the user's reported shadow flickering still need
manual acceptance. This profile does not establish coverage of other 3D menu
previews.


## Select Teams correction after r51

The user supplied private recording `2026-10-15 21-25-00.mp4` shows Select Teams,
including the standing player preview. Its first three seconds contain 180
recorded frames. In the stationary player crop (1225,510;140×300), adjacent
8-bit grayscale mean differences separate compression noise (roughly0.02–0.2)
from actual pose changes (roughly3–10). Thresholds0.5,1.0 and2.0 independently
count25 pose changes in each second. The recording's60 fps container therefore
does not imply60 distinct player poses.

Root cause: r51 authorized only the original Training preparation callback
`802BDA2C`. Select Teams shares scene607 and the19-node model-state-zero rig,
but its active scheduler owner is `802A0C48`. Its original overlay is ROM
`4534E0 → 8029EEA0`; the first64 bytes at ROM `455288` match the completed
private `hidden-test-01/team16-completed.rdram` snapshot and have SHA-256
`1cb1769e3ad816e07fd9fb81daa98804ad0848dcfc7d4b00be8a72e6f984bb3e`.
The correction requires these exact16 instruction words and this active owner
before reusing the existing bounded19-record proof. The root's reciprocal state
pointer, distinct records, live allocation generations, limb links, both matrix
arenas and all19 original submitted MODEL LOADs remain required.

The genuine Select Teams regression failed before the correction at missing
submitted menu metadata. After the correction it runs four original matrix/draw
frames in both banks, checks all19 scoped tags, exact8 MiB RAM equality with the
uninstrumented chain, scene cuts, root reallocation, immutable prior submissions,
and the separately built original title's exclusion. Altered/inactive owner,
scheduler cycle, duplicate or foreign joint, and broken reciprocal owner reject.
The existing Training preparation/foreign-menu regressions also pass.

This corrects coverage of the demonstrated first player rig. It does not
establish60 distinct GPU images, coverage of every menu/title/second player rig,
or arbitrary flag transitions. The2D sprite matcher still deliberately
rejects changed texture content, UVs and materials. No game/GPU execution or
simulation-rate changes were performed. Visual acceptance remains with the user.


## Select Teams waving flags

Select Teams also renders waving flags as original3D geometry. The two flag
roots come from its original globals `802ACD78/802ACD7C`, populated by
`802A5F68 → 8000A560 → 800397A4`; their shared original display list is at
`800BD9E0`, and its shared vertex grid at `800BD9D8`. Original per-frame
`80039A88 → 8003946C → 800393CC` updates this6×5 grid. The first branch passes
amplitude80 and `800393CC` stores `trunc(sine×80)` as Z, establishing the full
`[-80,80]` bound rather than inferring it from a few samples.

Only the exact active Select Teams owner can attach up to two optional cloth
models. Their original root allocations, both matrix arenas, exact four
12-vertex strips and triangle topology, fixed XY/UV grid, original shared setup
entry, texture768-byte span and palette512-byte span are validated. Unknown
meshes and titles remain excluded. Invalid/absent flag metadata does not remove
the independently proven player rig. Publication independently requires each
included flag's current live allocation generation and freshly captured matrix.

For these two validated models only, the existing RT64 matrix group also enables
vertex-position interpolation. UV interpolation stays disabled. A private group
identity incorporates original texture/palette contents and resource pointers,
so changing the selected team texture or palette cuts the old identity instead
of morphing different flags. Scene cuts and allocation reuse also renew IDs;
queued snapshots retain their prior immutable IDs. No original RAM or rendering
instruction is changed.

The genuine original closure now runs the real wind producer before the existing
matrix/draw chain, proves actual changed cloth vertices, both flags' genuine
submitted MODEL LOADs, stable groups across adjacent frames, texture identity
cuts, allocation guards, and foreign topology/XY/UV rejection. The exact original
flashing sprite `8013CE54` separately emits30 observed E4 rectangles with stable
IDs when alpha changes80→96; its entire8 MiB output remains identical with and
without the observer. This shows that producer is covered by existing2D tracking;
it does not by itself prove GPU color matching or smooth border presentation.

RT64's vertex-position interpolation does not interpolate original per-vertex
RGB shade updates. Those shades retain their original cadence. GPU smoothness,
all other menu scenes and complete120Hz acceptance remain unverified.


## Second avatar correction after r53

The old Select Teams fixture was misclassified: completed snapshot
`.local/hidden-test-01/team16-completed.rdram` contains **two articulated
players**, not one player and an unrelated title. Model-state zero is
`801A07CC`, root `8014FD94`; model-state one is `801A08CC`, root `8014FC64`.
Each has 18 independent child records and a reciprocal root `+84` pointing to
its own model state. The original model-state stride is `100`, established by
`8002D894` and the original state traversal. The actual unrelated title in the
Training preparation fixture remains excluded.

The regression previously asserted exclusion of `8014FC64`. It now fails the
old 19-entry capacity, then proves both real 19-node rigs with the original
matrix/draw closure. The scope holds exactly 19 or 38 records; a second player
is admitted only under the exact active Select Teams owner and only when the
second state's complete rig passes the same pool, allocation/matrix-built,
distinctness, reciprocal state, arena and within-rig link checks. Links between
the two rigs are rejected. A missing or malformed present second rig rejects
the proof, rather than silently publishing its first half.

Task validation uses a 64-bit observed mask and requires all 19 or 38 MODEL
LOADs in one submitted bank. A missing second root or mixed second-root bank
rejects. The immutable tracker independently requires the declared count to be
19 or 38, every used record to have a current live allocation/matrix tag, and
all unused slots to be zero. A stale second state cannot authorize another
player when Training preparation is active. The fixture's complete 8 MiB
original output remains byte-identical across four frames and both banks.

This establishes the prior second-player omission. Actual r53 single-player
and two-player RT64 matching/presentation remains under separate investigation;
this metadata capacity correction alone is not GPU smoothness acceptance.


## Yellow Training Select Teams: distinct original owner

An actual hidden r53 capture established a separate failure from the second
player omission. `.local/select-teams-54-before/yellow.rdram` is the yellow
single-team selector, with model-state zero root `8014FCFC` and no second rig.
Its active dispatch owner is `802A8434` in original overlay ROM
`46FC80 → 8029EEA0`, not the blue selector's `802A0C48`. The first 64 bytes at
ROM `479214` match the captured RAM exactly; SHA-256 is
`3f0bfa2f9c094599200636a6588037d0062b2dd69110bb33ae9220a6e3725c28`.
The proof requires those 16 exact instruction words and the bounded active
scheduler callback, retaining every original 19-node rig guard. This owner
cannot authorize state one or the separate standalone flag roots.

Four captured r53 tasks had stable scene `607` / epoch `55`, an installed
bridge, zero captured metadata, unknown bank `2`, and all 104 matrix calls
ignored. This proves that interpolation was absent in that scene before the
correction. It was not an inference from recording/container FPS. The new
regression first failed for the missing owner, then accepted the exact captured
host-adapted task `800E0388`, including its real extended raster commands. That
task uses model bank zero while the live bank global is already one and the
live Gfx arena global has been cleared; task inspection remains required.

The CPU regression runs four subsequent original matrix/draw frames, checks
both banks, all 19 selected limb groups and whole-memory observer equality,
and rejects changed code, inactive owner and broken reciprocal ownership.
The blue selector regression additionally executes genuine `80031E74` animation
and its real pose-baking closure: both rigs' actual matrices change between
adjacent frames while IDs stay stable. Original geometry `8002EB64` is compiled
as C intact; original BREAK, invalid switch and unresolved targets terminate
the fixture. No successful SDK stand-ins are used.

Actual post-fix RT64 matching and generated-image acceptance is recorded by the
root runtime integration work, separately from these CPU/metadata regressions.
