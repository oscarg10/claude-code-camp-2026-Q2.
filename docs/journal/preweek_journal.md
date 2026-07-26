# Preweek Technical Documentation

## Technical Goal

The technical goal of Preweek (Explore) is to determine how well Agent
Architectures fit our business use-case, using a tbaMUD server as the
test environment.

[Ref 1] Examples of Agent Architectures That Scale With Effort:
- An agent file with referenced files, e.g. `AGENT.md`, `@~/docs/*.MD`
- Agent Skills driven by main agent, e.g. `~/.skills`
- Filesystem Subagent driven by a coding harness or Coding Agent SDK, e.g. -> yet to be done. 
  `~/subagents`
- AI workflow automation platform, e.g. n8n -> decided not to do. 
- Use a generic AI Agent SDK that leverages plug-and-play generic AI packages -> not done yet
- Use low-level first-party LLM SDKs and write our own agentic loop
- Use REST APIs directly, write our own agentic loop -> not done yet
  - The agentic loop is model-driven orchestration with middleware
    programmatic guidance
  - The agentic loop is code-driven orchestration

Decided to move on after completing the first two explorations due to time constraints. However, the plan is to come back and explore the agent sdk. N8n I'll skip since I think this will not be useful for our purpose. 


## Technical Uncertainty
- I'm uncertain if a coding harness's agentic loop is effective/productive
  enough to drive a non-coding workload.
- I'm uncertain if an LLM's thinking mode and other intelligence parameters
  are sufficient to hold memory and drive decisions for a work-specific
  use-case.
- I'm uncertain that a coding harness can interact with a MUD without an
  interface or SDK, or manage the telnet session itself — specifically
  whether a shell-invoked agent can hold a persistent connection at all,
  given that each shell call starts and finishes rather than staying open.

## Technical Hypotheses
- Based on [Ref 1], I think we will have issues with the coding harness
  driving the MUD without an interface, because we don't have a defined API
  — we are driving commands over a protocol we need to live-monitor. Telnet
  communication seems like it would be a sticking point.
- I think we will need an interface because managing a long-lived telnet
  session may prove difficult. In the past I've always found managing
  live sessions challenging.
- I think that the only agent architecture able to drive our use-case will
  be one where we implement a specialized agentic loop, as I think generic
  models' memory will not be capable enough to remember and navigate the
  MUD world.
- I think we need to roll our own agent without an SDK because generic
  primitives for observability and memory won't fit our use-case without
  specialized implementation, and because we want to connect broadly with
  all frontier models — many SDKs will lack support for one of them.

## Technical Observations

**Tier 1 — Plain `CLAUDE.md` agent.** A bare agent (no framework) driven by
an operating manual and two memory files could not connect to the MUD
directly: the original instructions told it to use `telnet`/`nc` as a human
would, which hangs a shell-invoked agent forever waiting on interactive
input, and a fresh `nc` call per command lands back at the login screen
instead of wherever the character actually is. The fix was a session-bridge script (`bin/mud "<command>"`) that opens a fresh connection, logs in (triggering tbaMUD's own "Reconnecting..." feature to resume in-place),
sends one command, waits for the reply, strips ANSI codes, and returns clean
output — with retry logic to smooth over the game's few-second
client-detection negotiation. Once the bridge existed and `CLAUDE.md` was
corrected to call it instead of raw `telnet`/`nc`, login, movement, and
state persistence worked correctly across independent process invocations.

**Tier 2 — Agent Skill.** The same bridge logic, repackaged as a
`SKILL.md` + script instead of a whole-session identity file, produced
identical capability with cleaner packaging (path resolution anchored to
the script's own location rather than caller working directory). This
confirms skills and subagents, paired with a session-management script, are
a viable architecture — but they still depend entirely on that external script to manage the connection; neither tier could talk to the MUD on agent reasoning alone.

**Markdown-file memory is weak for navigation.** Driving the agent with
plain `data/player.md` / `data/world.md` memory files, rather than
structured/queryable world data, produced fragile, verbose navigation
instructions the agent had to re-derive or re-state at length, e.g.:
```sh
To reach the **Newbie Zone** from Market Square:
1. `north` → Temple Square
2. `north` → Temple
3. `north` → Altar
4. `north` → Behind Altar
5. `north` → Great Field
6. `north` → Great Field (with newbie zone sign)
7. `east` → Newbie Zone entrance
8. `north` → Enter corridor
```
This suggests plain markdown notes are not a durable substitute for real
map/world data structures.

**Ground-truth world data outperforms wandering.** Using the project's own
world-parser source files (raw `.wld` zone data) as a ground-truth map let
the agent plan exact routes and locate specific rooms (e.g. grepping for a
"bakery" mention to find the correct room among red herrings, or finding a
guildmaster's actual load location to distinguish a guild's entrance hall
from its real practice yard) — a materially better strategy than
undirected exploration.

The agent was able to successfully reach the bakery and also the guild to practice the kick skill. The main gap, which is explained below, was when it tried to fight someone. It started the fight but it felt as if after the first command was triggered, the connection got dropped. 


**A real architectural limitation surfaced in combat.** The reconnect per 
command bridge worked for anything non realtime. For example - moving, looking,
shopping, or practicing skills; but broke down in sustained combat because
the bridge disconnects after every single command by design. Any fight
still ongoing at disconnect time triggered the game's own link-dead
handling and relocated the character mid-fight with no command issued to
cause it. This is a genuine gap, not a bug in the bridge logic itself. It
reflects the mismatch between "one command per process" and MUD combat's
real-time, multi-round nature. This still needs to be implemented in week 1 or 2.

## Technical Conclusions
- Skills and Subagents are capable of driving the MUD, provided they are
  paired with a script that manages the session/connection on their behalf.
- We do need specialized memory for map navigation and world data; plain
   memory files are not sufficient on their own.
- The reconnect-per-command (meaning manually connecting through nd) architecture is solid for non real time actions
  but not for sustained, real time interactions like combat. A variation of this connection is needed for a better approach in the future. This still needs to get built. 
- I opened a new technical usecase: whether our agent needs to handle
  multiple sessions for multiple players playing at the same time, since
  co-op is a common factor in MUDs we hadn't considered in our design.
- Implementing our own specialized agentic loop remains technically
  uncertain and will need deeper exploration in Week 1 or 2.
- Without a customized agentic loop, agents could not perform goals
  efficiently, and lacked key meta-strategies or journey/player-level
  strategy.

## Key Takeaway
When we have a specialized use case like playing a MUD, we likely cannot
leverage generic SDKs for agents, because we need specialized tooling (a
session-bridge script to manage the live connection) and specialized
agentic loops (structured world/memory data rather than prose notes) to get
reliable, efficient behavior.
