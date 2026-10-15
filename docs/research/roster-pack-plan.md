# Selectable roster and visual packages — proposed plan

Original project work: djultra64. Date: 2026-10-15.

**Status: PROPOSED future work; not an approved implementation specification.**
This document records a concrete sequence for review. It does not authorize a
loader, change the supported ROM, add a menu or expand the 1.0 implementation
scope. Finish and verify [1.0 acceptance](../releases/1.0-acceptance.md) first.
Research and planning can proceed in parallel; implementation requires a later
approved design based on the remaining evidence.

**Goal:** let a user choose Original or a validated package of teams, players
and, separately, proven visual resources before entering a match, while
preserving original behavior and saves.

**Architecture:** keep the imported canonical ROM immutable. Validate a package
into an immutable host representation, then apply only reviewed data overrides
at verified original load boundaries. Preserve stable guest IDs and original
simulation/copy paths. Original is a built-in selection independent of any
installed package.

**Evidence, not an approved feature spec:**
[pal-roster-database.md](pal-roster-database.md),
[roster-database.md](roster-database.md) and
[team-visual-assets.md](team-visual-assets.md). Both distinguish verified
addresses and widths from hypotheses. Proposed host components would use the
existing C++20/portable filesystem approach; offline inventory tools can use
Python, without introducing a Python dependency in the shipped game.

## Principal PAL identity — proposal update

The principal future package target follows the PAL English 1.0 base,
`iss2000-pal-en-de-rev0`. The earlier US research remains a separate preserved
reference; it does not supply PAL addresses, baseline bytes or save layouts.
Original PAL consumers independently confirm the same 106×22×56 factory shape,
but all 2,332 complete records differ from US, and PAL uses a `0x7A00` NISX Pak
payload rather than the US `0x7900` NISE payload. Exact original PAL field/load
and registration evidence is in [pal-roster-database.md](pal-roster-database.md).

The proposed format must bind both `dataLayoutVersion` and `saveLayoutVersion`
to the exact base-ROM digest. The 110 registered-player slots are five containers
of 22 user records, outside the factory override domain. Current Career state
and registration data remain user progress. A package's declaration of Career
support requires separate original progression/reference/save verification;
ordinary exhibition tests cannot establish that compatibility.

## Boundaries and unresolved evidence

- Phase 2 replaces existing factory slots: exactly 106 team IDs `0..105`,
  22 player indices `0..21` per team, 56 source bytes per player. It does not add
  teams or reinterpret reserved IDs `106..114`, edited-team blocks or templates.
- Team ID, source player ID, active-record index and current lineup slot differ.
  Preserve the provenance pairs and the original 56-to-76-byte active copy.
  Never serialize the 20 mutable runtime bytes as roster content.
- Names use eight encoded bytes with multi-byte paths; a complete safe encoder
  is not yet known. Attribute getter offsets are known; many semantic labels
  and packed fields are not. Those fields are unavailable to an editing UI until
  verified; a lossless representation retains them unchanged.
- The preserved US visual research finds two callers with factory bounds
  `<0x67` and `<0x6A`; these visual identities still need PAL ownership proof. The intermediate
  table is identity for 106 bytes, but that does not resolve the special handling
  of IDs `103..105` in every caller. Selection/country/competition maps remain
  incomplete; 106 DB rows do not prove 106 selectable national teams.
- In the preserved US visual research, bank 145, descriptor and palette
  mappings are traced, but the exact asset
  supplying its reused texture workspace is unresolved. The 77-entry 48×32 run
  is not proof of 77 countries or flags. Flag identity requires actual pixels
  and original load provenance.
- UI art does not establish 3D jersey, shirt/shorts/socks, goalkeeper, mesh,
  skeleton, UV or material ownership. The paired appearance mask is not a single
  texture index. Defer unsupported visual categories rather than invent hooks.
- Existing Controller Pak note fields and edited-team CRC regions are known;
  full mode/player reference persistence and package migration are not. An
  initialized-memory CRC match is not save/restart acceptance.

## Proposed files and responsibilities

These names describe future components; none is created by this plan.

