# PAL original background widescreen scopes

Original project work: djultra64.

The native port scopes the original `0x80041B50` sprite emitter for eight proven
background resource families. Patterned menu images and the screen, gradient and result
covers occupy the full 16:9 viewport. Scripted and scene-specific
full-screen images retain the original centered 4:3 canvas and fill the side
areas from their outermost image columns, preserving baked logos and lettering.
The separate original full-frame color clear also fills the viewport. Exact
original CI8 intro-logo canvases additionally receive white side extensions
from their own texture and fade state; their logos remain proportional.
Subsequent text, portraits, buttons and panels retain their ordinary aspect
behavior. The field sky has its separately verified original-engine
extension. This is bounded background coverage, not proof that every menu,
loading image, title card or Career scene has been classified or visibly tested.

The input is the private English/German PAL revision 0 ROM, SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
No original image, generated game source or memory capture is published here.

| Original role | Resource identity | Descriptor / segment list | Original ROM evidence |
| --- | --- | --- | --- |
| Common blue illustrated menu background | bank 16, index 42, layer 1 | `0x803D7EF8` / `0x803E41A0` | descriptor `0x356CF8`, segments `0x362FA0`, resource `0x36C984` |
| Career mode-2 full-screen gradient cover | bank 102, index 24, resource bank 113/index 29, layer 1 | `0x8022FC8C` / `0x802406FC` | descriptor `0x5406AC`, segments `0x55111C`, resource `0x55702C` |
| Career blue patterned background | bank 88, index 0, layer 1 | `0x8022EE64` / `0x8023E71C` | descriptor `0x53F884`, segments `0x54F13C`, resource `0x5555D4` |
| Scripted full-screen RGBA16 image | resident original constructor, sprite 0, layer 0 | `0x80086FEC` / `0x80086BC0` | descriptor `0x87BEC`, segments `0x877C0` |
| Globe / football / I.S.S.2000 full-screen art | bank 53, index 0, layer 5, two exact scene owners | `0x803D5B58` / `0x802B8D40` | descriptors `0x354958`, segments `0x46CBD0`, resources `0x46D18C` and `0x46E41C` |
| Scene-specific football/net full-screen art | bank 64, index 28, layer 3, exact original scene resource owner | `0x803D6428` / `0x802BB640` | descriptors `0x355228`, segments `0x46F4D0`, resource `0x46F72C` |
| Match-results black translucent cover | bank 2, index 151, sprite 107, layer 11 | `0x8025A014` / `0x80260848` | descriptor `0x4D02A4`, segments `0x4D6AD8`, resource `0x4D96C4` |
| Match-presentation black screen cover | bank 14, index 0, sprite 0, layer 11 | `0x801F6EE0` / `0x801EF7CC` | descriptor `0x2BC3E0`, segments `0x2B4CCC`, resource `0x2BBDAC` |

The common-menu, Career-pattern and scripted-image resources each have 40
original segment records and traverse 40 descriptors; both complete extents are
480 bytes. The screen cover has 150
segment records (1,800 bytes) that reuse exactly one 12-byte descriptor. Each
profile pins its exact descriptor/segment lengths and SHA-256 in
`pal_background_widescreen.cpp`; no assumed 150-descriptor read is performed. The bank directory, active descriptor,
segment pointer, queue membership, object type, layer, origin, view, scales and
single-texture flags must also match. The original main-menu artwork has tile
bounds `(4,2)..(324,258)`. In widescreen only, a scoped rectangle alignment
shifts only this background four native pixels left and two pixels up, making
its canvas start at`(0,0)` before viewport scaling. The previous vertical offset
left a visible black top strip in the genuine Training capture. Original UVs,
foreground placement and the viewport remain unchanged. Rectangle alignment is reset before any foreground draw.
Decorative lettering baked into that background image scales with the image;
independent menu lettering does not.

Private evidence `.local/pal-background-runtime-01/evidence.json` records exact
ROM identities and three observed objects: the main menu in `mainmenu09.rdram`,
and Career file selection / character summary in `career-files08.rdram` and
`career-final08.rdram`. Career face selection also retains the same background
resource in `career-face08.rdram`. Scene numbers alone never authorize a scope.
The same resource will receive the same treatment in another original scene;
that does not establish which resources an unseen scene actually requests.

