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
`5b452ff00298dc6d5015627e9de020fa8aa655e14b3282fa69d2ab11b146e99e`,
palette SHA-256 `b893ae3ef4c5ee2d11c62c06f3a35b7319328f53ef9e8724faaf707d795794a2`.
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
