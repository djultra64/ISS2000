# PAL enhanced-memory notice routing

Original project work: djultra64. Static evidence and isolated CPU fixtures:
2026-10-15. No game was launched by this task.

The PC port omits only the informational “Memory Expansion Pak enhanced” notice.
Actual 8 MiB boot detection, memory configuration, original high-memory buffers
and later Controller Pak save/error/create paths stay original. The replacement
uses the original selector's already-seen continuation before any notice is
queued. It never injects an Accept press, invents an SDK result or claims memory
exists when it does not.

## Original owner, message and state

The Data Change UI owner is the original CPU overlay loaded from ROM `481680`
to guest `802B1070`. Its selector `802B1FDC`, ROM `4825EC`, size `13C`, writes
message-state byte `802B4819`. Parent initializer `802B1CC8` calls that selector
before queuing its UI script `802B4334` through original `801AE594`.

Original message dispatcher `802B181C` indexes table `802B40F4` with this state.
The three nearby states are distinct:

| State | Original table entry points to | Translated English source | Meaning |
| --- | --- | --- | --- |
| 14 | `802C4FEC` | `802DDB2C` | Enhanced-memory informational notice |
| 15 | `802C5034` | `802DD8C0` | Controller Pak insertion/save flow |
| 16 | `802C50A0` | `802DDB74` | No Expansion Pak detected |

State 14's complete English message occupies 69 bytes at ROM `51507C`, SHA-256
`8d057ca0a914891920b0ec232acfead532118e40c0a1c45bcd81c98e744f7af0`.
Original language setter `802DD400` copies pointer-table entry ROM `514828`
into `802C4FEC`; the source resides in the original language-data load beginning
ROM `514950` at guest `802DD400`. This chain identifies the message independently
of its approximate RAM location or a screenshot.

The original selector enters its enhanced-memory path only when actual context
byte `8013B429 == 1`. It then checks informational sentinel `803FFFFF` against
`C9`, boot word `8000030C`, and the original context's bit 29. These conditions
can select notice 14 and set the informational sentinel. The original skip
continuation at `802B2060` handles the subsequent genuine context/accessory
checks without selecting notice 14. It can retain message 15 and all subsequent
Controller Pak handling. An informational dismissal must not be confused with
a successful Controller Pak save or an initialized motor.

## Bounded derivative

`tools.prepare_pal_expansion_ui` verifies the exact PAL ROM, original selector
body and original generated-source hashes. Its sole behavioral change makes
original branch `802B2024` take the existing `802B2060` continuation. The branch
is reachable only inside the original high-memory path. Its original delay-slot
assignment is retained; no physical-memory, context, filesystem or input field
is fabricated or rewritten by a host helper. The informational sentinel is not
falsely marked acknowledged.

The original low-memory and unknown-context paths do not reach this changed
branch and remain byte-identical in the isolated RAM comparison. State 16 is
retained; it is outside this Enhanced-notice request. Controller Pak state 15
is also retained, including in the actual parent-initializer fixture. Later
save/error/corruption handlers are neither inputs to this generator nor replaced.

```sh
python3 -m tools.prepare_pal_expansion_ui \
  --rom .local/inputs/pal-en-de/rom.z64 \
  --source .local/pal-map-bound-01/functions/func_802B1FDC_overlay_481680_802b1070.c \
  --output PRIVATE_BUILD/pal-expansion-ui-v1
```

Outputs are `pal_skip_expansion_notice.cpp` and `receipt.json`; the export is
`extern "C" void iss2000_pal_skip_expansion_notice(uint8_t*, recomp_context*)`.
Root must dispatch it only while the exact active original function pointer is
`func_802B1FDC_overlay_481680_802b1070`. Compile the derivative and rerun the
identity/output check as a build dependency. Existing outputs are accepted only
if every file is identical. Symlinked output paths and changed inputs/outputs
are rejected. The receipt contains no developer-machine paths.

## Evidence and acceptance limits

`tests/test_pal_expansion_ui.py` has three focused checks. Its behavior fixture
executes the genuine generated original selector, its derivative and the genuine
parent initializer with bounded controlled UI-service callbacks. Across 192
memory-context/sentinel/boot/acknowledgment/accessory combinations, enhanced
contexts select the same subsequent state and produce the same entire 8 MiB
image as the original already-seen continuation, after restoring only reference
fixture input differences. Other contexts match the original selector exactly.
Actual memory/configuration fields are unchanged. The parent fixture verifies
that its queued script sees Controller Pak state 15 and never Enhanced state
14. This is isolated generated CPU execution with synthetic RAM, not gameplay,
SDK hardware or visible acceptance.

The behavioral regression first failed against the unchanged, renamed original
selector because state 14 was still selected. All three tests pass after the
bounded change. Further tests reject wrong ROM/source bytes and modified existing
outputs. Private `.local/pal-expansion-ui-01/evidence.json` records original
body/table/message hashes, and `generated/receipt.json` binds the derivative.
Native integration and a fresh visible boot remain root acceptance tasks.
