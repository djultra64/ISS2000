# ISS2000

Read the approved design under `docs/superpowers/specs` and the current milestone
record before changing code. Work on `codex/` branches. Run `git status --short`
first; preserve existing work. Other game projects are read-only references.

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
