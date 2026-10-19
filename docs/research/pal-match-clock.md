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
At the original isolated-helper checkpoint, this subtask did not wire the
helper or execute a full game. The current integration is described below.

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

## Original added time and half-end gates

Static follow-up explains the visible PAL first-half clock remaining at `0:00`
before the natural halftime transition. The original game maintains two clocks:

| PAL field | Original use |
| --- | --- |
| `0x8012DDD6` / `0x8012DDD8` | Displayed remaining seconds / subcounter |
| `0x8012DDDA` / `0x8012DDDC` | Secondary remaining seconds / subcounter, used by half-end logic |
| `0x8012DDDE` / `0x8012DDE0` | Corresponding elapsed-seconds totals |

In original tick `0x801DC14C`, the secondary clock advances only when byte
`0x8009DF78 < 2` and word `0x800C1A10 & 0x40` is clear. The displayed clock's
later path does not use those two gates. Thus excluded play states accumulate
positive secondary time while the HUD continues toward zero. This is original
timekeeping, not a host-created fixed added-time allowance. Its wall-clock
length depends on preceding play states and future clock-eligible updates;
there is no verified universal number of real seconds after visible zero.

The original half-end consumer is `0x80250F90`, in the CPU section loaded from
ROM `0x4A6820` to guest `0x80230590`. Caller `0x801E64A8` reaches it at
`0x801E656C` only when byte `0x8013B44C == 4`. Its entry can first defer on
cooldown halfword `0x8026BE04` (decremented only in state zero). It then requires
halfword `0x800C1A7A == 0`, signed mode byte `0x8012DE74` outside `{4,9}`,
and state byte `0x8009DF78` outside `1..10` and unequal to `16`.

The decisive clock check at `0x8025103C..0x80251058` requires **both secondary
remaining seconds and its subcounter to be zero**. It does not use the displayed
clock as the completion condition. The original secondary clock reloads 25 even
on its final seconds decrement, so its final subcounter must also drain. The
local NTSC correction changes neither this condition nor either seconds field.

Before starting the transition, if its transition counter `0x8026BE00` is zero,
the consumer can defer while `abs(float[0x800C19B4]) > 300.0`. It increments
halfword `0x8026BE06` and proceeds at 250 such eligible calls, or earlier when
the coordinate condition clears. The absolute-value helper is original resident
`0x8000A384`. This is a bounded coordinate-dependent extra delay, distinct from
the preceding secondary-clock catch-up; the static code alone does not justify
converting its 250 calls into a measured real duration. For match context byte
`0x8009E028` equal to zero or two, the transition commits state `11` at
`0x80251174..0x8025117C`; other contexts follow original full-time/extra-time
branches. No transition or timer was forced during this investigation.

Private `.local/pal-half-end-01/report.json` pins the original tick, consumer,
caller and absolute-value helper body hashes, the threshold instruction and
counter bound. Root's separate visible run subsequently reached natural
halftime (capture `125`), consistent with these original gates. That observation
does not establish completion of a full match.

## Integration status — 2026-10-17

The historical helper-only scope above no longer describes the linked runtime.
`src/runtime/native_game.cpp` calls each original initializer/tick once and
then applies `NtscMatchClock`; lookup requires the exact active original
function identity at `801DB94C` or `801DC14C`. Overlay address reuse therefore
does not admit an unrelated function. `src/runtime/ntsc_match_clock.cpp` only
shortens every sixth eligible interval by one update, independently for the
two subcounters; it does not replace remaining/elapsed seconds or half-end
conditions.

The final 498-test CPU suite (three unrelated native-diagnostic launch tests
skipped) passed the actual original PAL/US leaf comparison over 2,700 clock
seconds: corrected PAL uses 69,750 calls and US uses 83,700. Every six-second
group agrees at the 5:6 rate ratio, with intervening error below one PAL update.
Independent gates, pauses, reset/stale observations, endings and restricted
writes also pass. These are executed CPU call-count checks, not a measured
final-build full-match duration. Consecutive friendly startup/quit and GPU
interpolation checks do not substitute for a natural full-match end or an
NTSC-reference wall-time comparison.
