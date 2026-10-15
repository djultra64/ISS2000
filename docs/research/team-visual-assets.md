# Team visual asset research

Original project work: djultra64. Date: 2026-10-15.

This research prepares a future selectable team/roster/flag/kit package feature.
It does not implement a package loader, add teams, change the ROM, or establish
that a match or an asset replacement works. Baseline 1.0 remains the priority.
Only the supported ISS2000 ROM, existing private captures/dumps, original
instructions, and local generic analysis tools were inspected. No other game's
binary was read and no game execution was performed for this research.

## Input and evidence limits

The canonical ROM SHA-256 is
`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`.
The fixed inputs are `.local/prompt-research-01/player-number.rdram` and
`.local/switch-research-01/team-select.rdram`. Each is an 8 MiB native RDRAM
snapshot with bytes reversed inside each 32-bit word. Convert a guest byte
address to native storage with `(address & 0x1FFFFFFF) ^ 3` after validating the
address. Interpreting these files as canonical big-endian memory gives incorrect
pointers, palette colors and texture nibbles.

A later parent-produced settled snapshot is
`.local/team-visual-assets-01/settled-team-selection.rdram`, paired with actual
capture `.local/captures/44-boot12-teams.png`. It visibly shows USA on the left,
Canada on the right, waving flags and two miniature 3D players. The settled
findings below supersede the earlier inability to classify actual flag pixels;
they do not retroactively identify the unrelated bank 145 contact sheet.

The initial team-selection snapshot contains initialization/transitional UI state. It
is not a final frame demonstrating every team flag or a 3D uniform. Texture
workspaces already hold or formerly held other menus' data; a descriptor with
a plausible size does not prove its currently referenced bytes are its intended
asset. The filenames of screenshots are also insufficient: capture24 still shows
Player Number, and capture25 shows partially initialized team panels.

## Verified asset and renderer conventions

| Item | Original evidence | Established meaning |
| --- | --- | --- |
| Sprite pool | `0x8013EF5C`, stride `0x3C` | Sprite visibility/type at `+4`; texture descriptor at `+0x14`; draw script at `+0x30`; palette pointer at `+0x34` |
| Texture bank table | `0x800795FC + bank*4` | Bank pointer; do not assume the table has only 128 banks: the verified team-art consumer uses bank 145 |
| Descriptor setter | `0x8000A4F4(sprite, bank, index)` | Assigns `bank_base + index*12` to sprite `+0x14` |
| Descriptor | Width/height at `+0/+2`, format/attributes at `+4`, texture pointer at `+8` | A 12-byte descriptor; format 1 is observed as CI4 in the verified A/B icon path |
| Original sprite dispatch | `0x800413B4`, call `0x8004143C` | Type 1 sprites are passed to original renderer `0x800414C0` |
| Original renderer | `0x800414C0..0x80041D6C` | Reads descriptor and draw script and produces original RDP rectangles; it is not a team database accessor |
| Palette selection | `0x80043548`, especially `0x800435A8..0x800435D4` | Palette class and encoded selector are independent of the texture index |

For ordinary encoded palette selectors, the high nibble chooses a pointer in
`palette_class_table[selector >> 4]`; the low nibble chooses a 32-byte palette
within that block. The palette-class pointer table starts at `0x80079368`.
Class 1 points to `0x80079328` in the captured state. For example encoded
selector `0xD3` resolves to palette `0x8006EB50`; `0xE3` resolves to
`0x8006ED50`. The special `0xFE`/`0xFF` paths in `0x80043548` are not ordinary
palette selections and must remain distinct.

A directly validated small example is the native A/B prompt integration:
bank 21 descriptors5/6 point to 16x16 CI4 textures `0x80237600/0x80237680`,
each 128 bytes, with separate 16-color, 32-byte RGBA5551 palettes. Their palette
bytes match original ROM `0x35EE40/0x35EE60`. They are controller prompts,
not team flags. Never apply their dimension or palette assumptions to every
team visual. Existing procedural prompt overrides must retain precedence over
an unrelated pack replacing common UI art.

