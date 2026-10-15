# Original camera, visibility and 16:9 research

Original project work: djultra64. Checkpoint: 2026-10-15.

This continues [rendering.md](rendering.md) with original game-side visibility
proof and narrow native helpers. The user prioritizes 16:9, then resolution,
then interpolation; gameplay acceptance runs are postponed. This task did not
execute the game, change guest instructions or modify renderer/bridge wiring.
Synthetic mathematics and an existing paused memory capture do not establish
visually verified widescreen gameplay.

## Submitted camera and RT64 correction

The supported ROM SHA-256 remains
`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`.
Private evidence is `.local/widescreen-evidence/paused-match-01.json`, generated
by `probe_widescreen.py` from the existing
`.local/team-visual-assets-01/paused-match.rdram`. It records input hashes and
walks display-list root `0x800D2C08`, including segmented nested lists, with
bounded depth/iteration checks. No input is modified; output creation is exclusive.
The probe is specific to this known original F3DEX2 capture, not a general
validator for every possible microcode or branch command.

The captured fields are:

| Guest location | Captured value | Original ownership |
| --- | --- | --- |
| `0x800A07E8` | `1.333333373` | Aspect; setter `0x80024D48`, initial store `0x8002A9D4` |
| `0x800A07D4` | 15 | Field of view; setter `0x80024D38` |
| `0x800A09FC` | 10 | Near bound |
| `0x800A07A4` | 2600 | Far bound |
| `0x800C43A0/0x800C43E0/0x8013DE78` | Diagonal X `5.696807861`, Y `7.595748901` | Original fixed perspective buffers |

The matrix diagonal ratio is `1.333334226`, including fixed-point quantization.
The builder at `0x8005B630` computes horizontal `cot(fovy/2)/aspect`
(`0x8005B6C8`) and stores X/Y coefficients at `0x8005B6EC/0x8005B6E0`.
Fixed-matrix wrapper `0x8005B7E0` is called at `0x80024CA0/0x80024D24` by
`0x80024C3C/0x80024CD4`. Preserve these guest matrices at 4:3 when RT64 owns
projection correction.

The paused list has 4,424 walked commands, 187 matrix operations, seven viewport
and seven scissor assignments. Every captured viewport/scissor is
`(0,0,320,240)`. Three perspective loads (`DA380007`) at
`0x800D3518/0x800D3C98/0x800D4478` use `0x800C43E0`; subsequent projection-stack
multiplies (`DA380005`) use camera matrix `0x800CECA8`. The multiply's raw diagonal
ratio is not another perspective aspect measurement.

Pinned RT64's `src/hle/rt64_workload_queue.cpp` derives source aspect from VI
framebuffer dimensions, sets the exact manual target, and uses
`resolutionScale = {multiplier * target/source, multiplier}`. In
`src/render/rt64_projection_processor.cpp`, AUTO corrects a projection when the
viewport/scissor intersection covers the framebuffer-pair width, is landscape,
and has no custom viewport origin. It scales the horizontal projection column
by `source/target`. The captured full-frame layout satisfies that geometric
criterion for its normal 4:3 source. With target 16:9 the factor is 3/4: wider
horizontal field of view, unchanged vertical perspective, rather than a stretch.

Use Manual 16:9 and extended aspect Original for the initial policy. Do not
also change guest aspect to 16:9: it would double-correct submitted perspective
and, as shown below, move some CPU limits in the wrong direction. RT64 does not
recover objects that the CPU declined to submit.

## CPU horizontal and vertical axes are independently proven

Original `0x80022E58` copies three camera basis rows into
`0x800AA0E0..0x800AA100`. The paused snapshot contains:

| Row | Vector | Consumer |
| --- | --- | --- |
| Horizontal `0x800AA0E0/E4/E8` | `(-0.14454554, 0, -0.95839399)` | First transformed dot product |
| Vertical `0x800AA0EC/F0/F4` | `(-0.23590429, 0.93941242, 0.03557922)` | Second transformed dot product |
| Forward `0x800AA0F8/FC/100` | `(0.95839399, 0.24614541, -0.14454554)` | Third dot product / depth |

