"""T2-003/U1-U8: real AsyncClient + MockTransport; no HTTP endpoint or real network."""

import asyncio
import json
import secrets
from dataclasses import FrozenInstanceError, replace

import httpx
import pytest

from task2_proxy.rpc import RpcError, inspect_request
from task2_proxy.security import AuthenticationError, AuthorizedRequest, guard_request
from task2_proxy.settings import Role
from task2_proxy.upstream import (
    FailureKind,
    UpstreamAdapter,
    UpstreamConfigurationError,
    UpstreamError,
    UpstreamSettings,
    load_upstream_settings,
)

pytestmark = pytest.mark.task2
URL = "https://mcp.example.test/rpc"


def permit(credentials, *, role=Role.VIEWER, raw=None, request_id=1, name="read"):
    token = credentials.admin if role is Role.ADMIN else credentials.viewer
    if raw is None:
        raw = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": {}},
            }
        ).encode()
    return guard_request([f"Bearer {token}"], raw, credentials.settings)


def reply(request_id=1, *, status=200, result=None, headers=None):
    return httpx.Response(
        status,
        content=json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}).encode(),
        headers={"content-type": "application/json", **(headers or {})},
    )


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "/rpc",
        "//mcp.example.test/rpc",
        "ftp://mcp.example.test/rpc",
        "http://mcp.example.test/rpc",
        "http://192.168.0.1/rpc",
        "https://user:password@mcp.example.test/rpc",
        "https://@mcp.example.test/rpc",
        "https://mcp.example.test/rpc#fragment",
        "https://mcp.example.test/rpc?token=opaque",
        "https://mcp.example.test:0/rpc",
        "https://mcp.example.test:65536/rpc",
        "https://mcp.example.test/white space",
        "https://mcp.example.test/\r\npath",
        "https://mcp.example.test/\x7f",
        "https://mcp.example.test\\evil.test/rpc",
    ],
)
def test_invalid_destination_fails_closed_without_echo(url):
    with pytest.raises(UpstreamConfigurationError) as caught:
        UpstreamSettings(url)
    assert str(caught.value) == "Invalid upstream configuration"


@pytest.mark.parametrize("url", [URL, "http://127.0.0.1:8080/rpc", "http://[::1]:8080/rpc"])
def test_fixed_https_or_literal_loopback_http_destination(url):
    assert UpstreamSettings(url).url == url


@pytest.mark.parametrize(
    "changes",
    [
        {"bearer_token": ""},
        {"bearer_token": "x\r\nCookie: injected"},
        {"bearer_token": True},
        {"connect_timeout": None},
        {"read_timeout": 0},
        {"write_timeout": -1},
        {"pool_timeout": float("inf")},
        {"total_timeout": float("nan")},
        {"total_timeout": True},
        {"total_timeout": 10**1000},
        {"max_request_bytes": False},
        {"max_response_bytes": 0},
    ],
)
def test_invalid_upstream_credentials_or_resource_limits(changes):
    with pytest.raises(UpstreamConfigurationError):
        UpstreamSettings(URL, **changes)


def test_upstream_configuration_is_separate_immutable_and_redacted(monkeypatch):
    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("TASK2_UPSTREAM_URL", URL)
    monkeypatch.setenv("TASK2_UPSTREAM_BEARER_TOKEN", token)
    settings = load_upstream_settings()
    assert settings.bearer_token == token
    assert token not in repr(settings)
    assert URL not in repr(settings)
    with pytest.raises(FrozenInstanceError):
        settings.url = "https://elsewhere.test/rpc"
    with pytest.raises(UpstreamConfigurationError):
        load_upstream_settings({"TASK2_ROLE_TOKENS": "{}"})
    assert load_upstream_settings({"TASK2_UPSTREAM_URL": URL}).bearer_token is None


