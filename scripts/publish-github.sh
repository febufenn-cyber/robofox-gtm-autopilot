#!/usr/bin/env bash
set -euo pipefail

OWNER="${GITHUB_OWNER:-febufenn-cyber}"
REPO="${GITHUB_REPO:-robofox-gtm-autopilot}"
VISIBILITY="${GITHUB_VISIBILITY:-private}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI (gh) is not installed or not on PATH." >&2
  echo "Install gh, authenticate with 'gh auth login', then rerun this script." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated." >&2
  echo "Run 'gh auth login', then rerun this script." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is not clean. Commit or stash changes before publishing." >&2
  exit 1
fi

if git remote get-url origin >/dev/null 2>&1; then
  echo "An origin remote already exists: $(git remote get-url origin)" >&2
  echo "Refusing to replace it automatically." >&2
  exit 1
fi

gh repo create "${OWNER}/${REPO}" \
  "--${VISIBILITY}" \
  --source=. \
  --remote=origin \
  --push \
  --description "Internal founder-led GTM channel selection and kill-review skills for Robofox products"

echo "Published https://github.com/${OWNER}/${REPO}"