The third family is explicitly constructed by original resident `0x80047558`,
which calls `0x80047500` with sprite index 0, origin `(0,0)` and layer 0. Its only
caller is the original intro sequencer `0x8004794C`, in the script flag `0x40`
path at `0x80047C98`. Its 40 RGBA16 tile descriptors form a 320 by 240
canvas, with 64 by 32 tiles and the final row clipped to 16 pixels. Both resident
metadata extents match the original ROM and the existing real menu/Career
captures. The regression executes the actual two-function constructor before
its actual original draw chain. This family is accepted only in sprite slot 0
at layer 0; it does not grant permission to resize arbitrary scripted sprites.
The first visible title acceptance (capture 197) exposed baked logo/copyright
distortion under the initial full-image stretch. That strategy is superseded
by the edge extension below; new visible acceptance is pending.

The original initializer `0x80008940` creates 274 sprite records, but the queued
sprite dispatcher `0x8000924C` walks only 273 of them, starting at `0x8013C47C`
with stride `0x3C`. The helper accepts only those 273 original queue entries,
with active context `0x8013B418` and the original 320 by 240 video mode. It does
not classify screen coverage or a low drawing layer by themselves.

The scope appends the pinned RT64 public extended-GBI commands to push the real
scissor, set an edge-anchored widescreen scissor, and select rectangle aspect
`STRETCH`. The original five-function drawing chain emits its own texture,
palette, color, material, rectangle and UV commands unchanged. The patterned-image scope then restores rectangle aspect `AUTO` and pops the
actual previous scissor. The real
Career material list at `0x8009CB78` contains no nested list or scissor command
that could overwrite the scope. The tested common material path has the same
property. No guest sprite positions, image data, UI coordinates, camera, physics or
culling values are changed.

The original display-list arenas start at `0x800D0320` or `0x800E0380`; display
commands begin at base plus 8 and task metadata begins at base plus `0x10008`.
The existing verified `pal_gfx_bounds` helper enforces those identities. A scope
requires 12 KiB remaining space before the original unscaled, single-texture
emitter (13 KiB for each edge-extension image family). The patterned Career extension is 56
bytes; the common-menu alignment adds 32 more balanced bytes. The tested Career
original path emits 5,768 bytes before the extension. Nested scopes and changed metadata fail
closed. Four-to-three mode declines the scope before any write.

For scripted images, `ADJUST` explicitly keeps the center at its original aspect.
The helper validates the complete emitted original stream before inserting any
side commands: all 40 RGBA16 texture bindings must match their original pinned
descriptors; all 40 rectangle/UV groups must match the exact original tile order,
geometry and steps. There are seven 32-pixel rows per column, followed by five
16-pixel bottom-row tiles. Sixteen extended texture rectangles are inserted
immediately before the original leftmost/rightmost tile rectangles, while their
original texture binding is active. They sample only column 0 or 63 with a zero
horizontal texture step, retaining the original vertical UV and step. Explicit
edge-to-center origins bridge the side areas to the centered canvas. An outward
one-pixel guard covers renderer edge rounding and is clipped by the full-viewport
scissor; the original center rectangle immediately redraws the inward overlap.
No interior logo, copyright or other center column is duplicated into a side.
The original center rectangle/UV commands are byte-for-byte unchanged.

The scripted path emits 3,848 original bytes in the fixture and appends 440 native
bytes in total, including sixteen 24-byte strips and the balanced scope. It
checks arena space again before moving any command. An unexpected texture, UV,
command, nested material target or changed tile count declines all side strips;
the original center remains proportional and the state stack is still balanced.
This handles only the pinned original scripted-image producer, with no new host
screen overlay or framebuffer texture sampling.

