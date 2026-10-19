# PAL native HIGH steady-field pace

Original project work: djultra64. Original inputs remain private and unchanged.

Actual hidden Linux Training observations exposed a resolution-dependent timing
error. In the same controllable Free Training scene `0604`, original LOW admitted
126 stage, actor and ball updates in 5.005016505 seconds. Original HIGH admitted
252 in 5.003645 seconds. Both were mode 4 and unpaused. These observations are
private `.local/training-timing-01/samples.jsonl`; the HIGH CPU snapshot is
`free-training-high.rdram`. They establish the approximately twofold difference
in that tested build, rather than an unbounded LOW execution loop.

Original PAL frame driver `80000C30` calls stage dispatcher `80002D90` at
`80000D34`. Its HIGH branch calls it again at `800010C4` when working resolution
byte `8013B42A` equals 1 and fade counter `8006CE70` equals zero. In scene `0604`,
the genuine dispatch chain is `80002D90` to `80003410`, `80053A80`, `80053DF8`,
and actor dispatch `801E64A8`. `80053DF8` increments halfword `8013B442` after an
admitted unpaused step. Training skips match-clock tick `801DC14C`; changing that
clock cannot repair this twofold Training update count.

Reviewed movement initialization and integration keep the same original PAL
coefficients in HIGH and LOW. In particular, `802C932C` adds full velocity
components to the player position, and ball vertical integration `802B6D60`
adds full vertical velocity and subtracts full gravity. The second stage pass
is not demonstrated to be a fractional physics step.

`tools/prepare_pal_native_pace.py` produces a private derivative named
`iss2000_pal_native_frame_pace`. It authenticates the complete PAL ROM, original
frame instructions at ROM `1830`, size 1272, and the exact translated source.
The original instruction body SHA256 is
`6fac9fbf788c9a44cc3c11713a6e087ff764fee0c777a458f749f13f31113935`;
the source SHA256 is
`0ea1d11a153c80b2deaa2076313cb227bbba7c03a2ce09cdfd4fb5f6be3c8136`.

The second dispatcher call and its paired skeletal update are conditionally omitted. The original frame
pointer must equal `8013B418`, working HIGH must equal 1, and stage/substage must
be `6/4` both at function entry and immediately before the duplicate call.
Every first pass remains original. Other scenes, changed resolutions and scene
transitions retain the original second-call decision. HIGH framebuffer and VI
selection, controller reads and SI waits, the first skeletal update `80031E74`
at `80000E54`, both `80001128` camera/replay calls, audio, rendering and the
surrounding frame instructions remain intact. The duplicate skeletal call at
`800010CC` uses the same captured admission decision as `800010C4`; a stage
transition during an admitted original second step cannot accidentally separate
that step from its skeletal update. The guard covers Training and other modes sharing
steady scene `0604`, including its pause and replay states. It makes no global
claim about all HIGH menu or transition animation rates.

The focused CPU regression compiles five independently hash-pinned genuine PAL
frame/stage translations and the derivative against actual HIGH Training RAM.
External rendering/input calls and actor leaves are explicit observed counters;
no substitute physics or synthetic rendered-frame evidence is introduced.
The test first reproduced two calls where one was required. With the guard it
verifies modes 0/4/9, paused and replay states, the original stage counter, complete
call ordering outside the duplicate closure, LOW preservation, fade gates and
scene/resolution/pointer transitions. Source/ROM rejection, exact output hashes,
Windows strong-entry declaration, LF bytes, idempotence and tamper rejection are
also checked.

The linked runtime selects the derivative only under the exact original
`80000C30` function identity. The production lookup regression also verifies that
an unrelated function at the same guest address, a missing active function and
other address aliases cannot receive this adaptation.

## Hidden Linux translation-cadence acceptance before skeletal correction

Build 43 subsequently completed the same genuine Free Training route with the
correct original HIGH request enabled. Its executable SHA256 was
`32cc414eb7e12a002e3da04d4012a0376704b028f339fc4163631d8df36b6a11`.
The last build-43 record in the private timing samples measured **125 stage,
actor and ball updates in 5.004120655 seconds**, approximately 25 updates per
second. Both endpoints were mode 4, scene `0604`, working HIGH 1 and unpaused.
The three counters advanced together: stage 1875 to 2000, actor 825 to 950,
and ball 859 to 984. The earlier uncorrected HIGH sample advanced all three by
252 in approximately five seconds; the LOW reference advanced them by 126.
The corrected HIGH observation therefore agrees with the LOW reference cadence
within the samples' one-update endpoint resolution.

