# Portable runtime lookup bridge

Original project work: djultra64. Verified Linux checkpoint: 2026-10-15.

The game now supports a direct lookup symbol without GNU linker wrapping.
The existing checked project registry, overlay-identity checks and fatal unknown
lookup behavior are retained. A full original PAL executable linked successfully
in DIRECT mode on Linux; no game execution or Windows build is claimed here.

## Application modes

Set `ISS2000_RUNTIME_LOOKUP_MODE` when configuring the game:

| Mode | Project export | Runtime archive | Linker behavior |
| --- | --- | --- | --- |
| `DIRECT` | `get_function` | Source-specific upstream rename | Ordinary symbol resolution |
| `WRAP` | `__wrap_get_function` | Original unrenamed runtime | GNU `--wrap=get_function`; validated on Linux |
| `AUTO` | Resolved at configure | Must match resolved mode | WRAP on GNU/Clang Linux; DIRECT elsewhere, including Windows |

Unknown values fail configuration. DIRECT requires the bridge configuration
receipt from the chosen runtime build. WRAP rejects a runtime carrying that
receipt. Use separate fresh runtime build directories for the two modes.
The receipt records the original overlay source digest and rename scope;
configuration checks that the source still matches. It is configuration
provenance, not an archive integrity receipt. The private production receipt
separately hashes the built archives. Normal duplicate/undefined symbol failures
remain enabled; no `FORCE:MULTIPLE`, weak-symbol fallback or SDK stub is used.

`native_game.cpp` changes only the exported function name under
`ISS2000_LOOKUP_DIRECT`; its existing registry body executes in both modes.
Unmapped, inactive or unsupported guest destinations continue to fail explicitly.
The bridge does not make a missing original function successfully return.

## Source-specific runtime build

Pinned `librecomp/src/overlays.cpp` defines upstream `extern "C" get_function`.
The build hook adds `get_function=iss2000_upstream_get_function` to that source
alone, using the source property's actual target directory. It does not rename
references in thread dispatch or other runtime translation units. The original
upstream function remains separately available. Dependency files stay pristine.

Append these arguments to a fresh pinned-runtime configuration:

```text
-DCMAKE_PROJECT_INCLUDE=/absolute/path/ISS2000/cmake/runtime_lookup_bridge.cmake
-DISS2000_RUNTIME_LOOKUP_BRIDGE_AUTO=ON
```

The hook defers until the top-level configuration has created `librecomp`.
Preserve any existing project include hook by including this file from that
hook instead of replacing it. Alternatively, include the file and call
`iss2000_enable_runtime_lookup_bridge(librecomp)` after adding the runtime
subdirectory. The call is idempotent and requires exactly one `overlays.cpp`.
Its receipt is `<runtime-build>/iss2000-runtime-lookup-bridge.json`.

Finish building the dependency before configuring the game: its existing archive
inventory records the archives present at configure time. Fresh single-config
Ninja build directories avoid mixing Debug/Release archives. Game CMake accepts
both `.a` and `.lib` archives, keeps GNU archive groups on compatible linkers,
and uses ordinary library linking for MSVC/clang-cl. DBus remains Linux-only.
Other Windows SDK/import-library requirements still need actual Windows linking.

## Linux verification

Eight focused tests configure, compile and link real temporary static-library
fixtures. An independent runtime thread caller reaches the project symbol;
unknown addresses terminate with the fixture's explicit failure status. The
renamed upstream function and another symbol in its same object remain callable.
Explicit/deferred hooks, idempotence, scope, missing sources, mismatched archive
modes and invalid mode values are checked. These tests do not execute the game.

```text
python3 -m unittest tests.test_runtime_lookup_bridge -v
```

All eight passed. A full project discovery run at this checkpoint ran 261 tests:
251 passed and 10 opt-in checks skipped. This does not replace root's separately
recorded integration-enabled suite or visible game acceptance.

The separately built pinned runtime `.local/runtime-direct-build` renamed exactly
one translation unit, confirmed through `compile_commands.json`. The actual
PAL executable `.local/pal-direct-build/iss2000`, using metadata generation 02,
linked with no wrap option. Its SHA-256 at this checkpoint is
`3d813a9b2bcec4f50d17c557cb96df2f2e7b90ae79da498408d0c98e20de7090`.
Final symbol inspection found exactly one project `get_function`, exactly one
`iss2000_upstream_get_function`, and no `__wrap_get_function`.
This development executable was neither launched nor packaged by this task.

