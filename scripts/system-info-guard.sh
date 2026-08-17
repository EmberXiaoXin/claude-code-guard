#!/bin/zsh
DIR="$(cd "$(dirname "$0")" && pwd)"
[[ -f "${HOME}/.claude/hooks/hook_sysinfo.py" ]] && DIR="${HOME}/.claude/hooks"
exec python3 "${DIR}/hook_sysinfo.py"