The original boot path detected 8 MiB, requested HIGH while retaining the original
LOW startup buffers, and naturally switched to working HIGH before this sample.
These are separate bytes: detected memory `8013B429`, working video mode
`8013B42A`, and HIGH request enable `8013B42B`. During the completed HIGH field
capture the working dimensions were 640 by 544 and packed word `8013B428` was
`20010101`. The private completed snapshot is
`.local/training-timing-01/free-training-high43-completed.rdram`; capture 378
records the actual HIGH image. A saved language preference or a startup request
alone would not establish that the measured field was actually running HIGH.

PAL VI scheduling remains 50 fields per second. In this observed steady field,
the corrected original driver admits one complete simulation pass per rendered
task, producing the measured approximately 25 full updates per second instead
of the HIGH duplicate's approximately 50. This establishes the tested native
translation-cadence correction; it does not establish animation speed or claim a physical display refresh rate, global
25-Hz behavior for every scene, or complete NTSC gameplay equivalence. Normal
match movement and match-clock comparison against an actual NTSC baseline,
other training exercises, and runtime pause/replay timing still require their
own acceptance evidence. Their CPU guard/call-order coverage is distinct from
this real unpaused Free Training measurement.

## Skeletal phase regression and paired correction

Subsequent user feedback identified fast running/foot animation despite the
accepted translation cadence. The initial regression preserved the two calls to
`80031E74` because its external observer did not execute that closure. That
function is not a read-only geometry synchronization: it walks 35 model states
at `801A07CC`, stride `100`, calls `800300D0`, and optionally bakes the resulting
pose through `8002FC14`. The original `800300D0` animation-command parser calls
`8002F448`, which advances phase float `state+84` by `state+DC` toward `state+D8`,
using `state+D4` and original endpoint/script rules. Maximum-detail rendering
retains this original phase parser.

Executing the genuine frame and skeletal closure against completed build-43
Training RAM reproduced the mismatch. For captured model state `801A08CC`, LOW
advanced phase from `9.19998169` to `10.3999786`, a delta of `1.19999695`. The
then-current HIGH derivative advanced it to `11.5999756`, a delta of
`2.3999939`, although both paths admitted exactly one stage update. Other models
also showed twice the progression or original endpoint clamping/wrapping.
Consequently the prior 25 actor/ball updates per second did not establish
correct skeletal timing.

The version-2 derivative skips the second skeletal pass only when it also skips
the second steady-field simulation pass. The first original animation parser,
pose bake and rendered geometry remain intact; animation coefficients and
keyframes are unchanged. LOW, nonsteady scenes, original fade gates and
scene/resolution transitions keep their original call sequence. The camera and
replay side effects in `80001128` remain untouched.

The expanded CPU regression independently pins seven additional original
function bodies/sources. It executes the actual original frame/stage and
skeletal phase closure, including the production maximum-detail derivative.
The final `8002FC14` pose bake is explicitly observed rather than executed, so
this regression asserts original phase/script timing rather than joint matrices
or rendered appearance. Across 25 consecutive native tasks, all 35 captured
states must match LOW for animation ID, phase, script cursor, range and step.
The unchanged HIGH path is a negative control and demonstrably differs. The
new test first failed on the retained second skeletal pass, then passed with
the paired correction; the focused suite contains five passing tests.

