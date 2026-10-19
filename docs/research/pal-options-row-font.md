# Original PAL Options row face

Original project work: djultra64.

The original Options rows are precomposed **CI4** words, separate from the
common-menu **I4** heading alphabet. The previous native body reused the heading
alphabet at three-quarter scale. Matching the game's original row face requires
its original word pixels and palettes at unit scale instead.

Original PAL asset `42` has decoded SHA-256
`5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8`.
Bank 114/index 2 descriptor `802D1C3C` contains
`00800020 01000000 80277640`: a 128 by 32 CI4 image containing Delete Registered
Player and Resolution. The latter uses the lower 16-pixel row. The original
Create Player and Game Setting words are in the same verified asset. No original
ROM pixels are distributed with this implementation; the validated user ROM
supplies them at runtime.

`pal_options_row_bitmap` copies only existing source pixels. PC Settings uses:

| Piece | Asset offset | Atlas width | Source x | Source y | Width |
|---|---:|---:|---:|---:|---:|
| P from Create Player | 700 | 96 | 48 | 16 | 12 |
| C from Create Player | 700 | 96 | 0 | 16 | 10 |
| Transparent word gap | — | — | — | — | 5 |
| Setting from Game Setting | 0 | 112 | 42 | 16 | 49 |
| s from Resolution | D00 | 128 | 18 | 16 | 7 |

Every piece retains its original 16-pixel source row and palette indices. The
result occupies 83 columns in an owned 128 by 16 CI4 bitmap. Its SHA-256 is
`886a8bfdfcbeffed201ab265a8fc0cc3ff264bf2c5ed703686cd99ad47fa3051`.
The tests also reconstruct original Setting, Game Setting, Create Player and
Resolution words pixel-for-pixel from their source slices.

The PC Settings and Graphics body rows use further bounded column crops from
**this same asset only**. This is not a recovered complete alphabet. Natural
labels originally avoided absent letters. The current correction adds the exact
user-requested Save options and Framerate limit labels:

| Settings key | Displayed row |
|---|---|
| Graphics | Picture |
| Save options | Save options |
| Aspect | Screen ratio |
| Framerate limit | Framerate limit |
| Back | Go back |

Controls, Cancel, Resolution and Screen retain their names. The original heading
alphabet remains reserved for headings on these pages, and the original small
font renders values/help. The pre-match Controller screen owns football types separately.

The extra lowercase p comes from player in asset42 offset2000, width64,
x20/y48, width9. Lowercase v is the right diagonal pair of w in New in the
same block, x24/y0, width6; the two unused trailing columns are excluded to
preserve the row spacing. Uppercase F is explicitly reconstructed from the
upper eight rows of E in Enter Password (offset2800, width128, x0/y0) and
the lower stem of P from Create Player. This is a same-face stroke composition,
not a claim that a complete original F image or font file was recovered.
All palette indices and antialiasing remain from those original strokes.

Original row palettes are independently pinned to completed original Options
RAM and the ROM. Unselected palette `803EF6C0` matches ROM `35E3E0`, SHA-256
`b51101957be8c54798b3c72fa1ebe1abaa375a434b4c646f74f80ace37435c95`.
Selected palette `803EF6E0` matches ROM `353890`, SHA-256
`18721d075d73e4c8a94d4d98473ca46fc3235d1c4697d359c63611e412da1c9d`.
The original sprite renderer consumes these CI4 palettes directly; the heading
font's vertex tint is not substituted for them.

All rows are validated before any guest writes. Unsupported page labels fail
closed without a heading-font fallback. Pixel/palette payloads belong to the
current graphics task's existing arena, behind a real display-list branch;
subsequent commands allocate after them. The original sprite initializer,
resource constructor and draw function produce the real CI4 commands at unit
scale. Focused CPU tests verify original pixel hashes, actual emitted row texture
and palette consumption, heading/body separation, context/stack ownership and
capacity rejection. These checks are separate from GPU appearance acceptance.

## Graphics footer capacity regression (r52)

The original italic footer metrics give Change57.75px, Apply and save120.75px,
and Back38.25px at the retained0.75 scale. Three16px glyphs, each followed by4px
text spacing, plus12px between items occupy302px. The prior preflight counted
an extra12px trailing gap (314px) against the304px plate and rejected the entire
Graphics page before drawing. The original Options page underneath consequently
remained visible. Only the final unused gap is now excluded; the fonts, glyph
sizes and plate remain unchanged. The genuine original sprite-closure regression
now draws all three actions for Xbox, PlayStation, Nintendo and keyboard, checks
actual glyph rectangles against the plate, and still rejects genuinely oversized
footers without guest writes. RED1 preceded the production correction; the
corrected original-function closure passes. This is CPU evidence, not a new game
capture.
