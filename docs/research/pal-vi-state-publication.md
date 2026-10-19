# PAL native VI state publication

Original project work: **djultra64**. Linux only; Windows remains untested.

## Runtime failure retained

Exact r59 SHA-256:
`39d015c77a9becb926fdb3ab9e3093d1d1a93f1f4d742dd43ae4d882cfe3fce7`.
Two fresh-data, normal runs of England Free Training reached a black field.
Both actor and ball counters stopped at4. The first stayed at stage_tick2234;
the second at2405. Confirm did not recover the first. Both closed normally0.
Real PipeWire audio was routed exclusively to an owned private null sink; no
other game, debugger or guest-memory writes were involved.

Evidence: `.local/ntsc-animation-reference-prep-01/runs/native-r59-high60-01`
and `native-r59-high60-02`. The latter preserves an8MiB read-only RAM snapshot.
All three framebuffer busy flags were1; completed-ring read and write both
pointed to8012DCE4, cached/current retirement state was80500000, and no SP/DP
graphics task was active. The isolated original scheduler replay
`.local/framebuffer-starvation-repro/r59-frozen-state.py` consumes this exact
snapshot and remains unable to allocate a framebuffer over120 simulated VI ticks.
The simulated hardware current initially equals the observed cached state;
this is a bounded scheduler reproduction, not a full hardware or live recovery.

A separate parent-debugger run and a third normal run reached the field and
advanced. Thus the failure is intermittent. No equivalence of these runs to the
user's original coin-skip incident is claimed.

## Deterministic native race

The pinned runtime's VI update flips `cur_state`, then copies the new current
state over the new next state. SDK setters, including `osViSwapBuffer`, hold
`events_context.message_mutex`; the VI update previously did not. A setter can
therefore write to the new next state between flip and copy, and the copy erases
that request. Unlocked current/next getters also read a concurrently changed index.

`tests/test_runtime_vi_synchronization.py` extracts the actual VI state methods,
VI update call site, SDK swap and getters. A fixture-only barrier after the index
flip forces the writer to attempt the real SDK call before the copy. Separate
fixture synchronization orders the accesses, avoiding an undefined data-race
experiment. Original and r59 adapters return next80500000 after requesting805AA000
(exit20). The corrected adapter returns next805AA000 (exit0). VI registers and
current framebuffer remain the previous valid image at this boundary.

This proves a lost-swap race in the native runtime. The full live instruction
sequence causing the retained training freeze has not been captured; the race
must not yet be presented as the exclusive proven cause of every black screen.

## Correction and limits

`tools/prepare_runtime_timing.py` retains its exact upstream source digest and
immutable generation. New output directory `pal-runtime-timing-v4` serializes
VI update and current/next framebuffer getters with the existing SDK mutex.
It changes neither PAL VI50Hz nor guest movement/animation clocks, scaling,
original scheduler messages, ring format or presentation/interpolation algorithms.
The previous allocator ownership correction remains present.

The deterministic regression and five related timing/scale/framebuffer tests pass.
Full r60 suite passed506 tests (503 passed,3 historical NTSC diagnostics skipped)
in428.684 seconds. The first normal exact-package run loaded four training fields
in one process, exercised free/corner kicks and original pause/quit returns, then
closed0. This remains bounded functional coverage; manual keeper actions and
independent fresh starts remain to be verified. A successful training start alone cannot close repeated
matches, coin skipping, sustained audio or intermediate-pixel acceptance.

## Observer limitation

The first private transition sampler in `native-r59-training-scheduler-03`
assumed upstream ViState32; the generated port adds ViScaleState and uses48.
Its host current/next decode is explicitly rejected in
`010-trace-host-layout-rejection.json`. Guest RAM blocks remain stable observations,
not atomic scheduler transactions. Do not use that rejected host decode as a
causal trace. The private source was corrected for future launches.
