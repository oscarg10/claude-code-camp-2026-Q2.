---
name: tbamud-play
description: Sends commands to and reads replies from this project's local tbaMUD (a CircleMUD/DikuMUD-derived game) server running on localhost:4000, handling the login handshake and telnet quirks that make a plain `nc`/`telnet` call unreliable for a non-interactive agent. Use this skill whenever the task involves exploring, walking around, looking things up, fighting, shopping, or otherwise interacting with "the MUD," "the game," or a named in-game place for this project (e.g. "find the bakery," "check my inventory," "go north and look around," "what's being sold in the market square," "attack the guard"). Do NOT attempt to connect with `nc` or `telnet` directly for this — those hang waiting on an interactive session; always go through scripts/mud.rb instead.
---

# tbaMUD Play

## Persistent Memory (read this first)

This skill keeps two markdown files that survive across sessions. Read them at the start of every session and update them whenever something notable happens. They are the only way to make progress on long-term goals like reaching level 7 or defeating a specific monster.

```data/player.md   — character stats, skills, inventory, goals, notes
data/world.md    — map layout, monsters, shops, navigation shortcuts
```
The data/ directory is at the same location as this skill file.

## Why this exists

This project runs a local tbaMUD server (a modern continuation of CircleMUD)
on `localhost:4000` via Docker. A human plays it by opening one long-lived
`nc`/`telnet` connection and typing into it — that one open connection is
what keeps them logged in and standing in a given room.

An agent working through a shell tool can't hold a connection open like
that: each shell call starts and finishes, so a raw `nc`/`telnet` call would
just hang forever waiting for interactive input, and piping one command
through `nc` would open a brand-new, unauthenticated connection and land
back at the login screen instead of wherever the character actually is.

`scripts/mud.rb` solves this the way the game itself expects it to be
solved: tbaMUD lets a character "reconnect" — log in again with the same
name and you're dropped right back where you left off, mid-game. So each
call to this script opens a fresh connection, logs in (triggering that
reconnect), sends exactly one command, waits for the reply to finish
arriving, prints it, and exits. The character's real position and state
live in the game server, not in the script.

## Usage

```sh
ruby scripts/mud.rb "<command>"
```

One command per call — read each reply before sending the next, the same
way a human player would. Examples:

```sh
ruby scripts/mud.rb "look"
ruby scripts/mud.rb north
ruby scripts/mud.rb "consider guard"
ruby scripts/mud.rb "buy bread"
```

Run it from this skill's directory (`02_agent_skill/`) so `.env` and the
relative path to the `mud_manager` gem resolve correctly.

## Configuration

Credentials and connection settings live in `.env` (gitignored) next to
this file, seeded from `.env.example`:

```
MUD_NAME=dummy
MUD_PASSWORD=helloworld
MUD_HOST=localhost
MUD_PORT=4000
```

## What you get back

Output has ANSI color codes stripped and the stale leftover prompt from the
login step discarded, so you're reading clean room/combat/shop text. The
MUD's own status line (HP/mana/movement) is preserved at the end, e.g.:

```
23H 100M 84V (news) (motd) >
```

Read that for current health/mana/moves instead of issuing a separate
`score` call every time.

## Things to know

- **It will kick other sessions.** If a human (or another script) is
  connected as the same character via `nc`/`telnet` when this runs,
  tbaMUD's reconnect logic disconnects them in favor of this connection.
  That's expected, not a bug.
- **Requires Ruby >= 3.0.** The script re-execs itself into Homebrew's Ruby
  if it started under an older system Ruby, so you can call it directly
  without checking which `ruby` is first on PATH.
- **No built-in memory.** This skill only handles the connect/send/receive
  round trip — it doesn't track rooms visited, inventory, or a goal across
  calls. If the surrounding task needs to remember things over many calls,
  track that yourself in whatever notes/memory mechanism the task is
  already using.
