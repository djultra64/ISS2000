# Continuous AI progress and intermittent audio clicks

Original project work: `djultra64`.

## Reproduced fault

The source44 Linux portable build's default audio backend is native PipeWire
through SDL2 compatibility / SDL3. In a hidden 1080/60 startup run, the adapter
rejected **115 valid audio DMAs in approximately 37 seconds**. The rejected
buffers contain 108,256 stereo frames, approximately 2.455 seconds at the original
PAL SDK rate of 44,099 Hz. Rejections repeat approximately every 0.320 seconds.
The first rejection precedes every debugger-induced pause; only the rejection
instruction had a breakpoint, rather than every audio call.

The original PAL producer at `0x8004BAE4` calls `osAiSetNextBuffer` at
`0x8004BB20`, then unconditionally calls `osAiGetLength` at `0x8004BB28`.
It does not inspect or retry a failed submission. Consequently, accepted SDL
output can remain continuous while entire generated blocks are missing from the
music. The recorded source contains a 23,114-unit sample discontinuity exactly
at a DMA boundary. This is distinct from sustained amplitude saturation.

The complete original producer body is 432 bytes at ROM `0x4C6E4`, SHA256
`262578405c86e9e099228cec98d511c5666c802ae628913893cf14262c677adf`.
The actual private receipt, PCM and debugger log are under
`.local/audio-investigation-01`; ROM and recorded game audio are not distributed.

## Cause

The former adapter advanced its two-descriptor AI FIFO from changes in
`SDL_GetQueuedAudioSize`. That count changes in complete device pulls; a 1024-frame
pull at 48,000 Hz occurs every 21.333 ms. The original PAL producer runs at 50 Hz,
every 20 ms. Approximately every 16 producer calls, two successive observations
can fall inside one host pull interval. The adapter therefore reports a full
FIFO even though an independently running AI DAC would have finished the older
descriptor.

