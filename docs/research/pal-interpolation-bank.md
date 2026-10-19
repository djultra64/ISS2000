# PAL transform-task bank and raster extensions

Original project work: djultra64.

The render metadata bank probe follows the original F3DEX2 task until its first
verified perspective-matrix LOAD. Original PAL sky drawing emits the pinned
RT64 enable command followed by rectangle-aspect commands before that LOAD.
The earlier probe rejected opcode `64`, producing a valid task snapshot without
a matrix bank: both model and camera interpolation groups were consequently
empty, despite correct match scene `0604` and genuine fractional render weights.

The private field09 and career-field10 snapshots both have scene bytes `6/4/0`.
Their task roots `800D0328` and `800E0388` encounter `64000033` at `800D03B8`
and `800E0418` after exact `E0525464 / 10000064` enable. Following those two
known raster commands reaches the original perspective matrices `000C1AC0`
and `000C1B00`, independently identifying banks 0 and 1. This is a common
sky-prefix parsing defect rather than evidence of different Career model pools.
Private provenance is recorded in `.local/pal-interpolation-bank-01/proof.json`.

The parser now accepts only the current non-control extended raster commands:
rectangle aspect and scissor push/pop occupy one 64-bit slot; extended scissor
and rectangle alignment occupy two; texture rectangles occupy three. Exact
enable magic is required. Unknown hook changes, extension commands and reserved
parameter bits reject the task. Full payloads must fit RDRAM and count against
the existing command budget. Payload words are never decoded as commands.
Unknown branches, microcode changes and unsupported projections remain rejected.

The regression first reproduced rejection using the actual two saved task
streams and synthetic command payloads resembling matrix opcodes. The fixed
probe resolves both original banks without changing any of the 8 MiB snapshot.
This does not change graphics commands, guest matrices, simulation, render
weights, model allocation or camera continuity guards. Live model/camera group
counts and different intermediate GPU results still require visible acceptance.
