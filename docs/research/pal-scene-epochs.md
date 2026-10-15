# PAL original scene and interpolation epochs

Research attribution: `djultra64`. This is original-code static analysis of the
English/German PAL revision 0, SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
No game execution was used. Original full-function hashes and ROM bounds are in
`.local/pal-runtime-01/scene-proof.json`; reproduce the checks with
`python3 .local/pal-runtime-01/audit_scene.py`.

## Scene 6/4 is the original field dispatch

Original initializer `80008BB0` creates context `8013B418`, clears its storage,
and stores its pointer at `8009E02C` (`80008BE4`). Original main dispatcher
`80002D90` reads context byte `+2E` (`8013B446`), indexes the original 13-entry
function table `8009AB14`, and calls the selected function. Table entry 6 is
`80003410`, which calls `80053A80` at `80003418`.

That second dispatcher reads `8013B44C`, indexes the original 24-entry table
`8009D100`, and calls its entry. Entry 4 is `80053DF8`. This original 6/4 handler
calls the field actor/ball update `801E64A8` at `80053E84`; its normal simulation
route then calls original clock dispatcher `801DB318` at `80053EA4`, update
`80244934` at `80053EAC`, and update `80254AD8` at `80053EB4`, before incrementing
the halfword counter `8013B442`. These are actual dispatcher table relationships,
not numerical offsets inferred from the US revision.

The handler reads the single byte `8013B452` at `80053E68`. If it is nonzero,
`80053E74` calls `801DC670` and bypasses those normal simulation calls. That
function dispatches UI state byte `8012DE32` among four original handlers,
including the recorded playback UI. Original functions `801DE110` and
`801DE13C` toggle `8013B452` with XOR 1 and a byte store at `801DE138` and
`801DE164`, respectively. They also set UI bytes `8012DE35/36`.
`8013B452` is therefore grounded as the simulation/UI bypass flag. It should
invalidate interpolation on change; its nonzero state alone does not identify
which particular pause/replay UI page is open.

## Original hierarchical stage setters

All functions below use the original pointer at `8009E02C`. Each explicit setter
takes the low byte of `a0`, writes its stage byte, zeroes the next byte, and
resets deeper stages by calling the next setter. Return values are unspecified;
these are original guest functions, not SDK services.

| Original guest function | Bytes | Context offset | Nested reset |
| --- | ---: | ---: | --- |
| `800036AC` | 28 | `36` | none |
| `80003710` | 52 | `34` | `800036AC(0)` |
| `800037BC` | 52 | `32` | `80003710(0)` |
| `80003868` | 52 | `30` | `800037BC(0)` |
| `80003914` | 52 | `2E` | `80003868(0)` |

Increment/decrement counterparts are `800036C8/800036EC`, `80003744/80003780`,
`800037F0/8000382C`, `8000389C/800038D8`, and `80003948/80003984`. All except
the deepest pair enter one of the lower setters. Hooks must call the original
function first and then notify a discontinuity. A setter may reset a scene to
the same numerical value, so only watching changed bytes misses some resets.
Nested notifications can be coalesced by the host epoch mechanism.

## Camera ownership and recorded playback

Original regular field camera `80232854` reads logical phase byte `8012DE27`.
For phase 3 it calls `801E8C64`; otherwise it calls the live camera updater
`8023264C`. It then reads camera mode byte `800C81A4` at `80232990`. Mode 2 uses
the original scripted six-vector camera path. The scripted camera controller
`8024378C` sets mode 1 at `80243894`, and callback `802438F0` sets mode 2 at
`80243954`. Thus `8012DE27` and `800C81A4` are meaningful discrete epoch bytes;
continuous eye/target coordinates are not appropriate epoch counters.

Original `801E8C64` loads halfword cursor `8012DDF0`, then calls `801E8C88`.
That loader selects `*(u32*)8012DD84 + cursor * 0x2B0` for `a1 == 0`; `a1 != 0`
selects snapshot pointer `*(u32*)8012DD88`. It decodes camera fields at record
`+268/+26A/+26C/+26E/+270`, restores two eleven-player loops through
`80032EF0`, and calls original ball loader `80244AC8`. Original recorder
`801E90EC` writes the corresponding camera, players and ball into the same
record layout. Initializer `801E9684` establishes the record buffer pointer
`80222730`, the preceding snapshot at `80222480`, and clears ring metadata.

