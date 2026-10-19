# PAL formation persistence

Original project work: **djultra64**. Linux correction candidate r59.

## Reproduction and cause

The exact r58 production hash `ee54e4a9c32dfd844e74195cd9e8f42d775d5f85714a536136e9aa096a7f18bc`
loads the existing slot1 formation and lets the user save into empty slot2. With
original accessory-choice bytes `8012E62B=[0,0]`, the original Formation Save
callback `802A3464` follows `802A6CD4`, updating its RAM table but scheduling the
RAM-only completion rather than the disk worker. All four saved-data files remain
byte-identical before any further Load/global Save. After normal exit0 and a cold
restart, slot2 is empty. This is independent of the separate dirty-mask concern.

Private evidence: `.local/editor-r58-diagnostic/runs/editor-01` and
`editor-02-cold`, including read-only parent-debugger traces, file hashes and cold
capture05. Both processes exited0. These runs do not qualify audio/performance.

## Correction

`tools/prepare_pal_formation_persistence.py` verifies the complete PAL ROM,
original callback body and generated source before producing an immutable private
derivative. The original callback is replaced only when the live registry has its
exact overlay-specific function identity. For its two valid logical ports,
explicit Formation Save uses the original persistent-storage branch regardless
of the historical physical-accessory choice. Other logical ports retain the
original branch. The choice bytes and save payload are not modified by the adapter.

The original SDK probe, asynchronous prepare/write, selected port/slot and error
callbacks remain authoritative. The adapter never supplies a successful SDK
result. Original write worker `802A3720` calls `80019A64`; success sets state6,
errors set state7. A C++ declaration is hoisted without moving its assignment.

This fixes this particular Save callback. Other editing callbacks, UI prompt
coverage and complete save/load acceptance need their own evidence.

## Verification

The original CPU callback fails the new regression with port0/choice0: RAMsave1,
diskprepare0. The derived callback matches the original storage-enabled route for
both supported ports, all three historical choices and nine probe results (54
combinations). Eight cases execute the unchanged original worker with successful
and failed write results and verify success/error states. ROM/source mismatch and
immutable output guards pass. Native lookup tests reject foreign overlay entries;
compiled helper symbols export their exact unmangled entry.

Exact r59 SHA-256:
`39d015c77a9becb926fdb3ab9e3093d1d1a93f1f4d742dd43ae4d882cfe3fce7`.
The private live save run records the derived callback, original prepare, original
worker and real SDK writer returning0 with choice bytes still [0,0]. File1 and its
backup change; files2–4 do not. A normal cold run without debugger shows slot2
4-3-3 and loads it successfully. That normal run also saves slot3 and loads it in
the same process; global Save then reports Saved with no further file difference.
The final normal cold check retains both slots and loads slot3 (capture06 in
`cold-03-global`). All three r59 processes exit0. Receipt:
`.local/editor-r59-diagnostic/persistence-receipt.json`.

The new portable contains no ROM or saves. The copied runtime test data is private
and never modifies the user's earlier packages or saved data.
