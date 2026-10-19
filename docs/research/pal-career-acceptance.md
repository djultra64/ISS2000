# PAL Career creation, progression and save acceptance

Original project work: djultra64. This is static research for Europe
English/German revision 0, SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
No game, emulator or original Career function was executed for this research;
no saves or guest RAM were changed. Actual creation, progression, Pak writing
and restart/reload remain visible acceptance tasks.

## Minimal genuine acceptance route

Use the original menus and bound Accept/Cancel actions. With default keyboard
bindings these are Z/X; use the currently displayed physical controller prompt
when a gamepad is active. Release each press before the next step.

1. From the original main menu, select **Career**, the second item. Its original
   zero-based cursor 1 selects mode 5. Accept the original Career title screen
   using Accept or Start if it appears.
2. Select an **empty** Career file among the two original slots. Record the slot
   number; do not overwrite an existing Career. The original file screen handles
   existing versus empty slots directly, so a separate Continue button is not
   required.
3. Follow the original country and protagonist/team setup screens. Give the
   protagonist a distinguishable name through the original name editor, record
   the selected country and visible starting attributes, and confirm the final
   affirmative choice. Exact setup label positions and country order have not
   all been decoded; follow the visible English screens rather than assumed
   button counts.
4. Reach a settled weekly schedule. Actual hidden acceptance starts at
   September 1 after the initial staff introductions. Capture the protagonist,
   country, date and status. Record the three calendar halfwords below as optional read-only
   corroboration.
5. Complete one available original **Rest** or **Training** schedule action and
   all resulting dialogue. Return to a settled schedule and capture the changed
   week/date and any changed status. Viewing a status screen alone does not prove
   progression. One ordinary weekly action is the minimal progression check;
   full three-year completion and match participation require further coverage.
6. Open the schedule's **Options** icon and choose **SAVE END**. Confirm saving
   to the selected Career file. Follow any original Data Change/save prompts
   with their save/affirmative choice and wait for the original saved/completed
   confirmation before exiting. Career leaving the screen by itself does not
   prove that the Controller Pak was written.
7. Record the resulting Pak image hash and original save confirmation, exit
   cleanly, and restart the same portable build with its same PAL data directory
   and Controller Pak selection. Do not restore or inject a fabricated save.
8. Re-enter Career and choose the **same now-occupied slot**. Confirm the unique
   protagonist, country, progressed date and relevant status match the saved
   checkpoint. Perform one further normal schedule action to show the reloaded
   Career remains playable. Keep the existing file unless intentionally saving
   this additional progress through the same original flow.

