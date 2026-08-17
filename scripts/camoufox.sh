#!/bin/zsh
set -u
GUARD_DIR="${HOME}/.claude-guard"
PYTHON="${CLAUDE_GUARD_PYTHON:-python3}"
"$PYTHON" "${GUARD_DIR}/ccg_guard.py" --status >/dev/null || exit 78
UPSTREAM="$("$PYTHON" -c 'import json; from pathlib import Path; s=json.loads((Path.home()/".claude-guard"/"state.json").read_text()); print(s.get("upstream_port") or s.get("bind_port"))')"
LAUNCHER="/Applications/Camoufox Persistent.app/Contents/Resources/launch_camoufox.py"
if [[ -f "$LAUNCHER" ]]; then
  PYBIN="${HOME}/.local/share/uv/tools/camoufox/bin/python"
  [[ -x "$PYBIN" ]] || PYBIN="$PYTHON"
  nohup "$PYBIN" "$LAUNCHER" --strict-network "$@" >/dev/null 2>&1 &
  exit 0
fi
print -u2 -- "未安装 Camoufox Persistent。不要改用系统浏览器。"
print -u2 -- "请用 Camoufox 走 http://127.0.0.1:${UPSTREAM} 打开登录页，并关闭 WebRTC。"
exit 78
