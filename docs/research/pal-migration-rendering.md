# PAL rendering migration inventory

Original project work: djultra64. This is a read-only migration assessment,
not PAL support or a migration implementation. Rendering implementation and
actual execution are paused at the user's request. The active USA input,
section map, generated code and runtime integrations remain unchanged.

## Candidate identity and current compatibility barrier

The private candidate `.local/inputs/pal-en-de/rom.z64` is the 16 MiB Europe
English/German revision-0 image, cartridge `NISX`, canonical SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
Its size, canonical digest and cartridge ID were checked against the preserved
`identity.json`; no PAL code mapping, compilation or execution was performed.
The input's Career/RPG content is outside this rendering inventory and is not
established by its language/region label alone.

`src/runtime/rom_image.cpp` currently requires USA rev0 SHA-256
`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850` and
16 MiB. It correctly rejects the PAL candidate. Merely allowing another digest
would be unsafe: current generated functions, section ROM/VRAM ranges, reviewed
SDK services and hooks are USA-specific. Keep exact per-revision validation;
do not replace it with size/title checks or accept PAL into the USA profile.

## USA-specific rendering evidence that must be recovered again

All addresses below are USA guest virtual addresses unless marked physical.
They are an inventory of existing assumptions, not proposed PAL addresses.

| Component | Current USA assumptions | Required PAL evidence |
| --- | --- | --- |
| Projection landmarks | Fixed perspective builder `8005B7E0`, float builder `8005B630`; callers `80024C3C`/`80024CD4`; aspect `800A07E8`, FOV `800A07D4`; setters `80024D48`/`80024D38`; initialization `8002A90C` | Identify corresponding builders, globals and call sites; retain one owner for projection correction |
| Visibility hooks | Retained original builders `80022E58`, `800243E0`; original point test `80022760`; alternate far writer `800228D0` | Recover actual consumers and invocation order before enabling the hooks |
| Visibility RAM | Aspect `800A07E8`; angular H/V `800A0984`/`800A08D0`; far H/V `800AA104`/`800AA108`; ray-axis arrays `800C5D3C`, `80177ED0`, `801A2FF0` | Verify layout, horizontal/vertical semantics, corner order and refresh lifecycle; current numeric guards do not identify a ROM revision |
| Camera transform bridge | Physical projection loads `C43A0`/`C43E0`; camera view multiplies `CEC68`/`CECA8` (slot0), `CECE8`/`CED28` (slot1) | Re-establish matrix double buffers and camera-slot relationship; matching addresses alone are insufficient |
| Scene gate | Field phase `(scene_token & FFFF)==0604`; token bytes at `8013DF26`/`8013DF2C` | Identify PAL scene/substate semantics, including Career transitions, and invalidate identity across scene changes |
| Object tracking | Root pool `80148104`,285 records of `98` bytes; child pool `80152A3C`,900 records of `60` bytes; record matrix fields `+18/+1C`,flags `+28` | Recover record sizes, allocator/free lifecycle, flags and matrix ownership; preserve recursion/child behavior |
| Tracking hooks | Original `800252B0` frame setup, `800252F8` root matrix, `80025710` child matrix, `8002A5A8` root allocation, `8002A820` child allocation, `8002A6C8` release | Bind only verified PAL equivalents and their original ABI |
| Matrix arenas | Physical bank0 `[AA128,AF228)`,bank1 `[AF228,B4328)`; bank selector `800A07B8`; cursor/end globals `800B4328`/`800B432C` | Verify allocation boundaries and bank swaps; current exact-bound tests must use the new revision profile |
| Microcode admission | Task text/data `80069250`/`8009C8E0` and `8006A5E0`/`8009CD00`; exact hashes documented in rendering.md; both currently recognized as F3DEX2 | Hash PAL text/data independently against pinned RT64; do not infer identical microcode or task addresses from the game title |
| Prompt interception | Sprite draw `800414C0`,bank21 pointer `80079650`,12-byte descriptors,slots5/6 16x16 CI4 and32-byte relevant palettes with exact USA hashes | Recover PAL banks/descriptors/consumers and validate actual pixels/palettes; procedural host glyphs can be reused |
| Title prompt | Register hook `800039F4`,text source `8009D490`,slot1 and USA glyph-table behavior | Verify PAL string source, language handling, glyph ABI and buffer capacity |

The bridge's F3DEX2 command decoding (`DA` matrix,`D8` pop), original-callback
preservation, metadata stack parity and no-RDRAM-write design are tied to the
pinned RT64 interface, not the USA game. Its concrete address and phase policy
is USA-specific. The current bridge is a source/unit-checked checkpoint, not
proof of interpolated gameplay. Generated CPU bodies and their exported USA
symbol names cannot be reused as PAL implementations by changing lookup keys.

## Host work that remains reusable

- Graphics JSON parsing/atomic persistence and the Original/720/900/1080/1440/
  1800/2160 height profiles, aspect-specific labels and compact settings pages.
  Actual VI height drives scaling, avoiding a hardcoded 240-line assumption.
  PAL VI height and interlace must still be checked through RT64's derived
  `VI::fbSize()`; profile names do not establish the actual framebuffer size.
- Generic RT64 Application/Vulkan integration, window presentation and Manual
  aspect/resolution controls. Recheck the pinned microcode registry and actual
  PAL rendering rather than adding game-specific shader changes by assumption.
- Immutable task snapshots, FIFO/fingerprint submission synchronization,
  monotonically generated transform IDs, scope cleanup and ownership tests.
  Pool/arena/function bindings must become revision-specific evidence.
- Logical input actions, active Xbox/PlayStation/Switch family detection,
  keyboard labels, remapping/persistence, rumble routing and native controls
  footer. Their guest button ABI and original on-screen prompt coverage still
  need verification in the new game's modes; the footer alone does not replace
  baked or sprite prompts.
- Portable data paths, ROM picker, packaging framework, safety checks and
  dependency/license notices. Preserve separate USA saves and PAL saves until
  save format, note identity and region compatibility are demonstrated.

## Concrete cost and safe order after a base decision

This would preserve the host framework while replacing the game's revision
profile and re-verifying guest integration. It is not a clean restart, and it
is not a ROM swap. Existing USA CPU mapping, SDK matching and renderer evidence
provide tooling and methodology, not authoritative PAL addresses or boundaries.

First retain the USA checkpoint and private evidence. Then establish a separate
exact-digest PAL profile and recover resident/overlay executable boundaries,
thread entries and verified SDK ABIs before enabling PAL execution. Establish
unmodified PAL baseline behavior and the required Career path before reapplying
16:9 visibility, resolution and interpolation work. Recover the addresses above
from original PAL instructions and approved visible snapshots. Revalidate PAL
VI timing and original simulation cadence separately from target presentation
rate: a manual60/120Hz target is not evidence that a PAL simulation should run
at60Hz. No credible duration estimate follows from this bounded inventory.
