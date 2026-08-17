#!/usr/bin/env python3
"""Local HTTP proxy gate. Ports come from detect/install state, not hardcoded vendors."""

from __future__ import annotations

import logging
import select
import signal
import socket
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional, Tuple

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from ccg_detect import load_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

stop_event = threading.Event()
safe_event = threading.Event()
validation_lock = threading.Lock()
full_validation_lock = threading.Lock()
active_lock = threading.Lock()
active_pairs: set[Tuple[socket.socket, socket.socket]] = set()
listener: Optional[socket.socket] = None
control_listener: Optional[socket.socket] = None
GUARD = HERE / "ccg_guard.py"


def run_guard(mode: str, timeout: float) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, str(GUARD), mode],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, type(error).__name__
    reason = (result.stdout or "guard rejected connection").strip().splitlines()
    return result.returncode == 0, (reason[0] if reason else "guard rejected connection")


def close_socket(sock: socket.socket) -> None:
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


def close_all_active() -> None:
    with active_lock:
        pairs = list(active_pairs)
    for client, upstream in pairs:
        close_socket(client)
        close_socket(upstream)


def safety_monitor() -> None:
    last_safe: Optional[bool] = None
    while not stop_event.wait(1.0):
        ok, reason = run_guard("--fast", 6)
        if ok:
            safe_event.set()
            if last_safe is False:
                logging.info("network guard recovered")
        else:
            safe_event.clear()
            close_all_active()
            if last_safe is not False:
                logging.warning("network guard closed all tunnels: %s", reason)
        last_safe = ok


def relay(client: socket.socket, upstream_addr: Tuple[str, int]) -> None:
    upstream: Optional[socket.socket] = None
    pair = None
    try:
        with validation_lock:
            ok, reason = run_guard("--fast", 6)
        if not ok or not safe_event.is_set():
            logging.warning("connection denied by guard: %s", reason)
            return
        upstream = socket.create_connection(upstream_addr, timeout=3.0)
        client.setblocking(True)
        upstream.setblocking(True)
        pair = (client, upstream)
        with active_lock:
            active_pairs.add(pair)
        while not stop_event.is_set() and safe_event.is_set():
            readable, _, exceptional = select.select([client, upstream], [], [client, upstream], 1.0)
            if exceptional:
                break
            for source in readable:
                try:
                    chunk = source.recv(65536)
                except OSError:
                    chunk = b""
                if not chunk:
                    return
                destination = upstream if source is client else client
                try:
                    destination.sendall(chunk)
                except OSError:
                    return
    finally:
        if pair is not None:
            with active_lock:
                active_pairs.discard(pair)
        close_socket(client)
        if upstream is not None:
            close_socket(upstream)


def handle_control(client: socket.socket) -> None:
    try:
        client.settimeout(34)
        if client.recv(64).strip() != b"CHECK":
            client.sendall(b"BLOCK\tinvalid control request\n")
            return
        with full_validation_lock:
            ok, reason = run_guard("--check", 32)
        if ok:
            client.sendall(b"OK\n")
        else:
            client.sendall(("BLOCK\t" + reason.replace("\t", " ").replace("\n", " ")[:500] + "\n").encode("utf-8"))
    except (OSError, UnicodeError):
        pass
    finally:
        close_socket(client)


def serve(bind: Tuple[str, int], handler) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(bind)
    sock.listen(64)
    sock.settimeout(1.0)
    return sock


def main() -> int:
    global listener, control_listener
    state = load_state()
    if not state:
        print("gate: missing ~/.claude-guard/state.json — run detect then install", file=sys.stderr)
        return 78
    gate_port = int(state["gate_port"])
    control_port = int(state["control_port"])
    upstream_port = int(state.get("upstream_port") or state.get("bind_port"))
    upstream_addr = ("127.0.0.1", upstream_port)

    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())

    ok, reason = run_guard("--fast", 6)
    if ok:
        safe_event.set()
    else:
        logging.warning("gate starts closed: %s", reason)

    threading.Thread(target=safety_monitor, daemon=True).start()
    control_listener = serve(("127.0.0.1", control_port), None)
    listener = serve(("127.0.0.1", gate_port), None)
    logging.info("gate %s -> %s control %s", gate_port, upstream_addr, control_port)

    def accept_loop(server: socket.socket, target) -> None:
        while not stop_event.is_set():
            try:
                client, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=target, args=(client,), daemon=True).start()

    threading.Thread(target=accept_loop, args=(control_listener, handle_control), daemon=True).start()
    while not stop_event.is_set():
        try:
            client, _ = listener.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        threading.Thread(target=relay, args=(client, upstream_addr), daemon=True).start()

    close_all_active()
    if listener:
        close_socket(listener)
    if control_listener:
        close_socket(control_listener)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
