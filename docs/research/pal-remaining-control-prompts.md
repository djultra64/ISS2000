# Remaining PAL control prompts — correction pass

Original project work: **djultra64**. Checkpoint: 2026-10-18.
The user owns the remaining gameplay, mode, controller and endurance acceptance.
This pass uses CPU regressions and saved private RAM; it starts no new game and
makes no Windows changes.

## Confirmed omissions and corrections

The r60 Free Kick/Corner pause captures retain original N64 Z/R labels. The old
adapter recognizes only the prefix consumer at `8025EA00`. Original dispatcher
`801DF7B0` selects six distinct resource triples through `801DF89C`; five other
prefix consumers were outside that coverage. The corrected adapter identifies
all six by their complete original consumer and atlas hashes, retains port
ownership and the original Low/High font/geometry checks, and draws short labels
through the original engine font. The adjacent attack/defence action-label
objects and asset bytes remain unchanged. The repeated right-column Z action is adapted too;
logical Dash/One-two/Through labels remain in the expanded variants.

The native set-play request builder also used generic Z/R bindings even though
football input projects them through Curve/Cursor in the applied Type1–5 or Free
map. It now uses that same per-port map for these two set-play labels. Keyboard,
replay and menu requests retain their respective original input paths. Physical
face positions use the existing family labels, including Nintendo A/B and X/Y
positions. Owning strings remain alive through both adapter calls.

The replay omissions are three separately owned original objects: the A/B,
stick and C-button diagram; the R/Z/C prefix image; and the Start-button text in
Cancel. These exact consumers now propose physical labels through the original
font. Move and four explicit direction labels replace the console diagrams.
Original panel art, playback indicators, Cancel text/arrow, Up/Down/Camera Angle
labels and the replay R badge retain their original owners. The R badge denotes
Replay; it is not an input instruction. Atlas/consumer/constructor, sprite layer,
origin, frame, font and High-emitter guards reject foreign states before any
substitution. The last active logical port supplies the physical requests.

Handicap has another shared CI4 image containing L/Z and R. Its exact two-cell
consumer at `802AAFC0` is now adapted separately. Both left actions remain visible;
their combined label fits the original32px cell. Its original neighboring P1/CPU
Control and Enter/Go back objects remain intact. Only the identified Low menu
resource, original atlas, font, layer, origin and scene are accepted.

There is no host controls overlay and no patch to original asset bytes or game
input consumers. Prompt proposals are read-only. Native original-font drawing
uses its existing checked task arena; the bounded result/dispatch arrays now
hold eight text lines for the seven-label replay diagram.

## Verification

Each new regression first failed on its missing behavior, then passed with the
correction. Compiler errors while preparing two fixtures were resolved before
accepting their behavioral negative controls. Strict old prompt tests also
caught two new formatting warnings; those are corrected.

- `test_setplay_prompt_variants.py`: all six genuine original constructors,
  Low/High, four ports and four input families; original font emits rectangles;
  altered consumers and wrong owner ports are rejected without changing RAM.
- `test_replay_physical_prompts.py`: original replay constructor, both video
  modes and every port/family; Xbox/PlayStation/Nintendo/keyboard face labels,
  original font emission, foreign layer/atlas/font/code/frame/origin rejection,
  invalid active port and null-memory handling.
- `test_handicap_physical_prompts.py`: original initialization/resource routines
  against the saved menu atlas and original footer consumer; both left actions,
  cell bounds, all ports/families, original font output and negative guards.
- `test_native_setplay_bindings.py`: extracted production request construction,
  actual scheme tables and physical-position label helper; all six schemes,
  four ports and four families, including Free Curve moved to another position.
- The existing native prompt lifetime regression still checks short and heap
  strings under AddressSanitizer and detects the historical dangling-owner bug.

The full source suite and final package verification are recorded under the
private `.local/r62-verification` directory and summarized in HANDOFF/acceptance.
These CPU results do not assert a fresh GPU screenshot, human controller input,
complete match, mode coverage or sustained performance/audio on r62.

## Other findings and scope

The r58 framebuffer-ownership, r59 formation persistence and r60 VI publication
corrections are preserved. The lost-swap regression proves that race, without
asserting that it exclusively caused every earlier black screen.

The unresolved halftime navigation route did not establish a new port defect:
the original PAL reference also keeps the red Start label while Member opens,
and the native retry never combined a deliberate D-pad top selection with the
following confirm. The gold geometry seen during a goal transition likewise
requires original comparison before a defect can be identified. These remain
explicit user functional observations; neither receives a speculative patch.
Historical source saturation was also present upstream and the observed monitor
saturation matched converted original PCM; no clipping-free claim is made.

The earlier private audio acceptance session was interrupted and retains no
clean-exit receipt. Its recorded PIDs are absent. A separately opened r60 game
was detected during this pass and was left untouched. No result from that game
is used as acceptance evidence.

Final r62 suite: Full automated r62 suite passed: 510 tests, 507 passed and 3 historical NTSC diagnostics skipped (445.732 seconds). The first full execution retained one old test failure: it inspected unused text slots after capacity increased from4 to8. The corrected test verifies active rows and empty unused slots; the complete rerun is green. The game executable did not change between these two executions.
