# Attribution and dependency status

Original ISS2000 project work is credited to **djultra64**. Preserve authentic third-party authorship separately.

| Project | Role in this checkpoint | Upstream |
| --- | --- | --- |
| N64Recomp | Actual compiler and generated-code ABI headers, used from a separate pinned checkout | https://github.com/N64Recomp/N64Recomp |
| Rabbitizer / spimdisasm | Static analysis during ISS2000 research | https://github.com/Decompollaborate/rabbitizer / https://github.com/Decompollaborate/spimdisasm |
| N64ModernRuntime | Native game runtime, thread/queue/OS services; linked into the development game | https://github.com/N64Recomp/N64ModernRuntime |
| RT64 | Native renderer for original graphics tasks; linked into the development game | https://github.com/rt64/rt64 |

Pins are recorded in `config/dependencies.json`. Libraries retain their upstream licenses. Recompilation does not change ownership of the original game code or assets. No original ROM, asset set, generated game-code files or compiled game binary is included in the source checkpoint.
