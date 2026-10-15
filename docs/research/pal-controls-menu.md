# PAL original-engine controls remapping

Original project work: djultra64. Input: Europe English/German revision 0,
SHA-256 `6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.

The native menu state and original-font adapter are implemented in
`src/runtime/game_controls_menu.*`. This record proves original menu ownership,
input state and original rendering calls. It does not claim visible remap-menu
acceptance or physical-controller verification. Native hook/input integration
and visible acceptance are tracked separately by the main implementation.

## Original controller screen and safe entry

The pre-match common-page wrapper `803D3248` installs controller setup `802C4640`
and its callbacks. The latter resides in ROM overlay `40C7A0`, VRAM `802C3490`.
Its flow is `802C47CC -> 802C4820 -> 802C48C0 -> 802C48F4`. The update loops
exactly four ports, writes the active port to byte `802D21EF`, and dispatches
through `802D1BE8`. The original Accept handler is `802C49B8`.

Use an exact active-function identity comparison against
`func_802C49B8_overlay_40c7a0_802c3490` before inspecting these overlay fields.
The proposed **Remap controls** entry uses Accept on the selected port's Type
row (cursor value 1) only when its ready flag is zero. Original Accept has no
Type-editing operation there; original left/right still change the original
Type. Preserve the original OK row and all ready/commit behavior.

| Field | PAL guest address |
| --- | --- |
| Selected rows, four bytes | `802D21E0` |
| Original Type choices, four bytes | `802D21E4` |
| Original cursor style, four bytes | `802D21E8` |
| Original keeper choices, two bytes | `802D21EC` |
| Mode / active port | `802D21EE` / `802D21EF` |
| Ready flags, four bytes | `802D21F0` |

The navigation consumer `801B5BE0` reads five-byte records
`enabled,up,down,left,right`. Original Type navigation at `802CF0A4` contains
**three** records, with left/right cycling 0..2. Do not infer four Types from
the controller texture's digits 1..4: the screen also serves four ports.
Original commit `802C53A4` selects twelve-byte profiles at `800774F0`, invokes
`80014A74` per port, and stores original Type/cursor/keeper settings separately.
The host logical remap does not alter these original profiles or save fields.

Original controller asset request `801B7C6C -> 8000A440` reads
`801BBF28 = {40000024,80270140}`. PAL asset `24` is compressed at ROM
`C2CC6E..C2D8DE`; decoded size is `2180`, SHA-256
`3503b69f26c73874393615c615d91f082c4cb6c3590689fee1eb3c8dc9f536b6`.
Its fourteen sprite descriptors belong to bank `21`, not bank `24`.
Decoded original labels establish Type, Cursor, Keeper Config, Auto,
S.Auto, Manual and D-Pad Switch L/R. Original image bytes stay private.
This proof concerns pre-match controller setup; a pause-menu route has not
been established by this analysis.

## Draft, capture and saving

`game_controls_menu()` returns one mutex-owning service. `open(port,initial)`
accepts ports 0..3 and copies only that port's preferences. The menu provides
fourteen logical N64 actions, a manual family selector, Restore defaults,
Save and Cancel, paginated six rows at a time. Logical names retain original
Type semantics instead of inventing football-action meanings.

Call `update(ControlsMenuCommand,physicalHeldMask,activeFamily,saveCallback)`
from the input integration. Physical bits are SDL controller button positions;
active family changes the displayed names. Capture waits for all buttons to be
released and then one fresh physical press. Chords must release fully before
another attempt. Physical B remains assignable: during capture, only keyboard
Escape should produce Cancel, rather than mapped controller B. Suppress the
original game input while editing and require a fresh release after closing.

The existing preferences remain applied until Save. The callback receives only
`(selectedPort,draftPreferences)` and returns success. It executes outside the
menu mutex; merge into a fresh four-port snapshot, persist first, then apply.
Failure or exception leaves the menu open with the draft intact. Cancel closes
without applying it. Navigation instructions continue to show the persisted
navigation bindings until Save. Family selection supports Auto, Xbox,
PlayStation and Nintendo. Existing trigger/right-stick fallbacks remain visible
and can be restored; this capture interface handles digital controller buttons.

## Original font and bounded drawing

The resident original dispatcher `80041A44` calls text function `80048660` for
queued objects with kind 2. The new adapter calls that same original function,
with a copied CPU context and temporary guest-stack object/string. Its signature
is `draw_pal_engine_text(ram,caller,lines,original80048660)`.
The root integration must guard the original resident identity and controller
owner before drawing. It must also compose the active menu so old controller
labels do not overlap the new screen; no independent host renderer is used.

The object matches original initialization `80048528`: zero flags/parent,
encoded-string kind 0 at offset 5, signed X/Y at `E/10`, palette 0 at `12`,
source pointer at `14`, zero spacing at `20/21`, and character limit `FFFF`
at `22`. The independently traced glyph encoding is space `00`, digits
`01..0A`, uppercase `0B..24`, lowercase `25..3E`, period `3F`, terminator
`FF 11`. All other input characters are rejected before mutation.
The original parser selects font 2, whose texture is original asset `0D` at
`80352800`; each normal glyph measures 6 by 12. Palette 0 comes from the
resident original palette table. Font asset decoded size is 12288, SHA-256
`237c7f53ac8b11353467cb957868f794507ca2688c93581d977dac03a4e8b765`.
Actual rendering still requires that original font asset to be loaded.

The main-thread stack allocation is `800A02D8..800A42D8`. The adapter validates
an aligned live SP with at least `400` bytes remaining, saves/restores those
bytes, creates a `100`-byte frame below live SP, and calls original text using
copied registers. The original closure consumes less than `100` more bytes.
Caller registers remain unchanged. Never restore the display-list head:
emitted original graphics commands must remain part of the frame.

Original `800006A4` chooses Gfx bases `800D0320` / `800E0380`.
`80002A10` stores the active base at `800A4AA4`, starts drawing at base+8,
and places task metadata at base+`10008`. Therefore the adapter validates that
exact base and the aligned head at `8009E0C8` within `[base+8,base+10008]`.
All lines are preflighted together, at most ten lines of forty characters and
within original 320x240 coordinates. It reserves 128 bytes per glyph plus 256
per line: font-2 `80049490` needs at most 56 palette bytes per line and 56
texture bytes per glyph, `80049158` adds 24 rectangle bytes, and setup adds
at most 32. The rounded reservation covers these paths without depending on
font cache hits.

After drawing, mirror original dispatch `80041AE4..80041B08`: set
`800BDB20=80041980`, `800BDB24/26/28=FFFF`, `800BDB2A=0`.
These invalidate the original sprite cache after text. Keep original font
caches coherent with emitted state; restoring stale cache values would make
later original draws skip required graphics state.

## Evidence and verification

Private `.local/pal-remap-menu-01/report.json` pins fifteen original function body
hashes, four complete navigation tables, original object offsets, controller
fields and Gfx bounds. Its `record_evidence.py` reproduces those records from
the pinned input. Decoded label assets remain in that private directory.

`python3 -m unittest tests.test_game_controls_menu -v` passes three tests:
Cancel isolation; capture/family/paging/save and callback lock ordering; and
an integration fixture compiling the actual 29-function original font closure
and two original clear functions.
The latter draws every menu row for three controller families in synthetic
8 MiB RAM and both original Gfx arenas, verifies caller/stack preservation and
coherent sprite-cache invalidation, and rejects short capacity, unsupported
text and insufficient stack without any RAM changes. It runs no full game,
SDK fallback, emulator or host rendering path. The private-input fixture skips
when the original input/translations are unavailable; report that skip honestly.

## SDL input integration and precise screen ownership

`src/platform.cpp` now samples menu active/port/capture state before taking the
input mutex. Menu visibility is atomic, so guest input checks it before the
input lock and again before copying a snapshot without acquiring the menu
mutex in that lock. All four guest ports return neutral input while the menu
is visible and during its closing release gate. Rumble requests are suppressed
and running motors are stopped while editing.

The pure `ControlsMenuInputRouter` in `game_controls_input.hpp` receives the
same raw SDL physical button mask and persisted selected-port bindings sampled
by the platform. Opening requires a neutral sample first; navigation uses
rising edges of mapped Accept/Cancel/D-pad/L/R and left-stick thresholds.
Other controller ports cannot navigate or supply captured buttons. All ports,
keys, sticks and triggers contribute to the release gate, so Save cannot reach
the original game on another poll. Completing/canceling capture and regaining
focus each require another full release before navigation resumes.

Keyboard navigation uses Z, X, Up/Down, Page Up/Down, Backspace/Delete and
Escape. During capture only Escape cancels; X and physical controller B remain
eligible for their separate intended roles. Escape does not quit while editing.
F6/F7 do not change settings or open an independent dialog while this menu is
active. Saving uses a fresh four-port snapshot and updates only the chosen port,
then persists before applying. No independent error dialog is shown on failure.
The title explicitly names the Gamepad target. Keyboard navigation status says
`Z edit. X cancel`; gamepad binding rows retain the actual controller family.
Draw with `lines(platform::controller_family(menu.port()))` so keyboard use does
not erase the target controller's family.

Original scheduler registrar `801B3D1C` stores the new callback at offset `C`
of the current node pointed to by `801ED420`. Controller wait `802C48C0`
registers `802C48F4` after its fade flag clears. However, updater `801B36E0`
leaves that current-node global **zero** after traversing the list. It is not a
persistent screen callback usable by the later graphics dispatcher.

For exact draw-time screen ownership, scan the original active list whose
head is word `80077390`. Original initialization `801B3750` creates the fixed
pool `[801E7070,801ED420)` of 220 nodes, each `74` bytes. The original resident
initialized head is `801E7070`; the root callback lies at its offset `C`.
Walk each node's next pointer at offset zero, validating pool membership and
`(node-801E7070) % 74 == 0`, bounded to 220 distinct nodes. The controller
screen is present when an active node's callback at `C` equals `802C48F4`.
Reject invalid pointers/cycles. Combine that proof with exact native overlay
function identity guards; merely having the controller overlay registered is
insufficient because it contains other screens.

Focused routing regression additionally verifies opening/closing release,
selected-port isolation, remapped Accept, analog rising edges, capture Escape,
focus regain and keyboard device status. The platform translation unit was
compiled separately with actual PAL game build flags. Visible input/menu
acceptance and physical controllers remain integration verification work.

The copied `recomp_context` also rebases its internal `f_odd` alias into the
copy's FPR storage. Both upstream FR0 (`f0.u32h`) and FR1 (`f1.u32l`) pointer
offsets are preserved; invalid external aliases reject before mutation.
The original-font fixture additionally writes an odd register through that
alias and verifies the live caller is untouched in both modes.

The final focused command
`python3 -m unittest tests.test_game_controls_input tests.test_game_controls_menu tests.test_input_preferences -v`
passes six tests with zero skips in the private-input development environment.

## Corrected complete-frame composition

Visible acceptance capture `.local/captures/103-pal-remap07.png` proved that
substituting the queued UI dispatcher was insufficient: original controller
sprites covered the new text. The original `80000C30` loop dispatches five UI
lists first, draws intervening scene/sprite passes, and then dispatches seven
more lists. Drawing inside `80041A44` therefore emitted the new screen twelve
times and still allowed later graphics to cover it. Earlier proposed queued-UI
substitution above is superseded by this verified draw ordering.

The current native hook is at **`80000BB8`**, the whole original render branch
called by `80002A10` at `80002AF0`. It executes that original function completely
first. The caller then performs display-list sizing, VI bookkeeping and task
submission, so this is a bounded final composition boundary before submission.
The original twelve UI lists and all original sprite/background lifecycle calls
run normally. `80041A44` is no longer intercepted for remap rendering.

Only under the exact controller-screen ownership guard, and only while the
remap menu is active, the hook appends one opaque original-engine screen.
`draw_pal_engine_text` optionally accepts the original resident clear function
`800019FC`. It preflights the combined clear/text capacity before mutation,
validates original 320x240 frame configuration, temporarily sets the original
frame RGB halfwords to zero and alpha to one, calls the original clear with a
copied/rebased context, and restores those frame fields. This emits original
fill color `00010001` and the original full-screen rectangle. No host overlay,
manual display-list replacement or independently drawn panel is involved.

The clear calls original `80001B2C`, which creates one task color-image fixup.
Validate its cursor at `base+1005C` against the exact original slot range
`[base+1000C,base+1005C)`, aligned four bytes. Preserve the emitted fixup and
cursor increment because original task submission must resolve the color image.
Reject an invalid/full fixup table before any writes. Reserve another 256 Gfx
bytes for the clear. Invalidate cached material `800BDB26` before font drawing
so the original font setup emits the necessary cycle/material state after fill.
The usual original sprite-cache invalidation follows all text.

The inactive P1 Remap hint now draws once at the same final boundary at y=212;
the previous y=222 was clipped by the original presentation safe area.
The expanded integration fixture runs all 31 original font/clear functions,
checks opaque fill color/rectangle and real fixup insertion, restores original
frame RGB/alpha, and rejects invalid fixup storage with byte-identical RAM.
Visible acceptance of this corrected composition remains a separate game test.
