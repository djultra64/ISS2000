# Football scheme preference storage

Original project work: `djultra64`.

Each logical controller port stores a football scheme independently of its
fourteen raw menu bindings, detected/manual controller family and vibration.
`PortPreferences::football_scheme` selects Type1, Type2, Type3, Type4, Type5 or Free.
`free_football_bindings` retains a complete eight-position permutation even while
a preset is selected. A new or migrated port defaults to Type1 and a Free copy
of the same Type1 matrix from `controller_schemes.hpp`.

The version-1 input-preferences JSON retains `manualFamily`, `buttons` and
optional legacy `vibration`. New saves add the complete pair `footballScheme`
and `freeFootballBindings`. The first is one of `type1`, `type2`, `type3`, `type4`, `type5`
or `free`. The second uses the action order Pass, Shoot, Dash, Lob, Through,
OneTwo, Curve, Cursor and physical names `south`, `east`, `west`, `north`, `l1`,
`r1`, `l2`, `r2`. These are positions, never Xbox/Nintendo letter labels.

Legacy two- and three-key port records load without changing their old menu
bindings or family. Missing vibration still defaults to enabled. If either new
field is present, both are required. Unknown fields/schemes/physical names,
duplicated JSON keys, invalid types, missing actions and repeated physical
positions reject the complete preference set before live application or save.
The Free permutation is validated even when a preset is active.

Existing atomic input storage and the two-file PC Settings rollback remain the
publication paths. Snapshot/apply carries both new fields for all four ports;
invalid later ports cannot partially update earlier ports. Callers must merge a
fresh preferences snapshot before saving one player's changes. Restoring only
raw menu bindings must preserve the separate football fields.

These persistence changes do not decode physical input, alter original guest
packets, select an original engine profile, or add editor UI. Those integrations
are separate from storage tests. Existing portable user data is not rewritten
merely by reading it.
