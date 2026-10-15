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
Actual game execution tests must use visible desktop windows. Save real
screenshots privately and embed them in the chat so the remote user can follow.
Do not replace captures with mockups or call diagnostics a playable version.

Controller prompts must use original game text/sprite rendering. The user explicitly rejects an independent controls overlay; do not restore the removed host footer or add a replacement overlay.
