# Historical real player names

Original project work: **djultra64**.

Version 0.7 replaces the eight encoded name bytes in all 2,332 factory player
slots: 100 national teams of 22 players, plus six combined teams of 22 players.
The 132 combined-team entries follow the original source-country and source-slot
provenance, independently checked against the user's private PAL ROM.

This is a historical name assignment, not a claim that every fictional original
has been conclusively identified. Recognizable names received individual review;
remaining slots use documented real internationals of the same country, with
position considered where known. Original appearance, attributes, jersey numbers,
lineups and gameplay are retained. A name replacement does not authenticate every
original attribute as a biography of the assigned real player.

The original field holds eight encoded Latin bytes. Long names are abbreviated,
accents are transliterated, and repeated family names are disambiguated with given
initials. The sourced names as recorded by the historical archive remain in the
[complete data table](../../config/rosters/real-names-1999-2000.json). Some archives
record only a given initial; no missing full given name is invented.

## Sources and period exceptions

The main source is [National Football Teams](https://www.national-football-teams.com/),
using each country's 1999 and 2000 appearance records. Additional 1999 Fiji records
and a 2000 DPR Korea keeper are documented by [11v11](https://www.11v11.com/).
The unused San Marino reserve keeper is documented on the
[31 March 1999 match bench](https://www.bdfutbol.com/es/p/p.php?id=300160).
Each player carries direct source and dated roster URLs in the data table.
Spelling variants are consolidated rather than counted as separate players.

Appearance lists omit unused substitutes and can be incomplete. The user approved
nearby-year internationals where 1999–2000 evidence cannot fill the original slots.
There are **24 such assignments**, listed below. They include a Liechtenstein
reserve goalkeeper, in addition to the three countries with incomplete main lists.
These exceptions are explicit; they are not presented as verified 1999–2000 caps.

| Team | Player as recorded | Documented nearby years |
| --- | --- | --- |
| Liechtenstein | Martin Oehri | 1998 |
| North Korea | Yong-Mu An | 2001, 2002 |
| North Korea | Chol Jon | 2001, 2002 |
| North Korea | Kwang-Chon Ri | 2001, 2002 |
| Fiji | Salesh Kumar | 1998 |
| Fiji | Atunesh Prasad | 2001 |
| Papua New Guinea | David Aua | 2002 |
| Papua New Guinea | Hans Fred | 2002 |
| Papua New Guinea | Harrison Kamake | 2002 |
| Papua New Guinea | Yanding Tomda | 2002 |
| Papua New Guinea | Joe Aisa | 2002 |
| Papua New Guinea | Reggie Davani | 2002 |
| Papua New Guinea | Nasa Wangu | 2002 |
| Papua New Guinea | Jonah Malus | 2002 |
| Papua New Guinea | Francis Moiyap | 2002 |
| Papua New Guinea | Tapas Posman | 2002 |
| Papua New Guinea | Ken Gule | 2002 |
| Papua New Guinea | Selan Elizah | 2002 |
| Papua New Guinea | Michael Lohai | 2002 |
| Papua New Guinea | Richard Daniel | 2002 |
| Papua New Guinea | Paul Komboi | 2002 |
| Papua New Guinea | Maurie Wasi | 2002 |
| Papua New Guinea | Andrew Kassam | 2002 |
| Papua New Guinea | Paulo Paterson | 2002 |

## Runtime ownership and verification

Only a genuine ROM DMA with the verified factory-table address mapping receives
the replacement. The imported ROM is immutable. Partial loads patch only the name
bytes included in that load; reloading restores the same real defaults. Active
match records, Career-created characters, registered players and stored save data
are not independently rewritten. User data follows the original game's flows.

The supported ROM's complete identity is checked before installing the table.
Tests check all 2,332 encoded outputs, full and fragmented loads, wrong identities
and destinations, field boundaries, reloads, and preservation of user-data regions.
The public generator rejects incomplete, ambiguous, unsourced or stale tables.
