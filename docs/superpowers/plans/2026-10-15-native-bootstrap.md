# ISS2000 Native Bootstrap Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Establish reproducible ROM import, executable-code metadata, and an honest native diagnostic before integrating a complete playable runtime.

**Architecture:** Normalize and verify the supplied ROM; identify functions using disassembly and SDK fingerprints; generate C through the pinned N64Recomp. An explicitly diagnostic host exercises original entry code and verifies memory behavior without representing simulated OS services as a running game.

**Tech Stack:** Python standard library, Rabbitizer/spimdisasm, N64Recomp, CMake, C++20.

**Spec:** `../specs/2026-10-15-iss2000-design.md`

**Execution checkpoint:** importer, controlled tool build, deterministic entry/buffer generation and native diagnostics are implemented. Tasks 1–3 deliver a verified bootstrap checkpoint. Task 4 reached a reproducible resident-map translation failure at external target `0x801B050C`; full-runtime integration remains open. See `docs/milestones/M0.md` and `HANDOFF.md` for actual results and continuation. The later user instruction discontinues active cross-ROM comparison; analyze ISS2000 directly.

## Global Constraints

- USA rev0 canonical SHA-256 `e18e87c062a66002c0cbd7e2dd793ef755609e70675d5679df0396d4b6c67850`.
- Enhanced target: 16:9, up to 3840 × 2160, interpolated 120 fps; guest simulation cadence is preserved.
- Guest RDRAM target: 8 MiB; accessory design includes four controller ports and rumble.
- ROMs, generated original game code, assets, saves and private execution evidence remain ignored.
- Project documentation is English; own commits use djultra64; other projects remain read-only.

## Review Focus

1. Mislabeled byte-order extensions must normalize by magic, not suffix.
2. ZIP ambiguity, truncation and excessive decompressed sizes must fail before output mutation.
3. Existing destinations and symlinks must not cause source overwrite.
4. Static candidates and SDK guesses must not be presented as established runtime behavior.
5. A diagnostic must fail when real original memory clearing or entry transfer is wrong, and must explicitly identify its unimplemented OS boundary.

## Task 1: Verified importer and audit

**Files:** `tools/rom.py`, `tests/test_rom.py`, `config/roms/iss2000-us-rev0.json`.

**Interfaces:** `normalize(data: bytes) -> bytes`; `validate(data: bytes) -> dict`; `import_rom(source: Path, destination: Path) -> dict`.

- [ ] Test all three byte orders with a synthetic aligned image and exact canonical expected bytes; reject bad magic, odd/truncated size and unsupported revision.
- [ ] Test ZIP ambiguity, a decompressed member exceeding 16 MiB, destination collisions and symlinks using real temporary files. Test successful import against the user's real ROM as an opt-in integration run.
- [ ] Run `python3 -m unittest discover -s tests -v`; observe missing importer failure.
- [ ] Implement normalization, exact revision validation and exclusive creation after all input checks. Emit checksums, header and microcode inventory as JSON.
- [ ] Run the full suite and import the supplied archive twice into separate private destinations; compare hashes. Commit implementation and tests.

## Task 2: Deterministic metadata and recompiler invocation

**Files:** `tools/recompile.py`, `tests/test_recompile.py`, `config/dependencies.json`, `config/recomp/boot.json`.

**Consumes:** canonical image from Task 1.

**Produces:** ignored TOML symbols and generated C, with tool commit and executable digest in the generation receipt. Preserve exact original entry bytes; no gameplay patching.

- [ ] Test metadata rejects unaligned/overlapping/out-of-ROM functions and unsupported ROM bytes before launching a tool; test deterministic metadata rendering.
- [ ] Observe failing tests, implement the smallest validated generator, rerun suite.
- [ ] Resolve the pinned recompiler source and build input identity; run N64Recomp for the original `0x80000400` entry stub.
- [ ] Generate twice and compare generated C digests; record the actual generated call boundary. Broader mapping stays explicitly provisional until validated. Commit.

## Task 3: Native entry diagnostic

**Files:** `src/diagnostic.cpp`, `CMakeLists.txt`, `tests/test_native.py`, `docs/milestones/M0.md`.

**Consumes:** original generated entry function and pinned runtime headers from Task 2.

**Produces:** a diagnostic executable, not a game executable, reporting original entry/BSS results, 8 MiB allocation and the stop boundary before OS/game initialization.

- [ ] Write an integration check that fails without the executable and checks real process status and result JSON, including BSS sentinels, stack and transfer target.
- [ ] Build with CMake; execute actual original recompiled code against sentinel-filled 8 MiB RDRAM. Dispatch only the documented continuation boundary to a diagnostic observer; every other target aborts.
- [ ] Verify changed code or wrong boundary fails. Run full suite and deterministic generation comparison.
- [ ] Record remaining full-runtime blockers precisely; do not substitute a no-op graphics/audio/runtime implementation for success. Commit.

## Task 4: Runtime integration follow-through

**Files:** `docs/research/runtime-integration.md`, runtime source/config as justified by evidence.

- [ ] Expand code/data mapping with SDK-function evidence and record compressed/overlaid code findings.
- [ ] Attempt the full CPU translation using verified text limits; record unresolved indirect and privileged instructions by address.
- [ ] Integrate real runtime services only after their guest ABI and addresses are established. A complete native title screen and controllable match are M1 acceptance, distinct from the M0 diagnostic.
- [ ] Preserve progress in Git and a source-only checkpoint, with actual test/build commands and remaining gaps.

## Execution decision

The user's `Sí, hazlo` approves the technical design and directs implementation. Execute inline in this session; do not introduce another approval cycle for routine reversible local work. Keep public publishing out of scope.
