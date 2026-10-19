# Historical development journal

This is the pre-0.7 local development README, preserved as historical evidence.
The root README and current release notes describe the public release. Old
freezes, candidate paths, and acceptance statements below are not current policy.

---

# International Superstar Soccer 2000 — native recompilation

Original project work: **djultra64**. **PAL English native port; release acceptance reopened for corrections.** The existing portable folders named 1.0.0 contain the older source44 checkpoint and do not include the current corrections.

The active base is Europe English/German revision0, running in English to retain Career. Targets are proper16:9,720p–4K rendering, interpolated120fps and original simulation/animation timing. The preserved USA work remains a historical diagnostic reference; regional addresses and saves are not interchangeable.

## Current results

- Native PAL English execution reaches the original menus, controllable matches, pause/replay and Career. The exact r56 production package loads genuine Career data, advances September week2 to3, saves through the original UI and reloads week3 in a fresh process. Current Training/control coverage and remaining mode checks are recorded separately.
- Historical audio timing correction (not current continuity acceptance): progress the two-slot AI FIFO continuously at its actual DAC frequency, rather than SDL device batch sizes. An actual default-PipeWire Linux run accepted947 DMAs without rejection;908999 active stereo output frames matched exactly. A302-frame intentional shutdown tail is excluded explicitly. See [audio evidence](docs/research/audio-ai-clock.md).
- Animation correction: omit both the duplicate High simulation update and its paired skeletal update. Actual High Training records126 stage/actor/ball/pose changes in about5.047s in both idle and running windows, matching the same-ROM Ares Low reference. Actual renderer callbacks establish stable IDs and interpolation for all19 articulated records across changing poses; physical120Hz scanout remains unverified.
- PC Settings uses the original engine. Its Options-row label now copies original CI4 word pixels at unit scale, verified in actual GPU captures; the new green pages use original menu art. Fullscreen application moved to the main SDL thread. The exact r57 full game under private KWin confirms actual fullscreen enter/exit, native Save and cold-restart restoration; Gamescope does not acknowledge that flag. See docs/research/native-fullscreen.md.
- Saving and vibration are independent. English save text uses game/data terminology; automatic storage probing bypasses insertion waits while keeping real errors and existing data. Actual source48 starts directly at Save Game and completes a genuine save in a private copy. All57 obsolete English text occurrences fall within43 guarded message profiles.
- Controls redesign now uses the supplied primary PS1 recordings: retain four original types, add an adapted current eFootball Type 5, then Free. Adapt the authentic pre-match/Training Edit Controller screen, with football actions and active-device glyphs; Start confirms Free. The former manual wait and Type 4 Modern proposal are superseded. Six-choice logic and persistence have focused CPU coverage. Current hidden Training runs exercise all four variants, Types1–5 and a saved/reopened Free binding; physical-controller behavior remains unverified.
- Earlier actual GPU evidence covers720p through2160p targets, widescreen sky/backgrounds, sprite alignment and player-name panels. New correction acceptance is separate from the older source44 package audit.
- Windows compilation and execution are frozen until the user gives further notice. Existing Linux/Windows packages and user saves are preserved.

See the [1.0 acceptance record](docs/releases/1.0-acceptance.md) and [current handoff](HANDOFF.md) for the latest evidence. The [M0 milestone](docs/milestones/M0.md) and earlier US research describe historical checkpoints.

## Portable builds

Latest Linux correction candidate: `portable/ISS2000-Linux-20261018-r70`.
Run `launch.sh`; first launch asks for the supported English PAL ROM. Configuration
and saves remain portable. The package includes no ROM or saved data.

r70 moves Euro Cup/Penalties right by 5% and Scenario/Training/Option by 10%,
with their lamps and selected labels. Ball, referee and assistant shadows share
the players' translucent projected style. The final suite passed 512 tests with
3 historical diagnostic skips; a private day/clear field and menu review closed
normally. See the [r70 evidence](docs/research/pal-r70-menu-and-shadow-style.md).

r69 moves only Pre-season Match and its lamp right together by the requested
10% of their previous leading-edge position. The rest of the menu retains r68
placement. Focused original-CPU verification and actual private menu review pass.

r68 adds a small row-specific left inset to the nine Main Select items,
following the ball more closely. The heading, row backgrounds and Exit Game
retain their positions. Focused original-CPU verification and an actual hidden
menu review passed; see the latest [handoff](HANDOFF.md).

r67 corrects Main Select's animated indicators and selected-label placement.
The ball, heading and option text follow the physical left edge, while the
rectangular row backgrounds retain their positions. Exit Game is larger and
heavier. The layout and exit prompt survive returning from Option. The exact
package's return, cancel and confirmed normal exit are verified in a private
compositor. See the [menu correction evidence](docs/research/pal-main-select-r67.md)
for the general-suite and final focused-test scopes.


r64 shortens the first automatic save/loading waits, adds an original-engine
Exit Game footer below the raised Main Select rows, preserves adapted title and
controller text through transitions, fits saved-data text and removes redundant
RS lettering. Player shadows use simplified projected pose geometry. It also
fixes a reproduced completion-ring wrap on second-half entry. The exact package
completed one friendly match. The full suite passed 511 of 514 tests, with three
historical NTSC diagnostics skipped (542.216 seconds). Goal-replay trail and
goal-overlay entrance corrections remain pending. See the
[current correction evidence](docs/research/pal-r63-ui-and-shadows.md).

The following r58–r62 results are historical and retain their original scope.

