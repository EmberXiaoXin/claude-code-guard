#!/usr/bin/env python3
"""Block tool calls that enumerate host identity. Works on macOS and Windows."""

from __future__ import annotations

import json
import re
import sys

ENUM = re.compile(
    r"(^|[^a-z0-9_.-])("
    r"system_profiler|ioreg|sysctl|scutil|networksetup|ifconfig|ipconfig|route|arp|netstat|"
    r"uname|sw_vers|hostname|hostinfo|whoami|dscl|security|diskutil|launchctl|"
    r"getmac|get-computerinfo|get-ciminstance|get-wmiobject|systeminfo|wmic"
    r")([^a-z0-9_.-]|$)",
    re.I,
)
SENSITIVE = re.compile(
    r"(systemversion\.plist|systemconfiguration|library/keychains|"
    r"appdata\\roaming\\microsoft\\credentials|appdata\\local\\microsoft\\credentials|"
    r"\\windows\\system32\\config)",
    re.I,
)


def deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return deny("Claude 系统信息保护：Hook 输入无效，已拦截。")
    tool = str(data.get("tool_name") or "")
    inp = data.get("tool_input") or {}
    blob = "\n".join(
        str(inp.get(key) or "")
        for key in ("file_path", "path", "notebook_path", "pattern", "command")
    )
    if SENSITIVE.search(blob):
        return deny(f"Claude 系统信息保护：已拦截 {tool} 对敏感系统文件的访问。")
    if tool in {"Bash", "PowerShell"} and ENUM.search(blob):
        return deny(f"Claude 系统信息保护：已拦截 {tool} 对系统枚举命令的访问。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
