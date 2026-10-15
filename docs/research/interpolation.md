# RT64 interpolation integration evidence

Original project work: djultra64. Read-only inspection of the pinned local RT64
source and original ISS2000 display lists; no new game execution or frame-rate
measurements. A 120 Hz configuration is not evidence that 120 distinct frames
were presented or that entity matching is correct.

## Presentation and simulation are separate

`src/renderer.cpp`, `RT64Context::config`, already maps the portable 120 option
to `UserConfiguration::RefreshRate::Manual` and `refreshRateTarget=120`.
Keep the original VI events, scheduler, simulation updates, controller polling,
AI DAC timing and audio FIFO consumption unchanged. Renderer configuration does
not authorize advancing the game simulation at 120 Hz.

Pinned implementation references, relative to `.local/deps/rt64`:

| Source and symbol | Relevant behavior |
| --- | --- |
| `src/hle/rt64_workload_queue.cpp`, workload processing around 975–1020 | Frame matching runs for targetRate>0. Intermediate frames require targetRate>viOriginalRate, !workload.paused, and a recognized presentation framebuffer. Logical/display ticks determine the number of intermediate frames. |
| `src/hle/rt64_state.cpp`, full-sync processing around 1614 | Original rate comes from an explicit extended refreshRate if set, otherwise `viHistory.logicalRateFromFactors()`. Do not set extended refreshRate=120: it describes the original logical rate. |
| `src/hle/rt64_present_queue.cpp`, presentation around 160–186 | Modified framebuffers default to interpolation disabled. The actual presented framebuffer becomes eligible; PresentEarly/SkipBuffering affect its selection. |
| `src/hle/rt64_game_frame.cpp`, `GameFrame::match`, `matchScene` | Matches scene/projection transforms and compatible draw calls. Default AUTO matching uses geometry/material compatibility and transform similarity; it does not know football entity identities. |

At a real original cadence of 30 updates/s, a 120 target would request four
presentation samples per update; at 60, two. These are conditional examples,
not measured ISS2000 cadence. Preserve Console presentation initially; changing
to PresentEarly also changes buffering/latency and needs its own verification.
A display refresh query alone reports swap-chain capability, not generated frame
count, simulation cadence or frame-pacing quality.

## Actual paused-match evidence

The private eight-MiB native-word-swapped snapshot is
`.local/team-visual-assets-01/paused-match.rdram`. It was captured by root's
visible run before the user postponed gameplay testing. Guest main state
`8013DF26=6`, substate `8013DF2C=4`, stage `8013DF2E=0` describes this captured
field/pause context. Prior menu context used main/substate 6/7. These are phase
landmarks, not a complete replay, pause or camera-mode specification.

A bounded static traversal from display-list root `800D2C08` followed 4,424
commands and found 187 matrix commands using 118 distinct matrix addresses:

| Original command | Count | Observed role/evidence |
| --- | --- | --- |
| `DA380007`, source `800C43E0` | 3 | F3DEX2 projection load; matches the reviewed perspective builder's `800C43A0+index*64` destination family. |
| `DA380005`, source `800CECA8` | 3 | Projection multiply, contributing the camera/view transform in this captured list. Exact camera-owner structure remains unresolved. |
| `DA380003` | 159 | Model-view loads, including sources in `800AFxxx`/`800B0xxx` and shared `801A6790`. |
| `DA380001` | 22 | Model-view multiplies; repeated source `8012C690` occurs in several chains. |

The projection roots occur at `800D3518/3538`, `800D3C98/3CB8`, and a later
repetition. Shared model matrices, repeated loads and nested sublists mean that
neither call ordinal nor raw RDRAM address is a verified player/joint ID. Matrix
storage may alternate across buffers. No player-slot-to-matrix ownership or
camera cut flag has yet been proved from this one snapshot.

## Supported tracking APIs and constraints

`include/rt64_extended_gbi.h` provides `gEXMatrixGroup`,
`gEXMatrixGroupSimple`, `gEXMatrixGroupDecomposed`,
`gEXMatrixGroupNoInterpolate`, and `gEXPopMatrixGroup`.
Its component modes are SKIP, INTERPOLATE and AUTO; IDs are IGNORE=0,
AUTO=FFFFFFFF, or explicit stable nonreserved values. Ordering can be LINEAR or
AUTO. Position, rotation, scale, skew, perspective, vertex position, texture
coordinates, tiles and look-at interpolation are separately controlled.

Equivalent host integration is possible without editing dependency source or
inserting commands into guest display-list buffers:

1. `src/hle/rt64_interpreter.h` exposes `Interpreter::hleGBI` and `gbiManager`.
   `src/gbi/rt64_gbi.h` exposes `GBI::map[256]`, each a
   `GBIFunction(State*,DisplayList**)`.
