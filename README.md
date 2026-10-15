# International Superstar Soccer 2000 — native recompilation

Original project work: **djultra64**. Work in progress: **native entry and buffer-profile diagnostics**, not a playable game.

The target is the original USA English/Spanish N64 game, with proper 16:9, rendering up to 4K, interpolated presentation up to 120 fps, guest Expansion Pak memory and controller rumble. These enhancements are not yet implemented in a running game. The diagnostic allocates 8 MiB and executes the original standard/expanded buffer-selection routine; automatic Expansion Pak detection is not yet integrated.

## Current results

- Deterministic normalization of big-endian, byte-swapped and little-endian ROM images, including ZIP import. Exact supported revision checking; no overwriting existing files.
- Controlled build of the pinned N64Recomp with artifact receipts checked before generation.
- Original entry function and buffer setup translated into native C and executed on the host. BSS clearing, surrounding memory, stack, dispatch boundary, and standard/expanded buffer choices are verified.
- Resident-code research finds 2,072 candidate functions. Four overlapping DMA load ranges are recovered; a partial 2,080-candidate map adds eight overlay functions, resolves `0x801B050C` and stops at `0x8023E684`. The full load map and runtime lifetimes remain unresolved. No unknown OS routine is silently treated as successful.

See [M0 evidence and limitations](docs/milestones/M0.md) and [runtime research](docs/research/runtime-integration.md).

## Local working folder

The canonical checkout is `/home/alfredo/Documents/ChatGPT/ISS2000` (the system
also resolves it as `/var/home/alfredo/Documents/ChatGPT/ISS2000`). The original ZIP,
private ROM, compiler source and rebuilt diagnostic are retained here. Previous
build caches and receipts are historical evidence under ignored
`.local/pre-relocation-20261015/`; use the fresh `.local/toolchain` and
`.local/clean-native-build` directories for current work.

## Private inputs

Supply your own USA revision 0 ROM. Canonical SHA-256:

`e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`

ROMs, original assets, generated game code and binaries are not distributed in this source checkpoint. Keep them under ignored `.local/`. Other recomp projects are workflow references, not comparison targets.

## Reproduce the diagnostic on Linux

Requires Python 3.11 or newer, CMake 3.20 or newer, Ninja and a C/C++ compiler with C++20 support. Verified here with Python 3.14 and GCC 15.2.1. The following commands run from the repository root. Paths with spaces must stay quoted. No Python packages are required for the core importer/generator/tests.

Prepare the upstream compiler checkout from `config/dependencies.json`. It is a separate upstream tool, not another game's codebase:

```sh
git clone --recursive https://github.com/N64Recomp/N64Recomp .local/deps/N64Recomp
git -C .local/deps/N64Recomp checkout ffb39cdad1da5de07eaaa48bd1db4a89a7986771
git -C .local/deps/N64Recomp submodule update --init --recursive
python3 -m tools.build_tool --source .local/deps/N64Recomp --build .local/toolchain
```

A preexisting read-only upstream checkout at that exact revision can also be supplied to `--source`. It must have clean, initialized submodules. Tool build logs stay in the private build folder. A build receipt binds the observed source revision and paths to the produced binary/cache/build-graph digests; it is a local build record, not a cryptographic signature or third-party attestation.

```sh
python3 -m tools.rom "/path/to/International Superstar Soccer 2000 (USA) (En,Es).zip" --output .local/rom.z64
python3 -m tools.recompile --rom .local/rom.z64 --output .local/boot --recompiler .local/toolchain/N64Recomp --source .local/deps/N64Recomp
cmake -S . -B .local/native-build -G Ninja -DCMAKE_BUILD_TYPE=Release -DISS2000_N64RECOMP_SOURCE="$PWD/.local/deps/N64Recomp"
cmake --build .local/native-build
.local/native-build/iss2000-diagnostic
ctest --test-dir .local/native-build --output-on-failure
ISS2000_DIAGNOSTIC=.local/native-build/iss2000-diagnostic python3 -m unittest discover -s tests -v
```

The result explicitly says `game_booted: false`. The continuation at `0x800007B8` is an observed stop boundary, not a substitute for OS initialization. Buffer testing explicitly sets the game's configuration flag before calling its original function; it does not claim OS memory detection is working.

The importer and generator deliberately require fresh output paths. To repeat generation, use a new `.local/boot-2` directory and select its `functions` folder with `-DISS2000_GENERATED`. Compare `generated_files` in the two receipts. Do not delete inputs or other projects to satisfy a fresh-output check.

Run `python3 -m unittest discover -s tests -v` for unit checks without private inputs. Native tests are then explicitly skipped, not counted as verified. Windows execution is not yet tested.

## AI disclosure

AI tools assisted research, implementation, testing and documentation under djultra64's direction. Independent code review identified a build-provenance weakness and a corrupt-ZIP error path; both have regression checks. The evidence record distinguishes observed behavior from unimplemented targets.

## Faced challenges

The original supplied ROM uses byte-swapped order despite its `.n64` suffix. Resident code references addresses outside the initial code map, so translating the initial block is insufficient. CPU and RSP code must also be separated correctly. Host memory macros require sign-extended guest addresses, a boundary checked by the native integration test.

## Attribution

International Superstar Soccer 2000 and its original code/assets belong to their original creators and rightsholders, including Konami. This project is unofficial and unaffiliated. Thanks to the authors and contributors of [N64Recomp](https://github.com/N64Recomp/N64Recomp), [N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime), [RT64](https://github.com/rt64/rt64), [spimdisasm](https://github.com/Decompollaborate/spimdisasm), and [Rabbitizer](https://github.com/Decompollaborate/rabbitizer). See [CREDITS.md](CREDITS.md). Upstream code is not vendored in this checkpoint; preserve all upstream notices when integrating it.
