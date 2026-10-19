# Linux correction and acceptance plan

> **For agentic workers:** Use systematic-debugging, test-driven-development and verification-before-completion. Preserve the existing dirty checkout; the user explicitly authorized autonomous continuation. Latest steering forbids agents and requires one game execution at a time.

**Goal:** Deliver a new Linux portable candidate and close the 1.0 requirements only where actual evidence supports them.
**Architecture:** Keep original simulation and display-list execution. Diagnose interpolation metadata independently of presentation/resource lifetime; missing metadata must preserve original rendering. Retain allocator identities, bank ownership and camera-cut barriers.
**Tech Stack:** C++20, translated PAL MIPS, RT64/Vulkan, Python unittest, private headless Gamescope.
**Spec:** ../specs/2026-10-15-iss2000-design.md and the user's 2026-10-17 continuation request.

## Constraints

- Windows compilation, testing and power actions remain forbidden.
- Preserve existing changes, packages, ROMs and saves; sources/ is read-only.
- Private inputs and runtime evidence stay in .local/. Own attribution is djultra64.
- Game windows stay in a private compositor. Audio/performance acceptance requires real audio without a debugger.
- No publishing or commit is required. No physical-device result may be inferred from virtual input.

## Work and verification

- [x] Read current handoff, design, acceptance and dirty status; independently audit interpolation, resource lifetime and coverage.
- [x] Add first-failure tracker diagnostics without changing quarantine behavior; focused tests distinguish mismatch, producer change, invalid fingerprint and missing snapshot.
- [x] Reproduce missing target-vector mutual exclusion with the actual generated growth block; lock growth with the presenter's existing mutex, releasing before waits/GPU. Use immutable v4 derivatives.
- [x] Reproduce first/second friendly, menu return, FPS changes and Start skip. Capture snapshot/group/epoch data and actual intermediate pixels; attribute causes only when observed.
- [x] Close direct radar rectangle ownership through parent-task/private-bank lifetimes and actor-generation roles. Verify original output parity and rejection cases before GPU acceptance.
- [ ] Check preserved r55 22-player/418-matrix/both-bank, radar sampling and stick behavior.
- [ ] Verify sustained real audio and frame delivery in an owned silent PipeWire sink, with no desktop audio recording.
- [x] Run current-source full automated suite, documenting every skipped integration prerequisite.
- [ ] Exercise clean/existing data, original Graphics Save/restart, resolutions/FPS/fullscreen, controls, pause/replay, Training variants, editing, leagues/cups and Career save/reload.
- [x] Produce a new ROM-free portable Linux folder and verify its exact executable and copied-folder operation.
- [ ] Finalize HANDOFF/acceptance after uncontended audio and Career receipts.

## Review focus

Repeated scene/camera cuts must not permanently lose interpolation. Reused addresses must never reuse another object's identity. Configuration cleanup and vector growth must not race presentation. Invalid interpolation must retain a valid original frame. Historical evidence, dummy audio and screenshots do not close current sustained acceptance.

## Evidence checkpoint

Final source suite:498 tests,495 passed,3 skipped historical NTSC diagnostics,
500.610 seconds. New candidate r56 production SHA256
`4acc1f74ea76dca1536a0b57b5858933a67f792346eb1e4209ef0eb250d6deea`;
46 manifest entries and40 notices verified; ROM-free delivery data empty.
Private exact-copy clean boot, native graphics save through2160p, shortcut label
changes and restart completed. Headless Gamescope does not acknowledge actual
fullscreen flags; full-game KWin painter attempt exited255, so actual full-game
fullscreen remains unverified.

Final development same-process first friendly60, original Pause/Quit, Settings
save120, second friendly/Start skip reached field with no persistent black.
Both matches were partial; no full-match completion is inferred. Real radar-region
GPU readbacks show distinct fractional images in89 workloads at60 and5 at120;
region also includes underlying field. All3242 field tasks retained snapshots,
46 radar commands were active, zero fallback or quarantine events occurred.
These observations do not establish that the user's exact black screen is solved.

## Audio regression discovered during acceptance

The exact r56 production candidate completed a natural friendly and reached a second friendly after native Settings 60→120 and Start/coin skip. Whole-stream real-device comparison nevertheless found 27 inserted silent gaps (2,102 stereo frames) during 1,730.8 seconds with no other project game/build/test running. All converted PCM was retained in order. Treat this as a blocker, not a pass.

- [x] Map gaps to producer boundaries and 1,024-frame device quantum; quantify full producer timeline.
- [x] Reproduce output starvation independently, keeping guest AI timing and PCM unchanged.
- [x] Add a failing production-path regression, implement only the supported host-output correction, and obtain independent review.
- [x] Build a fresh r57 candidate without replacing r56; run focused/full relevant checks.
- [ ] Repeat real-device whole-stream verification and sustained frame-delivery measurements exclusively.

Actual full-game fullscreen is now verified under isolated KWin OpenGL: Alt+Enter enters/exits actual SDL/window-manager fullscreen, native save persists it, and cold restart restores it. Both child processes exited 0. This does not imply physical display acceptance.

R57 production SHA-256: `f1a5fcd13794f3428ea86c6d4537d4092b3c4778cb67af64c002a4b5a4676480`. Final suite: 501 tests, 498 passed and 3 historical NTSC diagnostic skips, 425.924 seconds. The exact copied package clean-booted and restored native saved fullscreen under KWin. Fullscreen visual checks use compositor captures after proving XGetImage can return stale black buffers while the compositor shows Main. Long audio and sustained presentation remain pending.

## Reopened graphics gate after r57 halftime

- [ ] Preserve and diagnose the real compositor-black/display-list freeze at
  sequence25329/time795.005212s in r57 run02; audio continues and pause/resume fails.
- [ ] Demonstrate the cause before applying a change, add a meaningful regression,
  independently review it, and repeat the original halftime/consecutive-match path.
- [ ] Any new product correction requires a new portable folder; preserve r57.
