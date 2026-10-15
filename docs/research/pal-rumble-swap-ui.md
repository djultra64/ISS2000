# PAL Rumble Pak swap-notice routing

Original project work: djultra64. Static research and isolated CPU fixtures:
2026-10-15. No game was launched by this task.

The PC port omits the original physical **Rumble Pak swap notice** by using
already-existing original menu continuations. The five original UI callers
still run their genuine accessory probes and retain their results. The change
is confined to their decision to queue the Rumble-specific modal script;
it does not manufacture a successful SDK initialization, edit input bits,
change the save filesystem or suppress Controller Pak errors.

## Original presentation and continuation proof

The original common UI overlay is loaded from ROM `2DEE70` to `801AD820`.
Its specific Rumble request starts at `801E334C`; the script refers to its
Rumble presentation sequence at `801E3330`, which uses the text descriptor
`801BFBD8`. The descriptor's translated source pointer at `801ED5E0` receives
English message `801EEF18` from the original language tables. That message is
114 bytes including its `FF11` terminator, ROM `316C18`, SHA-256
`7b7805919bd1bb1df64d63d80d47ca48a2262033fe7ce2c214bde56a95d865b0`.

The Controller Pak request is a different script at `801E33B4` inside the
sequence beginning `801E3394`. It uses descriptor `801BFC08`, translated pointer
`801ED620`, and English message `801EEF8C` at ROM `316C8C`. Neither that script,
its message nor its callers are modified. Other save/create/error prompts and
original filesystem code also remain outside the derivative inputs.

The original `801B9654` checks the motor-availability mask from original
`800072B4` against the original configured-player group. Original `801B96D4`
checks only P1. The mask producer queries the original controller status, calls
original `osMotorInit` at `8005F8A4` for each applicable port, and sets a bit
only on actual success. These original probe functions are retained.

Exactly five classified original callers request script `801E334C`:

| Original caller | Owning overlay ROM / guest | UI branch changed | Existing nonmodal continuation |
| --- | --- | --- | --- |
| `802B5574` | `3FC9F0` / `802B35B0` | `802B55CC` taken; `802B55E8` not taken | Register original callback `802B56C0` |
| `802BA770` | `401910` / `802B8500` | `802BA7A0` not taken | Register original callback `802BA860` |
| `802BE1B8` | `401910` / `802B8500` | `802BE1E4` not taken | Register original callback `802BE29C` |
| `802C6D34` | `40C7A0` / `802C3490` | `802C6D90` not taken | Register original callback `802C6E60` |
| `803D2F34` | `57F870` / `803D1A30` | `803D2F48` not taken | Call original Career continuation `803D2FD0` |

The Career continuation chooses its original next stage from the selected
original slot's occupied flag: existing file uses stage 1, empty file uses stage
2. It does not create a player, load invented state, force progression or skip
a save. The other callers retain their original validation/ready/exit branches.

Routing occurs before original `801AE594` queues the modal. No popup is queued
and then hidden for a frame, and there is no synthetic global Accept press.
The derivative retains every original probe call, its register result,
all branch-delay instructions and all remaining original instructions.

## Private generation and runtime integration

`tools.prepare_pal_rumble_ui` pins the complete PAL ROM SHA-256, the complete
original body hashes and exact generated-source hashes of these five callers.
It makes private C++ derivatives with distinct exports. Original ROM and CPU
translation files are read-only inputs. It rejects changed/missing inputs,
symlinked output paths and modified existing outputs. Identical outputs can
be verified on every build.

```sh
python3 -m tools.prepare_pal_rumble_ui \
  --rom .local/inputs/pal-en-de/rom.z64 \
  --generated .local/pal-map-bound-01/functions \
  --output PRIVATE_BUILD/pal-rumble-ui-v1
```

Outputs are `pal_rumble_ui_ADDRESS.cpp` for the five addresses above and
`receipt.json`. Each export is `iss2000_pal_skip_rumble_ADDRESS`, using
`extern "C" void(uint8_t*, recomp_context*)`. Runtime lookup must select a
replacement only for the exact corresponding active original function pointer;
guest addresses alone cannot distinguish overlapping original overlays.
Compile all five sources and rerun the generator as a build dependency.
The receipt records original bounds/hashes, changed UI branch PCs, generated
source hashes and exports without local-machine paths.

Private `.local/pal-rumble-ui-01/evidence.json` records additional original
probe/continuation bodies and the distinct Rumble/Controller Pak script/text
hashes. Its `generated/receipt.json` binds the five implemented derivatives.
Neither original assets nor generated original CPU code is distributed.

## Verification and limitations

`tests/test_pal_rumble_ui.py` has three checks. Its isolated native fixture
compiles the five original callers, their derivatives, original four-port
motor-mask producer, both original probe predicates and original Career
continuation. Original shared-overlay data supplies the predicate's genuine
jump table. Controller query, motor service and unrelated rendering/scheduler
boundaries are controlled fixture callbacks, not gameplay or hardware proof.

Across 450 caller/player-layout/motor-result/slot combinations, the original
missing-motor path queues the notice while the derivative queues none. Both
paths keep all four applicable motor probes. The fixture observes the unchanged
missing-motor predicate value at the original registrar, verifies original
continuation targets and both Career slot outcomes, and compares full RAM for
already-nonmodal and unrelated validation/ready/exit paths. The behavior check
first failed on renamed unchanged originals because the modal was still queued.
Identity tests reject wrong ROM/source bytes and changed existing output.

All three focused tests pass with private fixtures present. This does not
establish visible integrated menu acceptance or real controller vibration.
Root owns the native lookup/CMake wiring and subsequent visible checks.

Current haptic routing remains a separate limitation: SDL reports actual rumble
capability, but the device callback and polling path also require a selected
virtual Rumble Pak. A selected Controller Pak therefore cannot currently vibrate
through that route. `osMotorInit` still performs real upstream OSPfs setup;
only its absent-Pak result is translated to device-type error 11 for a selected
Controller Pak. No success is invented. Simultaneous virtual save storage and
modern haptics needs an explicit capability-based host design, independent of
this UI-only change.
