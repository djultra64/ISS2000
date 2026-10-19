# Original PAL menu sprite interpolation

Original project work: djultra64.

The pinned RT64 game-frame matcher includes perspective and orthographic scenes,
but excludes Rectangle projections. Its fractional framebuffer renderer reads
current rectangle bounds directly. Consequently, rendering additional images
alone repeats original menu positions at their original update cadence. The
existing model matrix bridge does not make these rectangles interpolate.

The new menu path retains the original 50 VI clock and simulation. With a chosen
60 or120 render target, it interpolates validated original sprite rectangle
positions and primitive/environment colors at RT64's actual fractional frame
weight. It neither advances the game more often nor adds an independent overlay.
Original refresh retains its explicitly selected original-rate behavior.

## Original producer identity and immutable task ownership

`menu_sprite_runtime` is enabled only by the exact supported PAL ROM digest.
The existing whole-frame original `0x80000BB8` wrapper begins capture before the
original executes. Exact original `0x80008A54` initialization gives each queued
sprite allocation a fresh lifetime. The original queue contains273 records at
`0x8013C47C`, stride`0x3C`. A stable rectangle identity includes that lifetime,
draw ordinal, descriptor, segment list and segment ordinal/count. Host-owned
original-engine temporary objects require an explicit named semantic page scope;
no stack address or screen position is used as a semantic identity.

Each complete `0x80041B50` adapter is enclosed before/after all existing sprite
modifications and background scope destruction. The exact original `0x80048660` font wrapper is enclosed as well: its
`0x80048D30`/`0x80049158` glyph pipeline emits E4 rectangles directly, bypassing
the image sprite emitter. Original pooled text shares the same initialization
lifetimes. Its font face, mode and original source/scalar distinguish it from
image sprites; temporary helper text again requires the named semantic page
scope. The genuine font regression emits two actual original glyphs, preserves
their IDs after four pixels of movement and assigns fresh IDs after original
reinitialization. No font glyph, layout or message control is rewritten by the
interpolation observer. The separately proven direct
CI8 intro producer records its final original command span by explicit resource
identity. Capture follows the current `A4AA4` Gfx arena at each producer, because
original `0x80002A10` rotates that arena inside the whole-frame callback. It does
not cache the previous frame's arena at entry. Both original arena extents and
exact E4/E1/F1 command shapes are bounded before identities are published.

The original submission publishes a copied immutable command-PC-to-ID map
beside matrix metadata under the existing producer submission mutex. The
renderer consumes the same exact task fingerprint in FIFO order. Unknown
microcode, stale observations, duplicate command identities, reordered task
fingerprints and overflow cannot reuse an older snapshot.
The first graphics producer is pinned; a second producer, missing/reordered
graphics event or queue overflow permanently quarantines this FIFO for the
process, matching the existing matrix tracker. Identical later fingerprints
cannot falsely resynchronize it. Audio tasks never enter the graphics FIFO.
Scene/high-mode/pause changes and explicit original transition hooks cut the
identity epoch. Already queued immutable snapshots survive normal scene cuts.

The scheduler can submit the previous arena after `BB8` has already drawn the
next one. The capture therefore seals its complete command map before the next
frame begins, retaining the source sequence/epoch in one immutable owner per
original arena. Publication selects the submitted task's arena and consumes its
ownership once. Arena reuse, scene cuts, an incomplete observation, an unsupported
microcode submission or a source older than the immediately preceding producer
frame cannot replay that owner. Already queued copies retain their exact FIFO
fingerprints and survive ordinary cuts.

The shared sprite/font path now also runs during unpaused field rendering. The
previous unconditional scene6/4 exclusion was unrelated to the identity/material
proof and prevented every ordinary pooled HUD rectangle from being considered.
The same lifetime, task ownership, material, UV and adjacent-frame checks apply
throughout the supported original video modes; no screen-specific eligibility
list replaces that exclusion.

The original separate text pool is `801650DC`, eighty records of stride`28`.
Original `800484E0` resets exactly those eighty records through `80048528`, and
`8000924C` queues the same bounded pool. The exact initializer's post-hook renews
each text allocation lifetime. Ordinary setters, including
`801E4EE0`→`8002CC18`→`8002CCB0`→`8002C0A4`→`8002BFC0`, do not call that reset on
each update. Repeated updates to the same name retain identity; changing the
original roster source pointer or reinitializing the record gives new IDs.
Unknown nonpool text still requires explicit semantic ownership. Direct radar
marker and score-flag emitters do not acquire identities merely by being HUD;
this change does not claim coverage of those separate producers or untagged
triangles.

