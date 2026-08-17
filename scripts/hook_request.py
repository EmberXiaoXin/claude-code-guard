#!/usr/bin/env python3
"""Claude hook: full egress check. Uses gate CHECK when available, else guard directly."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ccg_detect import load_state


def block(reason: str) -> int:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


def check_via_gate(port: int) -> str | None:
    try:
        sock = socket.create_connection(("127.0.0.1", port), timeout=32)
        sock.sendall(b"CHECK\n")
        data = sock.recv(1024).decode("utf-8", "replace")
        sock.close()
    except OSError:
        return None
    if data.strip() == "OK":
        return "OK"
    if data.startswith("BLOCK"):
        return data.split("\t", 1)[-1].strip() or "blocked"
    return "invalid"


def main() -> int:
    state = load_state()
    control = int(state.get("control_port") or 7900) if state else 7900
    via_gate = check_via_gate(control)
    if via_gate == "OK":
        return 0
    if via_gate and via_gate != "invalid":
        return block(via_gate)

    guard = HERE / "ccg_guard.py"
    result = subprocess.run(
        [sys.executable, str(guard), "--check"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=32,
        check=False,
    )
    if result.returncode == 0:
        return 0
    reason = (result.stdout or "full network validation failed").strip().splitlines()
    return block(reason[0] if reason else "full network validation failed")


if __name__ == "__main__":
    raise SystemExit(main())
