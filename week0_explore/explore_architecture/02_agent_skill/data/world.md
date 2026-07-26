# World — Midgaard (partial map)

Rooms visited so far, with vnum where known. Exits noted only where
observed or confirmed.

## `#3015` — Main Street (general store side)
Exits: N → General Store (`#3010`), E → Main Street (`#3016`),
S → Pet Shop (`#3031`), W → Market Square (`#3014`).

## `#3014` — Market Square
The Midgaard Worm statue. Exits: N → Temple Square (`#3005`),
E → Main Street (`#3015`), S → Common Square (`#3025`),
W → Main Street (`#3013`).

## `#3013` — Main Street (Bakery side)
Exits: N → **The Bakery** (`#3009`), E → Market Square (`#3014`),
S → Armory (`#3020`), W → Main Street (`#3012`). A cityguard stands here.

## `#3009` — The Bakery
Exits: S → Main Street (`#3013`). The baker is present.

**Wares (via `list`):**
| Item | Cost | Stock |
|---|---|---|
| A danish pastry | 7 gold | unlimited |
| A bread | 14 gold | unlimited |
| A waybread | 73 gold | unlimited |

## Known but unvisited (named in room descriptions)
- General Store (`#3010`, north of `#3015`)
- Pet Shop (`#3031`, south of `#3015`)
- Armory (`#3020`, south of `#3013`)
- Main Street continues west of `#3013` (`#3012`, unexplored)
- Temple Square (`#3005`, north of Market Square)
- Common Square (`#3025`, south of Market Square)

## `#3000` — The Reading Room
West of the Temple of Midgaard (`#3001`). Contains **the teleporter** — a
gettable object with a command trigger (`teleport <keyword>`) that
transports the holder to one of ~180 bolted-on zones donated to this
tbaMUD build. Full list via `help zones` in-game (heavily paginated — the
in-game pager doesn't survive this bridge's reconnect between commands, so
reading it required a one-off script that stayed connected for the whole
listing). Also: a bulletin board, and a saleswoman NPC selling overpriced
gadgets.

**Must be carried, not just present in the room** — `teleport newbie` said
"Huh!?!" until we did `get teleporter` first.

### Zone 5 — "NEWBIE Farm" (levels 1-10, keyword `newbie`)
Reached via `teleport newbie` from the Reading Room while holding the
teleporter. Arrives at **Small Path** (`~#500`) — "a small dirt path...
surrounded by trees and gorgeous flowers." A dandelion, a little spring,
and **a cute little bunny** were present (`consider` → "the perfect
match!", a fair fight for a level 1 character). Exits seen: `w` from the
arrival room; a *different* "Small Path" room (same name, different flavor
text) with exits `e s w` appeared after the aborted bunny fight — this
zone has multiple same-named path segments, worth mapping properly on a
future visit.

Other newbie-appropriate zones spotted in `help zones`, not yet visited:
`234 Newbie SCHOOL` (1-4, keyword `school`), `306 Newbie TREE` (1-9,
keyword `tree`), `28 MUDSCHOOL` (1-3, keyword `mudschool`),
`74 Newbie GRAVEyard` (3-5, keyword `grave` — above our current level).

### Farm Entrance (Newbie Farm, vnum not recorded)
South of the "beginning of the farm" Small Path room. "An ugly little
rooster" here (`consider` → "you would need some luck!" — tougher than the
bunny). Fled here after a 20-round fight against the rooster hit the
safety cap — see `player.md`. Exits: n, e, s (e leaves the farm per the
room text: "if you go back to the east, you will be leaving the farm").
A small pile of cracked corn is on the ground.

### Small Path — "beginning of the farm" segment
West of the second Small Path room. Flavor text jokes no animals are
visible here ("Where are all the animals? Maybe they are all hiding.") —
a large boulder and a leafy apple tree are the only features. Exits: e, s
(south leads to Farm Entrance).
