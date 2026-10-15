# Rendering evidence and widescreen strategy

Static research, 2026-10-15. This establishes supported microcode identities and
projection hooks; it does not establish a rendered title screen, playable game,
or verified widescreen output. No original instruction bytes or assets are
included in this document.

## Original microcode and RT64

The original startup task uses text at `0x80069250` and data at `0x8009C8E0`.
The original task builder at `0x80001924` receives these pointers, and the
private boot capture also records them. Their word-swapped XXH3 hashes exactly
match pinned RT64's `F3DEX2.fifo 2.06` registry entries. A second pair, text
`0x8006A5E0` and data `0x8009CD00`, matches `F3DLX2.fifo 2.06.Rej` (the text
hash is shared with 2.05; the data hash resolves 2.06). Both select RT64's
`GBIUCode::F3DEX2`; the latter carries LowP and ReJ flags. RT64 annotates the
secondary registry entry as needing confirmation, so recognition is stronger
than a claim of fully verified rendering compatibility.

Original display-list construction switches to the secondary pair around
`0x80002278`–`0x8000228C`, then restores the primary pair around
`0x80002304`–`0x80002324`. This uses the F3DEX2 load-ucode command sequence.
A new microcode implementation is not indicated by these exact identities.

Private reproducible evidence is in `.local/render-evidence/`: run
`python3 .local/render-evidence/render_evidence.py`. It verifies the approved
ROM SHA-256, computes all four hashes in the host word-swapped memory layout,
checks the pinned RT64 registry, and asserts the projection instructions used
below. `render-evidence.json` records a fresh successful execution. The script
reads only the project's original ROM and public upstream implementation.

Relevant upstream source is under `.local/deps/rt64/`:

- `src/gbi/rt64_gbi.cpp`: registered instances, segment hashes and recognition.
- `src/hle/rt64_workload_queue.cpp`: source/target aspect and scale calculation.
- `src/render/rt64_projection_processor.cpp`: projection correction.
- `src/render/rt64_framebuffer_renderer.cpp`: viewport/scissor and output sizing.
- `include/rt64_extended_gbi.h`: explicit per-group aspect modes.

## Exact projection landmarks

The resident fixed-matrix perspective builder is `0x8005B7E0`; its float-matrix
counterpart is `0x8005B630`. Their horizontal matrix coefficient is
`cot(fovy / 2) / aspect`, while the vertical coefficient is `cot(fovy / 2)`.
The two direct calls to the fixed builder found by scanning aligned words in
the whole ROM are at `0x80024CA0` and `0x80024D24`, within wrappers
`0x80024C3C` and `0x80024CD4`. This is an aligned direct-call inventory, not
proof that no indirect projection path exists.

Both wrappers load the aspect from `0x800A07E8`, pass its float bits in `a3`,
and load field of view from `0x800A07D4`. Their matrix destinations are
`0x800C43A0 + index * 64` and `0x8013DE78`; the normalization outputs are
`0x800A0796` and `0x800A06F4`. Setters are `0x80024D48` (aspect, `f12`) and
`0x80024D38` (field of view, `f12`). Initialization at `0x8002A90C` explicitly
sets aspect 4:3, field of view 15 degrees, near 10 and far 2600. Global aspect
has a direct initialization store at `0x8002A9D4` and setter store at
`0x80024D4C` in the resident instruction inventory.

## Recommended first 16:9 implementation

Use RT64 as the single owner of render projection correction initially:

1. Set `userConfig.aspectRatio = RT64::UserConfiguration::AspectRatio::Manual`
   and `userConfig.aspectTarget = 16.0f / 9.0f`. Keep
   `userConfig.extAspectRatio = AspectRatio::Original` until explicit HUD origin
   commands are implemented. Manual fixes 16:9 independently of window shape;
   Expand instead follows the window and is not an exact 16:9 target.
2. Retain the original guest 4:3 projection and field of view. For a 4:3 VI
   source RT64 computes target/source = 4/3 and multiplies the projection's
   horizontal column by its reciprocal, 3/4. Thus the final horizontal scale
   becomes `cot(fovy/2)/(16/9)` with unchanged vertical field of view. This is
   a wider perspective, not a horizontal stretch.
3. Verify RT64's AUTO rule for every relevant viewport. It corrects projections
   whose viewport/scissor intersection spans the framebuffer width, is wider
   than tall, and uses no custom origin. A narrower viewport or split-screen
   may deliberately fail this rule and requires an explicit policy. AUTO is
   not restricted to perspective matrices; inspect orthographic/HUD draws too.
4. Validate a real match and menus: circles and player proportions, pitch-edge
   visibility, CPU object culling, replay cameras, transitions, all split-screen
   layouts, HUD anchoring, and pointer/hit-test coordinates. A wide framebuffer
   or a single screenshot is insufficient evidence of proper widescreen.