`tests/test_pal_background_widescreen.py` compiles and executes the actual PAL
original `0x80041B50 -> 0x800419F8 / 0x800423FC / 0x8004250C / 0x80042D0C`
draw chain against the two fixed offline captures, and executes the actual
scripted-image constructor against its unchanged resident metadata. It follows the emitted
material list, checks all 40 rectangle/UV command groups remain identical, checks exact public
GBI edge-strip encoding and constant-U sampling, rejects changed texture/UV
output before any insertion,
checks balanced state restoration, and compares the whole 8 MiB RDRAM against
the unmodified original path in 4:3. Every other sprite in both captured pools
is rejected without writes. Metadata mutation, noncanonical pointers, moved or
scaled objects, insufficient arena capacity and nesting are also checked.
A second test compiles the actual pinned RT64 viewport conversion routine and
checks scoped full-width patterns, proportional scripted-image centers with
edge-to-center strip coverage, and ordinary centered square foregrounds
across the supported output scaling range. These are offline CPU drawing and
renderer calculations, not a substitute for visible game acceptance.

The fourth family is the original black screen cover used by the presentation
sequence in ROM owner `2B0E60`. Its original initializer `801EB990` installs
resource table `801F684C`. The phase-0 branch of actual callback `801ECC08`
requests resource 8 into sprite 0 at `801ECC68`; actual `801EBB14` activates it at
origin `(0,0)`, layer 11. Instructions `801ECC88..801ECC90` set RGB to zero and
`801ECC94..801ECCA0` select original material 19 (`26000000` in the upper flag
bits). The next original object is accompanying text, with separate ownership.
All 150 original 32 by 16 segments tile the full 320 by 240 screen using a single
repeated texture binding; this is a full-screen cover rather than a portrait or
frame. Its original alpha and fade-control calls remain unchanged.

The cover scope requires that exact slot, layer, RGB, material, original bank
pointer and full metadata hashes, in addition to the ordinary context, view and
unit-scale guards. It uses the balanced `STRETCH`/wide-scissor scope; every
original rectangle/UV/color command remains unchanged. The offline regression
maps the exact original overlay data into the fixture, executes the whole
original phase-0 callback and all of its genuine callees (no mock callbacks),
and then executes the complete original draw chain. It emits 150 rectangles in
4,880 bytes; each rectangle after the initial texture binding requires 32 bytes.
The existing 12 KiB reservation accommodates this path and the original
material/cache overhead. Tests reject nonblack or changed-material objects,
a copy in a different slot, and a changed final segment; they also prove that
unrelated bytes beyond the single 12-byte descriptor are outside the guard and
that original alpha values are preserved. Four-to-three whole-RAM equality
includes the genuine constructor's original state.

The fifth family is the original bank 64/index 28 full-screen football/net art.
Original scene entry `802B7CA8` installs resource table `802BB80C` and starts
script `802BBAA4`. Before its 100-tick wait and higher UI objects, that script
calls first subscript `802BB9FC`: original `AA` sets origin `(0,0)`, `E9` requests
resource 12 (`802BB89C`), `8D` selects palette bank 49/index 8, and `E5` selects
material 2. The resulting original object is type 1, layer 3, flags `04026642`,
view `8000`, unit scales, descriptor `803D6428`, segment list `802BB640` and
palette `803D50F0`. Original loader `803BEC34`, called by this scene owner,
requests asset `0x36` to `80270140`; its texture data includes the image's first
tile at `8027B380`. This is original scene background art with baked markings,
so it uses centered `ADJUST` plus edge extension, rather than full-image stretch.
No human-readable scene name is inferred from the artwork.

This family pins 38 descriptor records and 38 segment records (456 bytes each),
plus the original resource, first subscript, main-script prefix and material
list. The currently installed original resource table must be `802BB80C`, and
its palette and material must match; unrelated scenes reusing an address or
foreign original resource tables decline the profile. Its segments cover the
complete 320 by 240 canvas; two bottom tiles are 128 by 16 rather than the usual
64 by 32. The full original emitted stream must contain exactly 38 matching CI8
texture bindings, 38 original palette bindings, and 38 exact rectangle/UV groups
with the original zero UV origin and `04000400` texture steps. The original
one-cycle clipping to 319/239 is retained. Both original material-cache
variants are accepted: the exact FA/E2 pair follows the material call, or starts
the emitted stream when material 2 is already active. The regression executes
that genuine cached-material branch as well. The 16 side strips sample only the
outermost left or right texture column and preserve the original palette;
all 38 center groups remain byte-for-byte unchanged.

