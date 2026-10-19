# PAL save presentation and automatic storage

Original project work: djultra64. This research applies to the exact supported
PAL English/Deutsch revision and its pinned private generated CPU sources.
The user-facing English wording uses PC save terminology. Internal SDK symbols,
original file identities, authentic notices and player names remain unchanged.

## Automatic insertion continuation

`tools.prepare_pal_auto_storage_ui` emits one private C++ translation unit with
these exports. The native lookup must check the corresponding exact original
function pointer before selecting either derivative.

| Original entry | Private derivative | Change |
| --- | --- | --- |
| `802B1CC8` | `iss2000_pal_automatic_storage_ui` | Enter original `802B2144` instead of waiting at insertion state 15; resolve a newly produced insertion request once before continuing. |
| `802B1D84` | `iss2000_pal_automatic_storage_update` | Resolve an active insertion request before the original per-frame scene update and after genuine input dispatch. |

Both paths use the unchanged original `802B2144` status interpreter and
`80018E98 → 80018EE0 → 80018F4C` probe. The latter still calls the original
filesystem wrappers and applies original error/retry decisions. The derivative
never invents a button press, returns SDK success, confirms Save/Repair, or writes
save contents.

The active UI flag at `8012E167` must be exactly **4 or 5**, and message state
`802B4819` must be 15. Original `802B1FDC` initializes flags 5; original
`803CAAF0` can independently set bit 4. Bit 0 is a separate background phase.
Original `802B2118` closes the owner by clearing the flag byte and dirty state,
but can leave the message-state byte unchanged. A state-15 check alone could
revive a closed scene. An exact-5 check was also insufficient: actual development
47 stopped on the genuine insertion screen with flags 4. Output revision 3
accepts both active variants and preserves closed 0 and unrelated flag values.

The original initializer/callback source SHA-256 pins are respectively
`01ea25bcc1eb2a04e20841538a7ede03375d104290178349de85c8b3381c792f`
and `466871b69202f51628b5c6de8df82be3abe8ff8c0c90a5b80254e0b0db4dacbe`.
The generator also verifies the full ROM and both original machine-code bodies.
Existing derivative directories are immutable; use a new output revision.

## English wording ownership

`tools.prepare_pal_storage_text --rom <private PAL ROM> --output <private directory>`
emits `pal_storage_text.cpp` and a receipt. Output revision 2 has **43 exact
message profiles**. Call its function immediately before the exact original
`80048660` font renderer:

```cpp
extern "C" bool iss2000_pal_storage_text(uint8_t* rdram8MiB,
                                         uint64_t original_font_object);
```

The result reports recognition/application. The original draw always continues.
The adapter accepts a bounded canonical font object of direct-string type 0,
its exact owned source pointer, and the complete original message bytes. It also
recognizes its own output and the nine earlier startup wording variants.
Malformed pointers, altered messages, numeric objects and unrelated text fail
closed without guest-memory writes.

| Original ROM bank | Proven load address | Scope |
| --- | --- | --- |
| `315400..316D00` | `801ED700` | Existing insertion instructions; their physical-accessory waits are handled separately. |
| `326630..32A300` | `801EF060` | Generic save-data access/repair warnings. |
| `50C3E0..5103D0` | `803FAF60` | Shared gameplay/Career load, creation, repair and error text. |
| `514950..515160` | `802DD400` | Data menu/startup save, load and creation text. |

All original control bytes, terminators, glyph-run lengths and message extents
remain intact. Existing Save/Load/Create/Overwrite/Repair decisions and errors
retain their actions. The visible save question reads **Save Game?**. No profile
contains replacement wording about game notes, Paks or pages.

Thirty-nine profiles have actual original whole-word pointer references. Four
additional generic messages at ROM `329961`, `3299B1`, `3299ED`, `329A51` have
no recovered consumer reference. Their profiles accept only leading zero-padding
positions within the exact original message, with whole-message byte validation
and the grounded loader mapping. The receipt explicitly labels that limitation;
these four are defensive coverage, not evidence that those screens execute.