## Proven team-ID-to-visual lookup

The following bridge is established by original instructions, without assigning
unverified country names or calling the resulting art a flag or jersey.

| Code/table | ROM offset | Evidence |
| --- | --- | --- |
| `0x801C2114` | `0x2F2DF4` | Intermediate team-ID mapping in the core raw load |
| `0x803D014C` | `0x3531DC` | Accepts sprite and team ID; factory branch checks ID `<0x67` |
| `0x803D00BC` / table `0x803EE976` | Table `0x371A06` | Reads intermediate mapping, then selects primary art descriptor index |
| `0x803D0104` / table `0x803EEA4A` | Table `0x371ADA` | Reads the corresponding independent encoded palette selector |
| `0x803D0210` | `0x3532A0` | Alternate team visual assignment with the same overall structure |
| `0x803D00E0` / table `0x803EE90C` | Table `0x37199C` | Alternate descriptor-index mapping |
| `0x803D0128` / table `0x803EE9E0` | Table `0x371A70` | Alternate palette mapping |
| Bank145 base `0x803D97F8` | `0x35C888` | Descriptor array selected by the factory paths |

For the primary factory branch the effective operations are:

```text
mapped = byte[0x801C2114 + team_id]
index = byte[0x803EE976 + mapped]
palette = byte[0x803EEA4A + mapped]
set_descriptor(sprite, bank=145, index=index)
set_palette(sprite, class=1, encoded_selector=palette)
```

The alternate branch substitutes `0x803EE90C` and `0x803EE9E0`.
Examples from the original tables, preserving numerical IDs:

| Team ID | Intermediate ID | Primary descriptor | Primary palette | Alternate descriptor | Alternate palette |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 43 | `0xD3` | 109 | `0xE3` |
| 1 | 1 | 40 | `0xD0` | 106 | `0xE0` |
| 2 | 2 | 41 | `0x00` | 54 | `0x20` |

Bank145 starts with exactly 77 consecutive 48x32 format 1 descriptors. Their
texture pointers are `0x8023DC00 + index*0x300`. The next descriptor at
`0x803D9B94` (ROM `0x35CC24`) starts a 64x32 format 1 run with pointers
`0x8024C300 + index*0x400` and varying palette indices. This is an array of
**different layouts**, not a license to overwrite every entry with 48x32 data.
Its visual meaning remains unconfirmed. Candidate extractions from unrelated
assets produced uninterpretable images and are explicitly not flag or kit proof.

### Contact sheet from actual saved memory

The follow-up extraction reads the **actual** team-selection RDRAM, not a guessed
decoded file substituted into the texture address. Private script
`.local/team-visual-assets-01/render_memory_bank145.py` resolves both visual
mapping paths for the intersection of their proven factory domain, IDs
`0x00..0x66`. For each entry it uses the descriptor's actual dimensions, its
actual texture pointer, and the encoded class 1 palette selected for that team.
CI4 nibbles are decoded with that palette's RGBA5551 colors. Each image is labeled
with numerical team ID, primary/alternate path, descriptor index and encoded
palette selector; no country name is guessed.

The result is `.local/team-visual-assets-01/actual-bank145-team-art.png`.
Its companion JSON records all 206 entries, actual texture/palette pointers,
dimensions, SHA-256 values and nonzero-byte counts. All 206 descriptors and
palettes resolved within RDRAM. Four payloads were entirely zero and 202 contained
nonzero bytes. **Visual inspection did not identify recognizable flags or jersey
icons**: the sheet shows fragmented patterns and menu-like pieces. Correct pointer
resolution by itself does not establish that this snapshot has the intended bank
payload loaded, or that direct descriptor interpretation captures additional
context performed by the original renderer.

