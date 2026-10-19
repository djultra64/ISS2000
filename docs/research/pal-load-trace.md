# PAL Training transition diagnostics

Original project work: `djultra64`.

This trace is for new diagnostic candidates only. Existing portable folders,
user configuration, saves and executables remain untouched. It opens no window,
audio device or separate log file. Its default stream is the application's
existing stderr, already appended to `data/runtime.log` by the fresh launcher.
No heartbeat thread, forced continuation or replacement game behavior is added.

## Proven original boundary

The preserved `training-prep49-completed.rdram` contains live scheduler callback
`802BE154` in original overlay ROM `401910`, guest base `802B8500`. Its input
result indexes table `802C3350`; A is event0 and its table entry is `802BE1B8`.
That callback checks the selected row byte `802C33C0`. Row0 is Begin Training.
It either schedules `802BE29C` directly through original `801B3D1C`, or first
uses the genuine original confirmation path, whose acceptance schedules29C.
Original29C calls `802BE3E4` directly.

Original3E4 calls `8000CC38(1,32)`, `8000C780(1)` and `8000E474`.
This sets the original transition parameters and enters `8000E490`, which
schedules resident `8000E4F8`. Later original scheduler stages `8000E52C` and
`8000E5C4` handle the fade, resource transition and readiness. Thus a BeginTraining
return log means that the transition was scheduled; it does not mean the field
was loaded. It narrows a later failure, together with original DMA trace records.

Both3E4 and optional Controller Ready `802C53A4` exactly match their original ROM
bytes in the preserved preparation RAM. Ready retains the genuine three-profile
initialization of all four controller objects. Diagnostic callers must still
require each exact original active registry function pointer before hooking;
other overlays reuse guest addresses and must not receive this trace label.

## API and verification

`trace_pal_load_transition(PalLoadTracePoint::TrainingBegin, ram, ctx, original)`
logs paired `[Load]` enter/return records with a sequence, original PC and current
SP/a0/v0. `ControllerReady` labels53A4. A thrown original exception logs throw
and propagates unchanged. The original runs once with its actual live context;
the helper does not clone or replace its context, alter guest RAM, borrow a
scratch stack, or suppress execution if the log stream is unavailable.

Four CPU tests first failed on the missing entry records, then passed after the
logger implementation. They compile the genuine original continuation closure,
verify the original entrypoint bytes against the actual preparation snapshot,
and compare the complete8MiB RAM and context against ordinary original execution.
They also cover all four Ready profiles, exceptions and a missing output stream.
These are bounded CPU fixtures, not a game run or reproduction of the reported
black transition. The freeze cause remains unresolved pending the user's next
manual diagnostic run.