This candidate preserves the maximum-detail players, expanded matrix banks,
radar corrections and stick response. The framebuffer ownership correction added
in r58 addresses a reproduced natural-halftime starvation. Exact r58 completed one
full friendly including golden-goal extra time and began a second; it retained
3234.368 seconds of consecutive audio unchanged with zero interior insertions.
Initial silence and shutdown tails are documented separately; original source
saturation remains. These are r58 results, not sustained acceptance of r62.

r59 corrects explicit Formation Save taking a RAM-only path. The exact portable
writes through the original storage worker; normal cold restarts load the saved
formation, including after Save → Load → global Save Game. See the
[formation persistence evidence](docs/research/pal-formation-persistence.md).
r60 additionally serializes native VI state publication and framebuffer getters
with the existing SDK mutex, after a deterministic regression proved a pending
swap could be overwritten. Two normal r59 fresh Training starts froze; r60 runtime
validation remains in progress. See the [VI race evidence](docs/research/pal-vi-state-publication.md).
r62 extends the guarded original-font adapters to all six set-play help variants,
the replay diagrams/Cancel prompt and Handicap L/Z–R footer. Set-play button names
also follow the actual Type1–5/Free map. See the
[control prompt correction](docs/research/pal-remaining-control-prompts.md).
The full r62 suite passed507 of510 tests, with3 historical NTSC diagnostics skipped (445.732 seconds). Verification is recorded in
[acceptance](docs/releases/1.0-acceptance.md) and [HANDOFF](HANDOFF.md).

The user owns the remaining functional acceptance, including match transitions,
modes, physical controllers and sustained performance/audio. This is **not an
accepted1.0 release**. Earlier actual120Hz private-compositor captures contain
intermediate leg contours at a fixed original pose phase; that bounded r60 result
does not establish complete r62 presentation coverage or physical scanout.
The launcher appends troubleshooting details to `data/runtime.log`.

The preserved folders are `portable/ISS2000-1.0.0-Linux` and
`portable/ISS2000-1.0.0-Windows`; they predate the active correction pass.
The older `ISS2000-1.0-Linux` user-tested folder is preserved as well.
Run `launch.sh` on Linux or `iss2000.exe` on Windows. First launch asks for the
supported PAL ROM; configuration and saves stay beside the executable.

Open **Option → PC Settings** for the PC output settings. Alt+Enter toggles
fullscreen for the current session; use Save options to persist it. The game's internal
resolution defaults to High; PC output resolution is separate. The corrected candidate requires manual visual, audio and Training-load
acceptance before a new1.0 claim. Development captures and binaries are private
under `.local/`.

The Linux binaries require a recent x86-64 system with GLIBC 2.38 and
GLIBCXX 3.4.32 or newer; selected SDL/D-Bus libraries are bundled. Windows ships
its selected SDL, shader compiler and Visual C++ runtime dependencies. Actual
Windows acceptance used the project's Windows machine; it does not establish
compatibility with every GPU or older operating system. Remaining user-manual
mode/controller coverage is recorded in the acceptance document.

## Native execution model

Original MIPS CPU instructions are translated to C and compiled for the PC. The CPU does not interpret MIPS instructions at runtime. The original loader still requests cartridge ranges for resources and overlay data; their executable counterparts are already native functions selected by the active-load registry. Reading cartridge bytes is data access, not CPU emulation.

The current importer stores a canonical ROM as the private resource container. Separate texture/model/audio extraction is not implemented. First launch asks for the user’s own ROM; no original assets are included in the source package.

## Local working folder

The canonical checkout is `/var/home/alfredo/Documents/ChatGPT/ISS2000`; the system also resolves `/home/alfredo/Documents/ChatGPT/ISS2000` to it. Prefer the actual `/var/home` path for importer/build provenance checks. Private PAL code and metadata are under `.local/pal-map-bound-01` and `.local/pal-native-metadata-04`; the current Linux development game build is `.local/pal-game-build`. Ignored historical US builds and receipts remain preserved.

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

See [PAL code mapping](docs/research/pal-code-map.md), [runtime lookup/build requirements](docs/runtime-lookup-bridge.md) and `HANDOFF.md` before preparing a fresh configuration. A successful link or unit suite does not replace actual gameplay acceptance. The portable production binaries disable input fixtures and render-evidence instrumentation; see the separate final-package acceptance record.

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

Run `python3 -m unittest discover -s tests -v` for unit checks without private inputs. Native tests are then explicitly skipped, not counted as verified. This historical US diagnostic is separate from the tested PAL Windows portable build.

## AI disclosure

AI tools assisted research, implementation, testing and documentation under djultra64's direction. Independent code review identified a build-provenance weakness and a corrupt-ZIP error path; both have regression checks. The evidence record distinguishes observed behavior from unimplemented targets.

## Research and remaining validation

Both supplied regional inputs required byte-order normalization. Their resident/overlay maps, host-service boundaries, timekeeping and save identities were recovered separately. Original PAL simulation keeps its regional timestep compensation, while presentation settings remain separate; see [simulation pace](docs/research/pal-simulation-pace.md) and [match-clock evidence](docs/research/pal-match-clock.md). The [Career acceptance route](docs/research/pal-career-acceptance.md) records the genuine tested menu/save/restart path. No RAM-forced progression or invented save data counts as acceptance.

## Attribution

International Superstar Soccer 2000 and its original code/assets belong to their original creators and rightsholders, including Konami. This project is unofficial and unaffiliated. Thanks to the authors and contributors of [N64Recomp](https://github.com/N64Recomp/N64Recomp), [N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime), [RT64](https://github.com/rt64/rt64), [spimdisasm](https://github.com/Decompollaborate/spimdisasm), and [Rabbitizer](https://github.com/Decompollaborate/rabbitizer). See [CREDITS.md](CREDITS.md). Upstream code is not vendored in this checkpoint; preserve all upstream notices when integrating it.
