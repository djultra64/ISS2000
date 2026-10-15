# PAL original CPU and load map

Original project work: djultra64. Static checkpoint: 2026-10-15.

The European English/German revision has a separately recovered private load
inventory and generated original CPU source. No PAL game, emulator or Windows
binary was executed. CPU translation and metadata preparation succeeded; this
is not a verified PAL boot or Career progression result.

## Identity and resident boundaries

All PAL inputs are gated by revision `iss2000-pal-en-de-rev0`, canonical SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`,
16 MiB, cartridge NISX, revision 0. The US `.local/rom.z64`, generated sources,
saves and prior evidence remain preserved.

The original entry at ROM `0x1000` sets the BSS clear start to `0x800ADD20`
and length to `0x0011F7D0`, establishing BSS `[0x800ADD20,0x801CD4F0)`.
The initialized resident limit inferred from that BSS start is ROM `0xAE920`
(VRAM `0x800ADD20`); it is distinct from a DMA-proven overlay load extent.
Resident CPU text is classified as ROM `[0x1000,0x6A600)`, guest
`[0x80000400,0x80069A00)`: the final CPU return at ROM `0x6A5F4`, its delay
slot and padding precede original RSP boot code at ROM `0x6A600`.

PAL helper identities were recovered from original instructions and reviewed
body equivalence, then used as parameters to the existing conservative local
constant analysis. No US ROM/VRAM offset translation was used:

| Original PAL routine | Guest address | Evidence |
| --- | --- | --- |
| Bounded raw ROM DMA helper | `0x80003E24` | Both original chunk-copy calls target it |
| Chunked DMA helper | `0x80055E8C` | Original body advances ROM/RAM together, with exact remaining final copy |
| Memory clear | `0x8005CD50` | Original instruction-identical body and following-load clear calls |
| Decoder candidates | `0x800082A8`, `0x80053950` | Original bodies identified; decoder-derived executable loads remain unproven |

Explicit original thread entries are `0x80000898`, `0x8000092C`,
`0x8001D72C`, `0x8004B998`, `0x80058A80` and `0x8005ECC0`.
US seed `0x80000500` was deliberately excluded after PAL instructions showed
it lies inside the original PAL `0x800004A4` function.

## Inventory and translation

Private `.local/pal-load-map-01/translation-sections-final.json` contains 78
resident/load identities; 67 have classified candidate CPU text and 11 have
unknown text. Every recovered overlay ROM/VRAM/count comes from locally proven
original PAL DMA constants. Reused guest addresses retain distinct section
names. Final-return text endpoints remain provisional, and this method can
miss computed/indirect/decompressed loads. Inventory size is not a completeness
or runtime ordering proof. For comparison only, the preserved US map has 82
load identities and 66 CPU sections; 66 is not its total load count.

The final private sources are `.local/pal-map-bound-01/functions`, generated
from 12,235 analyzed functions with 53 reviewed PAL service bindings. The union
of 20 privileged and 53 bound entries excludes 65 unique original bodies from
ordinary generation. There are 12,170 original CPU `.c` bodies plus two generated
header/include files. The retained original PAL SDK body at `0x80060DD0` is
separately preserved under a unique symbol by metadata generation.

The unmodified pinned N64Recomp attempt is recorded under
`.local/pal-map-bound-strict-01`. It still rejects the original direct call at
`0x80003670` (inside function `0x80003668`) to unresolved target `0x801ED920`.
The separately receipted diagnostic compiler changes only all-call lookup
policy and generates the full candidate source with return code zero. Runtime
lookup must still reject unknown/inactive targets; no entry or success stub was
invented. This unresolved original call remains a limitation.

Metadata under `.local/pal-native-metadata-01` registers 67 CPU sections,
53 PAL service bindings and one retained original service. The receipt pins
ROM, section analysis, binding manifest, generated metadata and retained-source
hashes. See [PAL SDK and timing research](pal-runtime.md) when available.

## Original nine-entry mode selection

The PAL menu selection routine `0x803C2CEC` (ROM `0x341AEC`) reads cursor
`0x803F7428` and checks `cursor < 9` at `0x803C2D04`. Its nine-pointer table
is guest `0x803F28A8`, ROM `0x3716A8`; cases write original mode byte
`0x8012DE74`:

| Cursor | Case guest address | Original mode byte |
| --- | --- | --- |
| 0 | `0x803C2D28` | 0 |
| 1 | `0x803C2D38` | 5 |
| 2 | `0x803C2D4C` | 6 |
| 3 | `0x803C2D60` | 7 |
| 4 | `0x803C2D74` | 13 |
| 5 | `0x803C2D88` | 2 |
| 6 | `0x803C2D9C` | 3 |
| 7 | `0x803C2DB0` | 4 |
| 8 | `0x803C2DC4` | 1 |

This is original nine-case instruction evidence, including the additional
mode-5 route. Identifying that row as Career is an inference from regional
context until the actual PAL English menu and progression are visibly tested.
Original resident loaders also establish these distinct candidate CPU banks:

| ROM start | Guest start | Initialized bytes | Candidate CPU bytes | Original DMA callsite |
| --- | --- | --- | --- | --- |
| `0x516CE0` | `0x801EF060` | `0xC440` | `0xAD50` | `0x80058058` |
| `0x523120` | `0x80212700` | `0x414C0` | `0xB800` | `0x80058148` |
| `0x564670` | `0x80257310` | `0xE840` | `0x4A60` | `0x800580D0` |
| `0x572EB0` | `0x803C4F80` | `0xC9C0` | `0xA380` | `0x8005820C` |
| `0x57F870` | `0x803D1A30` | `0x2560` | `0x1A10` | `0x80058274` |

These loads and text presence do not establish successful Career execution.

## Original switch extents and validation

A compiler success initially concealed three truncated switches, so the final
map includes four independently reviewed original function extents:

| Function start | Size | Original table | Guarded entries |
| --- | --- | --- | --- |
| `0x8021347C` | `0x54` | `0x80250398` | 11 |
| `0x801F8978` | `0x50` | `0x801FB200` | 6 |
| `0x802A37EC` | `0x134` | `0x802AC398` | 12 |
| `0x802A7508` | `0xC8` | `0x802B0798` | 12 |

Each merges complete contiguous analyzed extents only after inspecting original
unsigned guards, all table pointers, terminal return/delay and next function.
No aligned direct JAL to merged case entries exists in the complete input.
Original instructions were not modified. The final generated-source audit
scanned 335 switches, proved 332 simple same-register bounds and found zero
concrete truncations or unresolved tables. Three guards remain outside that
simple audit: `0x8001D72C`, `0x802A3100` and `0x802CA8E4`. This is not an
exhaustive control-flow proof.

Private reproducibility scripts and original evidence are under
`.local/pal-load-map-01/`: `recover_pal.py`, `translate_bound_pal.py`,
`generate_lookup_pal.py`, `audit_switches_pal.py`, `assert_pal_evidence.py`,
`grounded-evidence.json` and the before/after switch reports. Generation scripts
require fresh output directories and explicit pinned tools. Original generated
code and ROM-derived evidence remain ignored and must not be published.

## PAL culling layout integration

`WidescreenGuestLayout` now carries original guest addresses explicitly.
Runtime PAL callers select `verified_pal_widescreen_layout()`; the US default
supports preserved US diagnostics/tests. The PAL profile is backed by unique
normalized full-body matches of the original routines recorded by the SDK
research, including the field consumer `0x80022D90` (US `0x80022760`), angular
builder `0x80023488` (US `0x80022E58`) and rotated-corner builder `0x80024A10`
(US `0x800243E0`). Body matching preserves register/control-flow/float semantics
while independently recovering referenced globals; it does not translate a
regional address delta.

| Camera field | PAL original guest address |
| --- | --- |
| Original aspect | `0x8009DF00` |
| Horizontal / vertical angular bounds | `0x8009E09C` / `0x8009DFE8` |
| Horizontal / vertical far extents | `0x800A7824` / `0x800A7828` |
| Four corner X/Y/Z arrays | `0x800C345C` / `0x801755F0` / `0x801A0760` |

All four culling helpers validate every scalar and complete corner-array range,
4-byte alignment and mutual non-overlap before any guest memory access. Invalid
layouts cannot partially write. Existing original-pair and corner geometry
checks remain intact. A native synthetic-RAM test selects the PAL layout,
checks horizontal widening and preserved vertical/forward geometry, and leaves
all original US camera locations as untouched sentinels. Original mode remains
a byte-exact no-op. These checks do not establish visually correct PAL 16:9;
visible projection and gameplay acceptance remain deferred.
