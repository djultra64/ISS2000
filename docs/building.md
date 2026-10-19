# Building ISS2000

Original project work: **djultra64**.

The current supported game build targets `iss2000-pal-en-de-rev0` (PAL English).
Dependency revisions and toolchain requirements are pinned in
[`config/dependencies.json`](../config/dependencies.json). Use the exact pinned
N64Recomp, N64ModernRuntime, RT64 and their dependencies; changing revisions can
invalidate the private source and renderer derivative receipts.

## Private prerequisites

Supply your own verified ROM. Original CPU and RSP translations, boot sources,
section analysis and metadata must be generated locally and stay under ignored
`.local/`. They are not included in this repository or a release archive. See
the [development journal](development-history.md),
[native input identity](research/native-build-inputs.md), and public `tools/`
modules for provenance and generation steps. This is a research build workflow;
a clean checkout alone does not contain the original game's build inputs.

The tested final Linux configuration uses Release, PAL metadata revision 04,
the direct runtime lookup mode, the production runtime and RT64 builds, and both
`ISS2000_ENABLE_INPUT_TESTING=OFF` and `ISS2000_ENABLE_RENDER_EVIDENCE=OFF`.
The game CMake configuration requires explicit paths for:

- `ISS2000_GAME_GENERATED`: verified original PAL CPU source directory.
- `ISS2000_GENERATED`: original boot translations.
- `ISS2000_NATIVE_METADATA`: verified PAL metadata and native bindings.
- `ISS2000_AUDIO_GENERATED`: verified original RSP audio translation.
- `ISS2000_PAL_ROM`: private exact PAL ROM, used by build-time identity guards.
- `ISS2000_N64RECOMP_SOURCE`, `ISS2000_RUNTIME_SOURCE`, `ISS2000_RT64_SOURCE`:
  pinned dependency source checkouts.
- `ISS2000_RUNTIME_BUILD`, `ISS2000_RT64_BUILD`: matching dependency builds.

Configure with `ISS2000_BUILD_GAME=ON`,
`ISS2000_ROM_REVISION=iss2000-pal-en-de-rev0` and
`ISS2000_RUNTIME_LOOKUP_MODE=DIRECT`. CMake verifies original input receipts and
prepares authenticated private derivatives; it fails on stale inputs. Build the
configured tree with `cmake --build <build-directory>`.

## Checks and packaging

Run `python3 -m unittest discover -s tests -v`. Private integration checks also
accept `ISS2000_ROM` (historical US input), `ISS2000_PAL_ROM` and `ISS2000_GAME`
(the executable, with its matching library path). Without these, the relevant
tests explicitly skip. Historical NTSC native diagnostics are separate from
current PAL gameplay checks.

Validate the factual player-name table with
`python3 -m tools.generate_pal_real_names --check`. Public source and release
packages must exclude ROMs, extracted original assets, original generated game
source, saves and private captures. Use `python3 -m tools.package_portable --help`
for explicit executable, dependency and notice inputs. A package manifest records
hashes; packaging by itself does not establish runtime acceptance.

The prepared Linux binary requires GLIBC 2.38 / GLIBCXX 3.4.32 or newer.
Windows uses the pinned Microsoft/LLVM toolchain and authentic redistribution
notices for the selected dependencies. Windows 0.7 compilation is still pending;
no successful Windows 0.7 build or runtime claim is made here.