A separate private `match_workspace.py` compared supported mode0 asset decodes
against the entire corresponding snapshot workspace beginning at `0x8023DC00`.
No complete asset matched there. This does not exclude partial loads, aliases,
other stream modes or renderer-dependent interpretation; it provides no basis
for choosing a guessed replacement source. The positive complete asset 0x15
match documented below remains intact and independently validates the decoder
for that asset.

For this particular bank 145 array, the remaining blocker is **its actual load
identity and draw context**, even when the separate flag display has settled. A useful next capture needs an actual call to
`0x803D014C`/`0x803D0210`, its numerical team ID and sprite, the resulting
`0x800414C0` draw, the emitted texture/palette commands and the immediately
preceding asset load(s) covering that texture. No new game run was started by this agent for
this contact-sheet investigation. The semantic class of bank 145 art and 3D
uniform materials remains unconfirmed; the separate flag path is proven below.

A second independent consumer in raw overlay ROM `0x472920`, at
`0x802A9310..0x802A9358`, reads the active side's team ID, checks `<0x6A`, uses
the same primary tables, and calls bank 145 assignment at `0x802A9344`.
This connects the lookup to active team state, rather than merely an unused table.

The nonfactory branch of `0x803D014C` uses saved/custom record bytes at
`0x80130D68/69 + (team_id - 0x6A)*26` to choose art and palette separately.
Do not extrapolate the factory branch's `<0x67` condition to the database's
`<0x6A` bound, or treat IDs `0x67..0x69` as explained. Their special handling
and caller constraints still need proof.

## Settled flags: confirmed IDs, pixels, palettes and source packs

The settled screenshot and active side headers establish two specific numerical
country associations: side 0 is team `0x3D` (decimal 61), displayed **U.S.A.** on the
left; side 1 is `0x45` (decimal 69), displayed **Canada** on the right. These labels
are verified for this snapshot, not extrapolated to other IDs.

Re-extracting bank 145 from the settled snapshot still produces fragmented
patterns. The active original display list instead references separate
`0x8037xxxx` material buffers for the actual flags. Following saved display-list
calls and segment-register commands identifies the following exact assets:

| Visible country | Current team ID | Actual CI4 pixels | Relevant 16-color RGBA5551 palette | Exact decoded original source |
| --- | --- | --- | --- | --- |
| USA, left | `0x3D` /61 | `0x803738A8`, 768 bytes | `0x803736E8`, 32 bytes | Asset `0x2A3`, offset `0x2400`; palette asset `0x2A1`, offset `0x1B40` |
| Canada, right | `0x45` /69 | `0x803733A8`, 768 bytes | `0x80373708`, 32 bytes | Asset `0x2A3`, offset `0x2700`; palette asset `0x2A1`, offset `0x1B60` |

The private extraction `settled-actual-flags.png` was opened and inspected. Its
rasters unmistakably show the US stars/stripes and Canadian maple leaf. The
associated JSON contains independent pixel and palette hashes. The original
stored US raster has its canton at the bottom in a direct row-major decode,
whereas the screenshot shows the rendered orientation; preserve the original
geometry/UV convention rather than silently normalizing imported pixels. This
observation does not recover jersey UVs.

The shared original flag display-list template is `0x80086F28`. Its command
`0x80086F48` loads the palette, and `0x80086FA0` loads CI4 texels. The tile-size
word `0x000BC07C` establishes a 48x32 texture. In the captured task, a display-list
call at `0x80357948` enters that template twice with different segment/material
state. These are **graphics command addresses, not MIPS function addresses**.
Canada is encountered first during this traversal and USA second; traversal
order must not be mistaken for left/right team order.

The palette-load command is `F0000000 / 073FC000`, which requests a larger TLUT
load than the 16 colors actually indexed by these CI4 flags. The 32-byte palette
matches in the table are the relevant first 16 entries. Do not overwrite the
entire nominal TLUT span as a texture replacement: adjacent memory contains
other palettes and material pixel buffers. The two relevant palettes are only
32 bytes apart, and the subsequent texture buffer is within the larger nominal
load range.

