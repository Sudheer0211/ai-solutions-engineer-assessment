import pytest

from task3_streaming.settings import ConfigurationError, HTTPSettings, authenticated, load_settings
from task3_streaming.upstream import UpstreamSettings
from tests.http_support import SETTINGS, TOKEN, UPSTREAM

pytestmark = pytest.mark.task3


@pytest.mark.parametrize(
    "token", [None, 4, "", "short", "x" * 4097, "x " * 20, "x" * 32 + "\n", "\u2603" * 32]
)
def test_settings_reject_unreliable_or_invalid_credentials_without_echo(token):
    with pytest.raises(ConfigurationError) as caught:
        HTTPSettings(SETTINGS.upstream, token)
    assert str(caught.value) == "Invalid HTTP configuration"


def test_settings_environment_loading_and_private_repr():
    settings = load_settings(
        {
            "T3_ACCESS_TOKEN": TOKEN,
            "T3_UPSTREAM_URL": "https://example.test",
            "T3_UPSTREAM_BEARER": UPSTREAM,
        }
    )
    assert TOKEN not in repr(settings) and UPSTREAM not in repr(settings)
    assert settings.upstream.bearer_token == UPSTREAM
    with pytest.raises(ConfigurationError):
        HTTPSettings(UpstreamSettings("https://example.test", TOKEN), TOKEN)


@pytest.mark.parametrize(
    "source",
    [
        {},
        {"T3_ACCESS_TOKEN": TOKEN},
        {"T3_ACCESS_TOKEN": TOKEN, "T3_UPSTREAM_URL": "file:///private"},
    ],
)
def test_configuration_errors_have_no_private_context(source):
    with pytest.raises(ConfigurationError) as caught:
        load_settings(source)
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "values",
    [
        [],
        [b"Basic private"],
        [b"Bearer private"],
        [("Bearer " + TOKEN).encode()] * 2,
        [("Bearer  " + TOKEN).encode()],
        [("Bearer\t" + TOKEN).encode()],
        [("Bearer " + TOKEN + ",private").encode()],
        [("Bearer " + TOKEN + " ").encode()],
        [b"Bearer \xff"],
        [b"x" * 4200],
    ],
)
def test_bearer_fail_closed(values):
    assert not authenticated(values, SETTINGS)


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER"])
def test_bearer_scheme_is_case_insensitive_token_is_exact(scheme):
    assert authenticated([(scheme + " " + TOKEN).encode()], SETTINGS)
    assert not authenticated([(scheme + " " + TOKEN.upper()).encode()], SETTINGS)
