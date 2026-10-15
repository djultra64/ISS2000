# PAL runtime bindings and original timing

Original project work: djultra64. Static checkpoint: 2026-10-15.

The English/German PAL revision now has 53 independently located runtime-service
bindings and four project-owned Controller Pak device boundaries. The manifests
are `config/recomp/iss2000-pal-en-de-rev0/runtime-symbols.json` and
`device-boundaries.json`. They require canonical SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
The original US manifests/input/saves are preserved. This work performed static
analysis and CPU translation only; no PAL game or Windows binary was executed.

## Instruction and ABI proof

Every manifest entry has a unique complete PAL function-body match to the
already reviewed original ISS2000 US body, after masking only relocation-sensitive
calls and guest-address operands. Opcodes, registers, stack/structure offsets,
ordinary constants and relative branches remain exact. Every absolute control
transfer is additionally checked: internal targets preserve their relative
position; service calls reach the corresponding independently matched PAL body;
other callees are checked against their original complete PAL bodies.

Small queue/access/parser helpers sometimes have identical normalized bodies
at two addresses. Their original PAL call edges and distinct relocated globals
resolve the intended helper; they are not new host-service bindings. No other
game binary, fixed regional offset or hypothetical success return was used.
The extra original PAL X-scale function at `0x8005F080` illustrates why a single
regional delta is insufficient: earlier SDK functions move by `0x7B0`, later
ones by `0x880`, and data relocations vary independently.

Private `.local/pal-runtime-01/body-proof.json` records full bounds/digests,
every changed instruction and each original PAL call target. Its companion
`audit_runtime.py` repeats the full-body uniqueness, source coverage and segment
hash checks against the two authorized ISS2000 inputs. It scans only the
independently recovered PAL resident CPU extent. The public verifier also passes:

```sh
python3 -m tools.identify_runtime \
  --rom .local/inputs/pal-en-de/rom.z64 \
  --manifest config/recomp/iss2000-pal-en-de-rev0/runtime-symbols.json
python3 .local/pal-runtime-01/audit_runtime.py
```

No currently reviewed US service remains unmatched in PAL. This does not prove
that all PAL-only original paths are mapped, that every upstream service is
implemented, or that a native PAL boot succeeds. Raw DP and unsupported yield
behavior must retain explicit failures. See [PAL code map](pal-code-map.md) for
the unresolved original overlay call and provisional executable inventories.

## Entry and thread identities

The original PAL entry at `0x80000400` clears BSS from `0x800ADD20` for
`0x11F7D0` bytes, sets stack `0x800CC370`, then jumps to `0x80000814`.
Original US seed `0x80000500` is inside a different PAL function and cannot be
retained as a PAL function boundary.

| Original PAL role | Address / original evidence |
| --- | --- |
| Boot continuation | `0x80000814`; calls `osInitialize` at `0x80000830` |
| `osInitialize` | `0x80062310` |
| `osCreateThread`, `osStartThread` | `0x8005E280`, `0x8005E440` |
| Idle thread | `0x80000898`, id 1 / priority 9 / stack `0x800A02D8` |
| Main thread | `0x8000092C`, id 5 / priority 10 / stack `0x800A42D8` |
| Graphics scheduler thread | `0x8001D72C`; entry constant at `0x8001D5E4` |
| Audio thread | `0x8004B998`; entry constant at `0x8004B948` |
| PI / VI manager threads | `0x80058A80`, `0x8005ECC0` |
| IS64 output transport | `0x80003B88`, ROM `0x4788`, size `0x1A8` |

The IS64 body is also a unique full-body match. It checks the original IS64
magic and device registers and takes buffer/count in `a1`/`a2`. A host debug
transport can replace that reviewed boundary while preserving original guest
formatting. Initial function pointer `0x8006CFB4` points to original no-output
formatter `0x8005D8D0`; pointer presence alone is not an active debug-output claim.

## Original Controller Pak filesystem stays authoritative