| Pack | Compressed original ROM range | Decoded size | Decoded SHA-256 |
| --- | --- | --- | --- |
| `0x2A1` | `0xF6E2F6..0xF6FDFC` | `0x3100` /12544 bytes | `0e20fe777954cb3ed392c84a247abccf223a5ce4d6e52aba917ffc2aff319bed` |
| `0x2A3` | `0xF7054C..0xF70E8E` | `0x3300` /13056 bytes | `5d6e786abbf99afd8d35b3c809c90be47722d65d226b6d24a5c7f635ef25cdd7` |

Both use the already verified mode0 decoder path. Every byte of both 768-byte
flag rasters and both 32-byte relevant palettes matches the listed decoded pack
offsets. Asset 0x2A3 has exactly 17 times 768 bytes; the two proven flags occupy
slots 12 and 13. This does not assign names or team IDs to the other 15 slots.
The US palette additionally matches raw resident ROM `0x6EB30`, so the compressed
palette pack is an exact match rather than a claim of unique ownership.

Reproducible private scripts are `render_settled_bank145.py`,
`trace_settled_dl.py`, `render_settled_flags.py`,
`find_settled_flag_sources.py` and `extract_settled_flag_packs.py`, all under
`.local/team-visual-assets-01/`. The task's root list is `0x800D2C08`, size
`0x8EF8`; the other queued task lists `0x800E2C68` with the same size. Saved
command traversal is bounded and does not execute a CPU, RSP or renderer.

The remaining flag-specific implementation research is the original CPU
allocation/copy path that supplies these material buffers and its full
team-ID-to-pack-slot mapping. The current proof supports these two countries
and a concrete source format, but not a pack hook for all teams. No claim is
made that bank 145 represents these flags, that the miniature players use the
same texture resources, or that a 3D jersey replacement has been solved.

## Uniform/material and model leads

Independent roster research identified, and this investigation inspected, the
original accessor `0x8002D9DC(side)`. Active side headers are at
`0x801A80CC + side*0x11E8`; their byte0 is a team ID. The accessor uses bit9
of the side word at `0x801A8F74 + side*0x11E8` and returns:

```text
byte[0x8007DA9C + team_id*2 + ((side_flags >> 9) & 1)]
```

This paired table is ROM `0x7E69C`. It is consumed by `0x8002DAE0`, which
combines both sides' masks and tests several individual bits, and by player
attribute routines `0x8001CA60/0x8001CBEC`. Those routines also use a packed
nibble table at `0x8007A0E0`, with an alternate-side offset of 106 before dividing
by two; nonfactory branches inspect mask `0x30` and return different categories.

These are concrete leads for alternate appearance categories and conflict
selection. They do **not** yet establish which bits mean shirt color, shirt
pattern, shorts, socks, goalkeeper kit, body shape or another property. Do not
replace this mask with a single texture number.

No authoritative player mesh, skeleton, animation, jersey UV island, material
record width, home/away/goalkeeper texture set or per-part geometry layout was
recovered here. In particular, the UI descriptor bridge does not prove a way to
replace a 3D jersey or model. A roster-only pack and a 3D visual pack must not
be presented as equivalent achievements.

## Bounded paused-match material findings

A subsequent parent-produced `.local/team-visual-assets-01/paused-match.rdram`
contains a real paused match, paired with captures55/56. This agent only decoded
that existing memory and graphics-command data; it did not launch, resume or
capture the application. Further gameplay verification was then explicitly
postponed while 16:9, resolution and interpolation work takes priority.

Private `render_paused_load_atlases.py` reconstructs saved segment/TLUT state and
renders 74 distinct observed CI4/CI8 load-atlas/palette combinations to
`paused-load-atlases.png`. The inspected sheet includes stadium sky/advertising,
faces, uniform-like patterned panels, number glyphs, sock/leg-shaped artwork and
HUD graphics. It is a classified research contact sheet, not a screenshot or an
asset-replacement test.

