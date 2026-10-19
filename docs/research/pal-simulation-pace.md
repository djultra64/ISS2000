# PAL original compensation and NTSC match pace

Original project work: djultra64. Static checkpoint: 2026-10-15.

The user requires match speed to agree with NTSC. Original PAL ISS2000 already
contains explicit 50-Hz compensation in player speed, acceleration, ball
physics and timers. Running that compensated code at 60 VI/s or applying a
blanket 1.2 speed multiplier would accelerate it again. Keep the PAL VI/audio
clock and original motion coefficients while verifying the remaining clock
rounding and update gates. Exact measured NTSC equivalence remains pending
because matched-state NTSC/PAL gameplay wall-time acceptance is not complete.

The evidence below compares only the authorized original ISS2000 US and PAL
inputs. It changes neither ROM. Private `.local/pal-runtime-01/pace-proof.json`
pins complete selected function bodies, all changed constants and readonly data
locations. `audit_pace.py` checks those original bytes and coefficient algebra;
it does not execute game code. A broader relaxed-immediate search identified
candidate differences, which were then reviewed individually. That broad search
is discovery material, not an automatic semantic mapping or completeness proof.

## Player speed and acceleration

The shared gameplay section is US ROM `0x389970 -> 0x802B9EC0`, PAL ROM
`0x386080 -> 0x802B57E0`. In original player-parameter initialization,
US `0x802CD568` corresponds to PAL `0x802C9184` (348 bytes). Its complete
instruction/register/structure shape is preserved; only relocated references
and reviewed inline constants differ. It reads the player attribute pointer at
record `+0xB0`, speed attribute `+0x23`, acceleration attribute `+0x24`, and writes
speed limits to `+0x10/+0x14/+0x18` and acceleration to `+0x28`.

| Original coefficient | US | PAL | PAL / US |
| --- | --- | --- | --- |
| First speed slope, readonly double | 0.00666666712 | 0.00799999918 | approximately 1.2 |
| Second speed slope, readonly double | 0.00523809478 | 0.00628571283 | approximately 1.2 |
| Speed base, readonly double | 2.29999995 | 2.76000023 | approximately 1.2 |
| Speed offset, inline float | 0.200000003 | 0.240000010 | approximately 1.2 |
| Acceleration slope, inline float | 0.00100000005 | 0.00144000014 | approximately 1.44 |
| Acceleration base, inline float | 0.00999999978 | 0.01440000068 | approximately 1.44 |
| Additional time factor | 1.71428573 | 1.42857146 | approximately 5/6 |

The readonly coefficients are US `0x802DB5E8/F0/F8` (ROM
`0x3AB098/A0/A8`) versus PAL `0x802D7228/30/38` (ROM
`0x3A7AC8/D0/D8`). PAL inline speed/acceleration construction occurs at
`0x802C91DC`, `0x802C91EC`, `0x802C9234`, `0x802C924C` and
`0x802C9288`.

Original speed update PAL `0x802C8B3C` (US `0x802CCF2C`, 424 bytes) consumes
these fields, changes speed `+0x0C` through acceleration `+0x28` and clamps to
limits. Its corresponding inline reductions are likewise scaled, for example
US `0.03` becomes PAL `0.036`. The speed/heading converter PAL `0x802C87E0`
(US `0x802CCBD0`, 104 bytes) stores heading `+0x38`, computes sine/cosine and
writes horizontal components `+0x34/+0x2C`. This is original movement dataflow,
not a UI timing constant.

For corresponding 50/60 (or 25/30) update rates, a velocity multiplied by 1.2
preserves distance per second: `50 × 1.2 = 60`. A per-update velocity increment
multiplied by 1.44 preserves acceleration because velocity itself is represented
per update: `(50/60)² × 1.44 = 1`. The bounded affine coefficient audit checks
all 256 attribute values for both slopes; relative linear-rate disagreement is
below `3e-7`, attributable to original floating constants. This algebra is not a
measurement of every player action, AI decision or animation in a running game.

## Ball vertical integration and damping

The original special record at PAL `0x800C19AC` has position components at
`+0/+4/+8`, vertical velocity at `+0x18` (`0x800C19C4`) and gravity at `+0x2C`
(`0x800C19D8`). PAL dispatch wrapper `0x802B6EC4` (US `0x802BB550`) explicitly
compares the input record with `0x800C19AC` before calling its vertical step.

PAL vertical step `0x802B6D60` (US `0x802BB3F0`) adds vertical velocity to
height and subtracts gravity from velocity at `0x802B6DC0..0x802B6DE8`, followed
by original ground/contact handling. The update arithmetic is unchanged.
A later threshold changes from 2.0 to 2.4; constructing that float adds one
instruction and shifts two branch displacements, so these particular function
bodies are semantically compared rather than claimed byte-identical.

Default reset PAL `0x802BBEE4` (US `0x802C0574`, 316 bytes) initializes:

| Original field | US | PAL | PAL / US |
| --- | --- | --- | --- |
| Gravity `+0x2C` | 0.11111111194 | 0.16000001132 | approximately 1.44 |
| Damping `+0x30` | 0.01666666009 | 0.01999999210 | 1.2 |

PAL stores these at `0x802BBF5C/60`; original `0x802BBF70` then performs the
explicit special-ball pointer comparison. The same compensation also appears
in original kick/setup PAL `0x802BB6EC` (US `0x802BFD7C`). Further trajectory
helpers use the matching gravity ratio; this is more than one incidental float
change. Ball damping/flight should retain these original PAL values at the
corresponding original cadence.

