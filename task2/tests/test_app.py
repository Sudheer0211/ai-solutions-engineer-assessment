"""T2-004/H1-H8: real ASGI HTTP ingress, accepted guards and mocked HTTPX egress."""

import asyncio
import gzip
import json
import secrets
from contextlib import asynccontextmanager

import httpx
import pytest
from asgi_lifespan import LifespanManager

from task2_proxy.app import create_app
from task2_proxy.settings import ConfigurationError
from task2_proxy.upstream import UpstreamConfigurationError, UpstreamSettings

pytestmark = pytest.mark.task2
URL = "https://mcp.example.test/rpc"


def rpc_body(*, name="read", request_id=1, method="tools/call", arguments=None):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": {"name": name, "arguments": arguments or {}},
        }
    ).encode()


def headers(credentials, role="viewer"):
    return {
        "authorization": f"Bearer {getattr(credentials, role)}",
        "content-type": "application/json",
    }


def echo(request):
    value = json.loads(request.content)
    result = (
        {
            "tools": [
                {"name": "admin_reset", "inputSchema": {"type": "object"}},
                {"name": "read", "inputSchema": {"type": "object"}},
            ]
        }
        if value["method"] == "tools/list"
        else {"echo": value.get("params", {}).get("arguments", {})}
    )
    return httpx.Response(200, json={"jsonrpc": "2.0", "id": value["id"], "result": result})


class RecordingTransport(httpx.MockTransport):
    def __init__(self, handler=echo):
        self.requests = []
        self.close_count = 0

        def record(request):
            self.requests.append(request)
            return handler(request)

        super().__init__(record)

    async def aclose(self):
        self.close_count += 1
        await super().aclose()


@asynccontextmanager
async def service(credentials, *, handler=echo, max_bytes=4096, body_timeout=1.0, token=None):
    recorder = RecordingTransport(handler)
    app = create_app(
        credentials.settings,
        UpstreamSettings(URL, token, max_request_bytes=max_bytes),
        upstream_transport=recorder,
        body_timeout=body_timeout,
    )
    async with LifespanManager(app) as manager:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=manager.app), base_url="http://proxy.test"
        ) as client:
            yield client, recorder, app
    assert recorder.close_count == 1


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "empty",
        "scheme",
        "bare",
        "invalid",
        "newline",
        "duplicate",
        "duplicate_same",
        "comma",
        "cookie_query",
    ],
)
def test_bad_bearer_credentials_are_rejected_without_upstream(credentials, kind):
    auth = {
        "missing": [],
        "empty": [("authorization", "")],
        "scheme": [("authorization", "Basic opaque")],
        "bare": [("authorization", "Bearer")],
        "invalid": [("authorization", "Bearer invalid")],
        "newline": [("authorization", "Bearer x\r\nRole: admin")],
        "duplicate": [
            ("authorization", f"Bearer {credentials.admin}"),
            ("authorization", f"Bearer {credentials.viewer}"),
        ],
        "duplicate_same": [("authorization", f"Bearer {credentials.admin}")] * 2,
        "comma": [("authorization", f"Bearer {credentials.admin}, Bearer {credentials.viewer}")],
        "cookie_query": [("cookie", f"authorization={credentials.admin}")],
    }[kind]

    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(
                "/mcp?token=ignored",
                content=b"{",
                headers=[("content-type", "application/json"), *auth],
            )
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == 'Bearer realm="mcp"'
            assert response.json() == {"detail": "Invalid Bearer credentials"}
            assert not recorder.requests

    asyncio.run(scenario())


def test_authentication_precedes_body_read_and_rpc_inspection(credentials):
    reads = []

    async def body():
        reads.append(True)
        yield b"{"

    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(
                "/mcp", content=body(), headers={"content-type": "application/json"}
            )
            assert response.status_code == 401
            assert not reads
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "role,name",
    [
        ("admin", "admin_reset"),
        ("admin", "read"),
        ("viewer", "read"),
        ("viewer", "trigger_refund"),
        ("viewer", "Admin_reset"),
    ],
)
def test_authorized_roles_and_literal_prefix_pass_through(credentials, role, name):
    raw = rpc_body(name=name)

    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post("/mcp", content=raw, headers=headers(credentials, role))
            assert response.status_code == 200
            assert response.json()["id"] == 1
            assert len(recorder.requests) == 1
            assert recorder.requests[0].content == raw

    asyncio.run(scenario())