The scanned original manual supports country/player setup, weekly schedule
choices, and Options → SAVE END. Its generic file-selection wording is refined
above by PAL code, which exposes two slots. The PDF filename says USA despite
English/German content; use it as a mechanics lead, not PAL identity proof.
[Original manual, printed pages 15–16](https://www.videogamemanual.com/n64/International%20Superstar%20Soccer%202000%20(USA).pdf).

## Entry, file selection and new versus existing Career

Original main-menu handler `803C2CEC` bounds nine rows; cursor 1 reaches case
`803C2D38`, storing mode 5 at `8012DE74`. The mode-to-common-page dispatcher
`803C2E2C` maps mode 5 to common page 3. Original page table `801E2D80` selects
`801B8DF0`, which loads the actual Career banks through resident loaders and
enters Career title `803D1C08` in ROM-owner `57F870`, VRAM `803D1A30`.
The original title update `803D1CB4` accepts the game's A/Start mask `9000`.

File selection enters `803D28E8`, refreshes occupied flags through
`803D29BC`, and dispatches input in `803D2D98`:

| Original field / operation | PAL guest address |
| --- | --- |
| File cursor | byte `803D3480` |
| Two occupied flags | bytes `803D4020..803D4021` |
| Chosen Career slot | byte `8012958C` |
| File Accept handler | `803D2E30` |
| Existing-file unpack route | `803D2F00 -> 80216410` |
| New/existing branch | `803D2FD0` |

Cursor values 0 and 1 are the two Career slots. Value 2 enters deletion mode
and is disabled when both slots are empty; it is not a third Career or Cancel.
The normal Accept dispatch is `803D2DFC -> 803D2E30`; deletion mode redirects
Accept to `803D30C8`, while B dispatch `803D31B4` handles cancellation. Accept stores the
selected slot in `8012958C`. An occupied flag of 1 loads that original slot;
empty slots follow the new-profile route through common `801B901C`,
`801B906C` and setup `803C523C` in ROM-owner `572EB0`.
Initialization `803C545C` clears and constructs the actual Career state.
Do not call these functions from a host shortcut to manufacture acceptance.

## Progression observables

Career state begins at `80128E38`; original initializer `801F62E0` clears
`6DC` bytes. Three halfwords form the original calendar tuple:

| State field | Guest address | Original new-profile value |
| --- | --- | --- |
| Year index | `80128EF2` (`state+BA`) | 0 |
| Month index | `80128EF4` (`state+BC`) | 8 |
| Week index | `80128EF6` (`state+BE`) | 0 |

Original `801F690C` increments the week, rolls at four, rolls month at twelve,
and increments year when entering month index eight. `801F2A30` is a normal
progression caller. Calendar/index consumers include `801F6380` and
`801F69BC`. The visible English month-name mapping is still to be confirmed;
index 8 alone is not a screenshot of a named month.

Forecast routine `801F5E18` also calls the date advance temporarily and then
restores the tuple. Consequently transient writes or an isolated call are
insufficient evidence of progression. Compare settled schedule screens before
and after an original player action. All three calendar fields are present in
the original packed Career save table.

## Original Save End and staged Career record

The original 98-entry Career event dispatch table at `801FA7A8` selects
`801F0840` for event ID 21. This installs `801F1148`, which runs confirmation
script `1FB` and then `801F1174`. Event 21 is an internal script ID, not a
claim that Save End occupies visible menu row 21.

After original script completion, confirmation halfword `80129156` selects:

| Value | Actual original behavior |
| --- | --- |
| 0 | Pack chosen Career slot, then leave Career |
| 1 | Leave without packing this Career state |
| 2 | Return to Career interaction |

Save branch `801F11C8` calls `80216328` with the selected byte at `8012958C`.
That serializer reads the complete original field table at `8021E6B0`, ROM
`52F0D0`: 368 entries of pointer plus bit count, followed by a zero terminator.
Their widths total 1244 bits, occupying 156 meaningful bytes. Original bit
packing uses helpers `802161A0` / `802161E4` and scratch `80256FF5`, then copies
160 bytes into the selected original record. The remainder is original copied
padding; do not assume a separate save version or zero-filled padding there.

| Career save structure | Original PAL value |
| --- | --- |
| Number of files | 2 |
| Record base | `8016C094` |
| Record stride / CRC extent | `A2` bytes = 162 |
| Slot 0 / slot 1 | `8016C094` / `8016C136` |
| Offset inside whole note payload | `5EA4` |
| Used flag | record byte 0 = 1; empty marker `FF` |
| Packed data | record+1, copied length `A0` = 160 |
| CRC words | `80166228` / `8016622C` |
| Global dirty flag | byte `8012E688` |
| Dirty field bits | word `8012E68C`, bits 12 / 13 |

Original `8001B93C` marks the record, sets dirty state and stores its CRC from
`8001BA70`. The latter covers the complete 162 bytes with original CRC
`8000A3D4`: polynomial `04C11DB7`, initial `FFFFFFFF`, final complement,
most-significant bit first. Original load `80216410` calls `8001B9DC` to
validate occupied state and CRC, then unpacks the same table with `80216290`.
The setup/file display also unpacks original slots into temporary state copies
for their previews; that display is not proof of restored playability.

The two Career files are separate from the five containers of 22 registered
players. The 110 registrations hold created/exported players and do not mean
110 independently resumable Career saves. See `pal-roster-database.md` for the
Career-completion-to-registration bridge.

## Physical note identity and persistence boundary

The original PAL note descriptor is guest `80077590`, ROM `78190`:

| Metadata | PAL original value |
| --- | --- |
| Game / company code | `NISX` / `A4` |
| Payload bytes | `7A00` = 31,232 |
| Data pages | 122 of 123; one data page remains |
| Extension | four zero bytes |
| N64 filename bytes | `223c2c3c2c3c121010100f0f0f0f0f00` |
| Runtime payload base | `801661F0` |

Original save manager `80019A64 -> 80019B04 -> 80019B94` validates data and
calls `80004B58` for a complete `7A00`-byte write. The wrapper invokes original
SDK `osPfsReadWriteFile` at `80060140` with direction 1. Original load
`800198C8 -> 80004AE4` uses direction 0 for the same whole payload.
Successful writer `80019B04` clears the global dirty flag; an error does not.

Packing via `80216328` changes RAM and dirty bits. A full successful original
write and the saved message establish a stronger checkpoint; only a new process
reopening the note and restoring the same playable Career establishes
persistence. Keep those observations separate in acceptance reporting.
The native Controller Pak image is `saves/controller-pak-1.mpk` under the active
portable data directory. Both Career files share the same original NISX note.

No original semantic save-format revision integer has been established here.
The exact ROM profile/revision/digest and original note metadata are pinned
separately. The payload's first word is assigned through `80019D5C`, which
combines original time/random-related results and another state word; it is not
proved to be a format-version constant. Do not invent or overwrite an original
revision field. US NISE/`7900` notes are a different identity/layout. Future
roster-pack namespaces must keep their own compatibility metadata outside the
unchanged original Pak bytes.

## Private evidence and remaining limits

`.local/pal-career-01/report.json` pins 46 original function bodies, the entire
368-entry packing table, dispatch table, Career slot/CRC layout, calendar fields
and original note descriptor. Reproduce it with that directory's
`pal_career_evidence.py`; it reads only the pinned PAL ROM/section map and writes
its private report. It executes no translated game code.

No country/menu text atlas was fabricated or transferred from US. Exact setup
menu row labels, a complete normal week event transcript, actual Pak changes,
and restart/reload screenshots remain to be captured. A successful weekly
round trip supports early Career playability and persistence; it does not by
itself establish complete three-year progression, every Career match, all
branches/endings, or completed-player export.

## Refined weekly navigation and confirmation order

Additional static PAL analysis pins the ordinary weekly menu and its Save End
submenu. Original `802145F0` chooses among primary lists `8021E228`, `8021E248`
and `8021E26C`, depending on Career state. The first two contain event IDs
`[0,1,22,2,4,33,5]` and `[0,1,22,2,4,33,5,6]`; their `99` marker terminates the
list. Some periods use a reduced list instead, so select visible labels rather
than assuming a fixed number of presses from the top.

Primary event 5 builds the submenu through
`80214FD4 -> 8021505C -> 80214384`. The exact original table `8021E3A0`, ROM
`52EDC0`, contains three entries:

| Visible submenu position | Original event | Meaning established by original continuation |
| --- | --- | --- |
| Left | 35 | Original controller icon, verified in hidden captures 091–092 |
| Center | 21 | Save End confirmation and original Career serializer |
| Right | 46 | Return from submenu |

Opening this submenu through original `802153D8` resets its active cursor to
zero at `80215464`. Actual hidden captures 091–092 establish that these entries
are horizontal; the earlier static Down inference is superseded. Therefore, after opening the visible **Options** menu,
release the input, tap Right once, release, and Accept to choose its center
**SAVE END** entry. Its English confirmation script is original root script
`1FB`, which branches to bank 6 offset 1. The source is compressed original
asset `1C0` (448), decoded offset `16E1`. Its choices are, in order:

1. **End after saving.** — serialize the chosen original Career slot.
2. **End without saving.** — leave without serializing this Career state.
3. **Return** — resume Career interaction.

Select the first choice and follow the genuine Pak write flow described above.
The menu label is not a promise that a Pak write succeeded; retain the actual
save confirmation and the clean restart/reload check.

Rest is original event 1, dispatched by `801F0768`. When its eligibility check
selects the ordinary resting path, script `211` reaches English bank 26 offset
0; its text includes “I'm going to take it easy this week.” Situational stories
can replace that ordinary path. Compare settled calendar tuples before and
after the chosen action rather than assuming one dialogue always advances a
week. Original `801F2A30` remains the normal calendar advance consumer.

The Test Match dialogue uses a different chooser. Visible capture 217 showed
that its initial cursor was unselected: the first Down selected **Play Game**;
it did not select **View Results**. Once Play Game is visibly selected, another
Down selects the second original row. Both labels are present in English asset
`1C2` (450), decoded offsets `5EB6` and `5EC3`. This analysis does not establish
whether View Results completes every forced trial or only a particular match
branch. The acceptance operator completed the forced trial naturally instead,
reaching its original post-match story (captures 218–219). No shortcut,
fabricated result or forced callback is required for that observed path.

Reproducibility/provenance for these table, handler and compressed-script
observations is private under `.local/pal-career-navigation-02/`. The research
performs only bounded ROM reads and script decompression; it does not execute
the game, mutate guest RAM or create a save.

## Hidden Linux save acceptance and user-owned remaining checks

The later build32 acceptance used a separate private data folder and an actual
hardware-GPU headless Gamescope compositor, following the user's requirement
that all remaining game windows stay hidden. App-only SDL controller inputs
reached original code; this is not physical-controller verification. A new
Career profile A used the original View Results choice for its trial, reached
the September 1 weekly menu, rested to September 2, selected Options → Save End →
End after saving, and completed the separate genuine Pak confirmation. The
original UI reported Saved. A normal process exit and a clean launch of the
same exact executable loaded file1 A at September 2; another original Rest
advanced it to September 3. The persisted September 2 Pak remained unchanged.
Private receipt: `.local/career-acceptance-02/acceptance.json`.

A separate build35 data copy exercised original Edit Team and Edit Formation,
changed England from 4-4-2 to 4-3-3, and saved formation file1. Its original UI
reported Saved and its private Pak digest changed. The user then explicitly
assumed the remaining editing, Training and League tests. Agent testing stopped
before formation reload; no Training or League acceptance is claimed. Both
owned games exited normally and their private compositor closed. The original
Career acceptance and its saved Pak remain separate. Private partial receipt:
`.local/menu-acceptance-01/acceptance.json`.