def test_original_request_and_discovery_response_bytes_are_unchanged(credentials):
    raw = (
        b'{ "jsonrpc":"2.0", "id":"discovery", "method":"tools/list",'
        b'"extra":{"exact":1e9999,"escaped":"\\u0061"} }'
    )
    response_body = (
        b'{ "jsonrpc":"2.0", "id":"discovery", "result":{"tools":['
        b'{"name":"admin_reset","inputSchema":{"type":"object"}},'
        b'{"name":"read","inputSchema":{"type":"object"}}]},'
        b'"opaque":1e999999999999999999999999999999999999999 }'
    )
    seen = []

    def handler(request):
        seen.append(request)
        assert request.content == raw
        assert request.url == URL
        assert request.method == "POST"
        assert request.headers["content-type"] == "application/json"
        assert request.headers["accept"] == "application/json"
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(
            200, content=response_body, headers={"content-type": "application/json"}
        )

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(handler)
        ) as a:
            response = await a.forward(permit(credentials, raw=raw))
            assert response.body == response_body
            assert response.status_code == 200
            with pytest.raises(FrozenInstanceError):
                response.body = b"rewritten"

    asyncio.run(scenario())
    assert len(seen) == 1


@pytest.mark.parametrize("request_id", [0, -1, 2**100, "", "1", None])
@pytest.mark.parametrize("error", [False, True])
def test_response_ids_results_and_error_objects_are_preserved(credentials, request_id, error):
    body = {"jsonrpc": "2.0", "id": request_id, "vendor": {"trace": "opaque"}}
    body.update(
        {"error": {"code": -32602, "message": "Upstream error", "data": [1, {"x": True}]}}
        if error
        else {"result": {"ok": True, "value": 2**100}}
    )
    raw = json.dumps(body, indent=2).encode()

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    400 if error else 200, content=raw, headers={"content-type": "application/json"}
                )
            ),
        ) as adapter:
            response = await adapter.forward(permit(credentials, request_id=request_id))
            assert response.body == raw
            assert response.status_code == (400 if error else 200)

    asyncio.run(scenario())


@pytest.mark.parametrize("status", [200, 201, 400, 401, 403, 429, 500, 502, 503])
def test_valid_correlated_jsonrpc_is_preserved_across_nonredirect_statuses(credentials, status):
    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(lambda _: reply(status=status))
        ) as adapter:
            assert (await adapter.forward(permit(credentials))).status_code == status

    asyncio.run(scenario())


@pytest.mark.parametrize("upstream_auth", [False, True])
def test_credentials_cookies_and_unsafe_headers_never_cross_contexts(credentials, upstream_auth):
    token = secrets.token_urlsafe(32) if upstream_auth else None
    seen = []

    def handler(request):
        seen.append(request)
        assert request.headers.get("authorization") == (f"Bearer {token}" if token else None)
        assert set(request.headers) <= {
            "host",
            "content-type",
            "content-length",
            "accept",
            "accept-encoding",
            "authorization",
        }
        assert credentials.admin.encode() not in repr(request.headers).encode()
        assert credentials.viewer.encode() not in repr(request.headers).encode()
        return reply(
            headers={
                "set-cookie": "session=opaque; Path=/",
                "connection": "keep-alive, x-untrusted, content-type",
                "x-untrusted": "injected",
                "location": "https://evil.test/",
                "www-authenticate": "Basic realm=upstream",
                "proxy-authenticate": "Basic realm=proxy",
                "access-control-allow-origin": "*",
                "authorization": "unapproved",
                "content-length": "999999",
            }
        )

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL, token), transport=httpx.MockTransport(handler)
        ) as adapter:
            for role in (Role.ADMIN, Role.VIEWER):
                response = await adapter.forward(permit(credentials, role=role))
                assert response.headers == (
                    ("content-type", "application/json"),
                    ("cache-control", "no-store"),
                )
            assert not list(adapter._client.cookies.jar)

    asyncio.run(scenario())
    assert len(seen) == 2


@pytest.mark.parametrize("status", [300, 301, 302, 303, 304, 307, 308])
def test_redirects_are_rejected_without_followup_or_retry(credentials, status):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, headers={"location": "https://evil.test/steal"})

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL, secrets.token_urlsafe(32)), transport=httpx.MockTransport(handler)
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.REDIRECT

    asyncio.run(scenario())
    assert len(calls) == 1
    assert calls[0].url == URL


