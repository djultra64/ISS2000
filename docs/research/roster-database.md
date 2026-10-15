# Roster and team database research

Original project work: djultra64. Research checkpoint: 2026-10-15.

This is future package planning, separate from the 1.0 acceptance work. No
package loader, selection menu, roster modification or game execution was added
by this research. Evidence comes directly from the supported ISS2000 ROM,
translated original functions, and the existing private team-selection RAM dump.
No other game's binary was used.

## Evidence and reproducibility

All offsets below use the canonical big-endian ROM with SHA-256
`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`.
Ranges have an exclusive end. Guest addresses are KSEG0 virtual addresses.
Private inputs and extracted information remain ignored under `.local/`:

```sh
python3 .local/roster-evidence/roster_evidence.py \
  --rom .local/rom.z64 \
  --rdram .local/switch-research-01/team-select.rdram \
  --output .local/roster-evidence/report-02.json
```

The saved checkpoint is `report-01.json`. The script requires the exact ROM
identity, converts the native dump's reversed four-byte words into guest order,
checks its resident identity, compares complete table ranges, and checks all 44
active records against their source records. It reports function body hashes,
field dispatch targets and saved-region CRCs without modifying either input.
Output creation is exclusive. Omitting `--rdram` gives ROM-only results. These
are static/data checks; they do not demonstrate an in-game save round-trip.

## Verified factory tables and load route

| Table | ROM start | Guest start | Size and interpretation |
| --- | --- | --- | --- |
| Player records | `0x2F2EE0` | `0x801C2200` | `0x1FE20`: 106 teams × 22 players × `0x38` bytes |
| Default player order | `0x7DC20` | `0x8007D020` | `0x91C`: 106 × 22 one-byte indices |
| Two-variant team lookup | `0x7E69C` | `0x8007DA9C` | `0xD4`: 106 × 2 bytes |
| Team metadata | `0x315BF0` | `0x801E4F10` | `0x27C`: 106 × 6 bytes |
| Team coordinate records | `0x313FD4` | `0x801E32F4` | `0x1B54`: 106 × 11 × 6 bytes |
| Team visual index | `0x2F2DF4` | `0x801C2114` | 106 bytes; identity mapping `0..105` in this ROM |

Every complete range in this table matches the existing RAM dump. The player
DB ends at ROM `0x312D00` / RAM `0x801E2020`; its SHA-256 is
`754ae20d77776cee4532f46e417dd82e8790c3e38982001c7221d6286a0f1d46`.
All 106 default order rows are permutations of `0..21`.

The player DB, metadata, coordinates and visual index are initialized raw data
inside the load `ROM 0x2E0D90..0x3166C0 -> RAM 0x801B00B0..0x801E59E0`.
Resident loader `0x800574EC` tests bit 1 of `0x8013DF1C`, sets that bit, and calls
DMA wrapper `0x80003964` at `0x8005753C` with this exact range. It subsequently
clears BSS `0x801E59E0..0x801EFCB0`. Re-entering through a different overlay load
can change this shared RAM area; a future package cannot assume a single
startup memory write persists for the whole application.
The default order and variant tables are resident initialized data
(`ROM = guest - 0x7FFFF400`).

Accessor `0x80013728(teamID, playerIndex)` masks both arguments to eight bits.
For team IDs below `0x6A`, its exact address calculation is
`0x801C2200 + (teamID * 22 + playerIndex) * 0x38`.
It does not check `playerIndex < 22`; a package validator must enforce that
bound rather than depend on the original accessor to reject bad references.
Function `0x800138F8` calls this source lookup at `0x8001390C`, then field
accessor `0x800110B4`.

## Team IDs, selection and active match records

Factory IDs are `0..105`; this does not establish 106 individually selectable
national teams. Country names, region classifications, competition eligibility
and the complete selection grid ordering have not been assigned to these IDs.
Those require original label/selection consumers and visible correlation.

