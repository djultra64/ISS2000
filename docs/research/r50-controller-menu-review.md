# r50 Controller and Settings correction review

Original project work: `djultra64`.

This independent pass used read-only original PAL code and bounded CPU fixtures.
No game, audio device or Windows process was launched. User portable settings,
saves and executable files were preserved.

The separate complete-controller projection defect and Controller entry-fade
ownership correction are described in [pal-football-processing.md](pal-football-processing.md).
Neither proves the cause of the reported black transition before Training.
The user's portable folder contains no runtime log, so the exact stalled stage
is unavailable. Existing integration19 passed 428 tests without exercising that
reported transition.

Current native Type callbacks execute the original callback once, then restore
only the genuine profile byte. The host Type5/Free enum never replaces guest
`802D21E4+port`. Original Ready `802C53A4` reads that genuine byte to select
`800774F0+12*profile`, initializes all four controller objects, and persists it
to `8012DE8D+port`. The bounded original initializer tests cover all three valid
guest profiles, neutral input and the Begin-confirm South input. No evidence
supports a host Type5 ordinal entering the guest three-profile table, and no
additional speculative transition patch was made.

Settings input remains owned by its opening port and requires release between
commands. The save callback captures fresh preferences before merging device
families and vibration, preserving football schemes and ordinary menu bindings.
Its tested transaction persists before applying live preferences. The existing
native integration regression catches held-button repetition as a negative
control. Footer input requests and device-family glyphs use one input snapshot.

The Settings sound model queues semantic events and guards acknowledgments by
sequence. BB8 drains only with original Options ownership and the exact active
resident sound function, attempting at most four events per frame. Full original
queues defer; a rejected request discards one event and stops. The production
drain is tested with the real model and actual original sound queue functions,
including full, duplicate, rejected-code and foreign-owner cases. No important
queue, context-preservation or persistence defect was found in this review.
Queue admission is not audible-playback acceptance.

Test extraction was repaired to match function definitions rather than the new
`draw_physical_prompt` forward declaration. Native title checks now link the
actual menu observer and configure it from the exact PAL ROM. Production observer
behavior was not stubbed or removed. Focused results: seven native Settings cases,
one native title case, and six original menu-audio cases passed independently.