A trustworthy external reference was located: [LongplayArchive's PAL
longplay](https://www.youtube.com/watch?v=RyvlOSb-AZw) identifies the PAL edition,
and [Glenn Plant's original-console recording](https://www.youtube.com/watch?v=zUp281cPxkU)
identifies original N64 hardware and cartridge capture. These source descriptions
are provenance leads, not a measured animation-cycle comparison. Locally installed
Ares 148 now provides an independent original-ROM observation. The installed
Flatpak ran the same hash-verified PAL ROM with its original frame body unchanged,
Expansion Pak enabled, no fast-forward, private configuration/saves, and an
isolated headless 50 Hz compositor. Original menu input selected High and Free
Training; read-only RAM sampling observed working High `1`, scene `0604`, mode
`4`, unpaused. In an idle window, 252 actor/ball updates occurred over
5.045966 seconds; in a held original D-pad-right window, 252 occurred over
5.047231 seconds. Model state `801A08CC` changed phase 253/251 times respectively,
with median absolute same-clip phase increments `1.199996948`. Its displacement
was zero while idle and 304.220704 game units during the directional window.
All 19 model-record pointers remained stable across these observed poses.
Private receipts retain the samples, original RAM, frame-body identity, and
input/audio isolation checks.

This measures this Ares configuration, not physical N64 timing. It establishes
that unmodified High also advances simulation and animation together at about
50 updates per second. The PC's intended 25-update cadence therefore needs the
paired correction to retain the LOW relationship between displacement and pose;
the Ares High result alone is not the intended 30-animation-sample-per-second
anchor.

The same isolated Ares session then returned through the original pause/quit and
Options menus, selected LOW, and re-entered Free Training without guest-state
writes. Working High/request were both `0`, scene `0604`, mode `4`, unpaused.
LOW admitted 126 actor/ball/stage updates over 5.049594 seconds idle, and 126
over 5.047774 seconds with the same original D-pad-right input. Model state
`801A08CC` changed phase 126 times in each window; its median absolute same-clip
phase increment remained `1.199996948`. This directly anchors approximately
25 phase updates per second, or 30 animation units per second away from original
endpoints/script transitions. The model's 19 record pointers stayed stable.
Idle displacement was zero and directional displacement was 167.503437 game
units. The High and Low windows had different initial idle animations and
subsequent script histories, so their aggregate displacement is not an exact
matched-state physics ratio.

The original frame body in both reference snapshots is byte-identical to the
PAL ROM. The private Low receipt retains original menu captures, raw state
samples and RAM/hash evidence. Post-correction native wall-time pose and
bridge identity observations follow below. Exact matched-state displacement
and completed GPU fluidity are distinct checks; CPU phase agreement and the
Ares measurements must not be described as completing them.

## Post-correction native pose observation

Hidden development build 47 (executable SHA-256
`11dac0e91212b2f463fc1103209fed0c31980dd897f2e61434e3e89044cb7ffa`)
then completed a read-only live observation of genuine High Free Training.
The sampler inherited a read-only memory descriptor from the owned debugger;
the debugger continued normally throughout each measured window. No process
security policy, guest memory or animation coefficient was changed.

Idle admitted 126 stage/actor/ball updates in 5.047793 seconds; moving admitted
126 in 5.045721 seconds. Model state `801A08CC` changed skeletal phase 126 times
in each, with median absolute same-clip increment `1.199996948`, matching the
original Ares LOW cadence and per-update step. Different original scripts and
initial poses prevent describing these independent runs as bit-identical
matched-state trajectories. The separate genuine CPU closure regression is the
matched-state comparison.

The observed player's 19 render-record pointers stayed stable throughout both
windows. During movement all 19 local pose blocks changed, and every limb's
current matrix had 87–105 distinct values. This is evidence of articulated pose
updates beyond root translation. Live RAM sampling is not an atomic completed
render task, so these observations do not establish the transform IDs actually
selected by RT64, interpolation continuity across those IDs, or completed GPU
fluidity. The completed build-43 display-list audit separately shows all 19
matrices are loaded and all 18 child matrices own original rigid vertex batches;
the separate actual post-correction bridge-ID observation follows below.

## Actual post-correction limb interpolation identity

A separate read-only native build-47 debugger observer collected three complete
field render tasks, sequences 20416–20418, matrix banks 0/1/0 and scene epoch 68.
It decoded the actual immutable task snapshots and observed the actual
`RT64::RSP::matrixId` machine-entry calls. Each call's return address had to fall
inside this exact executable's bridge matrix callback, avoiding unrelated engine
calls. The probe measured the host ABI from the current project headers and
self-tested raw hash-table decoding and optimized SysV call registers on CPU
fixtures first. It used no debugger function calls or guest writes.

Every task contained all 19 records of player state `801A08CC`; all record/ID/
allocation-generation/epoch tuples remained identical. The root used ID 1492,
generation 6; the 18 child records used distinct IDs in 1474–1491, generation 1.
Each completed task actually selected those IDs in 91 bridge-origin model calls:
one root call and 3–9 calls for every child. Every observed call selected matrix
decomposition, position interpolation and rotation interpolation; vertex
interpolation remained SKIP. Skeletal phase advanced 9.199982 → 10.399979 →
11.599976 across these tasks. Their root position stayed constant: this is
changing-pose identity evidence, combined with the separate five-second moving
RAM observation above, not a claim that the three debugger-observed tasks also
had running translation.

Together with the original rigid-limb display-list audit, this confirms that
interpolation covers the articulated player's limbs rather than only the world
root. Global vertex interpolation is consequently not justified by this case.
The private `native47-limb-acceptance.json` pins the executable, headers, exact
probe, raw metadata/calls and all 19 identities. Debugger observation affects
cadence and is separate from the wall-time samples; it does not itself prove
completed intermediate GPU images or subjective smoothness after the pose fix.
