# Portable Linux and Windows folders

All development inputs and final portable folders stay inside the canonical
`/home/alfredo/Documents/ChatGPT/ISS2000` project. Native binaries, private game
material and captures remain under ignored `.local/` during development.
Packaging is separate from game verification: a copied executable does not prove
an authentic title screen, controllable match, audio, saves or enhanced rendering.

`tools.package_portable` copies only the executable, each explicitly supplied
shared library, and explicitly named UTF-8 text notices. It does not scan source folders or discover transitive libraries.
It never gathers ROMs, assets, generated source, previous saves or research
captures. Select required redistributable dependencies explicitly; do not copy
the operating system's C library or graphics-driver installation into a package.
Keep applicable dependency license notices with any eventual distribution.

## Layout and portable data

Linux places the executable beside `launch.sh`, dependencies under `lib/`, and
creates empty `data/` and `screenshots/` directories. The launcher derives its
own absolute folder, changes into that folder, prepends its `lib/` to
`LD_LIBRARY_PATH`, and preserves arguments verbatim. Spaces in installation
paths and executable names are supported.

Optional `--notice SOURCE=DESTINATION_FILENAME` arguments copy exact notice bytes
into `licenses/`. The Python API accepts `notices=[(source, destination_name)]`.
Destination names cannot contain directories, Windows reserved names, or trailing
spaces/dots. Duplicate names are rejected case-insensitively on both platforms.
Binary notices and notices larger than 1 MiB are rejected before output creation.
Source license authorship is preserved unchanged. The packager does not discover
or certify a complete license set.

Windows places the `.exe` and explicitly supplied `.dll` files together at the
folder root, with the same empty data and screenshots directories. Creating a
Windows layout neither builds nor runs Windows software.

The application contract is a first-run ROM picker, followed by settings and
saves under `data/` beside the executable. The application must derive this base
from its executable location rather than the caller's current directory. The
packager creates that layout; it cannot add those behaviors to an arbitrary
input executable. Root `README.txt` describes the intended launch and data use.

Input dependency symlinks are resolved and copied as regular files under the
requested library filename; original inputs remain untouched. Libraries require
platform-appropriate filenames (`.so`, `.so.1`, and similar numeric versions for
Linux; `.dll` for Windows). Duplicate destinations, including case-insensitive
Windows duplicates, are rejected. Validation finishes before output creation;
copy failures remove the newly created partial folder. Existing outputs and
symlinked output paths are refused.

## Creating a folder after runtime verification

From the canonical project folder, create the package parent once:

```sh
mkdir -p .local/portable
```

Supply the actual verified executable and each selected Linux dependency. The
paths below are explicit placeholders, not claims that those builds exist:

```sh
python3 -m tools.package_portable \
  --platform linux \
  --executable /absolute/path/to/iss2000 \
  --library /absolute/path/to/libSDL2-2.0.so.0 \
  --output .local/portable/linux
```

Repeat `--library` for additional reviewed dependencies, or omit it when none
are required. Output must be fresh, disjoint from every input, and have an
existing parent. Do not package the entry diagnostic as a playable game.

Windows compilation, packaging and actual testing belong to the final Windows
stage, after the Linux runtime works. Do not power on or use the Windows build
machine prematurely. The later packaging command has the same explicit-input
contract:

```sh
python3 -m tools.package_portable \
  --platform windows \
  --executable /absolute/path/to/ISS2000.exe \
  --library /absolute/path/to/SDL2.dll \
  --output .local/portable/windows
```

## Evidence and remaining verification

Synthetic tests execute the Linux launcher from another working directory with
spaces in paths, verify arguments and library search paths, preserve source
files, and check validation/copy-failure cleanup. Windows layout checks only
copy synthetic bytes; no Windows executable is built or run by those tests.

```sh
python3 -m unittest discover -s tests -p test_package_portable.py -v
```

Actual runtime acceptance must be visible and include the first-run ROM picker,
settings/save persistence after restart, title-to-match control, sound, and the
requested Linux and eventual Windows environments. No playable portable package
or actual Windows validation is established by the packaging tests.


## Current Linux dependency inventory

The historical `.local/packaging-inventory.json` records the initial inventory.
The current `.local/packaging-inventory-final.json` checkpoint records explicit
source paths, SONAME destination names, development executable/library hashes,
required symbol versions and 39 explicit notice inputs. The production binary
hash is deliberately unset until the input-testing fixture is disabled and the
final executable is rebuilt. It describes the current development build,
not a package manifest that has passed runtime acceptance. Recompute it after
changing dependencies or compiler settings.

