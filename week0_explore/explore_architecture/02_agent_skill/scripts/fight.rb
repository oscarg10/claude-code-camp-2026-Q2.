#!/usr/bin/env ruby
# frozen_string_literal: true

# scripts/fight.rb — sustains real-time combat over ONE open connection.
#
# scripts/mud.rb reconnects for every single command, which is fine for
# moving/looking/shopping/practicing but breaks combat: tbaMUD protects
# players who go "link-dead" mid-fight by pulling them out of it, and a
# fresh reconnect between every command is indistinguishable from that to
# the server. This was observed live twice — fighting a fido, then a bunny
# — where the character was relocated mid-fight the moment the bridge
# disconnected, with no movement command ever issued. This script fixes
# that by opening one connection and staying on it for the whole fight,
# only disconnecting once things are actually resolved.
#
# Usage:
#   ruby scripts/fight.rb "<target>" ["<opening command>"]
#
# Examples:
#   ruby scripts/fight.rb fido              # opens with "kill fido"
#   ruby scripts/fight.rb fido "kick fido"   # opens with a specific move
#
# Stops (and flees if still in danger) when:
#   - the target dies
#   - the target is no longer there
#   - HP drops to/below FIGHT_FLEE_PCT of max HP (default 50%)
#   - FIGHT_MAX_ROUNDS is reached with no resolution (default 20) — this is
#     a safety net so the script never just leaves the fight hanging open
#     when it exits
#
# Config — same .env as scripts/mud.rb, plus:
#   FIGHT_MAX_ROUNDS   default 20
#   FIGHT_FLEE_PCT     default 0.5 (fraction of max HP)
#
# Requires Ruby >= 3.0 — see scripts/mud.rb for why the re-exec below has
# to stay parseable under older Rubies too.
if RUBY_VERSION < "3.0"
  newer = [
    "/opt/homebrew/opt/ruby/bin/ruby",
    "/usr/local/opt/ruby/bin/ruby",
  ].find { |p| File.executable?(p) }

  if newer
    exec(newer, __FILE__, *ARGV)
  else
    abort "scripts/fight.rb needs Ruby >= 3.0 (found #{RUBY_VERSION}); install with `brew install ruby`"
  end
end

require_relative "../../../mud_manager/lib/mud_manager"
require_relative "lib/mud_helpers"

SKILL_DIR = File.expand_path("..", __dir__)
MudHelpers.load_dotenv(File.join(SKILL_DIR, ".env"))

target  = ARGV[0]&.strip
opening = ARGV[1]&.strip
if target.nil? || target.empty?
  warn %(usage: ruby scripts/fight.rb "<target>" ["<opening command>"])
  exit 2
end
opening = "kill #{target}" if opening.nil? || opening.empty?

username = ENV["MUD_NAME"].to_s
password = ENV["MUD_PASSWORD"].to_s
if username.empty? || password.empty?
  warn "MUD_NAME and MUD_PASSWORD must be set (env vars, or a .env in #{SKILL_DIR})"
  exit 2
end

host          = ENV.fetch("MUD_HOST", "localhost")
port          = Integer(ENV.fetch("MUD_PORT", "4000"))
quiet         = Float(ENV.fetch("MUD_QUIET", "1.0"))
timeout       = Float(ENV.fetch("MUD_TIMEOUT", "10"))
login_retries = Integer(ENV.fetch("MUD_LOGIN_RETRIES", "2"))
max_rounds    = Integer(ENV.fetch("FIGHT_MAX_ROUNDS", "20"))
flee_pct      = Float(ENV.fetch("FIGHT_FLEE_PCT", "0.5"))

begin
  session = MudHelpers.connect(
    host: host, port: port, timeout: timeout,
    username: username, password: password, retries: login_retries
  )
rescue MudManager::Session::Timeout
  warn "login timed out after #{login_retries} attempt(s)"
  exit 1
rescue MudManager::Session::LoginError => e
  warn "login failed: #{e.message}"
  exit 1
rescue MudManager::Session::Error => e
  warn "session error: #{e.message}"
  exit 1
end

HP_RE   = /(\d+)H\s+\d+M\s+\d+V/.freeze
DEAD_RE = /is dead|You have (?:slain|killed)/i.freeze
GONE_RE = /Huh\?!?|isn't here|can't find|not here/i.freeze

outcome = nil

begin
  session.drain

  # `score` first, purely to learn max HP so the flee threshold scales
  # with the character instead of being a hardcoded number.
  session.send_command("score")
  score_text = MudHelpers.strip_ansi(session.read_until_quiet(quiet, timeout: timeout))
  print score_text
  max_hp = score_text[/(\d+)\((\d+)\) hit/, 2]&.to_i
  flee_threshold = max_hp ? (max_hp * flee_pct).ceil : nil

  session.send_command(opening)
  round = 0

  loop do
    round += 1
    text = MudHelpers.strip_ansi(session.read_until_quiet(quiet, timeout: timeout))
    print text

    current_hp = text.scan(HP_RE).last&.first&.to_i

    if text.match?(DEAD_RE)
      outcome = :victory
      break
    elsif text.match?(GONE_RE)
      outcome = :target_gone
      break
    elsif flee_threshold && current_hp && current_hp <= flee_threshold
      outcome = :fled_low_hp
      session.send_command("flee")
      print MudHelpers.strip_ansi(session.read_until_quiet(quiet, timeout: timeout))
      break
    elsif round >= max_rounds
      outcome = :max_rounds_disengaged
      session.send_command("flee")
      print MudHelpers.strip_ansi(session.read_until_quiet(quiet, timeout: timeout))
      break
    elsif text.strip.empty? && round > 1
      # Nothing happened this round — the fight has likely already ended
      # quietly (e.g. the target left before we could tell).
      outcome = :no_activity
      break
    end
  end
rescue MudManager::Session::Error => e
  warn "session error: #{e.message}"
  outcome = :session_error
ensure
  session.close
end

warn "\n[fight.rb] outcome: #{outcome || 'unknown'}"
exit(outcome == :victory ? 0 : 1)