In `0x80022FD4`, the object position minus camera position is dotted with these
rows. The routine takes absolute first/second components and tests:

- Horizontal: `0x800230C0` loads `0x800A0984`; `0x800230C4` multiplies it by
  depth; `0x80023130/0x80023134` compare this against the first absolute dot
  product minus radius.
- Vertical: `0x800230E8` loads `0x800A08D0`; `0x800230F0` multiplies by depth;
  `0x8002311C/0x80023120` compare it against the second absolute dot product
  minus radius.
- Near/far comparisons remain separate at `0x800230E0..0x80023114`.

`0x80023150` has the analogous cached-basis rejection path. `0x800261D0` also
consumes `0x800A0984/0x800A08D0`. These are actual CPU rejection limits, rather
than only shader coordinates.

`0x80022E58` builds horizontal angular extent `0x800A0984` and vertical angular
extent `0x800A08D0 = horizontal / originalAspect`. It also builds the cached
pair `0x800AA104` and `0x800AA108 = first / originalAspect`, used by a separate
point test. The captured pairs are respectively
`0.1583844423 / 0.1187883317` and `410.7557983 / 308.0668335`.

Changing only global aspect to 16:9 would make the divided vertical terms
smaller while keeping the horizontal terms unchanged. The proven correction
is to multiply horizontal terms by 4/3, preserving the two vertical terms,
field of view, near/far, camera basis and camera position.

## Reviewed native boundaries and alternate writer

| Boundary | Original evidence | Narrow correction |
| --- | --- | --- |
| After `0x80022E58` | Direct call at `0x8002AE58` inside camera driver `0x8002ACAC`; builder returns before object iteration | Scale `0x800A0984/0x800AA104` by 4/3 |
| Before `0x80022760` | Reads `0x800AA104` at `0x80022848`, vertical partner at `0x80022858`, before point rejection | Ensure cached horizontal pair is wide exactly once |
| After `0x800243E0` | Called at `0x8002461C` by `0x800245F8`, before bounds are consumed | Widen rotated corner pairs as below |

An aligned whole-ROM direct-call scan found the listed callers; this does not
prove absence of indirect calls. All these functions are resident and have
original translated bodies in map 04.

The alternate writer `0x800228D0` stores the cached pair at
`0x800229E8/0x80022A6C`. Its direct caller is `0x80022E08` inside
`0x80022D14`, which immediately branches on the returned result at `0x80022E10`.
The writer itself performs rejection by repeatedly calling `0x80022760`, for
example at `0x80022B34/0x80022B4C`. **A correction after `0x800228D0` returns is
too late for its current decision.** Preparing the pair before `0x80022760`
covers this writer and the other caller `0x80022B9C` while preserving the
original decision function. Repeated corner calls must recognize an already
corrected pair without multiplying it again.

## Rotated world corners

`0x800243E0` creates four camera-local rays:

```text
horizontal: [+h, -h, +h, -h]
vertical:   [+v, +v, -v, -v]
depth:      [-1, -1, -1, -1]
```

Stores `0x80024494/49C/4A4/4B0` establish horizontal signs;
`0x80024498/4A0/4AC/4B4` establish vertical signs; `0x80024470..47C` establish
depth. The common basis transform at `0x80024534..0x800245C4` rotates these
rays in place into arrays X `0x800C5D3C`, Y `0x80177ED0`, Z `0x801A2FF0`.
There is no per-corner camera translation in this loop. Their addresses then
name world components; scaling the X array alone would be incorrect.

The horizontal pairs are `(0,1)` and `(2,3)`. For each three-dimensional pair
A/B, preserve midpoint `M=(A+B)/2`, multiply half-difference `(A-B)/2` by 4/3,
and reconstruct A/B. This preserves their common vertical/depth contribution
and widens only the camera-horizontal component, regardless of camera rotation.
It must follow the original rebuild each time. `0x800245F8` consumes these rays
at `0x8002468C/0x8002469C/0x800246AC` and later iterations to derive world-space
bounds; its callers are at `0x800249D8/0x800249F8` inside `0x800249B8`.

