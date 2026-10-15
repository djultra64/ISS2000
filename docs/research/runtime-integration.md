# ISS2000 runtime integration research

## Current barrier

The native original-entry diagnostic succeeds, but the resident map alone cannot generate a complete game. A direct call at `0x80000F10` targets `0x801B050C`, outside the initial resident text. There are 128 distinct external direct-call targets in the current candidate resident scan. Four overlapping load origins at `0x801B00B0` have now been recovered statically; their full section boundaries and runtime lifetime are not yet established.

Do not conflate resident `.text`, resident initialized data, BSS, RSP programs and dynamically loaded CPU code. In particular, `ROM 0xA1200` does not show a simple executable continuation of the initial resident mapping. Extending one linear ROM-to-VRAM rule is unsupported.

## Reproduce the provisional map

Use the pinned spimdisasm checkout from `config/dependencies.json` and a compatible Rabbitizer Python package. These are upstream analysis tools. The actual research run used the pinned local spimdisasm and Rabbitizer 1.16.2. Supply their directories explicitly:

```sh
python3 -m tools.map_main \
  --rom .local/rom.z64 \
  --output .local/main-map \
  --spimdisasm "/path/to/pinned/spimdisasm" \
  --packages "/path/to/python/site-packages" \
  --recompiler .local/toolchain/N64Recomp \
  --source .local/deps/N64Recomp
```

The command returns the real recompiler exit code. For the current incomplete map, **exit 1 is the documented unresolved-call result**, not successful game generation. Inspect `summary.json` and `recompile.log`. Outputs remain private and a fresh output directory is required.

The scan assumes resident CPU text ends at ROM `0x69D80` and resident initialized memory ends at guest `0x800A0600`; these are research limits. Metadata output remains provisional. The 20 privileged functions are skipped only to inspect the remainder of the CPU translation; they have no fake runtime implementations.

## Next concrete steps

1. Trace the game's ROM/DMA and decompression routines leading to the external-call region. Establish exact ROM ranges, RAM destinations, copy/decode sizes and load lifetime for each executable block.
2. Map the corresponding code separately and register section identity with the native runtime. Distinguish reused RAM addresses from fixed sections.
3. Identify ISS2000's actual OS entry points from its own instructions and calling context, and connect real runtime implementations. Verify queues, thread scheduling, DMA, VI timing and save access.
4. Inventory RSP tasks actually submitted by the game. The F3DEX and F3DLX.Rej strings are leads; they are not a substitute for task evidence.
5. Follow the original memory-detection path that sets configuration byte `+0x12`. The current buffer diagnostic only controls that flag to verify both resulting branches.
6. Reach an authentic title/menu/match with audio and saves before validating enhancement profiles or physical rumble.

## Publication boundary

No GitHub repository or release has been created for this checkpoint. Own source commits use djultra64. The source archive excludes ROMs, generated original code, captured game assets/audio/images and native binaries.

## Static overlay evidence — 2026-10-15

The canonical working folder is `/home/alfredo/Documents/ChatGPT/ISS2000`.
The original diagnostic was rebuilt here after relocation: 22 Python checks
passed without skips, both CTest checks passed, and generated-file digests match
the earlier checkpoint. This remains a diagnostic, not game boot.

Four resident loader paths pass constant ROM source, guest destination and length
to `0x80003964`. All ranges below are half-open **initialized transfer ranges**;
they are not declarations that every transferred byte is executable text.

| Loader entry | DMA callsite | ROM range | Guest RAM range |
| --- | --- | --- | --- |
| `0x80002E4C` | `0x80002E80` | `0x2CB900..0x2D58A0` | `0x801B00B0..0x801BA050` |
| `0x80002FF0` | `0x8000301C` | `0x2D58A0..0x2D8500` | `0x801B00B0..0x801B2D10` |
| `0x80055A2C` | `0x80055A90` | `0x25D3D0..0x289BA0` | `0x801B00B0..0x801DC880` |
| `0x800574EC` | `0x8005753C` | `0x2E0D90..0x3166C0` | `0x801B00B0..0x801E59E0` |

The instruction slices include each call's delay slot, which computes the
transfer length. The wrapper forwards those values to `0x80003894`, submits
through `0x800580B0`, then waits through `0x8005D2C0` with mode argument 1 before
returning. Exact SDK identities still need confirmation from ISS2000 itself.
No decompression step has been identified on this particular transfer path.

