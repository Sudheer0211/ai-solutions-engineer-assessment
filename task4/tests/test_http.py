"""T4-005 authenticated ASGI contract over real SQLite and accepted orchestration."""

import asyncio
import json
import secrets
from contextlib import asynccontextmanager

import pytest
from http_support import HTTPProvider, auth, http_stack, raw_asgi
from orchestration_support import ManualClock, until
from storage_support import database

from task4_limiter.app import create_app
from task4_limiter.models import BoundsUnavailable
from task4_limiter.providers import ProviderStatus
from task4_limiter.service import RoutingPolicy
from task4_limiter.settings import (
    ConfigurationError,
    HTTPSettings,
    TenantCredentials,
    load_settings,
)


def rows(state):
    with database(state[2].path) as db:
        return db.execute("SELECT count(*) FROM requests").fetchone()[0]


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("authorization", "")],
        [("authorization", "Basic invalid")],
        [("authorization", "Bearer invalid")],
        [("authorization", "Bearer " + "x" * 43)],
        [("authorization", "bearer  " + "x" * 43)],
        [("authorization", "Bearer\t" + "x" * 43)],
        [("authorization", "Bearer " + "x" * 43 + ",Bearer " + "x" * 43)],
        [("authorization", "Bearer " + "x" * 43), ("authorization", "Bearer " + "x" * 43)],
    ],
)
def test_authentication_rejection_zero_reservations_and_calls(state, headers):
    async def scenario():
        async with http_stack(state) as (_, client, _, primary, backup, _):
            response = await client.post("/generate", headers=headers, content=b"invalid JSON")
            assert response.status_code == 401
            assert response.json()["error"]["code"] == "invalid_credentials"
            assert response.headers["www-authenticate"] == 'Bearer realm="task4"'
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


def test_valid_duplicate_credentials_and_nonascii_headers_reject_without_reading_body(state):
    async def scenario():
        async with http_stack(state) as (app, _, keys, primary, backup, _):

            async def never_receive():
                raise AssertionError("Auth rejection must not read body")

            for values in ([b"Bearer " + keys[0], b"Bearer " + keys[0]], [b"Bearer \xff"]):
                messages = await raw_asgi(
                    app, [(b"authorization", v) for v in values], receive=never_receive
                )
                assert messages[0]["status"] == 401
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b'"text"',
        b"{}",
        b'{"prompt":1}',
        b'{"prompt":true}',
        b'{"prompt":null}',
        b'{"prompt":""}',
        b'{"prompt":"x","prompt":"y"}',
        b'{"prompt":"x","tenant_id":"spoof"}',
        b'{"prompt":"x","input_tokens":1}',
        b'{"prompt":"x","extra":1e99999}',
        b'{"prompt":NaN}',
        b'{"prompt":"\\ud800"}',
        b'{"prompt":"\xff"}',
        b'{"prompt":"' + b"x" * 16001 + b'"}',
    ],
)
def test_strict_input_rejection_never_admits_or_dispatches(state, body):
    async def scenario():
        async with http_stack(state) as (_, client, keys, primary, backup, _):
            response = await client.post(
                "/generate",
                headers={**auth(keys[0]), "content-type": "application/json"},
                content=body,
            )
            assert response.status_code == 400
            assert response.json()["error"]["message"] == "Invalid request"
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "headers,status",
    [
        ({"content-type": "text/plain"}, 415),
        ({"content-type": "application/json; charset=latin-1"}, 415),
        ({"content-type": "application/json", "content-encoding": "gzip"}, 415),
        ({"content-type": "application/json", "content-encoding": "identity"}, 415),
        ({"content-type": "application/json", "content-length": "999999"}, 413),
        ({"content-type": "application/json", "content-length": "-1"}, 400),
        ({"content-type": "application/json", "content-length": "1"}, 400),
    ],
)
def test_http_header_and_size_policy(state, headers, status):
    async def scenario():
        async with http_stack(state) as (_, client, keys, primary, backup, _):
            result = await client.post(
                "/generate", headers={**auth(keys[0]), **headers}, content=b'{"prompt":"safe"}'
            )
            assert result.status_code == status
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "extra",
    [
        [(b"content-type", b"application/json")],
        [(b"content-length", b"17"), (b"content-length", b"17")],
        [(b"transfer-encoding", b"chunked"), (b"content-length", b"17")],
        [(b"transfer-encoding", b"gzip")],
    ],
)
def test_duplicate_and_ambiguous_entity_headers(state, extra):
    async def scenario():
        async with http_stack(state) as (app, _, keys, primary, backup, _):
            headers = [
                (b"authorization", b"Bearer " + keys[0]),
                (b"content-type", b"application/json"),
                *extra,
            ]
            messages = await raw_asgi(app, headers, b'{"prompt":"safe"}')
            assert messages[0]["status"] in (400, 415)
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize("size,status", [(64, 200), (65, 413)])
def test_streamed_body_limit_at_exact_boundary(state, size, status):
    async def scenario():
        async with http_stack(state, limit=64) as (_, client, keys, primary, backup, _):
            data = b'{"prompt":"' + b"x" * (size - 13) + b'"}'
            assert len(data) == size

            async def stream():
                for start in range(0, len(data), 7):
                    yield data[start : start + 7]

            response = await client.post(
                "/generate",
                headers={**auth(keys[0]), "content-type": "application/json"},
                content=stream(),
            )
            assert response.status_code == status
            assert len(primary.calls) == int(status == 200) and not backup.calls
            assert rows(state) == int(status == 200)

    asyncio.run(scenario())


