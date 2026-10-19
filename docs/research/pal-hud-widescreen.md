# PAL original-engine widescreen match HUD

Original project work: djultra64.

Current High Training refinement: radar background and all original player/ball
markers move down28 logical pixels; both player panels move by the same amount
while retaining their horizontal centers. Ordinary matches, Low and4:3 retain
the preceding placement. See [Training render corrections](pal-training-render-corrections.md)
for the exact visible524-row VI anchor, original marker producer and CPU tests.
The earlier placement descriptions below apply to the baseline/ordinary match.

The match HUD uses explicit screen origins for the score, clock and player
panels in 16:9. Original sprites, fonts, scale and UV commands are retained. The
radar stays centered. At 4:3, the helper makes no writes.

## Original PAL producers and identities

Original `8000924C` builds layer lists from sprite records at `8013C47C`, stride
`3C`, and text records at `801650DC`, stride `28`. Original `80041A44` dispatches
sprite kind 1 to `80041B50` and text kind 2 to `80048660`. Match initialization
`801E021C` constructs the HUD; `801E4EE0` updates the two player-name text records.
These addresses are recovered directly from the pinned original PAL revision.

| HUD group | Original sprite indices | Additional original path |
| --- | --- | --- |
| Left player panel | 1,3,4,7,9,11,12,20,24,25,26 | Name text `801650DC` |
| Right player panel | 2,5,6,8,10,13,14,21,27,28,29 | Name text `80165104` |
| Score | 30..35 | Flag emitters `8023A510`, called by compositor `8023A890` |
| Clock | 36..43 | Original animated face/hands remain in that group |

The score flags are separate from the normal sprite pass. The main original
frame builder calls `8023A890` at `8000104C`; it invokes `8023A510` twice. Saved
field commands `800D3380` and `800D33B0` match those two flag rectangles. Applying
the same score origin around each inner flag emitter keeps the flags and score
panel aligned. The outer compositor first calls original `800017C0`, which
queues original display list `8006CE18`. Its ordinary `ED` command at
`8006CE28` reinstalls a centered 320-by-240 scissor. A scope around the outer
compositor is therefore overwritten and clips the flags moved toward the left
screen edge. The scope must begin at `8023A510`, after that original setup.
That inner emitter and its material display list `80264958..802649D8` contain no
scissor or rectangle-alignment reset.

The actual field06 snapshot contains 26 active selected sprite components and
the two name records. Every selected sprite segment list matches original ROM
bytes directly, including its sign-bit terminator. Radar index 0 and all unrelated
indices are excluded. The private evidence also records each selected object's
original descriptor, segment ROM offset/hash and bounds. Inactive unverified
central animation indices 15..19 and 22..23 are deliberately outside these groups.

The original clock updater `801DBD88` also has a numeric mode. Its resource
`BA`/`BB` changes objects 37/38 to native panel descriptor `80076F7C`, while
object 39 becomes the numeric separator at `80076EF8`. Resource `BD`/`BE`
changes object 43 to the period label at `80076F28`, using exact segment
`80261D30`/`80261D3C`. These alternatives are part of the same clock group.
The saved field09 snapshot independently confirms every active tuple. The
previous circular-only guards omitted them, leaving the `1st` label separated
from the shifted digits; the numeric variants now receive the identical
clock origin and offset. Their texture/segment bytes remain original. An
unrelated nearby segment is rejected, and 4:3 still declines without writes.

## Positioning and scope

The score and clock retain a 16-pixel native safe margin with translations
`(-6,+1)` and `(-1,+3)` from their original envelopes. Following the user's
latest layout refinement, each complete player-name panel is centered in the
space between its screen edge and the unchanged radar, rather than attached
to the same outer margin. Its vertical translation remains `-7`.

The original radar spans native x120..200. The complete left/right player
panel envelopes are x26..120 and x199..293, with centers73/246 and width94.
Quarter-screen extended origins256/768 correspond to original x80/240.
The RDP first adds the native origin80/240 to rectangle coordinates.
Using pre-origin translations -93/-226 therefore gives net shifts -13/+14
and places the panel centers at viewport coordinates60/260.
The actual RT64 viewport then maps those centers to the exact midpoint of
each radar-to-edge space at any expansion ratio, including the PAL VI crop.
Both the original sprite components and name text share that group placement;
width, height, UVs and derivatives remain original. RT64 edge quantization
can differ by up to one original pixel at fractional scales. Score, clock and
radar placement are unchanged by this refinement.