PAL `osPfsInitPak` is `0x80060DD0`, ROM `[0x619D0,0x61BC8)`, 504 bytes.
Original call `0x800046F8` passes queue `0x801A3DE8`, OSPfs base `0x801A043C`
plus `port * 104`, and channel in `a2`. Its instructions preserve the original
ID checksum/repair, label, inode and directory algorithms. The full 126 original
instructions were separately translated to
`.local/pal-runtime-01/functions/func_80060DD0_resident.c`; the PAL manifest pins
the source hash and requires the collision-free export
`iss2000_original_80060DD0`. The source also compiles independently to an object.
The US retained source and old public function name are not PAL substitutes.

| Project boundary | PAL address | ABI / required behavior |
| --- | --- | --- |
| `osPfsIsPlug` | `0x800608E0` | queue, **byte** bitpattern; includes inserted Rumble Pak |
| `__osPfsGetStatus` | `0x80061100` | queue, port; invalidate inode-cache **byte** `0x80099A44` to `0xFA` with original `sb` at `0x8006112C`; preserve actual accessory/error results |
| `__osContRamRead` | `0x80061E10` | queue, port, block index, 32-byte buffer |
| `__osContRamWrite` | `0x80062000` | same arguments plus force at stack `+0x10`; original protected-block rules |
| Motor init / access | `0x8005F8A4` / `0x8005F760` | Original OSPfs queue/channel/bank/status ABI is unchanged |

A selected Controller Pak must use the uniquely retained PAL filesystem body.
Disconnected, absent, different or corrupt accessories must keep real errors.
An upstream no-Pak result does not implement filesystem initialization. Save
namespace/layout compatibility and Career save/restart remain unverified.

## Original PAL VI and audio cadence

Independent original PAL evidence establishes the region, rather than relying
on the cartridge name:

- Boot `0x80000818..0x8000082C` explicitly writes PAL video clock **49,656,530**
  to `0x80099A68`. Original `osInitialize` selects that same clock when guest
  `osTvType` at `0x80000300` is zero.
- Original mode selection at `0x80001F44..0x80001F68` chooses PAL VI records
  `0x80098DC0` or `0x80099040`. They contain `vSync=625` / interlaced `624` and
  PAL timing registers; these represent the original PAL 50-field cadence.
- Original `osViSetEvent` call `0x8001D5CC` preserves its supplied retrace count.
- Original audio builder `0x8004B6D0..0x8004B6E8` multiplies actual audio
  frequency by float `0.02`, independently identifying a 50-Hz audio quantum.

This establishes **50-Hz PAL VI**, not a claim that every game simulation or
render pass runs at 50 fps. Original retrace divisors and game decisions remain
authoritative. The 120-fps setting is a presentation/interpolation target.

Pinned N64ModernRuntime `librecomp/src/recomp.cpp` initializes `osTvType=1`
(NTSC). A project PAL initialization override must set it to zero after upstream
initialization and before the original entry. Pinned `ultramodern/src/events.cpp`
hardcodes 60 in both the VI deadline and elapsed-VI counter. Both expressions
must use 50 for this PAL profile, independently of renderer presentation rate.
A privately generated, source-hash-checked project override can keep the pinned
dependency checkout pristine. This research did not edit dependency sources.

PAL `osAiSetFrequency` is `0x80058FE0`, size `0x120`. Its original algorithm is:

1. Convert clock to float32, divide by request converted to float32, add
   float32 `0.5`, truncate to unsigned DAC divider.
2. Return `-1` if divider is below 132.
3. Set bitrate to `min((divider / 66) & 0xFF, 16)`; write DACRATE `divider-1`
   and BITRATE `bitrate-1`.
4. Return integer `clock / divider` as actual frequency; original caller
   `0x8004B678` stores this return and uses it in audio-buffer calculations.

For a 32,000-Hz request the original result is 31,995 Hz. Pinned upstream
`ai.cpp` passes the request through and leaves its NTSC quantization code
commented out. A project PAL adapter should preserve original quantization,
return the actual rate and configure the host converter to that rate. Existing
current/next AI FIFO behavior remains required; no instantaneous DMA success
stub is justified.