For the inspected build, `ldd` finds `libSDL2-2.0.so.0` and `libdbus-1.so.3`
under Linuxbrew, plus the host C/C++ runtime. This SDL2 is **sdl2-compat**, which
opens `libSDL3.so.0` dynamically; SDL3 must also be supplied explicitly even
though the executable's `ldd` output does not list it. Pass the SONAME symlink
paths to `--library`, not their resolved versioned basenames. The packager
resolves their contents while preserving the supplied filename in `lib/`.
Those three library files currently depend only on host libc/libm and the ELF
loader. SDL3 also loads system desktop/audio/input backends as available; the
three-file list does not provide a graphics driver or an entire desktop stack.

The executable requires `GLIBC_2.38` and `GLIBCXX_3.4.32` symbols and is compiled
with SSE4.1. This is a compatibility floor for this particular build, not a claim
of support for every Linux distribution. A package relying on host libstdc++
needs that symbol version. Bundling reviewed `libstdc++.so.6` and `libgcc_s.so.1`
can address C++ runtime availability, but their own glibc requirements and notices
must be checked. Do not bundle glibc, the ELF loader, or graphics drivers. A lower
glibc target requires building against an older compatible baseline.

The launcher's `LD_LIBRARY_PATH` selects `app/lib` before the inspected binary's
Linuxbrew RUNPATH and allows SDL2-compat to find packaged SDL3. This must still
be checked against the assembled folder with the actual selected libraries.

Linux RT64 does **not** load DXC at runtime in this pinned build:
`DynamicLibraries::load()` and `ShaderCompiler` perform DXC loading only under
`_WIN32`. Build-time DXC emits SPIR-V which CMake converts into compiled C blobs.
There is no Linux `libdxcompiler.so` search path to patch, and copying the shader
build directory is unnecessary. ImGui uses its embedded ProggyClean font and the
controller overlay draws its symbols as geometry; no external font files are
required. Preserve the embedded font's own notice in addition to ImGui's license.
The Windows DXC DLL requirements remain separate and need final-stage review.

The current checkpoint includes complete nlohmann JSON 3.12.0 and ProggyClean
MIT texts from their official upstream repositories, plus the full D-Bus AFL 2.1
and GPL 2.0-or-later alternatives from the official SPDX license-text repository.
Original attribution notices remain separate inputs. Paths, URLs and byte
digests are pinned in the private inventory. N64ModernRuntime's
GPL license and any corresponding-source requirements remain applicable;
collecting license texts alone does not resolve those obligations. No original
game material is added by the explicit notice workflow.


### C++ runtime choice and release gate