## Cadence and match-clock limits

Independent PAL VI/audio evidence is in [PAL runtime research](pal-runtime.md).
The original main initialization passes retrace count one to scheduler
`0x8001D4D0`, which calls original `osViSetEvent` at `0x8001D5CC`. Scheduler
VI processing `0x8001DC50` notifies its linked clients; the main queue is
`0x800A4958`. Main `0x80000B40` blocks on that queue, dispatches its message
at `0x80000B4C`, and message type one reaches render/update driver
`0x80002A10` through `0x80000B94`. Original buffer availability and game phase
still gate actual work. This proves VI-linked opportunities; it does **not**
license calling the observed game simulation exactly 25 or 30 fps.

Separate original match-clock proof is under `.local/pal-clock-01/proof.json`:
PAL init `0x801DB94C` changes US reload 30 to 25; PAL tick `0x801DC14C`
contains two matching reload changes. The original decrement-then-reload path
actually takes **31 calls in US versus 26 in PAL** per displayed clock unit.
Duration tables are identical. Thus original PAL scaling is close but its clock
rounding alone does not prove mathematically exact NTSC wall-time behavior.
The subsequent bounded correction is confined to eligible original clock
reloads, preserves pause/phase decisions and independent counters, and retains
the original final-clock behavior; see [the clock adapter](pal-match-clock.md).
Its call-count proof still depends on the original 5:6 scheduling ratio for a
wall-time interpretation.

The motion evidence supports retaining 50-Hz PAL execution with original
compensation. It does not justify changing the whole runtime to 60 Hz, applying
a global movement multiplier, speeding audio, or tying simulation to 120-Hz
presentation. Later visible verification still needs measured match-clock
elapsed time and comparable player/ball movement against the preserved NTSC
baseline, including pause, replay and speed settings.

## Implementation status — 2026-10-17

The static checkpoint above is historical evidence about original regional
coefficients, not a statement that runtime integration remains deferred.
`src/runtime/native_game.cpp` now selects the version-2 native frame derivative
under the exact original function identity. In stable HIGH scene `0604`, it
omits the duplicate complete simulation pass and its paired skeletal-phase
pass. Original first passes, PAL motion coefficients, VI/audio timing and
other scene/transition paths remain intact. The local NTSC match-clock adapter
is also connected to the exact original initializer and tick identities.

The final Linux CPU suite recorded 498 tests with three native-diagnostic
launch tests skipped. Genuine PAL frame/skeletal closure, original PAL/US clock
leaf comparison, audio DMA progress, all-22-player capacity and preserved
full-detail task traversal tests all passed. The phase regression compares 35
states over 25 tasks with original LOW; its final pose bake is an observer.
Earlier live build-47 HIGH Training and original Ares LOW measurements establish
approximately 25 admitted updates per second in those particular runs, not a
fresh final-build NTSC match equivalence result. See
[the native pace evidence](pal-native-frame-pace.md).

Final-build matched-state player/ball displacement, animation cycles and full
match-clock duration against the NTSC reference, including pause/replay and
speed settings, remain distinct wall-time acceptance work. Distinct GPU images
at 60/120 Hz demonstrate presentation interpolation, not those timing claims.
Audio CPU tests demonstrate source-clock/FIFO behavior; actual output/device
quality and drift require their own recording or listening evidence.

## Executed original integration leaves — 2026-10-17

Private `.local/ntsc-pal-leaf-comparison-01/receipt.json` records a completed
CPU-only comparison using authenticated original PAL and US ROMs, exact
translated sources and original function-body hashes. No game, audio device
or GPU ran. The harness executes complete original position leaves PAL
`802C932C` in overlay `386080` and US `802CD70C` in overlay `389970`, plus
original airborne vertical steps PAL `802B6D60` and US `802BB3F0`. An unexpected
external call aborts instead of substituting a behavior stub.

For both original speed slopes and all 256 attributes (512 cases), initial
horizontal velocity comes from the authenticated original readonly slope/base
coefficients. This explicitly does not execute the full player initializer,
acceleration, heading or clamp closure. After 25 PAL versus 30 US position
calls, maximum relative displacement disagreement was `7.56608222e-7`, below
the predeclared `2e-5` floating-point tolerance. These calls represent one
synthetic second under the assumed 25/30 cadence; they do not measure it.

The ball starts at height 1000 with zero vertical velocity and the original
regional gravity literals. The original position-before-gravity integration
predicts `y = 1000 - g*n*(n-1)/2` and `v = -g*n`. Observed PAL height was 952;
US height was 951.666687012. Their difference, 0.333312988, agrees with the
precomputed discrete-Euler difference 0.333330296 to approximately
`1.7308e-5` game units. Each result also satisfied its predeclared roundoff
bound `8*float_epsilon*n*1000`. Regional terminal velocities, expressed per
assumed second, were approximately -100.00002384 and -100.00003338. Thus the
small height difference is consistent with the original different step sizes,
not evidence requiring a new global pace multiplier.

This adds executed integration evidence to the earlier coefficient algebra.
It does not establish full accelerated trajectories, ground contacts, regional
animation-script equivalence, AI decisions, actual NTSC scheduling or final
wall-time gameplay equivalence. No product change follows from these results.
