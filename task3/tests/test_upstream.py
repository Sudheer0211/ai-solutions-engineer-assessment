import logging

import httpx
import pytest

from task3_streaming.models import ErrorCode, StreamError
from task3_streaming.upstream import UpstreamAdapter, UpstreamRequest, UpstreamSettings
from tests.async_support import Body, Transport, exercise, make_service
from tests.support import stream, text_output

pytestmark = pytest.mark.task3


@pytest.mark.parametrize(
    "url",
    [
        "http://example.test/x",
        "http://localhost/x",
        "file:///private",
        "https://user:private@example.test",
        "https://example.test/?token=private",
        "https://example.test/#private",
        "https://example.test/\nprivate",
        "//example.test/x",
        "ftp://example.test/x",
        "https://example.test:0/x",
        "https://example.test\\private",
        None,
    ],
)
def test_trusted_destination_validation_does_not_echo_details(url):
    with pytest.raises(ValueError) as caught:
        UpstreamSettings(url)
    assert str(caught.value) == "Invalid upstream configuration"
    assert caught.value.__context__ is None


@pytest.mark.parametrize("url", ["https://example.test/x", "http://127.0.0.1/x", "http://[::1]/x"])
def test_permitted_fixed_destinations_and_private_configuration_repr(url):
    value = UpstreamSettings(url, "private-credential")
    assert "private" not in repr(value) and url not in repr(value)


@pytest.mark.parametrize("token", ["bad token", "private\ncredential", "", "\u2603", 3, "a" * 4097])
def test_invalid_credential_syntax(token):
    with pytest.raises(ValueError):
        UpstreamSettings("https://example.test", token)


@pytest.mark.parametrize("body", [b"", b"x" * 65537, "private", None])
def test_typed_request_size_and_repr(body):
    with pytest.raises(StreamError):
        UpstreamRequest(body)
    assert "private" not in repr(UpstreamRequest(b'"private"'))


@pytest.mark.parametrize(
    "headers,status,code",
    [
        ([("content-type", "application/json")], 200, ErrorCode.INVALID),
        ([], 200, ErrorCode.INVALID),
        (
            [("content-type", "text/event-stream"), ("content-type", "text/event-stream")],
            200,
            ErrorCode.INVALID,
        ),
        ([("content-type", "text/event-stream; charset=latin1")], 200, ErrorCode.INVALID),
        ([("content-type", "text/event-stream; unknown=x")], 200, ErrorCode.INVALID),
        (
            [("content-type", "text/event-stream"), ("content-encoding", "gzip")],
            200,
            ErrorCode.INVALID,
        ),
        (
            [("content-type", "text/event-stream"), ("content-encoding", "identity")],
            200,
            ErrorCode.INVALID,
        ),
        ([("content-type", "text/event-stream")], 302, ErrorCode.UPSTREAM),
        ([("content-type", "text/event-stream")], 429, ErrorCode.UPSTREAM),
        ([("content-type", "text/event-stream")], 500, ErrorCode.UPSTREAM),
        ([("content-type", "text/event-stream")], 204, ErrorCode.UPSTREAM),
    ],
)
def test_strict_status_encoding_type_rejection_reads_zero_body_and_closes(headers, status, code):
    async def scenario():
        body = Body([b"private@upstream"])
        transport = Transport(body, headers=headers, status=status)
        service = make_service(transport)
        with pytest.raises(StreamError) as caught:
            async with service.stream(UpstreamRequest(b"{}")):
                pass
        assert caught.value.code is code and caught.value.__context__ is None
        assert body.reads == 0 and body.closed and body.closes == 1
        assert len(transport.requests) == 1 and service.active == 0
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize(
    "media",
    ["text/event-stream", "Text/Event-Stream; charset=UTF-8", 'text/event-stream;charset="utf-8"'],
)
def test_authorized_content_types_request_bytes_and_separate_credentials(media):
    async def scenario():
        raw = b' {"prompt":"private synthetic prompt","extension":1} '
        transport = Transport(
            Body([stream("a@b.test ")]),
            headers=[
                ("content-type", media),
                ("set-cookie", "private=ignored"),
                ("x-role", "admin"),
            ],
        )
        service = make_service(transport, token="private-upstream-token")
        for _ in range(2):
            transport.body = Body([stream("safe ")])
            async with service.stream(UpstreamRequest(raw)) as session:
                frames = [frame async for frame in session]
                assert text_output(frames) == "safe " and session.completed
        for request in transport.requests:
            assert request.url == "https://synthetic.example.test/stream"
            assert request.content == raw and request.method == "POST"
            assert request.headers["authorization"] == "Bearer private-upstream-token"
            assert request.headers["accept-encoding"] == "identity"
            assert "cookie" not in request.headers and "x-role" not in request.headers
            assert request.extensions["timeout"] == {
                "connect": 5,
                "pool": 5,
                "write": 5,
                "read": 15,
            }
        assert await service.aclose() and transport.closes == 1

    exercise(scenario())