## Implemented pure helpers and validation limits

`src/runtime/widescreen_culling.*` supplies four small APIs, each taking
`std::span<uint8_t>` native-word-layout RDRAM and a `bool wide`, returning success:

- `apply_widescreen_culling`: after the original angular/cached builder; changes
  only the two proven horizontal floats.
- `apply_widescreen_far_extents`: low-level operation on a freshly original
  cached pair. It is not a sufficient post-`0x800228D0` fix.
- `ensure_widescreen_far_extents`: before original point rejection; accepts either
  an original 4:3 pair (scales once) or already-wide 16:9 pair (no mutation).
- `apply_widescreen_world_corners`: after original corner rebuilding; changes
  only the twelve ray component floats.

Original mode is a byte-exact no-op. Wide mode requires exactly 8 MiB RDRAM,
finite expected original aspect, positive finite applicable scalar extents and
consistent original pairs; arithmetic overflow rejects before mutation. The
corner helper rejects nonfinite/degenerate/non-parallelogram rays. Original
scalar ratio checks prevent accidental repeated application; the corner helper
requires the documented original rebuild, since rectangle symmetry alone cannot
identify a previously widened rectangle. No helper changes guest aspect,
projection matrices, simulation state or a visibility return value.

All eight focused native synthetic tests pass:

```sh
python3 -m unittest tests.test_widescreen_culling -v
```

Tests cover a point outside the original horizontal bound but within the wide
bound, unchanged vertical rejection, whole-buffer sentinel preservation,
nonfinite/negative/inconsistent input rejection, original refresh, alternate
cached writers with repeated corner tests, and a camera rotated about two axes.
The existing paused snapshot was also read into a private host vector and all
three recommended helper operations accepted it; unrelated bytes remained exact.
The copied angular pair became `0.211179 / 0.118788` and cached pair
`547.674 / 308.067`. Receipt: `.local/widescreen-evidence/helper-paused-copy.log`.
This did not run any original CPU function or alter the snapshot file.

Root wired the three recommended boundaries and reported build 18 passing,
without game execution. This establishes compile integration, not visually
verified enhancement. Root owns CMake/native hook integration.

## HUD, overlays and remaining camera coverage

Pinned `rt64_framebuffer_renderer.cpp` normally applies reciprocal aspect to
ordinary rectangle coordinates around the original framebuffer center, so
small HUD sprites keep their original shape/centered 4:3 layout. Extended aspect
Original does not universally disable rectangle stretching: full-width
rectangles, tile-copy paths and explicit STRETCH commands can bypass that
correction. AUTO projection processing also includes orthographic scenes;
it is not limited to 3D perspective. These cases need separate inspection.

The paused list establishes a full-width 3D layout, not coverage of every menu,
player marker, minimap, scoreboard, replay, split viewport or transition.
Keep original logical UI coordinates and hit tests until a specific element's
mapping is proven. Moving peripheral HUD elements later requires paired visual
and interaction changes with explicit origins, rather than changing every
sprite's X coordinate.

Other original aspect readers remain independently relevant: resident
`0x8001FC88` reads aspect at `0x8001FD7C`, divides at `0x8001FD9C`, transforms
vectors and calls `0x80020BE8/0x8002170C`; `0x80044184` reads it at
`0x80044304` for an appearance/size path. Overlay `0x4A9290` functions
`0x80259D1C/0x8025A29C` read it at `0x80259E18/0x8025A3A4` and multiply derived
terms. Their full mode/overlay ownership and effect on visible edges are not
established by the three proven boundaries above. Do not globally alter these
inputs or call all cameras solved.