A significant format distinction is proven by saved commands at
`0x80360FF0` and `0x80361B18`: a complete 64x64 CI4 atlas is loaded first, then
later tile commands select 40x12 or 40x24 regions with different TMEM offsets/line
strides. A tile's final 40-pixel width is not the row stride or byte count of its
source atlas. The earlier exploratory `paused-actual-materials.png` used final
tile extents and is superseded for load/source interpretation by
`paused-load-atlases.png`. Never use those cropped interpretations as import
layouts or source-identification evidence.

| Actual saved resource | Established observation | Exact original payload source |
| --- | --- | --- |
| `0x803BECA8`, 64x64 CI4 | Visually identifiable face-view atlas; observed with different palettes | Asset `0x2A8`, ROM `0xF74FFC..0xF77798`, decoded offset `0x1800`, 2048 bytes |
| `0x803BD498`, 64x64 CI4 | Another face-view atlas | Same asset, decoded offset `0x1000`, 2048 bytes |
| `0x803BEAA8`, 32x32 CI4 | Visually identifiable number 3 glyph | No complete pixel-source match established |
| `0x803BD298`, 32x32 CI4 | Visually identifiable number 13 glyph | No complete pixel-source match established |
| `0x803CDC58` / `0x803BC898` | Red/light patterned 64x64 source-atlas candidates used by loaded player-material commands | Exact source pixels and generation/copy path unresolved |
| `0x803CD458` / `0x803BC098` | Red/light source-atlas candidates, later cropped into strips by tile commands | Exact source pixels and anatomical/UV assignment unresolved |
| `0x803D5DA8`, 32x32 CI4 | Visually identifiable white leg/sock-shaped artwork | Pixel source and anatomical assignment unresolved |

Material palettes can be matched independently. For example the current red
panel palette at `0x803CE458` matches decoded asset `0x27B` offset `0`, the red
strip palette at `0x803CE4D8` matches offset `0x80`, and the white leg-shaped
resource's palette at `0x803CE518` matches offset `0xC0`. Light panel/strip and
number palettes match offsets `0xE00/0xE80/0xEC0` in that same decoded asset.
Some of these 32-byte palettes also occur in other original packs, so these are
exact matches, not unique ownership claims. Do not infer that a palette match
identifies the complete shirt texture, its factory team ID or its UV layout.

The raw active-side header bytes in this paused snapshot are 61/62, whereas the
settled selector snapshot read 61/69 for the visibly named USA/Canada sides.
This stage-dependent discrepancy was communicated to roster research. It
prevents treating these header bytes as a universally stable pack namespace
without tracing the transition. The report's USA61/Canada69 identification
remains scoped to the earlier settled selector evidence.

Private source evidence is `paused-load-atlases.json`,
`paused-load-atlas-source-matches.json`, `trace_paused_dl.py` and
`find_paused_load_atlas_sources.py`. These findings identify concrete material
resources to probe later. A complete jersey/shorts/socks assignment, model-part
consumer, generated-number writer, player-to-material instance map, skeleton,
and UV specification remain open. No jersey replacement or model import was
implemented or tested.

## Compression and reusable asset identity

`0x80053150(asset_id, destination)` reads the asset directory at guest
`0x80099104`, ROM `0x99D04`, with entry `(asset_id-1)*8`. A negative start word
selects original decoding at `0x80007DE8`; its high bit is a flag and not part
of the ROM address. There are alias/empty-entry paths, so not every entry can
be decoded independently by subtracting its endpoints.

The original decoder has multiple stream modes. The privately transcribed
mode0 path uses bounded literal runs, byte/zero repeats, and a 10-bit-distance
backreference. Other header modes and the alternate decoder at `0x80281D40`
remain outside this transcription. Block padding is aligned to original ROM
addresses, not the host buffer origin. Unrecognized modes, invalid extents or
references before output are rejected; no generic compression-library name is
claimed.