| ID domain | Verified accessor behavior at `0x80013728` |
| --- | --- |
| `0x00..0x69` | Factory player table |
| `0x6A..0x6C` | Shared 56-byte template at `0x80079F30`; player index ignored |
| `0x6D..0x71` | Five editable team blocks, described below |
| `0x72` | Template at `0x80079F68` |
| Other values | Falls back to the first factory record |

Two active side blocks begin at `0x801A80CC`, stride `0x11E8`. Their verified
layout is:

| Offset in side block | Size | Meaning |
| --- | --- | --- |
| `+0x000` | 1 | Team ID |
| `+0x028` | 22 × `0x4C` | Active player records: factory 56 bytes plus 20 runtime bytes |
| `+0x6B0` | 22 × 2 | `{sourceTeamID, sourcePlayerIndex}` pairs |
| `+0x6DC` | 22 | Player ordering indices |
| `+0x7F4` | Multiple formation slots | Six-byte coordinate records; selected slot comes from `+1` |

Function `0x8002CCA0(outputPairs, teamID)` initializes 22 provenance pairs using
the default order table. Its output is the pair array, rather than a complete
side block. Function `0x8002CD60(sideBlock)` resolves each pair through
`0x80013728` and copies all `0x38` source bytes into active records with stride
`0x4C`. A null edited source uses the original template. The 20-byte runtime
extension must not be mistaken for package roster data.

Accessor `0x80010EE8(side, lineupSlot)` adds a second indirection through
`0x801308B7 + side * 22 + lineupSlot` before selecting the active record.
`0x80011068` addresses a physical active index directly; `0x80010F58` uses the
side's `+0x6DC` ordering. Function `0x8000A6AC` copies that saved ordering into
the `0x801308B7` table. Consequently a source player ID, active slot and current
lineup slot are distinct concepts.

In the existing snapshot, side IDs are decimal 61 and 69; all 22 provenance
pairs per side are `{sameTeamID, 0..21}`. All 44 complete 56-byte active records
match the corresponding factory records. Both order arrays are identity.
This proves the link from factory IDs into active match state in that capture,
without claiming that a playable match was verified by this research.

Selection preservation is visible in resident `0x8000E778`, which copies both
side team IDs to `0x80131007/0x80131008` in modes 0/2; `0x8000E840` restores them.
`0x8000E7F0` and `0x8000E818` normalize IDs `106..108` to side-specific template
IDs 106 and 107. A future package must preserve these reserved domains.

## Record fields: known layout, unassigned semantics

The player field getter `0x800110B4` checks selector `<39` and dispatches through
39 pointers at RAM `0x8009D698` / ROM `0x9E298`. The following mapping is exact;
labels such as speed, stamina and technique remain unverified.

| Field selector | Record read |
| --- | --- |
| `0..12` | Bytes `+0x20..+0x2C`, respectively |
| `14..18` | Bytes `+0x2D..+0x31`, respectively |
| `22`, `32`, `34`, `35`, `36` | Bytes `+0x32`, `+0x33`, `+0x34`, `+0x35`, `+0x14` |
| `13`, `23` | Low/high nibble of `+0x0E` |
| `20`, `21` | Low six/high two bits of `+0x0F` |
| `24` | Byte `+0x10` |
| `25`, `26` | Low/high nibble of `+0x11` |
| `27`, `28` | High five/low three bits of `+0x12` |
| `29`, `30` | High/low nibble of `+0x13` |
| `31` | Low six bits of `+0x0B` |
| `19`, `33`, `37`, `38` | Constant zero |

The first word is used as a bit set: getter `0x800112A0` returns it and
`0x80011234` counts bits 0..22, capped at six. Individual bit roles remain
unknown. Bytes `+0x36/+0x37` are zero in every factory record; their required
future meaning is not established.

