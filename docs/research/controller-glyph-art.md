# Artist controller glyphs in the original sprite pipeline

Original integration work: djultra64. Source artwork: greatdocbrown.

The selected pack is [Gamepad UI / Controller Prompts Pack](https://greatdocbrown.itch.io/gamepad-ui),
whose official page identifies the artwork as CC0-1.0 and includes Xbox,
PlayStation, Switch, keyboard and mouse sheets. The original downloads, author
notice, official source links and exact SHA-256 hashes are retained under
`assets/controller-prompts/greatdocbrown/`. The current PlayStation 3 PNG is newer
than the version-2 all-files archive; the integration uses that current PNG.
The notice is included in the portable-package license inventories.

`tiles.json` records inspected source rectangles and physical family/name keys.
`tools.prepare_prompt_glyphs` verifies each official PNG digest before baking
`src/runtime/gdb_prompt_glyphs.inc`. That generated table contains 103 distinct
artist tiles and 177 family/name entries including aliases. Crops retain the
artist's pixels. The wider Enter and touchpad tiles use an aspect-preserving
nearest-neighbor fit into 16x16. The four right-stick directions combine the authentic, unbranded R-marked
stick tile from the Xbox sheet (12x12 fit at0,0) with the authentic Switch
direction tile (8x8 fit at8,8). Using the marked R tile across all three families
preserves right-stick identity; unlettered stick shapes would be ambiguous.
Both source rectangles and the composition recipe are recorded. No letter,
arrow or relief shading is redrawn.
The tool refuses source digest changes and unexpected generated-file changes.

The existing guarded bank-21 A/B sprite adapter selects artwork by the family
and physical glyph label from one input snapshot. Nintendo south is B and east
is A; the original logical action is never used as the physical label. The
same A letter can select different Xbox and Nintendo artwork. PlayStation
symbols and names select the same author-created symbol tile. Keyboard Z/X use
the keyboard sheet. Common digital remaps select the appropriate face,
shoulder, trigger, stick, menu or directional artwork. Directional symbols are
shared author-created Switch tiles; their arrows do not carry a family brand.

The original two CI4 icon palettes have fixed blue/green shades. Their exact
hash guards, original bytes and shared ownership remain unchanged. Each artist
pixel is reduced to a palette entry using luminance distance, then weighted RGB
distance as a tie breaker. Transparent source pixels require a transparent
palette entry; opaque source pixels can select only opaque entries. Thus the
artist's silhouette and relief shading survive while source colors adapt to
the game's existing icon colors. This is a color-reduced CC0 modification,
not a claim that the original Rosy-42 colors remain intact.

The A/B adapter writes only its recognized128-byte texture. The PAL C adapter
writes its recognized640-byte80x16 CI4 strip. Four16x16 cells share each40-byte
row; cell order is Left,Right,Up,Down,neutral. All four physical requests are
resolved before a write, and the neutral fifth cell remains exact. Original
palette pointers, bytes, descriptors, dimensions and allocation lifetimes stay
unchanged. Original reload, ownership loss and restoration retain their guards.
There is no host overlay or new guest-memory reservation.

The Career menus have a separate shared A/B image: bank94/index19,32x16,
attributes010A0000. Its physical bank-pointer field is80076C54; descriptor ROM
541FCC is in the original Career overlay523120→80212700. The entire256-byte
texture is SHA-256 `c62537a1c45ff4cfd489a6fd4b08451caea827b3a36f79444fe78ee8180a80a3`,
and its exact shared palette at ROM536A50 is
`3eff1d2aa46ae1715ad68a79a0efb7e288c116f8bbff8c287fd4be95e7ab3375`.
Original asset113, ROMCECE64..CF3308, decodes to65536bytes
(`538b8d34b4eaca15b41ff50574a37f48fd8ba23b03399ecc312ae1e535bcba6e`);
request ROM521CD8 loads it at803D4E40. OffsetFA00 is the original two-cell icon.
This route uses the same original80007C2C initializer and80041B50 draw hook.

Career resources ROM5586AC/55822C/558238 select bank94/index19 and terminal16x16
segments8023322C/8023D2A0/8023D2AC. U0 selects logicalA; U0200 selects logicalB.
Both physical cells are prepared before one256-byte row-interleaved write.
Missing artwork offers one original-font line for the currently selected cell,
including the right-cell UV offset. Real file/name memory snapshots establish
B Return at(20,201), A Select at(104,176), and B Return at(168,176), before the
font's vertical centering offset. Career's viewport flag8000 does not affect
geometry in the original sprite builder; original anchor bits still apply.
Original reload/foreign texture/palette ownership remains guarded. The US
profile does not acquire this PAL-only route. Private identity/source/snapshot
proof is under `.local/pal-prompt-research-04/career-ab-proof.json`.

The optional PAL profile proves bank21 descriptor8 (`010A0000`), its entire
texture (`d36021674ebafd8b1692386877ab990103b19c747979cbeef86d803f8c4a644e`)
and palette (`9e591d8246bb991a8afaf791cc716f7697d23d9c008c822f18dd17c1682b34cf`).
Original resource ROM4185B0 selects bank21/index8 and segment pointer802CEE3C.
The initializer80007C2C resolves those fields and stores sprite+14/+30. The
four-segment list at ROM41814C uses U=0000/0200/0400/0600 (five fractional
bits) and positions (136,169),(211,187),(211,169),(136,187). Adjacent resources
418598/4185A4 bind A/B indices5/6 to single-icon lists802CEE24/802CEE30.
The US compatibility profile does not inherit this PAL C/font proof.

The shared controller preview follows Player1:802C5540 reads unindexed row
802D21E0, then55D0/55E8/5628 read unindexed Type/cursor/keeper21E4/21E8/21EC.
The update loop's21EF is not a later draw port;21F8 is a preview page. The
caller therefore supplies explicit port0 physical requests for this preview,
while the four editable controller rows retain their individual port owners.

`prepare_physical_prompt_sprite` distinguishes unrelated sprites, applied art,
a validated text-fallback proposal, and rejected known assets. A missing artist
tile restores only bytes still owned by the adapter. A/B fallback requires one
terminal16x16 segment at UV0. C fallback requires the exact48-byte consumer
SHA-256 `3e0509f2dee89c473e451037c3a58bd0808e174b60aaa4d266f01fa396458621`
and returns all four labels together. Both require unscaled geometry, bounded
viewport anchors, the canonical frame pointer at8009E02C with mode byte+12=0
and original width/height320x240 at+14/+16, and exact original font asset0D at
80352800,12288bytes,
SHA-256 `237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765`.
The native caller additionally verifies the active original resident48660
function identity, preflights the complete Gfx/stack/context transaction, and
draws every line using that original game font, then suppresses
that original sprite only after a successful whole draw. A proposal itself
neither renders nor hides anything. Partial C art/text is never offered.

Short original-font aliases fit within the original16px icon cells: P1..P4
(paddles),PS,MC (microphone),SQ/TR (square/triangle),RL/RR/RU/RD (right-stick
directions), and the normal face/shoulder letters. They use the original6px
font; complete physical names remain in Remap. Font/consumer/palette/geometry
mismatches return a native diagnostic status and never invent a position or
replace foreign memory.

The PAL Start-for-random image is replaced by an original-font proposal when
an optional fifth physical Start request is supplied. Descriptor1 is96x16,
attributes03030000, entire768-byte image SHA-256
`5b452ff00298dc6d5015627e9de020fa8aa655e14b3282fa69d2ab11b146e99e`.
The exact descriptor is I4: original8004250C maps format3 through8009CE8C to
N64 intensity format4. It does not consume the sprite's palette override at+34;
that field may remainFFFFFFFF after the normal initializer. The original-font
proposal therefore requires the image/descriptor/consumer/font identities without
claiming ownership of an unused palette. Color-indexed A/B/C guards retain their
exact palette requirements.
Three original resource records select this image and one full terminal UV0
segment: ROM36CEA0→803E645C at(177,213), ROM46C67C→802B860C at(188,216),
and ROM4806B8→802AEAD4 at(182,214). Complete12-byte consumer SHA-256 guards
are respectively `1f591ec6e6f04c2117262b3afaceebf0059ae95089655142f465ddf98d3f5fbd`,
`8198269896413885239bc9c1fb4ada83587e54a41c286666124c8572ec1a38c4`,
`1f9e9485697ea8879fd20b1d4ed1d6353f2b9bf8b1401fcde855dc0b84d6db4d`.
The source image is untouched. The proposed phrase fits its original96x16 cell,
for example Menu Random,Options Random,Plus Random,Enter Random or Cross Random.
The same original-font transaction and normal original-frame checks apply.
Host720p..4K resolution scaling remains independent of this original320x240
coordinate-mode guard.

Descriptor13 combines L/Z/R paging hints; descriptor7 is an unlettered red
button. Their separate action/consumer routes still need proof before changes.
Private complete bank/consumer evidence is in `.local/pal-prompt-research-03/`.

Verification covers exact official source pixels through an independent CI4
reference, family-specific selection, source tampering, actual private PAL
palette transparency/shading, invalid palettes, and synthetic RDRAM bounds,
foreign replacement, palette ownership, C row/cell ordering and whole-text
transactions, original-frame rejection and all three Start consumers. These are
CPU checks. Visible
artist-glyph acceptance and physical-controller verification remain separate.
Private inspection images are under `.local/gdb-glyph-review-01/`.


## Career country and name-editor packed prompts

Real boot10 snapshots revealed two additional bank105 sources, independently of
bank21 and the Career A/B pair. The immutable PAL profile reads bank105 through
80076C80. Original asset113 decodes to65536bytes with SHA-256
`538b8d34b4eaca15b41ff50574a37f48fd8ba23b03399ecc312ae1e535bcba6e`.
Both new texture extents match this original decoded asset exactly; descriptors,
palettes and whole segment lists also match original PAL ROM bytes exactly.

The country selector uses descriptor11,128x16,01030000 (ROM540A3C), texture
asset offset1380,1024bytes, SHA-256
`8fda1c5c8ca05884a12afabef3f9345cda6797c53d1f0cdd112ea9cc692d4321`.
The complete24-byte consumer at ROM5529C4 has SHA-256
`d30478fc454983e266340ea9b649a272ad7f34ab2b32b8b0e9dd2bec92c19c90`.
Original803C69FC reads the menu input and dispatches through801B5844/801B57AC:
L(mask20) and Z(mask2000) select the same previous-category handler803C6BA8;
R(mask10) selects the next-category handler803C6C4C. The adapter requires three
explicit physical requests in L,Z,R order and proposes one original-font line,
for example `LB LT RB`, at(47,151). The vertical offset is the original consumer's
16px cell height plus2px, placing the readable phrase below the unchanged
arrows at(39,135)/(70,135), each16x16, and above A Select at y176.
The snapshot regression checks that the font rectangle intersects neither arrow. Physical aliases use only the established font
letters/spaces; the font helper does not accept a literal slash. Original game
input and category changes remain unchanged.

The name editor uses descriptor2,64x16,01320000 (ROM5409D0), texture asset
offset100,512bytes, SHA-256
`14ae1010194afa4df48b5b03ad50f3fdaa67fd956346d6d7b341ff1f64ea6f77`.
The complete48-byte consumer at ROM55156C has SHA-256
`cdfaa6af8d477f8682a3d1a26cfbd4754abc310320d34dc7a9d80e30d3b89c3c`.
Its source cells are Right,Left,Up,Down, while its consumer draws
Right,Left,Down,Up at x46/32/208/128,y49. The genuine artist tiles are written
transactionally in that original row-interleaved cell order, preserving all
consumer UVs. Missing artwork restores only owned image bytes and proposes all
four original-font labels at the corresponding original positions. Complete
source/palette/consumer/font and frame guards remain mandatory. Reloaded original
bytes may be reacquired; foreign bytes cannot be overwritten or restored.

`tests/test_career_packed_prompts.py` exercises the actual country10/name10
snapshots and checks exact art placement, font proposals, whole-RAM ownership,
and rejection of foreign consumers, palettes and fonts. Private original-ROM,
compressed-asset and input-consumer proof is under
`.local/pal-prompt-research-05/career-packed-proof.json`. These are CPU checks;
new visible rendered output still requires the parent acceptance run.

The legacy resident string adapter at80003EB4/8009AB98 is a separately verified
text route. It does not establish coverage of the commercial title's large
PRESS START image. The saved title10 memory was already in intro exit/cleanup
(state800BE944=2,count800BE948=-12), with the transient sprite pool cleared;
a steady-title snapshot is required before extending that route.


The same real name-editor snapshot also proves separate bank105 A/B images at
indices0/1,16x16,attributes01300000/01310000. Their original asset113 offsets
are0/80 (128bytes each), with whole-image SHA-256
`545d023679e76e79c3398c2d00f847868017f120f69190d5d48879c32ebedde8` and
`2392c695da5ef20c906f872a4b5b78a27613c3ef0d2845ece6da3a0f1c7350a8`.
The exact terminal consumers at ROM551554/551560 place A Enter at(108,177)
and B Delete at(164,177). These two sources have independent ownership caches,
exact palette/consumer guards, genuine artist replacement and one-line physical
font fallback. They do not inherit or modify the Career bank94 pair's ownership.
The actual-snapshot test verifies Nintendo B/A physical requests together with
the source A/B logical positions and preserves every byte outside each icon.

The completed steady commercial-title snapshot now identifies its separate
3D prompt: script80086FB4 creates model0B from original asset228, followed by
steady script80086FD0. Original47818 loads the model; original3E814/33B70 apply
exactly60 relocation words to its5648bytes. Normalizing those verified vertex,
texture-reference and pointer-table relocations reproduces SHA-256
`9426249b731453a9059de98b51a673dc0ee018e5494843597b99da6ee8361752`.
The title root owns exactly20 child meshes; completed original Gfx contains each
of the20 corresponding DE calls once per task arena. This is separate from the
scripted background and logo, and from the legacy resident text prompt.

`prompt_title_model` preflights that complete original model, root/child ownership,
steady state, original320x240 framebuffer, exact font asset0D, original font2
palette pointer/32bytes and one complete newly emitted20-part draw. It proposes
one original-font physical Start line. The completed original matrices project
the mesh bounds to native(89.72,160.46)..(229.43,178.35); font y164 lies inside
that band. Only after the original font draws successfully may the caller NOP
the20 verified original DE calls. The entire preflight repeats before any NOP;
appended font commands, previous task arenas, original model/animation, CPU
callbacks, logo and copyright remain untouched. Partial draws, foreign assets,
invalid frames or failed font preflight preserve the original draw.

`tests/test_title_model_prompt.py` verifies the original completed draw commands,
projected geometry, complete/duplicate/missing-part rejection, foreign font and
palette rejection, successful font-command append and byte-exact write ownership.
The saved completed snapshot had already reset the next-frame Gfx cursor; the
CPU test restores only that cursor to the known original pass end. A separate
synthetic-command fixture uses the real pre-draw model/font snapshot and is
explicitly a CPU transaction test. Private original-body hashes and title proof
are in `.local/pal-prompt-research-05/title-model-proof.json`. Visible adapted
title output still requires the parent acceptance run.


The initial8002B618 integration boundary was not reached by the actual steady
title (visible build30), despite the CPU wrapper test passing. Static original
callers distinguish that special renderer from the normal8002B9B4 route. Title
adaptation now belongs after the existing whole-frame80000BB8 original call.
Original80002A10 sets the current arena at2A2C/2A44, initializes its cursor at
2AEC, calls00BB8 at2AF0 and only afterward finalizes/submits the graphics task
(01834 call at2CDC). The adapter accepts current arena begin..cursor, still
requiring exactly the20 owned model calls. The completed-title CPU regression
also exercises the whole current arena, preserving every earlier pass except
those20 calls. This establishes the guarded frame boundary; visible adapted
output remains a separate acceptance step.

Parent acceptance capture260 (`260-title-after-frame-prompt.png`) confirms the
commercial title now displays `PRESS Return` through the original font after
whole-frame integration. The original logo/copyright and background remain
visible. This confirms the keyboard route for that actual title frame; it does
not establish physical-controller hardware verification or complete coverage of
other original instruction sources.


The genuine completed team-selection snapshot also identifies the original cyan
L/Z/R region hints as a separate common-atlas consumer. Resource bank45/index119
at ROM45D03C points to the exact60-byte consumer ROM2EFD50 (guest801BE700).
Its offscreen first segment advances to index120, so the guard validates both
128x32 CI4 descriptor images, the original palette and the entire consumer.
The decoded original asset19 images match the captured sources at offsets0/800.
No shared atlas or palette bytes are changed.

For the proven single-player mode8012DE56=1, original callbacks802A135C and
802A14F0 both map card index1 back to controller0. Four original-font lines
therefore replace only this exact combined hint. The first layout placed physical
L/Z at(30,52)/(166,52) and R at(123,52)/(258,52). Its CPU ink test allowed only
a two-pixel gap after the region letter. Actual hidden capture menu-032 showed
that R visually joined EUROPE B/A and L extended outside the card. The narrow
ink-gap criterion did not establish a readable layout and has been superseded. Font/frame, scale,
viewport, consumer, both images and palette all remain exact guarded inputs.
Other modes are rejected until separate card ownership is proven; a global P1
default would be incorrect for mixed-family multiplayer.

`tests/test_team_region_prompts.py` uses that completed original snapshot, checks
the neighboring glyph ink and all four font proposals, and verifies byte-exact
nonmutation plus rejection for multiplayer, foreign assets/font/palette/consumer,
scaled/high-resolution frames and unsupported physical names. Its ownership test
failed before the mode guard and passed after. This establishes CPU proposal
behavior; actual adapted team-region output still needs hidden GPU acceptance.
Private proof is `.local/pal-prompt-research-05/team-region-proof.json`.


The completed field16 set-play frame proves a different packed Start instruction:
bank2/index142 is the original64x56 I4 atlas from asset55+10A00. The exact
36-byte consumer at8025FC90 draws StartButton at(116,19), then the equals
separator twice at(164,20). The GameControls image is a separate object with
its own terminal consumer8025FFA8 at(172,19); it remains an ordinary original
draw. Whole-atlas SHA-256 is
`32bff5e761ac0082d6348e3a026c2c192f3b2cc022e76aca23132c9b87186d7a`,
and whole-consumer SHA-256 is
`6b02ed26e70b9dcab0973eb9bb70c954c9840575de664b2521c4bd208910a3e9`.
Original801DDD5C directly consumes logical Start mask1000 to open the original
pause/game-controls route. This is independent of the random-team Start image.

The guarded adapter proposes the physical Start label alone, centered within
the original48-pixel cell, using the original font at y17. Its12-pixel band
ends at29, inside the original panel; GameControls begins at172 and is left
untouched. The original caller suppresses only the complete owned Start sprite
after successful original-font drawing. Dropping its equals separator produces
a standard physical-button/action layout without pointer rewriting or extra
rendering paths. Menu, Options, Plus, Return and bounded remapped labels fit;
unsupported labels, foreign atlases/consumers/fonts, shifted/scaled origins and
nonstandard frames fail closed. Since this is I4, unused palette overrides do
not participate in ownership.

`tests/test_field_start_prompt.py` verifies the actual completed field snapshot,
all those physical labels and negative guards, nonmutation of the complete RAM
and preservation of the separate GameControls consumer. It failed with an
unrelated original source before the adapter and passes after. Adapted hidden
GPU acceptance remains pending. The independent original ROM, constructor,
consumer and offline-original-draw proof is recorded privately under
`.local/pal-field-prompts-01/proof.json`.


The completed original pause-controls frame identifies the separate four-prefix
sprite at bank2/index141 (64x64 I4, original asset55+10200). Its entire120-byte
consumer8025EA00 and2048-byte atlas are pinned, with the original action labels
remaining in a separate sprite at8013D958. Only the literal Z/R physical labels
change. The logical instructions `1 2 Pass Button` and `T Pass Button` retain
their names; the separate KickerChange, ArrowOnOff, ChangeLocation and
SwitchScreens images remain untouched. All shared atlas bytes remain unchanged.

The original font supports per-axis scaling at80048B48: font-object flags+C
bit8 reads scale-owner+28/+2C. Font2 X1/Y2/3 produces six-pixel advances and
eight-pixel rectangles through the original48660 call graph, using the same
guarded asset0D. Offline execution of that exact original path on the captured
pause frame emits27 glyph rectangles for the four proposed lines. Their bounds
are x123..135 at y192..200, x123..135 at200..208, x74..164 at208..216 and
x86..164 at216..224. These stay inside the original panel beginning x72 and
above its body bottom226; the separate action labels begin x153/167. The font
source Y values are191/199/207/215 because the original glyph renderer adds one.
The four-row proposal therefore carries explicit height8; every older proposal
continues to default to height12. Private original words and full bounding proof
are `.local/pal-field-prompts-01/font8-proof.json`.

Controller ownership is explicit. Original801DDD5C loops ports0..3 and stores
the port which opened pause plus1 at8012DE37. The resolver returns this port
only after the entire exact pause sprite, image, consumer, normal framebuffer,
font and origin pass their guards. Z/R requests must carry the same port; stale
P1 requests cannot adapt a P2/P3/P4 pause screen. The new per-request port field
defaults to0 for existing callers. The single-player team-region proposal also
rejects nonzero request ports. Actual-snapshot tests exercise every port value,
invalid/stale owners, complete nonmutation, all row bounds and unchanged
separate actions. These are CPU checks; hidden GPU acceptance remains separate.


Hidden build35 acceptance of the team screen exposed an actual layout defect:
physical LB/LT appeared outside/alongside the card heading and RB visually joined
its original EUROPE B/A page letter. Those B/A letters belong to separate
original region-heading objects57/58; they are not N64 physical button prompts
and remain untouched. The correction changes only the guarded team-region
proposal, using the now-proven original eight-pixel font path in its own row.

Exact original snapshot geometry gives SelectTeams foreground glyphs Y20..36
and the card frames starting Y48. The four font proposals now have inputY39,
which emits actualY40..48, leaving four pixels below title ink and ending at
the card border. Their X positions43/130/179/266 keep each complete label inside
the two card envelopes40..144 and176..280. Font width, source assets and original
headers stay unchanged. The snapshot regression now asserts the actual title
segments, card start, per-line height and separate-row bounds; it fails against
the earlier layout and passes after this correction. Hidden GPU acceptance must
still verify the new row's readability and contrast; CPU coordinates alone do
not establish those visual properties.


The global on-field Start tooltip has a different owner policy from pause.
Original801DDD5C accepts Start from all four ports, so assigning this one global
hint permanently to P1 can show a wrong physical name in mixed-controller games.
The host now records the last meaningful mapped keyboard or known-controller
input event under its existing input mutex. Keyboard actions/movement select P1;
controller button presses and axes exceeding12000 select their assigned port.
Small movements, releases, repeats and unknown device IDs do not steal selection.
Trigger activation requires a positive value. Active removal or a detached
controller falls back to P1. Logical input mapping and bindings are unchanged.

The prompt resolver accepts that active host port only after the complete exact
field-Start I4 image, consumer, original font, framebuffer and geometry pass all
guards. Other sprites retain their own ownership; the exact pause prefix still
uses8012DE37 even when the last host event came from another port. The optional
resolver argument defaults to absent for existing callers. Input snapshots then
carry the resolved explicit port through every physical request.

`tests/test_active_input_port.py` executes the actual production event observer
and getter against four isolated SDL controller handles, without a game, window
or OS input injection. It verifies event ordering, thresholds, mapped keyboard
input, unknown IDs and both removal-event and detached-handle fallback. The
actual field-snapshot tests verify all four active ports, unrelated/foreign-source
rejection, configured resolver behavior and unchanged original pause ownership.
The tests failed before these capabilities and pass after; mixed-controller
hardware acceptance remains a separate step.


Hidden build36 capture322 confirms the separate team hint row clears the
original headings, but white glyphs remain difficult to read on the bright blue
background. The correction uses an existing original-font color selector, with
no texture edits, background panel or independent overlay. The selector is the
font object's byte at hex offset12; offset5 instead selects the text format.
For these font2 I4 glyphs, original49454 dispatches49780/499B8, which reads RGB
triples at800876B0. Selector4 is black000000. The alternative CI4 palette path
is unused here; its black palette index2 would instead choose light blue in the
actual I4 tint path and must not be used for this correction.

The entire original48-byte tint table is pinned by SHA-256
`9e9815495c5e7239bbb7278da97e9ca4b07581d82b43a29378a2985f5bd6681d`.
Only the exact team-region profile proposes selector4 after that guard passes.
Other text proposals retain default selector0. Actual original-font execution
on the saved team frame emits `FA000000 000000FF` before each line's I4 glyph
loads, with every earlier rectangle and texture coordinate unchanged. A foreign
tint table rejects the proposal; no original palette/table bytes are modified.
The selector test fails against the white proposal and passes after the change.
Corrected hidden GPU contrast acceptance remains pending.
