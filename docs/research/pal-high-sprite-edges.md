# PAL High COPY sprite edges

Original project work: `djultra64`.

The original PAL High sprite leaf is `807AA008` in overlay `515890/807AA000`
(ROM `515898..515B4C`,692bytes). Resident sprite producer `80041B50` calls it at
`80042388` when the original frame's High byte is set. It doubles screen
coordinates and halves the main texture derivatives. This is an original
presentation path, independent of transform interpolation and simulation speed.

The existing RT64 `Upscale2D::All` setting bypasses the shader's low-resolution
UV snapping. It cannot fix this separate High-path issue: the original High
leaf also emits right/bottom edge rectangles with full perpendicular texture
rates. RT64 COPY handling makes those edges two High pixels wide/high. At
fractional output scales their interpolated coordinates sample a preceding or
following atlas texel, creating seams and stray lines.

The edges must remain. Original `80041F88..80041FC4` subtracts one source pixel
from COPY endpoints. For the actual8×16 segment at `80261844`, belonging to
sprite3 at `8013C530`, the main High rectangle covers seven source columns;
the right edge supplies the genuine eighth column. Removing both edge rectangles
would crop the asset. The original format19 branch uses a different material
and does not emit these edges.

`tools.prepare_pal_high_sprites` generates a private derivative that executes
all original instructions and then changes four words in the original72byte
output:

- Right edge: advance its initial U by8/32 to the exact final source column and
  set its horizontal derivative to zero.
- Bottom edge: advance its initial V by8/32 to the exact final source row and
  set its vertical derivative to zero.

The Gfx cursor, rectangle count, every screen coordinate, main rectangle UV and
derivatives, material, original CPU context and original assets remain intact.
Only original mode0 is eligible. Original `800423FC` resolves that mode through
`80085F90` to material list `8009CB78`, whose first command selects COPY.
Other formats, including19, retain the complete original result.

The guard requires the canonical original cursor pointer `8009E0C8`, original
material cache0 at `800BDB26`, frame pointer `8009E02C→8013B418`, High byte1,
and640×544 dimensions. A72byte aligned reservation must fit one of the two
original graphics arenas. After original execution, the cursor must have
advanced exactly72bytes and all three E4/E1/F1 groups must have the exact
original edge geometry relationship. All checks precede any mutation. Rejected
cases keep the original output. The upstream header and original CPU/ROM inputs
remain untouched; the generated C++ unit includes the reviewed Windows strong
entry definition.

Focused CPU verification executes the actual pinned original leaf and its
derivative. Its original72byte result matches the genuine High snapshot's
sequence at `800D2520`. It compares the complete8MiB result and guest context:
only the four identified edge words change. It checks rejected frames, formats,
caches, pointers, unaligned/insufficient reservations and malformed command
sequences. The numerical regression compiles the pinned RT64 FixedRect and
viewport conversion implementations, accounts for COPY inclusive endpoints,
COPY horizontal derivative division and the renderer's half-pixel offset, and
checks edge samples at scales1,1.5 and output heights720,1080,1440,2160. Mirrored
and clamped sampling preserve the intended final column/row. The original
sampling is retained as a failing numerical control.

Run `python3 -m unittest tests.test_pal_high_sprites -v`. The private generator
uses `--rom`, `--source` and `--output`, exporting
`iss2000_pal_high_sprite_edges(uint8_t*, recomp_context*)`. Hook only the exact
active original `807AA008` identity. Actual hidden GPU comparison remains the
parent's integration acceptance step; CPU/numerical checks alone do not claim
that the visible defect is resolved.

## 2026-10-21: verified one-cycle POINT scoreboard material

The copy-only restriction above records revision1. The resolution audit found
that the score panel uses original sprite mode2 (`0x04026642`) and material
`8009CC20`, selected by table entry `80085F98`. Its pinned original list selects
one-cycle rendering and POINT filtering. Its High leaf emits the same72-byte
body/right/bottom pattern, with right/bottom starts one quarter texel before
the final source column/row. The initial hypothesis was that their sampling caused the repeated bright dots; integrated GPU comparison rejected that hypothesis.

Revision2 admits exactly mode0/cache0 and mode2/cache2, verifies the original
material2 cycle/filter words in the ROM, and applies the same four edge-word
changes. Format19 and all other modes/cache mismatches retain their original
results. The new original-CPU regression first failed on the uncorrected mode2
edge rates, then passed with full context and8MiB difference checks and sample
comparisons through2160 output. Existing COPY controls and guard negatives pass.
The immutable build directory is now `pal-high-sprites-v2`; revision1 output is
retained. This paragraph records CPU proof; the audit record separately records
actual integrated GPU verification and any remaining limits.


### Revision3: one-cycle duplicate coverage

Actual `pixel05-integrated-2160` retained the bright dots after revision2.
Its authentic emitted commands confirm revision2 did run (edge dS=0), so this
was a failed visible fix, not an unexecuted patch. The score panel main chunk
covers native x44 through92 exclusively; its right strip covers92 through93,
while the next chunk starts at92. Another join repeats the overlap at108.
The translucent top border is therefore blended twice at these joins. The
source atlas contains a uniform border rather than those bright marks.

Revision3 keeps COPY's four sampling-word corrections. For verified mode2
one-cycle POINT only, it instead makes right and bottom repair strips empty by
setting each strip's far endpoint equal to its near endpoint. Only two geometry
words change; the main rectangle, every source coordinate/derivative, the72-byte
command body length, CPU context and cursor remain. The original-CPU regression first
failed against revision2, then passed against revision3. Real RT64 rectangle
conversion gives zero strip width/height at native,1080 and2160 scales. The
immutable stage is `pal-high-sprites-v3`; earlier stages remain private and
unchanged. Integrated GPU comparison in `pixel06-point-v3-2160` confirms the top-border bright dots are absent over both crowd and green-field backgrounds. The precise candidate and remaining1080p checks are recorded in `pal-resolution-audit.md`.
