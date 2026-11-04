"""T1-005: test-only injected domain failure, using public SDK APIs."""

import asyncio
import logging
import sys

from mcp.server.stdio import stdio_server

from task1.repository import MockRepository
from task1.server import create_server


class FailingRepository(MockRepository):
    def get_customer(self, customer_id):
        raise RuntimeError("PRIVATE_IMPLEMENTATION_DETAILS")


async def main():
    server = create_server(FailingRepository())
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    asyncio.run(main())
