# Week 1 Baseline Technical Documentation

## Technical Goal

The technical goal of Week 1 (Baseline) is to build BOUKENSHA's agentic loop
from scratch, step by step, using low-level first-party LLM SDKs and our own
orchestration rather than a generic agent framework — the path flagged as
"not done yet" in the Preweek exploration ([Ref 1] in
`docs/journal/preweek_journal.md`). Each step lives in its own numbered
folder (`00_config`, `01_struct_skeleton`, ...) and is built first in Ruby,
then ported to Python in lockstep, so both language tracks stay at parity
step-for-step as the design solidifies.

So far this covers:
- `00_config` — a `Config` class that loads `.boukensha/settings.yaml` and
  `.boukensha/.env`, plus a stateless `Tasks::Base`/`Tasks::Player`
  abstraction for per-task provider/model/prompt resolution.
- `01_struct_skeleton` — the core data structures (`Tool`, `Message`,
  `Context`) that everything downstream will pass around.

## Technical Uncertainty

- I'm uncertain whether porting each step to a second language (Python) as
  we go is worth the overhead, versus finishing the Ruby track first and
  porting the whole thing once at the end. -> I am still doing it since I am most
  comfortable with Python. 

- I'm uncertain how much of the config/data-structure layer we're building
  now will actually survive once the real agentic loop (API calls, tool
  execution, the run loop itself) lands in later steps.

## Technical Hypotheses

- I think building config and data structures before any API-calling logic
  will pay off, because per-task provider/model/prompt resolution is exactly
  the kind of thing that's painful to retrofit once multiple tasks
  (player, judge, summarizer, etc.) exist.
- I think porting to Python at every step, rather than at the end, will
  surface design bugs earlier. 

## Technical Observations

**Cross-language porting caught bugs that a same-language read-through
missed.** Porting `00_config` to Python required tracing `Config#tasks`
back through `dig(:tasks)`, which surfaced that `.boukensha/settings.yaml`
was missing its top-level `tasks:` key — `player:` and `mud:` were sitting
at the document root instead. This wasn't a Python bug; it broke the Ruby
side identically (`Base.fetch` blowing up on `nil["prompt_override"]`) the
moment it was noticed. I noticed/got the same type of bug later in the
session when the settings file drifted back to the unnested shape. Config schema drift seems to be a recurring risk here, worth a schema check rather than relying on rediscovery.

**The same relative-path arithmetic bug was copy-pasted across steps.**
Both `00_config/examples/example.rb` and
`01_struct_skeleton/examples/example.rb` compute their `BOUKENSHA_DIR`
override as `File.expand_path("../../../.boukensha", __dir__)` — one `../`
short of the actual repo root, landing on `week1_baseline/.boukensha`
instead. Because each new step starts as a copy of the previous step's
folder, this off-by-one shipped twice before being caught (once while
debugging `00_config`, then again independently in `01_struct_skeleton`).

**Environment/tooling drift cost more debugging time than the actual
language port.** Running `./00_config` failed initially because macOS's
built-in Ruby 2.6 (`/usr/bin/ruby`, on `PATH` by default) doesn't match the
Homebrew Ruby 4.0.6 the `Gemfile.lock` was generated against
(`BUNDLED WITH 4.0.10`, which Ruby 2.6's bundler can't even resolve). Fixing
`PATH` in `~/.zshrc` resolved it. Separately, the Python launcher assumed a
single shared virtualenv at the **repo root**, but the first attempt created
`.venv` inside `python/00_config/` instead — the launcher script's own
relative path to `.venv` was the source of truth here, not habit from a
typical per-project virtualenv workflow.

## Technical Conclusions

- Porting each step to a second language as we go, rather than deferring
  translation to the end is much better for a faster bug identification and resolution.
- It is way better to have Claude Code (in my case, or the AI agent being used) to help corroborate the accuracy of pathing

## Key Takeaway

Building the agentic loop bottom-up (config → data structures → ... ) and
porting each step to Python immediately, rather than in one batch at the
end, is worth the time due to the more often consistency checks so that bugs and typos stop
compounding forward into every subsequent step.