## RSP and RT64 identities

All six segments below match complete original US ISS2000 bytes. Four graphics
segments independently match the pinned RT64 word-swapped XXH3 registry, with
exact hashes in private `microcodes.json`. RSP audio source can therefore retain
the existing translated original program, with PAL dispatcher admission.

| Segment | PAL guest | PAL ROM | Compared size |
| --- | --- | --- | --- |
| RSP boot | `0x80069A00` | `0x6A600` | `0xD0` |
| F3DEX2.fifo 2.06 text | `0x80069AD0` | `0x6A6D0` | `0x1390` |
| F3DEX2.fifo 2.06 data | `0x80099EF0` | `0x9AAF0` | `0x420` |
| F3DLX2.fifo 2.06.Rej text | `0x8006AE60` | `0x6BA60` | `0x1188` |
| F3DLX2.fifo 2.06.Rej data | `0x8009A310` | `0x9AF10` | `0x410` |
| Audio program | `0x8006BFF0` | `0x6CBF0` | `0xE28` |

Original PAL audio task construction at `0x8004BC00..0x8004BC3C` explicitly
supplies boot `0x80069A00`, program `0x8006BFF0` and data `0x8009A720`.
The secondary graphics registry entry retains upstream's compatibility caveat;
static recognition does not verify every rendered Career or match scene.

## Enhancement addresses and original scene proof

All eleven currently used US enhancement hook bodies have unique complete PAL
instruction matches. Private `enhancement-layout.json` records the original
bounds/digests and corresponding globals with per-instruction evidence.

| Hook role | PAL address |
| --- | --- |
| Matrix arena / root / child builders | `0x80025910` / `0x80025958` / `0x80025D70` |
| Record allocation / child allocation / free | `0x8002AC08` / `0x8002AE80` / `0x8002AD28` |
| Far visibility / culling rebuild / world corners | `0x80022D90` / `0x80023488` / `0x80024A10` |
| Title string registration / sprite draw | `0x80003EB4` / `0x80041B50` |

The PAL transform record pools are `0x80145624` (285 × `0x98`) and
`0x8014FF5C` (900 × `0x60`), with unchanged original record-field ABI. The
original pool loops independently specify these counts/strides. Matrix arena
base is `0x800A7848`, each bank is `0x5100`; selector `0x8009DED0`, cursor
`0x800B1A48`, end `0x800B1A4C`. Perspective matrices start `0x800C1AC0`
with 64-byte bank stride; view matrices start `0x800CC388` with 64-byte bank
and 128-byte camera stride.

Culling globals are aspect `0x8009DF00`, horizontal `0x8009E09C`, vertical
`0x8009DFE8`, far horizontal/vertical `0x800A7824/28`; rotated corner axes
are `0x800C345C`, `0x801755F0`, `0x801A0760`. Original title storage is
`0x8009AB98` with the same 12-byte guarded text and explicit slot-one caller.
The sprite-bank pointer array is `0x80076ADC`; bank 21 is `0x80076B30`.
PAL prompt asset hashes need their own decoded-data proof before activation.

Original PAL dispatcher analysis now establishes scene `0x0604`: main table
`0x8009AB14` entry6 calls `0x80003410`, which dispatches substate table
`0x8009D100`; entry4 calls original field handler `0x80053DF8`. Its normal path
calls clock and simulation updates. The byte at `0x8013B452` selects the
simulation/UI bypass, logical phase is `0x8012DE27`, discrete camera mode is
`0x800C81A4`, and recorded-playback cursor is halfword `0x8012DDF0` over68
records. Full original hashes, hierarchical setter ABIs, camera ownership and
playback entry/return are documented in
[PAL scene and interpolation epochs](pal-scene-epochs.md).

This supports configuring the PAL observer and invalidating history at proven
original transitions. Actual visual acceptance across goals, pauses, camera
cuts and replay remains deferred. A PAL team-selection wrapper temporarily
writes substate4; main stage6 and the complete original dispatch route are
therefore part of the proof, rather than relying on substate4 alone.