| Proposed component | Responsibility |
| --- | --- |
| `tools/inventory_rosters.py` | Read-only exact-ROM inventory; private machine-readable ownership and identity report |
| `tools/inventory_team_assets.py` | Read-only verified load/decode/descriptor/palette inventory; rejects unknown decoder modes |
| `src/runtime/roster_package.*` | Strict manifest parsing, file/digest/reference validation, immutable staged package |
| `src/runtime/roster_overrides.*` | Reviewed factory data application at original data-load boundaries |
| `src/runtime/team_asset_overrides.*` | Separately reviewed bitmap/palette replacements with resource ownership |
| `src/runtime/package_selection.*` | Pending/active selection transaction and save-namespace contract |
| Later original-menu/platform integration | Presents selection and safe restart without exposing guest addresses or patch details |

Keep parsing separate from guest mutation, and roster tables separate from
visual resources. Reuse existing portability helpers where their guarantees
match; do not relax ROM import verification or couple packages to a test input
fixture. Future tests should mirror these responsibilities.

## Manifest and portable storage proposal

For the principal PAL proposal, the baseline canonical ROM SHA-256 is
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
Every package declares this exact base identity and explicit roster/save layout
versions. The preserved US digest
`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`
requires its own separate manifest/layout and never auto-selects on PAL.
A filename, equal record dimensions or console header CRC is insufficient.

| Manifest field | Proposed rule |
| --- | --- |
| `schemaVersion` | Integer 1; reject unknown versions and duplicate keys |
| `packageId` | Stable 1..64-character lowercase ASCII letters/digits/hyphens identifier, beginning with a letter; independent of display name/version; reject platform-reserved names |
| `packageVersion` | Human-readable immutable release revision; never the integrity check |
| `displayName`, `description` | Bounded UTF-8 text; displayed as text, never interpreted as paths/markup |
| `baseRomSha256` | Exact canonical supported-ROM digest |
| `dataLayoutVersion` | Explicit reviewed layout, initially proposed `iss2000-pal-en-de-r0-roster-v1` |
| `saveLayoutVersion` | Explicit regional payload/CRC identity, initially proposed `iss2000-pal-en-de-r0-pak-v1`; independent from roster shape |
| `capabilities` | Explicit roster/names/UI-art categories; unknown categories reject; no implied 3D support |
| `languages` and `modes` | Explicit supported subsets; unresolved modes stay unavailable for that package |
| `saveCompatibilityId` | Same bounded identifier grammar as `packageId`; a declaration alone never authorizes migration |
| `files` | Unique relative path, resource kind, exact byte size and SHA-256 per payload |
| `teamSlots` / resource mappings | Unique bounded team/player IDs and semantic asset references; no arbitrary memory writes |

**Content ID:** compute SHA-256 of the exact bounded UTF-8 manifest bytes after
strict parsing and complete payload digest verification. Payload hashes in the
manifest bind the entire file set transitively. The manifest does not contain
its own content ID; installed state records the computed ID. Whitespace changes
therefore create a different immutable package identity, which is acceptable.
The computed content ID is exactly 64 lowercase hexadecimal characters.
Reject undeclared files that could affect interpretation. A display version
cannot substitute for this content ID or overwrite another installed revision.

A first installation format can be an unpacked directory to avoid an unnecessary
archive decoder in the product. If archive import is later approved, impose
compressed/uncompressed byte, file-count and nesting limits before allocation,
reject traversal/symlinks/case-fold collisions, and validate in private staging.
Its limits need an explicit reviewed resource budget; never reuse the ROM's
16 MiB limit as an unexplained package-size assumption.

All paths remain under the existing portable data root beside the executable,
or its explicit `--data-dir` override. No home-directory discovery is added:

```text
data/
  iss2000-pal-en-de.z64             immutable verified principal PAL import
  iss2000-us.z64                    preserved US import if already present
  graphics.json                    existing unrelated preferences
  packages/
    <baseRomSha256>/<packageId>/<contentId>/
                                    immutable installed manifest and payloads
  package-state/<baseRomSha256>.json
                                    independent active/pending identity per base
  package-staging/                 bounded interrupted-install recovery area
  saves/iss2000-pal-en-de-rev0/      Original PAL save namespace
  saves/                           preserved legacy US save location
  package-saves/
    <baseRomSha256>/<packageId>/<saveCompatibilityId>/
      package-binding.json         exact content identity and reviewed compatibility
      ...                          independent per-port Pak/backend files
```