@pytest.mark.parametrize(
    "failure,kind",
    [
        (httpx.ConnectError, FailureKind.TRANSPORT),
        (httpx.ReadError, FailureKind.TRANSPORT),
        (httpx.WriteError, FailureKind.TRANSPORT),
        (httpx.RemoteProtocolError, FailureKind.TRANSPORT),
        (httpx.ConnectTimeout, FailureKind.TIMEOUT),
        (httpx.ReadTimeout, FailureKind.TIMEOUT),
        (httpx.WriteTimeout, FailureKind.TIMEOUT),
        (httpx.PoolTimeout, FailureKind.TIMEOUT),
    ],
)
def test_transport_failures_are_sanitized_and_not_retried(credentials, failure, kind):
    calls = []
    secret = secrets.token_urlsafe(32)

    def handler(request):
        calls.append(request)
        assert request.extensions["timeout"] == {"connect": 1, "read": 2, "write": 3, "pool": 4}
        raise failure(secret, request=request)

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(
                URL, connect_timeout=1, read_timeout=2, write_timeout=3, pool_timeout=4
            ),
            transport=httpx.MockTransport(handler),
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is kind
            assert secret not in str(caught.value)
            assert caught.value.__suppress_context__

    asyncio.run(scenario())
    assert len(calls) == 1


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"{",
        b"\xff",
        b"[]",
        b"null",
        b'{"jsonrpc":"2.0","id":1}',
        b'{"jsonrpc":"2.0","id":1,"result":{},"error":{}}',
        b'{"jsonrpc":"1.0","id":1,"result":{}}',
        b'{"jsonrpc":"2.0","id":true,"result":{}}',
        b'{"jsonrpc":"2.0","id":1.0,"result":{}}',
        b'{"jsonrpc":"2.0","id":1,"result":NaN}',
        b'{"jsonrpc":"2.0","id":1,"result":Infinity}',
        b'{"jsonrpc":"2.0","result":{}}',
        b'{"jsonrpc":"2.0","id":1,"method":"x","result":{}}',
        b'{"jsonrpc":"2.0","id":1,"error":null}',
        b'{"jsonrpc":"2.0","id":1,"error":{"code":true,"message":"x"}}',
        b'{"jsonrpc":"2.0","id":1,"error":{"code":1.0,"message":"x"}}',
        b'{"jsonrpc":"2.0","id":1,"error":{"code":1,"message":null}}',
        b'{"jsonrpc":"2.0","id":1,"id":1,"result":{}}',
        b'{"jsonrpc":"2.0","id":1,"result":{"x":1,"x":2}}',
        b'{"jsonrpc":"2.0","id":1,"result":{},"res\\u0075lt":{}}',
    ],
)
def test_malformed_upstream_response_is_not_relayed(credentials, body):
    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200, content=body, headers={"content-type": "application/json"}
                )
            ),
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.INVALID_RESPONSE

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "request_id,response_id", [(1, "1"), (1, 2), (None, 1), (1, None), ("", 0)]
)
def test_mismatched_ids_are_rejected_without_coercion(credentials, request_id, response_id):
    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(lambda _: reply(response_id))
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials, request_id=request_id))
            assert caught.value.kind is FailureKind.ID_MISMATCH

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("content-type", "text/html")],
        [("content-type", "text/event-stream")],
        [("content-type", "application/json"), ("content-type", "application/json")],
        [("content-type", "application/json"), ("content-encoding", "gzip")],
    ],
)
def test_unsupported_media_or_encoding_is_rejected(credentials, headers):
    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200, stream=Chunks([b'{"jsonrpc":"2.0","id":1,"result":{}}']), headers=headers
                )
            ),
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.INVALID_RESPONSE

    asyncio.run(scenario())


def test_forwarding_requires_a_guard_issued_unmodified_permit(credentials):
    issued = permit(credentials)
    constructed = AuthorizedRequest(Role.ADMIN, inspect_request(issued.request.raw_body))
    invalid = [
        None,
        b"raw",
        issued.request,
        constructed,
        replace(issued, role=Role.ADMIN),
        replace(
            issued,
            request=inspect_request(
                b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"admin_reset"}}'
            ),
        ),
    ]
    calls = []

    def handler(request):
        calls.append(request)
        return reply()

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(handler)
        ) as adapter:
            for value in invalid:
                with pytest.raises(AuthenticationError):
                    await adapter.forward(value)
            with pytest.raises(RpcError) as caught:
                await adapter.forward(permit(credentials, name="admin_reset"))
            assert caught.value.code == -32001
            assert not calls
            assert (await adapter.forward(issued)).status_code == 200

    asyncio.run(scenario())
    assert len(calls) == 1


