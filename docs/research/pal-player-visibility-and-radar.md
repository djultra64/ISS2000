# PAL player visibility, radar sampling and analog response (r55)

Original project work: djultra64. Private evidence stays under `.local/corrections-r55/`.

## All 22 highest-detail players

The original field callback selects detail variant zero for outfield players.
The previous culling guard accepted only variants one/two, so its synthetic
variant-one fixtures missed the live maximum-detail case. A genuine captured
field now covers variant zero. The native wrapper still calls the original
visibility function once, then retains all first22 verified football rigs in
field scene6/4. Unrelated objects keep the original behavior; GPU clipping
naturally determines what reaches the viewport.

Disabling this CPU rejection alone is insufficient: original80025910 owns two
0x5100-byte banks, only324 matrices per bank. Executing original8002B30C and its
real callbacks against captured field RAM reproduced14 retained players and
8009DF24 overflow with the original small pool. The corrected traversal retains
all22, writes all418 distinct bone matrices, and leaves overflow clear.

The port reserves807C0000..807E0000 as two0x10000-byte field banks. The verified
High framebuffer/depth end at807AA000; original80008DB4 loads High code and
clears its BSS only through807B4A60. Static code references and original Low/High
captures were checked before selecting this separate region. The nearly full
original bump heap is not extended. Redirection requires the exact freshly
initialized original cursor/end,8MiB detection, bank, scene and video layout.
Menus continue using original banks. Transform snapshots and shadow ownership
accept both exact bank pairs, preserving retained-task lifetimes and rejecting
foreign bounds.

## Right-half radar seams

The original High sprite emits14 primary rectangles plus28 one-pixel repair
strips. The primary rectangles already cover every pixel of the160x112 radar
once. Repair strips overlap subsequent pieces, blending translucent pixels
again. More narrow pieces on the right cause the uneven opaque grid.

After validating the exact original texture, all42 rectangles, source UVs,
derivatives and owned output bounds, only the28 redundant rectangles receive
zero-area bounds. The14 main pieces, texture data, state and command lengths
remain unchanged. An actual original-producer regression checks one coverage
per pixel and unchanged foreign/4:3 output.

## White lines on radar dots

Each marker uses an8x8 cell in the original32x32 atlas. Fractional upscale
positions could put the final sample at7.997texels; the pinned POINT shader
rounds to1/128 and reaches the adjacent cell. At the atlas edge this wraps into
another icon. The exact original marker adapter now insets UVs7/32texel and uses
High496/Low992 derivatives. The resulting endpoint remains inside the cell,
while all native Low integer and High half-texel samples retain their original
texels. The sprite phase preparation recognizes these exact derivatives.

Sampling checks cover720p,1080p,1440p,2160p and other supported resolutions:
32 adjacent-cell samples before, zero after. This does not replace a complete
visual sweep of every gameplay mode or every frame.

## Analog precision

Gameplay left-stick input now has a continuous radial15% deadzone and a gentler
low/middle response: normalized magnitude m becomes m*(0.5+0.5*m). Direction,
full-deflection range and maximum running speed remain intact. Menu navigation,
keyboard/D-pad, triggers and right stick are unchanged. Tests use the real
native-axis conversion and check center continuity, monotonic output, symmetry,
full range and invalid values. Physical ROG Ally corner/free-kick feel remains
a manual acceptance item; these checks do not claim physical-device testing.