def test_body_deadline_is_controlled_and_has_zero_calls(state):
    async def scenario():
        async with http_stack(state, body_timeout=10) as (app, _, keys, primary, backup, _):

            async def stalled():
                await asyncio.Event().wait()

            messages = await raw_asgi(
                app,
                [(b"authorization", b"Bearer " + keys[0]), (b"content-type", b"application/json")],
                receive=stalled,
            )
            assert messages[0]["status"] == 408
            assert rows(state) == 0 and not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "mode,status,backup_count,charge",
    [
        ("success", 200, 0, 5),
        ("unknown", 200, 0, 20),
        ("429", 200, 1, 25),
        ("failure", 502, 0, 20),
        ("backup_failure", 502, 1, 40),
        ("missing_bounds", 503, 0, 0),
    ],
)
def test_routing_status_accounting_and_no_prompt_or_secret_leak(
    state, mode, status, backup_count, charge, caplog
):
    async def scenario():
        primary, backup = HTTPProvider(), HTTPProvider("backup")
        if mode in ("unknown", "429", "backup_failure"):
            primary.usage = None
        if mode in ("429", "backup_failure"):
            primary.status = ProviderStatus.RATE_LIMITED
        if mode == "failure":
            primary.error = RuntimeError("private-provider-credential")
        if mode == "backup_failure":
            backup.status = ProviderStatus.TRANSPORT_FAILURE
            backup.usage = None
        if mode == "missing_bounds":
            primary.prepare_error = BoundsUnavailable()
        async with http_stack(state, primary=primary, backup=backup) as (
            app,
            client,
            keys,
            _,
            _,
            _,
        ):
            prompt = "private-prompt-marker"
            response = await client.post(
                "/generate", headers=auth(keys[0]), json={"prompt": prompt}
            )
            assert response.status_code == status and len(backup.calls) == backup_count
            assert app.state.store.usage(keys[0]).total_tokens == charge
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["x-content-type-options"] == "nosniff"
            for value in (
                prompt,
                keys[0].decode(),
                "private-provider-credential",
                state[2].identity_secret.hex(),
                str(state[2].path),
            ):
                assert value not in response.text + caplog.text
            body = response.json()
            assert (body.get("request_id") or body["error"]["request_id"]) == response.headers[
                "x-request-id"
            ]

    asyncio.run(scenario())