def test_copied_proof_cannot_authorize_modified_role_body_or_metadata(credentials):
    issued = permit(credentials)
    forged = [
        AuthorizedRequest(Role.ADMIN, issued.request),
        AuthorizedRequest(
            Role.VIEWER,
            inspect_request(
                b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"admin_reset"}}'
            ),
        ),
        AuthorizedRequest(Role.VIEWER, replace(issued.request, request_id="spoofed")),
        AuthorizedRequest(Role.VIEWER, replace(issued.request, tool_name="admin_reset")),
    ]
    for value in forged:
        object.__setattr__(value, "_proof", issued._proof)

    def handler(request):
        pytest.fail("Forged permit reached upstream")

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(handler)
        ) as adapter:
            for value in forged:
                with pytest.raises(AuthenticationError):
                    await adapter.forward(value)

    asyncio.run(scenario())


def test_media_parameters_identity_encoding_and_escaped_response_id(credentials):
    body = b'{"jsonrpc":"2.0","id":"\\u0061","result":{"value":1.2}}'

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200,
                    content=body,
                    headers={
                        "content-type": "Application/JSON; charset=utf-8",
                        "content-encoding": "Identity",
                    },
                )
            ),
        ) as adapter:
            assert (await adapter.forward(permit(credentials, request_id="a"))).body == body

    asyncio.run(scenario())


def test_fixed_url_ignores_body_urls_and_spoofed_headers(credentials):
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "url": "https://evil.test/",
            "headers": {"Authorization": "unapproved", "Cookie": "x=y"},
        }
    ).encode()
    seen = []

    def handler(request):
        seen.append(request)
        return reply()

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL), transport=httpx.MockTransport(handler)
        ) as adapter:
            await adapter.forward(permit(credentials, raw=raw))

    asyncio.run(scenario())
    assert seen[0].url == URL
    assert "authorization" not in seen[0].headers
    assert "cookie" not in seen[0].headers
    assert seen[0].content == raw


class Chunks(httpx.AsyncByteStream):
    def __init__(self, chunks, *, wait=False, failure=None):
        self.chunks = chunks
        self.wait = wait
        self.failure = failure
        self.closed = False
        self.started = asyncio.Event()

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        self.started.set()
        if self.wait:
            await asyncio.Event().wait()
        if self.failure:
            raise self.failure("stream failed")

    async def aclose(self):
        self.closed = True


def test_streamed_response_is_bounded_and_closed_on_success_and_failures(credentials):
    async def scenario():
        raw = b'{"jsonrpc":"2.0","id":1,"result":{}}'
        for chunks, limit, expected in [
            ([raw[:10], raw[10:]], len(raw), None),
            ([raw[:10], raw[10:]], len(raw) - 1, FailureKind.RESPONSE_TOO_LARGE),
            ([b"{"], 100, FailureKind.INVALID_RESPONSE),
        ]:
            stream = Chunks(chunks)
            async with UpstreamAdapter(
                UpstreamSettings(URL, max_response_bytes=limit),
                transport=httpx.MockTransport(
                    lambda _, stream=stream: httpx.Response(
                        200, stream=stream, headers={"content-type": "application/json"}
                    )
                ),
            ) as adapter:
                if expected:
                    with pytest.raises(UpstreamError) as caught:
                        await adapter.forward(permit(credentials))
                    assert caught.value.kind is expected
                else:
                    assert (await adapter.forward(permit(credentials))).body == raw
                assert stream.closed

    asyncio.run(scenario())


