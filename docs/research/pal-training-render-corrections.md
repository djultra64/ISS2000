# PAL Training HUD, visibility and shadow characterization

Original project work: djultra64.

The r50 feedback is four separate observations. The High Training HUD and CPU
frustum corrections below are CPU-verified; integrated GPU acceptance remains
required. The shadow investigation establishes missing vertex interpolation,
not a verified explanation for every temporal artifact.

## Training bottom anchor

The completed original High43 frame has working video mode1, allocation640×544,
depth80700000 and game mode byte8012DE74=4. Its original PAL High VI mode at
80099040 produces **640×524 visible rows** under the pinned RT64 `VI::fbSize()`:
interlace halves the1280-byte stride, the field vertical interval67..588 gives
521 rows, then RT64 adds two filter rows and rounds to a multiple of four.
The original radar's bottom452 therefore appears at approximately932 of1080
output pixels, matching the user's capture.

A translation of28 original logical pixels is56 High rows. The radar ends at508
of524, an eight-logical-pixel inset (about33px at1080). Left/right player panels
receive the same translation relative to their previous -7logical offset,
resulting in +21logical. Their existing horizontal centers remain unchanged.
Only exact **High Training** receives this change. Ordinary matches, Low mode,
foreign objects and4:3 retain their previous behavior. Output720–2160 scales
this native inset proportionally.

Radar sprite0 is descriptor80259918, palette8006D718, segment list80261B44
(14×12B). Its complete168-byte segment digest is
`e4d87004cd8e844afe34e517e232d7dde65ac9f00563ca691067bd52750d1186`.
The exact original descriptor, palette pointer, layer11, kind1 and unit scales
are required before applying its balanced `PalHudScope`.

Moving only that sprite would leave player/ball dots behind. Original callback
**802A5290**, overlay ROM376010→802A4380, constructs the marker display list.
The actual High43 object is8014D6FC, with+24 pointing to802B4D68 and+7C to that
callback. Original802A5AAC creates it. The private double buffer starts802B4408,
stride960, selected by the original signed halfword8013B418. Its current cursor
is802B4400. Original flat world-to-radar producer **802A4DC0** emits exactly one
24-byte E4/E1/F1 rectangle per marker. Selected-player highlights pass through
802A5180→the same producer; the ball also uses it.

The native wrapper saves that private cursor, calls the exact original producer
once, then `align_pal_training_radar_marker` verifies the complete output,
private buffer bounds, High dimensions/emitter identity, flat projection and
Training owner before shifting only the two rectangle Y fields by224 quarter
pixels. UVs, derivatives, projected X, world coordinates and all original ABI
results remain unchanged. It does not scan vertex memory or modify simulation.
`test_pal_training_hud` executes the whole genuine802A5290 closure and proves
all23 marker rectangles move with their background, including highlights and
ball. Unknown topology/cursor/scene/video rejects without writes.

## CPU visibility matches the actual High projection

Pinned RT64 `WorkloadQueue::threadConfigurationUpdate` derives its source
aspect from the visible VI size, and its renderer uses target/source to expand
3D projection. For actual PAL High, `(16/9)/(640/524)=1.455556`. The previous
CPU helper multiplied by4/3, leaving its horizontal frustum approximately8.4%
narrower than the rendered view. This is a concrete cause of premature edge
culling.

`pal_widescreen_projection_scale` verifies the canonical frame owner, High
allocation/depth and complete original adjusted80-byte PAL High mode table,
then executes the same RT64 size calculation. The selected guest layout carries
this factor through angular limits, far extents and rotated world corners.
Vertical, near/far, original bounding radii and all physics remain original.
An unknown High table returns zero and fails before writes. Low retains its
previous4/3 correction: its live `osViSetYScale` is separate from the stored mode
table and is not guessed here.

