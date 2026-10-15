# Continue ISS2000 locally

Canonical repository: `/home/alfredo/Documents/ChatGPT/ISS2000` (actual `/var/home/alfredo/Documents/ChatGPT/ISS2000`). Branch `codex/m0-native-bootstrap`; preserve uncommitted work. Read AGENTS.md. Own attribution exclusively `djultra64 <329694832+djultra64@users.noreply.github.com>`. English docs, Spanish chat; `.local/` private ignored; mirror sources read-only.

## Current authoritative checkpoint

User requires autonomous completion of1.0, visible Linux execution captures and final-stage Windows portable build. Latest steering: fix ALL split sprite textures, widen the in-match HUD toward screen corners in16:9, and use suitable retro controller glyphs. Root selected greatdocbrown CC0 pack after primary-source web research and user authorized choice. No independent controls overlay; use original engine sprites/font only.

PAL build20 Release PASS; all294 configured integration tests PASS zero skips97.290s `.local/tests-pal-integration-05.log`. Source checkpoint1e2851a precedes uncommitted sky, sampling, remap and presentation updates. Preserve all current work. PAL source/private metadata02 has12170 CPU functions,54 host bindings plus retained original PFS. Exact PAL ROM SHA6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf at `.local/inputs/pal-en-de/rom.z64`; all private data under ignored.local.

Actual live game boot07 GDB PTY76917 (`.local/pal-game-build/iss2000`). Boot06 deliberately stopped before match completion. Boot07 reopens existing PAL note, reaches9-option mainmenu including Career, completes firsthalf naturally(capture125embedded) and nowplayssecondhalf GermanyCPUvsEnglandP1. Liveprocessstilloldbuild15 untilmatchcompletion. Capture110 proves full-width16:9 sky and was embedded. Capture90 previously showed fixed field player nameplates. Sampler fix Upscale2DAll causally verified same paused frame87Original/88HDwrong/89HDAllclean. Permanent fix in build15. Need fresh coin/ball/arrows/KICKOFF acceptance.

Manual120 policy now uses RT64 SkipBuffering for real PAL rotating framebuffer history; actual GPU fractional field proof pending. Evidence log `.local/pal-acceptance/render07.jsonl`; GPU gate `.local/pal-acceptance/capture.flag` currently absent, create only on live field to reserve240 readbacks. Physical display60Hz, clamp retained; do not claim measured120Hz. Geometry investigation proves PAL VI232 reference produces correct cropped720..2160 output despite larger allocation; no fbSize override justified.

Agents latest: pal_map reviewed HUD/LOD, found originalscissoroverwrite in outerflagcompositor; rootmovedscope toinner8023A510 andactualoriginal-chainregressionPASS. pal_runtime reviewedRemap/glyph andisfixingduplicatebindingSaveambiguity; interpolation_coreextendsprovenbank21Cstrip+rarefontfallback. RootHUD/LOD/glyphbuild20notyetvisuallyaccepted. Earlierassignment: pal_map correcting visible Remap composition failure103: old41A44 hook ran12 times before later draws; move to final80000BB8 boundary with original clear+font once, nohostoverlay. Owns native_game remap integration. pal_runtime implementing exact original PAL HUD object alignment/scissor helper for score/time/nameplate groups (radar excluded), owns helper/tests/docs and renderer extAspectRatio when proven. interpolation_core integrating greatdocbrown genuine CC0 glyph assets into original prompt sprite pipeline; owns newglyphassets/promptcode/tests/docs, no sharednative/CMake edits until coordinated. Root owns visible runs, CMake integration and production Linux. All must coordinate sharedfiles.

Current visible navigation: pre-match EditController B returnscursor toOK top row but cannot exit mode0; then A marksP1ready and commits. Root already returnedpregame and launchedstadium. Fixture `.local/input-test/buttons.txt`, app-only buttons a/b/start/up/down/left/right, release empty. Focus exactwindow77594639 then Spectacle capture. Never xdotoolkey or bypassKDE globalinputpermission.

PAL original boot now correctTV0 physical300; real SDK X/Yscale implemented; exactVIorigin->FBregistry fixes prior oddaddress/colorcorruption. Capture67cleanintro,71Career mainmenu,84widefield. Naturalhalftimeconfirmed; no completedmatch/Careerprogression/save-change restart acceptance yet. Remaining complete match, Career persistence, HUD/glyph/remap finalvisible checks, fieldGPU interpolation, resolutionactual output, clean production Linux copy/ROM-first and final Windows. Not1.0yet.