Original uses the matching regional save namespace. Existing US files remain
preserved in their established location; this proposal does not relocate them.
Package saves do not replace either region's files. Even a package retaining the same slot IDs can change their meanings;
sharing an existing competition or player edit silently is unacceptable.
Reject unreviewed content-ID changes within an existing save compatibility
namespace. Any later compatible revision needs explicit validated compatibility
metadata and tests; default to a new namespace.

## Phase 1 — read-only inventory and extraction

**Deliverable:** a reproducible private database/asset inventory, with no runtime
behavior change. Public artifacts contain tools/schema and findings, never
extracted original records, textures, generated original CPU code or saves.

- [ ] Turn current private checks into focused read-only tooling with exact-ROM
  verification and synthetic malformed-input tests. Reproduce all six complete
  ROM/RAM table comparisons, 106 lineup permutations, 44 active source copies
  and original edited-region CRC checks from existing fixed US inputs. PAL
  has an independent six-table ROM inventory and registration/save proof; it
  needs its own RAM, active-copy and actual save/restart evidence.
- [ ] Complete numerical team-to-country/selection/competition maps using actual
  original consumers and settled visible captures; distinguish factory/edited
  branches and identify every language-specific label path.
- [ ] Verify field labels, bit meanings and name encoding, including accent,
  multi-byte, padding and eight-byte boundary cases. Preserve raw bytes beside
  semantic interpretations privately, so round-trip loss can be detected.
- [ ] Trace the actual asset request supplying bank 145. Match decoded payloads
  byte-for-byte to a settled snapshot, then correlate team ID, descriptor,
  palette and visible art. Record alias/reload lifetime, not just RAM addresses.
- [ ] Independently establish kit/clash/goalkeeper and 3D material ownership.
  Unsupported decoder modes, unknown fields and unmatched pixels remain
  explicit inventory failures, rather than fabricated successful extraction.

**Gate:** each replaceable field/resource has a documented owner, size, encoding,
original identity, consumer and reload path. A verified subset may advance;
unknown visual categories remain excluded.

## Phase 2 — bounded factory roster overrides

**Deliverable:** validated data-only replacement of existing factory slots,
without a selector or visual-replacement claim.

- [ ] Specify a lossless typed record representation. Unknown bits/bytes retain
  their baseline values, with base identity checked before applying changes.
  Initially expose only verified fields; unresolved names remain read-only.
  Preserve baseline unknown bits locally from the verified user import. Public
  packages contain user-authored typed changes/new art, rather than redistributing
  complete extracted original records or assets; a private lossless inventory
  is not automatically a distributable package.
- [ ] Write failing synthetic tests for strict manifest parsing, required fields,
  wrong base/layout/hash, duplicate slots, invalid counts/indices, malformed
  names, lineup permutations and cross-table role/formation references.
- [ ] Implement validation into an immutable staged object without mutating ROM,
  guest state, package state or save files. A malformed payload must leave the
  previous staged/active package intact.
- [ ] Apply validated tables at every proven factory-data load boundary before
  original consumers run. Include resident order/variant tables as needed;
  guard overlay aliases by load identity and expected baseline content. Retain
  the original provenance and active-player copy functions.
- [ ] Test repeated loads, unload/reload and both sides; verify copied factory
  fields and runtime state remain distinct. Reserved IDs and custom team records
  must execute their original paths unchanged.

**Gate:** Original reproduces baseline bytes; a bounded synthetic change affects
only the intended factory slot and survives its legitimate reloads. Actual
selection/lineup/match checks follow after 1.0 and implementation approval.
No new team count, AI rules, simulations or unknown-field editing enters here.

## Phase 3 — separately owned visual resources

**Deliverable:** replacements for the exact verified subset of UI/team assets;
3D kits remain excluded until separately proven.

- [ ] Validate texture dimensions, format, byte extent, descriptor ownership and
  separate palette identity. Preserve CI4 nibble packing and RGBA5551 semantics
  where those are the proven original formats.
- [ ] Treat shared palettes explicitly: clone/remap through a reviewed resource
  binding or reject the conflicting override. Recoloring unrelated art is a
  failure. Special palette selectors `0xFE/0xFF` retain distinct semantics.
- [ ] Preserve original reload/alias boundaries and procedural controller-prompt
  override precedence. Reject a menu bitmap presented as a 3D jersey resource.
- [ ] Test primary/alternate selections, both sides, edited/template branches,
  language transitions and replay reloads. Pair a settled real capture with
  exact decoded data identity before marking a flag or uniform verified.

