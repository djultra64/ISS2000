# Resolution and sprite sampling audit

Original project work: djultra64.

## Scope (2026-10-21)

Review accessible menus at actual 1920×1080 and 3840×2160 output, beginning with Original filtering. Capture stable states, selection changes and transitions separately. Record the tested route and unvisited screens; do not claim complete menu coverage from a few screenshots.

User reports to reproduce:

- Stadium Select: Weather / Clear alignment at 4K.
- Stadium preview: unexpected black line inside the lower-left image.
- Match scoreboard: white pixels above the flags at kickoff.
- Goal Kick announcement: alignment errors at 4K.
- End of 1st Half: one-pixel white line between the two score numbers.
- Additional menus: labels, selection lamps, tiled artwork, borders and transitions at both resolutions.

Compare Original and legacy Bilinear only after establishing an Original baseline. Trace geometry, texture coordinates, palette/atlas ownership and sampling before applying fixes. A sharper filter cannot repair misplaced rectangles. Private captures and authentic game inputs remain under ignored `.local/`.

## Filter direction approved

Original remains the default. The user approved the direction Original / Super-xBR 2× / Super-xBR 4×, with alpha handling and a private asynchronous cache. The written integration design is in `../superpowers/specs/2026-10-21-super-xbr-design.md` and awaits review. The implementation plan is pending; this audit does not claim the new filter exists.

## European ROM backlog

Support additional European ROM variants/revisions once identified and verified. The user cannot provide them currently. Preserve exact supported-ROM validation; do not accept unknown revisions, patch offsets speculatively, or request ROM uploads now. Record each supported revision and its independent validation before advertising compatibility.

## Published-build baseline evidence

The published Linux 0.7.0 executable was tested with fresh disposable settings,
Original filtering and 60 Hz presentation. Private headless compositors and
separate verified null audio sinks were used, with one game at a time.

| Screen | 1080p capture | 4K capture | Scope |
| --- | --- | --- | --- |
| Title | Yes | Yes | Keyboard prompt and artwork |
| Main Select | Yes | Yes | Initial entry includes animation; not stable-state acceptance |
| Pre-season mode selection | Yes | Yes | Two-choice menu |
| Player Number | Yes | Yes | Player/CPU choices |
| Controller count | Yes | Yes | One through four controllers |
| Select Teams | Yes | Yes | England/Germany, confirmation and keyboard prompts |
| Handicap | Yes | Yes | Conditions, players, keeper and motivation |
| Stadium Select | Yes | Yes | Stable repeated captures of Euro Center Stadium, Day/Clear |
| Game Setting | Yes | Yes | Default settings |
| Pre-match team overview | Yes | Yes | Original roster/tactical layout |
| Edit Controller | Yes | No | Config/Cursor/Keeper and return |
| Edit Team overview | Yes | No | Default formation/settings |
| Match introduction | Yes | Yes | Natural intro sequence |
| Scoreboard during play | Not yet | Yes | 4K flag-top dots also visible with Original |
| Goal Kick announcement | Not yet | Not yet | Reached restart setup; transient announcement not yet isolated |
| End of 1st Half | Not yet | Yes | Stable 0–2 panel; white vertical join reproduced, no clock edits |
| Native Options / PC Settings | Not yet | Not yet | Further route required |
| Training / other competition menus | Not yet | Not yet | Further route required |

Private runs: `.local/r63-ui/runs/pixel01-original-1080` and
`pixel02-original-2160`. The 1080p session was interrupted with KeyboardInterrupt
and cleaned its owned process group, audio sink and runtime. It is not evidence
of normal game exit. The 4K captures were checked as 3840×2160. Two overlapping
capture requests failed while scene observation was also capturing; those missing
frames are not counted as evidence. Later capture scheduling was serialized.

## Initial POINT precision investigation (superseded by GPU comparison below)

Both authentic Stadium Select snapshots contain one-cycle POINT rectangles with
identity derivatives for the preview and Weather/Clear. The preview's original
pieces join at native x83 and x115. The pinned sampler rounds interpolated UVs to
1/128 before selecting a POINT texel. For the x115 join at scale2160/232, the last
sample U31.996296 rounds to32. The equivalent 1080p sample U31.888889 remains31.
This reproduces an adjacent-column read independently of Bilinear.