@pytest.mark.parametrize("total,status", [(49999, 200), (50000, 200), (50001, 429)])
def test_combined_admission_boundaries_and_quota_rejection(state, total, status):
    async def scenario():
        primary = HTTPProvider(input_bound=25000, output_cap=0, usage=None)
        backup = HTTPProvider("backup", input_bound=total - 25000, output_cap=0, usage=None)
        async with http_stack(state, primary=primary, backup=backup) as (
            app,
            client,
            keys,
            _,
            _,
            _,
        ):
            response = await client.post(
                "/generate", headers=auth(keys[0]), json={"prompt": "safe"}
            )
            assert response.status_code == status
            assert len(primary.calls) == int(status == 200) and not backup.calls
            if status == 200:
                with database(state[2].path) as db:
                    assert (
                        db.execute("SELECT sum(bound_tokens) FROM attempts").fetchone()[0] == total
                    )
                before = len(primary.calls)
                denied = await client.post(
                    "/generate", headers=auth(keys[0]), json={"prompt": "safe"}
                )
                assert denied.status_code == 429 and len(primary.calls) == before
                assert denied.json()["error"]["code"] == "tenant_quota_exceeded"
            else:
                assert rows(state) == 0

    asyncio.run(scenario())


def test_http_concurrency_tenant_isolation_and_restart_persistence(state):
    async def scenario():
        keys = tuple(secrets.token_urlsafe(32).encode() for _ in range(2))
        primary = HTTPProvider(input_bound=5000, output_cap=0, usage=None)
        primary.gate = asyncio.Event()
        backup = HTTPProvider("backup", input_bound=5000, output_cap=0)
        async with http_stack(state, keys=keys, primary=primary, backup=backup) as (
            app,
            client,
            _,
            _,
            _,
            events,
        ):
            tasks = [
                asyncio.create_task(
                    client.post("/generate", headers=auth(keys[0]), json={"prompt": "safe"})
                )
                for _ in range(6)
            ]
            await until(lambda: len(primary.calls) == 5 and any(t.done() for t in tasks))
            assert app.state.store.usage(keys[0]).total_tokens == 50000
            other = asyncio.create_task(
                client.post(
                    "/generate",
                    headers={**auth(keys[1]), "x-tenant-id": "spoof"},
                    json={"prompt": "safe"},
                )
            )
            await until(lambda: len(primary.calls) == 6)
            primary.gate.set()
            results = await asyncio.gather(*tasks, other)
            assert sorted(r.status_code for r in results) == [200] * 6 + [429]
            assert app.state.store.usage(keys[0]).total_tokens == 25000
            assert app.state.store.usage(keys[1]).total_tokens == 5000
        assert events == ["open", "close"]
        async with http_stack(state, keys=keys) as (app, _, _, _, _, _):
            assert app.state.store.usage(keys[0]).total_tokens == 25000
            assert app.state.store.usage(keys[1]).total_tokens == 5000

    asyncio.run(scenario())


def test_http_primary_timeout_and_unconfirmed_cleanup(state):
    async def scenario():
        for resistant in (False, True):
            mono = ManualClock()
            primary = HTTPProvider()
            primary.gate = asyncio.Event()
            if resistant:
                primary.resistant = True
                primary.finish = asyncio.Event()
            async with http_stack(state, primary=primary, mono=mono) as (
                app,
                client,
                keys,
                _,
                backup,
                _,
            ):
                task = asyncio.create_task(
                    client.post("/generate", headers=auth(keys[0]), json={"prompt": "safe"})
                )
                await until(lambda p=primary: bool(p.calls))
                await mono.waiting(3000)
                mono.advance(3000)
                if resistant:
                    await mono.waiting(3500)
                    mono.advance(3500)
                response = await task
                assert response.status_code == (503 if resistant else 200)
                assert len(backup.calls) == int(not resistant)
                if resistant:
                    assert app.state.store.usage(keys[0]).reserved_tokens == 40
                    primary.finish.set()
                    await until(lambda: app.state.service.pending_cleanup == 0)
                else:
                    assert app.state.store.usage(keys[0]).total_tokens == 25

    asyncio.run(scenario())