The offline fixture maps the original scene and common script overlays into a
fixed capture, initializes the pool record with actual `80008A54`, initializes
an isolated script context with actual `801AD90C`, and executes the genuine
`AA/E9/8D/E5` handlers on the untouched original subscript. The fixture supplies
the caller's object-to-script-context link; it does not run a scene scheduler or
pretend this is a new game capture. All original constructor callees and the full
original draw chain execute without mocked game callbacks. They emit 5,496
bytes; the same bounded 13 KiB reservation accommodates the 440-byte extension.
Tests cover all original center groups, palette/texture and UV mutations,
resource/script owner changes, final-record mutations, capacity, balanced
state, whole-RAM 4:3 equality, and both COPY and one-cycle viewport edge rounding.
Visible acceptance of this specific scene remains pending.

The sixth family is the original globe/football background with baked
I.S.S.2000 lettering. Original loader `803BEB6C` requests asset `0x2A` at
`80259640` through the original request at `803D68C0` (ROM `3556C0`). The asset
decodes to `0x9E00` bytes; its 20 original CI4 descriptors at `803D5B58`
(ROM `354958`) and 20 segments at `802B8D40` (ROM `46CBD0`) reconstruct the
full 320 by 240 image. Private art inspection confirms the image role; it is
not a new gameplay capture. Both metadata extents are exactly 240 bytes.

Two exact original scene owners construct it before their higher UI widgets:
`802B65E4` installs table `802B926C` and script `802B9534`, whose first child
`802B933C` requests resource 12, sets origin zero and calls palette selector
`802B5DB4`. `802B7540` installs table `802BA394` and script `802BA7FC`, whose
first child `802BA658` requests resource 42, sets origin zero and calls palette
selector `802B6800`. Both resource records request bank 53/index 0 at layer 5.
The native profile pins each resource and original script prefix independently.
Material 0 and the original palette-bank root must match. Selector `802B5DB4`
reads original byte `802BBE11` and maps states 0/1/2/3/4 to palette indices
0/1/3/2/5 (other values use 0); `802B6800` maps zero/nonzero byte `802BA36C`
to indices 6/7. The object palette must equal the corresponding original
`803D3E10 + index*32`; arbitrary palette-range admission is not used.

Its centered 4:3 image stays proportional. Eight left-edge rows and four
right-edge rows receive 12 constant-U side strips, each emitted while its
original texture and palette are bound. The original rightmost tile uses
64-pixel rows; its last 48-pixel source row and the leftmost final 16-pixel
visible row retain their original screen clipping. The complete original
stream must have all 20 matching texture bindings, 20 palette bindings and
20 exact rectangle/UV groups. The original COPY-mode steps are `10000400`
with zero UV origin; no baked center logo or lettering is rescaled or copied
into the sides. The original material list is also hash-guarded.

The regression executes both original constructor routes and their genuine
palette selector/copy callees across all seven selected palette variants. The
fixture supplies only the isolated caller context, as described above for the
fifth family. All 20 original center rectangle/UV groups remain byte-for-byte
identical; the 2,888-byte original output gains 344 bytes, within the same
13 KiB reservation. Whole-RAM 4:3 equality, foreign scene resources, changed
script/palette/material, changed final records, insufficient capacity and
balanced restoration are checked for each constructor variant. Specific visible
acceptance remains pending.

The original full-frame color clear is a separate route from sprite artwork.
Actual hidden intro captures 262/263 showed black sidebars around the original
white KONAMI/KCEO canvases. Original resident `800019FC` derives RGBA5551 from
the active frame's four color halfwords at context offsets `6/8/A/C`, selects
FILL cycle, emits `F7` fill color and exactly one `F6` rectangle from `(0,0)` to
`(319,239)`, then restores cycle type 0. Its only callee `80001B2C` optionally
registers an `FF` color-image command in the original task patch list. It does
not emit an `ED` scissor reset. The ordinary caller's `800017C0` setup list
contains the original scissor before this narrower boundary.

`PalScreenFillScope(span, wide)` is used only around that exact original clear,
after its caller setup. The 40-byte prefix pushes the actual scissor, selects
the full widescreen scissor and rectangle `STRETCH`; the 16-byte suffix restores
`AUTO` and pops the previous scissor before any logo or foreground is drawn.
The original clear coordinates, color and all original commands are unchanged.
The prefix precedes `80001B2C`, so its original registration records the correct
new `FF` address; no registered command is moved later. Only the known 320 by
240 active context and the original display-list arenas are accepted, with at
least 128 bytes free. The original clear emits 48 bytes without registration
or 56 bytes with it; either branch plus the scope fits that reservation.

