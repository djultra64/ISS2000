# ISS2000 runtime integration research

## Current barrier

The native original-entry diagnostic succeeds, but the resident map alone cannot generate a complete game. A direct call at `0x80000F10` targets `0x801B050C`, outside the initial resident text. There are 128 distinct external direct-call targets in the current candidate resident scan. Their load origin and lifetime are not yet established.

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