@pytest.mark.parametrize("request_id", [0, "", 2**100, None, "\ud800"])
def test_viewer_denial_has_exact_code_message_and_id_without_upstream(credentials, request_id):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(
                "/mcp",
                content=rpc_body(name="admin_reset", request_id=request_id),
                headers=headers(credentials),
            )
            assert response.status_code == 403
            assert response.json() == {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32001, "message": "Unauthorized Tool Call"},
            }
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "raw,code",
    [
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"\\u0061dmin_reset"}}',
            -32001,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"admin\\u005freset"}}',
            -32001,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools\\u002fcall","par\\u0061ms":{"na\\u006de":"admin_reset"}}',
            -32001,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"read","name":"admin_reset"}}',
            -32600,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"read","na\\u006de":"admin_reset"}}',
            -32600,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","role":"admin","params":{"name":"admin_reset"}}',
            -32001,
        ),
    ],
)
def test_encoded_names_duplicates_and_role_claims_cannot_bypass(credentials, raw, code):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post("/mcp", content=raw, headers=headers(credentials))
            assert response.status_code == (403 if code == -32001 else 400)
            assert response.json()["id"] == 7
            assert response.json()["error"]["code"] == code
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize("role", ["admin", "viewer"])
def test_discovery_request_response_and_admin_definitions_are_transparent(credentials, role):
    raw = b'{ "jsonrpc":"2.0", "id":"list", "method":"tools/list", "extra":1e9999 }'
    response_raw = (
        b'{ "jsonrpc":"2.0", "id":"list", "result":{"tools":'
        b'[{"name":"admin_reset"},{"name":"read"}]}, "extra":0.1234567890123456789 }'
    )

    def handler(request):
        assert request.content == raw
        return httpx.Response(
            200,
            content=response_raw,
            headers={
                "content-type": "application/json",
                "set-cookie": "session=opaque",
                "connection": "keep-alive",
                "www-authenticate": "unapproved",
            },
        )

    async def scenario():
        async with service(credentials, handler=handler) as (client, recorder, _):
            response = await client.post("/mcp", content=raw, headers=headers(credentials, role))
            assert response.status_code == 200
            assert response.content == response_raw
            assert response.json()["result"]["tools"][0]["name"] == "admin_reset"
            assert response.headers["content-length"] == str(len(response_raw))
            assert "set-cookie" not in response.headers
            assert "connection" not in response.headers
            assert "www-authenticate" not in response.headers
            assert len(recorder.requests) == 1

    asyncio.run(scenario())


