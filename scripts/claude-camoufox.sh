#!/bin/zsh

# Open Claude OAuth / login URLs in Camoufox on the pinned 7898 listener.

set -u

readonly GUARD="${HOME}/.claude/hooks/network-killswitch.sh"
readonly PERSISTENT_LAUNCHER="/Applications/Camoufox Persistent.app/Contents/Resources/launch_camoufox.py"

[[ -x "$GUARD" ]] || {
  print -u2 -- "Claude 浏览器保护：网络保护脚本不可用，已拒绝打开。"
  exit 78
}

"$GUARD" --status >/dev/null || exit 78

if [[ -f "$PERSISTENT_LAUNCHER" ]]; then
  python_bin=""
  if [[ -x "${HOME}/.local/share/uv/tools/camoufox/bin/python" ]]; then
    python_bin="${HOME}/.local/share/uv/tools/camoufox/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    python_bin="$(command -v python3)"
  else
    print -u2 -- "Claude 浏览器保护：找不到 Camoufox 使用的 Python。"
    exit 78
  fi
  nohup "$python_bin" "$PERSISTENT_LAUNCHER" --strict-network "$@" \
    >/dev/null 2>&1 &
  exit 0
fi

print -u2 -- "Claude 浏览器保护：未安装 Camoufox Persistent。不要改用系统 Chrome/Safari 登录。"
print -u2 -- "请按 references/fingerprint.md 用 Camoufox 走 http://127.0.0.1:7898 打开登录页。"
exit 78