@pytest.mark.parametrize("disconnect", [False, True])
def test_http_cancellation_preserves_dispatched_accounting(state, disconnect):
    async def scenario():
        primary = HTTPProvider()
        primary.gate = asyncio.Event()
        async with http_stack(state, primary=primary) as (app, _, keys, _, backup, _):
            sent = False
            gone = asyncio.Event()

            async def receive():
                nonlocal sent
                if not sent:
                    sent = True
                    return {
                        "type": "http.request",
                        "body": b'{"prompt":"safe"}',
                        "more_body": False,
                    }
                await gone.wait()
                return {"type": "http.disconnect"}

            task = asyncio.create_task(
                raw_asgi(
                    app,
                    [
                        (b"authorization", b"Bearer " + keys[0]),
                        (b"content-type", b"application/json"),
                    ],
                    receive=receive,
                )
            )
            await until(lambda p=primary: bool(p.calls))
            if disconnect:
                gone.set()
                assert (await task)[0]["status"] == 499
            else:
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            await app.state.service.drain()
            assert app.state.store.usage(keys[0]).total_tokens == 20
            assert not backup.calls and primary.prepared[0].closed.is_set()

    asyncio.run(scenario())


def test_database_failure_is_sanitized_and_unconfigured_provider_fails_closed(state):
    async def scenario():
        async with http_stack(state) as (app, client, keys, primary, backup, _):
            app.state.store.close()
            response = await client.post(
                "/generate", headers=auth(keys[0]), json={"prompt": "safe"}
            )
            assert response.status_code == 503 and not primary.calls and not backup.calls
        settings = HTTPSettings(state[2], TenantCredentials((keys[0],)), RoutingPolicy(1000, 10000))
        app = create_app(settings, accounting_clock=state[1])
        import httpx

        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app), base_url="http://test"
            ) as client:
                assert (
                    await client.post("/generate", headers=auth(keys[0]), json={"prompt": "safe"})
                ).status_code == 503
        assert rows(state) == 0

    asyncio.run(scenario())


def test_startup_and_shutdown_failure_are_generic_and_close_partial_store(state):
    async def scenario():
        key = secrets.token_urlsafe(32).encode()
        config = HTTPSettings(state[2], TenantCredentials((key,)), RoutingPolicy(1000, 10000))

        @asynccontextmanager
        async def broken():
            raise RuntimeError("private-provider-credential")
            yield

        app = create_app(config, provider_resources=broken, accounting_clock=state[1])
        with pytest.raises(ConfigurationError, match="^Invalid Task 4 configuration$"):
            async with app.router.lifespan_context(app):
                pass
        assert not app.state.accepting

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "path,method,status",
    [
        ("/generate", "GET", 405),
        ("/generate/", "POST", 404),
        ("/docs", "GET", 404),
        ("/openapi.json", "GET", 404),
    ],
)
def test_only_documented_route_is_enabled(state, path, method, status):
    async def scenario():
        async with http_stack(state) as (_, client, _, primary, backup, _):
            response = await client.request(method, path)
            assert response.status_code == status and rows(state) == 0
            assert not primary.calls and not backup.calls

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "field,value",
    [
        ("TASK4_TENANT_KEYS_JSON", "[]"),
        ("TASK4_TENANT_KEYS_JSON", '"not-array"'),
        ("TASK4_TENANT_KEYS_JSON", '["short"]'),
        ("TASK4_IDENTITY_SECRET_HEX", "invalid"),
        ("TASK4_IDENTITY_SECRET_HEX", "00"),
        ("TASK4_DATABASE_PATH", "relative.sqlite3"),
        ("TASK4_BACKUP_TIMEOUT_MS", "0"),
        ("TASK4_RESERVATION_MS", "10"),
        ("TASK4_MAX_BODY_BYTES", "0"),
        ("TASK4_BODY_TIMEOUT_MS", "0"),
    ],
)
def test_invalid_external_configuration_is_generic(state, field, value):
    key = secrets.token_urlsafe(32)
    env = {
        "TASK4_DATABASE_PATH": str(state[2].path),
        "TASK4_IDENTITY_SECRET_HEX": state[2].identity_secret.hex(),
        "TASK4_TENANT_KEYS_JSON": json.dumps([key]),
        "TASK4_BACKUP_TIMEOUT_MS": "1000",
        "TASK4_RESERVATION_MS": "10000",
    }
    assert load_settings(env).credentials.authenticate(["Bearer " + key]) == key.encode()
    env[field] = value
    with pytest.raises(ConfigurationError, match="^Invalid Task 4 configuration$"):
        load_settings(env)