def test_opaque_arguments_extensions_and_separate_credentials_survive_http(credentials):
    upstream_token = secrets.token_urlsafe(32)
    raw = (
        b'{ "jsonrpc":"2.0", "id":"\\u0061", "method":"tools/call", "params":'
        b'{"name":"read","arguments":{"amount":0.1234567890123456789,"huge":1e9999}},'
        b'"extension":{"url":"https://evil.test","headers":{"Authorization":"ignored"}} }'
    )
    response_raw = (
        b'{"jsonrpc":"2.0","id":"a","error":{"code":-32602,'
        b'"message":"Upstream error","data":{"opaque":true}}}'
    )

    def handler(request):
        assert request.url == URL
        assert request.content == raw
        assert request.headers["authorization"] == f"Bearer {upstream_token}"
        assert "cookie" not in request.headers
        assert "x-api-key" not in request.headers
        return httpx.Response(
            400, content=response_raw, headers={"content-type": "application/json"}
        )

    async def scenario():
        async with service(credentials, handler=handler, token=upstream_token) as (
            client,
            recorder,
            _,
        ):
            response = await client.post(
                "/mcp?upstream=https://evil.test",
                content=raw,
                headers={
                    **headers(credentials),
                    "cookie": "session=inbound",
                    "x-api-key": "ignored",
                },
            )
            assert response.status_code == 400
            assert response.content == response_raw
            assert len(recorder.requests) == 1

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "raw,code,request_id",
    [
        (b"", -32700, None),
        (b"{", -32700, None),
        (b"\xff", -32700, None),
        (b"null", -32600, None),
        (b"[]", -32600, None),
        (b'[{"jsonrpc":"2.0","id":1,"method":"tools/list"}]', -32600, None),
        (b'{"jsonrpc":"2.0","id":7,"method":42}', -32600, 7),
        (b'{"jsonrpc":"2.0","id":7,"method":"tools/call"}', -32602, 7),
        (b'{"jsonrpc":"2.0","id":7,"id":8,"method":"tools/list"}', -32600, None),
        (b'{"jsonrpc":"2.0","id":true,"method":"tools/list"}', -32600, None),
        (b'{"jsonrpc":"2.0","id":1.0,"method":"tools/list"}', -32600, None),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/list","extra":1e999999999999999999999999999999999999999}',
            -32700,
            None,
        ),
    ],
)
def test_malformed_rpc_and_batches_never_reach_upstream(credentials, raw, code, request_id):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post("/mcp", content=raw, headers=headers(credentials))
            assert response.status_code == 400
            assert response.json()["id"] == request_id
            assert response.json()["error"]["code"] == code
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "role,name,status",
    [("viewer", "admin_reset", 403), ("viewer", "read", 400), ("admin", "admin_reset", 400)],
)
def test_notifications_are_rejected_without_rpc_reply_or_upstream(credentials, role, name, status):
    body = json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name}}).encode()

    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post("/mcp", content=body, headers=headers(credentials, role))
            assert response.status_code == status
            assert response.content == b""
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize("method", ["GET", "HEAD", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"])
def test_only_post_is_allowed_without_read_or_upstream(credentials, method):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.request(
                method, "/mcp", content=rpc_body(), headers=headers(credentials)
            )
            assert response.status_code == 405
            assert response.headers["allow"] == "POST"
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize("path", ["/mcp/", "/", "/docs", "/openapi.json"])
def test_no_implicit_redirects_or_extra_endpoints(credentials, path):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(path, content=rpc_body(), headers=headers(credentials))
            assert response.status_code == 404
            assert "location" not in response.headers
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "metadata,status",
    [
        ([], 415),
        ([("content-type", "text/plain")], 415),
        ([("content-type", "application/json; charset=utf-16")], 415),
        ([("content-type", "application/json"), ("content-type", "application/json")], 400),
        ([("content-type", "application/json"), ("content-encoding", "gzip")], 415),
        ([("content-type", "application/json"), ("content-encoding", "br")], 415),
        (
            [
                ("content-type", "application/json"),
                ("content-encoding", "identity"),
                ("content-encoding", "identity"),
            ],
            400,
        ),
        ([("content-type", "application/json"), ("content-length", "+1")], 400),
        ([("content-type", "application/json"), ("content-length", "-1")], 400),
        ([("content-type", "application/json"), ("content-length", "one")], 400),
        (
            [
                ("content-type", "application/json"),
                ("content-length", "1"),
                ("content-length", "1"),
            ],
            400,
        ),
        (
            [
                ("content-type", "application/json"),
                ("content-length", "1"),
                ("transfer-encoding", "chunked"),
            ],
            400,
        ),
        ([("content-type", "application/json"), ("transfer-encoding", "gzip, chunked")], 400),
        (
            [
                ("content-type", "application/json"),
                ("content-length", "999999999999999999999999999999999"),
            ],
            413,
        ),
    ],
)
def test_bad_http_metadata_is_rejected_before_rpc_without_upstream(credentials, metadata, status):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            request = client.build_request(
                "POST", "/mcp", content=b"{", headers=headers(credentials)
            )
            request.headers = httpx.Headers(
                [("authorization", f"Bearer {credentials.viewer}"), *metadata]
            )
            response = await client.send(request)
            assert response.status_code == status
            assert "jsonrpc" not in response.json()
            assert not recorder.requests

    asyncio.run(scenario())


def test_compressed_body_is_not_decompressed_or_forwarded(credentials):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(
                "/mcp",
                content=gzip.compress(rpc_body()),
                headers={**headers(credentials), "content-encoding": "gzip"},
            )
            assert response.status_code == 415
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize("declared", ["1", "4096"])
def test_content_length_mismatch_is_not_silently_forwarded(credentials, declared):
    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post(
                "/mcp",
                content=rpc_body(),
                headers={**headers(credentials), "content-length": declared},
            )
            assert response.status_code == 400
            assert response.json()["detail"] == "Content-Length mismatch"
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize("extra", [0, 1])
def test_chunked_limit_is_enforced_during_read_before_forwarding(credentials, extra):
    raw = rpc_body()

    async def scenario():
        async with service(credentials, max_bytes=len(raw)) as (client, recorder, _):

            async def chunks():
                yield raw[:10]
                yield raw[10:]
                assert not recorder.requests
                if extra:
                    yield b" "

            response = await client.post("/mcp", content=chunks(), headers=headers(credentials))
            assert response.status_code == (413 if extra else 200)
            assert len(recorder.requests) == (0 if extra else 1)
            if not extra:
                assert recorder.requests[0].content == raw

    asyncio.run(scenario())


def test_declared_oversize_is_rejected_without_reading(credentials):
    reads = []

    async def chunks():
        reads.append(True)
        yield b" " * 200

    async def scenario():
        async with service(credentials, max_bytes=100) as (client, recorder, _):
            request = client.build_request(
                "POST", "/mcp", content=chunks(), headers=headers(credentials)
            )
            request.headers.pop("transfer-encoding", None)
            request.headers["content-length"] = "200"
            response = await client.send(request)
            assert response.status_code == 413
            assert not reads
            assert not recorder.requests

    asyncio.run(scenario())


def test_body_read_deadline_is_controlled_without_upstream(credentials):
    async def chunks():
        yield b"{"
        await asyncio.Event().wait()

    async def scenario():
        async with service(credentials, body_timeout=0.02) as (client, recorder, _):
            response = await client.post("/mcp", content=chunks(), headers=headers(credentials))
            assert response.status_code == 408
            assert not recorder.requests

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "exception,status",
    [
        (httpx.ReadTimeout, 504),
        (httpx.ConnectTimeout, 504),
        (httpx.ConnectError, 502),
        (httpx.RemoteProtocolError, 502),
    ],
)
def test_upstream_failures_are_controlled_and_correlated(credentials, exception, status, caplog):
    sensitive = secrets.token_urlsafe(32)

    def fail(request):
        raise exception(sensitive, request=request)

    async def scenario():
        async with service(credentials, handler=fail) as (client, recorder, _):
            response = await client.post(
                "/mcp", content=rpc_body(request_id="request-id"), headers=headers(credentials)
            )
            assert response.status_code == status
            assert response.json() == {
                "jsonrpc": "2.0",
                "id": "request-id",
                "error": {
                    "code": -32603,
                    "message": "Upstream timeout" if status == 504 else "Upstream request failed",
                },
            }
            assert len(recorder.requests) == 1
            assert sensitive not in response.text
            assert sensitive not in caplog.text

    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["redirect", "malformed", "wrong_id", "oversize", "encoding"])
