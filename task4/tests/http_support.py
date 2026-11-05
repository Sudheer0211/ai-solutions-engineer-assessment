"""T4-005 ASGI fixtures: synthetic accounting/adapters, never real model claims."""

import asyncio
import secrets
from contextlib import asynccontextmanager

import httpx
from asgi_lifespan import LifespanManager
from orchestration_support import FakeProvider

from task4_limiter.app import create_app
from task4_limiter.providers import ProviderResult, ProviderStatus
from task4_limiter.service import RoutingPolicy
from task4_limiter.settings import HTTPSettings, TenantCredentials


class HTTPProvider(FakeProvider):
    def prepare(self, text):
        attempt = super().prepare(text)
        original = attempt.execute

        async def execute():
            result = await original()
            if result.status == ProviderStatus.SUCCESS:
                return ProviderResult(result.status, result.usage, "Synthetic completion")
            return result

        attempt.execute = execute
        return attempt


@asynccontextmanager
async def http_stack(
    state, *, primary=None, backup=None, mono=None, keys=None, limit=65536, body_timeout=5000
):
    _, clock, storage, _ = state
    keys = keys or tuple(secrets.token_urlsafe(32).encode() for _ in range(2))
    config = HTTPSettings(
        storage, TenantCredentials(keys), RoutingPolicy(1000, 10_000), limit, body_timeout
    )
    primary = primary or HTTPProvider()
    backup = backup or HTTPProvider("backup")
    events = []

    @asynccontextmanager
    async def resources():
        events.append("open")
        try:
            yield primary, backup
        finally:
            events.append("close")

    app = create_app(
        config, provider_resources=resources, accounting_clock=clock, monotonic_clock=mono
    )
    async with LifespanManager(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app), base_url="http://test"
        ) as client:
            yield app, client, keys, primary, backup, events


def auth(key):
    return {"authorization": "Bearer " + key.decode()}


async def raw_asgi(app, headers, body=b"", *, receive=None, method="POST", path="/generate"):
    messages = []
    sent_body = False

    async def default_receive():
        nonlocal sent_body
        if not sent_body:
            sent_body = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Event().wait()

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers,
        "server": ("test", 80),
        "client": ("127.0.0.1", 1),
        "root_path": "",
    }
    await app(scope, receive or default_receive, send)
    return messages