2. A project-owned wrapper can save the original verified F3DEX2 matrix callback,
   classify the exact command/source, assign interpolation group state with
   `RSP::matrixId(...)`, then invoke the original callback once. Its original
   decoding is in `src/gbi/rt64_gbi_f3dex2.cpp`, `F3DEX2::matrix`.
3. Install once per verified GBI instance, preserve existing callback ownership,
   and handle task/microcode reset. Never accidentally wrap an already wrapped
   callback or assume every microcode's matrix opcode/flags match F3DEX2.

`src/hle/rt64_rsp.cpp`, `RSP::matrixId`, has an important limitation:
`idIsAddress=true, editGroup=true` edits properties of existing editable groups
found via `physicalAddressTransformMap`; it does **not** replace their matrix ID.
It cannot retroactively assign stable player IDs. Editing after
`Application::processDisplayLists` is also too late: full-sync processing can
already queue the workload during interpretation. Tracking changes must occur
before the affected transforms are captured/queued.

## Bounded implementation order

First keep a small presentation policy independent of game data: Original keeps
the original target, 60/120 choose a manual presentation target. Expose evidence
of the target and later actual original/presented frame counts separately.
Do not label a target choice as verified interpolation.

Then wrap the verified matrix path and assign a distinct camera group for the
verified field phase. Keep ordinary camera interpolation simple: pinned
`GameFrame::matchScene` explicitly defaults camera decomposition off. Use a
scene-generation token so a phase transition cannot match the previous camera.
Orthographic UI, text, score digits, full-screen fades and unclassified projection
passes should use IGNORE/no interpolation until their behavior is proved.

For player/ball interpolation, first recover the real entity and joint ownership
from the original matrix-building callers, including buffer selection and
substitution/spawn generation. Assign stable IDs from scene generation + entity
slot + joint, rather than draw order or raw matrix address. Use decomposed rigid
transforms only for proved rigid bodies. Explicit vertex interpolation may be
needed for CPU-deformed models; topology and vertex correspondence must match.
AUTO geometry matching remains a provisional baseline and can match similar
players incorrectly when visibility/order changes.

For cuts, change camera/entity scene IDs before processing the cut workload, or
mark the affected groups IGNORE for that workload and resume with a new epoch.
`GameFrame::matchScene` maps explicit camera IDs only when previous and current
IDs agree; ignored transforms are unmapped in `GameFrame::match`. This gives a
supported reset without globally resetting/destroying RT64 state. Phase6/4 to
6/7 is a proved transition signal; replay cuts, goal cinematics, camera changes,
substitutions and teleport/reset events still need exact guest evidence.
Do not reinterpret the guest pause as `workload.paused` without proving that API's
semantics; unchanged simulation transforms naturally produce identical samples.

After 16:9 and resolution work, root's separately authorized visible tests should
verify moving players and ball, camera pans, sidelines/occlusion, pause/resume,
replays and abrupt cuts, then compare match-clock progression and audio timing
against Original mode. A paused still image cannot validate interpolation.

## Verified original owners and host tracker implementation

Subsequent static inspection establishes two camera slots and their buffer
ownership. Resident `8002ACAC` toggles `800A07B8` with XOR1 at `8002ACE8..ACF0`,
then calls `80024C3C` to build the perspective matrix. Its loop uses
`viewslot=0,1` (`8002ADB8: slti s0,2`) and calls original camera/view builder
`80020DA4` at `8002ADB0`. Matrix destinations are:

- Perspective: `800C43A0 + framebufferIndex*40` (hexadecimal byte offsets).
- Camera/view: `800CEC68 + framebufferIndex*40 + viewslot*80`.

Original emitters `8002AFB8` (`8002B268..B2A4`) and `8002B354`
(`8002B64C..B688`) use that same camera formula for `DA380005`.
Consequently `800CEC68/800CECA8` share stable camera slot0;
`800CECE8/800CED28` share slot1. Buffer alternation must not create a new
camera identity. This proves buffer/slot ownership, not all camera-cut flags.

The original model renderer uses fixed allocation pools:

| Pool base | Count | Stride | Allocator returning record in v0 |
| --- | --- | --- | --- |
| `80148104` | 285 | `98` hex | `8002A5A8` |
| `80152A3C` | 900 | `60` hex | `8002A820` |

Initialization/free-list rebuild is `8002A90C`/`8002A3DC` for the first and
`8002A438` for the second. Shared flags are at record+28, active bit80000000;
bit00100000 distinguishes the smaller pool. `8002A820` initializes
C0104012 there and clears bank matrix pointers at +18/+1C. Parent/first child
links are +44/+48 and sibling links +4C/+50. **The same free routine8002A6C8
handles both pools**, recursively freeing first children through the call at
8002A710; it branches on bit00100000 at8002A78C to select the correct free list
and avoid larger-record-only cleanup. Every recursive entry must participate in
host lifecycle tracking; do not release only the outer root.

