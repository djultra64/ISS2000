# Credits and licensing

Original ISS2000 project work is credited to **djultra64**. Preserve authentic third-party authorship separately.

| Project | Role | Upstream |
| --- | --- | --- |
| N64Recomp | Actual compiler and generated-code ABI headers, used from a separate pinned checkout | https://github.com/N64Recomp/N64Recomp |
| Rabbitizer / spimdisasm | Static analysis during ISS2000 research | https://github.com/Decompollaborate/rabbitizer / https://github.com/Decompollaborate/spimdisasm |
| N64ModernRuntime | Native game runtime, thread/queue/OS services; linked into the development game | https://github.com/N64Recomp/N64ModernRuntime |
| RT64 | Native renderer for original graphics tasks; linked into the development game | https://github.com/rt64/rt64 |
| greatdocbrown | Retro controller prompt artwork, CC0; adapted to original sprite palettes | https://greatdocbrown.itch.io/gamepad-ui |

Pins are recorded in `config/dependencies.json`. Libraries retain their upstream licenses. Recompilation does not change ownership of the original game code or assets. No original ROM, asset set, generated game-code files or compiled game binary is included in the source checkpoint.

## Original game

International Superstar Soccer 2000 was developed by Konami Computer
Entertainment Osaka and published by Konami. The game, its artwork, audio,
models, player likenesses, and trademarks remain the work and property of
their respective creators and rights holders. Nintendo owns its respective
platform names and trademarks. This independent project claims no ownership
of those works and distributes no original ROM or extracted game assets.

## Project code and AI assistance

Project direction, original port work, and playtesting: **djultra64**.
Original project code is GPL-3.0-or-later; see LICENSE and NOTICE.
OpenAI Codex assisted with research, implementation, debugging, tests, builds,
packaging, and documentation under the project author's direction. See the
AI Disclosure in README.md for the scope of that assistance.

Authentic upstream author names and required copyright and license notices
are preserved in licenses/ and in each portable package.
