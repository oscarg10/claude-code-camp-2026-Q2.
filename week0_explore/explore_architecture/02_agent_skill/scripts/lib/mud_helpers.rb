# frozen_string_literal: true

# Shared helpers for scripts/mud.rb and scripts/fight.rb. Kept here instead
# of duplicated in both, since the two scripts drifting apart (e.g. one
# getting a login-retry fix the other doesn't) is exactly the kind of bug
# that's already bitten this project once.
module MudHelpers
  # tbaMUD sends terminal color codes (e.g. "\e[0;33m") that are meaningless
  # noise once printed outside a real terminal / read by an agent.
  ANSI_RE = /\e\[[0-9;]*[A-Za-z]/.freeze

  module_function

  def strip_ansi(text)
    text.gsub(ANSI_RE, "")
  end

  # Minimal .env loader — no gem dependency. Handles `KEY=value` and #
  # comments.
  def load_dotenv(path)
    return unless File.file?(path)

    File.foreach(path) do |line|
      line = line.strip
      next if line.empty? || line.start_with?("#")

      key, _, val = line.partition("=")
      key = key.strip
      next if key.empty?

      val = val.strip.gsub(/\A["']|["']\z/, "")
      ENV[key] ||= val
    end
  end

  # Opens a session and logs in, retrying the whole connect+login on a
  # timeout — tbaMUD's client-detection negotiation occasionally races the
  # login handshake. Raises MudManager::Session::Error subclasses on a
  # non-recoverable failure; the caller is expected to warn+exit on those.
  def connect(host:, port:, timeout:, username:, password:, retries:)
    attempt = 0
    session = nil
    begin
      attempt += 1
      session = MudManager::Session.new(host: host, port: port, timeout: timeout)
      session.open
      session.login(username, password)
      session
    rescue MudManager::Session::Timeout
      session&.close
      retry if attempt < retries
      raise
    end
  end
end
