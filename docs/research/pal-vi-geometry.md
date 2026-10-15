# PAL VI geometry and enhanced resolution

Original project work: djultra64.

The observed PAL English mode has width 320, VSTART `0x0043024C`,
XSCALE `0x1EB`, YSCALE `0x386` and VSYNC 625. These values were read from
the live host VI registers during visible acceptance. The original mode data
in the private title, field and pause RDRAM snapshots agrees with the original
PAL mode initializer; the host applies its original 0.96 and 0.88125 scale factors.

RT64 estimates a 320 × 232 visible source area for those registers. Its estimate
rounds `(588−67)*902/2048` to 229 rows, adds two filter rows, then rounds to a
multiple of four. The original RDP canvas can still draw 240 rows. The enhanced
resolution multiplier uses the 232-row visible reference. Consequently the
allocated color texture contains extra rows while the VI samples only the
requested visible height.

| Setting | Color allocation for 240 RDP rows | Visible video area |
| --- | --- | --- |
|720p|1280 × 745|1280 × 720|
|900p|1600 × 931|1600 × 900|
|1080p|1920 × 1117|1920 × 1080|
|1440p|2560 × 1490|2560 × 1440|
|1800p|3200 × 1862|3200 × 1800|
|2160p|3840 × 2234|3840 × 2160|

`tests/test_pal_vi_geometry.py` exercises the actual pinned RT64 VI,
RenderTarget sizing, and VIRenderer viewport/scissor methods alongside the host
resolution helper. It verifies each visible size and a full-size viewport and
scissor, using RT64's enabled `removeBlackBorders` policy. It also verifies that
raw VI origin, vertical range and scale remain unchanged. This is CPU geometry
verification; it does not render or establish GPU resolution or frame rate.

The VI shader samples `videoResolution/textureResolution`, so a 1920 × 1117
allocation does not itself indicate an incorrect 1080p image. Replacing 232 with 240
would change visible crop and source aspect ratio without evidence supporting
that change. No production VI sizing override was added.

The paused gray bottom rectangle appears in both private native-resolution
capture 87 and 1080p capture 88 at approximately the same window position and
height. That observation does not identify its original draw call, but it does
not support a resolution-only diagnosis. Its content/ownership remains a
separate visible-acceptance investigation.