The three selected app-library inputs remain `libSDL2-2.0.so.0`,
`libSDL3.so.0` and `libdbus-1.so.3`. The current recommended checkpoint uses
the host C++ runtime with the stated `GLIBCXX_3.4.32` requirement. Both inspected
optional host GCC 15 libraries (`/lib64/libstdc++.so.6` and
`/lib64/libgcc_s.so.1`) additionally require `GLIBC_ABI_GNU2_TLS`. Bundling those
files changes the compatibility contract: numeric glibc 2.38 alone no longer
describes it. The inventory records their exact needed versions and hashes,
with GPL 3 and GCC Runtime Library Exception 3.1 texts if they are selected.
Do not strip the ABI requirement or bundle glibc to hide it. The upstream linker
documents that this tag rejects incompatible runtimes rather than permitting
silent GNU2 TLS failures. See the [GNU binutils explanation](https://sourceware.org/pipermail/binutils/2025-August/143487.html).

All 12 focused synthetic packaging tests pass at this checkpoint. Review of the
explicit-input implementation confirms fresh empty `data/` and `screenshots/`,
SONAME symlink contents copied under the requested SONAME, and no discovery of
ROMs/assets/saves. No actual final package was assembled and no game was run by
this inventory task. Final packaging still requires a production binary hash,
`ISS2000_ENABLE_INPUT_TESTING=OFF`, actual assembled dependency resolution, clean
portable data and copied-folder acceptance. Corresponding-source and remaining
per-source notice review must be finished before external distribution; this
file does not certify legal completeness. Release preparation is paused while
the user-prioritized widescreen/resolution/interpolation work proceeds.

## PAL preparation checkpoint

The selected native profile is `iss2000-pal-en-de-rev0`: European revision0,
English/German cartridge, with English selected for this release. Its exact
canonical ROM SHA-256 is
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
The original root entries of the private inventory describe the earlier US-era
`.local/game-build/iss2000` development executable. They must not be used as the
PAL release executable identity. Its `pal_preparation_review` records the new
candidate and remaining checks while preserving the historical evidence.

The PAL application derives `data/` from its executable location and opens the
ROM picker before creating or importing game data when that folder is empty.
It validates the selected PAL digest and stores the imported canonical bytes as
`data/iss2000-pal-en-de.z64`. PAL Controller Pak files are isolated under
`data/saves/iss2000-pal-en-de-rev0/`. There is no automatic migration of the
preserved US ROM or US Pak files. The packager creates fresh empty directories
and copies none of those development files. A final package must identify this
supported revision and executable digest explicitly; the private inventory,
which includes developer source paths, is not a distributable package manifest.

At this checkpoint all3 selected library inputs and39 notice inputs still match
the inventory digests. The PAL development binary still enables the controller
test fixture and contains embedded dependency `__FILE__` source paths plus a
Linuxbrew absolute RUNPATH. The generated launcher and README themselves contain
no developer paths, but copying this executable preserves its embedded paths.
A clean production build requires source-path remapping for both project and
linked dependencies, disabling the input fixture, and reviewing the final Linux
RUNPATH. Stripping debug information alone does not remove `__FILE__` strings.
Reinspect the resulting executable before establishing the final package hash.
No final package was created by this review.

Windows executable and DLL destinations now reject reserved device names,
including `CON.exe` and `NUL.dll`, before creating output. All14 synthetic
packaging tests pass. These tests create temporary layouts only.

The [runtime lookup bridge](runtime-lookup-bridge.md) now has an integrated
DIRECT mode for Windows: a fresh runtime archive renames the upstream symbol in
`overlays.cpp` alone, the project exports actual `get_function`, and GNU
`--wrap=get_function` is excluded. The runtime bridge receipt and source hash are
checked before application configuration. The Linux WRAP mode remains separate.
Synthetic link tests verify the source-specific rename and reject mixed modes;
they do not establish a successful Windows build. No Windows machine or Windows
compiler was used for this preparation.

## Build metadata and guarded production preparation

Every portable folder now includes `build-info.json` with schema1, selected ROM
revision/digest/size/cartridge identity, English language, `djultra64` attribution,
and SHA-256/size for each copied file. Its file keys are relative package paths;
it contains no developer input paths. The copied executable, libraries, notices,
README and Linux launcher are covered. The JSON does not hash itself. The default
revision is PAL; preserved US preparation requires explicit
`--revision iss2000-us-rev0`. The README states the selected revision and digest.

Ordinary layouts are labeled `development`, with unknown input-fixture status.
`--release --build-dir BUILD` labels inputs `production-prepared` only after
checking the matching CMake revision, explicit
`ISS2000_ENABLE_INPUT_TESTING=OFF`, executable location within that build, and an
executable timestamp at least as new as its CMake cache. Missing, stale, unrelated
or fixture-enabled builds are rejected before output creation. This is a build
configuration check, not an independent proof that arbitrary supplied binaries
implement their cache settings. Runtime acceptance remains explicitly unclaimed
by package metadata.

Production preparation also rejects embedded Linux/macOS/Windows developer home
paths in executable/library bytes. This catches personal `__FILE__` strings and
Homebrew home-directory RUNPATH strings; it does not replace a complete runtime
search-path audit. Rebuild sources/dependencies with path mapping and review
`readelf -d` before packaging. All21 focused synthetic package tests pass.

## Clean PAL dependency inputs

The current clean private staging folder is
`.local/pal-package-preparation-02`. It contains only3 explicitly selected runtime
libraries,39 authentic notice files and private preparation scripts/receipts.
The preparation scripts and receipts are not copied into the eventual package.
It contains no ROM, save, game asset or game executable yet.

Selected libraries are system `sdl2-compat 2.32.64` and `SDL3 3.4.0`, plus a new
private D-Bus1.16.2 build. All79 SDL symbols imported by the current PAL executable
are exported by the chosen SDL2 compatibility library. A library-only version
probe loaded that compatibility layer and the staged SDL3 without initializing a
window or the game. All25 D-Bus symbols imported by the PAL executable are exported by the rebuilt
library. All3 libraries have no
embedded home paths and no RPATH/RUNPATH, and need only host libc/libm. Their
maximum numerical glibc requirement is `GLIBC_2.38`; both SDL libraries also
require the explicit loader ABI tag `GLIBC_ABI_DT_RELR`. The final executable's C++
requirements must still be inspected separately. No glibc, loader, driver,
systemd library or desktop backend is bundled.

The D-Bus original source archive was fetched from Debian's
[original-source mirror](https://packages.debian.org/stable/source/dbus), with
SHA-256 `0ba2a1a4b16afe7bceb2c07e9ce99a8c2c3508e5dec290dbb643384bd6beb7e2`,
matching its `.dsc` SHA-256 entry. The unmodified source is1.16.2 from the
[upstream release series](https://dbus.freedesktop.org/releases/dbus/).
Meson1.8.5 builds it with `/usr`, `/etc`, `/var`, `/run` defaults, systemd and X11
auto-launch disabled, public API usage checks enabled, and source paths mapped.
Only libc is needed by the result. All6 upstream library tests pass. The source,
Meson configuration, compiler commands and logs remain private under
`.local/portable-dependencies-01`. Package notices use the actual selected system
SDL license files and original D-Bus `COPYING`, preserving their authorship.

The previous Homebrew3-library inputs are retained as historical inventory, not
selected production inputs. Their absolute RPATHs and D-Bus socket/machine-id
prefixes are the reason they were replaced; no installed dependency was edited.

## Exact next Linux commands

From the canonical project root, the prepared script builds fresh runtime,
renderer and PAL executable directories with source-path mapping, no build RPATH,
and input testing disabled. It deliberately refuses existing output directories:

```sh
sh .local/pal-package-preparation-02/build-linux-production.sh
```

This script is prepared but has not been executed by the packaging work. It does
not launch a game. Root integration may choose equivalent independently reviewed
fresh build directories; preserve the same profile and path-mapping settings.
After the production executable and copied-library runtime acceptance are ready:

```sh
mkdir -p .local/portable
python3 .local/pal-package-preparation-02/package-linux.py \
  .local/pal-production-build .local/portable/ISS2000-Linux
```

The runner verifies every staged input hash, supplies the explicit clean libraries
and39 notices, and invokes the guarded PAL package API. `data/` and `screenshots/`
start empty. It creates no archive and launches no executable. Visible ROM-first
import, input, rendering, sound and save acceptance still belong to the root
verification work. Windows compilation remains a later separate action.


## Final Windows source preparation

Private scripts and authentic SDK inputs are prepared under
`.local/windows-preparation-01`; its README records exact final commands and
remaining SDK/toolchain inputs. Nothing in that preparation reserves or powers
on the machine. Root must complete Linux acceptance and explicitly start the
final Windows stage under the maquinita workflow before executing them.

The project now owns SDL main startup and obtains the Windows HWND and actual
owning thread through SDL's versioned native-window interface. The Windows link
block explicitly retains RT64's SDK/DXC links and the native dialog COM/shell
links that were lost when flattening upstream static archives. Host synthetic
compilation/configuration tests cover these changes; the actual Windows compiler
and runtime are still pending.

The final scripts use x64 Visual Studio SDK plus clang-cl, DIRECT runtime lookup,
PAL original sources and input testing disabled. A private RT64 source derivative
receipts the approved official DXIL validator replacement while leaving the
pinned dependency intact. They select vendor SDL2, the DXC compiler/validator and
specific VS C++ runtime DLLs, inspect their import closure, and require authentic
selected runtime notice text. Current38 Windows dependency notice inputs are
pinned privately; the installed VS runtime notice is a final-stage input.
The portable package contains no original ROM, research assets, saves or another
game's binaries. The separate **private build-input transfer** includes exactly
the hash-pinned user-owned PAL ROM at `.local/inputs/pal-en-de/rom.z64`, because
the reviewed sky source generator verifies it at compile time. This archive
must remain private and must never be copied into a release folder or published.
The recipe's `--check` mode validates current inputs without freezing an archive;
`--archive` is reserved for the final authorized transfer. The build explicitly
selects metadata02 with54 bindings and passes `ISS2000_PAL_ROM`.