The fresh `.local/runtime-production-build` contains eight completed archives.
Every C/C++ compile command has both file/macro prefix maps for the two canonical
project paths, mapping them to `ISS2000`. Byte inspection of all eight archives
found no personal `/var/home` or `/home` user paths. Only `overlays.cpp` receives
the lookup rename, and the pinned runtime checkout remains clean at commit
`cdf5abbd5026fef5c364c676e4667c45e42b6863`. Private archive hashes and symbol proof
are in `.local/runtime-production-build/iss2000-production-receipt.json`.
Select this dependency using `ISS2000_RUNTIME_BUILD` and explicitly choose DIRECT.
That receipt describes dependency outputs; final executable path/symbol checks
still belong to the final production build.

## Remaining Windows verification commands

These are final-stage commands, not a Windows result. Run from the copied project
root in an x64 developer PowerShell with the Windows SDK, LLVM/clang-cl, CMake,
Ninja and Python available. Keep pinned submodules and the verified private CPU,
ROM and retained-original inputs; do not copy Linux archives as Windows inputs.
The SDL2 configuration below is the x64 SDK already supplied by pinned RT64.
Use fresh output directories. Preserve the separate Linux builds and saves.

```powershell
$Project = (Get-Location).Path.Replace('\', '/')
$SDL2 = "$Project/.local/deps/rt64/src/contrib/mupen64plus-win32-deps/SDL2-2.26.3/cmake"
cmake -S "$Project/.local/deps/N64ModernRuntime" -B "$Project/.local/runtime-windows-direct" -G Ninja `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl `
  "-DCMAKE_PROJECT_INCLUDE=$Project/cmake/runtime_lookup_bridge.cmake" `
  -DISS2000_RUNTIME_LOOKUP_BRIDGE_AUTO=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$Project/.local/runtime-windows-direct" --parallel 4
cmake -S "$Project/.local/deps/rt64" -B "$Project/.local/rt64-windows" -G Ninja `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl -DRT64_STATIC=ON
cmake --build "$Project/.local/rt64-windows" --parallel 4
py -m unittest tests.test_runtime_lookup_bridge -v
py -m tools.prepare_native --rom .local/inputs/pal-en-de/rom.z64 `
  --sections .local/pal-map-bound-01/section-analysis.json `
  --runtime-symbols config/recomp/iss2000-pal-en-de-rev0/runtime-symbols.json `
  --retained-source .local/pal-runtime-01/functions/func_80060DD0_resident.c `
  --output .local/pal-native-metadata-windows
cmake -S "$Project" -B "$Project/.local/pal-game-windows" -G Ninja `
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-cl -DCMAKE_CXX_COMPILER=clang-cl `
  -DISS2000_BUILD_GAME=ON -DISS2000_ROM_REVISION=iss2000-pal-en-de-rev0 `
  "-DISS2000_N64RECOMP_SOURCE=$Project/.local/deps/N64Recomp" "-DSDL2_DIR=$SDL2" `
  "-DISS2000_RUNTIME_BUILD=$Project/.local/runtime-windows-direct" `
  "-DISS2000_RT64_BUILD=$Project/.local/rt64-windows" `
  "-DISS2000_NATIVE_METADATA=$Project/.local/pal-native-metadata-windows" `
  -DISS2000_RUNTIME_LOOKUP_MODE=DIRECT -DISS2000_ENABLE_INPUT_TESTING=OFF `
  -DISS2000_ENABLE_RENDER_EVIDENCE=OFF
cmake --build "$Project/.local/pal-game-windows" --target iss2000 --parallel 4
```

The bridge tests recognize `cl`/`clang-cl` with Ninja on Windows; the GNU WRAP
execution test deliberately requires Linux. Reject an entirely skipped test run.
Review exact compile commands, symbols and retained original-code receipts on the
actual Windows toolchain. With MSVC tools, inspect the compiled objects/archive:

```powershell
dumpbin /symbols "$Project/.local/runtime-windows-direct/librecomp/librecomp.lib" | Select-String 'get_function'
dumpbin /symbols "$Project/.local/pal-game-windows/CMakeFiles/iss2000.dir/src/runtime/native_game.cpp.obj" | Select-String 'get_function'
```

Require the upstream archive definition under its renamed symbol, the project
object's ordinary `get_function` definition, and external runtime calls resolving
to the project's registry in the final executable. Inspect the actual filenames
if the chosen toolchain uses a different archive prefix. Any missing Windows
system/import libraries or compiler compatibility failure must be resolved and
relinked normally. Then verify final source-path mapping, required DLLs, clean
portable-folder import/save behavior and visible original-game execution before
claiming Windows acceptance or packaging. None of those steps has run here.
