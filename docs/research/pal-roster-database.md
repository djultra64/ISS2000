# PAL roster, registered players and package boundaries

Original project work: djultra64. Static checkpoint: 2026-10-15.

The principal PAL English/German revision has independently verified factory
roster consumers and a 110-player registration store. The 110 registrations
are five containers of 22 players, not 110 additional teams. PAL save payloads
also differ from US: the original PAL note is `0x7A00` bytes with game code
`NISX`. These findings support future package planning; no loader, package
selector, roster edits, game execution or save migration was performed.

All PAL addresses below are for canonical SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`,
revision `iss2000-pal-en-de-rev0`. US references use their separately pinned
original input. The algorithms and complete bodies were compared directly;
ROM/guest addresses were recovered from original PAL consumers, not by applying
a regional offset delta. Ranges have exclusive ends.

## Factory tables and ownership

| Table | PAL original ROM | PAL guest | Extent |
| --- | --- | --- | --- |
| Factory player records | `0x2F1290` | `0x801BFC40` | 106 × 22 × 56 = `0x1FE20` bytes |
| Default player order | `0x7B100` | `0x8007A500` | 106 × 22 = `0x91C` bytes |
| Two-variant team lookup | `0x7BB7C` | `0x8007AF7C` | 106 × 2 = `0xD4` bytes |
| Six-byte team metadata | `0x313FA0` | `0x801E2950` | 106 × 6 = `0x27C` bytes |
| Team coordinate records | `0x312384` | `0x801E0D34` | 106 × 11 × 6 = `0x1B54` bytes |
| Team visual index | `0x2F11A4` | `0x801BFB54` | 106 bytes; identity `0..105` |

The factory records end at ROM `0x3110B0` / guest `0x801DFA60`; their SHA-256
is `ec74f65de36b6af88f26ca1edfba9668515d36bf96bc3faad6af6d4bee057428`.
All 106 default-order rows are permutations of `0..21`. The first five metadata
columns stay within `0..10`; this does not assign their unverified role names.
The final metadata byte and coordinates retain the existing formation-consumer
interpretation, with field axes/units still requiring separate confirmation.

The nonresident tables belong to original raw load
`ROM [0x2DEE70,0x314A80) -> guest [0x801AD820,0x801E3430)`.
PAL loader `0x80057CEC` sets the original load-state bit and calls raw DMA
`0x80003E24` at `0x80057D3C` with those exact bounds; the subsequent original
clear covers `[0x801E3430,0x801ED700)`. Reused overlay addresses require a future
package to verify the owning ROM load and apply at each legitimate reload.
Resident tables use their own original resident mapping. No PAL RAM snapshot
was available for this research, so ROM/RAM equality is not claimed.

## Original record consumers and ID domains

Accessor `0x80013B58` checks factory team ID `<106` and calculates:

```text
0x801BFC40 + (teamID * 22 + playerIndex) * 56
```

Both inputs are masked to eight bits. The accessor does not validate
`playerIndex <22`; a future package must enforce that bound itself.
The complete `0x138`-byte original body has one normalized PAL match against US
`0x80013728`, with only address references changed. The independently recovered
PAL paths are:

| Team ID | Original PAL source |
| --- | --- |
| `0..105` | Factory record table |
| `106..108` | Shared 56-byte template `0x80077410`; player index ignored |
| `109..113` | Five registered/editable containers, selected by original save-source state |
| `114` | Separate template `0x80077448` |
| Other values | First factory record fallback |

The original PAL team-selection initializer `0x802A9834` calls provenance
builder `0x8002D300` for IDs `0..99`, with its explicit `<100` loop guard at
`0x802A9878`. This distinguishes 100 ordinary rows from the six additional
fixed factory rows `100..105`; the latter's exact English labels, unlock rules
and eligibility are not established by this inventory. The selection identity
table at `0x803F29E8` contains IDs `0..108`, including three template IDs.
Consequently 106 factory records must not be described as 106 national teams,
and table membership alone does not establish every mode's selectable count. Preserve reserved domains rather
than expanding the table and expecting other consumers to grow automatically.

## Original selection categories

The original team-selection overlay at ROM `0x46FC80`, guest `0x8029EEA0`,
reads signed category byte `0x802B092C`. Original function `0x802A7480`
selects its first team ID using a 12-entry table at `0x802B0768`;
original function `0x802A7508` selects its count using a 12-entry table at
`0x802B0798` and stores it to `0x802B092E`. Both original guards require a
category below 12. Reading the actual case instructions, including delay slots,
produces these domains:

| Category index | First ID | Last ID | Count |
| --- | --- | --- | --- |
| 0 | 0 | 13 | 14 |
| 1 | 14 | 23 | 10 |
| 2 | 24 | 36 | 13 |
| 3 | 37 | 50 | 14 |
| 4 | 51 | 60 | 10 |
| 5 | 61 | 68 | 8 |
| 6 | 69 | 78 | 10 |
| 7 | 79 | 85 | 7 |
| 8 | 86 | 95 | 10 |
| 9 | 96 | 99 | 4 |
| 10 | 100 | 105 | 6 |
| 11 | 100 | 108 | 9 |

The first ten groups form the contiguous ordinary domain `0..99`, exactly
matching the independently bounded 100-row initializer. Group 10 consists of
six additional factory IDs; group 11 adds the three template IDs to the same
six. Their presence in a switch does not establish their labels, unlock rules
or availability in every mode. The same guest addresses in another overlay
are unrelated and were excluded from this analysis.

The familiar national grouping, corroborated separately by the original menu
and regional team lists, is Europe/UEFA 51 across four pages, Africa/CAF 10,
CONCACAF 8, South America/CONMEBOL 10, Asia/AFC 17 across two pages, and
Oceania/OFC 4. The ROM proof here establishes the exact numeric page domains;
it does not claim to have decoded or visually checked the PAL confederation
label bitmaps. In particular, 106 factory IDs and the 110-player registration
capacity must remain separate from the 100 ordinary national selections.

Original `0x8002D300` creates 22 source `{teamID,playerIndex}` pairs from the
PAL default-order table. Original `0x8002D3C0` then calls the verified source
accessor and copies all 56 source bytes into 76-byte active records. Side blocks
start at `0x801A583C`, stride `0x11E8`, with active records at `+0x28`, source
pairs at `+0x6B0` and ordering at `+0x6DC`. The remaining 20 bytes of each active
record are runtime state and must not enter a package's source roster data.
The current-lineup indirection is a separate original table at `0x8012DED7`;
source IDs, active slots and lineup positions remain distinct.

Getter `0x800114E4` has the same complete 39-selector field logic as the original
US getter, with its PAL table at `0x8009ADA8`. All 39 table pointers have the
same relative positions inside the corresponding original function bodies.
The record field widths, packed masks and eight encoded name bytes at
`+0x18..+0x1F` therefore retain the verified structural interpretation in
[the US field inventory](roster-database.md). Many stat labels, alphabet/control
codes and bit meanings remain unresolved; structural equivalence does not
supply those meanings.

## PAL factory content is different from US

The entire default-order, two-variant, metadata, coordinate and visual-index
ranges match their independently located US reference ranges. The factory
player table does **not**: all 2,332 complete records differ, totaling 9,754
changed bytes. The changed record offsets are:

| Record offsets | Changed bytes/records at those positions |
| --- | --- |
| `0x18..0x1F` | 5,161 encoded-name bytes total |
| `0x28` | 2,269 records |
| `0x2D` | 2,323 records |
| `0x2E` | One record |

This comparison describes bytes, not an inferred licensing explanation or
unverified stat labels. Equal table shape and several equal auxiliary tables
cannot authorize a US roster package on PAL. Its expected baseline content,
encoded names and semantic data can differ even when team/slot IDs agree.

## The original 110 registered-player slots

PAL resident `0x8001BADC` explicitly rejects registration indices `>=110` after
masking to a byte. It divides the index by 22 using original unsigned
multiply/shift arithmetic, then computes:

```text
group = registrationIndex / 22       # 0..4
slot  = registrationIndex % 22       # 0..21
container = 0x801675CC + group * 0x514
record    = container + 0x44 + slot * 56
```

The `0x44`-byte header plus 22 records exactly fills each `0x514`-byte container.
The writer copies 56 bytes from its input blob's `+0x18`, then writes metadata
from input `+1` into `container[slot]` and input `+3` into
`container[0x16+slot]`. The complete meanings of these metadata categories and
the rest of the header are not assigned here. The source accessor treats
header byte `0xFF` as missing and returns null; an ordinary registered record
still uses its same source-record path into active players.

Selector `0x8012E62D` values 0/2 choose base `0x801675CC`; value 1 chooses
`0x8016EFCC`, exactly `0x7A00` later. Original team/source IDs `109..113`
address these five containers. Calling them five editable team blocks describes
the storage/accessor organization; it does not prove five extra selectable
national teams, and it must not be confused with the total of 110 players.
The preserved US writer `0x8001B638` independently has the same complete
110-slot body structure. The additional PAL Career route supplies developed
players to an existing registration mechanism; it is not evidence that every
US registration slot or editor was removed with the exposed Career menu.

The supplied online manual describes registering a player after successful
Career completion, gives a capacity of 110, and describes both created and
Career-developed players in transfer operations. These mechanics agree with
the independently proven 5×22 PAL capacity. Its regional attribution remains
ambiguous because of the filename/warranty/language mixture; this document
uses original PAL instructions as the capacity proof. See the [manual, printed
page 16 and transfer section](https://www.videogamemanual.com/n64/International%20Superstar%20Soccer%202000%20(USA).pdf).

## Bounded Career-to-registration dataflow

Original PAL Career code provides a concrete bridge to the same registration
input:

1. Career helper `0x801F7AF8` in ROM-owner section
   `overlay_516ce0_801ef060` constructs a 56-byte record using the original
   Career state at `0x80128E38`. It packs bits, converts eight name positions,
   reads Career attributes and derives additional fields through original
   routines. It is not a raw copy of an entire progression/save structure.
2. Career transition `0x801F2DD8` calls `0x801F2E20`; the latter calls that
   builder with mode argument 1 and copies exactly 56 bytes from its stack
   buffer into guest `0x8012E120`. It separately copies eight name bytes into
   `0x8012E110`. The surrounding transition later requests original state
   `(3,4)` through `0x8000C7CC`.
3. The registration UI commit `0x802BC798`, owned by
   `overlay_3d0680_802bae10`, computes `group*22+slot`, records the corresponding
   `109+group`/slot pair, and passes blob `0x8012E108` to `0x803CF5C0`.
   Its record is at blob `+0x18`, exactly `0x8012E120`.
4. Common wrapper `0x803CF5C0` calls the independently verified bounded resident
   writer `0x8001BADC`, which copies that record to the selected registration
   slot and recomputes the original registered-region checksum.

These original producer/consumer addresses and widths establish the shared
record/dataflow boundary. They do not prove that all eligibility branches,
complete Career progression, UI confirmation, save and restart have succeeded.
The current Career protagonist/state and user registrations are mutable user
progress, outside a future factory-roster package's writable domain.

## PAL note and checksum identity

Original PAL manager `0x80019514` allocates `0x7A00` bytes; original
`0x800198C8` transfers that same full payload size. The note descriptor at
`0x80077590` (ROM `0x78190`) contains:

| Property | Original PAL value |
| --- | --- |
| Payload size | `0x7A00` = 31,232 bytes = 122 data pages |
| Game / company | `NISX` / `A4` |
| Extension | Four zero bytes |
| Encoded filename | `22 3C 2C 3C 2C 3C 12 10 10 10 0F 0F 0F 0F 0F 00` |
| Payload guest base / staging stride | `0x801661F0` / `0x7A00` |
| Registration payload offset | `0x13DC` |
| Five-container checksum extent | `0x1964` bytes from `0x801675CC` |
| Checksum word | Payload `+0x10`, guest `0x80166200` |

The 121-page manual statement and preserved US `0x7900` note do not override
the original PAL allocation/transfer/stride evidence. Original PAL registered
CRC wrapper `0x80016F7C` uses `slot*0x7A00`, the verified 5-container base and
length `0x1964`; its checksum calls original `0x8000A3D4`, whose complete
normalized body matches the verified non-reflected MSB-first CRC32 routine.
There are other independently checksummed regions; do not replace them with a
single checksum over the entire note. No PAL memory CRC/save-roundtrip check
is claimed without a corresponding snapshot or authorized execution.

## Future package contract — proposed, not implemented

Use `iss2000-pal-en-de-r0-roster-v1` as a **proposed** PAL data-layout identity,
paired with the exact canonical PAL digest and a separate proposed PAL Pak
layout identity. An unchanged 56-byte structure does not make the US and PAL
base/content/save identities interchangeable.

Initial packages may target existing factory slots `0..105`, players `0..21`
and separately proven visual resources. They must preserve reserved IDs,
registration headers/records, current Career state, source provenance and
original derived-copy paths. A future Career-compatible declaration needs its
own progression/reference/save testing; ordinary exhibition success cannot
supply it. Unsupported mode/visual capabilities remain unavailable, including
3D kits whose ownership is still unresolved.

Original remains a built-in choice using the exact regional base and its
independent saves. Package selection must occur before active match,
competition or Career state is created, or after a reviewed orderly save/exit
and reload. Save namespaces include base revision/content identity and package
compatibility identity; a package never rewrites Original's registered players
or silently reinterprets a Career/competition save. Do not automatically migrate
US notes, PAL notes or saves from another package. See the updated
[proposed package plan](roster-pack-plan.md).

Private reproducibility: `.local/pal-rosters-01/report.json` records table/body
hashes, every changed instruction in the matched consumers, original Career/UI
route owners, regional differences and save bounds. Run its copied
`pal_roster_evidence.py --output .local/pal-rosters-FRESH` for a fresh,
exact-identity-gated report. It emits metadata only, preserves both ROMs and
never publishes original records, textures or saves. The copied
`team_groups.py` reproduces `team-groups.json` directly from the two original
selection switches and their ROM-owned tables. Both evidence reports were
independently regenerated and compared byte-for-byte. No new game verification
was performed by this documentation task.
