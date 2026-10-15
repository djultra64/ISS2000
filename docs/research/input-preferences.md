# Portable input preferences

Original project work: djultra64.

`input-preferences.json` lives in the portable data directory. Schema version one
contains exactly four `ports`, each with `manualFamily` (`auto`, `xbox`,
`playstation` or `switch`) and exactly fourteen integer `buttons` in this order:
A action, B action, Start, Z, L, R, C up, C down, C left, C right, D-pad up,
D-pad down, D-pad left, D-pad right. These are logical N64 actions; the values
are SDL controller button positions, independent of printed face labels.
Nintendo face positions therefore display B/A/Y/X where Xbox displays A/B/X/Y.

Missing preferences retain the original defaults. Invalid, duplicate, unknown
or incomplete settings are rejected and preserved. Saving first validates any
existing file, synchronizes an exclusively created sibling temporary and
atomically replaces the JSON file. Linux also synchronizes the parent directory;
Windows uses a write-through replacement after flushing the file. If directory
synchronization fails after publication, a new whole JSON file may already
exist; the operation reports failure and callers do not apply a partial input
snapshot. Applying a valid snapshot updates all four ports under one input lock.

Button value `-1` leaves no digital button assigned. Z then uses the left
trigger, while C directions use the corresponding right-stick direction. The
original C-up Y and C-down X defaults also accept the right stick. A nondefault
digital remap disables that action's original axis alternative. Restoring an
action's default restores its original behavior. Keyboard controls and the
primary left stick remain unchanged.

The native settings dialog offers action groups and small physical-button
menus, plus a per-action Restore default option. Explicit selections save before
applying. Cancel and Back do not create a new mapping. Manual prompt-family
selection is persisted with the mappings; Automatic still follows detection.
The F6 family shortcut saves after releasing the input lock and restores the
previous running family if saving fails.

Synthetic tests cover real JSON and file round-trips, malformed and symlink
preservation, injected synchronization failure, actual platform snapshot
application and rollback after invalid input, family-specific labels and the
original C-button axis alternatives. The adapter compiles with current native
application flags. No game window, GUI automation or physical-controller test
was run for this change. Physical prompts and actions still need joint visible
verification by the runtime operator.
