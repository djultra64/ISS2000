> This project was created with AI assistance. If that's not your cup of tea, feel free to move along.

# ISS2000 Recompiled

A community native PC port of **International Superstar Soccer 2000** for Nintendo 64, using static recompilation with [N64Recomp](https://github.com/N64Recomp/N64Recomp), [N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime), and [RT64](https://github.com/rt64/rt64).

**Version 0.7.1 — Linux and Windows x86-64.** Download the portable packages from [Releases](https://github.com/djultra64/ISS2000/releases/tag/v0.7.1). This is an early development release; see the [0.7.1 release record](docs/releases/0.7.1.md) for tested scenarios and remaining issues.

Independent fan project. Not affiliated with, sponsored by, or endorsed by Konami or Nintendo.

Project direction, original port work, and playtesting: **djultra64**.

**Status:** In development... SO-MANY-ALIGNMENT-ISSUES!

## Features

- Native execution of the PAL English game, including Career, training, and the original football modes.
- Original 4:3 or widescreen 16:9, with internal resolutions from the original size through 2160p.
- Original, 60, or 120 fps presentation limits, with interpolation separate from the game's simulation timing.
- In-game PC Settings using the original menu engine and artwork from your own ROM.
- Optional 2D bilinear filtering, independent of 3D texture filtering.
- Corrected enhanced-resolution sprite joins in Stadium Select, the scoreboard border, and End of 1st Half.
- Keyboard and four controller ports, with prompts for the active Xbox, PlayStation, Nintendo Switch, or keyboard layout.
- Original control types, an adapted eFootball-style Type 5, and a Free action layout in Edit Controller.
- Portable settings and saves, fullscreen, per-player vibration, and an Exit Game confirmation.
- Shared translucent projected shadows for players, officials, and the ball.
- Real historical player names in all 100 national teams and six combined teams, with [24 documented nearby-year exceptions](docs/research/pal-real-player-names.md).

## Requirements

- A legally obtained, user-supplied **Europe (English/German), revision 0** ROM. The game runs in English. Other regional revisions are not interchangeable with this build.
- An x86-64 Linux or Windows system with a Vulkan-capable GPU and current graphics drivers.
- The prepared Linux build requires GLIBC 2.38 and GLIBCXX 3.4.32 or newer; selected SDL and D-Bus libraries are bundled.
- For 120 fps presentation, suitable hardware and display settings. A selected frame limit is not a performance guarantee.

The supported canonical big-endian ROM has SHA-256:

```
6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf
```

## Download and play

1. Download the package for your operating system from [Releases](https://github.com/djultra64/ISS2000/releases).
2. Extract the complete folder to a writable location.
3. On Linux, run `launch.sh`. On Windows, run `iss2000.exe`.
4. At first launch, choose your own supported ROM. Keep the imported ROM private.

Configuration, imported private data, and saves remain beside the executable in `data/`. Back up that folder before changing versions. Release packages contain no ROM or pre-existing save data.

## Controls and options

Open **Option → PC Settings**. Graphics controls aspect ratio, resolution, frame limit, fullscreen, and **Filtering → 2D Original / 2D Bilinear**. Apply and save commits your changes; leaving without saving restores the saved preferences. Original filtering is the default.

The on-screen footer follows the active input device. Xbox and Nintendo face-button positions are treated separately. Controller-family selection can be set manually per player when automatic detection is ambiguous. Football action layouts are configured in **Edit Controller**; Type 5 is an ISS adaptation, not a claim that modern compound mechanics were added.

On the keyboard, the default menu controls include arrow keys, `Z` to select, `X` to go back, and `Enter` for Start. Follow the displayed shortcuts in PC Settings, where `X` applies and saves and `Escape` goes back. Main Select shows the Exit Game shortcut and asks for confirmation.

## Validation and known issues

Validation applies to the specific builds and scenarios recorded in the release notes and [acceptance record](docs/releases/1.0-acceptance.md). Version 0.7.1 is not an accepted 1.0 release. Full gameplay completion and physical testing of every controller family remain separate from automated checks.

Bilinear filtering softens the original artwork; some tiled menu plates can still show faint seams. Original filtering remains available and is the default.

Windows compiled successfully and rendered the original introduction during a hidden-desktop smoke test. Its window-close request did not complete in that test environment, so the disposable test was cancelled. Full interactive Windows gameplay, audio, and normal-exit acceptance remain pending.

Goal Kick announcement alignment, goal-replay effects, and some goal overlays still need broader visual review. Super-xBR remains a separate proposal; this release keeps Original as the default and retains the legacy Bilinear option. Do not interpret an interpolated-frame counter or a successful native build as proof that every game mode is correct.

## Build and contribute

Dependency revisions are pinned in [config/dependencies.json](config/dependencies.json). Original ROMs, extracted assets, generated original game source, private saves, and execution captures must remain outside the public source tree. See the [build notes](docs/building.md), [development journal](docs/development-history.md), and [native build inputs](docs/research/native-build-inputs.md) for the supported PAL build and verification workflow.

Run the automated suite with:

```
python3 -m unittest discover -s tests -v
```

Some integration tests require private, locally generated inputs and explicitly report a skip when those inputs are unavailable.

## AI Disclosure

I use **OpenAI Codex** to assist with research, reverse-engineering analysis, code implementation, debugging, tests, builds, packaging, and documentation. I direct that work, contribute code reviews and ideas for implementation, evaluate the game's behavior through hands-on testing, and decide which changes and releases to accept. Validation claims remain limited to the recorded builds and scenarios.

The original game and upstream tools remain the work of their respective creators. See [CREDITS.md](CREDITS.md).

## Legal and licensing

No original ROM, extracted game artwork, audio, models, or other original game data assets are distributed in the source repository or release packages. Original assets are read from the user's own verified ROM at runtime. No ROM download links are provided.

International Superstar Soccer, Konami, Nintendo, and related names and marks belong to their respective owners. This project does not grant rights to the original game, its assets, or its trademarks. Historical player-name references do not imply endorsement by any player, team, or association.

Original project code is licensed under **GPL-3.0-or-later**; upstream components retain their own licenses. See [LICENSE](LICENSE), [NOTICE](NOTICE), [CREDITS.md](CREDITS.md), and the notices included with each package. This software is provided without warranty.