The scoped HLE bridge runs each original E4/extended-rectangle callback once and
uses the existing otherwise-unused `DrawCall.uid` field. It does not modify guest
RAM or introduce guest opcodes. Untracked fill/flip rectangles get identity zero.
An original empty rectangle returns before flushing its predecessor; the bridge
preserves that pending predecessor's identity. Disjoint matrix and shadow
bridges retain their callback ownership and execute in the existing order.

## Adjacent render matching and upload lifetime

The render scope accepts only the exact previous workload that RT64 maps into
the previous game frame. The workload slot generation, adjacent original capture
sequence and equal scene epoch must all agree. Duplicate or unknown IDs reject
matching. Material, combiner, filtering/cycle, texture content, UVs, sampler
parameters, origins, scissor and rectangle topology must remain identical. The
color framebuffer address is deliberately excluded because original buffers
alternate. `RDPTile.address` is a TMEM byte offset (`tile.tmem <<3`), not a guest
DRAM texture payload address. Changed texture content and framebuffer tile
copies cannot morph into an unrelated menu image.

The framebuffer derivative transforms both validated endpoint rectangles by
the same original viewport/aspect/origin rules, then interpolates the resulting
physical bounds. UVs and original filters remain unchanged. The matching helper
also computes primitive/environment colors. Each actual fractional render owns
a full private copy of current RDP parameters, changing only matched colors.
The original queued CPU vectors are never edited. Unmatched calls retain their
exact original parameters; endpoint renders restore their original colors.

The pinned queue derivative inserts one scope inside RT64's existing per-workload
render loop and existing workload mutex. Its uploader joins original
`recordSetup`, uploader wait, GPU execution and GPU fence wait. The scope owns
its parameter copy until after that original GPU fence. Its destructor also
waits for the CPU upload thread before releasing source memory. No scheduling,
VI, target-rate clamp, game-time or original render call is removed or reordered.

`tools.prepare_rt64_menu_interpolation` generates a complete private pinned
`rt64_workload_queue.cpp`. Its optional `--evidence` flag composes the existing
real GPU observer into that same source. When enabled, only the separate
present-queue evidence source is also compiled; two workload implementations
must never be linked. Both generators reject altered pinned source and altered
existing output rather than silently changing an immutable derivative folder.

## Evidence and limits

The focused CPU tests execute the genuine original PAL sprite producer on the
actual completed Controller49 RAM fixture. They prove stable IDs during real
movement and an original emitted96-alpha fade, new IDs after original
reinitialization/cuts, arena rotation, snapshot ownership and FIFO rejection.
The pure matcher produces five distinct fractional position/color states and
exact endpoints, rejecting old/nonadjacent frames, cuts, duplicate/unknown IDs,
changed compatibility and invalid weights. Adapter mechanics tests verify
original-once callbacks, pending empty rectangles, field/material/UV cuts and
private upload-copy lifetime. The production adapters and complete generated
queue/framebuffer sources compile against the actual pinned RT64 headers.
These CPU/API fixtures do not establish a GPU image or smooth presentation.

The optional existing private render evidence log now records `menu_rectangles`,
`menu_matches`, `menu_moved`, `menu_fades` and `menu_fractional` after the real
render. A fractional weight or match count alone is not image proof: actual
moving/fading menu images within the same workload must differ at intermediate
weights and preserve correct endpoints. The inherited hardware display clamp
remains in force; no physical120 claim is made on a60 Hz display.

The initial CPU/API implementation did not establish actual GPU presentation.
The subsequent bounded hidden GPU evidence is recorded below. Screen-transition,
intro-join, fade-endpoint and whole-game coverage still require their respective
evidence. This path covers bounded original 2D sprites/fonts and explicitly
tagged original-engine custom pages; it does not claim every arbitrary guest
draw has been matched. Newly encountered materials/ownership changes fail closed.

## October16 shared-ownership correction evidence

Private live probes in `.local/select-teams-54-after` found the exact global
failure: eight submissions had capture active/synchronized and459–468 rectangle
IDs, but the submitted task root belonged to the opposite original arena every
frame. Twelve actual bridge snapshots were nonnull with zero commands. This was
a producer/task ownership mismatch, before RT64 matching. The original rectangle
callback flushes each draw, so a suspected batching mismatch was disproved. The
observed inline texture skips contained no spurious rejected E4 command; that
separate parser hypothesis did not explain these samples.

The delayed-arena original-CPU regression failed on empty prior-arena metadata
before the correction. It now exercises both arena directions, source sequence,
object reuse, same-arena immediate submission, once-only publication, unsupported
microcode, stale age, arena overwrite and queued-copy survival across cuts.
Separate actual Low-field fixtures execute the original HUD player panel and
font/roster-name closures: movement preserves IDs, pause/resume/scene/material
changes or reinitialization prevent stale matching, and changing the selected
name uses distinct source ownership. Observed execution remains byte-identical
to the original CPU across the complete8MiB RAM. These CPU results establish
producer ownership; actual GPU coverage remains a separate runtime check.