The name is eight **encoded bytes** at `+0x18..+0x1F`. Name consumer
`0x8002C5BC` selects an active player and passes that field to `0x8002C654`,
which calls `0x80040BF8`. The scanner accounts for eight encoded bytes and uses
`0x800489CC/0x80048A64` for character classification/conversion, including
multi-byte paths. Eight bytes does not imply eight Unicode characters.
An initial Latin code hypothesis (`A..Z = 0x07..0x20`,
`a..z = 0x25..0x3E`) yields plausible names, but the complete alphabet,
padding, control codes, accents and encoder still need verification. A future
editor must retain the original bytes until it has a validated encoder.

Byte `+0x2D` ranges 58..99; getter branch `0x8001CB1C` adds 100. Height in
centimetres is a hypothesis consistent with 158..199, not a confirmed field
label. Attribute ranges and all dispatch addresses are in the private report.
Do not clamp every attribute to 99: byte `+0x2E`, for example, reaches 216.

## Team metadata and visual references

`0x8002C9D8(side)` reads the first five bytes of the six-byte metadata row,
resolves each source player index with `0x8002C990`, and stores the resulting
lineup indices at side offsets `+0xE43/+0xE44/+0xE45/+0xE46/+0xE48`.
All input values in these five columns are `0..10`. Captain and set-piece
assignments are plausible labels, pending the actual role consumers/UI.

`0x8002D138(side)` reads the sixth metadata byte into side `+1`, then copies
11 six-byte records from the team's coordinate row into the corresponding
formation slot at `+0x7F4`, negating the middle halfword. Formation positions are
a strong interpretation, but coordinate axes/units and all formation IDs are
not established. The sixth byte includes values up to 13; a package must not
assume a short contiguous set based on the most common value alone.

`0x8002D9DC(side)` selects one of the two resident lookup bytes per factory team
using bit 9 of the word at side `+0xEA8`. Kit/color selection is inferred;
the returned value's complete asset semantics still need tracing.

Independent asset research identified the following bridge in the common
raw load `ROM 0x32F090 -> RAM 0x803AC000`:
`0x803D014C` checks `teamID < 0x67`; helper `0x803D00BC` maps through
`0x801C2114[teamID]`, then `0x803EE976[mappedID]`, into a bank-145 descriptor via
`0x8000A4F4`. Helper `0x803D0104` similarly reads `0x803EEA4A` for the palette
setter `0x80043548`. Alternate helpers use `0x803EE90C/0x803EE9E0`.
The team-selection overlay `0x472920` caller `0x802A9310` consumes the active
side's team ID with factory bound `0x6A`. These different bounds must remain
explicit; one consumer's domain cannot be extrapolated to another.

Bank 145 begins at `0x803D97F8`; its first 77 descriptors are 48×32 CI4,
followed by a 64×32 CI4 run. Their classification as flags, kit previews or
another team graphic is not yet visually established: texture workspace
`0x8023DC00` in the existing snapshot has been reused. Do not persist absolute
workspace pointers or declare descriptor index equal to country ID. Asset
research continues separately.

## Editable teams, checksum and save compatibility

Later independent PAL registration research also matched original US writer
`0x8001B638`: the five `0x514` containers provide 5×22 = 110 registered-player
slots. The "editable team blocks" wording below describes their storage/source-ID
organization, not five additional selectable national teams. See
[the PAL registration and regional save comparison](pal-roster-database.md).

For IDs `109..113`, `0x80013728` selects one of five blocks with stride `0x514`.
Global selector `0x8013100D` values 0/2 choose base `0x8016A0AC`; value 1 chooses
`0x801719AC`, exactly `0x7900` later. Other selector states are not established.
A block's byte at `+playerIndex` equal to `0xFF` means no record; otherwise the
record starts at `+0x44 + playerIndex * 0x38`. The `0x44`-byte header precedes exactly 22 player records; its remaining
fields are not fully decoded.