A full positive cross-check is available: asset `0x15`, ROM
`0xC7073C..0xC863DA`, decodes to `0x26F40` bytes. Its decoded SHA-256 is
`2a00a6356e10fb53d1a6fa23c9061b3a3265edacb7aae393b47c60b1248f4c27`.
**Every byte** matches the fixed Player Number dump at
`0x80216CC0..0x8023DC00`, including the original prompt icon pixels. This is
a verified asset load/decode identity, not only a visually plausible extraction.

Core data ROM `0x2EF158`, guest `0x801BE478`, contains queued request
`0x4000000C -> 0x8023DC00`; other requests in that area reuse `0x8023DC00`
for assets `0x3E`, `0x3F`, `0x1A`, `0x1D` and `0x22`. Common data ROM
`0x3594C0`, guest `0x803D6430`, contains request `0x40000029 -> 0x8023DC00`.
These are contextual alternatives, not a single permanently resident texture.
The exact asset request supplying the bank 145 team-art path is unresolved.

Private reproducible evidence is under `.local/team-visual-assets-01/`:
`probe_assets.py`, `decoded-assets.json`, `decoder-output.json`,
`candidate_grid.py`, `candidate-assets.json`, decoded originals and diagnostic
candidate images. Only the scripts/data explicitly listed there were produced;
no generic installed asset extractor or external game dump was used. Re-run the
scripts from the canonical folder. The candidate images are research
visualizations, never screenshots or evidence that replacement artwork rendered
inside the game.

## Future package plan and acceptance probes

1. **Finish provenance first.** During a parent-owned visible team-selection run,
   record bank 145 draw calls, team ID, both mapping bytes, palette address,
   texture address and the last actual asset request affecting that workspace.
   Save one settled frame and RDRAM snapshot for several original teams and both
   appearance choices. Match the decoded asset payload exactly before naming a
   flag or uniform file.
2. **Resolve semantics independently.** Correlate one verified country label with
   its numerical ID, primary/alternate bitmap, palette and selected-side bit.
   Trace the paired appearance mask into its consumers; establish goalkeeper and
   clash-selection behavior separately. Never infer all 106 country labels from
   the 77-entry texture run.
3. **Probe real 3D materials.** At a visible match/replay safe point, capture the
   original graphics task, texture/palette addresses and model/material update
   callsites for both teams. Recover mesh vertices, UVs and animated-object
   identity before considering jersey/logo or model replacement. Menus alone
   cannot validate this.
4. **Define a versioned manifest.** A future pack should target the verified ROM
   digest and semantic team slots, with separate roster, localized name, flag,
   primary/alternate kit and goalkeeper resources. Record expected original
   descriptor/layout and decoded payload hashes; never make transient guest RAM
   addresses its public identity. Adding a team exceeds replacing an existing
   slot: database limits, menus and custom-save domains need separate design.
5. **Begin with bounded replacement.** Preserve dimensions, CI4 packing,
   RGBA5551 transparency and palette ownership for the first proven flag/UI
   resource. A 16x16 CI4 icon is 128 bytes plus a 32-byte palette; a 48x32 CI4 image
   is 768 bytes. A larger image or a shared-palette edit can corrupt adjacent
   resources or recolor other teams. Detect reloads/aliases, retain originals,
   reject unknown layouts, and select a pack only at a proven safe transition.
6. **Validate selection and persistence.** Future in-game selection must show the
   active pack, support original assets again, and keep the user's base ROM and
   existing saves intact. Test malformed packs, wrong revisions, duplicate slots,
   missing dependent palettes, home/away changes, edited teams, language changes,
   replays and save/reload. Bind pack metadata to compatible saves rather than
   silently interpreting a different roster under an old save.

No pack loader, replacement asset, menu selector, renderer import hook or new
team database change is implemented by this document.
