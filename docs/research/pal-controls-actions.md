# PAL football actions and original control profiles

Original project work: djultra64. Research checkpoint, 2026-10-15.
The user supplied primary PS1 controller-menu recordings after the earlier
manual search. The pure host scheme module implements those four original
layouts, an explicitly adapted eFootball Type 5, and Free. Screen integration,
persistence and real-controller acceptance remain separate work.

## Evidence boundaries

The PAL N64 input is English/German revision 0, SHA-256
`6ce6739b8ead149857c9442178a1ecd9b7f6d15b93a582c7208ca85d493817bf`.
The original [N64 instruction booklet, USA scan](https://www.videogamemanual.com/n64/International%20Superstar%20Soccer%202000%20(USA).pdf)
provides the action names and Type 1 icons on printed page 20 (PDF page 22),
Curve on printed page 21 (PDF page 23), and contextual R-button uses on those
pages. Page 20 also states that L can activate Z-button actions. The scan is
primary documentation for the N64 game, not proof about the PS1 release or
all regional alternate-profile layouts. Its diagrams were inspected visually;
OCR alone confuses C-button arrows and numbered Types.

## Primary PS1 menu recordings and host schemes

The PAL PS1 KCEO releases are SLES-02550 (English/German) and SLES-03149
(French/Spanish/Italian). The user's two recordings show the actual Spanish
controller menu with four numbered Types and Free; they supersede the earlier
unverified secondary-only Type 1 research. They are private references, not
redistributed UI assets:

| Recording | SHA-256 |
| --- | --- |
| `2026-10-15 18-59-43.mp4` | `3ca526d67b6e4361af80ab2d37f3c304e48bf8a16baff650a7dd3bd1eed60a1f` |
| `2026-10-15 19-00-47.mp4` | `b1183e7bfe60817763277645b500eb2663960d18e237e029a2417a37bd1e3d09` |

The first recording contains Types 1–4 (Type 4 around 21 seconds); the second
shows Free editing with occupied assignments exchanged. Private contact sheets
are in `.local/control-video-reference-01/`. The video is displayed stretched;
the port must reuse its own original assets and preserve their proportions.

| Action | Type 1 | Type 2 | Type 3 | Type 4 | Type 5 adaptation |
| --- | --- | --- | --- | --- | --- |
| Pass | Square | Cross | Cross | Cross | Cross |
| Shoot | Triangle | Square | Triangle | Square | Square |
| Dash | Cross | Circle | Square | R1 | R2 |
| Lob | Circle | Triangle | Circle | Circle | Circle |
| Through | R1 | R2 | R2 | Triangle | Triangle |
| One-two | L1 | L2 | L2 | R2 | R1 |
| Curve | L2 | L1 | L1 | L2 | L2 |
| Cursor | R2 | R1 | R1 | L1 | L1 |

Type 5 uses the six basic positions in Konami's original
[eFootball PS5 controller diagram](https://img.konami.com/efootball/s/img/manual/efootball2023_ps5_en.pdf).
One-two on R1 and Curve on L2 are explicit ISS adaptations. This does not
reproduce eFootball's complete mechanics or compound one-two command. The
single-action bijection preserves all eight existing ISS actions and permits
predictable Free swaps. Original Types 1–4 are unchanged by that adaptation.

The pure module stores physical positions South/East/West/North and L1/R1/L2/R2,
not printed face-button letters. PlayStation Cross/Circle/Square/Triangle map
to South/East/West/North; Xbox A/B/X/Y occupy those same positions. Nintendo
labels require the active-family prompt adapter. Triggers are positions,
not invented SDL button indices. Free maintains a complete eight-position
permutation by swapping the displaced action onto the edited action's former
position. Invalid maps or enum values fail without modifying the map.

## Exact N64 Type 1 input boundary

These are guest N64 pad bits, before the original football input normalizer.
Physical host buttons must remain separate from these internal identifiers.

| Football action | Original N64 Type 1 button | Guest pad bit | Normalized football bit |
| --- | --- | --- | --- |
| Pass | A | `8000` | `0004` |
| Shoot | B | `4000` | `0008` |
| Dash | C-down | `0004` | `0002` |
| Lob / fly ball | C-left | `0002` | `0001` |
| Through pass | C-up | `0008` | `4000` |
| One-two pass | C-right | `0001` | `8000` |
| Curve / special modifier | Z, with L alias | `2000`, `0020` | Same bits retained |
| Change player / pass cursor | R | `0010` | Same bit retained |

These labels describe the primary football actions. The original game gives
the same buttons contextual roles: for example R also selects a pass teammate,
enables a no-search pass, and modifies a shot; Z/L also perform special moves.
A host preset must preserve those original contextual uses rather than replace
them with isolated scripted actions.

## ROM table, selection and normalization

Resident table `800774F0` maps to ROM `780F0`, length 36 bytes, SHA-256
`12f1ff9761cd1fbb2a14411d3fb38abcbed37b37ae700a9fe872deb08a385633`.
Each record contains six big-endian halfwords in this order:
One-two, Through, Dash, Pass, Shoot, Lob. Exact PAL bytes are:

| Original profile index | Six guest masks |
| --- | --- |
| 0, original Type 1 | `0001 0008 0004 8000 4000 0002` |
| 1 | `0001 0008 4000 8000 0002 0004` |
| 2 | `8000 4000 0002 0004 0008 0001` |

The host bridge supports all three genuine guest profiles separately. Host
Types 4 and 5 and Free never become out-of-range guest profile indices. Do not
substitute alternate layouts copied from another regional manual for these
actual PAL bytes.

Original resident `8002D8C0` initializes all four ports to record 0. The real
controller menu commit `802C53A4`, in overlay ROM `40C7A0` / VRAM `802C3490`,
reads per-port choice byte `802D21E4 + port`, multiplies it by 12 and calls
`80014A74`. Resident public selector `80014A3C(port, profile)` selects the same
table and calls the same copier.

The copier writes the six masks at `801274DA + port * A8`. Each original
football controller context begins at `80127468 + port * A8`, so the masks
are offsets `72..7C`. It also sets context offset `24` to the original pad
packet at `8013B454 + port * A`; this is a genuine four-port input boundary.

Gameplay overlay `25AAF0` / VRAM `801AD820` contains normalizer `801D4880`.
At `801D4898..48B8`, it retains the original pad packet's modifier/navigation
bits using mask `3FF0`. At `801D48BC..4918`, it loops the six selected masks,
ANDs each with the original packet, and ORs the corresponding canonical bit
from `801D9A70` into normalized context fields `66` and `68`. The original
packet offsets are `4` and `2` respectively. It never rewrites that packet
in the tested conversion path.

The canonical six-word table is ROM `286D40`, length 12 bytes:
`8000 4000 0002 0004 0008 0001`, SHA-256
`83b883595d4b6130ca2a6dfa1a3a3702c1d5da077c96e485d696c98593c56a89`.
Thus a normalized football bit is not always numerically equal to its original
N64 pad bit. Feeding normalized Pass `0004` directly as a guest pad value
would request Type 1 Dash, not Pass.

Z/L/R are outside the six-word table. Their original bits survive `3FF0`.
Original consumers explicitly test `2020` for Z/L together, including
`801D4880` at `801D498C` and `801D5458` at `801D54E8/5540`.
The original R test at `801D4954` examines normalized field `66`, and
`801D7D30` at `801D7E40..7E4C` examines controller field `68 & 10`.
These source identities include the overlay, since equal VRAM addresses in
other overlays do not identify the same function.

## CPU verification and limits

Private `.local/pal-control-actions-01/` contains a reproducible script, fixture
and hash receipt. It compiles the unmodified original `8002D8C0`, `80014A3C`,
`80014A74` and `801D4880` translations against the pinned recompilation header.
The fixture seeds the two tables from the exact PAL ROM bytes, runs the real
initializer and public profile selector, then checks every one-hot table position and
R/L/Z through the real normalizer for all three profiles and all four ports:
**108 cases pass**. Original input packets and stack return are preserved.

The fixture selects the normalizer's genuine mode-14 early-return branch after
conversion. It proves table installation and pad-to-action normalization, not
the semantic names previously assigned to those table positions, all later
player/ball state machines, a complete match, host bindings, physical
controllers or rendered prompts. No emulator, full game or Windows process was
run for this research.

`tests/test_controller_schemes.py` includes six focused checks:
the video layouts, adapted Type 5, atomic Free swaps/port isolation, the primary
N64 manual across all three genuine profiles, all five presets through unchanged
original `801D4880`, and the original held-Dash consumer `801D4F88`. The normalizer
checks **480 cases** (5 presets × 3 genuine guest profiles × 4 ports × 8
actions), including unchanged original input packets. All six tests pass with
zero skips when the private PAL input and pinned translation are present.
This proves the action bridge, not rendered labels, menu commit/persistence,
physical gamepads or full gameplay integration. Direction and Start remain
outside the football action map; generic menu input must retain its normal
behavior.


## Scoped live-context football input bridge

`pal_football_input` adapts only the active original `801D4880` football
normalizer. Its caller must verify the exact registered PAL function identity,
select a gamepad rather than keyboard input, and supply the latest genuine SI
sample's eight-position held and pressed masks. No menu buttons or raw shared SI
packets are rewritten. Pressed must be a subset of held; samples are not
accumulated between SI reads.

The bounded helper requires exactly 8 MiB of RDRAM, a canonical original
controller context `80127468 + port * A8`, its exact original source pointer
`8013B454 + port * A`, and one of the three six-halfword PAL profiles. It also
checks the canonical normalization table and validates the physical bindings.
The incoming main-thread stack must be eight-byte aligned in
`800A06F8..800A42D8`, allowing a new 32-byte caller frame and a conservative
1 KiB margin below it inside the original main-stack allocation.

The helper copies the original ten guest bytes into that reserved frame, beyond
the normal argument area, and replaces only scratch offsets `2` (held) and `4`
(pressed). The mapped football bits are combined with each original field's
`1F00` direction/Start bits. Connection/status and both signed sticks retain
the exact source bytes. Guest byte order matters: the ten-byte per-port stride
means ports 2 and 4 are not word aligned, so a raw memory copy between source
and scratch would be incorrect.

Only controller-context offset `24` temporarily points to scratch. The unchanged
original normalizer executes once with the live CPU context, including its
modifier flags, previous-held state and filtered release calculations. On normal
return or a C++ exception, the original packet pointer, incoming stack pointer
and entire reserved 32-byte frame are restored. All other genuine CPU and game
state effects survive; no context/FPU copy is made.

Original `8000453C` establishes source offset `2` as held and offset `4` as
`new & (old ^ new)`. Original `801D4880` has no source-packet writes and no
source-pointer storage escape. Its conditional `801D4540` closure passes the
controller to `801D5168` and `802A7CEC`/`802A7B14`, whose inspected paths use
normalized context fields rather than offset `24`; other callees receive
player/world pointers or scalar arguments. The four actual callers are
`801D5A74`, `801D5E1C`, `801D5EA4` and `801D5FE8`. Their post-call code reloads
needed packet pointers or overwrites caller-saved registers before using them;
they do not retain the temporary source through returned `r8`/`r3` aliases.

`tests/test_pal_football_input.py` executes the original full normalizer through
**2,304 press/hold/release frames**: five presets plus an edited Free layout,
three original profiles, four ports, eight actions and four frame states.
It additionally checks fifteen invalid-boundary cases without any mutation,
exception restoration while retaining live register/FPU effects, and a genuine
conditional call into original `801D4540` using its original early-return
condition. All four focused tests pass, with zero skips when private originals
are available. This proves the bounded bridge and tested original paths;
physical controller delivery and complete gameplay/UI integration require
separate acceptance.


## Device preferences stay separate from football schemes

PC Settings → Controls → Player now contains only Controller type (Auto, Xbox,
PlayStation or Nintendo), Vibration and Back. These are per-port device
preferences in the same Save/Cancel transaction as graphics. Keyboard is not a
manual controller-family override. The obsolete raw N64 button editor is no
longer reachable from this flow; its compatibility callback is never invoked.
Original Type 1–4, adapted Type 5 and Free belong to the authentic pre-match /
Training Controller screen instead.

The retained Controls and Player pages use the original Options CI4 row face,
including the intact original Player word, existing Rumble composition for
Vibration and bounded Controller composition from already verified source
columns. Family names and values use the original secondary font. Tests check
actual original constructor/draw commands, per-row CI4 pixels and selected
palettes. This is CPU verification; updated whole-page GPU acceptance is tracked
separately by the parent task.


## Correction after r52: semantic ROM slot order

The former document and host conversion table confused three N64 C-button masks.
The raw masks are C-down`0004`, C-left`0002`, C-right`0001`; their former
`0001/0004/0002` labels were wrong. The primary booklet's printed20/PDF22 attack
table gives Type1 Dash=C-down, FlyBall=C-left, OneTwo=C-right. Its Types2 and3
independently agree with every corresponding mask in the unchanged PAL ROM table:
Type2 Dash=B, FlyBall=C-down, OneTwo=C-right; Type3 Dash=C-left, FlyBall=C-right,
OneTwo=A. The actual six ROM slots therefore mean OneTwo, Through, Dash, Pass,
Shoot, Lob. Merely executing the original normalizer never established the names
attached to those slots; the previous tests repeated those mistaken names.

The host `FootballAction` order remains Pass, Shoot, Dash, Lob, Through, OneTwo,
Curve, Cursor. The corrected original guest masks in this order are:

| Guest profile | Correct semantic action masks |
| --- | --- |
| 0 | `8000 4000 0004 0002 0008 0001 2000 0010` |
| 1 | `8000 0002 4000 0004 0008 0001 2000 0010` |
| 2 | `0004 0008 0002 0001 4000 8000 2000 0010` |

For every profile, the original normalized action bits in that same semantic
order are `0004 0008 0002 0001 4000 8000 2000 0010`. Physical Type1..5 and Free
positions are unchanged. For Type5 specifically, R2 now feeds genuine Dash,
East feeds FlyBall/Lob and R1 feeds OneTwo. The former conversion instead sent
R2→OneTwo, East→Dash and R1→FlyBall. Pass, Shoot and Through were already correct.

A new primary-manual regression failed against the former conversion before this
correction. It asserts all24 action masks across the three profiles using the
manual's actual buttons, independently of the implementation's table layout.
The480 original-normalizer cases now use the corrected semantic expectations.

The downstream proof additionally executes genuine original `801D4F88` after
`801D4880`. At `801D4F8C/4F90`, the held-Dash consumer tests context`+68 &0002`;
it increments context`+84`, and after five held frames for the ball-holder sets
context flag`0400` at `801D4FE4` and clears controlled-player`+C4 &0100` at
`801D4FF4`. Release resets the counter. The new Type5 R2 closure proves these
actual downstream changes across all three profiles and four ports. Its negative
control feeds each former incorrect Dash mask, which normalizes to`8000`, and
proves the held-Dash counter/flag never activates. This covers144 original CPU
frame states, not merely a comparison against another copy of the host table.
No game/window or Windows execution was performed for these focused tests.