def test_unsafe_upstream_responses_are_replaced_with_generic_correlated_error(credentials, mode):
    def handler(request):
        if mode == "redirect":
            return httpx.Response(307, headers={"location": "https://evil.test/"})
        if mode == "malformed":
            return httpx.Response(200, content=b"{", headers={"content-type": "application/json"})
        if mode == "wrong_id":
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": 999, "result": {}})
        if mode == "oversize":
            return httpx.Response(
                200, content=b" " * 2_097_153, headers={"content-type": "application/json"}
            )
        return httpx.Response(200, content=b"{}", headers={"content-type": "text/event-stream"})

    async def scenario():
        async with service(credentials, handler=handler) as (client, recorder, _):
            response = await client.post("/mcp", content=rpc_body(), headers=headers(credentials))
            assert response.status_code == 502
            assert response.json() == {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {"code": -32603, "message": "Upstream request failed"},
            }
            assert len(recorder.requests) == 1
            assert "location" not in response.headers

    asyncio.run(scenario())


def test_unexpected_upstream_exception_never_discloses_credentials(credentials, caplog, capsys):
    secret = secrets.token_urlsafe(32)

    def fail(request):
        raise RuntimeError(secret)

    async def scenario():
        async with service(credentials, handler=fail, token=secret) as (client, recorder, _):
            response = await client.post("/mcp", content=rpc_body(), headers=headers(credentials))
            assert response.status_code == 500
            assert response.json()["id"] == 1
            assert response.json()["error"] == {"code": -32603, "message": "Internal error"}
            assert len(recorder.requests) == 1
            for value in (secret, credentials.admin, credentials.viewer):
                assert value not in response.text
                assert value not in caplog.text

    asyncio.run(scenario())
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_concurrent_clients_do_not_mix_roles_results_or_repeated_ids(credentials):
    async def scenario():
        ready = asyncio.Event()
        seen = []

        async def handler(request):
            value = json.loads(request.content)
            number = value["params"]["arguments"]["owner"]
            seen.append(number)
            if len(seen) == 20:
                ready.set()
            await asyncio.wait_for(ready.wait(), 2)
            await asyncio.sleep((24 - number) * 0.001)
            return httpx.Response(
                200, json={"jsonrpc": "2.0", "id": 1, "result": {"owner": number}}
            )

        async with service(credentials, handler=handler) as (client, recorder, app):
            client.headers.update(headers(credentials, "admin"))

            async def call(number):
                role = "admin" if number % 2 else "viewer"
                name = "admin_reset" if number % 3 == 0 else "read"
                caller = client if role == "admin" else viewer
                response = await caller.post(
                    "/mcp",
                    content=rpc_body(name=name, arguments={"owner": number}),
                )
                denied = role == "viewer" and name == "admin_reset"
                assert response.status_code == (403 if denied else 200)
                if not denied:
                    assert response.json()["result"] == {"owner": number}
                assert response.json()["id"] == 1

            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://proxy.test",
                headers=headers(credentials, "viewer"),
            ) as viewer:
                await asyncio.gather(*(call(number) for number in range(24)))
            assert len(recorder.requests) == 20
            assert set(seen) == set(range(24)) - {0, 6, 12, 18}

    asyncio.run(scenario())


