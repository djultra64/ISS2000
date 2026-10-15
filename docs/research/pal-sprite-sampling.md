# PAL sprite sampling at enhanced resolutions

Original project work: djultra64.

The shared sprite sampler now selects RT64's supported `Upscale2D::All`
configuration. The default `ScaledOnly` configuration applies a screen-grid UV
adjustment to identity-scale rectangles. At fractional output scales, that
adjustment gives independently positioned sprite tiles different source-texel
phases. The original sprite commands and asset pixels remain unchanged.

## Evidence and cause

Private captures `87-pal-pause-native.png`, `88-pal-pause-1080.png`, and
`89-pal-pause-all-sprites.png` show the same paused scene. The transition from
87 to88 changes only the original rendering resolution to the 1080 setting;
Original refresh and the wide aspect setting remain fixed. Capture88 has
visible horizontal breakup in the P1 pause heading. The transition from88 to89
changes only `upscale2D` from `ScaledOnly` to `All`, followed by RT64's normal
configuration update. The heading and menu text become continuous in89.

The paused PAL P1 glyph command at `800D3888` has original rectangle
`(122,33)..(146,41)`, identity texture derivatives `(1024,1024)`, and texture
source `80207540`. At the diagnostic scale `1080/296`, its rounded viewport top
is120 and bottom150. RT64's default shader subtracts
`fmod(120,1080/296) * (8/30) = 0.86486486` source texels from its first vertical
sample. A texture coordinate that should begin at zero therefore becomes
negative. Point sampling can read the previous row or wrap to another tile.
The supported All option preserves the rectangle's interpolated texture
coordinates, eliminating this screen-relative phase adjustment. At scale1,
the old subtraction is zero and both options preserve the same coordinates.

The relevant pinned RT64 code is:

- `hle/rt64_state.cpp`: `ScaledOnly` leaves identity rectangles with
  `flags.upscale2D=false`; copy rectangles first normalize horizontal texture
  derivatives in `hle/rt64_rdp.cpp`.
- `shaders/RasterPS.hlsl`: the false flag subtracts
  `fmod(screenPos.xy,resolutionScale.yy) * (ddxUV.x,ddyUV.y)`.
- `render/rt64_framebuffer_renderer.cpp`: each rectangle's viewport edges are
  rounded independently to output pixels.

Following both actual graphics tasks in each saved native-word RDRAM snapshot
produces these original command counts per task:

| Snapshot | Texture rectangles | Identity derivatives after copy normalization | Fractional guest edges |
| --- | ---: | ---: | ---: |
| field06 | 130 | 128 | 0 |
| match-intro06 | 73 | 73 | 0 |
| pause06 | 92 | 92 | 0 |

These are bounded display-list walks from original task headers, including
nested calls and othermode updates. The absence of quarter-pixel edges rules
out the initially suspected fractional-Y offset in `RDP::drawRect` for these
snapshots. The original PAL sprite emitter `80041B50` routes these sprites
through ordinary texture rectangles. No per-sprite coordinate or texture repair
is needed for this sampling defect.

Private `.local/pal-sprite-sampling-01/proof.json` records the ROM identity,
upstream source hashes, snapshot hashes, walked rectangle commands, numerical
case and controlled capture hashes. Its adjacent read-only audit script can
regenerate the receipt.

## Verification and remaining acceptance

`python3 -m unittest tests.test_rt64_sprite_sampling -v` compiles the actual
pinned upstream fragment adjustment, state flag expressions and identity-scale
predicate against synthetic inputs. It reproduces the negative first sample
with the previous default, checks the configured path at all six enhanced
heights, verifies scale1 equivalence, both derivative signs, and the existing
continuous path for already-scaled rectangles. The original configuration
failed this regression before the integration change.

The menu comparison directly verifies this fix. Visible revisits of the
coin/ball selection, direction arrows, KICK OFF lettering and player nameplates
remain necessary to accept every reported symptom. The separate bottom band
and target-height issue seen in the same screenshots is outside this sampler
change. No Windows build or execution was performed for this investigation.
