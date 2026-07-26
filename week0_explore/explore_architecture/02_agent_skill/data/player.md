# Player

- **Name:** Dummy
- **Class:** Warrior — title at level 1: "Dummy the Swordpupil"
- **Age:** 17
- **Level:** 1 (5 exp; 1995 more needed for level 2)
- **Gold:** 0 | **Quest points:** 0 | **Quests completed:** 0
- **Time played:** 0 days, 22 hours

## Stats (via `score`)
- HP: 14/23
- Mana: 100/100
- Movement: 65/84
- Armor class: 90/10
- Alignment: 0
- Position: standing
- Condition: hungry, thirsty

## Skills
- `kick` — **(bad)**, unchanged. Practiced once at the fighters'
  guildmaster in the Tournament and Practice Yard (`#3023`). 0 practice
  sessions remaining (these refill on level-up, which needs exp from
  kills — see below).

## Notable events
- **Attempted to fight a bunny** in the Newbie Farm zone (`teleport
  newbie` from the Reading Room's teleporter — see `world.md`) using
  `kick`. Missed, and the moment the bridge disconnected after that single
  attempt, the character was relocated to a different room with no
  movement command issued — same symptom as an earlier fido fight.
  Confirmed the combat-vs-reconnect problem was systemic, not one mob's
  fluke.
- **Fought an ugly little rooster** (Farm Entrance, Newbie Farm zone;
  `consider` → "you would need some luck!") using the new
  `scripts/fight.rb`, which keeps one connection open for an entire fight
  instead of reconnecting per command. Ran a full, trackable 20-round
  fight (HP 23 → 14, all visible, no mystery relocations), hit the
  round-cap safety net, and fled cleanly on command to Farm Entrance. The
  rooster survived, but **exp went from 1 → 5** — real, if partial,
  progress. `kick` is still "(bad)" (needs a practice session, which needs
  a level-up, which needs more exp), but sustained combat is now provably
  reliable via `scripts/fight.rb`.