def test_lifespan_creates_one_client_and_closes_it_on_normal_or_exceptional_exit(
    credentials, monkeypatch
):
    from task2_proxy import app as module

    original = module.UpstreamAdapter
    instances = []

    class ObservedAdapter(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            instances.append(self)

    monkeypatch.setattr(module, "UpstreamAdapter", ObservedAdapter)

    async def scenario():
        transport = RecordingTransport()
        app = create_app(credentials.settings, UpstreamSettings(URL), upstream_transport=transport)
        assert not instances
        with pytest.raises(RuntimeError, match="outside request"):
            async with LifespanManager(app) as manager:
                assert len(instances) == 1
                assert not instances[0]._client.is_closed
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=manager.app), base_url="http://proxy.test"
                ) as client:
                    for _ in range(2):
                        assert (
                            await client.post(
                                "/mcp", content=rpc_body(), headers=headers(credentials)
                            )
                        ).status_code == 200
                raise RuntimeError("outside request")
        assert instances[0]._client.is_closed
        assert transport.close_count == 1
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://proxy.test"
        ) as client:
            assert (
                await client.post("/mcp", content=rpc_body(), headers=headers(credentials))
            ).status_code == 503

    asyncio.run(scenario())


def test_factory_does_not_load_credentials_until_startup_and_missing_config_fails(monkeypatch):
    monkeypatch.delenv("TASK2_ROLE_TOKENS", raising=False)
    monkeypatch.delenv("TASK2_UPSTREAM_URL", raising=False)
    app = create_app()

    async def scenario():
        with pytest.raises(ConfigurationError):
            async with LifespanManager(app):
                pytest.fail("Missing config started service")

    asyncio.run(scenario())


def test_missing_upstream_configuration_fails_before_client_creation(credentials, monkeypatch):
    monkeypatch.delenv("TASK2_UPSTREAM_URL", raising=False)
    app = create_app(credentials.settings)

    async def scenario():
        with pytest.raises(UpstreamConfigurationError):
            async with LifespanManager(app):
                pytest.fail("Missing upstream started service")

    asyncio.run(scenario())


@pytest.mark.parametrize("timeout", [0, -1, True, float("inf"), float("nan"), 10**1000])
def test_invalid_http_deadline_fails_configuration(timeout):
    with pytest.raises(ConfigurationError):
        create_app(body_timeout=timeout)


@pytest.mark.parametrize("disconnect", [False, True])
def test_asgi_lengthless_stream_limit_and_disconnect_fail_closed(credentials, disconnect):
    async def scenario():
        async with service(credentials, max_bytes=100) as (_, recorder, app):
            events = (
                [
                    {"type": "http.request", "body": b"{", "more_body": True},
                    {"type": "http.disconnect"},
                ]
                if disconnect
                else [
                    {"type": "http.request", "body": b" " * 60, "more_body": True},
                    {"type": "http.request", "body": b" " * 60, "more_body": False},
                ]
            )
            sent = []

            async def receive():
                return events.pop(0)

            async def send(message):
                sent.append(message)

            await app(
                {
                    "type": "http",
                    "asgi": {"version": "3.0"},
                    "http_version": "1.1",
                    "method": "POST",
                    "scheme": "http",
                    "path": "/mcp",
                    "raw_path": b"/mcp",
                    "query_string": b"",
                    "root_path": "",
                    "client": ("127.0.0.1", 1234),
                    "server": ("proxy.test", 80),
                    "headers": [
                        (name.encode(), value.encode())
                        for name, value in headers(credentials).items()
                    ],
                },
                receive,
                send,
            )
            assert sent[0]["type"] == "http.response.start"
            assert sent[0]["status"] == (400 if disconnect else 413)
            assert not recorder.requests

    asyncio.run(scenario())


def test_unexpected_body_reader_failure_is_sanitized_without_upstream(credentials, caplog):
    sensitive = secrets.token_urlsafe(32)

    async def chunks():
        yield b"{"
        raise RuntimeError(sensitive)

    async def scenario():
        async with service(credentials) as (client, recorder, _):
            response = await client.post("/mcp", content=chunks(), headers=headers(credentials))
            assert response.status_code == 500
            assert response.json() == {"detail": "Internal Server Error"}
            assert sensitive not in response.text
            assert sensitive not in caplog.text
            assert not recorder.requests

    asyncio.run(scenario())
