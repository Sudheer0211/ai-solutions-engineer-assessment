"""T1-008: SDK parser contracts, classification and bounded stream ownership."""

import contextvars
import io
import json

import anyio
import pytest
from anyio.abc import ObjectSendStream
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
from mcp.types import jsonrpc_message_adapter
from pydantic import ValidationError

from task1.stdio_boundary import BoundaryReceiveStream, ObservedInput, classify_frame

pytestmark = pytest.mark.task1


def sdk_item(raw):
    try:
        return SessionMessage(jsonrpc_message_adapter.validate_json(raw, by_name=False))
    except ValidationError as error:
        return error


@pytest.mark.parametrize("raw", ['{"id":17,', "not-json", "", "{", '[{"id":17}'])
def test_malformed_syntax_never_recovers_partial_id(raw):
    error = classify_frame(raw, sdk_item(raw))
    assert error.error.code == -32700
    assert error.id is None
    assert '"id":null' in error.model_dump_json(by_alias=True, exclude_unset=True)


@pytest.mark.parametrize("request_id", [0, 42, "", "original-A", "original-B"])
def test_id_preserved_when_validation_details_lose_it(request_id):
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": 7,
            "params": [],
            "result": [],
            "error": [],
        }
    )
    error = classify_frame(raw, sdk_item(raw))
    assert error.error.code == -32600
    assert error.id == request_id
    assert type(error.id) is type(request_id)


@pytest.mark.parametrize("request_id", [True, False, 1.5, [], {}, None])
def test_invalid_id_union_fallback_is_not_a_notification(request_id):
    raw = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": "tools/list"})
    error = classify_frame(raw, sdk_item(raw))
    assert error.error.code == -32600
    assert error.id is None


@pytest.mark.parametrize("value", [None, [], [1, 2], 42, "request"])
def test_nonobject_envelope(value):
    raw = json.dumps(value)
    error = classify_frame(raw, sdk_item(raw))
    assert error.error.code == -32600
    assert error.id is None


@pytest.mark.parametrize("extras", [{"result": {}}, {"error": {"code": -32600, "message": "x"}}])
def test_request_with_invalid_method_cannot_fall_back_to_response(extras):
    raw = json.dumps({"jsonrpc": "2.0", "id": "invalid-method", "method": 7, **extras})
    error = classify_frame(raw, sdk_item(raw))
    assert error.error.code == -32600
    assert error.id == "invalid-method"


@pytest.mark.parametrize(
    "raw",
    [
        '{"jsonrpc":"2.0","method":"notifications/initialized"}',
        '{"jsonrpc":"2.0","method":"notifications/cancelled","params":{"requestId":7}}',
        '{"jsonrpc":"2.0","method":"notifications/progress","params":[]}',
        '{"jsonrpc":"2.0","id":7,"result":{}}',
        '{"jsonrpc":"2.0","id":7,"result":[]}',
        '{"jsonrpc":"2.0","id":7,"error":[]}',
        '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{}}',
    ],
)
def test_notifications_responses_and_method_validation_remain_sdk_owned(raw):
    assert classify_frame(raw, sdk_item(raw)) is None


async def test_observation_contract_fails_closed_and_closes_only_owned_file():
    source = io.StringIO("one\ntwo\nthree\n")
    async with ObservedInput(source) as observed:
        assert await observed.readline() == "one\n"
        assert await observed.readline() == "two\n"
        with pytest.raises(RuntimeError, match="lookahead contract"):
            await observed.readline()
        assert observed.high_watermark == 2
        assert observed.take_frame() == "one\n"
        assert observed.take_frame() == "two\n"
        with pytest.raises(RuntimeError, match="correlation unavailable"):
            observed.take_frame()
    assert source.closed
    assert not observed.frames


class PausedOutput(ObjectSendStream[SessionMessage]):
    def __init__(self, target):
        self.target = target
        self.blocked, self.release = anyio.Event(), anyio.Event()

    async def send(self, value):
        self.blocked.set()
        await self.release.wait()
        await self.target.send(value)

    async def aclose(self):
        await self.target.aclose()


async def test_real_sdk_parser_pipeline_with_paused_error_output():
    frames = []
    for index in range(100):
        method = 7 if index % 2 == 0 else "ping"
        frames.append(json.dumps({"jsonrpc": "2.0", "id": index, "method": method}) + "\n")
    source, output = io.StringIO("".join(frames)), io.StringIO()
    async with ObservedInput(source) as observed:
        async with stdio_server(stdin=observed, stdout=anyio.wrap_file(output)) as (read, write):
            paused = PausedOutput(write)
            boundary = BoundaryReceiveStream(read, paused, observed)
            accepted = []

            async def consume():
                async with boundary:
                    async for item in boundary:
                        accepted.append(item.message.id)
                await write.aclose()

            async with anyio.create_task_group() as tasks:
                tasks.start_soon(consume)
                with anyio.fail_after(5):
                    await paused.blocked.wait()
                assert observed.high_watermark <= 2
                assert source.tell() < len(source.getvalue())
                paused.release.set()
        errors = [json.loads(line) for line in output.getvalue().splitlines()]
        assert [error["id"] for error in errors] == list(range(0, 100, 2))
        assert all(error["error"]["code"] == -32600 for error in errors)
        assert accepted == list(range(1, 100, 2))
        assert not observed.frames
        assert observed.high_watermark <= 2


async def test_cancellation_and_nonvalidation_io_error_are_not_protocol_errors():
    sender, receiver = anyio.create_memory_object_stream(1)
    out_sender, out_receiver = anyio.create_memory_object_stream(1)
    async with ObservedInput(io.StringIO("input\n")) as observed:
        await observed.readline()
        failure = OSError("synthetic read fault")
        await sender.send(failure)
        boundary = BoundaryReceiveStream(receiver, out_sender, observed)
        with pytest.raises(OSError, match="synthetic read fault"):
            await boundary.receive()
        with anyio.CancelScope() as scope:
            scope.cancel()
            await boundary.receive()
        assert scope.cancelled_caught
        with pytest.raises(anyio.WouldBlock):
            out_receiver.receive_nowait()
        await boundary.aclose()
    sender.close()
    out_sender.close()
    out_receiver.close()


async def test_forwarded_message_identity_metadata_and_context():
    class ContextInput:
        last_context = contextvars.copy_context()

        async def receive(self):
            return message

        async def aclose(self):
            pass

    message = sdk_item('{"jsonrpc":"2.0","id":1,"method":"ping"}')
    message.metadata = object()
    outgoing, incoming = anyio.create_memory_object_stream(0)
    async with ObservedInput(io.StringIO('{"jsonrpc":"2.0","id":1,"method":"ping"}\n')) as observed:
        await observed.readline()
        source = ContextInput()
        boundary = BoundaryReceiveStream(source, outgoing, observed)
        assert await boundary.receive() is message
        assert boundary.last_context is source.last_context
        await boundary.aclose()
    outgoing.close()
    incoming.close()