## October16 raw TMEM matching correction and review

After fixing the task-arena handoff, live downstream probing found another
shared rejection: all56 tagged title rectangles in the inspected workload used
RT64's raw TMEM sampling path, which the rectangle capture rejected outright.
Raw sampling is an addressing mode, not evidence of unstable texture content.
The pinned `State::fullSyncFramebufferPairTiles` normally assigns these tiles
`TextureManager::uploadTMEM`'s content hash before the render scope runs.

For that path, `uploadTMEM` hashes all4096 TMEM bytes plus the byte offset/count.
This includes all texel banks and the upper-half palette/TLUT. The real
`TextureCache::queueGPUUploadTMEM` copies those bytes into its owned upload
vector. Later changes to producer TMEM cannot mutate the queued image. The
matcher now accepts valid raw tiles with a nonzero content key, includes raw
versus decoded mode in compatibility, and retains the existing texture-content,
TLUT, format/size, TMEM address/stride, palette, masks/shifts/clamps, tile bounds,
sampler, derivatives, finite UVs, material and source-ownership checks.
An unrelated TMEM byte changing may conservatively reject a match; it cannot
cause changed content to be blended as the same image.

Independent review found a concrete exception to treating every nonzero raw
key as a content hash. The pinned framebuffer-copy fallback can clear
`tileCopyUsed` when a selected GPU copy is too small, while retaining that
copy's ID and dimensions. Its later upload branch calls `uploadEmpty`, not
`uploadTMEM`. Therefore matching rejects every tile with `tileCopyUsed` **or
nonzero `tileCopyWidth`/`tileCopyHeight`**, including that flag-cleared fallback.
These dimensions are assigned only when selecting an original framebuffer copy;
fresh noncopy tiles are value-initialized with both zero. The source-extracted
regression executes the exact fallback and upload branches, and the adapter
regression rejects either retained dimension independently. The pinned hash
regression changes texels, palette bytes and ranges and verifies distinct keys;
unchanged content retains its key across creation-frame changes.

Private `.local/select-teams-54-final3/render.jsonl` records positive actual
menu matching at requested60 with original50: the bounded Main Select capture
contains40 real1280×745 GPU readbacks with40 distinct pixel hashes,170–175
matched rectangles and up to7 moving matches. The corresponding39 display-list
events have zero interpolated3D model groups. These are actual changing GPU images in a menu workload with active2D
matching, rather than a frame-rate counter alone. Each of
those40 readbacks belongs to a different original workload, however, so this
capture by itself does **not** prove distinct intermediate images at two weights
inside one original workload. The final copy-provenance guard requires the
subsequent rebuilt runtime check; paired-weight GPU evidence is tracked by the
root receipt when available. This bounded check makes no audio, render
performance, physical120Hz or whole-game visual-acceptance claim.

## October16 paired Main Select GPU evidence

The rebuilt `.local/select-teams-54-final4/render.jsonl` provides the narrower
paired-weight check missing from final3. Its256×256 readback region is
`x512,y244` inside the actual1280×745 render target. Initial Main Select samples
could miss the first-row selected indicator, which lies above this crop. The
native PC Settings page also redraws an opaque static base/skin after the
original frame, hiding original moving calls underneath it. Positive movement
metadata in those cases does not require pixels inside this crop to change.
Those identical earlier crops are retained as inconclusive evidence.

With Euro Cup selected in Main Select, the visible indicator lies inside that
same region. Four original workloads each produced two real GPU readbacks at
different fractional weights with distinct SHA256 pixel hashes:

| Original workload | Weights | Matched rectangles | Moving matches | Distinct region hashes |
| --- | --- | --- | --- | --- |
|30757|0.25 /0.666667|174|2|2|
|30758|0.5 /0.916667|174|7|2|
|30761|0.416667 /0.833333|174|2|2|
|30763|0.5 /0.916667|165|7|2|

All eight renders report target120 and original50. The six display-list events
within their bounded time window report scene1543 (`0607`) and zero interpolated
3D model groups. This proves distinct rendered region images at two fractional
weights while each original workload remains the same, with active2D matching;
it is not inferred from a presentation counter or from two different original
updates. It covers this selected Main Select indicator region in this rebuilt
runtime. It does not establish every screen, arbitrary untagged draw, field HUD,
physical120Hz presentation, audio/performance acceptance or GPU endpoint1
behavior. The later latest-HUD/seam build and requested60 run have their own
root-owned receipts and are not implied by this bounded120-target evidence.
