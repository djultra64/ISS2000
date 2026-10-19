# PAL original Options entry and fixed High default

Original project work: djultra64.

The approved port interface reuses the original Options screen's **Resolution**
row as **PC Settings**. The user explicitly removed the Low/High selector and
requires the original High preference. The other seven original rows and the
original eight-row navigation remain. Modern settings are drawn with the
original game font through the native menu adapter; no host settings popup or
independent overlay is part of this design.

The supported input is English/German PAL revision 0, ROM SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
Original assets, generated original CPU code and fixtures remain private.

The main-menu Accept handler `803C2CEC` bounds nine main-menu rows. Index 8 takes
case `803C2DC4`, storing mode 1 at `8012DE74`. Dispatcher `803C2E2C` maps mode 1
to common page 7; table `801E2D80` selects `803B2070`, whose loading continuation
`803B2094` enters original Options `8029F1B4` in ROM owner `3B47E0`, VRAM
`8029EEA0`. Initializer `8029F1E8` installs script `802A6CC8` and input callback
`8029F274` through the ordinary fade/scheduler registration path.

| Original row | Index | Port behavior |
| --- | --- | --- |
| Go Back | 0 | Original |
| Game Setting | 1 | Original |
| Create Player | 2 | Original |
| Delete Registered Player | 3 | Original |
| Data | 4 | Original |
| Transfer | 5 | Original |
| Resolution | 6 | PC Settings, as explicitly requested |
| Language | 7 | Original |

The original cursor is byte `802B1090`; changed-row byte `802B1091` drives the
original selection frame. Original Up `8029F33C` and Down `8029F390` wrap modulo
8, while B handler `8029F314` returns the cursor to Go Back. Original Accept
`8029F2D8` executes its original save/preparation calls, remembers the chosen row
at `8012DE75`, and closes through `8000C7AC`. The approved native hook intercepts
only row 6 to open the original-engine PC settings menu; other rows run the
original handler. Native dispatch must compare the currently registered function
pointer with `func_8029F2D8_overlay_3b47e0_8029eea0`, in addition to the helper's
memory/profile checks. Address equality alone does not establish overlay ownership.

`pal_options_entry(span)` is a read-only guard returning `{row, pc_settings}`.
It requires the original context `8013B418`, mode 1, cursor 0..7, exact original
Options function bodies/scripts/tables, and a valid complete original scheduler
list containing active callback `8029F274`. It checks all 220 bounded nodes,
rejecting cycles or foreign pointers even after finding the callback. The
transient current-node pointer at `801ED420` alone is insufficient after update.

The original script has `F4000008` at `802A6CD4`; it creates eight groups of row
objects. We leave that count and all navigation untouched. A ninth cursor would
also require replacing `8029F0FC`, which copies only eight y-coordinate bytes to
its local stack before indexing the selected row. Reusing row 6 avoids that
uninitialized-stack access entirely. `8029F0FC` moves the selected frame; it is
not a semantic description-text callback.

## Exact label ownership and font position

Only the Resolution word sprite is substituted. The original bar, bullet and
selection frame remain separate original objects. Child script `802A6C68`
requests resource 3 and calls `8029F070`; that original callback requests
resource `row + 3`. For row 6 this is resource 9 at `802A6C20`:

```text
00720002 08000000 802A6B6C
```

It selects descriptor bank 114/index 2, layer 8, segment list `802A6B6C`.
The descriptor is `802D1C3C`, from original bank root `802D1C24`. The two original
64 by 16 rectangles sample the lower half of the 128 by 32 I4 atlas at
`80277640`; the upper half says Delete Registered Player and the selected lower
half says Resolution. Original asset `42`, loaded to `80276940`, owns that atlas
at offset `D00`. The exact decoded asset SHA-256 is
`5dbf56dd71d5c280fc0fad104003a23898312e4fd9468a76fd023db8d221a3e8`.
The atlas's 2,048 bytes are pinned independently.

Original callback `8029F004` reads row 6's y value `A6` from table `802B08C0` and
calls original position setter `801B0000` with `(54,166)`. This is a coordinate
setter, not a bank/descriptor selector. The segments add `(13,1)`, so the word's
actual ink origin is **(67,167)**, in a **128 by 16** region.

`pal_options_pc_label(span, object)` returns this `{x,y,width,height,selected}`
only for that exact original word object. It requires original pool membership,
type/layer, descriptor, segments, unit scales, original position and script
context row 6, as well as the exact resource/descriptor/segment and English atlas
hashes. It performs no guest writes and imports no platform/SDL interface.
The caller may omit this one original sprite and emit PC Settings through
`draw_pal_engine_text` at the returned position. Text drawing must use the same
bounded original-font setup and final draw ordering already used for Remap.

## Keyboard operation and output resolution

Within PC Settings, Up/Down select a row, Z selects, and X or Escape goes
back. Left/Right change the selected Graphics value; Page Up/Page Down remain
aliases. The Graphics page explains Left/Right in its original-font footer.
The same directional commands change the selected controller accessory.
Keyboard repeats are ignored, so each press makes one change. Input stays
suppressed from the underlying game until the menu closes and held controls
are released; entering or leaving the Remap child rearms that release gate.

