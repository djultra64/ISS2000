# PAL full-detail interpolation task budget

Original project work: djultra64. Investigation date: 2026-10-17.

## Confirmed failure

The r55 all-22-player visibility correction increased genuine display-list
traversal beyond the transform metadata parser's 16,384-slot limit. A complete
scan is required before publishing model references. Exhaustion discarded all
references, including the known perspective bank, while original rendering
continued. Consequently a valid task snapshot could have zero model and camera
interpolation groups. This is independent of FIFO quarantine and does not prove
the cause of the separately reported black screen.

The first-friendly field segment in private
`.local/consecutive-r56-baseline/render.jsonl` had `snapshot:true`, scene 1540
(hexadecimal 0604), and repeatedly zero model/camera groups. The bridge does not
exclude the r55 extended matrix banks: snapshots support the complete 8 MiB
address space, and frame validation accepts both exact extended bank ranges.

## Original captured-task reproduction

An offline native parser probe read existing private RDRAM captures without
executing original game code or modifying the captures. Each row gives total
traversed 64-bit slots and collected model LOADs, including repeated sublists.

| Private capture | Root | Slots | Model LOADs |
| --- | --- | ---: | ---: |
| corrections-r55/baseline/field-a.rdram | 800D0328 | 10,635 | 692 |
| corrections-r55/baseline/field-a.rdram | 800E0388 | 10,647 | 692 |
| corrections-r55/baseline/field-b.rdram | 800D0328 | 9,519 | 700 |
| corrections-r55/baseline/field-b.rdram | 800E0388 | 9,520 | 700 |
| corrections-r55/final/field-final-a.rdram | 800D0328 | 22,098 | 2,190 |
| corrections-r55/final/field-final-a.rdram | 800E0388 | 22,099 | 2,190 |
| corrections-r55/final/field-final-b.rdram | 800D0328 | 20,352 | 2,100 |
| corrections-r55/final/field-final-b.rdram | 800E0388 | 20,157 | 2,096 |

All paths are relative to ignored `.local/`. In final capture A at root
800D0328, the original budget reaches zero-based slot 16,383 at address 00369F60,
command `DA380003 / 09000000`, then rejects. With sufficient bounded budget,
every final task terminates at its actual DF command with list depth zero.

## Narrow correction and regression coverage

`src/runtime/graphics_task_bank.cpp` now permits 131,072 slots: at most 1 MiB
of command traffic per traversal, with headroom over the measured 22,099-slot
maximum. This is a traversal allowance, not a new guest allocation or a claim
that commands occupy contiguous memory. The depth limit remains 32; address,
microcode, extension payload, and unsupported control-flow checks remain intact.
The change adds no scene allowlist or inferred object identity.

`tests/test_full_detail_task_budget.py` first failed on all four original final
capture/root combinations and a synthetic valid task exceeding 16K slots. All
passed after the bounded increase. It also verifies immutable RAM and rejection
of cycles, oversized tasks, and unsupported control flow. Its private capture
case explicitly skips when the original game snapshots are unavailable; the
public synthetic regressions still execute. Existing exact boundary tests in
`tests/test_graphics_task_bank.py` now exercise slots 131,071 and 131,072.

The focused parser, full-detail, global-model, and extended-bank test run passed
17 tests, including the private capture case without a skip. This establishes
metadata recovery on the captured tasks. It does not establish distinct rendered
intermediate images, sustained performance, physical display refresh, or
second-match acceptance. Actual GPU images at different fractional weights of
the same original workload are required separately at both 60 and 120 targets.
