"""Only new async tests isolate the process-global counter; no production override."""

import pytest


@pytest.fixture(autouse=True)
def isolated_async_capacity(request, monkeypatch):
    if request.module.__name__ in {"tests.test_service", "tests.test_upstream"}:
        from task3_streaming import service

        monkeypatch.setattr(service, "_PROCESS_CAPACITY", service.Capacity())