`tests/test_rt64_point_precision.py` compiled the pinned quantization block and
first failed on the expected 4K column assertion. The experimental derivative
in `tools/prepare_rt64_point_precision.py` keeps floor(UV) invariant only for
magnified, upscaled one-cycle POINT rectangles without linear filtering; the
original-grid, COPY, 3D, filtered and high-resolution replacement paths remain
unchanged. Its CPU test passes, including negative controls. This is a shader
hypothesis, not a claim that all visible defects are fixed.

A private Linux comparison executable was linked from the unchanged existing
production objects plus all six corrected SPIR-V fragment variants. It is under
`.local/pixel-audit-20261021/point-probe`; no production build integration or new
portable package has been made. GPU comparison remains required before retaining
the change in the normal game build. The lower-left black line and explicit
HUD/halftime shapes must each be checked rather than assumed to share this cause.


The 4K published-build session reached the authentic End of 1st Half panel
(0–2) and reproduced a vertical white join between the scores. Its captured
original RAM is `10-halftime-ram.bin`. Escape from that private session exited
the game with status0; owned compositor/audio/runtime cleanup is receipted.

The first shader-probe executable exited with SIGSEGV before rendering menus:
the unchanged consumer still compiled array lengths from the older shader
headers. Regenerating blobs also requires recompiling `rt64_raster_shader.cpp`
against matching generated declarations. A second private link includes that
unchanged consumer source with all six correct declarations; it boots. This
packaging failure is recorded independently of the numerical POINT hypothesis.


## GPU comparison of POINT precision

Private `pixel04-point-probe-v2-2160` confirms that the corrected shader removes
the stadium preview's vertical line and lower-left black line, and the
Weather/Clear cut. The same actual CPU-vs-CPU route reached End of 1st Half
(0–0): the full-height white join between the scores is absent. Original
filtering remains selected. This run exited through Escape with status0 and
owned cleanup completed before the next game started.

The fix is now integrated into normal Linux compilation: six SPIR-V fragment
variants and their unchanged pinned consumer are rebuilt together. The Linux
build passed. The separate mode2 High border correction has original-CPU proof
and a passing incremental build; integrated HUD comparison is in progress.
Windows shader paths are prepared in CMake but have not been compiled in this
pass. No release or Windows machine order was made.


## Integrated build and broader 4K coverage

The normal Linux build contains both corrections. Executable SHA-256:
`1ade08ea8ca7719c9b35abb789f92c7c9e1132d72e9159005e23bb3236b1ac6d`.
Private run `pixel05-integrated-2160` uses actual3840×2160 output and fresh
Original settings. Its Stadium Select capture reproduces the POINT probe's
clean preview and Weather/Clear boundaries.

Additional actual screens inspected in this run: native Options, PC Settings,
Graphics, Controls player list, Language (English/Deutsch), Training Select Team,
Select Training and Begin Training, Scenario New Game/Continue and No Data
file selection, Penalties Player Number, Euro Cup/International Cup/World League
New Game/Continue entries, and Career File Select. This does not cover full
campaigns, all training drills, loaded saves or every transition. Some private
capture filenames describe intended destinations rather than the actual screen;
coverage is based on visual inspection. Career requires its own title/intro
before File Select; its initial gray loading frame is not a menu acceptance.

Full automated suite after both code changes:522 tests in642.468s, exit0,
12 expected skips. Normal production compilation and incremental compilation
both exited0. Windows compilation and runtime acceptance remain outstanding.


The revision2 normal-build session also reached End of 1st Half naturally
(1–0); its central score-panel join is clean. It exited0 and completed owned
cleanup. Original-size HUD comparison nevertheless retained the top-border
bright dots. Authentic emitted commands show that revision2 sampling changes
executed. The next investigation identified duplicate alpha coverage between
one-cycle main chunks and their extra strips; see the revision3 account in
`pal-high-sprite-edges.md`. Its CPU regression and normal Linux build pass;
GPU acceptance is pending. The earlier 522-test result applies to revision2;
a fresh full suite is running for revision3.

