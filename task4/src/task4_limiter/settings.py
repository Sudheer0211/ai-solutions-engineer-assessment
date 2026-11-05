"""T4-005: external HTTP credentials/configuration, separate from provider secrets."""

import hashlib
import hmac
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from task4_limiter.service import RoutingPolicy
from task4_limiter.storage import StorageError, StorageSettings

_TOKEN = re.compile(rb"[A-Za-z0-9._~+/-]{32,256}=*")


class ConfigurationError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid Task 4 configuration")


class AuthenticationError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid credentials")


@dataclass(frozen=True, slots=True, init=False)
class TenantCredentials:
    _digests: tuple[bytes, ...] = field(repr=False)

    def __init__(self, keys: tuple[bytes, ...]) -> None:
        if (
            type(keys) is not tuple
            or not 1 <= len(keys) <= 1024
            or any(type(k) is not bytes or len(k) > 256 or not _TOKEN.fullmatch(k) for k in keys)
            or len(set(keys)) != len(keys)
        ):
            raise ConfigurationError()
        object.__setattr__(self, "_digests", tuple(hashlib.sha256(k).digest() for k in keys))

    def authenticate(self, headers: list[str]) -> bytes:
        if len(headers) != 1:
            raise AuthenticationError()
        try:
            scheme, token = headers[0].encode("ascii").split(b" ")
        except (UnicodeError, ValueError):
            raise AuthenticationError() from None
        if scheme.lower() != b"bearer" or len(token) > 256 or not _TOKEN.fullmatch(token):
            raise AuthenticationError()
        digest = hashlib.sha256(token).digest()
        # Visit every configured digest; a revoked/not-listed key is indistinguishable
        # from an unknown one. No roles or caller-selected tenant identity.
        allowed = False
        for configured in self._digests:
            allowed |= hmac.compare_digest(digest, configured)
        if not allowed:
            raise AuthenticationError()
        return token  # Existing SQLiteStore derives the stable tenant HMAC.


@dataclass(frozen=True, slots=True)
class HTTPSettings:
    storage: StorageSettings = field(repr=False)
    credentials: TenantCredentials = field(repr=False)
    routing: RoutingPolicy
    max_body_bytes: int = 65_536
    body_timeout_ms: int = 5000

    def __post_init__(self) -> None:
        if (
            type(self.storage) is not StorageSettings
            or type(self.credentials) is not TenantCredentials
            or type(self.routing) is not RoutingPolicy
            or type(self.max_body_bytes) is not int
            or not 1 <= self.max_body_bytes <= 1_048_576
            or type(self.body_timeout_ms) is not int
            or not 1 <= self.body_timeout_ms <= 60_000
        ):
            raise ConfigurationError()


def load_settings(environment: Mapping[str, str] | None = None) -> HTTPSettings:
    env = os.environ if environment is None else environment
    try:
        keys = json.loads(env["TASK4_TENANT_KEYS_JSON"])
        if type(keys) is not list or any(type(k) is not str for k in keys):
            raise ValueError
        return HTTPSettings(
            StorageSettings(
                Path(env["TASK4_DATABASE_PATH"]), bytes.fromhex(env["TASK4_IDENTITY_SECRET_HEX"])
            ),
            TenantCredentials(tuple(k.encode("ascii") for k in keys)),
            RoutingPolicy(int(env["TASK4_BACKUP_TIMEOUT_MS"]), int(env["TASK4_RESERVATION_MS"])),
            int(env.get("TASK4_MAX_BODY_BYTES", "65536")),
            int(env.get("TASK4_BODY_TIMEOUT_MS", "5000")),
        )
    except (KeyError, ValueError, TypeError, UnicodeError, OverflowError, StorageError):
        raise ConfigurationError() from None