The regression executes actual `800017C0`, `800019FC` and `80001B2C` against the
fixed original capture, covers both registration branches and white/black/color
values, checks every original command and exact registered `FF` pointer,
checks the public GBI scope and restoration, and compares the complete 8 MiB
RDRAM to the original call chain in 4:3. Changed frame context, size or arena,
insufficient capacity and nesting decline the scope without writes. The pinned
RT64 viewport regression separately proves that the scoped full-canvas fill
covers 16:9 and ordinary foreground dimensions remain unchanged after `AUTO`.
The original logos receive no sprite or texture-coordinate change. The subsequent actual build-36 capture 318 showed that this clear alone does
not cover the white intro canvas: the original clear is black, while the
centered KONAMI image supplies white. The clear scope remains valid for the
original clear itself; the direct intro adapter below addresses that separate
image producer.

The seventh family is the original Career mode-2 full-screen gradient cover.
Original resource-bank directory `80076FA0` entry 113 points to `802464B0`;
resource index 29 at `8024660C` (ROM `55702C`) requests descriptor bank 102/index
24 at layer 1. This is the resource directory used by original `80007C90`,
distinct from the descriptor directory at `80076ADC`. The descriptor at
`8022FC8C` (ROM `5406AC`) is a single 96 by 32 CI4 image; 90 original segments
at `802406FC` (ROM `55111C`, 1,080 bytes) repeat its three gradient cells with
U offsets 0/1024/2048 to cover the complete 320 by 240 canvas.

Original `801EF0D8` requests asset `112` to `80265B80` through the record at
`801FA050` (ROM `521CD0`). Compressed bytes `CEA434..CECE64` decode to `6740`
bytes, SHA-256 `9e74f95ee7237b5676a786ec4e1fafb370dd597d7563fbf52075538e7a1a9656`.
The image is exactly asset offset `2300`, 1,536 bytes, at `80267E80`; its
original art is three plain gradient cells, without letters or logos. The
complete original segment list reconstructs a dark full-screen canvas with a
horizontal bright gradient band. Current weekly snapshots contain English
language-script bytes at this reused texture address, so those bytes were
explicitly excluded as art evidence. The native profile hashes the actual
original gradient data as well as the descriptor and complete segment list,
preventing that storage reuse from authorizing a scope.

Original `8021CE9C` starts parent script `802537A8`; original `8021CEE0` keeps
its image only when the active Career context referenced by `801FD5F0` has
mode byte `+1E == 2`. The parent calls image subscript `80252898`, whose exact
`EC711D` requests resource bank 113/index 29 and whose `8E4130` selects the
original palette at `8022C6B0`. The helper requires this original resource-bank
pointer, the descriptor-bank pointer, complete original parent/image script
hashes, a bounded canonical active context with mode 2, material 0 and that
palette. Canvas size or mode alone does not admit an unknown object.

The regression maps the exact original Career/common-script data and decoded
asset into an offline fixture. It supplies the real working-context structure
from the weekly capture with mode 2 as constructor input, executes actual
`8021CEE0` and the genuine `EC/8E` handlers and their original resource/palette
callees, and then executes the full original drawing chain. This is a CPU
fixture, not an execution capture or an injected gameplay state. All 90 original
rectangle/UV groups remain identical; the original 3,000-byte output gains only
the balanced 56-byte `STRETCH` scope within the existing 12 KiB reservation.
Whole-RAM 4:3 equality and changed resource/script/texture/palette/material,
non-mode-2 or missing context, final-record mutations and capacity are checked.
Specific hidden-window visual acceptance remains pending.

The eighth family is the original match-results translucent black cover.
Original constructor `80235C50`, called by the results-state route at
`80235048`, requests resource `1D1` from table `80261E68`. Its record at
`80263434` (ROM `4D96C4`) requests bank 2/index 151. The actual constructor
activates sprite 107 (`8013DD90`) at origin zero, layer 11, sets RGB to zero,
alpha to 96, and material 19. Higher result-screen widgets are separate objects.

