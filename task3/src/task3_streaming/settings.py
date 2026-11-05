"""T3-004 operator-only configuration; no caller routing or credential options."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from hmac import compare_digest

from task3_streaming.upstream import UpstreamSettings


class ConfigurationError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid HTTP configuration")


@dataclass(frozen=True, slots=True)
class HTTPSettings:
    upstream: UpstreamSettings = field(repr=False)
    access_token: str = field(repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.upstream) is not UpstreamSettings
            or type(self.access_token) is not str
            or not 32 <= len(self.access_token) <= 4096
            or re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", self.access_token) is None
            or self.access_token == self.upstream.bearer_token
        ):
            raise ConfigurationError()


def load_settings(environ: Mapping[str, str] | None = None) -> HTTPSettings:
    source = os.environ if environ is None else environ
    failed = False
    try:
        result = HTTPSettings(
            UpstreamSettings(source["T3_UPSTREAM_URL"], source.get("T3_UPSTREAM_BEARER")),
            source["T3_ACCESS_TOKEN"],
        )
    except (KeyError, TypeError, ValueError):
        failed = True
    if failed:
        raise ConfigurationError()  # No environment values or exception context.
    return result


def authenticated(values: list[bytes], settings: HTTPSettings) -> bool:
    if len(values) != 1 or len(values[0]) > 4103:
        return False
    value = values[0]
    match = re.fullmatch(rb"(?i:Bearer) ([A-Za-z0-9._~+/-]+=*)", value)
    return match is not None and compare_digest(match[1], settings.access_token.encode("ascii"))