The PC Settings Resolution row controls the host output target (Original,
720p, 900p, 1080p, 1440p, 1800p or 2160p). It does not change the game's
internal Low/High choice or original buffer allocations. Original output uses
the scene's native framebuffer size; a selected output height is scaled from
that actual size. The fixed internal High default below remains independent
of both this output setting and the 60/120 rendering refresh selection.

## Fixed original High default

Resolution and Language use different original selectors. Resolution entry
`802A6110` registers initializer `802A613C`, which installs resource table
`802B03C8`. Its selector is byte `802B10F0`: row 0 is Low, row 1 is High.
The original position table `802B0FFC` gives y111 for Low and y87 for High;
position callback `802A5F4C` uses that table directly. Original word resources
3/4 both use bank115/index133: their segments are `802B0374` (Low at y112)
and `802B0368` (High at y89). Original capture360 independently confirms
this screen arrangement. Complete original commit `802A63DC` stores the
selected 0/1 into `8013B42B`. Accept handler `802A6234` refuses High when
memory-detected byte `8013B429` is zero.

The earlier interpretation of `80133676`, selector `802B1100`, and the top
bits of `8013B428` as Resolution was incorrect. Those fields belong to
Language. The derivative and tests no longer modify those fields or use
Language resources as evidence of resolution semantics.

The actual frame context is `8013B418`, published by original `80008BB0`.
Byte +11 (`8013B429`) records genuine 8 MiB detection, +12 (`8013B42A`)
is the current working video mode, and +13 (`8013B42B`) enables original
High requests. Main `8000092C` calls `80008BB0` at `80000988`, before the
later settings startup at `80000A18`. The frame pointer is published at
`80008BE4`; original `80008C30` is called at `80008C18`.

Resident `80008C30` calls original `osGetMemSize` (`80062270`) and compares
its result against `007FFFFF`. It writes the detected flag first, clears
current mode at `80008C80`, and originally clears the High request default
at `80008C90`, before calling `80008CBC`. Generator
`tools.prepare_pal_fixed_high` changes only that desired-mode default to
copy the already detected +11 flag. The generated source contains the same
delay-slot store twice, and both representations are guarded and changed.
The full supported ROM, complete original 140-byte body at ROM `9830`, and
exact original generated source are SHA-256 pinned.

```text
python3 -m tools.prepare_pal_fixed_high --rom <private-PAL-ROM> \
  --source <original-functions>/func_80008C30_resident.c --output <fresh-private-output>
```

It emits `pal_fixed_high_initializer.cpp`, exporting
`iss2000_pal_fixed_high_initializer`, plus a schema2 receipt. Inputs and
foreign output directories are preserved. Native integration binds only
exact original resident `80008C30` to this derivative. Current mode remains
Low during original title/buffer initialization; `80008CBC` reads current
mode and detected memory, independently of the new desired default.

Original scene requests still run `80001D44`, and original `80001E40` /
`80002D08` install the VI settings, dimensions, Z-buffer and color buffers.
The genuine High layout is 640×544, Z-buffer `80700000`, and color buffers
`80500000`, `805AA000`, `80654000`. Original temporary mode changes,
including Career disable/restore paths, remain intact. No working-mode flag,
buffer pointer, Language preference, save, or original CPU source is forced.

## Verification scope

`tests/test_pal_options_entry.py` executes the genuine original resource
constructor `8029F070 -> 80007BF8 -> 80007C2C`, position callback `8029F004`,
position/scheduler callees, and both original eight-row navigation handlers and
their genuine audio-queue callees. An offline fixture supplies the ordinary
scheduler/object context and exact original overlay data/decoded asset 42.
All eight resource/coordinate outcomes are checked, with only row 6 admitted
for replacement. Owner, source, metadata, atlas, cursor and cyclic-list changes
are rejected; the pure helper leaves the entire fixture unchanged.

`tests/test_prepare_pal_fixed_high.py` executes complete original `80008C30`,
`80008CBC` and `80008E34`, alongside the generated derivative. Its positive
case executes the original `80062270` memory probe with faithful KSEG0/KSEG1
physical RAM aliases; its negative case supplies a 4 MiB result at the SDK
capacity boundary. At original buffer initialization, it checks detected
memory, current Low mode and the desired default independently. Original and
derived boot fixtures are equal across the entire 8 MiB after restoring only
the intended desired byte; Language and every original buffer write match.

The fixture then executes original `80001D44`, `80001E40`, `80002D08`,
`80043324` and `80008E34` to establish the genuine High dimensions and
buffers. Only interrupt/VI hardware side effects use argument-checking test
recorders; they never alter guest video fields. This proves original CPU
request/install behavior, not a running VI device or complete game loop.
A separate test executes real Resolution resource constructors, position
callback and complete `802A63DC` commit for both Low and High. Full ROM,
source/output guards and repeat generation are checked. Native settings
integration tests extract the actual lookup gate and require exact original
`80008C30` symbol identity; foreign owners fall through. Actual scene/GPU
acceptance is tracked separately by the parent.

Actual hidden build43 acceptance subsequently confirmed installed-memory=1,
desired=1 and current=0 on the title, followed by a natural Training transition
to current=1 and 640×544. Completed evidence is private
`.local/training-timing-01/free-training-high43-completed.rdram`; capture378
shows the High HUD. This observation is separate from the CPU-only fixtures.