An inventory of original encoded English terms also found `Pak` at ROM `55B34C`.
It is a **player surname**, adjacent to other player names, and is excluded.
`Controller 1..4` refers to player ports and is also unrelated. Other languages
and text baked into image assets are outside this English encoded-text inventory.

## Capacity and remaining evidence

The actual logical backing image remains 32,768 bytes, with 123 data pages.
The original PAL game file occupies `7A00` bytes: 122 pages. It already contains
all supported original persistent state, including both Career records. Career
progression updates this fixed payload; it does not allocate a new file each
week. Ordinary ongoing play therefore does not require an infinite-capacity
claim or a new filesystem. Foreign notes in imported backing images can still
consume the logical quota; preserve genuine failures and meaningful choices.

Original startup `802B27F8 → 80004A60 → 80060BC0` queries free bytes. The
initializer stores those bytes at `802B4810` and required size `7A00` at
`802B4814`; `802B2868` consumes them for real allocation gating. These are not
presentation counters. Literal page counts in the startup warning messages are
covered by the wording adapter.

The shared 177-byte creation template at ROM `510207`, original source
`803FED87` and table target `803FED88` at ROM `50BEA8`, contains blank numeric
fields alongside its old page wording. No numeric-control token exists inside
that message. Its possible separate numeric producer has **not been recovered**.
The wording removes the obsolete text, but removal of any separately rendered
capacity digits is not yet established. Do not claim complete visual capacity
coverage from the string tests alone.

## Verification

`tests.test_pal_auto_storage_ui`: two CPU tests execute the genuine selector,
probe/retry, SDK wrapper, input mapper and update chains. They cover active flags
4/5, closed/unrelated variants, genuine error and creation states, unchanged
input packets, original context/stack return, wording ownership and failing
negative controls. SDK endpoints in the fixture are explicit test models;
these tests do not establish disk or GPU acceptance.

`tests.test_pal_storage_text`: three tests exercise every profile through the
complete original `80048660` direct-call closure with an actual completed PAL
RAM fixture. They verify unchanged memory outside the owned message, controls,
repeated application, earlier variants, unknown sources and player names.
The final 43-profile run passed with no skips. Hidden GPU acceptance of the
updated flow and all relevant rendered dialogs remains a separate check.

## Independent English terminology audit

The private receipt `.local/pal-save-ui-01/encoded-inventory.json` scans twelve
obsolete term/case patterns across the four proven English text domains. All
**57 term occurrences** fall within the 43 owned message extents; none remain
outside those extents. The regression checks actual original term locations,
not just the number of profiles. Whole-message/source-pointer runtime guards
still apply; this inventory alone does not establish every dialog's execution.

Twenty-three other occurrences of Controller Pak/Rumble Pak belong to the
original German/French text domains. They are not claimed as English coverage.
The separate enhanced/no-expansion notices at ROM `51507C`/`5150C4` belong to
states 14/16, handled by the memory-notice policy rather than save terminology.
The supported actual 8 MiB configuration does not enter no-expansion state 16.

The actual Data Change heading reads Data Change. The reviewed original
controller-label atlas (asset `24`) contains Type/Cursor/Keeper controls;
the Options/new-player/character-editor/Game Setting atlas inventories
(`42`, `43`, `45`) supplied no additional identified accessory/save-note words.
This is a bounded review of the relevant known resources, not exhaustive OCR of
every compressed image. No additional concrete English bitmap replacement is
currently justified by that review.

## Silent initial save/create flow (v4)

Original project work: djultra64. The first genuine `802B1CC8` DataChange
initializer in a host process consumes a startup token. The scope becomes active
only after the original resource loader returns with owner `8013B418`, current
resource `802B4174`, and all eleven original resource-prefix words intact. A
second entry, an unknown owner/resource, or any real error permanently returns
the entry to normal manual behavior. Guest bytes `8012E680` and `8012E688` are
continuation/dirty state, not startup provenance, and are not used as such.
The actual fresh-boot entry capture under `.local/startup-autosave-01` established
this initializer and the resource transition from `80077340` to `802B4174`.