Its one original 128 by 32 I4 descriptor at `8025A014` (ROM `4D02A4`) points to
atlas `80212580`, loaded by the original asset-55 request to `80201280`.
Although other atlas cells contain SCENARIO lettering, all 180 original cover
segments at `80260848` (ROM `4D6AD8`, 2,160 bytes) sample only the solid-white
56 by 8 cell at source `(64,24)`. Their original geometry tiles 336 by 240;
the original scissor clips the last 16 horizontal pixels. This is a uniform
translucent cover, with no text or picture in its sampled region.

The profile pins that exact slot, table, bank pointer, resource, complete
segment list, descriptor and all 2,048 original atlas bytes. RGB, alpha 96,
material, origin, view and unit scales must match. Foreign result objects,
changed colors or alpha, another resource table or changed image bytes decline
the scope. It widens only the original cover with the balanced `STRETCH`
scope; its original alpha, rectangle coordinates and UV words remain unchanged.

The offline regression maps the original match overlay and decoded asset 55,
executes the actual pool initializer and the entire `80235C50` constructor,
including its genuine resource, activation and audio-queue callees, then runs
the complete original draw chain. Unknown original calls abort the fixture;
no constructor callback is replaced. All 180 original rectangle/UV groups
remain identical. The original 5,840-byte output gains 56 bytes within the
existing 12 KiB reservation. Whole-RAM 4:3 equality, unrelated pool objects,
final-segment and atlas mutations, resource/slot/color/alpha/material changes,
capacity and balanced state restoration are checked. Specific hidden-window
visual acceptance remains pending.

The original intro logo canvas uses a separate direct CI8 emitter, not the
queued `80041B50` sprite route. Actual hidden build-36 capture 318 showed black
sidebars beside the original white KONAMI artwork. Original caller `801ADC7C`
in owner ROM `2C99E0` calls `801ADD44` with one of three exact argument sets:

| Original canvas | Descriptors | Palette | Segments / count | Original output |
| --- | --- | --- | --- | --- |
| KONAMI logo on white | `801B7608`, 120 bytes | `801AE080` | `801AE280`, 163 records | 4,536 bytes |
| KCEO / PRESENTS on white | `801B7680`, 96 bytes | `801B2BC8` | `801B2DC8`, 96 records | 2,816 bytes |
| Separate plain white canvas | `801B76E0`, 12 bytes | `801B7048` | `801B7248`, 80 records | 2,040 bytes |

These canvases retain their original centered `AUTO` geometry. After the actual
original call, `extend_pal_intro_canvas` appends a balanced wide-scissor /
`ADJUST` scope and two side-only extended texture rectangles. The rectangles
sample a single original white texel with zero horizontal and vertical steps
from the final texture that the emitter already bound. Exact original palette
and texture hashes prove that its complete 3 by 3 neighborhood is white, so
filtering cannot pick up nearby lettering. The unchanged original `FA` color
retains alpha 0..255; no color or alpha is synthesized. The side rectangles
meet the central canvas exactly at native x=0 and x=320 without inward overlap,
so a fading edge never receives the original alpha twice.

The emitter uses private cursor `801B77C0`. Its caller writes that cursor before
the call and returns it afterward; it does not use `8009E0C8` for these individual
writes. The hook captures original r4/r5/r6/r7 and the private cursor before the
exact active original `801ADD44`, runs it, then calls the post-adapter with those
saved arguments. The adapter changes only the appended 104 bytes and that
private cursor. No original command is moved and no return register is changed.
The original caller consumes the new cursor through its ordinary return path.

Admission requires original PAL emitter bytes and the exact original material
list at `801B7710`, the complete corresponding descriptor/segment extents, the
512-byte original palette and final original texture, and a SHA-256 pin of the
entire actual emitted command stream. Only the original fade-alpha byte is
normalized in a local copy for that last comparison. The active original 320 by
240 context and fixed Gfx arena must also match, with 104 bytes remaining after
the exact original output. Unexpected pointers, alpha outside 0..255, changed
output or metadata, foreign overlay content, nested native scopes and insufficient
capacity decline without writes. The known material list has no scissor reset.