`800252B0` resets two matrix arenas. For framebuffer bank b:

```
begin = 800AA128 + b*5100
end   = 800AF228 + b*5100  (exclusive)
```

It writes cursor/end to800B4328/432C. `800252F8` at80025484..54A4 and
`80025710` at80025730..5760 write the next matrix address to
`record+18+b*4` and advance the cursor by40. Both routines recurse before
returning, so a before/after hook can see more than40 bytes of cursor movement.
A record pointer changing to exactly the captured pre-call cursor is useful
ownership evidence; scanning all object matrix pointers later is insufficient.
The paused snapshot has stale/aliased pointers even on active records, and its
current bank0 differs from the captured display list's bank1.

`src/runtime/transform_tracker.hpp/.cpp` now implements host-only lifecycle and
capture metadata. It validates exact pool slot addresses, canonical zero/sign
extended KSEG0/KSEG1 aliases, the two arena boundaries, relative40-byte matrix
alignment, active state, cursor progress and changed/new-allocation ownership.
Ambiguous unchanged pointers are left untracked. Distinct record generations
claiming one physical matrix make that matrix untracked rather than guessing.
Allocation generations and scene epochs receive monotonic nonreserved32-bit
IDs, including the two camera IDs from the same namespace. IDs never wrap or
silently reuse after free; exhaustion is explicit. This identifies an actual
render-record lifetime; it does not assert a decoded roster-player/bone number.

A frame token selects a particular arena build. Published
`TransformTaskSnapshot` objects own immutable matrix/tag maps, camera IDs,
scene token, epoch and task root. Free/reallocation, next-frame capture and
scene changes cannot alter an already published snapshot. The submission
fingerprint includes normalized data_ptr, data_size, ucode and ucode_data.
Non-graphics tasks never enter the metadata queue; untracked graphics tasks
enter with an empty snapshot and zero camera IDs. A fingerprint mismatch,
missing metadata or a second graphics producer quarantines tracking permanently
until an explicit reset while the upstream queue is stopped and drained.

The ordering contract follows inspected pinned source:

- `librecomp/src/sp.cpp`, `osSpTaskStartGo_recomp`, is the sole upstream caller
  of `ultramodern::submit_rsp_task`.
- `ultramodern/src/events.cpp:565` copies the OSTask into a graphics action;
  its graphics worker passes that copied task to `send_dl` at378.
- The project must serialize metadata publication **and** the actual upstream
  submission in one external submission mutex; internal tracker locking alone
  cannot serialize a different queue's enqueue.
- The pinned moodycamel queue has implicit per-thread producer streams;
  `ConcurrentQueue::try_dequeue` chooses producer streams heuristically. A
  mutex across different producer threads does not imply global FIFO. The
  tracker therefore pins the first graphics producer's actual std::thread::id
  and quarantines tracking if another graphics thread submits. Audio can come
  from another thread without changing this contract.
- The original compiled direct-call inventory finds only8001DCB4 calling
  osSpTaskStartGo8005D88C, inside scheduler helper8001DC5C, called by
  scheduler event handlers8001D624/1D724/1D814/1D90C. This supports the normal
  single graphics-producer path; the host thread check enforces the assumption.

The renderer consumes the front fingerprint and exact internal sequence token;
it must never select a map by a reused data_ptr alone or scan mutable guest
object pools. Frame-to-task binding still needs a validated display-list bank
probe at the publication boundary. Synthetic C++ tests cover bank alternation,
recursive cursor advance, malformed addresses/bounds, ambiguous ownership,
allocation reuse, immutable old tasks, scene/camera ID changes, repeated roots,
audio interleaving, all fingerprint fields and actual second-thread quarantine.
They execute no original game instructions and do not validate visual quality.

## Private real-engine evidence (PAL acceptance)

The pinned RT64 workload configuration explicitly caps a manual target to the
swapchain's detected refresh rate (`rt64_workload_queue.cpp`, lines 225–227).
Consequently a 120 option on the available 60 Hz display requests 120 but uses
an effective target of 60. The engine's conditional sampling supports higher
rates when the detected display supports them; this source fact is not physical
120 Hz acceptance. The cap, VI cadence, simulation, and presentation buffering
remain intact.

`tools.prepare_render_evidence` emits private copies of the pinned workload and
present queue sources. It checks both original SHA-256 digests and refuses to
overwrite modified output. The copies only add opt-in callbacks after the real
GPU render completes and after each actual swapchain presentation API call.
Build these with `ISS2000_ENABLE_RENDER_EVIDENCE=ON`. Source and generated hashes
are retained in the private output's `receipt.json`; dependency checkouts stay
unchanged. The renderer never draws a diagnostic HUD or a controls footer.
Original button prompts continue through the game's own text/sprite consumers.