Next non-execution checks can compare original and wide computed horizontal
bounds/matrices for fixed captures, audit hook order and inspect rectangle
categories. When the user resumes visible verification, compare the same scene
at 4:3/16:9: unchanged vertical framing/proportions, added field at both edges,
no prematurely culled players/pitch pieces, correct markers/HUD, camera options,
replays and transitions. Record any uncovered path explicitly; do not replace
its result with forced visibility. Resolution and interpolation remain separate
subsequent workstreams.


### Remaining consumers classified more narrowly

The following additional original instruction review refines the limits above:

| Reader | Concrete downstream behavior | Consequence |
| --- | --- | --- |
| `0x8001FC88` | Caller `0x800219E4` gates it on object flags `+0x28 & 0x1000` at `0x80021E18`, calls at `0x80021E24`. It multiplies object X/Y by depth/FOV-derived extents, rotates through camera basis, adds camera position, writes a transform through `0x80020BE8` and scales its columns through `0x8002170C` | Screen-relative object-to-world transform construction, not an independent visibility-return test. Retain original 4:3 inputs for centered original UI until its objects are identified |
| `0x8025A29C`, ROM alias `0x4A9290` | From camera eye/target distance and FOV, obtains one extent and an aspect-multiplied partner (`0x8025A3AC`), caches diagonal magnitude plus 50 at `0x80270650` (`0x8025A3DC`), then derives object fields `+0x54/+0x58`. Absolute coordinate comparisons against 1.2 at `0x8025A550/0x8025A568` set object flag `+0xC4 & 0x800` at `0x8025A578..580`; later comparisons against 1 update edge state | Camera-normalized position and edge/indicator behavior, with its own aspect-sensitive derived cache. The three culling hooks do not change it |
| `0x80044184` | Checks that flag and additional mode/state guards; passes `+0x54/+0x58` to `0x80259D1C` at `0x80044234`, updates another record's position, then computes an angle from `+0x54 * aspect` and `+0x58` (`0x80044304..320`), stores at `+0x68` | Couples camera-relative coordinates, position and orientation. It is not safe to correct only one displayed X coordinate |
| `0x80259D1C`, same alias | Uses camera eye/target distance and half-FOV, forms a second extent by multiplying aspect at `0x80259E20`, converts input direction/edge coordinates through `0x80259BDC`, builds rotations/transforms and calls intersection helper `0x80259950`, returns a boolean | Reverse direction/edge-to-world query consistent with the paired normalized-position path; no proven generic player-culling replacement |

The **offscreen indicator/marker** interpretation of the paired overlay and
resident paths is strongly supported by coordinate thresholds, flag ownership,
reverse projection and angle construction. Its exact visible asset, actor
classes and every mode are still unverified; this is more precise than calling
all remaining readers either visibility tests or ordinary HUD rectangles.
Direct callers of `0x8025A29C` occur in ROM aliases `0x289BA0`, `0x29A360`,
`0x4E2300` and `0x503B70`; `0x80259D1C` is called from `0x80044184` and
alias `0x389970`. A numerical guest address alone cannot identify the active
overlay's ownership.

A later marker correction needs paired forward/reverse coordinate policies and
cache invalidation when the target aspect changes, independently of the proven
CPU frustum limits. Do not set the aspect global, force the visibility flag, or
disable the original branch as a shortcut. The current APIs claim only the
three established horizontal-bound mechanisms.

### Settings transition lifecycle

The bridge must run each original builder before its post-helper. The scalar
pair check rejects a double application until original values are refreshed;
the corner helper relies on the original rebuild. The pre-point-test ensure
accepts already-wide values to support repeated tests and handles the alternate
writer's fresh pair before its current rejection decision.

Switching from wide to Original makes helpers no-ops; previously cached wide
limits can persist until the original builders refresh them. This is a
conservative excess-submission interval, not proof of a missing-object bug, but
immediate exact restoration has not been implemented by these helpers. Original
render projection remains unchanged throughout. Configuration-transition cache
refresh and independent marker caches need explicit lifecycle tests before
claiming complete 16:9 behavior for live settings changes.
