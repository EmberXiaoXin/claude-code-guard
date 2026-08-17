#!/bin/zsh
exec python3 "$(cd "$(dirname "$0")" && pwd)/ccg_identity.py" scan "$@"