The original Controller Pak payload is `0x7900` bytes, based at `0x80168CD0`
with a staging copy `+0x7900`. Edited teams start at payload offset `0x13DC`.
Function `0x80016B4C(slot)` checks the combined five-block region of `0x1964`
bytes using `0x80009F14`; `0x80016CA4` stores its result at payload `+0x10`.
The algorithm initializes `0xFFFFFFFF`, XORs each byte into bits 31..24,
performs eight MSB-first rounds with polynomial `0x04C11DB7`, and complements
the result. It is non-reflected CRC32, not the usual ZIP CRC implementation.
The private implementation checks `123456789 -> FC891918` and empty input ->0.
Both staging regions in the existing snapshot calculate `B33F0781`, exactly
matching their stored words. This verifies checksum interpretation of current
initialized memory; it does not establish a completed in-game save/reload.

Other payload regions have separate checksum calls; a single checksum over the
whole Pak or whole note is insufficient. See [save-storage.md](save-storage.md)
for the original NISE/A4 descriptor, full-note read/write routes, Pak filesystem
and separate acceptance limits. No checksum over the factory roster region was
established by this research. The canonical ROM remains immutable and keeps its
existing identity checks.

## Proposed versioned data packages — not implemented

Keep this future work outside the 1.0 completion path. An initial package format
should target the proven existing slot capacities, preserving team IDs `0..105`
and 22 player indices per team. Adding teams beyond those capacities requires
separate analysis of every consumer, selection grid and competition structure.

1. Use a strict manifest with format/schema version, stable package ID, package
   revision, canonical base-ROM SHA-256, required engine/data-layout version,
   content SHA-256 per file, and an explicit save compatibility ID. Derive the
   package content identity from a deterministic manifest plus all file digests;
   a human-readable version alone is insufficient. Keep the base-ROM bytes
   unchanged. Unknown versions/digests fail before activating a package.
2. Describe typed changes by stable team/player slot IDs rather than arbitrary
   memory patches. An early lossless record format can preserve unresolved
   original bits while editing only verified fields. Validate counts, lengths,
   name encoding, default-order permutations, role references, formation banks
   and cross-file team/player references as one transaction. Unknown stat labels
   and unsupported fields remain unavailable to an editor.
3. Separate roster content from visual assets. Asset references should name a
   semantic resource plus a versioned mapping/descriptor identity, dimensions,
   format, palette and digest. Never store live pointers. Preserve descriptor
   bank/overlay alias identity until flag/kit ownership is proven. Packages may
   reference the user's locally imported base assets; distributable packages
   must not embed extracted original assets or the original database.
4. Validate the whole package into immutable host data before touching guest
   state. Future application needs a reviewed data-load boundary for every
   relevant raw overlay activation, before original consumers use the tables;
   active player copies must then come through the original provenance/copy
   path. A one-time write to a reused address is insufficient. Do not modify
   original CPU instructions or save a dump of runtime player extensions.
5. Select a package only outside an active match/competition; restart/reload the
   relevant original state after a committed selection. Record the active
   package digest with the session. Mid-match switching cannot be treated as
   changing a cosmetic setting because provenance and derived copies persist.
6. Namespace saves by stable package compatibility ID and bind a sidecar to the
   exact package/content digest, leaving the original Pak payload intact. The
   base game keeps its existing directory. Default to separation when roster
   IDs or player meanings change; never silently reinterpret an old competition
   or edited-team save. Any future migration needs an explicit source-to-target
   ID mapping, original checksum regeneration, validation, immutable backup and
   visible user choice. A package declaring compatibility needs tested evidence.

Before implementing the loader: finish country/selection/competition ID maps;
confirm all field labels and name encoding; connect actual flag/kit pixels to
team IDs; identify every reload/derived-copy boundary; and verify an original
menu save/restart/load with edited teams. Then test package validation and
atomic activation with synthetic data, followed by visible original-game
selection, team names, lineups, match entry and save isolation. This document
establishes data ownership and a bounded design; it claims no selectable package
feature today.
