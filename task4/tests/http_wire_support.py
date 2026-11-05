"""T4-005 real child processes, dynamic bound ports and bounded readiness/cleanup."""

import hmac
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx


def wait_until(predicate, timeout=12):
    deadline = time.monotonic() + timeout
    event = threading.Event()
    while time.monotonic() < deadline:
        if predicate():
            return
        event.wait(0.01)  # Bounded readiness/state polling, never elapsed-time assertions.
    raise AssertionError("Wire readiness/state deadline exceeded")


class StartupFailure(RuntimeError):
    pass


class WireLab:
    def __init__(self, directory):
        self.directory = directory
        self.children, self.servers, self.outcomes = [], {}, []
        self.credentials = []
        self.rejections = []

    def spawn(self, role, env, directory, expected=0):
        nonce = secrets.token_hex(4)
        ready = directory / f"{role}-{nonce}-ready.json"
        lifecycle = directory / f"{role}-{nonce}-lifecycle.json"
        stop = directory / f"{role}-{nonce}-stop"
        stdout, stderr = directory / f"{role}-{nonce}.out", directory / f"{role}-{nonce}.err"
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).with_name("http_wire_child.py")), role],
                stdin=subprocess.PIPE,
                stdout=out,
                stderr=err,
                env={
                    **env,
                    "WIRE_READY": str(ready),
                    "WIRE_LIFECYCLE": str(lifecycle),
                    "WIRE_STOP": str(stop),
                },
                cwd=Path(__file__).parents[1],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        child = {
            "process": process,
            "expected": expected,
            "role": role,
            "lifecycle": lifecycle,
            "stdout": stdout,
            "stderr": stderr,
            "stop": stop,
        }
        self.children.append(child)

        def check():
            if process.poll() is not None:
                raise StartupFailure("Wire child startup failed")
            if not ready.exists():
                return False
            try:
                port = json.loads(ready.read_text())["port"]
            except (ValueError, OSError):
                return False
            try:
                with httpx.Client(trust_env=False, timeout=0.25) as client:
                    status = client.get(f"http://127.0.0.1:{port}/").status_code
                    if status not in (200, 404):
                        return False
                child["port"] = port
                return True
            except httpx.TransportError:
                return False

        wait_until(check)
        return child

    def stop(self, child):
        if child.get("reaped"):
            return
        process = child["process"]
        forced = False
        try:
            if process.poll() is None:
                try:
                    if child["role"] == "proxy":
                        child["stop"].touch()
                    else:
                        process.stdin.write(b"stop\n")
                        process.stdin.flush()
                except (OSError, ValueError):
                    pass
                try:
                    process.wait(12)
                except subprocess.TimeoutExpired:
                    forced = True
                    process.terminate()
                    try:
                        process.wait(5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(5)
        finally:
            process.stdin.close()
            child["reaped"] = True
            outcome = {
                "role": child["role"],
                "exitcode": process.returncode,
                "forced": forced,
                "expected": child["expected"],
            }
            self.outcomes.append(outcome)
        assert not forced and process.returncode == child["expected"], outcome
        if child["role"] == "proxy" and child["expected"] == 0:
            assert json.loads(child["lifecycle"].read_text())["provider_context_closed"]

    def get(self, mode="success"):
        if mode not in self.servers:
            directory = self.directory / mode
            directory.mkdir()
            keys = tuple(secrets.token_urlsafe(32).encode() for _ in range(128))
            secret = secrets.token_bytes(32)
            self.credentials.extend(k.decode() for k in keys)
            self.credentials.append(secret.hex())
            db, journal = directory / "usage.sqlite3", directory / "journal.sqlite3"
            env = {
                **os.environ,
                "WIRE_MODE": mode,
                "WIRE_JOURNAL": str(journal),
                "TASK4_DATABASE_PATH": str(db),
                "TASK4_IDENTITY_SECRET_HEX": secret.hex(),
                "TASK4_TENANT_KEYS_JSON": json.dumps([k.decode() for k in keys]),
                "TASK4_BACKUP_TIMEOUT_MS": "1000",
                "TASK4_RESERVATION_MS": "10000",
                "TASK4_MAX_BODY_BYTES": "1024",
                "TASK4_BODY_TIMEOUT_MS": "1000",
            }
            upstream = self.spawn(
                "upstream", {k: v for k, v in env.items() if not k.startswith("TASK4_")}, directory
            )
            env["WIRE_UPSTREAM"] = f"http://127.0.0.1:{upstream['port']}/attempt"
            proxy = self.spawn("proxy", env, directory)
            self.servers[mode] = WireServer(self, proxy, upstream, env, directory, keys, secret)
        return self.servers[mode]

    def close(self):
        errors = []
        try:
            for child in reversed(self.children):
                try:
                    self.stop(child)
                except AssertionError as exc:
                    errors.append(str(exc))  # Continue reaping ALL children after a failure.
            for child in self.children:
                logs = child["stdout"].read_text(errors="replace") + child["stderr"].read_text(
                    errors="replace"
                )
                assert not any(value in logs for value in self.credentials)
                assert "wire-private-prompt" not in logs
            assert not errors, errors
        finally:
            summary = {
                "children": len(self.children),
                "reaped": len(self.outcomes),
                "forced": sum(o["forced"] for o in self.outcomes),
                "outcomes": self.outcomes,
                "local_rejections": self.rejections,
                "modes": {mode: server.snapshot() for mode, server in self.servers.items()},
            }
            root = Path(__file__).parents[1] / ".cache"
            root.mkdir(exist_ok=True)
            (root / "http_wire_summary.json").write_text(json.dumps(summary, indent=2))


class WireServer:
    def __init__(self, lab, proxy, upstream, env, directory, keys, secret):
        self.lab, self.proxy, self.upstream, self.env = lab, proxy, upstream, env
        self.directory, self.keys, self.secret = directory, keys, secret
        self.index = 0

    @property
    def url(self):
        return f"http://127.0.0.1:{self.proxy['port']}"

    def key(self):
        result = self.keys[self.index]
        self.index += 1
        return result

    def calls(self):
        with sqlite3.connect(self.env["WIRE_JOURNAL"], timeout=5) as db:
            return db.execute("SELECT ordinal,auth FROM events WHERE phase='start'").fetchall()

    def snapshot(self):
        path = Path(self.env["TASK4_DATABASE_PATH"])
        if not path.exists():
            path = path.with_suffix(".offline")
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5) as db:
            requests = db.execute("SELECT phase,count(*) FROM requests GROUP BY phase").fetchall()
            charge, held = db.execute(
                "SELECT coalesce(sum(charged_tokens),0),"
                "coalesce(sum(CASE WHEN state IN ('reserved','started') THEN bound_tokens "
                "ELSE 0 END),0) FROM attempts"
            ).fetchone()
        calls = self.calls()
        return {
            "primary_calls": sum(n == 1 for n, _ in calls),
            "backup_calls": sum(n == 2 for n, _ in calls),
            "phases": dict(requests),
            "charged_tokens": charge,
            "held_tokens": held,
            "credential_headers_forwarded": sum(flag for _, flag in calls),
        }

    def request_count(self):
        with sqlite3.connect(self.env["TASK4_DATABASE_PATH"], timeout=5) as db:
            return db.execute("SELECT count(*) FROM requests").fetchone()[0]

    def rejected(self, before_calls, before_requests, category):
        result = {
            "category": category,
            "provider_delta": len(self.calls()) - before_calls,
            "reservation_delta": self.request_count() - before_requests,
        }
        assert result["provider_delta"] == result["reservation_delta"] == 0
        self.lab.rejections.append(result)

    def rows(self, key):
        tenant = hmac.digest(self.secret, b"task4-tenant-v1\0" + key, "sha256").hex()
        with sqlite3.connect(self.env["TASK4_DATABASE_PATH"], timeout=5) as db:
            return db.execute(
                "SELECT r.phase,a.ordinal,a.state,a.charged_tokens,a.bound_tokens,"
                "a.source FROM requests r JOIN attempts a USING(tenant,request_id) "
                "WHERE tenant=? ORDER BY a.ordinal",
                (tenant,),
            ).fetchall()

    def release(self):
        with httpx.Client(trust_env=False, timeout=2) as client:
            client.get(f"http://127.0.0.1:{self.upstream['port']}/release").raise_for_status()

    def restart(self):
        self.lab.stop(self.proxy)
        self.proxy = self.lab.spawn("proxy", self.env, self.directory)