The adapter currently passes the runtime aspect enum to RT64 and keeps extended
aspect Original; game startup currently selects Original. The configuration
above is a proposed next change, not an implemented enhancement.

Do not also set guest aspect to 16:9 while leaving RT64's AUTO/ADJUST correction
active: that applies the horizontal 3/4 factor twice. If later evidence requires
native guest projection changes (for example CPU-side visibility calculations),
set the guest matrix aspect to 16:9 and tag only those already-corrected
projection groups with `G_EX_ASPECT_STRETCH`. Despite the name, in
`ProjectionProcessor` this mode disables the additional matrix correction;
manual 16:9 still controls output width. Other original projections can retain
AUTO or explicit ADJUST. Pair the group with the correct lifetime/pop and leave
HUD handling separate. Setting all output aspect modes to Original would also
remove wide output, so it is not the corresponding switch for this strategy.

No CPU visibility routine or game-specific HUD correction is established yet.
Do not change the global aspect blindly; first compare the original and wide
camera at the same simulation state and trace any missing objects to the
original visibility conditions.


## Resolution profiles and static RT64 audit

The portable graphics settings retain Original and add six explicit height
profiles. The settings picker separates Standard and High pages with at most six
buttons; page navigation changes no setting, and only the outer Save publishes
the graphics draft. Dimensions on the buttons reflect the graphics draft's chosen aspect ratio.
Selecting a height does not silently change the chosen aspect ratio.

| Profile | 16:9 target | 4:3 target | Scale for 240-line VI | Scale for 480-line VI |
| --- | --- | --- | --- | --- |
| 720p | 1280 x 720 | 960 x 720 | 3 | 1.5 |
| 900p | 1600 x 900 | 1200 x 900 | 3.75 | 1.875 |
| 1080p | 1920 x 1080 | 1440 x 1080 | 4.5 | 2.25 |
| 1440p | 2560 x 1440 | 1920 x 1440 | 6 | 3 |
| 1800p | 3200 x 1800 | 2400 x 1800 | 7.5 | 3.75 |
| 2160p | 3840 x 2160 | 2880 x 2160 | 9 | 4.5 |

These are the expected primary full-frame targets for a 4:3 native source,
not measurements of the application. Original returns scale 1 and preserves the
native height. The version-1 JSON accepts string values `Original`, `720`, `900`,
`1080`, `1440`, `1800` and `2160`; existing profiles remain compatible. The
settings helpers reject invalid enum values. They divide the requested height
by the actual nonzero native VI height, with a 240-line fallback before the
first valid VI, so an interlaced 480-line source does not double the requested
height.

The static integration review follows `src/renderer.cpp` and the pinned RT64
implementation in `.local/deps/rt64/`:

- `src/hle/rt64_workload_queue.cpp`, `threadConfigurationUpdate`, uses the
  configured multiplier directly for Manual resolution. It computes scale X
  as multiplier times target/source aspect and scale Y as multiplier. A 320 x
  240 source at 16:9 and multiplier 9 therefore produces 3840 x 2160; a 640 x
  480 source uses multiplier 4.5 for the same result.
- `src/hle/rt64_vi.cpp`, `VI::fbSize`, derives the source framebuffer dimensions
  from the VI configuration, including interlace and alignment. The adapter
  uses this derived height rather than assuming every VI is 240 lines.
- The adapter selects Manual for explicit profiles, Original for Original,
  and downsample multiplier 1. Manual target size is independent of the SDL
  window size. The VI renderer fits presentation into the available window;
  resizing a 1280 x 720 window is not evidence of a 4K internal target.
- `src/hle/rt64_workload_queue.cpp`, `getTargetsFromPair`, can reduce the scale
  for oversized offscreen framebuffers. Render-target sizing also rounds
  scaled dimensions and makes widths even. Therefore the table does not mean
  that every auxiliary target or texture is allocated at its listed size.
- The largest requested multiplier here is 9 for a 240-line VI, within the
  pinned user-configuration multiplier limit of 32. These profiles require no
  new shader ABI macros. This does not establish available VRAM or performance.

`tests/test_graphics_settings.py` compiles the actual settings implementation
and exercises every aspect/resolution/refresh combination, native heights 0,
240 and 480, strict parsing, invalid enum rejection, atomic persistence and
concurrent publication. New 900/1800 tests failed with Unsupported resolution
before implementation, then all 15 focused tests passed, including direct assertions of the labels used
by the picker for both aspect ratios. This is settings and
scale verification only. Actual framebuffer dimensions, 720p through 4K
presentation, resize transitions, shader output, HUD appearance and performance
remain deferred until the user resumes visible game testing. Resolution work
does not establish correct widescreen projection or 120 fps interpolation.
