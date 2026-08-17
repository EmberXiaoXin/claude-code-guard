#!/usr/bin/env python3
"""Scan / purge leftover Claude Code identity on macOS and Windows. Never print secrets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ccg_detect import claude_home, home, os_name


KEYCHAIN_SERVICE = "Claude Code-credentials"
IDENTITY_KEYS = (
    "machineID",
    "userID",
    "oauthAccount",
    "firstStartTime",
    "claudeCodeFirstTokenDate",
    "groveConfigCache",
    "passesEligibilityCache",
    "cachedUsageUtilization",
    "cachedGrowthBookFeatures",
    "cachedGrowthBookFeaturesAt",
    "cachedExperimentFeatures",
    "cachedExperimentData",
    "cachedExtraUsageDisabledReason",
    "orgModelDefaultCache",
    "modelAccessCache",
)


def claude_json() -> Path:
    return home() / ".claude.json"


def camoufox_profile_roots() -> list[Path]:
    h = home()
    return [
        h / "Library/Application Support/Camoufox Persistent/profiles",
        h / "AppData/Roaming/Camoufox Persistent/profiles",
        h / "AppData/Local/Camoufox Persistent/profiles",
        h / "AppData/Roaming/camoufox/profiles",
    ]


def backup_root() -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if os_name() == "windows":
        base = home() / "AppData/Roaming/Claude Network Guard Backups"
    else:
        base = home() / "Library/Application Support/Claude Network Guard Backups"
    path = base / f"identity-{stamp}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def mac_keychain_present() -> bool:
    try:
        subprocess.run(
            ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def mac_keychain_delete() -> bool:
    try:
        subprocess.run(
            ["security", "delete-generic-password", "-s", KEYCHAIN_SERVICE],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


def windows_cred_targets() -> list[str]:
    try:
        raw = subprocess.check_output(["cmdkey", "/list"], text=True, errors="ignore")
    except (OSError, subprocess.CalledProcessError):
        return []
    hits: list[str] = []
    current = None
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("target:"):
            current = stripped.split(":", 1)[1].strip()
        if current and "claude" in (stripped + current).lower():
            if current not in hits:
                hits.append(current)
    return hits


def windows_cred_delete(target: str) -> None:
    subprocess.run(["cmdkey", "/delete", target], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def json_identity_flags(path: Path) -> list[tuple[str, bool]]:
    if not path.is_file():
        return [("~/.claude.json", False)]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [("~/.claude.json (unreadable)", True)]
    flags = []
    for key in ("machineID", "userID", "oauthAccount", "firstStartTime", "groveConfigCache", "passesEligibilityCache", "cachedUsageUtilization"):
        value = data.get(key)
        flags.append((f"~/.claude.json:{key}", value not in (None, "", {}, [])))
    return flags


def scan() -> list[tuple[str, bool]]:
    items: list[tuple[str, bool]] = []
    if os_name() == "darwin":
        items.append((f"keychain:{KEYCHAIN_SERVICE} (oauth access+refresh token chain)", mac_keychain_present()))
    elif os_name() == "windows":
        targets = windows_cred_targets()
        items.append((f"credential-manager:{KEYCHAIN_SERVICE}", bool(targets)))
        for target in targets:
            items.append((f"credential-manager-target:{target}", True))
    items.extend(json_identity_flags(claude_json()))
    cdir = claude_home()
    items.append((str(cdir / "stats-cache.json"), (cdir / "stats-cache.json").is_file()))
    tele = cdir / "telemetry"
    items.append((str(tele) + "/", tele.is_dir() and any(tele.rglob("*"))))
    senv = cdir / "session-env"
    items.append((str(senv) + "/", senv.is_dir() and any(senv.iterdir())))
    cookie_count = 0
    for root in camoufox_profile_roots():
        if root.is_dir():
            cookie_count += len(list(root.rglob("cookies.sqlite")))
    items.append((f"camoufox cookies.sqlite ({cookie_count})", cookie_count > 0))
    return items


def claude_running() -> bool:
    needle = "claude"
    try:
        if os_name() == "windows":
            raw = subprocess.check_output(["tasklist"], text=True, errors="ignore")
            return "claude" in raw.lower() or "camoufox" in raw.lower()
        raw = subprocess.check_output(["ps", "-axo", "comm="], text=True, errors="ignore")
        return any("claude" in line.lower() or "camoufox" in line.lower() for line in raw.splitlines())
    except (OSError, subprocess.CalledProcessError):
        return False


def strip_claude_json(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in IDENTITY_KEYS:
        data.pop(key, None)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def purge(*, yes: bool, purge_browser: bool) -> int:
    if not yes:
        print("拒绝：必须带 --yes。请先 scan，并确认客户要换号或这台曾被封。", file=sys.stderr)
        return 64
    if claude_running():
        print("拒绝：Claude 或 Camoufox 仍在运行。先全部退出再清。", file=sys.stderr)
        return 75
    backup = backup_root()
    cj = claude_json()
    if cj.is_file():
        shutil.copy2(cj, backup / "claude.json")
        strip_claude_json(cj)
        print("已从 ~/.claude.json 去掉设备/账号身份字段")
    if os_name() == "darwin" and mac_keychain_present():
        (backup / "keychain-claude-code-credentials.flag").write_text("present\n", encoding="utf-8")
        mac_keychain_delete()
        print(f"已删除钥匙串 {KEYCHAIN_SERVICE}")
    if os_name() == "windows":
        for target in windows_cred_targets():
            windows_cred_delete(target)
            print(f"已删除 Windows 凭据 {target}")
    cdir = claude_home()
    if (cdir / "stats-cache.json").is_file():
        shutil.move(str(cdir / "stats-cache.json"), backup / "stats-cache.json")
    if (cdir / "telemetry").is_dir():
        shutil.move(str(cdir / "telemetry"), backup / "telemetry")
        (cdir / "telemetry").mkdir(exist_ok=True)
    if (cdir / "session-env").is_dir():
        shutil.move(str(cdir / "session-env"), backup / "session-env")
        (cdir / "session-env").mkdir(exist_ok=True)
    if purge_browser:
        for root in camoufox_profile_roots():
            if root.is_dir():
                dest = backup / root.name
                if dest.exists():
                    dest = backup / f"{root.name}-{root.parent.name}"
                shutil.move(str(root), dest)
                root.mkdir(parents=True, exist_ok=True)
                print(f"已隔离 {root}")
    print(f"备份目录：{backup}")
    print("hooks 与 settings.json 未动。清完后先装防护，再用指纹浏览器做第一次登录。")
    return 0


def print_scan() -> int:
    items = scan()
    found = False
    for label, present in items:
        print(f"{'PRESENT' if present else 'absent'}\t{label}")
        found = found or present
    if found:
        print("旧身份未清空。换号或这台机器曾被封时，先退出 Claude / Camoufox，再运行 ccg_identity.py purge --yes", file=sys.stderr)
        return 2
    print("未发现 Claude Code 软件身份残留。")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "scan"
    if cmd == "scan":
        return print_scan()
    if cmd == "purge":
        yes = "--yes" in sys.argv
        browser = "--purge-browser" in sys.argv
        return purge(yes=yes, purge_browser=browser)
    print("Usage: ccg_identity.py scan|purge [--yes] [--purge-browser]", file=sys.stderr)
    return 64


if __name__ == "__main__":
    raise SystemExit(main())