def test_raw_64k_segmentation_does_not_coalesce_small_events():
    async def scenario():
        body = Body([b":x\n\n" * 16384])  # Exactly one native 64 KiB raw block.
        adapter = UpstreamAdapter(
            UpstreamSettings("https://example.test"), transport=Transport(body)
        )
        lease = adapter.lease(UpstreamRequest(b"{}"))
        await lease.open()
        pieces = [await lease.read() for _ in range(16)]
        assert all(len(piece) == 4096 for piece in pieces)
        assert body.reads == 1 and lease.raw_chunks == 1 and lease.peak_raw_bytes == 65536
        assert await lease.read() is None
        await lease.aclose()
        await adapter.aclose()
        assert body.closed

    exercise(scenario())


def test_oversized_raw_transport_chunk_fails_without_processing_or_leak():
    async def scenario():
        body = Body([b"x" * 65537])
        service = make_service(Transport(body))
        with pytest.raises(StreamError) as caught:
            async with service.stream(UpstreamRequest(b"{}")) as session:
                await anext(session)
        assert caught.value.code is ErrorCode.LIMIT and body.closed
        assert session.lease.processing_chunks == session.lease.peak_raw_bytes == 0
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize(
    "error,code",
    [
        (httpx.ConnectError("private connect"), ErrorCode.UPSTREAM),
        (httpx.ConnectTimeout("private connect timeout"), ErrorCode.TIMEOUT),
        (httpx.PoolTimeout("private pool timeout"), ErrorCode.TIMEOUT),
        (httpx.WriteTimeout("private write timeout"), ErrorCode.TIMEOUT),
        (RuntimeError("private unexpected"), ErrorCode.UPSTREAM),
    ],
)
def test_open_failures_no_retry_and_no_diagnostic_context(error, code):
    async def scenario():
        transport = Transport(error=error)
        service = make_service(transport)
        with pytest.raises(StreamError) as caught:
            async with service.stream(UpstreamRequest(b"{}")):
                pass
        assert caught.value.code is code and "private" not in str(caught.value)
        assert caught.value.__context__ is None and len(transport.requests) == 1
        assert service.capacity.active == 0 and await service.aclose()

    exercise(scenario())


def test_httpx_private_io_logging_suppressed_without_suppressing_other_requests(caplog):
    class LoggingTransport(Transport):
        async def handle_async_request(self, request):
            logging.getLogger("httpcore.connection").debug("private-upstream-token private@body")
            return await super().handle_async_request(request)

    async def scenario():
        service = make_service(
            LoggingTransport(Body([stream("private@example.test ")])),
            token="private-upstream-token",
        )
        async with service.stream(UpstreamRequest(b'"private-prompt"')) as session:
            frames = [frame async for frame in session]
        assert "private@example.test" not in text_output(frames)
        assert await service.aclose()

    caplog.set_level(logging.DEBUG)
    exercise(scenario())
    assert "private" not in caplog.text
    logging.getLogger("httpx").warning("unrelated-safe-record")
    assert "unrelated-safe-record" in caplog.text