Within this scope, the existing insertion probe runs normally. A bounded helper
calls the genuine original `802B2868` handler with a copied register context for
its default Yes states 0/4 and its completed state 2. The original capacity/file
limits still gate creation; original `2780/27C8/22F8/2758` jobs retain their delays
and real create/write operations. No input packet, payload, success return or
filesystem result is manufactured. For the captured boot flags `00010001`, a
fresh file follows original states `0 → 4 → 5 → 1 → 2`; a healthy existing file
can close directly through the original probe with no write.

The project derivative of resident `80041A44` traverses the original queue and
retains its stack/register and font-reset operations, suppressing only its two
sprite/font draw calls. Suppression requires one of the twelve exact original
owner queues (`owner+5060+n*488`, `n=0..11`) and healthy startup states
0/1/2/4/5/15. This removes the initial question, Creating/Saving and completion
art while the original jobs run. Error screens and later entries render
normally. Draw-only descriptor clipping retirement inside the omitted sprite
callee is also omitted during this hidden entry; full descriptor-memory
identity to an ordinary rendered frame is not claimed.

One original error-policy defect matters when auto-closing: `22F8` retains dirty
state on failed `80019A64`, but its previously scheduled `2758` still labels state
2 unconditionally. The derivative therefore requires actual port-zero SDK
result `800C1124 == 0` before closing state 2. Original `80019B94` stores the
`80004B58 → 80060140` write result at `800C1124` and `800C1134`, and original
`80019B04` retries failures three times. `2758` does not overwrite those words.
A nonzero completion result selects the existing generic unavailable state 3,
retains the actual SDK result and dirty data, and disarms automation/presentation
suppression. Re-probing is deliberately avoided because storage presence can
succeed after a write failure and erase the useful error result.

`tests.test_pal_startup_autosave` executes the genuine initializer, selector,
probe, A handler, jobs, allocation/write wrappers and UI queue routine. Eleven
isolated scenarios cover actual boot flags, an alternate original confirmation
mode, original probe errors, SDK4 allocation/write failures, all six hidden
states across all twelve queues, unrelated queues, owner/resource/prefix drift,
second entry and unchanged input packets. Failure scenarios require visible
error callbacks, no automatic close, retained dirty state and unchanged existing
file bytes. The SDK endpoints, scheduler timing boundary, checksum and unrelated
serialization/load subsystems are explicit CPU test models; this does not prove
loaded production-save payload preservation or GPU presentation. Those remain
separate real-runtime checks. RED was observed before automatic choices existed
and with the new async-result guard removed; the complete focused four-test
storage suite passed after restoring the guard.

The immutable derivative is `.local/pal-auto-storage-ui-v4`; its receipt pins the
ROM, initializer/update/render sources and ROM bodies, plus each wording extent.
The queue source rejects even a single added byte. Earlier v1/v2/v3 outputs are
preserved.

## r53 actual hidden runtime acceptance

The fresh-data run `.local/startup-autosave-02/` executed the native game and real
SDK filesystem adapter. It created directory0 NISX/A4 and genuine save contents,
advanced5→1→2/closed with SDK result0, and reached Main Select. Only Start was
injected; no save confirmation was pressed. Debugger observations of both
original sprite/font draw functions recorded no healthy startup UI draw.

The existing-data run `.local/startup-autosave-03/` executed the exact packaged
production r53 binary and bundled libraries, with fixtures disabled. Private
Xwayland keyboard Enter was the only input until Main Select. All four copied
primary save images remained byte-identical; healthy storage art did not draw.
Both sessions exited normally. Runtime data and captures are private. These
checks establish those actual files and paths, not exhaustive Career payload,
all modes, physical controllers or full release acceptance.
