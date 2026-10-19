# PAL r70 menu placement and common shadow style

Original project work: **djultra64**. Linux only, one worker, no agents.
Windows remains frozen. Existing packages and user data are preserved.

## Menu composition

The requested relative right translations use the same leading-edge basis as
r69's Pre-season adjustment, rounded to the quarter-pixel renderer grid. Euro
Cup and Penalties move 8.75 logical pixels (5%); Scenario moves 17, Training
16.25 and Option 15.25 logical pixels (10%). Every item's label, selected glow
and lamp move rigidly together. Original size, UVs, derivatives, vertical
positions, heading, ball, row backgrounds and Exit Game are retained. The 4:3
horizontal layout retains its original behavior.

## Shared shadows

The previous silhouette admission stopped after the first 22 football states.
The three reciprocal referee/assistant roots at table positions 22 through 24
therefore retained the legacy shadow. They now receive the same eleven-joint,
eighty-vertex silhouette, primitive material and lighting-dependent alpha as
players. Both pinned two-quad and central four-quad floodlight lists recover
the strongest original quad's light direction before projecting the silhouette.
The central four-quad variant was previously excluded even for players.

The ball used an independent textured quad with its own opacity and placement.
Its genuine callback now prepares the original ball first; a scoped adapter
then replaces only its authenticated attached shadow child's display list.
A sixteen-vertex convex projected sphere uses the identical untextured black
primitive material as players: alpha 96 in daylight and 64 in weather/night,
pixel depth and a ground offset of one tenth of a world unit. Ball height
moves its ground projection; the ellipse accounts for the same light vector.
The original sphere radius is 1.4 world units. Original body, texture, physics,
pose and clock data remain untouched.

Both original ball detail lists, the original callback prologue, complete
legacy shadow material, exact object pools and reciprocal parent/body/shadow
links must agree. Before the genuine callback runs again, an authenticated
replacement is restored to its original list. Suppressed and foreign scenes
retain original behavior rather than carrying a stale world-space disc.

The existing two reserved 64 KiB banks now hold 26 bounded 2048-byte slots:
22 players, three officials and the ball. No new memory region is reserved.
The ball's sixteen-vertex load has its own immutable lifetime and exact
address/count interpolation tag; it cannot alias a human chunk or foreign
geometry. Existing cut, seek, bank, FIFO and generation checks remain active.

## Verification scope

The original CPU menu fixture first rejected the old positions, then passed
in 9.786 seconds. The actual training and match snapshots first reproduced
excluded official/ball shadows and the central nighttime material. After the
correction, all six focused shadow tests passed in 33.777 seconds, including
both banks, all 25 human owners, four original material variants, ball height,
foreign ownership/material negatives, restore behavior and scoped RT64 loads.
These CPU/adapter results are not a new GPU nighttime or performance claim.

Current runtime/full-suite receipts live in `.local/r70-verification` and
`.local/r63-ui/runs/ui15`; final disposition must be read from those receipts.
The first UI14 setup ended before game launch because its SDL pkg-config path
was absent. UI15 explicitly supplies the known local SDL path.

Prior goal replay trail/overlay work and complete gameplay acceptance retain
their earlier scope. This candidate is **not accepted as 1.0**.

## Final disposition

The complete suite ran 515 tests in 500.708 seconds: 512 passed and three
historical NTSC diagnostics were skipped. Exact r70 UI15 reviewed the menu,
bounded day/clear friendly play, return to Main Select and confirmed normal
Exit Game (status 0). The recorded compositor, game, monitor and harness PIDs
are absent; the owned sink and private runtime are gone.

Both actual field banks contain all 25 human owner headers plus the ball,
with exact expected display-list commands and shared alpha 96. The live RAM
copy is not atomic: one assistant was sampled during its original callback,
with its temporary original display-list pointer while both completed bank
headers retained its verified projected lists. Header/command/reciprocal-owner
validation avoids presenting that copy as an atomic completed task snapshot.
Actual game images establish the bounded daytime visual review. Full gameplay,
physical-controller, nighttime GPU and sustained-performance acceptance remain
with their prior scope.

All 46 manifest files and 40 notices verify; fresh portable data is empty.
Final package SHA-256 is
`50c405647e410b32a87bd8f192003cf277d072587b17d05205e43ee222e2dcbb`.
