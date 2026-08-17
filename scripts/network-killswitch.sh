#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "${HOME}/.claude-guard/ccg_guard.py" ]]; then
  DIR="${HOME}/.claude-guard"
fi
exec python3 "${DIR}/ccg_guard.py" "$@"