Linux clean production sources/runtime/RT64 built and candidate01 private but stale; rebuild latest before packaging. `.local/pal-package-preparation-02` explicit SDL2compat/SDL3/privatecleanD-Bus plus39 notices. Final fixture/evidenceOFF, no RPATH/personalpaths. Windowsprep `.local/windows-preparation-01` updated exact metadata02/PALROM and all current sources, transfercheck24811inputs~531MB/5testsPASS. NO Windows archive/SSH/power/reservation yet. Use maquinita-windows-recomps skill atfinalstage;192.168.68.111 userryarcade, HAhelperonly,lock/ownership rules. See privateREADME and skill.

## Historical notes below (may describe superseded checkpoints)

## Latest steering — PAL Career mode base review

The user has paused rendering implementation to consider the attached European ROM as the base in order to retain Career/RPG mode. Recommendation: use PAL as the principal base if Career is a 1.0 requirement, retaining the US work as a preserved reference. No base replacement or PAL runtime migration has been performed. No game execution is authorized by this review; the earlier test deferral remains in force.

The private candidate is `.local/inputs/pal-en-de/rom.z64` with `identity.json`: 16 MiB, SHA-256 `6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`, NISX revision 0, entry 0x80000400, CRC 336364A0/06C8D5BF. Imported from the user attachment with byte-order normalization only. Active `.local/rom.z64`, US configuration, generated functions and saves remain unchanged. The supplied edition is English/German; Spanish support would require separate investigation/work.

US evidence: settled main menu has eight entries and original handler 0x803C34B8 explicitly guards indices <8, dispatching [0,6,7,13,2,3,4,1] to game mode 0x80130854. Career is not exposed by that menu. US ROM nevertheless contains RPG narrative remnants; do not claim every Career asset/function was removed or unlock it by inventing a ninth menu case. See `docs/research/regional-base.md` and `docs/research/pal-migration-rendering.md` when available. The online manual labeled USA describes Career and English/German but contains American warranty material; it is not reliable regional proof by filename alone.

Migration must establish PAL-specific section/overlay maps, SDK bindings, timing/VI/audio behavior, private resource tables, game/save identity and layouts. Reuse portable host infrastructure where independently valid. Verify original PAL timing instead of retaining US 60 Hz assumptions; 120 fps is a presentation/interpolation target, not permission to accelerate simulation. Do not transfer US roster/texture offsets or saves blindly.

Rendering checkpoint before this pause: build 18 passed and includes resolution profiles and widescreen culling, but there has been no enhanced game run. Later transform-tracker/runtime/RT64 bridge integration in the working tree is incomplete and has not been rebuilt as a whole. Before resuming it, wire TransformMatrixBuilder and post-call flags_after into transform_runtime observations (the final tracker rejects their current default values), and retain frame_mutex through tracker.submit_task to prevent scene/frame token invalidation. Full camera-cut/replay/teleport epochs remain unresolved. Do not describe interpolated 120 fps as implemented or verified.

## User requirements and current status

Continue autonomously to a playable 1.0; parallel agents are authorized. Intermediate builds/runs Linux only. Build/package/test Windows only at the final stage; no Windows machine action has occurred. Separate final portable Linux/Windows folders remain pending. All actual game tests use visible desktop windows with real captures embedded in chat. No hidden game executions, fake screenshots or substitute gameplay.

Actual native original CPU and audio RSP render the introduction, title and original menus through RT64. Boot 12 reached a controllable match, original pause and Replay before the user deferred further game executions. **Release 1.0, a completed match and enhanced rendering remain unverified.** Acceptance record: `docs/releases/1.0-acceptance.md`.

New user request: plan selectable roster/team/flag/kit/jersey packages for later updates while keeping 1.0 first. Research is in [roster-database.md](docs/research/roster-database.md) and [team-visual-assets.md](docs/research/team-visual-assets.md). The future proposal is [roster-pack-plan.md](docs/research/roster-pack-plan.md); it is not an approved implementation specification. No package loader/selector is implemented. The factory player database is verified at 106 × 22 × 56 bytes; edited teams/save CRCs and team-to-visual consumer routes are documented. Do not assume 106 individually selectable national teams or identify unconfirmed texture banks as flags/3D jerseys.

## Current generation and build