`test_pal_culling_vi` extracts the pinned real RT64 `fbSize()` implementation and
executes genuine original80023604. A point atx±14/depth10 is inside the rendered
High view but was rejected by the old CPU frustum; the corrected original test
accepts it. Points atx±16, beyond the far plane or outside the unchanged vertical
frustum still reject. Original80023604 subtracts object+6C bounding radius from
absolute projected coordinates, so the original object-volume test survives.
The full4:3 RAM no-op, invalid layouts and far-test idempotence remain covered.

## Radar texture phase

The radar uses original material2 at8009CC20: one-cycle POINT, not material0
COPY. Its High rectangles have512/512 derivatives because the original engine
doubles destination geometry. The existing identity-sprite viewport correction
accepts1024/1024 and therefore excludes this High path. The two right goal-area
segments use U7D00=1000 with a512-texel mirror period, not a negative derivative.
Independent rounding of differently sized High pieces must be tested through
that exact mirror/POINT sampling path. The renderer-derivative owner is handling
this separate correction; the COPY edge fix must not be generalized blindly.

## Shadow state: proven and unproven

The max-detail near route800368E8→80036820→80036610 constructs ten articulated
quads (40 vertices,640 bytes) from the original pose. Only X/Z halfwords deform;
the fixed identity matrix801A3F00 does not encode that pose change. The draw list
80083AD0 loads28 vertices at segment5+0 and12 at+1C0. Original shadow materials
80083B90/C8 retain original alpha, primitive Z source and depth7FFF; their common
state enables Z compare/update with translucent Z mode. No depth-bias change is
justified by this static evidence.

The current generic transform bridge explicitly skips vertex interpolation.
Consequently CPU shadow deformation still updates at the original simulation
cadence while articulated player matrices can interpolate at output refresh.
`test_pal_shadow_geometry` executes the genuine complete near generator with
one original pose endpoint varied and proves40-vertex deformation, fixed
material/topology/matrix and unchanged original depth state. A bounded per-actor
vertex identity path requires allocation generations, scene/cut continuity,
immutable task metadata and both original VTX chunks; it must reject unknown
layouts. Actual temporal GPU observation is still necessary before claiming
the reported flicker is fixed.

### Bounded shadow vertex interpolation implementation

`pal_shadow_vertices` observes the genuine285-node pool's allocations/releases
and original per-bank frame boundary. Shadow constructor80037894 allocates
1280bytes for its two640-byte banks. Its metadata comes from the original
140×40-byte allocator8001E600/8001E64C at800A5250..800A7550;
8002B290 creates the reciprocal owner link. Recognition validates that complete
original relationship, original80037498 callback, enabled flags, either genuine
near material and the complete192-byte80083AD0 topology, including its terminator. It records no foreign
or stale callback result and changes no guest bytes.

Each original shadow lifetime and continuity epoch receives two unique IDs in
60000000..6FFFFFFF, one for each fixed28/12-vertex chunk. A process-wide bounded
atomic allocator never reuses them, including after reconfiguration; the generic
transform allocator is explicitly capped below this range. Release, actor-owner
changes, observed scene/phase boundaries and explicit cuts retire continuity.
Both banks carry separate frame observations. Submission freezes copies in a
bounded64-entry FIFO paired by the exact task fingerprint under the existing
submission lock. Unknown microcode/frames produce paired empty entries; a
mismatched consumer, multiple producer threads or queue overflow quarantines
matching rather than searching by reused task address. Already submitted
snapshots retain their immutable actor lifetime.

`RT64ShadowBridge` installs only F3DEX2 VTX callback01 after the existing matrix
bridge. It accepts the current snapshot's exact28/12 loads at destination0,
while the original identity matrix801A3F00 and perspective projection are active.
Only vertex position interpolation is enabled; rigid components, UVs and tile
interpolation remain skipped. RT64 needs a fresh world-transform record for the
new group, so the bridge explicitly marks the unchanged MVP dirty before calling
the original VTX callback once. It then restores the prior group and marks the
MVP dirty for subsequent unrelated vertices. The same restoration applies if the
original callback throws. Callback maps are restored on scope exit; nested or
foreign bridges decline. The MenuSpriteBridge owns disjoint rectangle callbacks.

