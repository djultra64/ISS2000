# Football physical input and editor boundary

Original project work: `djultra64`.

The physical football snapshot is independent of the fourteen ordinary menu
bindings. SDL positional face buttons and the two shoulder buttons provide
South/East/West/North/L1/R1; actual left/right trigger axes strictly above 10000
provide L2/R2. Manual controller family and raw menu remapping do not change
these positions. Existing SDL initialization disables button-label remapping.

The main SDL loop polls this state under `input_mutex`. The public
`football_physical_input(port)` getter copies the focused current state without
consuming it. Start and D-pad Up/Down navigate the original Free screen.
Keyboard Enter/Up/Down/Escape supply navigation only; East remains assignable
and cannot cancel Free. Escape while the shared editor snapshot is editing
Free bypasses the ordinary game-quit handler. The editor snapshot is obtained
before acquiring the input mutex.

Only the real runtime `get_input` callback latches `FootballSiInput`. Each valid
port call increments its sequence and computes `pressed = held & ~previous`.
Reading this sidecar does not consume edges. Two SI calls with a held button
therefore expose a press only in the first sample, matching the original PAL
raw packet producer. Polling between SI calls never accumulates transient
presses. Disconnection, focus loss, keyboard use and old PC Settings/raw-menu
suppression produce a zero non-gamepad SI sample and reset previous held state.
The existing ordinary menu packet, sticks and return value are preserved.

Original PAL `8000453C` writes ten-byte packets at `8013B454 + port*0xA`:
connection at +0, held at +2, pressed at +4, sign-extended sticks at +6/+8.
Its pressed calculation is the same new-held edge. Normalizer `801D4880`
reads +2/+4 through controller object +0x24. The separate guarded scratch
adapter owns football projection; this platform code never rewrites guest RAM
or changes the ordinary menu mapping. Original callers reload the source
pointer before later stick processing. Odd ports require guest-byte XOR3 copy
because their ten-byte packets are only two-byte aligned.

`FootballControllerEditor` is a thread-safe four-port draft model. It preserves
stored Free bindings while cycling the six schemes, swaps occupied physical
positions atomically, and requires neutral controls on entry and between
assignments. Cancel restores the Free entry draft; Start confirms it. Cancel
wins over Start and Start wins over a simultaneous assignable button. The
original screen integration owns rendering and actual selected-port saves.

Focused CPU checks execute the real sampler and `get_input` body with four SDL
virtual controllers and no video/audio initialization. They verify all eight
positions, actual SDL trigger conversion at 10000/10001, per-port sequence and
edge isolation, unchanged raw packets, reset paths and keyboard navigation.
The real extracted Escape handler is checked with the shared editor singleton.
A separate caller links the actual platform translation unit and invokes both
public getters, checking their exported linkage rather than only extracted code.
These tests are not physical-controller acceptance or a game execution claim.

The PC Settings save callback merges drafted family and vibration values into
a fresh preference snapshot before the existing two-file transaction. Free
bindings, schemes and other raw remaps survive that merge; publication failure
preserves exact old file bytes and live state.

The opt-in development controller fixture accepts `a b x y l1 r1 l2 r2`
for these eight positions. Existing `start`, analog `up/down/left/right` and
explicit `dpad_*` tokens are unchanged. Its SDL virtual descriptor exposes all
six controller axes. Trigger rest is raw -32768 (SDL controller value 0),
and a held trigger is raw +32767. An empty, missing or invalid snapshot releases
every control; a partially parsed invalid file never leaves earlier tokens held.
Fourteen focused fixture tests pass, including actual SDL axis capability and
neutral-state checks before the first snapshot pump. The fixture remains inert
without the development build flag and explicit absolute snapshot environment.
No physical-controller behavior is claimed by this app-owned fixture.