def test_failed_attempt_close_quarantines_resources_instead_of_claiming_shutdown(state):
    async def scenario():
        key = secrets.token_urlsafe(32).encode()
        primary, backup, events = HTTPProvider(), HTTPProvider("backup"), []
        primary.close_error = True

        @asynccontextmanager
        async def resources():
            events.append("open")
            try:
                yield primary, backup
            finally:
                events.append("close")

        config = HTTPSettings(state[2], TenantCredentials((key,)), RoutingPolicy(1000, 10000))
        app = create_app(config, provider_resources=resources, accounting_clock=state[1])
        with pytest.raises(RuntimeError, match="^Task 4 shutdown incomplete$"):
            async with app.router.lifespan_context(app):
                messages = await raw_asgi(
                    app,
                    [(b"authorization", b"Bearer " + key), (b"content-type", b"application/json")],
                    b'{"prompt":"safe"}',
                )
                assert messages[0]["status"] == 503
        assert events == ["open"] and not app.state.accepting
        stack, store, _ = app.state.quarantined_resources
        assert store.usage(key).reserved_tokens == 40
        # Fixture-only cleanup: handles have no real resources; owner acknowledges
        # the unclean close rather than resetting the service's quarantine state.
        primary.close_error = False
        await primary.prepared[0].aclose()
        await stack.aclose()
        store.close()
        assert events == ["open", "close"]

    asyncio.run(scenario())


def test_startup_cancel_discovers_initialized_worker_before_closing(state, monkeypatch):
    async def scenario():
        import threading

        import task4_limiter.app as module
        from task4_limiter.storage import SQLiteStore, StorageError

        entered, release, created = asyncio.Event(), threading.Event(), []
        loop = asyncio.get_running_loop()

        def constructor(*args, **kw):
            store = SQLiteStore(*args, **kw)
            created.append(store)
            loop.call_soon_threadsafe(entered.set)
            assert release.wait(10)
            return store

        monkeypatch.setattr(module, "SQLiteStore", constructor)
        config = HTTPSettings(
            state[2],
            TenantCredentials((secrets.token_urlsafe(32).encode(),)),
            RoutingPolicy(1000, 10000),
        )
        app = create_app(config, accounting_clock=state[1])
        context = app.router.lifespan_context(app)
        task = asyncio.create_task(context.__aenter__())
        await entered.wait()
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not app.state.accepting and len(created) == 1
        with pytest.raises(StorageError):
            created[0].usage(b"fixture")

    asyncio.run(scenario())


def test_shutdown_cancellation_drains_owned_provider_context(state):
    async def scenario():
        key = secrets.token_urlsafe(32).encode()
        closing, release, closed = asyncio.Event(), asyncio.Event(), asyncio.Event()

        @asynccontextmanager
        async def resources():
            try:
                yield HTTPProvider(), HTTPProvider("backup")
            finally:
                closing.set()
                await release.wait()
                closed.set()

        config = HTTPSettings(state[2], TenantCredentials((key,)), RoutingPolicy(1000, 10000))
        app = create_app(config, provider_resources=resources, accounting_clock=state[1])
        context = app.router.lifespan_context(app)
        await context.__aenter__()
        task = asyncio.create_task(context.__aexit__(None, None, None))
        await closing.wait()
        task.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed.is_set() and not app.state.accepting
        assert app.state.shutdown_task.done()

    asyncio.run(scenario())
