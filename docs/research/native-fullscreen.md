# Main-thread native fullscreen

Original project work: `djultra64`.

Fullscreen is a native PC Settings preference. The renderer previously copied
this requested setting into `applied_settings` while preparing RT64 configuration.
An unrelated runtime configuration update could consume the pending difference
without changing the window. RT64 also issued the SDL window request from its
graphics thread and cached success without checking the SDL return value.

The existing `platform::update` callback runs on the main thread that created the
SDL window. It now reconciles the requested preference against actual
`SDL_WINDOW_FULLSCREEN` flags there. A successful SDL call is only a pending
request; flags must confirm the real transition. Failed or asynchronous requests
retry at most once per second. A new user selection resets that cooldown. A
concrete failure is logged once while unresolved, without a popup. Renderer
configuration and snapshots no longer change window mode.

Four CPU regressions execute the production main-thread prefix and fullscreen
function, including the renderer snapshot assignment that formerly swallowed
the difference. They first failed, then passed for real-flag acknowledgment,
failed/asynchronous requests, bounded retry, fresh selections and windowed mode.
Native handle/initialization and keyboard/preference contracts are also checked.
Actual compositor transition acceptance belongs to the subsequent parent-run
Linux build; these CPU tests do not establish a visible transition or Windows
execution.

## Actual isolated window comparison

The identical software SDL probe and extracted production synchronization function
were executed with the actual portable SDL2 compatibility / SDL3 libraries.
Private KWin 6.6.4 virtual/Xwayland correctly changed flags from windowed to
fullscreen and back, added then removed `_NET_WM_STATE_FULLSCREEN`, and restored
640 by 360 after fullscreen 1280 by 720. Both the probe and compositor exited 0.

The same probe in headless Gamescope c31743d+ resized to 1280 by 720 but never
published `_NET_WM_STATE_FULLSCREEN`; actual SDL flags lacked the fullscreen bit
throughout. Its child correctly failed acknowledgment with exit 4, even though
Gamescope itself exited 0. This reproduces the parent's DEV48 flag observation
without involving the game or RT64. A compositor exit code alone is insufficient
for acceptance.

SDL2 defines `SDL_WINDOW_FULLSCREEN` as 0x1 (bit 0) and desktop fullscreen as 0x1001.
The positive probe checks the actual bit and WM property, not a requested label
or dimensions alone. Actual loaded maps and SHA-256 identities for both runs,
normal exits, and owned-process cleanup are recorded privately in
`.local/fullscreen-investigation-01/acceptance.json`. All probe windows stayed
inside private headless sessions; audio was not initialized. This establishes
actual helper/window transitions, not another full-game or Windows run.

## Alt+Enter session shortcut

Alt+Enter toggles the currently applied window preference on the main thread.
Either Alt and regular or keypad Enter are accepted; auto-repeat never toggles
again. The complete consumed Enter press is removed from a local keyboard
snapshot through release, including when Alt is released first. SDL's own state
is untouched, and the chord cannot act as guest Start, confirm Free controls, or
switch active controller prompts to keyboard. Plain Enter retains Start.

The shortcut changes only fullscreen for the current session. It does not write
preferences or apply other pending graphics/controller edits. While PC Settings
is open, only the fullscreen field is synchronized in its draft and Cancel
baseline. Save options or the Graphics Apply shortcut can explicitly persist it
alongside the other draft options. The existing actual-window-flag reconciliation
and bounded request retries remain in force. Four CPU regressions execute the
production event loop, keyboard snapshot filtering, shortcut application and real
settings model; no game or desktop window is created. Actual manual acceptance
belongs to the user, and Windows execution remains frozen.

## Exact r56 fullscreen verification in private KWin — 2026-10-17

The production executable `4acc1f74ea76dca1536a0b57b5858933a67f792346eb1e4209ef0eb250d6deea` ran under an isolated virtual KWin OpenGL compositor, with real SDL/Xwayland window management and dummy audio. Alt+Enter changed SDL's actual fullscreen bit from 0 to 1 and `_NET_WM_STATE_FULLSCREEN` appeared; a second Alt+Enter returned the bit to 0 and removed that property. Native Graphics Settings then applied and saved Fullscreen, again acknowledged by SDL. A fresh game process loaded the saved preference and both SDL and the window manager reported fullscreen. Both game children and compositors exited normally with code 0 through Escape. The private keyboard helper's final keyup failed because the correctly closed display was already gone.

This closes the earlier actual-fullscreen uncertainty for the tested Linux virtual-window-manager path. Gamescope's lack of fullscreen acknowledgement and the earlier painter-backend failure remain harness-specific observations; neither is discarded. No physical monitor, audio or sustained performance result is inferred. Evidence: `.local/r56-fullscreen-kwin-gl/acceptance-receipt.json` and `.local/r56-fullscreen-kwin-gl-restart/`.

## r57 capture-method control — 2026-10-17

During exact r57 clean boot under virtual KWin, ImageMagick X11 window captures appeared black after the title. A controlled repeat compared XGetImage against Spectacle on the same private KWin bus/output, without intervening game input or resize. The compositor showed the animated Main menu while XGetImage returned black or an older KCEO frame; repeated compositor→X11→compositor captures retained this discrepancy. This is a demonstrated stale-window-capture artifact. It does not explain the user's earlier reported black screen. Future KWin visual acceptance uses private compositor captures.

The exact r57 executable (`f1a5fcd13794f3428ea86c6d4537d4092b3c4778cb67af64c002a4b5a4676480`) reached Main from empty data, with default 720p/60/16:9 and explicit private ROM argument. Native Graphics saved fullscreen; Alt+Enter toggled actual SDL state; cold restart restored SDL and window-manager fullscreen. All three relevant game children and compositors exited 0. Dummy audio and simultaneous test activity exclude sound/performance claims. Receipt: `.local/r57-portable-clean/acceptance-receipt.json`; controlled captures: `.local/kwin-compare57/`.
