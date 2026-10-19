# Native PC Settings persistence

Original project work: `djultra64`.

The native PC Settings Save action changes graphics and per-player vibration
preferences together. Previously, it published `graphics.json` before attempting
`input-preferences.json`. An invalid input file or second-file write failure
reported Save failed while retaining changed graphics on disk. Cancelling the
menu did not undo those persisted changes.

`save_game_preferences` validates both existing files, stages both new outputs
through the existing strict serializers, and publishes them while keeping the
exact old files available for rollback. A publication failure restores both
original files, including their exact bytes and the case where neither existed.
The callback updates live graphics and input only after both files succeed.
Fresh input preferences are captured at Save so independently saved remapping
and other players' preferences survive a parent graphics/vibration edit.

Four CPU regressions execute the extracted production Save callback and actual
stores. Injecting a real second-file rename failure reproduced the old partial
save; malformed existing input and absent original files reproduced two further
failures. All three pass with rollback, and the success test verifies preserved
other-port remapping alongside the requested vibration settings.

This is rollback for reported runtime failures, not an atomic two-file commit
across power loss. If rollback itself fails, the recovery directory is retained
rather than deleting its previous files. Neither this helper nor its tests touch
game save images, imported ROMs, release packages, or the user's portable data.
