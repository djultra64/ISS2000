# PAL Main Select layout and animation correction — r67

Original project work: **djultra64**. Linux only, one worker, no agents.
Windows stays frozen. Older packages, private ROMs and all user data are preserved.

## User intent and final layout

The supplied `2026-10-18 16-44-11.mp4` (1920×1080, 60 fps container,
13.833 seconds) shows lamps jumping between rows and selection text outside its
panel. The user first requested moving the large ball to the left edge while
retaining the options' positions. After reviewing the actual capture, the user
also requested moving MAIN SELECT, option labels and their lamps left together,
following the ball's contour, while keeping the rectangular row backgrounds fixed.
Exit Game should be easier to read and use a heavier stroke.

The final wide layout uses physical LEFT origins for the ball and all its
components, the heading, labels and lamps. Their original horizontal offsets,
relative shape, dimensions and UVs are retained. Row backgrounds and the animated
panel highlight retain their previous horizontal positions. Rows keep the
existing 16-pixel upward adjustment; the heading moves up only 12 pixels, leaving
more top margin. Aspect 4:3 retains the original horizontal origins and ball.

The footer uses a 14-pixel active-device glyph and the original 12-pixel font.
Two opaque native font passes, one original pixel apart, thicken its strokes.
It remains below the options and inside the PAL visible crop. The English modal,
default No, physical north shortcut and four-port family mapping remain intact.
No font atlas is replaced and no independent host overlay is introduced.

## Causes and exact corrections

The prior rectangle texture list missed three of the twelve lamp animation
images and four selected-label atlases. The real original sprite emitter now
runs through every lamp frame and all five selected-label atlases in the
regression. Normal and selected labels receive identical row offsets. The
whole-menu rectangle-count threshold is removed: a genuine partial entry or
exit draw must not suddenly switch layout when the list reaches 70 rectangles.

The ball's grid shares texture 23EF00 with the row panels. Its exact sprite draw
is scoped separately, so the grid follows the ball instead of receiving the row
lift. The ball outline, eight reviewed internal lettering profiles and all
sixteen original figure frames share that scope. A balanced full-width scissor
admits the actual left edge; rectangle alignment returns to NONE afterwards.
The original emitter still generates the geometry, UVs, material and animation.

Foreground rectangles are converted in place to the existing RT64 signed
extended rectangle command when LEFT alignment is needed. Their command
addresses, immutable task ownership, UVs, derivatives and interpolation UIDs
remain intact. No global interpolation or texture-compatibility guard is relaxed.

A genuine r66 return from Option exposed a separate ownership error: the original
byte 8012DE74 retains the destination value 1 after returning to Main Select.
It is not a unique current-scene identifier. Original function 803C2C74 maps the
nine destinations 0,5,6,7,13,2,3,4,1 to the nine main rows. The final guard admits
exactly those values while still requiring the live Main Select callback,
resource, PAL frame identity and pinned source bytes. The selector's complete
120-byte original body is now pinned as well. Values 8–12,14 and255 are negative
controls. The original destination byte is never changed by the adapter.

## Ownership and verification

Main Select retains the exact 803D75D4 resource and 803C29FC callback hashes.
Only its reviewed original entry/exit continuation may own transition rendering.
Ball profiles require a canonical live sprite-pool object, exact descriptor and
segment pairs, the complete pinned 8 KiB descriptor bank, pinned 1696-byte
segment table and the actual original 80041B50 emitter body. Foreign owners,
resources, regions, unknown destination values and changed artwork decline
without writes. The original sprite pool and caller context remain preserved.

The original-CPU fixture checks all twelve lamp frames, all five selected-label
atlases, seven ball draw layers, eight internal lettering profiles, sixteen
figure frames, nine retained destinations, immutable row-background coordinates,
original UVs/derivatives, all four ports and Xbox/PlayStation/Nintendo/keyboard
footer and modal rendering. It first failed for missing animation states and
again for the actual Option-return snapshot before the respective corrections.
Receipts: `.local/r65-verification`, `.local/r66-verification`,
`.local/r67-verification`.

Actual private compositor evidence lives under `.local/r63-ui/runs`:
UI09/r65 verifies the first relocation; UI10/r66 verifies the requested text
relocation, stronger footer and navigation, and preserves the failed return
snapshot. UI09 and UI10 exited normally with status 0 and cleaned their owned
processes and audio sink. r65 and r66 are intermediate checkpoints, not the final
handoff. Final r67 runtime and verification results are recorded in the latest
handoff and `.local/r67-verification`.

