# Continue ISS2000 locally

Open this repository folder in local Codex:

`/var/home/alfredo/Documents/Codex/2026-10-15/new-chat/work/ISS2000`

Active branch: `codex/m0-native-bootstrap`. Start with `git status --short`, read `AGENTS.md`, `README.md`, `docs/milestones/M0.md` and `docs/research/runtime-integration.md`.

## Verified checkpoint

The supplied USA English/Spanish ROM is imported privately at `.local/rom.z64`. The original archive remains untouched in `/var/home/alfredo/Documents/ChatGPT/ISS2000/`.

`.local/clean-native-build/iss2000-diagnostic` executes original recompiled entry and buffer-selection code. It verifies BSS, stack, continuation and the original normal/expanded buffer addresses in 8 MiB of host-backed RDRAM. It deliberately stops before game initialization. The game is not playable yet.

The latest verification command is:

```sh
ISS2000_DIAGNOSTIC=.local/clean-native-build/iss2000-diagnostic python3 -m unittest discover -s tests -v
ctest --test-dir .local/clean-native-build --output-on-failure
```

Expected: 22 Python tests, no skips with the variable set, and 2 CTest checks passing.

The compiler is built in `.local/toolchain`; source/dependency provenance is in its controlled-build receipt. Generation outputs `.local/boot` and `.local/boot-repeat` have matching file digests. The already-configured CMake build records the read-only upstream compiler checkout location; README describes standalone upstream setup when rebuilding elsewhere.

## Resume prompt

> Continue ISS2000 on the current codex/m0-native-bootstrap branch. Read AGENTS.md, README.md, docs/milestones/M0.md and docs/research/runtime-integration.md, then inspect Git and existing private evidence before changing anything. Preserve the working diagnostic and existing tests. The user's approved targets are faithful native N64 recompilation, proper 16:9, up to 4K, 120 fps through interpolation without accelerating simulation, Expansion Pak / 8 MiB and per-port rumble. Other recomps are only workflow references: do not actively compare their game binaries. Analyze ISS2000 directly. The current resident mapping has 2,072 candidate functions and 128 external direct-call targets. Full N64Recomp translation stops at a call from 0x80000F10 in func_80000D90 to 0x801B050C. Recover the game's executable-block load/decompression/overlay map, then integrate real runtime services and work toward an authentic title screen and controllable match. Do not replace unknown functions with silent success stubs. Keep ROMs, generated original code, assets and captures private. Use djultra64 for own commits. No enhanced rendering, full Expansion Pak detection, rumble delivery or Windows build is verified yet.

## Portable copy

The public-source-only snapshot is sufficient to retain original project work, tests and documentation; rebuilding requires your private ROM and the pinned upstream tools. The existing local folder additionally contains private generated sources, native binaries and execution evidence under `.local/`. No GitHub publication was performed.
