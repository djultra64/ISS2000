# PAL football processing and Controller entry corrections

Original project work: `djultra64`.

The r50 report describes a black transition after Begin Training, before the
field appears. There is no runtime log in the user's r50 portable folder.
Its preferences were inspected read-only: P1 Type5, other ports Type1,
1080/60 fullscreen 16:9. No user data or executable was changed. The existing
full integration19 result was428 passed, zero skipped; that result did not
exercise the user's transition. No new game or Windows execution was used.
The black transition itself has not been reproduced or established as fixed.

## Complete original controller processing

A separate input correctness defect was reproduced through genuine original
CPU code. Normalizing a private projected packet only inside801D4880 restores
it before later original consumers. Original801D5A74 subsequently invokes
801D4CC0→801D4B4C, which reads controller+0x24 held at4CF4/4BC8 again. Type5 R1
therefore normalized OneTwo while this later original path saw the ordinary
menu R input0010 instead of projected0002 in genuine guest profile0.

The temporary packet scope now encloses the complete original processor at
801D5A74. Original801D5E1C receives the same scope for its auxiliary path.
The direct801D5EA4 branch at5F7C normalizes then invokes4CC0 separately, so
801D4CC0 also has an exact per-port scoped entry. Each new lookup hook requires
the active verified original function pointer from overlay25AAF0/801AD820.
The existing801D4880 hook remains the fallback for initializer801D5FE8.

An outer projected packet makes the object's source pointer differ from its
fixed original SI address. Nested wrappers immediately execute their genuine
original body without reading the SI sidecar or converting again. A full
processor therefore uses one physical sample and one conversion. Source packet,
32-byte reserved frame and incoming SP restore only after the entire original
processor returns. Original sticks, normalized outputs and later raw consumers
remain in the same scope. Original CPU bodies and genuine SI packets are not
rewritten. Keyboard, foreign object/profile/source/stack and inactive overlay
paths retain their ordinary original behavior.

`tests/test_football_full_stage.py` compiles194 original active bodies selected
by exact PAL ROM-byte equality against the preserved High43 Training capture.
It extracts the production wrapper implementations and executes full5A74,
auxiliary5E1C and direct4CC0 paths. Type5 press/hold/release covers all three
genuine profiles and four logical ports; counts, raw consumer observation,
full non-stack RAM output and source/SP restoration are compared with the
ordinary original projected-input baseline. Nested normalization executes once.
Keyboard and foreign objects do not project. A retained negative control using
the old inner-only boundary fails the raw-consumer assertion. Unexpected original
calls throw rather than silently succeed. These are bounded CPU fixtures, not
an execution or acceptance of the whole game.

The initializer test additionally executes genuine Controller Ready802C53A4
through80014A74 for all four profile objects, then genuine801D5FE8 first-input
initialization. Neutral and South Begin-confirm input finish for each original
profile and agree with original projected-input output. This rules out those
specific isolated initialization failures; it does not prove the black
transition's cause or exclude every later gameplay branch.

## Original Controller entry fade

Original802C4820 constructs Controller, then queues48C0 through8000CC5C with
fade duration0030. CC5C stores pending48C0 in scheduler node+0x10 and changes
the live callback to8000CDD0. Only later does48C0 install48F4. Both previous
owner probes accepted only48F4, leaving the original screen visible during
this entry phase.

The native and graphics adapter probes now additionally accept exactly live
48C0 or the pair{liveCDD0,pending48C0}, retaining original overlay/body hashes,
bounded220-node list validation, cycle rejection and all graphics preflight.
They do not accept arbitrary pending callbacks. A completed original Controller
fixture replayed in these genuine entry states first failed ownership, then
passed both probes and the original CPU rendering chain after the correction.
Foreign pending/live callback variants still reject with unchanged RAM. No
host overlay or black cover was added.

## Type 5 action semantics correction — r53

The host scheme was stored and its projection ran in genuine Training, but three
football actions had been assigned the wrong meanings. The primary original N64
manual identifies C-down as Dash (raw0004), C-left as FlyBall (raw0002), and
C-right as OneTwo (raw0001) in original profile0. All three resident profiles
therefore use table order OneTwo, Through, Dash, Pass, Shoot, FlyBall. The former
conversion permuted these three actions in every host preset and Free.

Only the guest-action table was corrected; physical PS1/eFootball layouts and
saved preferences retain their positions. New independent manual-derived
expectations and original held-Dash consumer801D4F88 cover the corrected meaning,
including the old conversion as a failing control. The corrected normalizer
oracle is Pass0004/Shoot0008/Dash0002/Lob0001/Through4000/OneTwo8000, with the
original Curve2000/Cursor0010 modifiers preserved.

Actual hidden native Training `.local/type5-runtime-02/` confirms all eight Type5
held actions through SDL→SI→the full original801D5A74 processor. RT advances the
original Dash counter and sets flag0400; release resets the counter. The real
Controller screen showed and confirmed Type5 before Begin Training loaded the
field. GPU captures and the bounded receipt retain the evidence. Input used the
app-only virtual controller, so this does not establish physical Ally acceptance
or resolve every possible black-screen report. Windows was not touched.