All executions use one hidden compositor at a time, a verified unique null audio
sink and copied private test data. The screenshot comparisons are actual game
output, not mockups. Receiver video timestamps are not physical scanout or
sustained 120 fps acceptance. Gameplay, physical controllers and the previously
pending goal trail/goal-overlay entrance remain outside this menu correction.


## Final r67 result

Executable SHA-256: `799f0283ec61c80b5c25d4849f2cc42c55bfaa11b3509061c4a246b82c626678`.
All 46 package files match the manifest; 40 dependency notices are present and
fresh package data remains empty. The final original-CPU fixture passed after
adding the selector source pin (10.591 seconds). The general suite recorded
under r66 passed 511 of 514 tests, with three historical NTSC diagnostics skipped
in 524.780 seconds. It is retained as a general-suite baseline; no new complete
r67 suite is claimed after the bounded destination-guard change.

Actual UI11 confirms the corrected layout after returning from Option, a visible
No-default exit dialog, cancellation and explicit Yes exit status 0. Its
`return-proof` recording contains 476 authenticated private-compositor frames;
these are receiver samples, not physical scanout evidence. The session completed
normally and all owned processes and the unique audio sink were removed.
Receipt: `.local/r67-verification/final-receipt.json`. No source changes followed
the final focused fixture and package build. No game remains running from this
correction pass.


## r68 composition refinement

Main Select r68 composition follow-up (2026-10-18).
Original project work: djultra64. Linux only, one worker, no agents.

The user approved the r67 layout and requested only a small additional leftward
movement of the nine items, Pre-season Match through Option, following the ball
more closely. The heading, row backgrounds, ball and Exit Game are retained.

The item labels, selected-label glow and all lamp images receive the same small
inset within each row: 6,5,4,3,2,1,1,1,1 original logical pixels from top to
bottom. The upper part therefore bends farther inward; the lower indicators,
already touching the outline, move only one pixel. Vertical positions, dimensions,
UVs, derivatives, immutable task addresses and interpolation IDs are unchanged.
The horizontal refinement is active only in wide mode. Original canonical item
bands determine the row before the existing upward adjustment.

The existing original-CPU Main Select fixture was updated and first failed on
r67's zero extra inset. It then passed in 9.346 seconds on r68. It checks small
matching insets for each label/indicator row, a nonincreasing inset down the
menu, unchanged heading and backgrounds, original UVs and derivatives, all
existing animation profiles and physical prompt cases. No new complete general
suite is claimed for this bounded composition change.

Portable: portable/ISS2000-Linux-20261018-r68/launch.sh.
Executable SHA-256: 5bdfd5de930cb0bb5c9de1f5001ae92af888e1202eee7fe3df0d2d8cd538af69.
All 46 manifest files and 40 dependency notices are verified; fresh data is empty.
Old packages and user data remain preserved. Actual UI12 (exact package) verified all nine visible rows and navigation to
Option at 1920×1080 in a hidden compositor. Confirmed Yes exited normally with
status 0; owned processes and the private audio sink were cleaned up.


## r69 first-item adjustment

Original project work: djultra64. Linux only, one worker, no agents.
The user requested moving Pre-season Match and its lamp 10% right. This is
interpreted relative to the group's current leading-edge position: r68's 134
logical pixels become 147.5, with a rigid +13.5-pixel translation (rounded to the
renderer quarter-pixel grid). At 1920×1080 this is about 65 output pixels.
Text, selected-label glow and lamp keep their original dimensions and spacing.
The other eight item offsets, heading, row backgrounds, ball and Exit Game
retain r68's positions. Aspect 4:3 keeps its previous horizontal layout.

The existing original-CPU Main Select fixture first rejected the old position,
then passed with the requested first-row translation in 9.348 seconds. It also
checks unchanged original UVs/derivatives and background coordinates, prompt
families, animation profiles and destination/owner negative controls. No new
full-suite run is claimed for this bounded composition change.

Portable: portable/ISS2000-Linux-20261018-r69/launch.sh.
Executable SHA-256: 33e1ba83a4e63dace9059554ed7099ed8a77bff57c98117379a0c7a00336876e.
All 46 manifest entries and 40 notices verify; fresh package data is empty.
Actual exact-package UI13 reviewed the first row at 1920×1080 in a hidden
compositor. Explicit Yes in Exit Game exited normally with status 0. All owned
processes and the unique audio sink were cleaned up; no private game remains.
