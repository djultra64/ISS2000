# Direct PAL HUD rectangle ownership

Original project work: djultra64. Investigated 2026-10-16.

The common pooled sprite/font path does not observe every direct HUD producer.
Score flags now join the same queued rectangle interpolation path through their
existing original-emitter wrapper. Radar markers still require explicit ownership
of their private display lists; their current cadence must not be described as
fully interpolated.

## Score flags

The original main dispatcher calls `8023A890`, which installs its original
scissor/setup, then calls `8023A510(8009E0C8, side)` for sides 0 and 1. The inner
producer emits one E4/E1/F1 textured rectangle into the main graphics cursor,
following texture/palette segment setup and the original `80264958` sublist.
Low coordinates use quarter pixels; High doubles them and adjusts derivatives.

`draw_widescreen_score_flags` saves the original side and main cursor, calls the
original emitter exactly once inside its existing balanced HUD scope, then
captures the complete cursor range after that scope finishes. Only the exact
main cursor argument and sides 0/1 receive named semantic identities. The shared
metadata API checks the real task arena and records only emitted rectangle PCs.
Empty or clipped flags create no invented draw. Distinct side identities survive
position changes and a hidden opposite flag. The same FIFO, epoch and immutable
queued ownership as other rectangles applies.

The shared renderer requires matching material, UVs, topology, scissor/origins
and immutable texture/TLUT content before interpolation. A changed flag resource
therefore does not morph into the previous resource merely because its logical
side remains the same. Simulation and original command generation are unchanged.

The genuine original CPU/compositor regression first failed because neither flag
had interpolation metadata. It now executes the actual integration wrapper in
Low and High, checks original calls exactly once, both distinct side identities,
movement and a hidden left flag, main-arena E4 bounds, and full 8 MiB equality of
the 4:3 wrapped/original outputs. Existing production rectangle-matcher and RT64
adapter regressions separately check fractional bounds/fades and material,
UV, TMEM-content, topology and epoch rejection. These checks do not establish
actual GPU acceptance or visual smoothness.

## Radar private-list gap

Original initializer `802A5AAC` allocates a render root through `8002AC08`,
stores it at `802B2950`, assigns callback `802A5290` at root `+7C`, and sets its
list pointer at `+24`. That callback writes into a private double buffer:
`802B4408 + s16(8013B418) * 0x960`, using cursor `802B4400`.
It chooses flat emitter `802A4DC0` or projected emitter `802A4F78` from byte
`8012E6A3`. Both emit one 24-byte E4/E1/F1 rectangle per marker; these are not
fill rectangles or RSP triangles. Their derivative is 1024 in Low and 512 in High.

Normal player helper `802A5230` takes a player record in `a0`, checks its active
and hidden flags, follows `+9C` to the actor, and reads actor `+58/+50` positions.
Highlight helper `802A5180` takes that player in `a2`, with separate color/role
arguments. The normal player pool starts at `801313D0`, stride `0x138`, with 28
candidates. Actor word zero identifies its original render root, as confirmed by
resident updater `800300D0`. A stable marker identity can combine the observed
render-root allocation generation with its marker role.

Two helper hooks alone are insufficient. Callback `802A5290` also emits directly
at call sites `802A5488`, `802A57BC`, `802A5960` and `802A5A5C`, covering controlled
players, a target and the ball. The ball root comes from `802B57D0`. The low
emitters receive world positions and UV selections, without a uniform actor
argument. Matching by draw ordinal or position would confuse missing markers,
controller changes or coincident players.

The smallest shared extension needs explicit bounded nested-list ranges owned
by the parent submitted task, retained through its double-buffer lifetime, plus
per-emission actor/ball identity and visual role from the real producer sites.
The current main-arena capture deliberately rejects these private addresses.
Only after that ownership is supplied should their E4 PCs join the existing
rectangle/material bridge. Original CPU tests should include hidden/reordered
players, selection-role changes, ball identity, both private banks, delayed
submission, reuse/cuts, exact 8 MiB parity and unchanged projection/UV output.
No radar interpolation implementation is included in this correction.
