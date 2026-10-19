# Optional 2D filtering

Original project work: **djultra64**.

Version 0.7 adds **Option → PC Settings → Graphics → Filtering**, with
**2D Original** and **2D Bilinear**. Original is the default. The existing Apply
and save transaction commits the setting with the other graphics preferences;
cancel restores the saved setting. Older preference files retain Original.

The renderer changes sampling only for textured one/two-cycle rectangles.
Copy/fill cycles, framebuffer-copy tiles and 3D geometry retain their original
policy. Original guest draw descriptors and viewport/interpolation ownership
remain unchanged. Hosted POINT rectangles receive a half-texel center adjustment
for smooth sampling. Nonrepeating axes clamp linear taps to their tile; genuine
repeated and mirrored ranges remain available.

`tools/prepare_rt64_filter_2d.py` verifies the pinned upstream State source before
producing an immutable private derivative. It does not modify the dependency
checkout. CMake compiles that translation unit with its upstream C++17 semantics;
the project's own implementation remains C++20.

Automated coverage checks saved/legacy/invalid preferences, six-row navigation,
the original menu font, shader eligibility and exclusions, source identity,
centered sampling and derivative immutability. Hidden GPU sessions UI16–18
reviewed actual menus. UI18 cold-started with Bilinear restored, changed back to
Original, applied and saved, and exited through Main Select's Yes confirmation
with status 0. All owned display/audio processes were cleaned up.

Bilinear softens the original art; some tiled plates can still show faint seams.
This is documented as a remaining visual limitation. These bounded menu checks
do not establish sustained gameplay performance or physical controller coverage.
