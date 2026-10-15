# Host rumble and the virtual accessory choice

Original project work: djultra64.

The current implementation routes original per-port motor requests to a physical
SDL controller when that port has **Rumble** selected as its virtual accessory
and SDL reports actual rumble capability. It preserves the original exclusive
accessory choice. Simultaneous virtual Controller Pak storage and host haptics
are not implemented or claimed.

`platform::device()` returns a connected controller independently of accessory
selection, but advertises upstream `Pak::RumblePak` only for a physically
rumble-capable controller with Rumble selected. Pinned upstream
`ultramodern/src/input.cpp::osMotorInit` then performs its real initialization:
queue/channel/bank/status fields, connected-device check, pak presence/type
check, and finally the motor-initialized status bit. The wrapper does not turn
an error into success. Its existing `motor_init_result` only converts no-pak
error 1 to different-device error 11 when Controller Pak is selected, since the
upstream capability enum cannot represent a Controller Pak.

Original motor access checks the initialized status bit, then passes that
original OSPfs channel to the platform rumble callback. Platform polling applies
requests only to the selected port's SDL controller, and suppresses/stops motors
on focus loss, controller removal, shutdown, or the controls-remapping screen.
The None and Controller accessory choices stop motor polling. Rumble requests
are never represented by a fake successful SDK initializer.

The virtual Controller Pak service is independent persistent block storage.
`init_controller_pak` requires a connected port and Controller selected, then
runs original PAL `80060DD0`; block read/write/status/plug services retain their
own selected-accessory rules and real filesystem errors. Controller Pak images
remain real per-port files. None returns no-pak rather than creating an
available accessory; Rumble is a different device for filesystem operations.
The controller query wrapper retains virtual accessory presence, so None also
remains absent in the original query status consumed by motor-probe loops.

This is a deliberate scope boundary, not a claim that modern controllers cannot
provide both storage and haptics. A broad change to advertise RumblePak while
Controller is selected is insufficiently verified for this original engine:

- PAL motor-probe loops `80007214` and `800072B4` use original query status and
  call `8005F8A4` with OSPfs `801A043C + port*68`.
- Original PFS wrapper `80004780` calls `80060DD0` with the same per-port OSPfs.
  Both initializers reset its status word; motor and filesystem status are not
  independent guest objects.
- Original accessory/file inspection `80018F4C` first queries filesystem state
  through `80004A04`. Its different-device classification 7 then probes
  `8005F8A4` and GB Pak initialization. Changed motor success can therefore
  participate in original accessory classification as well as haptics.

Any future combined-storage/haptics enhancement must prove original save/menu
classification and motor/PFS reinitialization lifecycles, while preserving None,
per-port errors and actual physical capability checks. It must not change SDK
errors or advertise hardware capability without SDL evidence.

This record is based on static original PAL code and pinned host source. No game
was launched for this investigation, and physical motor output was not verified.
Physical-controller acceptance remains necessary for every available family and
port before making a tested-hardware claim.