For the first range, guest `0x801B050C` maps to ROM `0x2CBD5C`. It is a complete
function ending just before `0x801B05D4`: it saves incoming `a1` at `0x801BA050`,
conditionally calls `0x801B05D4` three times, and returns that pointer. This is
consistent with resident caller `0x80000F10`, which supplies the display-list
pointer from `0x800A09B0` and stores the return value there. The other three
ranges place data-like words or instruction interiors at the same guest PC.
This is strong static ownership evidence for this call, not proof of runtime
load order or a complete function map.

Startup clears `0x80168848` at `0x800008F8`; the call to `0x801B050C` is guarded
by that word equaling 1. State dispatch `0x800029B0` indexes the table at
`0x8009D40C` using configuration byte `+0x2E`. Its state-zero handler calls
`0x800574EC`; state-four and state-six handlers can call `0x80002E4C` on flagged
transitions. The guard's setter and the actual state/load sequence remain open.
The first translator error therefore does not establish the first executed
external call.

Private reproduction, from the canonical checkout:

```sh
python3 -B .local/overlay-research-20261015/recover_overlay.py \
  .local/rom.z64 .local/overlay-research-20261015/repeated-verification
```

The script checks the canonical ROM digest and reconstructs the four argument
triples directly from their instruction slices. Detailed original instruction
words and target evidence remain private alongside it. A second execution by
the primary agent reproduced all four ranges. This fixed-slice research script
is not a general control-flow analyzer.

## Runtime consequences checked in pinned upstream source

At the pinned N64ModernRuntime revision in `config/dependencies.json`,
`librecomp/src/pi.cpp` (`do_rom_read`, `do_dma`) copies ROM data and reports DMA
completion; it does not activate executable sections. `librecomp/src/recomp.cpp`
initializes the startup section through `load_overlays`, but subsequent game
loads need an explicit integration hook.

`librecomp/include/librecomp/overlays.hpp` exposes `register_overlays`,
`load_overlays` and `unload_overlays`; section/function records are defined in
`librecomp/include/librecomp/sections.h`. `load_overlay` in
`librecomp/src/overlays.cpp` replaces entries at matching guest addresses but
does not remove all unmatched functions from the previous section. Reused RAM
therefore requires explicit unloading at the correct lifetime boundary.

N64Recomp's `resolve_jal` in `src/recompilation.cpp` resolves same-section calls
directly, rejects missing functions, and uses runtime lookup for ambiguous
external section candidates. Distinct sections and verified load hooks are
required; broadening the resident section or deferring lookup alone cannot
supply missing executable bytes or establish which overlay is active.

Next: establish text/data/BSS boundaries, identify the guard's setter and all
relevant load/decode paths, then generate distinct section identities and verify
runtime load/unload/call traces. Real runtime services, graphics/audio task
submission, authentic title/menu and a controllable match remain unverified.

## Reproduced partial translation advance

A private expanded probe combines the existing 2,072 resident candidates with
8 candidates in the first alias. Its provisional CPU-text interval is guest
`0x801B00B0..0x801B0910`, corresponding to ROM `0x2CB900..0x2CC160`.
The terminal return at `0x801B08FC`, its delay slot, alignment padding, and a
referenced texture beginning at `0x801B0910` support that boundary. The final
candidate's extent includes the padding; this is still a provisional object map.

The combined 2,080-candidate map resolves `0x801B050C` and stops at the next
unmapped call: `0x80001060 -> 0x8023E684`, also in `func_80000D90`.
Putting the overlay section metadata first and selecting one output file per
function preserves eight successfully translated original C functions before
that resident failure. The primary agent reproduced both results using the
rebuilt compiler in the canonical folder. Both compiler invocations return 1,
which remains an incomplete translation, not a successful game build.

```sh
python3 -B .local/overlay-probe-20261015/probe.py \
  .local/overlay-probe-20261015/new-verification
```

The output directory must be fresh. The probe verifies the ROM and compiler
receipt and reads the pinned spimdisasm checkout and Rabbitizer 1.16.2 as noted
in its private report. It retains the existing 20 resident privileged-function
exclusions for translation exploration only. No original instruction was patched
and no unknown function was replaced with a success stub. The eight generated
functions were not compiled, linked or executed in a game runtime. Other aliases
at the same RAM base are not yet included.
