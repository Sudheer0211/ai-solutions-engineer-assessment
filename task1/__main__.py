"""T1-004: python -m task1 starts only the official SDK STDIO transport."""

import asyncio
import logging
import sys

from task1.server import create_server
from task1.stdio_boundary import validated_stdio

logger = logging.getLogger(__name__)


async def run() -> None:
    server = create_server()
    logger.info("MCP STDIO server starting")
    try:
        async with validated_stdio() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    finally:
        logger.info("MCP STDIO server stopped")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(levelname)s %(name)s %(message)s",
        force=True,
    )
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("MCP STDIO server interrupted")


if __name__ == "__main__":
    main()