The regression first failed because this direct-image adapter was absent. It
then executes actual `801ADC7C ->` the integration wrapper extracted from
`native_game.cpp -> 801ADD44`, covering all three canvas profiles
and alpha values 0, 96 and 255. It checks exact active-symbol dispatch, complete guest-context preservation
across the native wrapper, the genuine parent return cursor,
every original command unchanged, all 163/96/80 rectangle/UV groups, exact public
extended-GBI words, whole 8 MiB 4:3 equality, and no wide-mode changes outside
the appended commands/private cursor. Source, material, palette, image, final
segment, original output, argument and capacity mutations decline. The pinned
RT64 viewport calculation checks full-width sides with no central overlap at
the supported output scales and proportional foreground restoration. New
hidden-window visual acceptance remains pending.

Additional candidates remain excluded pending original consumer and role proof.
Career bank 91/index 7 and bank 107/index 10 contain broad foreground
compositions at layers 9 and 5. The Career match-transition frame at bank
12/index 1 has a large central hole despite a screen-size bounding box.
None is approved merely because its bounding box spans the screen.


## Actual Select Teams composite correction after r53

Hidden captures `.local/select-teams-54-before/05-yellow-settled.png` and
`12-blue-teams-settled.png`, with their completed RAM, exposed two independent
background defects. This correction is grounded in those scenes and the exact
original CPU producers; post-change GPU acceptance is recorded separately.

The common menu is a composite. Its forty CI8 base tiles were already stretched,
but two additional layer-2 I4 watermark lettering sprites retained centered
4:3 geometry and clipping. Those ordinary clipped ends then appeared inside
the widened background. Original `803C3E20` moves fixed sprite 3 horizontally,
and `803C3EA0` moves fixed sprite 4 vertically; both obtain their records through
`803C36C0`, update the original shared position and alpha through `803C3978`, and
retain original timing. These are decorative background words, separate from
headers, body text, flags and player models.

The two atlases are bank16/index36 at `803D7EB0` and index39 at `803D7ED4`.
Each descriptor extent is36 bytes. The yellow Training selector uses12-piece
segment lists `803E4CF8/803E4D88` (144 bytes each); the blue Pre-season selector
uses14-piece lists `803E4728/803E47D0` (168 bytes each). All descriptor and segment
bytes match their original ROM metadata exactly; each variant has its own
SHA-256 guard. Only fixed slots `8013C530/8013C56C`, type1/layer2, material19,
zero palette, unit scales and the original view are admitted. The horizontal
layer must keep y0 and original x range[-562,100]; the vertical layer must keep
x0 and original y range[-100,442]. The two-pixel threshold overshoot comes from
the original previous-position wrap checks. The same balanced wide-scissor /
STRETCH scope now covers these two background layers. Texture, UV, color, alpha,
position, wrap logic and simulation cadence are unchanged.

The base image also lost pixels because its original emitter clips the
`(4,2)..(324,258)` canvas to319/239 **before** the existing(-4,-2) alignment.
In COPY mode, inclusive low bits then leave a316-by238 canvas after alignment:
four native pixels at the right and two at the bottom are uncovered. Moving
the origin alone cannot recover those pixels. The scoped post-adapter now
validates the entire40-tile output: exact CI8 texture pointers, selected palette,
original tile order and geometry, zero UV origins, COPY steps and known original
material/raster commands. Only after every group matches does it restore the
four right-edge and ten bottom-edge rectangle boundaries. Those existing tiles
sample their own previously clipped in-bounds source pixels; all UVs, bindings,
interior boundaries and original RAM resources remain intact. A changed texture,
UV or output shape rejects the complete boundary repair without partial writes.
This is the specific exception to the earlier all-rectangle-bytes-unchanged
claim above. Four-to-three output remains whole-memory identical.

The focused composite regression executes the actual original draw chain on
both completed Select Teams snapshots and the actual motion callbacks. It
checks balanced render state, identical decorative rectangle/UV groups, exact
base boundary corrections, foreign/moved/scaled/changed-resource rejection,
mutation fallback and unchanged4:3 output. The pinned RT64 viewport calculation
also receives the real COPY inclusive/alignment coordinates and proves complete
coverage across the supported scale range, including fractional PAL scaling.
The full background test module has5 passing tests; no game or GPU execution was
performed by this worker for these changes.
