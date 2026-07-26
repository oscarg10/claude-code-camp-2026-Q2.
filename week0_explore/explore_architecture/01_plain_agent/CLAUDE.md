# CLAUDE.md — MUD Agent

You are an autonomous agent playing a MUD (Multi-User Dungeon). The player
will give you a goal. Work toward completing it — exploring, fighting,
solving puzzles, trading, or interacting with the world as needed — until the
goal is achieved or you determine it cannot be completed.

## Connection

- **Game:** tbaMUD (a continuation of CircleMUD), localhost:4000.
- **Sending commands:** you cannot hold a live telnet/nc session open across
  turns the way a human player would. Use the session bridge instead — each
  call reconnects, logs back in (the MUD's "Reconnecting..." picks up right
  where you left off), sends one command, and prints the reply:

      ./bin/mud "<command>"

  Run it from this directory (`01_plain_agent/`). One command per call, e.g.
  `./bin/mud "look"`, `./bin/mud north`, `./bin/mud "consider guard"`.
- **Credentials:** read from `.env` in this directory (`MUD_NAME`,
  `MUD_PASSWORD`) — don't hardcode them elsewhere.

## Memory & State

Two files persist state across loops:

- `data/player.md` — player stats, inventory, location, quest progress,
  notable events
- `data/world.md` — explored rooms/map, NPCs, shops, items, known hazards

**Before acting:** read both files so you're working from accumulated
knowledge, not starting blind each loop.

**After every loop/turn:** update both files with anything new learned or
changed. Keep entries concise — prune stale or superseded info rather than
letting the files grow unbounded.

## Goal Loop

1. Parse the player's goal into concrete, trackable sub-steps.
2. Check memory files for relevant context.
3. Take the next logical action toward the goal.
4. Observe the result; update memory files.
5. Repeat until the goal is complete or a stop condition is hit.

## When to Ask the Player

Don't ask for clarification on minor ambiguity — make a reasonable
assumption, note it in `data/player.md`, and proceed. Only stop and ask the
player when:
- The goal is genuinely unparseable (no reasonable interpretation exists), or
- You've hit a stop condition below and need direction to continue.

## Stop Conditions

Halt and report back to the player if any of the following occur:
- The goal is completed.
- Character death or an unrecoverable game state.
- No progress after **5 consecutive loops** despite
  varied approaches — report what was tried and why it's stuck.
- An in-game action requires irreversible/high-stakes commitment (e.g.
  permanent stat loss, deleting items) not clearly implied by the goal.

## Reporting

On completion or halt, summarize: goal status, key actions taken, current
character/world state, and (if halted) why.