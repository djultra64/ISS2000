# Original PAL menu sound requests

Original project work: `djultra64`.

PC Settings reuses original menu sound requests rather than synthesizing host
sounds. The approved semantic mapping is:

| Intent | Original ID | Evidence |
| --- | --- | --- |
| Navigate | `0101` | Options Up/Down `8029F33C`/`8029F390` call `801B7E00` |
| Accept | `0100` | Options Accept `8029F2D8` calls `801B7D90` |
| Back | `0100` | Same original GoBack-row confirmation sound, explicitly approved |
| Error | `0152` | Invalid Password path `802A6234` calls `801B7DC8` |

Each small original sound wrapper calls resident `8004C59C`, which calls the
original command queue `8004C608`. Original Options B callback `8029F314` is
silent: it selects GoBack without a sound call. Back therefore deliberately
uses the original GoBack confirmation sound, not an invented distinct B sound.
ID `0102` is a value-adjustment sound and is not treated as Back.

`play_pal_menu_sound` accepts one intent, the original caller context and the
identity-checked original `8004C59C` function. Its caller must execute it on the
original guest thread, such as after `80000BB8`, and must verify the active
registry function identity before passing the callback. The module checks exact
PAL resident code hashes for both bodies, the main stack bounds/alignment, FPR
alias bounds and original queue state. Rejection calls nothing and leaves RAM
unchanged. It uses a private context copy with its FPR alias rebased and restores
the borrowed64-byte stack region even if the original callback throws. Genuine
queue writes survive; original caller registers and FPRs are unchanged.

The genuine queue retains eight entries at `80166198`, count byte `8009DEA4`
and original busy byte `8009E07C`. The adapter executes the original request
exactly once and reports `Queued`, `AlreadyPending`, or `Full`, preserving the
original full-before-dedup order. Invalid/busy states return `Rejected`. It
creates no second audio queue, no SDL sound, no success stub and no changes to
AI DMA timing, PCM or gain. A caller can defer its intent on Full; it must not
claim playback from queue admission alone.

Six CPU tests pass with no skips against the actual private PAL input and bound
original translations. They execute original Options navigation, original
confirmation and the invalid Password branch to verify the IDs, then verify
queue contents, dedup/full behavior, exact caller/stack preservation, exceptions
and twelve foreign-code/context/queue rejection variants. These tests do not
open an audio device or execute the game and do not constitute audible playback
acceptance. User-owned portable data and executables remain untouched.

The sixth test extracts the exact production BB8 sound-drain block and combines
it with the real Settings state model and original queue bodies. It verifies
Options ownership and active-function identity, at most four attempts per frame,
full-queue deferral, duplicate acknowledgments, and acknowledgment of exactly one
rejected event before stopping. Native title extraction also links and configures
the real menu-sprite observer with the pinned PAL ROM instead of replacing its
frame boundary with a no-op. These checks establish queue integration, not audible
output or whole-game acceptance.
