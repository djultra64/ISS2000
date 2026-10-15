# Original PAL and US match-clock comparison

Original project work: djultra64. Static research: 2026-10-15.

The user requires NTSC-equivalent game pace while retaining PAL Career content.
The original PAL match-clock code already contains regional timing adjustments.
Changing the host display or VI frequency alone cannot establish equivalent
simulation, clock, animation, movement or audio behavior. No game was executed
for this comparison.

## Original functions and fields

Two complete functions have unique PAL matches across all classified PAL CPU
function entries after explicitly substituting the observed timing literals.
The only semantic instruction changes are three reload constants, from 30 in
US to 25 in PAL. Register use, branch offsets, stores and arithmetic match.
Address-related instruction differences are retained in the private proof;
all direct jumps in these two functions were independently checked to remain
at the same relative position inside their owning function. Neither calls
another function, so no masked external JAL hides a changed callee.

| Role | US original | PAL original | Size | Observed semantic differences |
| --- | --- | --- | --- | --- |
| Clock initialization | `0x801DD9EC` | `0x801DB94C`, ROM `0x2882FC` | `0xA4` | PAL `0x801DB984` sets reload 25; US sets 30 |
| Clock tick | `0x801DE1EC` | `0x801DC14C`, ROM `0x288AFC` | `0x18C` | PAL `0x801DC1A4` and `0x801DC204` set reload 25; US sets 30 |

| Field | US guest | PAL guest |
| --- | --- | --- |
| Remaining displayed seconds, unsigned halfword | `0x801307B6` | `0x8012DDD6` |
| Remaining second's subcounter, unsigned halfword | `0x801307B8` | `0x8012DDD8` |
| Elapsed displayed seconds, unsigned halfword | `0x801307BE` | `0x8012DDDE` |

The original tick reads the subcounter first. If it was nonzero, it decrements
it. If it was already zero, it decrements the remaining-seconds field,
increments elapsed seconds, and reloads the subcounter unless remaining time
has reached zero. A reload of N therefore produces **N+1 tick calls per normal
seconds rollover**: 31 for US and 26 for PAL. Treating the reload literal itself
as a measured real tick frequency would be incorrect.

The original dispatcher calls the PAL clock tick at `0x801DB428` or
`0x801DB558`, in separate paths of `0x801DB318` (size `0x2E8`). US corresponding
call sites are `0x801DD4C8` and `0x801DD5F8`. Main-loop/scheduler cadence must be
established separately to convert these call counts into wall-clock pace;
they do not prove a real frequency by themselves.

## Duration and display evidence

Initialization's eight-halfword duration table is unchanged:

| US guest / ROM | PAL guest / ROM | Original halfwords |
| --- | --- | --- |
| `0x8009A90C` / `0x9B50C` | `0x80097F1C` / `0x98B1C` | 180, 300, 420, 2700, 60, 180, 180, 900 |

The original code chooses one of the first four or last four entries using the
match option and context byte; this comparison does not invent menu labels for
those options. Both builds initialize remaining seconds from this table and
elapsed seconds to zero. The separate 60-halfword clock threshold table at US
`0x801ED270` / PAL `0x801EB1E0` also matches completely.

The HUD routine US `0x801DDE28` / PAL `0x801DBD88` (size `0x3C4`) has a complete
normalized body match. It reads the remaining-seconds field and uses the same
unsigned division-by-60 arithmetic for its minute/second digits. The arithmetic
supports identifying the field as displayed clock seconds; this was not inferred
from the numerical value in a screenshot.

## Consequence for NTSC-equivalent pace

A PAL update rate increase of 50 to 60 VI events per real second, with unchanged
update scheduling and unchanged PAL reloads, would increase the number of clock
ticks per real second by 20%. That is a conditional consequence, not a measured
PAL game speed and not a complete proposed patch. PAL movement, ball integration,
animations and other timers can have their own compensated constants.

The implementation must select a coherent timing policy using the original
scheduler and per-update units together, then preserve the user's selected
simulation pace independently of 60/120-fps presentation. Full NTSC-equivalent
pace remains unverified until original scheduling/timestep research, focused
adapter checks and later authorized visible gameplay comparison are complete.
Do not claim that changing VI configuration alone solves the requirement.

Private `.local/pal-clock-01/proof.json` pins both ROM digests, full function
bounds/hashes and every instruction difference. `prove_clock.py` reproduces the
assertions from original input data and the independently recovered PAL section
inventory. All original data remains private and unchanged.

## Bounded NTSC clock adapter and isolated leaf checks

`NtscMatchClock` now implements a reviewed local correction for the original
inclusive-counter bias. Each of the two PAL subcounters independently schedules
five 26-call intervals and one 25-call interval, totaling 155 calls per six
clock seconds. The first interval is counted at original initialization; only
an observed original zero-to-25 reload, together with a one-second decrement,
advances that counter's phase. An elapsed paused/gated interval cannot advance
the carry, and a zero-time ending cannot invent another reload.

The initializer hook is original PAL `0x801DB94C`, generated symbol
`func_801DB94C_overlay_287ab0_801db100`; the tick hook is `0x801DC14C`,
`func_801DC14C_overlay_287ab0_801db100`. Both belong to the private original
`overlay_287ab0_801db100` section. The runtime must verify exact revision,
active original section and function pointer before admission, call the
original initializer/tick once, and apply the helper afterward. The helper
never writes remaining seconds, elapsed seconds, HUD digits, physics or audio;
its only guest writes are halfwords `0x8012DDD8` and `0x8012DDDC`. It rejects
short memory, uninitialized/stale observations and invalid subcounter values.
No helper wiring or full-game execution was performed by this subtask.

The SDK/main-loop research establishes original VI-linked update opportunities
at a PAL:US ratio of 50:60 through the same scheduler/queue route. Actual
simulation updates also have buffer/phase gates; this research does **not**
claim that 25/30 or 50/60 is a measured fixed simulation frequency. The rational
clock correction depends on their common 5:6 ratio, not that absolute choice.
Original PAL player/ball timestep compensation is documented separately; it is
preserved by keeping this adapter local to clock subcounter reloads.

An isolated native test executes the actual generated original PAL and US
clock leaf functions over fresh synthetic 8-MiB buffers, with no host-service
calls, game loop, rendering or emulator. It observes every original rollover
across 2,700 clock seconds and both counters. At the representative 25/30 rate
pair, original PAL accumulates 18 seconds of clock-period difference; at 50/60,
it accumulates 9 seconds. The adapter removes cumulative drift, agrees exactly
after each complete six-second group, and keeps every intervening rollover
within one PAL update. These are synthetic call-rate comparisons, not measured
gameplay results. Additional checks cover independently gated counters,
unchanged pauses/endings, reset/stale observations, and untouched memory outside
the two verified subcounters.

For any initial duration K divisible by six (all eight original duration-table
entries), corrected PAL calls are `K × 155 / 6` versus US `K × 31`. Their
wall-clock duration agrees at the original 5:6 update-rate ratio. For example,
the 180-count option takes 4,650 corrected PAL calls versus 5,580 original US
calls. At 25/30 updates per second, each is 186 seconds; these representative
rates explain the ratio and do not establish the game's actual fixed cadence.
