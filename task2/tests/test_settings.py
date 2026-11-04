"""T2-C1/T2-C2: configuration failures, immutability and secret redaction."""

import json
import secrets
from dataclasses import FrozenInstanceError

import pytest

from task2_proxy.settings import (
    ENVIRONMENT_KEY,
    ConfigurationError,
    Role,
    SecuritySettings,
    TokenBinding,
    load_settings,
)

pytestmark = pytest.mark.task2


@pytest.mark.parametrize("environment", [{}, {ENVIRONMENT_KEY: ""}, {ENVIRONMENT_KEY: None}])
def test_missing_configuration_has_no_default(environment):
    with pytest.raises(ConfigurationError):
        load_settings(environment)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        {},
        {"admin": []},
        {"admin": [], "viewer": []},
        {"admin": [True], "viewer": ["x"]},
        {"admin": "x", "viewer": ["y"]},
        {"admin": ["x"], "viewer": ["y"], "owner": ["z"]},
        {"admin": [""], "viewer": ["y"]},
        {"admin": ["x y"], "viewer": ["y"]},
        {"admin": ["é"], "viewer": ["y"]},
        {"admin": ["x\n"], "viewer": ["y"]},
        {"admin": ["x"], "viewer": ["x"]},
        {"admin": ["x", "x"], "viewer": ["y"]},
    ],
)
def test_invalid_mapping_fails_closed(value):
    with pytest.raises(ConfigurationError, match="Invalid role-token configuration"):
        load_settings({ENVIRONMENT_KEY: json.dumps(value)})


@pytest.mark.parametrize("raw", ["{", "not-json", '{"admin":["x"],"admin":["y"],"viewer":["z"]}'])
def test_malformed_or_duplicate_role_keys(raw):
    with pytest.raises(ConfigurationError):
        load_settings({ENVIRONMENT_KEY: raw})


def test_environment_is_loaded_explicitly(monkeypatch):
    admin, viewer = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    monkeypatch.setenv(ENVIRONMENT_KEY, json.dumps({"admin": [admin], "viewer": [viewer]}))
    settings = load_settings()
    assert {binding.role for binding in settings.bindings} == {Role.ADMIN, Role.VIEWER}
    assert (
        load_settings({ENVIRONMENT_KEY: json.dumps({"admin": ["A"], "viewer": ["B"]})}) != settings
    )


def test_settings_are_immutable_redacted_and_allow_multiple_tokens(credentials):
    mapping = {
        "admin": [credentials.admin, secrets.token_urlsafe(32)],
        "viewer": [credentials.viewer],
    }
    settings = load_settings({ENVIRONMENT_KEY: json.dumps(mapping)})
    assert len(settings.bindings) == 3
    for binding in settings.bindings:
        assert binding.token not in repr(binding)
        assert binding.token not in repr(settings)
    with pytest.raises(FrozenInstanceError):
        settings.bindings = ()
    with pytest.raises(FrozenInstanceError):
        settings.bindings[0].token = "changed"
    mapping["admin"].clear()
    assert len(settings.bindings) == 3


def test_configuration_errors_do_not_echo_supplied_secret(credentials):
    raw = json.dumps({"admin": [credentials.admin], "viewer": [credentials.admin]})
    with pytest.raises(ConfigurationError) as caught:
        load_settings({ENVIRONMENT_KEY: raw})
    assert credentials.admin not in str(caught.value)
    assert credentials.admin not in repr(caught.value)


@pytest.mark.parametrize("bindings", [(), [], ({"token": "x", "role": "admin"},)])
def test_direct_configuration_construction_cannot_bypass_validation(bindings):
    with pytest.raises(ConfigurationError):
        SecuritySettings(bindings)


@pytest.mark.parametrize("token,role", [("x", "admin"), ("x", None), (True, Role.ADMIN)])
def test_binding_rejects_untrusted_roles_and_token_types(token, role):
    with pytest.raises(ConfigurationError):
        TokenBinding(token, role)