**Gate:** declared visual categories render in their actual original consumers
without adjacent-resource damage. Unsupported categories are absent from the
package's capability list and UI description.

## Phase 4 — selection, activation and save isolation

**Deliverable:** an accessible in-game package selector at a proven menu safe
point before match/competition state is created. Original is always available,
even if every external package is missing or invalid.

- [ ] Show Original, validated package names, supported modes/languages, current
  selection and a concise incompatibility reason. Prompts use logical actions
  and the active controller family's real glyphs/names, including Nintendo's
  swapped physical labels and the existing manual-family fallback.
- [ ] Validate/stage before requesting a safe transition. If original state cannot
  be safely rebuilt, display “Restart required to apply this package” and retain
  it as pending until a user-confirmed orderly restart. Do not offer mid-match
  hot swapping or silently discard an active match/competition.
- [ ] Prepare a save namespace and durable pending record before activation.
  Acquire the existing storage exclusion and bind backend paths before starting
  any guest threads/save operations; the backend cannot change under live writes.
- [ ] Publish selection with a portable atomic transaction/journal: install
  immutable content, record pending intent, validate/load under exclusive
  ownership, then commit active identity. Maintain the previous active identity
  until commit. On failed pre-commit application, discard partial guest state
  and reinitialize through original loading, or restart with the previous
  selection; never continue with mixed tables.
- [ ] Recover interrupted transactions explicitly. A crash with only pending
  intent keeps the last committed package and files; a missing/corrupt committed
  package explains the problem and offers Original or restoration. Selecting
  Original also selects its original save namespace, never the package's saves.
- [ ] Do not automatically migrate saves. A later migration feature would require
  explicit source/destination ID maps, original per-region checksum regeneration,
  immutable backups, a dry-run validation and visible user consent. It is outside
  these four phases.

**Gate:** change and rollback preserve every existing save byte, malformed
packages produce clear failures, copied portable folders retain configuration,
and actual original-game transitions/restarts load the displayed package.

## Required test and acceptance matrix

| Layer | Required cases and assertions |
| --- | --- |
| Manifest | Wrong/missing schema, ROM/layout/hash; duplicate keys/IDs/files; unsupported capabilities; deterministic exact-byte content ID; no output mutation on failure |
| Filesystem | Traversal, absolute paths, symlinks, case-fold collisions, missing files, changed payload during read, oversized content, interrupted install; Linux/Windows filename behavior |
| Rosters | 106 × 22 × 56 extents; ID bounds; reserved domains unchanged; unknown bits round-trip; valid lineup permutations; roles/formation references; multibyte name boundary |
| Derived state | Both side blocks and provenance pairs; 56-to-76-byte copy; current lineup indirection; repeated raw loads and wrong overlay alias rejection |
| Visuals | Texture/palette independence, shared-palette conflict, dimensions/format, primary/alternate, edited branches, unsupported 3D resource rejection, prompt precedence |
| Transactions | Failure before/after pending journal, incomplete guest application, process crash, missing previous content; no mixed active package; atomic state publication or explicit recovery error |
| Saves | Original unchanged; package namespaces isolated; same IDs/different meanings; content mismatch refused; per-port independence; no automatic migration or new checksum shortcuts |
| Modes/languages | Selection, exhibition, tournaments/leagues, training, editor, replay and PAL English/German checked independently; preserved US English/Spanish evidence remains regional; unsupported combinations blocked before state creation |
| Actual game | Original baseline; package selection and names/lineups; visible match actions and return; restart/load and edited teams; supported art in real menus/match; correct physical prompts |
| Portability | Linux first; final Windows verification; copied-folder launch/import; relative data/config/save/package paths; no source-tree/home dependency or test-only input endpoint |

Each implementation task starts with meaningful failing synthetic tests and
ends with focused passing checks plus independent review. Those checks prove
the data/transaction mechanism, not a playable package. Visible game evidence
is required for every supported mode/language/visual category; an untested mode
is recorded as unverified and unavailable in the package's declared support.
No fake-success fallback, empty original-function replacement or suppressed
runtime failure is permitted. An ordinary validation failure preserves the
previous state and gives an actionable message.

The 1.0 dependency is explicit: baseline playable-match, persistence, controller,
render/audio and final portable-folder requirements remain tracked in its own
acceptance record. Package work cannot be used as evidence that any of those
requirements passed, and this proposal changes none of their status.
