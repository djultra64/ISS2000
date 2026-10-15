# PAL sky-only widescreen correction

Original project work: djultra64.

The PAL stadium sky is emitted by original resident function `0x80035CC0`
(ROM `0x368C0..0x371EC`), called at `0x80000E6C`. It converts the original
camera direction to panoramic scroll coordinates, fills per-texture placement
lists, and draws six columns of 64-by-32 rectangles. Its explicit clipping to
320-by-240 explains the sky sidebars when the perspective field already fills
16:9. This function is separate from HUD/menu sprite rendering.

The exact PAL identity, original body hash and generated-source hash are pinned
in `tools/prepare_pal_sky.py`. The generator creates a private derivative; it
never edits the original generated CPU input, ROM, or RT64 checkout. Original
camera math, sky texture/TLUT loading, vertical coordinates, mode guards and
simulation remain original. Only horizontal sky coverage and rectangle emission
change.

Eight columns include the preceding panoramic tile and cover the virtual range
`[-53 1/3, 373 1/3]`. Their guest x coordinates are compressed around center by
3/4, while horizontal sampling increases by 4/3. Scoped RT64 rectangle aspect
then expands that geometry by 4/3, restoring the original physical tile width
and texture proportions. Thus this does not expand a six-column sky image by
stretching its clouds. Copy-cycle texture slope uses the nearest representable
fixed-point value (5461 at native size, 2731 at the game's doubled size).
All other 2D draws retain their original aspect mode. Extended GBI is enabled
through its native F3DEX2 no-op hook, and rectangle aspect returns to AUTO before
the original trailing fill operation.

## Original memory bounds

`0x800006A4` selects frame records at `0x800D0320` and `0x800E0380` with stride
`0x10060`. `0x80002A10` writes the active record to `0x800A4AA4`, begins its Gfx
array at record+8, and accesses OSTask metadata from record+`0x10008`. Therefore
the reviewed Gfx interval is `[record+8, record+0x10008)`. The original current
write pointer is `0x8009E0C8`. `pal_gfx_bounds` requires the exact record choice,
canonical addresses, alignment and cursor range. It rejects inactive zero
records rather than inferring capacity from unrelated arenas.

The sky lists at `0x800BC1C8` have sixteen `0x140`-byte regions containing
8-byte placement records and an original terminator. The relevant original
24-by-14 tile table at `0x8008384C` alternates a distinct even/odd texture pair
per row. The helper checks every byte of that table before expanding coverage.
Eight rows of eight columns produce at most 32 records per texture, below the
39-record usable capacity. All generated rectangle and extension writes also
check the Gfx end. The full derivative requires at most `0xA10` bytes; preflight
reserves `0xA20`. No guessed allocation limit or arbitrary extra guest scratch
memory is used.

## Integration

Generate the private source with:

```sh
python3 -m tools.prepare_pal_sky \
  --rom .local/inputs/pal-en-de/rom.z64 \
  --source .local/pal-map-bound-01/functions/func_80035CC0_resident.c \
  --output .local/pal-wide-sky-02
```

Compile its `pal_wide_sky.cpp` and `src/runtime/pal_sky_widescreen.cpp` for PAL.
Hook original `0x80035CC0`. Construct `PalSkyWriteScope` around the derivative
only when 16:9 is selected; if it rejects the data, run the unchanged original
body. The derivative export is `extern "C" void iss2000_pal_wide_sky(uint8_t*,
recomp_context*)`. No renderer-global 2D stretch setting is required.

## Verification and limits

`python3 -m unittest tests.test_pal_sky_widescreen -v` verifies coverage across
all 64 horizontal sub-tile scroll phases, normal/doubled game coordinates,
clipped UV origins, scoped aspect commands, original table guards, allocation
end validation and unchanged bytes outside bounded writes.

Private `.local/pal-sky-evidence/field06.json` compares the actual original sky
function and derivative on copies of `.local/pal-acceptance/field06.rdram`.
The fixture selects the original eight-row option in both copies, because the
captured gameplay camera itself had no visible sky rectangles. It records 64
rectangles, coverage 0..1280 quarter-pixels, two scoped aspect commands, original
2168 bytes versus derivative 2576 bytes, and identical original CPU side effects
outside sky placements, their cursors, and Gfx output. This is an isolated
function fixture, not a game execution or GPU screenshot. Sanitizer libraries
were unavailable in this environment; the fixture ran without them.

Visible full-game acceptance remains the root task's responsibility, including
stadium introduction, replay, both original game sizes and native/2160p output.
