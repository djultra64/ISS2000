# PAL identity-sprite texel phase

Original project work: djultra64.

## Observed boundary

The user's Select Training capture showed vertical discontinuities in the
backgrounds of Free Training, Free Kick, Corner Kick and Keeper Training. The
matching actual post-BB8 frame is private `select-training49-completed.rdram`.
Its active frame is **Low 320 by 240**, even though the requested gameplay
resolution is High. Its material is original one-cycle POINT, not the High
COPY branch covered by `prepare_pal_high_sprites.py`.

The real task contains four background bars from atlas `80279600`, with 19
pieces each. Original segment list `802B9CFC` mixes 16-pixel-high caps and
8-pixel-high repeated center cells, at original y73,92,111,130. The original
texture coordinates and POINT filtering are intentional. No smoothing or
source-art modification is needed to explain the sampled phase discrepancy.

Pinned RT64 `convertViewportRect` independently rounds each piece's physical
edges, then interpolates the unchanged native UV span over that rounded extent.
For a fractional PAL output scale the resulting UV-per-pixel slope differs
between adjacent pieces. At scale1080/232, the y130 cap becomes75 GPU rows while
its 8-row center becomes37 rows; the same physical offset14 samples source row2
in the cap and row3 in the center. This is a CPU characterization of the real
display list and renderer geometry, not a new GPU acceptance claim.

## Bounded private derivative

`tools/prepare_rt64_sprite_phase.py` verifies the complete original framebuffer
renderer source SHA256 before generating a separate private source file. The
upstream dependency is never modified. Only the Rectangle callsite can select
the additional viewport helper. Its complete guard requires:

- Both origins are the ordinary centered origin.
- No GPU framebuffer tile copy is involved.
- RT64 already selected upscaled2D rendering.
- Original rectangle derivatives have identity magnitude.
- Original cycle is one-cycle and filtering is POINT.

The helper retains fractional physical viewport edges, using the same original
center/aspect/scale transformation. Original native rectangle coordinates, UVs,
UV derivatives, filters, texture contents, material state and scissor behavior
remain unchanged. COPY, two-cycle/fill, 3D, explicitly anchored HUD rectangles,
nonupscaled rectangles and framebuffer copies retain the original helper.
Integer native transforms produce exactly the original viewport.

Generate with:

```
python3 -m tools.prepare_rt64_sprite_phase \
  --source .local/deps/rt64/src/render/rt64_framebuffer_renderer.cpp \
  --output .local/rt64-sprite-phase-v1
```

Compile its `rt64_framebuffer_renderer.cpp` as the full replacement for the
pinned original source. Retain original `src/render` include resolution and the
same HLSL_CPU/FFX_GCC compile definitions. Output receipts are immutable and
explicit UTF-8 bytes, including on Windows; no Windows build was performed.

## Verification and remaining acceptance

The original rounded helper failed the actual-frame phase regression before the
fractional-edge correction. The final focused run passed two tests with zero
skips in0.355seconds. Tests parse all76 genuine background pieces from the
completed task and exercise720/900/1080/1440/1800/2160 output profiles in4:3 and
16:9. Across87,962 POINT sample comparisons against the original native texel
phase, the original rounded geometry differed3,226times and the bounded
correction differed zero times. Foreign origins, nonupscaled, scaled, COPY,
other cycle/filter cases and integer native geometry remain excluded or
byte-identical. Source hash, immutable output and LF-byte contracts also pass.

Private generated proof source SHA256 is
`cc411c471767cb3301e5ddda0743f6bc1afb0392b1b619d061b27c46316a4773`.
Actual integrated before/after GPU capture of the same Training screen is still
required before calling the visible seams fixed. This module's tests do not
launch a game and do not establish all unrelated sprites visually correct.

## Revision 3: exact intro joins, original High sprites and menu motion

The v1 generated digest above records the first derivative only. New builds use
an immutable `rt64-sprite-phase-v3` output folder; they do not overwrite v1.
The original complete source pin remains unchanged.

The reported intro line has a separate cause from the Training texture seams.
The authentic CI8 intro uses centered original image rectangles and two authored
constant-UV white side strips. The center now has fractional physical edges,
while the explicitly anchored strips previously retained rounded edges. That
can expose a subpixel gap at the old 4:3 boundary. Revision 3 admits only those
two exact full-height side shapes to the same fractional coordinate transform:
left `(-4,0)..(0,960)` with LEFT/NONE origins and right
`(1280,0)..(1284,960)` after original origin translation, with NONE/RIGHT origins.
It additionally requires one-cycle POINT, ADJUST aspect, upscaled2D and both UV
derivatives zero. Neither strip overlaps the original image, so intermediate
fade alpha is applied once. All other explicit origins retain their prior path.

Original High sprites double geometry and halve identity UV derivatives to
512. In a 640-wide framebuffer, those signed half derivatives now qualify for
the same regular-origin, upscaled one-cycle POINT phase correction. COPY is
still excluded. The genuine completed High43 radar task contains fourteen such
pieces, including mirrored texture coordinates. Across all six supported output
heights and both aspect profiles, the original rounded helper differs from its
native texel phase 932 times; the fractional helper differs zero times. This is
in addition to the 87,962 genuine Low Training-bar sample comparisons above.

Revision 3 also consumes independently validated adjacent menu rectangle
metadata to interpolate previous/current physical viewports at RT64's actual
fractional render weight. Its source coordinates, UVs, filtering and simulation
remain unchanged. Exact endpoints return the original endpoint viewport. See
[PAL menu interpolation](pal-menu-interpolation.md) for matching, ownership,
color upload lifetime and the limits of CPU verification.

The focused geometry checks retain all original guard negatives, check all
fourteen actual High radar pieces, and prove that both intro joins exactly meet
the center without a gap or double-alpha overlap at720 through2160 output
heights. No game process was launched for this correction. Actual user GPU
acceptance of the new derivative remains pending.
