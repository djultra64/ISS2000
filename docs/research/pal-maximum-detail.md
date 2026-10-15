# PAL original model and shadow detail

Original project work: djultra64.

The Europe English/German revision-0 game has genuine distance-selected model
LOD. The verified enhancement always selects its existing highest model detail
and articulated shadows. This applies to both presentation aspect ratios. It
does not invent meshes, textures, animation, or stadium detail.

## Original evidence

Input is the pinned 16 MiB PAL ROM, SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
All addresses below were recovered from this original PAL code and its original
data. Private reproducible analysis is `.local/pal-max-detail-01/audit.py`, with
body/table/snapshot hashes and counts in `evidence.json`.

`800300D0` reads the root model's signed depth at `+20`, then calls `8002EA50`.
The latter maps depth into levels bounded by the configured floor and level 6:

```text
floor = word[8007B0F4]
near = word[8007B0F8]
far = word[8007B0FC]
level = floor + clamp(trunc((6-floor)*(depth-near)/(far-near)), 0, 6-floor)
```

Depth sentinel 9998 returns the configured floor. That global is an LOD floor,
set by original `800314B8`; it must not be mistaken for a verified camera enum.
The original caller can promote selected models by two levels, then compares
the chosen level against the animation/model-state cache at `+BC`.

`8002EB64(state, level)` selects a type-specific table using signed type `+B8`
(0–6), assigns geometry to 19 original limbs, and applies the original
level-specific hierarchy/flags. Seven tables each contain seven 19-word rows:

| Original type | PAL table | Raw triangle references in rows 0 → 6 |
| --- | --- | --- |
| 0 | `8007B2F8` | 420, 290, 219, 133, 79, 48, 38 |
| 1 | `8007BB48` | 428, 321, 225, 143, 93, 52, 38 |
| 2 | `8007B50C` | 428, 428, 225, 169, 125, 52, 38 |
| 3 | `8007B720` | 464, 464, 219, 137, 93, 52, 38 |
| 4 | `8007BD5C` | 472, 472, 225, 143, 93, 52, 38 |
| 5 | `8007B934` | 420, 419, 219, 95, 62, 45, 35 |
| 6 | `8007BF70` | 428, 428, 225, 143, 93, 49, 35 |

These are bounded display-list triangle-reference counts from the original
loaded geometry in the saved `field06.rdram`, not claimed final rendered
triangle counts. Original head and outfit substitutions and visibility flags
still apply. Head slot 2 is selected independently from a runtime table at
`800B6CB0`, indexed by the original head variant and the same level. For the
saved head variant 0, its original lists contain 77, 49, 28, 28, 28, 4, 4
triangle references. Selecting level 0 therefore also preserves its original
highest head detail. The saved scene contains 25 articulated model states.

The original constructor paths `80030730` and `80030A90` already initialize
models through `8002EB64(..., 0)`. Original flag-change paths `80030DF8` and
`80030E20` reuse cached level `+BC`. Keeping that cache truthful is necessary:
changing geometry pointers alone would allow subsequent updates to restore a
lower level or rebuild unnecessarily.

`8002EB04` attaches an original shadow constructed by `80037894`. Its callback
`80037498` has separate distance-based detail for shadow modes 0/1. Original
near, medium and far display lists at `80083AD0`, `800839E8`, and `80083A78`
contain 28, 18 and 2 triangles respectively. Near generation `800368E8` writes
40 vertices into the existing per-frame 640-byte vertex buffer. The constructor
allocates 1280 bytes for the two existing buffers. Original mode 0/1 material
wrappers differ in alpha (`AA` versus `64`), which remains unchanged. Mode 2
has different position-dependent blending behavior and is preserved exactly.

## Bounded implementation

`tools/prepare_pal_max_detail.py` verifies the complete PAL ROM digest, both
original function bodies, and both original generated-source hashes before
creating private C++ derivatives. It refuses to alter existing derivative
outputs and revalidates their exact content on reuse. Original CPU inputs and
ROM remain untouched. Output receipts contain no developer-machine paths.

- `iss2000_pal_max_detail_models`: original `800300D0`, with selected register
  `s0` set to zero at the common `8003022C` path immediately before the original
  cache test and original type-specific geometry update. Thus original cache
  writes store level 0 and unchanged models avoid repeated geometry rebuilds.
- `iss2000_pal_max_detail_shadows`: original `80037498`, with modes 0/1 sent
  through their own original near material wrapper and original articulated
  generator after existing visibility/enable/buffer setup. Original shadow
  suppression and mode 2 remain intact.

No changes are made to original frustum tests, depth computation/sorting,
matrix allocation limits, physics, animation clocks, model types, or asset
loading. Generic distance-based fades are not treated as mesh LOD. No separate
stadium multi-mesh LOD selector has been proven by this audit, so no stadium
selector is claimed or guessed. Original texture filtering/mipmap state is
also unchanged; geometric LOD is a different mechanism.

## Integration

Root owns CMake and native dispatch. Generate into a private build directory:

```sh
python3 -m tools.prepare_pal_max_detail \
  --rom .local/inputs/pal-en-de/rom.z64 \
  --models-source .local/pal-map-bound-01/functions/func_800300D0_resident.c \
  --shadows-source .local/pal-map-bound-01/functions/func_80037498_resident.c \
  --output .local/pal-max-detail-01/generated
```

Compile both generated `.cpp` files against the same pinned runtime lookup
`recomp.h` used by the original CPU translation. Declare both entries with the
usual `extern "C" void(uint8_t*, recomp_context*)` ABI. PAL native lookup routes
`800300D0` and `80037498` to the respective derivative; leave original registry
entries available for reference. Re-run the generator as a build verification
step, including reused outputs. Include this generator in the private Windows
source transfer; the private PAL ROM is already a required build input for the
sky generator. Neither ROM nor generated original/derived CPU source belongs
in a portable/public distribution.

## Verification and acceptance limits

`python3 -m unittest tests.test_pal_max_detail -v` passes three focused tests.
The main regression was first run on unchanged, renamed original functions:
it failed because the original selector cached a lower level. After the
bounded changes, tests compile original PAL selectors and original geometry
assignment, run only synthetic RAM fixtures, and verify all seven model types
across depths 0/100/200/400/600/9998 and floors 0/1/2. They compare every chosen
limb pointer with an independent call to original `8002EB64(...,0)`, prove
no repeated rebuild on the next update, and preserve the original visibility
skip. Shadow tests cover both material modes, all three floor settings,
near/far depths, hidden-shadow suppression, and byte-identical special-mode
behavior. Additional tests reject wrong ROM/source identities and changed
existing outputs.

This investigation did not launch or control the game. Visible near/far and
replay acceptance and performance measurement remain with the root integration
run. In particular, original per-frame display-list/matrix capacities remain
bounded; increased rendering work must be observed in an actual full-team
match before claiming release acceptance.
