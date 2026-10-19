# ISS2000

Canonical working folder: `/home/alfredo/Documents/ChatGPT/ISS2000`.
Keep the repository, private inputs and build outputs here. Historical worktrees
under `.local/pre-relocation-20261015/` are evidence, not active checkouts.

Read the approved design under `docs/superpowers/specs` and the current milestone
record before changing code. Work on `codex/` branches. Run `git status --short`
first; preserve existing work. Other recomps are workflow/structure references
only. Do not actively compare their game binaries or transfer game-specific
patches. Analyze ISS2000 directly; upstream tools may be reused read-only.

Use `djultra64 <329694832+djultra64@users.noreply.github.com>` for own commits.
Preserve real upstream authorship and notices. Documentation is English.

Private ROM, assets, generated original game code, saves and execution captures
belong under ignored `.local/`. Never publish them or silently replace original
functions with success stubs. A native diagnostic is not a playable game.

Required enhanced target: proper 16:9, rendering up to 4K, interpolated 120 fps
with original simulation timing, Expansion Pak / 8 MiB RDRAM and per-port rumble.
Keep actions independent of physical button names; support four controller ports.

Verification: `python3 -m unittest discover -s tests -v`. Native diagnostics and
ROM integration are opt-in checks documented in the README; do not confuse skipped
integration tests with a verified game boot.

## Delivery and visible verification

The user requires separate portable Linux and Windows folders, kept in this
canonical project directory. Prompt for a user-supplied ROM on first launch;
keep configuration, saves and imported private data beside the executable.
Do intermediate development and verification on Linux. Build/package/test
Windows only at the final stage; use the Windows-machine skill then.
The latest explicit user instruction (2026-10-15) requires all remaining game
execution tests to use hidden windows. This supersedes the earlier visible-window
requirement. Use a private headless compositor/display; never expose or activate
test windows on the user desktop. Real GPU/compositor screenshots may still be
saved privately as evidence. Do not replace captures with mockups or call
diagnostics a playable version.

Controller prompts must use original game text/sprite rendering. The user explicitly rejects an independent controls overlay; do not restore the removed host footer or add a replacement overlay.

## Current correction pass (2026-10-15)

The user explicitly froze ALL Windows compilation until further notice. Continue
only Linux work; do not start Windows builds/tests/SSH work as part of this pass.
Reopen audio/performance acceptance and animation cadence independently from
translation counters. Compare ISS2000 against the same ROM in Ares or grounded
gameplay references. Redesign PC Settings and Remap to match the original green
Options art and exact typeface. Add native fullscreen selection. Hide console
accessory selection; saving and vibration must work transparently together.

All user-facing save flows must use PC game/save terminology. Remove Game Notes,
Controller Pak/Pack, Rumble Pak and console capacity labels from English UI. Keep
genuine saves, confirmations and meaningful error/recovery choices intact.

Controls redesign decision: preserve the original PS1 control types and their
numbering; latest user steering also allows Type 4 Modern. Remove the extensive
N64-button remapping UI. Verify original PAL KCEO PS1 types before implementing;
show football actions and active-device glyphs, without C-left/N64 terminology.

Latest controls clarification: the user chose WAIT FOR THE PS1 MANUAL before
closing/reworking controls, rather than implementing only Type 1 and Type 4 now.
Freeze controls implementation until that reference is available; continue the
authorized font/audio/animation/fullscreen/save corrections independently.


## Authoritative controls update — 2026-10-15 latest user decision

This update supersedes the earlier manual wait and Type 4 Modern proposal;
retain all historical notes as evidence. The user supplied primary PS1 videos
2026-10-15 18-59-43.mp4 and 2026-10-15 19-00-47.mp4 in Downloads.
Adapt the authentic pre-match/Training Controller screen; remove the extensive
raw N64 remapping and its Options entry. Keep Type 1 through Type 4 from PS1,
add Type 5 as an adapted current eFootball layout, then Free: six choices total.
Free edits football actions with actual device glyphs; Start confirms, with an
explicit English footer. All UI text remains English. The supplied stretched
videos are references only, never replacement UI assets.

Map by physical positions, accounting for Nintendo face-button swaps. Type 5
basic positions: Pass South, Shoot West, Lob East, Through North, Dash R2,
Cursor L1. OneTwo R1 and Curve L2 are ISS-specific adaptations, not a claim of
identical modern compound mechanics. Official reference:
https://img.konami.com/efootball/s/img/manual/efootball2023_ps5_en.pdf
Keep six host choices separate from the genuine N64 three-profile table.
Preserve four ports, original Cursor/Keeper behavior, saves, and real errors.
Windows remains frozen; game tests remain hidden; old portable folders and
user data remain preserved.


## Authoritative release update — 2026-10-18

The user explicitly reopened the final Windows stage for version 0.7. The earlier
Windows freeze is historical and superseded. Use the maquinita skill and hidden
execution for all Windows game checks. Preflight currently blocks physical
orders because the Sonoff and consumption sensor are unavailable; no power order
or Windows SSH was sent, and the own reservation was released. Repeat reservation
and preflight after recovery; never bypass the helper or substitute an old build.
All player names use documented 1999–2000 internationals where possible, with
nearby-year exceptions explicitly approved and listed in the name research record.
No agents: keep execution in this worker. Documentation remains English.
