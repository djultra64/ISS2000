# Regional base selection: US and European Career evidence

Original project work: djultra64. Date: 2026-10-15.

The user supplied a Europe English/German archive while considering the
Career/RPG mode as a requirement. This checkpoint compares only the authorized
ISS2000 US and European inputs. It does not migrate the active project, enable a
hidden mode, execute the European game or claim its menu has been verified.
Rendering implementation is paused at the user's request while this decision
is evaluated; its completed helper/test files remain available.

## Input identities

| Property | Existing US base | New European candidate |
| --- | --- | --- |
| Archive/member language label | USA, English/Spanish | Europe, English/German |
| Member name | `International Superstar Soccer 2000 (USA) (En,Es).n64` | `International Superstar Soccer 2000 (Europe) (En,De).n64` |
| Canonical size | 16,777,216 bytes | 16,777,216 bytes |
| Canonical SHA-256 | `e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850` | `6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf` |
| Cartridge identifier | `NISE` | `NISX` |
| Header revision | 0 | 0 |
| Entry address | `0x80000400` | `0x80000400` |
| Stored CRC1 / CRC2 | `8E835437` / `CD5748B4` | `336364A0` / `06C8D5BF` |

Root's memory-only archive audit found one European ROM member, with
adjacent-byte-swapped input order despite the `.n64` extension. The preservation
location is `.local/inputs/pal-en-de/rom.z64` with `identity.json`; the active
US `.local/rom.z64` remains unchanged. These identity results do not establish
that either file's whole game has passed acceptance. Equal size and entrypoint
do not make code/data addresses or save layouts interchangeable.

## US exposed main menu: visual and instruction evidence

Existing authentic settled capture
`.local/captures/40-boot12-after-notice.png` shows eight English entries. The
original selection routine independently has exactly eight exposed cases:

- Raw common load: ROM `0x32F090` to guest `0x803AC000`.
- Selection function: `0x803C34B8`, ROM `0x346548`.
- Cursor byte: `0x803F6D68`, loaded at `0x803C34C0`.
- Bound: `cursor < 8`, checked at `0x803C34D0`.
- Jump table: guest `0x803F22E0`, ROM `0x375370`, eight pointers.
- Destination: game-mode byte `0x80130854`.
- Commit caller: `0x803C3274` calls the selection routine at `0x803C3284`.

| Visible row / cursor | Menu label | Mode byte | Case address |
| --- | --- | --- | --- |
| 0 | Preseason Match | 0 | `0x803C34F4` |
| 1 | World League | 6 | `0x803C3504` |
| 2 | International Cup | 7 | `0x803C3518` |
| 3 | Euro Cup | 13 | `0x803C352C` |
| 4 | PK | 2 | `0x803C3540` |
| 5 | Scenario | 3 | `0x803C3554` |
| 6 | Training | 4 | `0x803C3568` |
| 7 | Option | 1 | `0x803C357C` |

The numerical case mapping is instruction-verified; its English row labels
come from the existing settled menu. Both the settled team-selection and paused
match snapshots contain mode byte zero, consistent with the observed Preseason
path. Seeing an entry establishes exposure, not successful completion of that
mode. There is no ninth Career/RPG choice in this original US main-menu handler.
Other hidden/submenu paths have not been exhaustively classified.

Private reproducible evidence is `.local/us-mode-inventory/`: the script checks
the supported ROM digest, exact eight-case guard, jump pointers and original
stores, and records the existing capture's hash:

```sh
python3 .local/us-mode-inventory/probe_us_modes.py \
  --output .local/us-mode-inventory/report-02.json
```

`report-01.json` is the saved successful checkpoint. Inputs are read-only and
report creation is exclusive. No game execution is involved.

## Retained US RPG dialogue prevents a stronger absence claim

Independent original-ROM inspection found encoded English narrative material
in the US input. Examples, described without reproducing the dialogue:

| ROM offset | Verified narrative subject |
| --- | --- |
| `0x59F737` | Beginning a football career and attending practice |
| `0x5AB4A3` | Achilles injury with possible career consequences |
| `0x5EE905` | Press conference about International Cup selection |
| `0x5EFAC3` | Protagonist discussing continuation of his career with a girlfriend |

The broader inspected dialogue region spans approximately
`0x5974EC..0x5EFAC3`. The independently decoded dialogue uses uppercase
`A..Z = 0x0B..0x24`, lowercase `a..z = 0x25..0x3E`, space `0x00`,
`FF 10` line breaks and `FF 11` endings. Encoding ownership is contextual;
do not silently apply this alphabet to every player-name or UI field.
Raw ASCII searches for Career/Success would miss these assets and textured
menu labels. Resident/J-League debug strings likewise do not establish a
selectable mode.

This proves retained narrative assets in the US ROM. It does **not** establish
a reachable complete US Career mode, an unlock flag, missing code restoration,
or a safe way to expose the assets. It would be incorrect to say the US ROM
contains no RPG material. Restoring an unexposed mode would be a distinct
reverse-engineering project, rather than a small menu-label change.

## European evidence and recommendation

The European candidate has a decoded `Career` keyword at ROM `0xDCE032` in a
bounded text inventory. This is supporting asset evidence; its selectable menu,
mode dispatcher, progression, save behavior and native execution are not yet
verified.

A contemporary firsthand FAQ by Janus Operative describes Career as an RPG
progression mode and, in its “No Career?” answer, reports that the American
release omitted the mode and recommends importing PAL. This agrees with the
US eight-entry menu evidence, but does not prove the new attached image's
execution. See the [2001 ISS2000 FAQ](https://www.cheatcodes.com/guide/faq-international-superstar-soccer-2000-n64-15859/).

The separately supplied manual has English/German pages but a KOA warranty,
despite its USA-style filename. Its regional attribution is ambiguous; use it
for described mechanics, not as proof that the US build exposes Career.

**Recommendation:** prioritize the European candidate as the base to verify
when original selectable Career/RPG is required. Preserve the working US
baseline and all private evidence. No migration has been performed by this
research. The recommendation is an inference from the exposed US dispatch,
European text evidence and contemporary regional account, not a claim of a
verified PAL menu or a completed European port.

Before changing the active base:

1. Pin the European input identity separately and verify its own menu/dispatch
   and Career load routes. Keep original functions and unknown-call failures
   honest; do not insert a forced-success Career entry.
2. Establish the European ROM/RAM section map, SDK boundaries, microcode and
   resource identities. Existing US addresses, hashes, function spans, culling
   hooks and task-bank constants remain US-specific until separately verified.
3. Audit PAL VI/audio/simulation cadence and decouple display interpolation from
   original timing. A 60/120 presentation target is not authorization to run a
   PAL simulation faster or transplant US timing constants.
4. Keep US and European imported ROMs and saves in distinct identity namespaces.
   Existing NISE/A4 note metadata and roster IDs cannot be assumed compatible
   with NISX. No automatic save conversion, overwrite or cross-region loading.
5. Record language scope explicitly: the attached candidate is labeled
   English/German; Spanish support from the US base does not transfer by itself.
   Any later localization or cross-region data port needs its own design.
6. Resume visible acceptance only when the user requests it. Confirm actual
   Career entry, progression and save/restart, then other original modes and
   the enhanced-rendering requirements. Asset/string presence cannot replace
   those checks.

No heavy PAL mapping, Windows-machine action, ROM alteration or game execution
was performed by this inventory/documentation task.
