# International Superstar Soccer 2000 — native recompilation

Original project work: **djultra64**. Work in progress: **PAL English native port**; release 1.0 is not complete.

The active base is the original Europe English/German revision 0, running in English, to retain its original Career mode. The goals are proper 16:9, resolution options from 720p to 4K, interpolated presentation up to 120 fps, 8 MiB Expansion Pak memory, rumble and remapping by logical action. The preserved USA English/Spanish work is a historical diagnostic reference; its addresses and saves are not interchangeable with PAL.

## Current results

- Visible Linux PAL runs reach the original introduction, nine-entry main menu including Career, a controllable match, pause, replay and natural halftime. A completed match and Career progression/save-and-reload acceptance remain pending.
- Original PAL CPU code is compiled into 12,170 native function bodies, with 67 registered CPU sections, 54 reviewed host-service bindings and the retained original Pak routine. Active overlay selection follows original loads; unknown calls remain fatal.
- Full-width 16:9 sky, clean ball/arrow sprites and clean KICK OFF/player-name sprites have visible evidence in captures 110, 113 and 114. Later HUD alignment and final original-engine Remap composition fixes compile but still need visible acceptance. There is no independent controls overlay.
- Logical actions, Xbox/PlayStation/Nintendo family handling, per-port preferences and persistent Controller Paks are implemented. Real controller prompts/actions and rumble still need hardware checks. Original Pak creation/reopening is observed; that does not establish a saved Career change surviving restart.
- The last complete configured integration suite passed **283 tests, zero skips**, before the latest HUD/glyph changes. Later focused checks passed **7 HUD/remap/VI tests and 15 glyph tests**. These counts describe separate runs, not a newer complete-suite result.
- ROM import checks exact identity and preserves existing files. Portable build/package preparation and the direct function-lookup bridge exist; final packages and actual Windows compilation/execution remain unverified. Actual 120 Hz presentation, fractional gameplay interpolation and all requested output resolutions still require acceptance.

See the [1.0 acceptance record](docs/releases/1.0-acceptance.md) and [current handoff](HANDOFF.md) for the latest evidence. The [M0 milestone](docs/milestones/M0.md) and earlier US research describe historical checkpoints.

## Native execution model

Original MIPS CPU instructions are translated to C and compiled for the PC. The CPU does not interpret MIPS instructions at runtime. The original loader still requests cartridge ranges for resources and overlay data; their executable counterparts are already native functions selected by the active-load registry. Reading cartridge bytes is data access, not CPU emulation.

The current importer stores a canonical ROM as the private resource container. Separate texture/model/audio extraction is not implemented. First launch asks for the user’s own ROM; no original assets are included in the source package.

## Local working folder

The canonical checkout is `/var/home/alfredo/Documents/ChatGPT/ISS2000`; the system also resolves `/home/alfredo/Documents/ChatGPT/ISS2000` to it. Prefer the actual `/var/home` path for importer/build provenance checks. Private PAL code and metadata are under `.local/pal-map-bound-01` and `.local/pal-native-metadata-02`; the current Linux development game build is `.local/pal-game-build`. Ignored historical US builds and receipts remain preserved.

## Private inputs

Supply your own **Europe English/German revision 0** ROM, cartridge identifier `NISX`, 16,777,216 canonical bytes. The active English profile is `iss2000-pal-en-de-rev0`, with canonical SHA-256:

`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`

The development input is `.local/inputs/pal-en-de/rom.z64`. Audit an existing input with the explicit profile:

```sh
python3 -m tools.rom "/path/to/your PAL ROM or ZIP" --revision iss2000-pal-en-de-rev0
```

To import, add `--output` with a fresh destination. The command refuses existing outputs. The low-level importer's omitted-profile default remains US for backward compatibility; pass the PAL profile explicitly. The native game build defaults to the PAL profile and verifies that its map and metadata describe the same exact ROM.

The preserved US revision 0 input is `.local/rom.z64`, cartridge identifier `NISE`, SHA-256 `e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`. Keep regional ROMs and saves separate; no automatic conversion is implemented. The attached PAL edition is English/German; Spanish support is not inherited from US.

ROMs, extracted assets, generated original code, binaries, saves and captures are private and are not distributed in the source checkpoint. Other recomp projects are workflow references, not comparison targets. Future selectable roster/team/flag/kit packs remain a [proposal](docs/research/roster-pack-plan.md); no pack loader or selector is implemented.

## Current PAL development build

The native game requires independently prepared pinned runtime/RT64 archives, original audio code, PAL CPU sources and matching metadata. These are private prerequisites, not included with this repository. In an already configured development checkout, build the game with:

```sh
cmake --build .local/pal-game-build --target iss2000 -j4
```

See [PAL code mapping](docs/research/pal-code-map.md), [runtime lookup/build requirements](docs/runtime-lookup-bridge.md) and `HANDOFF.md` before preparing a fresh configuration. A successful link or unit suite does not replace visible gameplay acceptance. Disable input fixtures and render-evidence instrumentation for final binaries; no final package is approved by this checkpoint.

## Historical US boot diagnostic on Linux

This section preserves the early **US-only** bootstrap reproduction. It does not generate the current PAL game or describe its acceptance status.

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

## Research and remaining validation

Both supplied regional inputs required byte-order normalization. Their resident/overlay maps, host-service boundaries, timekeeping and save identities were recovered separately. Original PAL simulation keeps its regional timestep compensation, while presentation settings remain separate; see [simulation pace](docs/research/pal-simulation-pace.md) and [match-clock evidence](docs/research/pal-match-clock.md). The [Career acceptance route](docs/research/pal-career-acceptance.md) records the genuine menu/save path still to be tested. No RAM-forced progression or invented save data counts as acceptance.

## Attribution

International Superstar Soccer 2000 and its original code/assets belong to their original creators and rightsholders, including Konami. This project is unofficial and unaffiliated. Thanks to the authors and contributors of [N64Recomp](https://github.com/N64Recomp/N64Recomp), [N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime), [RT64](https://github.com/rt64/rt64), [spimdisasm](https://github.com/Decompollaborate/spimdisasm), and [Rabbitizer](https://github.com/Decompollaborate/rabbitizer). See [CREDITS.md](CREDITS.md). Upstream code is not vendored in this checkpoint; preserve all upstream notices when integrating it.
