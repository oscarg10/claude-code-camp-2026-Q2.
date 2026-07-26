#!/usr/bin/env ruby
# frozen_string_literal: true

# scripts/mud.rb — connect/login/command/read round trip for the tbamud-play
# skill. See ../SKILL.md for why this exists instead of a plain nc/telnet
# call: each invocation reconnects, logs in (tbaMUD's "Reconnecting..." drops
# us back where we left off), sends ONE command line, prints the MUD's reply
# to stdout, and exits.
#
# Only good for things that aren't time-sensitive (moving, looking,
# shopping, practicing) — for real-time combat, use scripts/fight.rb
# instead, which stays connected for the whole fight. Reconnecting between
# every command is exactly what breaks sustained combat: tbaMUD protects
# players who go "link-dead" mid-fight by pulling them out of it, which is
# indistinguishable from a real disconnect from the server's point of view.
#
# Usage:
#   ruby scripts/mud.rb "look"
#   ruby scripts/mud.rb north
#   ruby scripts/mud.rb "consider guard"
#
# Config — environment variables, or a .env file next to this skill:
#   MUD_NAME      character name        (required)
#   MUD_PASSWORD  character password    (required)
#   MUD_HOST      default: localhost
#   MUD_PORT      default: 4000
#   MUD_QUIET     seconds of silence that marks end-of-reply (default 1.0)
#   MUD_TIMEOUT   hard cap per read, seconds               (default 10)
#   MUD_LOGIN_RETRIES  login attempts before giving up      (default 2)
#
# Requires Ruby >= 3.0 (mud_manager gemspec constraint). On macOS the system
# Ruby (2.6) shadows Homebrew's on the PATH, so if we booted under an old
# Ruby we re-exec ourselves under a newer one before loading the gem.
if RUBY_VERSION < "3.0"
  newer = [
    "/opt/homebrew/opt/ruby/bin/ruby",
    "/usr/local/opt/ruby/bin/ruby",
  ].find { |p| File.executable?(p) }

  if newer
    exec(newer, __FILE__, *ARGV)
  else
    abort "scripts/mud.rb needs Ruby >= 3.0 (found #{RUBY_VERSION}); install with `brew install ruby`"
  end
end

require_relative "../../../mud_manager/lib/mud_manager"
require_relative "lib/mud_helpers"

SKILL_DIR = File.expand_path("..", __dir__)
MudHelpers.load_dotenv(File.join(SKILL_DIR, ".env"))

command = ARGV.join(" ").strip
if command.empty?
  warn %(usage: ruby scripts/mud.rb "<mud command>"   e.g. ruby scripts/mud.rb "look")
  exit 2
end

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

begin
  # `login`'s "Reconnecting" path leaves the just-completed status line
  # sitting in the buffer — drop it so the command we're about to send
  # starts from a clean slate.
  session.drain

  session.send_command(command)
  output = MudHelpers.strip_ansi(session.read_until_quiet(quiet, timeout: timeout))
  print output
  print "\n" unless output.end_with?("\n")
rescue MudManager::Session::Error => e
  warn "session error: #{e.message}"
  exit 1
ensure
  session.close
end
