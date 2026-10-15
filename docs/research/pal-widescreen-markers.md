# PAL widescreen marker calculations

Original project work: djultra64. Source/static verification, not visual acceptance.

The original forward projection, reverse edge-to-world query and orientation
calculation must use the same local target aspect. Merely widening the camera
frustum leaves the original marker threshold/clamping path at 4:3. These three
PAL functions have unique complete instruction-shape matches to the independently
classified US consumers, with concrete original PAL aspect loads from 8009DF00:

| PAL function | Role | Original aspect-load PC | Float register |
| --- | --- | --- | --- |
| 80255A6C, overlay4A6820 at80230590 | Forward normalized position, visibility/edge threshold and derived extent cache | 80255B74 | f2 |
| 802554EC, same overlay | Reverse marker coordinates to world query | 802555E8 | f20 |
| 80044814, resident | Marker orientation after reverse query | 80044994 | f14 |

Private body matching evidence: `.local/pal-marker-01/body-matches.json`. Exact
source hashes and reviewed PCs/registers are pinned in the PAL profile's
`render-patches.json`. `tools.prepare_render_sources` checks the original map's
ROM identity, original generated-source hashes and the unique original load,
then inserts a C call after that load in a separate private derivative. Original
CPU source and ROM files remain unchanged. A receipt records original/output
hashes; CMake substitutes only those three source objects.

The callback changes a local 4:3 aspect value to16:9 only when widescreen is
selected. All other values pass through. It does not mutate the guest aspect
global, reserve guest memory, change projection matrices or change simulation.
RT64 remains the sole projection owner; original screen-relative 2D construction
keeps its original 4:3 policy. Forward, reverse and angle computations therefore
share nx=x/(vertical_extent*aspect), inverse x=nx*vertical_extent*aspect and
atan2(nx*aspect,ny). Original code still performs its layout, thresholds, cache
updates and world intersection work.

Tests verify paired coordinate/angle consistency and that preparation alters
only the reviewed load result while preserving every other generated line.
Actual marker positions, corner states, menus, replay cameras and live aspect
changes still need later visible acceptance; these source checks do not replace
that evidence.