Enable logging before launch with `ISS2000_RENDER_EVIDENCE=/absolute/path.jsonl`.
For a bounded pixel comparison also set `ISS2000_RENDER_EVIDENCE_GPU=1` and
`ISS2000_RENDER_EVIDENCE_GPU_GATE=/absolute/capture.flag`. Start with that flag
absent, then create it when original field motion is visible. The gate prevents
title/menu renders from consuming the 240-readback limit. Use original internal
resolution and MSAA off for the first evidence capture; then verify the desired
resolution separately. Full-resolution GPU readback affects timing and can make
RT64 skip additional frames, so this mode is not a performance benchmark.

Each `render` row records the actual workload/present IDs, sample index,
planned samples, current/previous weights, effective/original rates, and RT64's
frame-matching state. When requested and supported, the diagnostic copies the
completed, single-sample offscreen color texture to a real Vulkan readback
buffer, waits for completion, invalidates host memory, and records its pixel
SHA-256 and dimensions. The image returns to its previous layout before ordinary
presentation proceeds. Swapchain images lack transfer-source usage in this
pinned backend and are deliberately not read this way. Failed/unsupported
captures have an explicit status and no invented hash.

`display_list` rows separately record immutable snapshot sequence/scene/epoch,
bridge installation, and selected camera/model/inherit/ignore group counts.
These establish whether the adapter is eligible and assigning identities; their
asynchronous timestamps do not establish exact pixel-to-task attribution.
`present` rows report actual API success, not proof of physical scanout.

Summarize a real log using
`python3 -m tools.analyze_render_evidence /absolute/path.jsonl`. Different pixel
hashes at distinct weights within one matched workload, including a fractional
weight strictly between 0 and 1, demonstrate a distinct GPU intermediate for
that workload. A configured rate, repeated hashes, unmatched frames, two hashes
from unrelated workloads, or the analysis unit fixtures do not supply that
proof. The analyzer always leaves physical 120 Hz unproven. A real 120 Hz display
and visible match/goal/pause/replay acceptance are still required for that claim.

## PAL VI framebuffer identity and original cadence correction

Root's first correctly identified PAL boot reached original title/demo rendering,
but its captured display showed green/magenta stripes. The independently saved
native-word-swapped snapshot `.local/pal-acceptance/title04.rdram` decodes cleanly
as RGBA16 at actual buffers `27D380`, `32D000`, and `307800`. These are later demo
pixels, not a claim of exact temporal correspondence with title screenshot 62.
Original ROM hashes, relevant instruction checks and the snapshot digest are
pinned in `.local/pal-vi-review-01/proof.json`.

Original PAL initializer `8000164C` deliberately writes field origin `519` to
both field records. The observed VI origin `27D899` is therefore the actual
framebuffer `27D380 + 519`. Upstream RT64 `VI::fbAddress()` assumes an offset of
one row for this mode, subtracts `320*2`, and incorrectly classifies `27D619` as
the framebuffer base. That odd address misses the known GPU framebuffer and
causes the RAM fallback to interpret shifted pixel bytes. A later observation
similarly produced `32D519` from actual framebuffer `32D000`; a fixed buffer
address is not an appropriate correction.

The PAL VI adapter now records the actual next-state framebuffer together with
its final physical VI origin, width and pixel size. A bounded host registry
retains 256 identities so copied, queued VI observations can resolve their
original framebuffer. Invalid ranges are ignored and conflicting identities
for one key are quarantined. The private, hash-pinned `tools.prepare_rt64_vi`
copy first queries that registry from `VI::fbAddress()`; unknown keys retain
upstream behavior. Guest memory, original field-origin values, all physical VI
registers and VI geometry remain unchanged. The host does not guess a buffer
from the captured title or apply a universal `519` subtraction.

A separate upstream assumption affected interpolation: `VIHistory` used a fixed
60 Hz base even for PAL. The same private VI copy derives the base from the
actual recorded vertical sync: the original PAL 624/625-line modes use 50;
NTSC 524/525-line modes use 60. Existing factors continue to select original
logical cadence (for example, PAL factors 1/2 yield 50/25). This does not advance
the simulation or lift the physical display-rate cap.

A focused compiled test uses the actual pinned RT64 `VI` implementation: its
unadapted version reproduces the wrong address, while the private adaptation
resolves the exact registered buffer, preserves the raw origin, and returns
50/25 and 60/30 for PAL and NTSC factors. This is a host VI test, not a game
execution or a claim that the visible corruption is already corrected. Root's
next visible acceptance run must establish the latter.
