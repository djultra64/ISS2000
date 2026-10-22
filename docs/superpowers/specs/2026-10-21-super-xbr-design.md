# Optional Super-xBR for ISS2000 2D art

Original project work: djultra64.

Status: direction approved; written specification awaiting user review.

## Intended result

The current Bilinear option blurs typography. Replace that option with Original, Super-xBR 2× and Super-xBR 4× in the existing native Graphics menu. Original remains the default, as explicitly requested. Fonts, glyph families, action bindings, guest artwork, menu geometry and original simulation timing remain authoritative. The user separately requested a 1080p/4K alignment audit; sampling/geometry defects must be reproduced and corrected independently of this enhancement.

## References and attribution

Takedawn documents Super-xBR and alpha-aware preparation rather than bilinear-only enlargement:
https://github.com/xenophobentx/takedawn/blob/5a00fc10f9548a189e9043c5a55975863ad49175/docs/ui-scale.md

The generic implementation inspected is `src/kernel/nv2a_texscale.[ch]` in:
https://github.com/xenophobentx/xboxrecomp/tree/5ae8ad90d984425e834dee759592c15592679880

Use only generic scaler code whose license permits reuse. Retain Hyllian's complete MIT notice and all applicable toolkit copyright/license notices for any adapted portions. Do not transfer Xbox game assets, game binaries, title-specific patches or Xbox texture predicates. Document the exact adapted source revision and local differences. Donor performance measurements are not ISS2000 measurements.

## Architecture

1. Keep the deterministic scaler independent of RT64 and the settings UI: straight RGBA input, factor 2 or 4, checked dimensions, straight RGBA output. Scale in premultiplied alpha with alpha contributing to edge detection. Clamp premultiplied color to alpha, safely unpremultiply, and extend adjacent visible colors into fully transparent output texels. Use the normal Super-xBR passes with anti-ringing; 4× is two 2× passes.
2. An ISS2000 adapter admits original 2D rectangle uses and snapshots their complete decode inputs before scheduling work. RT64's `TextureUpload` already carries TMEM bytes, dimensions, TLUT and load-tile interpretation; asynchronous jobs must own their copies. A CPU decoder must agree with the pinned texture decoder for the admitted RGBA, CI and intensity/alpha formats. Unsupported formats use Original. No render-thread GPU readback is introduced.
3. Bind a prepared texture per eligible draw through a separate host cache. RT64's original texture hash can also be used by 3D draws, so globally replacing that hash is forbidden. Preserve original guest dimensions, rectangle geometry, UV derivatives, palette ownership, scissor and blend state; supply an explicit source-region-to-prepared-texture mapping to the host sampler.
4. Use one bounded background worker. Original textures remain usable while preparation is pending. Completed jobs enter the existing render/upload ownership boundary; CPU workers never mutate live GPU descriptors. Generation tokens prevent late results from a previous setting, palette or source from being installed. Retire GPU resources only after their workload users finish.

## Eligibility and atlas boundaries

Require an actual 2D rectangle with original memory-backed imagery, no depth test/write, and no framebuffer/effect-target copy. Exclude 3D, feedback textures, unknown decode modes and unverified repeating/mirrored regions. COPY rectangles can qualify only after their original horizontal derivative normalization is accounted for; do not rewrite guest cycle or blend semantics.

An atlas crop is a separate cache input. Include its source region, texture interpretation, palette, orientation and edge policy in its identity. Clamp sampling to the admitted region so enlarged fonts do not read neighboring glyphs. A subregion with ambiguous ownership falls back to Original. Tiled artwork requires verified adjacent-region ownership and equivalent border samples before joining regions; do not invent neighboring pixels or assume Xbox atlas behavior applies to N64 TMEM. Unsupported or ambiguous pieces may therefore remain Original while surrounding eligible art uses Super-xBR.

## Cache, limits and failures

Keep generated texels under the selected portable data directory, in a private `cache/2d-super-xbr-v1` folder. Never include these derived assets in source control or distributable packages. Hash complete decoded RGBA plus source-region/decode metadata, scale factor and algorithm version. Validate dimensions, payload length and checksum before use. Write via a unique temporary regular file and atomic rename; reject symlinks and malformed cache records.

Admit at most 512×512 source texels per job. Bound queued jobs to 32, combined CPU/in-flight cache allocations to 256 MiB, GPU prepared textures to 256 MiB, and persistent cache to 512 MiB with eviction. Check arithmetic before allocations. Generate alpha-aware mip levels down to source size for stable minification. GPU mip sampling must respect region borders. A cache miss, corrupt entry, full queue, allocation failure or unsupported upload leaves Original available and does not interrupt gameplay or replace user settings.

## Settings and UI

Extend the existing `Filter2D` setting and Graphics filtering row; no additional host overlay. Use Original / Super-xBR 2x / Super-xBR 4x when the original font cannot render the multiplication sign. Keep the existing Apply/Save, navigation, help and device glyph behavior. Persist optional `filter2D` values `SuperXBR2x` and `SuperXBR4x` in schemaVersion 1; omit the key for Original as today. Recognize legacy `Bilinear` as Original in the new loader and migrate its serialized form only on normal Apply/Save. Preserve resolution, refresh, aspect, fullscreen and all independent input/save files. Explain in English release documentation that older builds may reject the newly extended enum values.

Switching modes invalidates eligibility/generation immediately; it does not wait for the worker. Returning to Original selects the original rendering path and releases prepared resources through normal workload ownership.

## Acceptance

- Deterministic scaler fixtures: opaque diagonals, tiny glyphs, transparent outlines, empty/invalid input, maximum dimensions, anti-ringing and both factors. No dark halo from hidden transparent colors.
- Decoder parity for admitted authentic TMEM formats and palette changes; unsupported formats must fall back without stale texture reuse.
- Cache tests: factor/version/palette/region changes, cancellation, corruption, truncated payloads, allocation limits, eviction, atomic persistence and shutdown with queued jobs.
- Per-draw ownership tests: the same source used by 2D and 3D cannot enable smoothing/upscaling in the 3D draw. Original must preserve its baseline.
- Settings: default Original, legacy Bilinear migration, round trips, Apply/Save, resolution changes and active-device glyphs.
- Hidden real GPU comparisons at 1920×1080 and 3840×2160 in Original, 2× and 4×. Include title, Main Select, native Options/PC Settings, Select Teams, Edit Controller, Stadium Select, pause, scoreboard and reachable match announcements/results. Record coverage gaps explicitly.
- Measure cold-cache and warm-cache behavior separately; no promise of zero cost or instantaneous preparation. Verify that a first-use miss does not synchronously rescale on the render thread.
- Linux first. Windows compilation/publication and machine power control remain a later authorized final stage, using the machine skill. This specification does not create a new release or alter v0.7.0.

## Excluded work

No new ROM revision support in this filter change, no distributed derived textures, no replacement game assets, no host UI redesign and no claim of complete 1.0 acceptance. Additional European ROM variants remain a documented backlog pending exact identification and independent validation.