SDL documents that its queue count tracks data awaiting hardware submission,
rather than a precise DAC playback position:
[SDL_GetQueuedAudioSize](https://wiki.libsdl.org/SDL2/SDL_GetQueuedAudioSize).
It cannot serve as a continuously advancing guest hardware register.

The original producer computes its next buffer from target minus current AI
frames plus 176, aligned to 16 frames and clamped to target minus 16. At 44,099 Hz,
the target is 896 and minimum 880 frames. Executing the production adapter with
this producer and 1024-frame host pulls loses 187 DMAs in 60 seconds. Using a
continuous AI clock with the same producer and the same two slots loses zero.

## Bounded correction

`AudioDmaClock` advances the original two-descriptor FIFO using monotonic elapsed
nanoseconds and the original SDK's actual source frequency. Fractional source
frames carry across observations. Once the FIFO becomes empty, elapsed idle time
cannot be spent on a future DMA. Long intervals use split integer arithmetic to
avoid multiplication overflow. Converter frequency changes retain the existing
requirement that the FIFO be idle, then reset the clock.

The full two-slot rejection remains real: a third simultaneous DMA still fails.
PCM channel restoration, conversion, queue submission, device sample count and
amplitude are unchanged. Each accepted source block is copied once. The change
does not add a descriptor, hide a failed DMA, discard queued audio, apply a
limiter, or alter game simulation timing.

## Verification scope

The focused regression executes the real production progress and frequency
functions, with a synthetic1024-frame host device and the verified PAL producer.
It failed against the former adapter, including 187 rejected buffers, then passed
with continuous progress. Other cases cover actual two-slot full behavior,
completion across descriptors, fractional-frame precision, repeated observations,
long idle periods, and active/idle frequency transitions.

Private PulseAudio baseline recordings at 1080/60 and 1080/120 match accepted
converted PCM sample for sample, after recorder prefill. A default-PipeWire
CPU-only replay also matches sample for sample. Those checks alone did not
exclude the reproduced failure before enqueue. Genuine Ares 148 PAL startup
waveforms also correlate closely with the original native music, without a
large gain or mixing difference; this is not a claim of bit-identical resamplers.

Corrected DEV46 (`f703faab7090eca0ddde1aa22c095799583493b73011a423325cc47f395f5af7`)
was then run with the copied portable SDL2/SDL3 libraries, default PipeWire,
16:9, 1080/60, and no input fixture enabled. Actual PipeWire graph links verified
both playback and recording used the same private silent sink before guest
execution began. The final run accepted 947 DMAs, with **zero rejections**, zero
queue failures, and no empty queue observations after startup. Pending output
stayed between 3844 and 8312 bytes; neither the device size nor sample amplitude
was changed.

The actual downstream recording matches queued PCM for **908,999 stereo frames**,
approximately 18.937 seconds, with no interior difference or change in sample
offset. The only unmatched 302 frames are one contiguous final tail when the
application was deliberately closed. The full comparison, including that tail,
is preserved rather than reported as wholly bit-identical. The private receipt
is `.local/audio-investigation-01/game-fixed-bundle-60-final/acceptance.json`.
Two additional corrected 40-second runs also had zero DMA rejections; they are
not used as downstream proof because their recorder selected the wrong private
monitor. A separate unprimed mid-song replay detected real startup underflow,
providing a negative control for the waveform-alignment check.

The focused audio set passes 17 checks with zero skips. Longer-duration physical
output and device-clock drift remain separate from these startup measurements.
Physical USB/analog output and Windows gameplay are not established by a silent
sink recording. No Windows work was performed for this investigation.

## 2026-10-17: independently reproduced host output starvation

The independent AI clock remains necessary; it did not by itself ensure host
output continuity. An exact r56 production run with real SDL/PipeWire and no
other project game, build or test running recorded 83,078,213 converted stereo
frames (1,730.8 s). Whole-stream alignment found all frames unchanged and in
order, with 27 inserted all-zero stretches: 2,102 frames total, maximum 760.
Startup and shutdown tails are explicitly separate. All gaps resumed on the
1,024-frame device boundary and began at an enqueue boundary. Original-source
saturation existed; downstream clipping was not added.

The device was unpaused while its queue was empty. Normal ~20 ms producer
packets were about 960 frames against a 1,024-frame device pull; observed
37–48 ms scheduling stalls could exhaust the shallow queue. Cumulative
production deficits were stepwise, with negligible steady drift in the measured
intervals, not evidence for changing the guest clock. A phase sweep over the
actual timing falsified a 3,072-frame reserve; 4,096 covered the recorded trace.
A paired real-device replay then produced 20 silence insertions without priming
and zero with priming, preserving all 959,360 converted frames exactly.

R57 changes only the host output startup in `src/platform.cpp`: SDL remains
paused until at least 4,096 real converted stereo frames have been queued.
It starts once per device lifetime. Frequency changes retain queued output
and do not re-prime; shutdown/reinitialization resets the startup state. No
silence is inserted, no PCM or volume is altered, and no guest AI timing or
simulation rate is changed. The minimum reserve is 85.33 ms of PCM, with
packet overshoot and backend latency; the captured packet pattern starts
after approximately 80 ms from the first enqueue, holding about 100 ms of PCM.
This is a bounded jitter margin, not protection against arbitrary host stalls.

Production-extracted threshold, lifecycle and callback-phase tests failed on
the prior source and pass with the change. Twenty focused audio tests passed;
the final whole source suite passed 498 tests with 3 historical NTSC diagnostic
skips. Independent code review found no blocker. Exact r57 long-session
acceptance is still pending while `.local/audio-r57-production/runs/uncontended-production-02`
is recorded. Neither the short replay nor the historical shorter PCM checks
close sustained audio acceptance. The capture probe is unchanged between r56
and r57; its synchronous writes are a measurement cost, so performance will
be measured separately without that PCM recording overhead.

Evidence: `.local/audio-r56-production/replay-summary.json`,
`.local/audio-r56-production/runs/uncontended-production-01/whole-pcm-comparison.json`,
`phase-audio-analysis.json`, and `.local/r57-verification/full-suite.log`.
