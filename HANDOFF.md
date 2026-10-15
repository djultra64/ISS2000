# Continue ISS2000 locally

Open this repository folder in local Codex:

`/home/alfredo/Documents/ChatGPT/ISS2000`

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

The compiler is built in `.local/toolchain`; source/dependency provenance is in its controlled-build receipt. Generation outputs `.local/boot` and `.local/boot-repeat` have matching file digests. The compiler source is now local at `.local/deps/N64Recomp`. Builds and generation were repeated in the canonical folder after relocation. Historical builds/receipts are retained in `.local/pre-relocation-20261015/`; their absolute paths describe the old location and must not be edited as if they were new evidence.

## Resume prompt

> Continue ISS2000 on the current codex/m0-native-bootstrap branch. Read AGENTS.md, README.md, docs/milestones/M0.md and docs/research/runtime-integration.md, then inspect Git and existing private evidence before changing anything. Preserve the working diagnostic and existing tests. The user's approved targets are faithful native N64 recompilation, proper 16:9, up to 4K, 120 fps through interpolation without accelerating simulation, Expansion Pak / 8 MiB and per-port rumble. Other recomps are only workflow references: do not actively compare their game binaries. Analyze ISS2000 directly. The current resident mapping has 2,072 candidate functions and 128 external direct-call targets. The resident-only N64Recomp probe stops at call 0x80000F10 -> 0x801B050C. A reproduced partial map adds eight overlay functions (2,080 total candidates) and now stops at call 0x80001060 -> 0x8023E684. These eight functions translate to C but have not been executed. Four static DMA aliases at RAM 0x801B00B0 are documented in docs/research/runtime-integration.md; the strongest owner for target 0x801B050C is ROM 0x2CBD5C in block 0x2CB900..0x2D58A0. Establish text/data/BSS boundaries and trace the guard at 0x80168848 plus load/unload lifetime, then integrate real runtime services and work toward an authentic title screen and controllable match. Do not replace unknown functions with silent success stubs. Keep ROMs, generated original code, assets and captures private. Use djultra64 for own commits. No enhanced rendering, full Expansion Pak detection, rumble delivery or Windows build is verified yet.

## Canonical-folder relocation

The active repository, original ZIP, private ROM, toolchain source, generated code
and rebuilt diagnostic now live in the canonical folder above. The former
`Documents/Codex/2026-10-15/new-chat/work/ISS2000` path is a compatibility symlink
to this folder. Its complete previous checkout is preserved privately under
`.local/pre-relocation-20261015/previous-worktree/`. Do not resume that archived copy.

Relocation verification: 22 Python tests passed without skips, 2 CTest checks
passed, and both new generation receipts match the previous generated-source
digests. The ROM digest is unchanged.

## Portable copy

The public-source-only snapshot is sufficient to retain original project work, tests and documentation; rebuilding requires your private ROM and the pinned upstream tools. The existing local folder additionally contains private generated sources, native binaries and execution evidence under `.local/`. No GitHub publication was performed.
