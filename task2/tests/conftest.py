"""T2-002: ephemeral synthetic credentials; no checked-in credential values."""

import json
import secrets
from dataclasses import dataclass, field

import pytest

from task2_proxy.settings import ENVIRONMENT_KEY, SecuritySettings, load_settings


@dataclass(frozen=True)
class Credentials:
    admin: str = field(repr=False)
    viewer: str = field(repr=False)
    settings: SecuritySettings


@pytest.fixture
def credentials():
    admin, viewer = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    settings = load_settings({ENVIRONMENT_KEY: json.dumps({"admin": [admin], "viewer": [viewer]})})
    return Credentials(admin, viewer, settings)


@pytest.fixture
def rpc_body():
    def make(*, method="tools/call", name="read_record", request_id="request-17", **extras):
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": {"name": name},
                **extras,
            }
        ).encode()

    return make