- `.local/game-build/iss2000`, build 17: `.local/runtime-map-04/functions` plus `.local/native-metadata-09`. Generated 12,134 original CPU bodies plus one uniquely retained original SDK function; 66 registered sections and 53 reviewed host-service bindings.
- Strict compiler `.local/toolchain/N64Recomp`, pristine pinned source `.local/deps/N64Recomp`; strict full map still rejects `0x800031AC -> 0x801EFED0`. Separately receipted diagnostic compiler changes only all-call lookup policy. Unknown/inactive calls remain fatal; do not invent an entry or success stub.
- Map 04 includes three explicitly reviewed merged function extents from original jump-table guards/targets. Boot 09 team selection fault was a truncated function at `0x802A81F4`; actual selector 5 target `0x802A8288` is now compiled. Audit of 332 switches found no additional concretely truncated extent.
- Pinned runtime/RT64 source `.local/deps/N64ModernRuntime`, `.local/deps/rt64`; archives `.local/runtime-deps-build`, `.local/rt64-build`; original audio `.local/runtime-research-rsp/audio.cpp`. Linux SDL2-compat depends on SDL3.
- CMake uses `ISS2000_ENABLE_INPUT_TESTING=ON` for the app-only virtual SDL controller. MUST turn it OFF for final binaries.
- Build 17 predates the small MotorInit result-priority fix now in source; rebuild before claiming that fix is in the game binary.

Reproducible metadata generation MUST include retained original source:

```sh
python3 -m tools.prepare_native --rom .local/rom.z64 --sections .local/runtime-map-04/section-analysis.json --runtime-symbols config/recomp/runtime-symbols.json --retained-source .local/runtime-map-02/functions/func_80060550_resident.c --output .local/native-metadata-FRESH
```

The manifest binding for `0x80060550` pins original ROM bounds/hash and generated-source hash. `native_retained.cpp` exports `iss2000_original_80060550`; root calls that unique symbol. Boots 10/11 regressed because fresh mapping replaced the old public `func_80060550_resident` symbol with upstream's honest no-Pak wrapper. Both runs were alive and received A, but Data Change stage 14 looped on game storage error 8. Do not misdiagnose this as VI deadlock or bypass the save failure. Metadata 09 fixes the collision; independent review checked provenance, aliases, generated hashes and compilation.

## Live execution and evidence

At the earlier boot 12 checkpoint the game was running under GDB PTY session 6706 (PID may differ; inspect session). Close/resume it deliberately before another launch. Original save file from boot 09 was preserved. Boot 12 passes Data Change to the main menu and settled team selection after the retained-SDK fix. `PFS 0x801A2CCC.status = 1`; original note-state counters captured. Actual editor/mode save changes surviving another restart are still unverified.

Important captures under `.local/captures/`:

- 01 first-run ROM prompt.
- 07 original intro; 11 title sustained for 277 seconds after real AI FIFO fix.
- 14 original Expansion Pak enhanced-memory notice.
- 20 original game Saved confirmation (boot 09); original .mpk creation receipt `.local/runtime-research-pak/actual-menu-save-01.json`.
- 40 boot 12 main menu after reload, embedded in chat.
- 41 menu with actual procedural physical A/B icons; 44 settled USA/Canada team selection, embedded.
- 46 original Handicap. Subsequent captures continue from 47; inspect before making claims.
- 04 is NOT game evidence (app had crashed); 09 is desktop input permission, not gameplay. Earlier 25 was incomplete team transition and must not be used to classify asset pixels.

Fresh settled 8 MiB native-word-swapped RAM: `.local/team-visual-assets-01/settled-team-selection.rdram`. Earlier snapshots `.local/switch-research-01/team-select.rdram` and `.local/prompt-research-01/player-number.rdram` remain fixed historical evidence. Do not overwrite them.

## Implemented host work and limits

Verified ROM import ZIP/Z64/N64/V64, exact canonical SHA, portable first-run selector and atomic preservation of invalid stored input. Default data beside executable. CPU overlays activate after real bounded ROM DMA copy and before PI completion; strict 8 MiB validation and SRAM direction checks. Raw unimplemented DP/yield requests fail explicitly. RT64 home discovery disabled.

AI adapter models current+next descriptors and reports current length only, using actual SDL consumed-output frames; prevents negative original buffer sizes. Original audio/title stability captured; match timing and full interrupt fidelity still require testing.

Four logical ports, hotplug, optional per-action remapping, correct Xbox/PS/Switch labels and manual family fallback. `input-preferences.json`, `graphics.json` and Controller Pak settings persist portably. F5 footer, F6 family, F7 modal settings; no runtime pause API, so settings instruct pausing in original game first. Real physical-controller prompts/actions and rumble are not yet verified. Native menu A/B textures replace only guarded known CI4 icons while retaining original palette/draw routine; additional original instruction textures still require coverage.