Verification covers the genuine original40-vertex generator; real completed
frame metadata; both banks; generations, cuts and saved snapshot lifetimes;
foreign topology, owner, spans, task/queue mismatch and producer-thread changes;
and exact VTX callback group/exception/nested-scope behavior. The new bridge also
compiles against the actual pinned RT64 headers with the game's existing compiler
flags. The callback fixture models the adapter boundary; it is not a replacement
for temporal GPU verification. Original depth commands remain unchanged.


### Follow-up: exact original primitive-depth translation

The user's r51 video `2026-10-15 21-25-22.mp4` is a1920×1080,
60fps desktop recording lasting34.917s. Consecutive final frames33.0–33.5s
show foot-shadow lobes disappearing and returning while the nearby player and
touchline remain visually stable. This establishes localized temporal shadow
coverage loss. The recording has no depth readback, so penetration into the
pitch and exact GPU causality cannot be distinguished from those pixels alone.

A bounded offline walk of the genuine completed High43 task at800D0328 follows
5572 commands, including nested lists, original segment updates and both known
microcode loads. Its three executions of the common near-shadow primitive-depth
command80083AE8 all have the same real state: other-mode low005049FC,
high0098ACE0 (two-cycle), combiner00FFFFFF/FFFDF6FB, black primitive color with
alphaAA, and original EE parameter7FFF7FFF. Recognition therefore uses the
observed two-cycle path; it does not assume a one-cycle material.

The defect is an exact representation mismatch. Pinned RT64
`RDP::setPrimDepth` divides the original15-bit7FFF by32767, yielding1.0.
Its raster vertex shader places that primitive at clip Z=W and its normal
Z-compare pipeline uses strict LESS. Equality with cleared maximum depth then
rejects mathematically. Floating rasterization and perspective division can
change coverage around this boundary; their role in the supplied video's
individual holes remains an inference pending GPU observation.

