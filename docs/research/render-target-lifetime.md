# Render-target lifetime during presentation

Original project work: djultra64. Investigated 2026-10-16.

The r53 Pre-season crash is a confirmed use-after-free of an RT64 interpolated
`RenderTarget`. The correction is included in Linux r54. Focused CPU checks and both application
builds pass. An actual hidden Preseason run passed coin toss, kickoff and
continued field play; this is a scoped transition check, not exhaustive race or
frame-pacing acceptance.

## Confirmed core evidence

The private core `.local/preseason-crash-54/iss2000-user-495386.core` was inspected
with its exact executable, `portable/ISS2000-Linux-20261015-r53/iss2000`.
`PresentQueue::threadPresent` called `RenderTarget::resolveTarget`, which passed
invalid `VkImage 0xF1` values through Plume barriers to RADV. RADV crashed while
dereferencing that invalid image handle.

The retained target was `0x7fd3ac109790`. The interpolated-target vector had
`begin == end == 0x7fd3ac0d16a0`, with capacity for two entries; its cleared backing
storage still contained the target at index 1. The 224-byte target's allocator
links were being interpreted as texture pointers, and another free chunk's
`0xF1` size field became the Vulkan image handle. This establishes invalid
application resource lifetime before the driver call.

The presentation captured counter-set index 0, while the global index had
advanced to 1. The current set had `presented == available == 0`, allowing the
original cleanup predicate to pass while an older presentation still used its
target. The pinned source clears this vector in
`WorkloadQueue::threadConfigurationUpdate` when framebuffer configuration or
swap-chain size changes. The core does not distinguish which flag triggered it.

Private evidence and verification receipt:
`.local/preseason-crash-54/analysis.json`. Supporting files include
`gdb-lifetime.txt`, `gdb-manager.txt`, `gdb-live-targets.txt`, `gdb-counters.txt`
and `rt64-layout.txt` in that directory.

## Correction and lock order

`src/runtime/render_target_lifetime.{hpp,cpp}` supplies owner-specific shared and
exclusive lifetime scopes without changing pinned RT64 headers or ABI.

The present derivative acquires a shared pin at entry to `threadPresent`, before
configuration or target reads, and retains it through all original GPU fences
and function exit. Its caller's `waitForWorkloadId` remains outside the pin.
The workload can continue producing extra interpolated frames while presentation
waits for them.

Only destructive configuration updates acquire the exclusive scope. They release
`configurationMutex`, acquire the lifetime scope, then reacquire
`configurationMutex` before reading or consuming configuration flags. This keeps
lifetime-before-configuration lock order and allows inspector/configuration
reentry while cleanup waits. Ordinary configuration updates acquire no exclusive
scope. The same workload producer publishes all remaining `available`/`skipped`
outcomes before entering the next workload's configuration update.

The exclusive scope replaces the original weak counter wait. Under
`interpolatedMutex`, both obsolete counter sets are reset, each with `count = 1`,
before the original manager cleanup and vector clear. An active presentation
finishes before destruction; a queued later presentation uses the existing
single-frame framebuffer/RDRAM path instead of indexing the retired vector.

`tools/prepare_rt64_menu_interpolation.py` emits schema 3 workload sources;
`tools/prepare_rt64_present_lifetime.py` emits production and evidence present
sources. Immutable output directories must be versioned, including
`rt64-menu-interpolation-v3`; existing derivatives must not be overwritten.

## Verification and limits

Four focused tests passed in 5.153 seconds: both derivative-composition tests,
the lifetime concurrency regression, and the existing genuine original-CPU
Saved Data regression. The unguarded concurrency baseline fails because cleanup
destroys the target before a withheld presentation fence. The guarded case proves
producer progress, target survival until the fence, configuration reentry,
ordinary-update progress, and coherent retirement before a pending presentation.
An independent review reran the three lifetime/derivative tests successfully and
found no concrete severe defect.

All four generated source variants passed syntax compilation against the pinned
RT64 headers: production/evidence present and final schema 3 production/evidence
workload. The result is recorded in the private receipt above. Upstream source
SHA-256 pins are:

- Workload: `6e53030e8899c42347b51e67879fcb9679ad487ac067c192612c432d85bca4a4`.
- Present: `90df4e9c97136fa9662ee003393ad657fcb3e58cade6a24052012cf54a124c90`.

Both final development and production Linux builds compile and link. A private
headless GPU run at requested120 passed original Preseason team selection,
Handicap, Stadium, Game Setting, roster, stadium introduction, coin toss,
kickoff and continued field play. Captures18–21 and render logs remain private
under `.local/select-teams-54-final3/`. The process exited normally after an
explicit Escape in its own display. The underlying lifetime fix is identical
to the final r54 package; later changes concern prompts and HUD only.

This verifies that scoped transition after the exact-core correction. It does
not prove exhaustive resource-race resolution, unchanged sustained pacing,
physical120Hz scanout or full-game acceptance. Dummy audio was used for this
rendering test. No Windows work was performed.