def test_request_and_preloaded_response_limits(credentials):
    calls = []

    def handler(request):
        calls.append(request)
        return reply(result="x" * 100)

    async def scenario():
        async with UpstreamAdapter(
            UpstreamSettings(URL, max_request_bytes=1), transport=httpx.MockTransport(handler)
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.REQUEST_TOO_LARGE
            assert not calls
        async with UpstreamAdapter(
            UpstreamSettings(URL, max_response_bytes=10), transport=httpx.MockTransport(handler)
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.RESPONSE_TOO_LARGE

    asyncio.run(scenario())
    assert len(calls) == 1


def test_total_deadline_and_cancellation_close_streams_without_retry(credentials):
    async def scenario():
        for cancel in (False, True):
            stream = Chunks([], wait=True)
            calls = []

            def handler(request, *, calls=calls, stream=stream):
                calls.append(request)
                return httpx.Response(
                    200, stream=stream, headers={"content-type": "application/json"}
                )

            async with UpstreamAdapter(
                UpstreamSettings(URL, total_timeout=0.05 if not cancel else 5),
                transport=httpx.MockTransport(handler),
            ) as adapter:
                task = asyncio.create_task(adapter.forward(permit(credentials)))
                await asyncio.wait_for(stream.started.wait(), 1)
                if cancel:
                    task.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await task
                else:
                    with pytest.raises(UpstreamError) as caught:
                        await task
                    assert caught.value.kind is FailureKind.TIMEOUT
                assert stream.closed
                assert len(calls) == 1

    asyncio.run(scenario())


def test_midstream_network_failure_is_contained_and_closed(credentials):
    async def scenario():
        stream = Chunks([b"{"], failure=httpx.ReadError)
        async with UpstreamAdapter(
            UpstreamSettings(URL),
            transport=httpx.MockTransport(
                lambda _: httpx.Response(
                    200, stream=stream, headers={"content-type": "application/json"}
                )
            ),
        ) as adapter:
            with pytest.raises(UpstreamError) as caught:
                await adapter.forward(permit(credentials))
            assert caught.value.kind is FailureKind.TRANSPORT
            assert stream.closed

    asyncio.run(scenario())


@pytest.mark.parametrize("same_id", [False, True])
def test_concurrent_requests_share_client_without_context_or_id_mixup(credentials, same_id):
    async def scenario():
        tokens = [secrets.token_urlsafe(32), secrets.token_urlsafe(32)]
        seen = []
        ready = asyncio.Event()

        def handler_for(index):
            async def handler(request):
                value = json.loads(request.content)
                owner = value["params"]["arguments"]["owner"]
                seen.append((index, owner, request.headers.get("authorization")))
                if len(seen) == 12:
                    ready.set()
                await asyncio.wait_for(ready.wait(), 2)
                await asyncio.sleep((12 - owner) * 0.001)
                return reply(
                    value["id"],
                    result={"echo": value["params"]["arguments"]},
                    headers={"set-cookie": "session=opaque; Path=/"},
                )

            return handler

        async with (
            UpstreamAdapter(
                UpstreamSettings(URL, tokens[0]), transport=httpx.MockTransport(handler_for(0))
            ) as first,
            UpstreamAdapter(
                UpstreamSettings(URL, tokens[1]), transport=httpx.MockTransport(handler_for(1))
            ) as second,
        ):
            requests = []
            for number in range(12):
                raw = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1 if same_id else number,
                        "method": "tools/call",
                        "params": {"name": "read", "arguments": {"owner": number}},
                    }
                ).encode()
                role = Role.ADMIN if number % 2 else Role.VIEWER
                requests.append(
                    (first if number % 2 else second).forward(
                        permit(credentials, raw=raw, role=role)
                    )
                )
            responses = await asyncio.gather(*requests)
            for number, response in enumerate(responses):
                body = json.loads(response.body)
                assert body["id"] == (1 if same_id else number)
                assert body["result"]["echo"] == {"owner": number}
            for index, number, authorization in seen:
                assert authorization == f"Bearer {tokens[index]}"
                assert index == (0 if number % 2 else 1)

    asyncio.run(scenario())


def test_pooled_client_configuration_and_idempotent_close(credentials, monkeypatch):
    original = httpx.AsyncHTTPTransport
    options = []

    def capture(**kwargs):
        options.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", capture)
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("SSL_CERT_FILE", "missing-untrusted.pem")

    async def scenario():
        adapter = UpstreamAdapter(UpstreamSettings(URL))
        assert adapter._client.follow_redirects is False
        assert adapter._client.trust_env is False
        await adapter.aclose()
        await adapter.aclose()
        with pytest.raises(UpstreamError) as caught:
            await adapter.forward(permit(credentials))
        assert caught.value.kind is FailureKind.CLOSED

    asyncio.run(scenario())
    assert options[0]["retries"] == 0
    assert options[0]["trust_env"] is False
    assert options[0]["limits"].max_connections == 20
    assert options[0]["limits"].max_keepalive_connections == 10