`PalHudScope` writes 48 bytes before the original draw: the pinned extension
enable, a scissor push, a wide scissor and the group's rectangle alignment. The
original function then emits its unchanged draw commands. The 24-byte suffix
restores default untagged rectangle alignment and pops the exact previous
scissor, including its origins and mode. A nested scope declines without writes.
The helper uses the existing verified original 64KiB Gfx array, requires 12KiB of
remaining headroom and checks the original cursor/frame boundary again before
restoring state. It never creates an alternative display-list buffer.

The renderer's `extAspectRatio=Expand` enables explicit screen-edge origins.
Untagged rectangles continue to use the original centered coordinate system:
the actual RT64 viewport calculation selects the framebuffer center whenever
origin is `G_EX_ORIGIN_NONE`, independently of this configuration. The same
calculation proves 4:3 untagged draws remain unchanged. Menus, center overlays,
world-position markers and the radar do not receive a HUD scope.

Runtime recognition requires the exact PAL context/table pointers, scene 6/4,
no UI bypass, match phase 0 or 1, exact selected sprite/text record addresses,
layer/kind and descriptor identities, unit original sprite scale and bounded
original segment lists. The original Low path is preserved. High additionally
requires640×544, depth buffer80700000 and the complete original807AA008 emitter
hash. Its original sprite/font/flag coordinates double; HUD translations double
and scissor height is544, with unchanged origins. Unknown layouts and unrelated
UI phases decline without writes. Host720 through2160 rendering is independent
of this original guest video-mode guard. High CPU chains pass; real High visual
acceptance is still pending.

## Integration and verification

Add `src/runtime/pal_hud_widescreen.cpp` to the PAL target. Around the existing
original sprite call, instantiate:

```cpp
PalHudScope hud({rdram,0x800000},wide,PalHudDraw::Sprite,ctx->r4);
```

Use `PalHudDraw::Text` in the existing original encoded-text wrapper. Add a
same-revision original-pointer-guarded wrapper for inner emitter `8023A510` with
`PalHudDraw::ScoreFlags`, only when original `a0 == 8009E0C8` and unsigned
`a1 < 2`. Preserve the complete original emitter call; the outer compositor
remains untouched. The active original symbol is
`func_8023A510_overlay_4a6820_80230590`, size `380`. No generated-source replacement
or asset redistribution is necessary.

`tests/test_pal_hud_widescreen.py` exercises exact recognition/phase/pointer
rejection,4:3 preservation, balanced commands against the actual pinned GBI
macros, no writes outside the original Gfx allocation/cursor, nested/capacity
rejection, and original E4/UV preservation. It also compiles the actual upstream RDP `movedFromOrigin` and
viewport functions to check margins/scale and radar-to-edge panel midpoints at integer and fractional resolutions,
untagged centering and4:3 equivalence. An additional regression executes the
actual original compositor, original setup and both original inner emitter
calls against the pinned saved `field06.rdram`. It compiles the actual native
integration wrapper and follows emitted original `DE` sublists, including the
`ED` scissor reset. It reproduces the rejected outer scope losing its wide
scissor, verifies the corrected inner scopes, preserves every original flag
rectangle/UV word and requires byte-identical RAM for the complete 4:3 path.
This is an isolated saved-state CPU fixture and display-list state audit, not
a game run or visual acceptance. The initial no-op helper failed the
recognition/position regression before implementation.

Private `.local/pal-hud-layout-01/evidence.json` pins 10 original function bodies,
the actual snapshot, selected original segment bytes and helper/test hashes.
Its audit and offline saved-snapshot classifier execute no game code. Visible
integrated 16:9/4:3 captures, moving clock/name updates and continued menu/central
animation behavior remain root acceptance tasks.

## Hidden integrated centering acceptance

Actual native build36 captures328/329 show both player plates centered between
the unchanged radar and their screen edges. In the1280x720 private compositor,
radar edges are518/762; left panel130..390 has center260 versus available-space
midpoint259; right panel887..1148 has center1017.5 versus midpoint1021.
The difference is within native pixel/grid quantization. Name text, player
number/position, bars and tactics plate share the move. Score and clock retain
their previously requested corner placement. Capture328 was embedded in chat.
The actual GPU target is the2160 profile downsampled by the private compositor;
physical4K display output is not claimed. Private receipt:
`.local/pal-hud-center-acceptance-01/receipt.json`.