The recorded playback controller `801E7CCC` explicitly advances or decrements
`8012DDF0`, with wrap endpoints 0 and 67. Autoplay `801E8AA8` advances the same
cursor and checks the circular capacity of 68. This proves cursor direction
and jumps can be detected from original data. It is not an inferred frame timer.
An epoch reset is appropriate for reverse motion, seek jumps, and conservative
wrap treatment; ordinary forward cursor steps should retain interpolation.
If host render sampling can skip multiple original updates, that distinction
must be handled by update observations rather than assuming every `+2` is a seek.

Original recorded playback entry `801E68F0` (1076 bytes) saves the live snapshot,
initializes the cursor and loads a recorded frame. Return `801E78F4` (504 bytes)
restores the saved state and camera path. Both belong to
`overlay_287ab0_801db100`, loaded from original ROM `287AB0` to guest `801DB100`.
Generated original symbols are
`func_801E68F0_overlay_287ab0_801db100` and
`func_801E78F4_overlay_287ab0_801db100`. A host hook must confirm that this
original overlay is the active owner before calling or intercepting it.

## Original position correction and reused-player placement

Additional original-ROM proofs, full-function hashes, and bounds are recorded in
`.local/pal-position-epochs-01/proof.json`; reproduce them with
`python3 .local/pal-position-epochs-01/audit.py`. No guest CPU execution is used.

The original ball render-record pointer is the word at `802B57D0`. It is not a
record embedded at that address: initializer `802A4CCC` calls `802A49EC`, which
allocates a root through `8002AC08`, then stores the returned pointer at
`802A4CFC`. Original correction function `802B718C` loads that pointer at
`802B7234/38`. After its existing pause/playback gates, it compares horizontal
ball displacement against its own original 20.0 limit. Only its correction
branch changes the ball/model positions; its stores to the pointed render
record are `+8`, `+0`, and `+4` at `802B7248`, `802B724C`, and `802B7254`.
The host observes those three words before and after the original function,
checks that the pointer still identifies the same configured pool record, and
retires current frame IDs only if their bits changed. This does not extend the
original 20.0 rule to other objects or introduce a host distance threshold.

Original placement function `802388C8` reuses three existing player structures
at `8026BEE0 + n * 138`, writes fixed positions and angles, then calls `802C6844`
for each. The latter copies position to each existing actor at `+50/+54/+58`;
ordinary resident update `800300D0` later copies those fields into render-record
position `+0/+4/+8`. Render-record `+C/+10/+14` is scale, not position.
Placement's only direct caller is `801EBE20` in `overlay_298280_801eb960`.
That caller dispatches state byte `8013B44E`; state 5 enters `801EBDAC`, waits
for halfword countdown `801F0F50` to expire, increments the state at
`801EBDE8`, and then invokes placement. Thus this function is a concrete
placement boundary suitable for an epoch reset after its original body.
The initial placement `80238778` first creates fresh actors, whose allocations
already receive fresh transform generations.

| Original symbol | Original ROM start | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `func_802B718C_overlay_386080_802b57e0` | `387A2C` | 268 | `ab58d15aca1f38903b6ba6ac9e4e9ec3155cdf04a57a48f5d5fb6d07a065eb33` |
| `func_802388C8_overlay_4a6820_80230590` | `4AEB58` | 316 | `e0a71b8240da66946658ebd26078e5c8bb1deb9413334fe48777b00943f8d5a4` |

Both hooks must compare the active original function pointer with that exact
symbol before observing or intercepting its address. Each wrapper calls its
original once. Current frame IDs retire; allocated generations and queued
immutable task snapshots remain available. Ordinary unchanged calls to the ball
correction do not reset interpolation.

## Integration boundaries

A grounded PAL policy can enable the 6/4 observer with the proven transform
layout, reset after original stage setters, playback entry/return and the proven
reused-player placement, observe the original ball correction, watch
`8013B452`, `8012DE27`, and `800C81A4`, and track playback cursor discontinuities
only in phase 3. The host retains its matrix/projection validation. These
position hooks cover the two proven correction/placement paths; other per-object
teleports outside these boundaries remain unclassified and require gameplay
acceptance and further original-code tracing if observed. None of these
observations changes simulation or VI cadence.

`8002AF40` is a camera/model reset wrapper calling `8002AF6C`, `80028234`, and
`800277B8`, but it has callers throughout many overlays. Its complete caller
frequency was not proven here; a blanket reset hook is not yet justified.
Likewise, `80025040` sets camera vectors during ordinary continuous camera
motion, so resetting on every call would prevent useful interpolation.

Semantic names for every phase, every goal sequence, and all possible scripted
camera cuts remain unclassified. The proven stage/mode/playback transitions
cover original discrete changes without claiming exhaustive gameplay validation.
Actual match, goal, pause, and replay testing remains deferred with the user.