The first Linux correction candidate folder
`portable/ISS2000-Linux-0.7.0-pixel-fixes-20261021` contains the revision2
executable above, with49 manifest files verified and no data files. It is a
superseded private comparison artifact, not the final correction candidate.
No artifact has been published in this pass.


## Revision3 GPU result and current candidate

Private `pixel06-point-v3-2160`, actual3840×2160, Original filtering:
`play-v3.png` and `hud-clean.png` both show a continuous score-panel top border
without the bright join marks. `hud-clean-score.png` is an original-resolution
crop over the live green field; flags and score art are intact. The two-word
mode2 endpoint correction therefore addresses the reported scoreboard dots.
This comparison is independent of the POINT shader fix for Low menu joins.

Current separate Linux candidate:
`portable/ISS2000-Linux-0.7.0-pixel-fixes-v3-20261021/launch.sh`.
Executable SHA-256:
`0218bfe297d3c64b99c6edef5781cf9d2b2df5a96c3e0bf034520506484e0add`.
All49 package manifest files verify; fresh package data is empty. No ROM,
original art, saves or private captures are included. The package is local;
published v0.7.0 and older data remain unchanged. Build fixtures and render
evidence are OFF. The final1080p comparison and revision3 suite results follow below.


## Final1080p comparison and automated validation

Private `pixel07-point-v3-1080` runs the exact packaged candidate, SHA above,
at actual1920×1080, fresh Original settings and60Hz. Visually checked Main
Select, native Options, PC Settings, Graphics (Original displayed), Controls
player list, Language, Training Select Team/Select Training/Begin Training,
friendly Player Number and Select Teams, Handicap, Stadium Select, Game Setting,
pre-match overview, live HUD and P1 pause/Continue. Stadium preview and Weather/Clear have no
reported cuts; `hud-score-1080.png` is an unscaled crop with a continuous border
and no bright join dots. CPU-vs-CPU pre-match input does not expose controller
editing: captures named `controller-config.png` and `controller-actual.png` are
match-introduction frames, not Edit Controller acceptance.

The final revision3 full automated suite completed:522 tests in594.859s,
exit0,12 expected skips. The original-CPU overlap regression and pinned sampler
regression also passed separately. `git diff --check` and Python bytecode
compilation passed. Normal Linux revision3 compilation exited0 in8.956s.
Windows compilation/runtime and additional European ROMs remain unverified.

Current visual status:

| Report |1080p final candidate |4K corrected build |
| --- | --- | --- |
| Stadium Weather/Clear cut | Clean | Clean |
| Preview vertical/lower-left black line | Clean | Clean |
| Scoreboard top-border bright dots | Clean | Clean, two independent frames |
| End of1st Half central white join | Clean, final packaged build0–0 | Clean, probe0–0 and normal build1–0 |
| Goal Kick announcement | Transient not yet isolated | Transient not yet isolated |

No complete campaign/all-menu/all-transition acceptance is claimed. The4K
competition coverage is limited to entry screens; saved-game branches and all
training drills were not traversed. Original-game and private capture files stay
ignored. Source changes are prepared on the existing work branch, with no new
release, push or Windows power action.


Manual change review covered shader admission guards, matching generated blob
array lengths, immutable source/output pins, original COPY behavior, mode2
cache and exact-triple guards, CPU context/cursor preservation, and packaging
identity. Review stayed within this single worker as requested; no review agent
was launched. Neither a successful build nor packaging is treated as complete
interactive acceptance. The final candidate hash and packaged manifest were
rechecked after the final suite.


The exact packaged candidate reached End of1st Half naturally at1080p (0–0).
`halftime-panel-1080.png` has no vertical white join between the score numbers.
No clock, score, mode or scene state was edited. Goal Kick remains the specific
unverified announcement: bounded watchers reached live play/restart setups but
have not isolated its transient text. Missing watcher screenshot files are not
counted as coverage. Do not advertise all match announcements as fixed.

Final sessions `pixel06-point-v3-2160` and `pixel07-point-v3-1080` both exited
through Escape with actual game exit0. Their owned game groups, audio monitors,
null sinks and private runtimes were cleaned. No game remains running for this
audit; no Windows machine was started.
