# PAL original Controller screen adaptation

Original project work: djultra64.

## Scope and original ownership

The replacement renderer adapts the genuine pre-match/Training Controller screen,
not a PC Settings page. The original `80000BB8` frame completes first. Original
background, Edit Controller heading, four colored cards, Ready, Cursor, Keeper,
UI scripts and state updates remain intact. Six host choices (Type 1 through
Type 5 and Free) are supplied as owned strings; none is written into the original
three-entry N64 Type table. The parent owns input, persistence and capture.

Original overlay `40C7A0` / `802C3490` owns the screen. Active scheduler callback
`802C48F4` and Accept body `802C49B8` are checked against their complete original
body hashes, and a bounded, acyclic walk of the 220-node scheduler verifies the
live owner. `802CF0D8` installs mixed resources: controller words use bank `22`
(hex), common physical prompt assets use bank `15` (hex). The earlier shorthand
“bank21” must not be applied to every Controller resource.

Original `802C55D0` copies **unindexed P1 Type** `802D21E4` to preview index
`802D21F8`. `802D21EF` is the update loop's transient port (3 in the completed
single-player frame), not the visible lower-panel owner. The immutable new view
therefore explicitly supplies its host-selected port and all physical labels.
No controller family is inferred from that transient guest byte.

## Exact replacement boundary

The actual completed Controller49 task uses original native 320 by 240 geometry.
Its original panel gradient occupies x23..300, y142..211, and the border uses
texture `80240C40`. The gradient and all 48 border rectangles remain untouched.
The renderer checks the complete decoded original asset24 (2180 hex bytes), the
original resource/segment span `802CD8D0..802CF300`, the resident sprite/text
bodies, the original font pixels/palette, frame layout, stack and task arena.

Only the four original Type values' eight rectangles and original foreground
inside the bounded panel after its gradient draw become NOPs. Replacement draws
are appended before those NOPs are published. This avoids drawing the partly
transparent gradient twice and preserves unrelated original commands. Unknown
owners, incomplete rectangles, bad resources or insufficient task space reject
the entire page before any mutation.

Eight football actions occupy two columns and four rows. Genuine artist tiles
start at native x42/180 and y146/162/178/194. The action text begins 28 pixels to
the right of the tile origin. Its vertical origin is computed from actual
artist alpha bounds and original font ink bounds, including descenders.
Free capture marks its selected action with original-font `Edit Pass` etc.
The supplied physical Start phrase uses the original 8-pixel text path at y216;
the actual emitted rectangles end at or before y225.

The authentic greatdocbrown CC0 sprite pixels are copied without redrawing.
Their existing 13-color palette is converted to original RGBA16, and tile CI4
indices/palette are stored behind a real G_DL skip in the current original task
arena. Original `80041B50` consumes the stack descriptor immediately; queued
pixels/palettes remain task-owned. No guest heap range is invented. Unsupported
small physical labels use bounded original-font text, never an independent HUD.

## CPU verification and limits

`tests/test_pal_controller_screen.py` first failed because the renderer did not
exist, then passed using the complete genuine original sprite/font call closure
and the actual post-BB8 snapshot `controller49-completed.rdram` (private SHA256
`dcebff719b85eb3ced45e4b114853b627490ad623834c70ee328fb5c068c570b`).
The final focused run passed one test with zero skips in 6.956 seconds.

The fixture checks four physical families, exact source art CI4 indices and
RGBA16 palette, actual emitted rectangle centers, footer bounds, preserved
original backdrop/border, caller/FPU alias/stack, original pixels and guest
controller state. Twelve negative cases prove complete RAM no-op rejection;
a real keyboard LS fallback and visible Free capture also execute the original
CPU renderer. No game was launched for this module's test. Actual integrated
navigation, six-choice behavior, four-port input and visual acceptance remain
parent-owned work; this fixture does not claim those outcomes or a vibration row
in the original N64 screen.
