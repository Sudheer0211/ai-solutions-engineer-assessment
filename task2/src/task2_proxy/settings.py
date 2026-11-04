"""T2-002: explicit immutable role-token configuration, with no default secrets."""

import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

ENVIRONMENT_KEY = "TASK2_ROLE_TOKENS"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._~+/-]+=*")


class Role(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"


class ConfigurationError(ValueError):
    """Safe configuration failure; never includes supplied values."""


@dataclass(frozen=True, slots=True)
class TokenBinding:
    token: str = field(repr=False)
    role: Role

    def __post_init__(self) -> None:
        if type(self.token) is not str or not TOKEN_PATTERN.fullmatch(self.token):
            raise ConfigurationError("Invalid role-token configuration")
        if type(self.role) is not Role:
            raise ConfigurationError("Invalid role-token configuration")


@dataclass(frozen=True, slots=True)
class SecuritySettings:
    bindings: tuple[TokenBinding, ...] = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.bindings) is not tuple or not self.bindings:
            raise ConfigurationError("Invalid role-token configuration")
        seen: set[str] = set()
        roles: set[Role] = set()
        for binding in self.bindings:
            if not isinstance(binding, TokenBinding) or binding.token in seen:
                raise ConfigurationError("Invalid role-token configuration")
            seen.add(binding.token)
            roles.add(binding.role)
        if roles != set(Role):
            raise ConfigurationError("Invalid role-token configuration")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError("Invalid role-token configuration")
        result[key] = value
    return result


def load_settings(environment: Mapping[str, str] | None = None) -> SecuritySettings:
    """Read credentials only when explicitly invoked; a mapping makes loading testable."""
    source = os.environ if environment is None else environment
    raw = source.get(ENVIRONMENT_KEY)
    if type(raw) is not str or not raw:
        raise ConfigurationError("Role-token configuration is required")
    try:
        mapping = json.loads(raw, object_pairs_hook=_unique_object)
        if type(mapping) is not dict or set(mapping) != {role.value for role in Role}:
            raise ConfigurationError("Invalid role-token configuration")
        bindings = []
        for role in Role:
            values = mapping[role.value]
            if type(values) is not list or not values:
                raise ConfigurationError("Invalid role-token configuration")
            bindings.extend(TokenBinding(token, role) for token in values)
        return SecuritySettings(tuple(bindings))
    except (ValueError, TypeError, RecursionError):
        raise ConfigurationError("Invalid role-token configuration") from None
