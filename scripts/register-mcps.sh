#!/usr/bin/env bash
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  echo "Claude Code CLI is not installed or not on PATH." >&2
  echo "Install/open Claude Code on your machine, then rerun this script." >&2
  exit 1
fi

claude mcp add --transport http hubspot https://mcp.hubspot.com/anthropic
claude mcp add --transport http meta-ads https://mcp.facebook.com/ads

echo "MCP registrations added. Open Claude Code and use /mcp to authenticate both servers."
