# ISS2000 save storage evidence

Original project work: djultra64.

## Verified behavior and limits

The native launcher currently configures `recomp::SaveType::Sram`. This is a
**provisional backend selection**, not evidence that the original game has used
cartridge SRAM or that saving works. No actual in-game menu save/restart round-trip has been verified. An isolated original-SDK storage round-trip is described below.
The initial baseline controller profile exposed no Controller Pak storage. The
new persistent device implementation is described below; a Rumble Pak remains
a different accessory and is not writable save storage.

Do not infer the active save device from the resident `SRAM DEBUG` and `SRAM INIT`
strings alone. Inspection of the original supported ROM establishes:

- `SRAM INIT` dispatches to guest function `0x80043B98`. Its loop calls
  `0x80061780` with queue `0x801A6678`, channel zero, block indices `0..39`, a
  32-byte buffer and force flag one. This is the Controller Pak RAM write ABI
  (`__osContRamWrite`), using SI rather than cartridge PI SRAM.
- Neighboring debug actions `0x80043B88` and `0x80043B90` are already `jr ra; nop`
  in the original ROM. Preserving these original instructions is distinct from
  inventing successful replacements for unknown guest functions.
- The actual startup accessory probe at `0x800042C0` passes queue, `OSPfs*` and
  channel to `osPfsInitPak` at `0x80060550`. The observed original path reached SI
  raw DMA through the status helper at `0x80060880`.
- The initial reviewed runtime binding uses upstream `osPfsInitPak_recomp`. The
  pinned implementation returns `PFS_ERR_NOPACK` (one). This represented the
  baseline absence of Controller Pak storage; it does not initialize a filesystem or
  demonstrate successful save access.
- The generic original ROM transfer wrapper `0x80003894` is called through
  `0x80003964`, which selects the handle returned by `osCartRomInit`.
  No active SRAM handle or cartridge SRAM transfer has yet been established.

Further known Pak entry points have been identified from their argument and
instruction semantics, without adding unneeded bindings:

| Guest address | Function | Evidence |
| --- | --- | --- |
| `0x8005F270` | `osPfsAllocateFile` | Company/game/name/extension arguments, allocation size rounded to 256-byte pages, output note index |
| `0x8005F6A0` | `osPfsDeleteFile` | Finds a note by company/game/name/extension and releases its inode chain |
| `0x8005F8C0` | `osPfsReadWriteFile` | Note index, direction, offset, size and buffer; checks 32-byte alignment |
| `0x8005FD00` | `osPfsFileState` | Reads a directory entry by note index and fills state metadata |
| `0x8005FEA0` | `osPfsFindFile` | Scans directory entries by company/game/name/extension and returns note index |
| `0x80060340` | `osPfsFreeBlocks` | Counts free inode entries and converts pages to bytes with a shift by eight |
| `0x80060450` | `osPfsNumFiles` | Returns maximum directory entries through argument one and used entries through argument two |
| `0x80060820` | `osPfsRepairId` | Repairs the Pak ID and clears the relevant filesystem status flags |
| `0x80067520` | `osPfsChecker` | Traverses note directories and inode chains to check/repair consistency |

## Pinned runtime SRAM behavior

In pinned N64ModernRuntime, `librecomp/src/pi.cpp`:

- `get_save_size(SaveType::Sram)` allocates `0x8000` bytes (32 KiB).
- Cartridge SRAM begins at physical address `0x08000000`.
- `do_dma` reads or writes the save buffer and queues a PI completion message.
- Save writes are coalesced by the saving thread, using upstream backup-aware
  file output. With game ID `iss2000-us`, the default file is
  `<portable data directory>/saves/iss2000-us.bin`.
- The low-level `save_read` and `save_write` bounds checks are assertions.
  Project adapters must validate ranges explicitly in Release builds.

`src/runtime/pi_transfer.hpp` supplies pure validation for original
`handle.baseAddress | message.devAddr` semantics: only read direction zero and
write direction one, 16 MiB read-only ROM, 32 KiB read/write SRAM, 8 MiB guest DMA
buffers, and checked KSEG aliases. Handle structures may use the runtime's
reserved `0x80800000..0x80801000` area; message structures may not. Nonempty or
empty valid transfers retain normal PI completion semantics. The validator does
not perform a copy, claim success, modify guest state or deliver a message.

## Required acceptance evidence

Before choosing and documenting the final save backend, observe actual original
save-device requests and their sizes. Controller Pak support requires persistent
per-port files, genuine filesystem behavior and accessory selection that remains
consistent with Rumble Pak detection. Cartridge SRAM support requires observed
PI transfers within the confirmed hardware capacity. In either case verify menu
save, process exit, restart and load with matching original data before claiming
save support.


## Original save descriptor and payload

The actual save manager at `0x800190E4` allocates `0x7900` bytes at
`0x8001914C..0x80019158`. The descriptor at `0x8007A0B0` (ROM `0x7ACB0`)
contains game code `0x4E495345` (`NISE`), company code `0x4134` (`A4`),
four zero extension bytes, and the sixteen filename bytes
`22 3C 2C 3C 2C 3C 12 10 10 10 0F 0F 0F 0F 0F 00`.
These are N64 encoded characters; retain the bytes rather than substituting an
ASCII filename. `0x80019498` reads the full `0x7900` bytes at file offset zero
through `0x80019550`, then can write the full payload through `0x800195EC`.
The note consumes 121 of the standard single-bank Pak's 123 data pages, leaving
512 bytes free.