Original RDP primitive depth has three fractional bits. The primary
[parallel-rdp primitive setter](https://github.com/Themaister/parallel-rdp/blob/master/parallel-rdp/rdp_renderer.cpp#L3226)
and [depth interpolation](https://github.com/Themaister/parallel-rdp/blob/master/parallel-rdp/shaders/interpolation.h#L119)
map7FFF to18-bit3FFF8, seven units below maximum3FFFF. Its
[depth compression](https://github.com/Themaister/parallel-rdp/blob/master/parallel-rdp/shaders/z_encode.h#L26)
and [depth writeback](https://github.com/Themaister/parallel-rdp/blob/master/parallel-rdp/shaders/memory_interfacing.h#L519)
retain that nonmaximum value. The
[translucent depth comparison](https://github.com/Themaister/parallel-rdp/blob/master/parallel-rdp/shaders/depth_test.h#L109)
accepts a fragment in front of stored depth or against stored maximum. After
the first shadow writes3FFF8, another equal shadow fragment is rejected.
Changing LESS to LESS_EQUAL would lose this overlap distinction and can darken
overlapping articulated quads.

`RT64ShadowBridge` now recognizes only the exact physical80083AE8 EE command,
complete192-byte original near list, current immutable604 shadow metadata,
perspective projection, verified two-cycle material, exact low other-mode,
combiner, blackAA/64 alpha, and original decoded1.0/dz. It calls the original
EE callback once and translates only that primitive Z to
`(32767 << 3) / 262143 = 0.9999732962`. This is the original fixed-point depth
expressed in RT64's18-bit UNORM domain, matching RT64's own D16 depth-image
decoder. Guest commands, vertex geometry, alpha, dz, LESS comparison and depth
writes stay unchanged. Depth recognition operates with Original refresh as well
as enhanced output; vertex interpolation still follows the user's setting.

Original E2 pixel-source reset runs once before the bridge restores the scalar
and marks PrimDepth dirty. Scope exit and exceptions also restore the owned
RDP stack slot, including when another slot is current; foreign slots are not
written. A later foreign EE takes ownership of its original result. RT64 copies
stack parameters into `drawCall.rdpParams` at the first triangle, then copies
that draw call during flush. The pending shadow therefore retains its translated
depth while the next ordinary draw reloads original1.0. This adds no per-triangle
flush, shader variant, pipeline cache, dependency/header change or guest write.

The regression first failed on pinned RT64's1.0 conversion, then passed with
the bounded bridge. A second RED case used the genuine task's two-cycle state
to catch and remove an initial one-cycle assumption before release. It executes
the actual pinned GBI EE decoder, RDP depth conversion, D16 decoder,
`State::checkDrawState` and PrimDepth load branch, with small API fixtures for
the other state machinery. It proves first-clear pass, equal-overlap and closer
blocker rejection, unchanged original bytes, consecutive shadow/ordinary call
parameter copies, alphaAA/64, refresh-independent matching, foreign material,
wrong topology/scene/epoch/source/primitive rejection, nested scope, exception
cleanup, foreign EE replacement and owned-slot restoration. Existing original
40-vertex generation, metadata lifetime and vertex/group tests also pass. The
bridge compiles against the actual pinned RT64 headers with the game's build
flags. These CPU results establish the translation correction; visual flicker,
self-overlap raster precision, and gameplay acceptance remain the user's manual
test. No game or GPU execution was performed for this follow-up.


## Shared field bottom anchor after the r54 screenshot

This update supersedes the earlier Training-High-only placement above. The
original radar, complete player plates, both text objects and all radar markers
now share a mode-specific bottom placement in ordinary field and Training.
Horizontal origins and centers are unchanged. The clock's vertical offset is
zero rather than its previous three logical pixels: approximately eight pixels
higher in the reported High 720p capture.

The requested radar bottom is approximately 698 of 720 visible pixels. The
original High radar ends at native row452; adding224 RDP quarter pixels moves
it to508, or720*508/524 =698.015 visible pixels. Low already ends at226 of232
visible rows; applying the same positive translation would clip it. Its bounded
-4-quarter-pixel translation ends at225, or720*225/232 =698.276 pixels. The
complete player groups receive the identical translation relative to their
prior -7-logical-pixel offset: High168 quarter pixels; Low-32 quarter pixels.
No extra downward shift is added to the already-corrected Training High path.

The reported1280x747 color allocation is consistent with544 High canvas rows
scaled by720/524 and rounded. Its VI still presents720 visible rows. Likewise,
Low240 rows produce a745-row color allocation through720/232. The allocation
height is not the visible framebuffer height and is not used to move the HUD.

`align_pal_radar_marker` accepts the exact original flat802A4DC0 and projected
802A4F78 producers. Both native wrappers call their original once before the
helper. In addition to the unchanged radar descriptor and168-byte segment-list
digest, it verifies root802B2950 belongs to the original live root pool, owns
callback802A5290, and points to the selected private960-byte list. Exactly one
24-byte E4/E1/F1 output must have the original8x8-logical size and Low1024 or
High512 derivatives. The helper then changes only its two Y fields. All original
world projection, UV, derivative, color and simulation data remain intact.
Unknown topology, owner, cursor, projection mode or overflowing geometry rejects
transactionally. 4:3 remains unchanged.

The expanded regression first failed on ordinary field radar placement before
this change. Five focused HUD tests now pass in19.346 seconds. The marker test
extracts both actual native wrappers and executes the genuine802A5290 CPU
closure across all16 Low/High, ordinary/Training, flat/projected and private-bank
combinations. Every emitted player, highlight, target and ball rectangle receives
the same offset; outside those Y fields, full8MiB output equals the original.
The genuine sprite/font test includes the fourteen-piece radar background and
retains original rectangles, UVs, derivatives and materials inside the balanced
scope. Existing score-flag, clock variant, viewport and 4:3 checks also pass.
No game process or full application build was run for this correction. Actual
GPU layout acceptance and the separately investigated mirrored radar seam remain
separate verification work.
