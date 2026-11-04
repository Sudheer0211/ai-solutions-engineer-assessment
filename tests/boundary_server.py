"""T1-008 test-only public handlers; production still advertises two tools."""

import asyncio
import logging
import os
import subprocess
import sys

import anyio
from mcp.types import RequestParams

from task1.server import create_server
from task1.stdio_boundary import validated_stdio

logger = logging.getLogger(__name__)


async def run():
    server = create_server()
    started, cancelled = anyio.Event(), anyio.Event()

    async def slow(ctx, params):
        started.set()
        try:
            await anyio.sleep_forever()
        finally:
            cancelled.set()
            logger.info("Slow handler stopped")

    async def wait_started(ctx, params):
        await started.wait()
        return {"started": True}

    async def wait_cancelled(ctx, params):
        await cancelled.wait()
        return {"cancelled": True}

    async def noise(ctx, params):
        print("BOUNDARY_PRINT_NOISE", flush=True)
        os.write(1, b"BOUNDARY_FD_NOISE\n")
        subprocess.run(
            [sys.executable, "-c", "print('BOUNDARY_CHILD_NOISE')"],
            stdin=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        return {"ok": True}

    for method, handler in (
        ("test/slow", slow),
        ("test/started", wait_started),
        ("test/cancelled", wait_cancelled),
        ("test/noise", noise),
    ):
        server.add_request_handler(method, RequestParams, handler)
    async with validated_stdio() as (read, write):
        await server.run(read, write, server.create_initialization_options())
        logger.info("Capture high_watermark=%s", read.observed.high_watermark)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    asyncio.run(run())
