# Explore Architecture Journal

Building an agent that can play the tbaMUD server in
`week0_explore/infrastructure/`. The core challenge every tier has to solve:
a human plays by keeping one `nc`/`telnet` connection open the whole
session — that one open connection is what keeps them logged in and
standing in a given room. An agent invoked through a shell tool can't hold a
connection open like that: each call starts and finishes, so a raw
`nc`/`telnet` call just hangs forever waiting on interactive input, and a
fresh connection per command lands back at the login screen instead of
wherever the character actually is.

## Tier 1 — `01_plain_agent`

A bare `CLAUDE.md`-driven agent: an operating manual plus two memory files
(`data/player.md`, `data/world.md`), no framework.

**Built `bin/mud "<command>"`** — the session bridge. Each call opens a
fresh connection, logs in (which triggers tbaMUD's own "Reconnecting..."
handling, dropping the character back where it left off), sends exactly one
command, waits for the reply to finish, and prints clean output.

Hardening added after live testing surfaced real problems:
- **ANSI color codes** in the raw output (`\e[0;33m`, etc.) — stripped.
- **Stale leftover prompt** from the login step bleeding into the first
  command's output — now drained before sending anything.
- **Login timing race** — tbaMUD runs a few seconds of client-detection
  negotiation before showing the name prompt, which occasionally raced the
  login handshake. Added a retry (`MUD_LOGIN_RETRIES`, default 2) on
  connect+login instead of guessing at extra sleeps.

**Ruby version problem:** `mud_manager` (the underlying gem with `Session`
+ `Primitives`) requires Ruby ≥ 3.0, but the only Ruby on the machine's PATH
was system 2.6.10. Installed Homebrew Ruby (4.0.6). Since Homebrew Ruby is
*shadowed* by system Ruby on PATH, `bin/mud` checks its own `RUBY_VERSION`
at startup and re-execs itself into the newer Ruby if needed — which means
the whole script has to stay parseable under Ruby 2.6 even though it only
runs under 3.0+, since Ruby must parse an entire file before executing any
of it (including the re-exec check). Hit this directly: an endless-method
def (`def x(y) = z`, Ruby 3.0+-only syntax) slipped into the script during a
later edit and broke the re-exec it was supposed to enable. Fixed by
reverting to classic `def...end`.

**`CLAUDE.md` correction:** it originally told the agent to connect via
`telnet localhost 4000` / `nc localhost 4000` directly — that's the human
instructions, copied in without adjusting for the fact that an agent can't
hold a session open the same way. Rewrote the Connection section to point
at `./bin/mud` instead, and to pull credentials from `.env` rather than
hardcoding the password in a tracked file.

**Verified live:** login, movement, and state persistence across
independent process invocations (moved west in one call, a wholly separate
process's `look` correctly showed the character still in the new room).

**Left open:** a `.gitignore` scoped to raw/regenerable exploration output
(logs, transcripts) was discussed but never actually written to disk.

## Tier 2 — `02_agent_skill`

Same underlying capability, repackaged as a Claude Code Skill (`SKILL.md` +
a bundled script) instead of a whole-session `CLAUDE.md` identity — a
different way of making the capability available, narrower in scope than
"this session's whole personality."

**Scope decision, made deliberately:** this lives only under
`week0_explore/explore_architecture/02_agent_skill/`, not under
`.claude/skills/`. That means it is **not** auto-discoverable or
auto-triggerable by Claude's Skill tool as-is — it's a self-contained
reference artifact for this tier. To actually invoke it, a session either
reads `SKILL.md` directly and follows it, or someone copies it into
`.claude/skills/` later to make it a real, triggerable skill.

**Script choice:** reused the tier-1 bridge logic (`scripts/mud.rb`,
functionally identical to `bin/mud`) rather than writing a fresh plain
`nc`/bash script as originally described. Reasoning: the hard part was
never "call nc" — it's knowing when the MUD's reply has actually finished
and handling its telnet/login quirks, which the tier-1 bridge had already
solved and proven live. A bash/`nc` version would very likely rediscover
the same login-timing and reply-boundary problems from scratch.

**Verified live:** syntax-clean under both Ruby 2.6 and Homebrew Ruby;
`ruby scripts/mud.rb "look"` round-trips correctly both from inside the
skill directory and from the repo root — path resolution is anchored to the
script's own file location (`__dir__`), not the caller's current directory,
so no `cd` is required to run it correctly if the full path is given.

## First real play session (via tier 2's bridge)

Used the project's own `circlemud-world-parser` source data (raw
`.wld`/`.mob`/`.zon` files) as a **ground-truth reference** to plan routes
before walking them live, rather than exploring blind — found the Bakery
and the actual Warriors' Guild guildmaster location this way. Findings from
that session (map, character state, the Bakery's wares, the guild training)
are recorded in `01_plain_agent/data/player.md` and `data/world.md`, not
duplicated here.

## Limitation discovered: combat doesn't work reliably yet

The reconnect-per-command bridge is solid for anything that isn't
time-sensitive — moving, looking, shopping, practicing a skill — because
nothing changes server-side while the bridge is briefly disconnected
between calls. **Combat is different: it's real-time and ongoing.**
Engaging a weak mob (a "beastly fido," rated a fair fight by `consider`)
showed that whenever the fight was still active at the moment the bridge
hung up (which happens after every single command, by design), the
character got relocated to a different room with no movement command
issued — consistent with the game's own protection for a player who goes
link-dead mid-fight.

## The combat fix — `scripts/fight.rb`

Built the variant flagged above: one connection stays open for an entire
fight instead of reconnecting per command, since reconnecting mid-fight is
exactly what was triggering the game's link-dead protection.

**Shared code extracted first.** Before adding a second script, pulled the
duplicated `load_dotenv`/`strip_ansi`/connect-with-retry logic out of
`mud.rb` into `scripts/lib/mud_helpers.rb`, required by both. Two copies of
the same login/retry logic silently drifting apart is exactly the kind of
bug already hit once with the Ruby endless-method syntax slip — not worth
risking twice.

**How `fight.rb` decides when to stop:** runs `score` once up front to
learn max HP (so the flee threshold scales with the character rather than
being hardcoded), sends one opening attack, then loops reading rounds on
the same connection — checking each round's text for the target dying, the
target being gone, current HP dropping to/below `FIGHT_FLEE_PCT` (default
50%) of max, or a `FIGHT_MAX_ROUNDS` cap (default 20). Hitting the cap
proactively sends `flee` rather than just exiting and leaving the fight
hanging open — the whole point was to never again exit mid-fight
uncontrolled.

**Verified live** against "an ugly little rooster" in the Newbie Farm
(`consider` rated it "you would need some luck!" — a real, non-trivial
fight, not another guaranteed-safe pushover). Result: a full, cleanly
tracked 20-round fight (HP 23 → 14, no lost state, no mystery relocations),
hit the round cap, fled on command to a specific named room. The rooster
survived, but **exp went 1 → 5** — actual progress, which the old
reconnect-per-command bridge never produced in two prior attempts. Details
in `02_agent_skill/data/player.md` and `data/world.md`.