Four persistent 32 KiB Controller Paks under `data/saves` use original SDK filesystem algorithms over reviewed block/status adapters; original isolated allocation/write/read/reopen/delete tested. Accessory selection is independent per port (Controller/None/Rumble) and defaults to a Controller Pak on P1. Never automatically format imported corrupt images; startup snapshots and backups preserved. The game cartridge save type is None; do not claim SRAM support is used. The source MotorInit adapter remaps only upstream NOPACK (1) to DEVICE (11) for a selected Controller Pak; preserves disconnected (4).

Graphics settings for 4:3/16:9, Original/720/1080/1440/2160 resolution and Original/60/120 refresh rate are wired to RT64. Current data profile original 4:3. Actual proper field projection, target dimensions up to 4K and scene-safe interpolation are pending. Primary display is 60 Hz, so actual 120 Hz measurement is unavailable here; do not report that as verified.

## Commands and verification

```sh
cmake -S . -B .local/game-build -DISS2000_GAME_GENERATED="$PWD/.local/runtime-map-04/functions" -DISS2000_NATIVE_METADATA="$PWD/.local/native-metadata-09"
cmake --build .local/game-build --target iss2000 -j4
ISS2000_ROM=.local/rom.z64 ISS2000_GAME=.local/game-build/iss2000 ISS2000_DIAGNOSTIC=.local/clean-native-build/iss2000-diagnostic python3 -m unittest discover -s tests -v
```

Latest full suite: 166 tests passed with all integration environment variables set, zero skips; log `.local/tests-integration-boot12.log`. Tests do not establish a controllable match.

Actual desktop/GPU runs require approved escalated tool environment with `DISPLAY=:0`, `GDK_BACKEND=x11 QT_QPA_PLATFORM=xcb SDL_VIDEODRIVER=x11`. Redirect inferior logs to private file under GDB. Historical LD_LIBRARY_PATH points to RT64 `dxc/lib/x64`; actual Linux uses embedded SPIRV and final packaging should verify it without developer paths. Activate exact window `ISS2000 | djultra64` then Spectacle capture, inspect and embed. Attaching to another process is restricted; launch GDB child instead.

KDE remote input-control permission appeared when sending X11 keys. User was asked to accept; never click/bypass that permission. App-only SDL virtual-controller test fixture controls only this app with `.local/input-test/buttons.txt` tokens start/a/b/up/down/left/right; release with empty file. This does not verify physical input. Fixture is prioritized as P1.

## Remaining

Reach and control a match; verify save changes/restart, original modes, audio transitions and full controller-family prompts. Validate graphics/interpolation with actual scene evidence. Produce portable Linux package with explicit runtime libs and notices, clean ROM-first import and copied-path verification. Only then use maquinita Windows skill for final Windows build/package/run; portable lookup bridge preparation is in `cmake/runtime_lookup_bridge.cmake` and `docs/runtime-lookup-bridge.md`, integration not complete. No Windows machine action yet.

All private ROM, extracted assets, generated original CPU code, builds, save files and captures remain ignored under `.local/`. Do not publish them. Source checkpoint pending; verify actual Git author and committer are `djultra64` before committing.

## Latest user priority — rendering work, execution tests deferred

The user now requests16:9 first, then720p through4K profiles, then120fps interpolation, and explicitly defers further game execution tests. Boot12 was closed deliberately; GDBsession6706 and gamePID95869 exited. Do not launch new game runs or Windows work while these tests are deferred. Compilation, unit checks and static original-data analysis continue.

Before closure boot12 reached actual field gameplay, responded to movement/action input, opened original P1pause and rendered Replay. Actual captures54(field),55(movement/action),56(P1pause),57(Replay). Captures54and56 were embedded in chat. This establishes the first controllable native match; it does not establish full match completion, graphicsenhancements or a finished1.0.

New paused original field snapshot `.local/team-visual-assets-01/paused-match.rdram` supports static rendering research. Rosterpack research now documents exact USA/Canada flag data matches in original compressed asset2A3 and palettes2A1;3Djersey/material ownership remains incomplete. Futurepackage implementation remains deferred.

Agent tasks: overlay_research implements guarded horizontalCPU-culling and rotated-worldcorner widening helpers after original22E58/243E0, based on exact originalcamera axes, with tests only. overlay_probe extends resolution profiles900p/1800p and accurateaspect-aware dimensions/default16:9 fornewsettings. runtime_research recovers stablecamera/entity/bone identities for scene-safeRT64interpolation. Root owns renderer/nativebridge/CMake. No one runs the game.

Root integrated new titleprompt adapter source/hook039F4 afterbuild17; not yetrebuilt/visuallyverified. It edits only original12-bytePRESSSTART storage toactualphysicalStartname; popupA encodedstrings discoveredbutnoadapterimplemented. See agents' docs for completedresearch.