## Persistent device implementation

`src/runtime/controller_pak.*` implements four independent canonical 32768-byte
images. `src/runtime/pak_services.*` replaces only the reviewed block read,
block write, device status and accessory-mask boundaries recorded with exact
body digests in `config/recomp/device-boundaries.json`. Allocation, directory
listing, note lookup, file state, checking, repair, deletion and file reads and
writes continue through the original compiled SDK functions. The original
`osPfsInitPak` body must run for a selected Controller Pak; upstream's constant
no-pack implementation cannot initialize this filesystem.

The images live under the portable saves directory as `controller-pak-1.mpk`
through `controller-pak-4.mpk`. `controller-paks.json` selects `controller`,
`rumble` or `none` independently for four ports; its default is a Controller Pak
on port one and no accessories on the other ports. This accessory selection is
independent of the physical controller's rumble capability. The host device and
motor reporting must use the same selection. Before configuration, the adapter
reports no accessory. Initial configuration is stable; later changes produce a
one-shot new-pack status.

An exclusive process lock covers the directory. Each accepted changed block
is persisted by synchronizing and atomically replacing the entire image, after
publishing the previous image as `.bak`. Every existing 32768-byte image also
gets an immutable `.preserved-N` startup snapshot before original SDK repair
can modify it. A malformed-size image is rejected and retained verbatim;
corrupt filesystem content of the correct size remains available to the
original checker. Storage failures return an error rather than a successful
write. If a directory synchronization error occurs after an atomic rename,
the published file may already contain the new whole image; the previous
image remains in its backup, and the stale-memory check blocks further writes.
Identical ordinary block writes still validate that the backing image exists,
has the expected size and contents, and is not a symlink before returning
success. SDK-defined bank-selection and protected-ID no-ops retain their
separate device semantics. Accessory preferences likewise synchronize the
parent directory after atomic replacement on Linux; if that synchronization
fails, the new whole JSON file may already be present while the running choice
remains unchanged. The error is reported rather than claiming durability.
Never automatically erase or reformat an existing file.

Fresh images contain four matching ID copies at offsets `0x20`, `0x60`, `0x80`
and `0xC0`, with generated device identity, device ID bit zero set, one bank,
and complementary halfword checksums over the first 28 ID bytes. This follows
`0x80060B34` and the ID validation in `0x80060550`. Primary and mirrored inode
pages at `0x100` and `0x200` contain 123 free markers `0x0003` starting at
entry five, with low-byte checksum `0x71`, as used by `0x8006124C` and
`0x80067520`. Sixteen empty 32-byte directory entries occupy `0x300..0x4FF`.
A fresh valid filesystem is more than an all-zero memory image.

## Isolated SDK verification

An isolated private unit diagnostic compiled 24 actual resident SDK functions
from this supported ROM and called the project's actual device adapters. It
used synthetic single-thread SI exclusion fixtures and never called the game
entrypoint or launched a game window. The private receipt is
`.local/runtime-research-pak/sdk-adapter-result-03.log`.

It verified original `osPfsInitPak` and `osPfsChecker` success; 16 available note
slots and 31488 free bytes; allocation of the exact NISE/A4 note and `0x7900`
payload; original full-file write/read/find; matching original file-state size,
company and game metadata; 512 bytes remaining; destruction and reopening of
the actual store followed by original SDK initialization and an exact payload
reload; and original deletion restoring 31488 free bytes. Public synthetic tests
also cover four-port separation, canonical byte order, malformed pointers,
write protection, busy process locking, corrupt-file retention and publication
failure. This verifies the storage layer and original SDK algorithms. Actual
in-game menu save/restart/load remains a separate visible acceptance test.

### Retaining the original initialization body

The Controller Pak bridge must call `iss2000_original_80060550`, the uniquely
named original SDK translation emitted into private `native_retained.cpp`.
`func_80060550_resident` can instead name a generated runtime wrapper when the
CPU map excludes a reviewed service. Boot 11 demonstrated this collision:
selected Controller Pak initialization returned the upstream no-pack error (1)
without initializing the guest filesystem state. A function name alone did not
prove the linked implementation was the original body.

The reviewed binding now requires `preserve_source: true` and pins the SHA-256
of its original generated translation. Generation verifies the ROM digest,
original body digest and bounds, translated instruction-address coverage and
source digest before writing any output. It fails if that retained source is
missing or replaced by a host wrapper. Both input and output hashes are recorded
in the private metadata receipt. The original source remains private.

Reproduce from the canonical project root, choosing a fresh output directory:

```sh
python -m tools.prepare_native \
  --rom .local/game-build/data/iss2000-us.z64 \
  --sections .local/runtime-map-04/section-analysis.json \
  --runtime-symbols config/recomp/runtime-symbols.json \
  --retained-source .local/runtime-map-02/functions/func_80060550_resident.c \
  --output .local/native-metadata-09
```

The native target must compile all three generated files:
`native_metadata.cpp`, `native_bindings.cpp`, and `native_retained.cpp`.
The bridge intercepts initialization before reviewed host service lookup and
calls the unique original entry only for the selected Controller Pak.
The compile/link regression deliberately supplies a separate absent-device
wrapper and verifies that the unique original body runs. This verifies emission
and symbol isolation; actual in-game saving remains a separate visible test.
