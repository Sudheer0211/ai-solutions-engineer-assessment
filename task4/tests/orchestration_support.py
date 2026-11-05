"""T4-004 deterministic fake model adapters and manual monotonic deadlines."""

import asyncio
from collections.abc import Callable

from task4_limiter.models import ModelTokenBounds
from task4_limiter.providers import ProviderResult, ProviderStatus, TokenUsage


async def until(predicate: Callable[[], bool]) -> None:
    # Wall-clock limit is only a deadlock watchdog, never a timing assertion.
    async with asyncio.timeout(10):
        while not predicate():
            await asyncio.sleep(0)


class ManualClock:
    def __init__(self):
        self.value = 0
        self.waiters = []

    def now_ms(self):
        return self.value

    async def wait_until(self, deadline):
        future = asyncio.get_running_loop().create_future()
        entry = (deadline, future)
        self.waiters.append(entry)
        try:
            if self.value < deadline:
                await future
        finally:
            self.waiters.remove(entry)

    def advance(self, value):
        assert value >= self.value
        self.value = value
        for deadline, future in self.waiters:
            if deadline <= value and not future.done():
                future.set_result(None)

    async def waiting(self, deadline):
        await until(lambda: any(d == deadline for d, _ in self.waiters))


class FakeAttempt:
    def __init__(self, provider, text):
        self.provider = provider
        self.text = text
        self.bounds = ModelTokenBounds(
            provider.model_id, provider.input_bound, provider.output_cap, provider.counter_id
        )
        self.started = asyncio.Event()
        self.cancelled = asyncio.Event()
        self.finished = asyncio.Event()
        self.closed = asyncio.Event()

    async def execute(self):
        p = self.provider
        p.calls.append(self.text)
        p.journal.append((p.model_id, "start", self.text))
        self.started.set()
        try:
            try:
                if p.gate is not None:
                    await p.gate.wait()
            except asyncio.CancelledError:
                self.cancelled.set()
                if not p.resistant:
                    raise
                await p.finish.wait()
            if p.error is not None:
                raise p.error
            if p.raw_result is not None:
                return p.raw_result
            return ProviderResult(
                p.status, p.usage, self.text if p.status == ProviderStatus.SUCCESS else None
            )
        finally:
            p.journal.append((p.model_id, "finish", self.text))
            self.finished.set()

    async def aclose(self):
        if self.provider.close_gate is not None:
            await self.provider.close_gate.wait()
        if self.provider.close_error:
            raise RuntimeError("private adapter diagnostic")
        self.provider.journal.append((self.provider.model_id, "close", self.text))
        self.closed.set()


_DEFAULT_USAGE = TokenUsage(3, 2)


class FakeProvider:
    """Synthetic counter/cap only; makes no assertion about real-model tokenization."""

    def __init__(
        self,
        model_id="primary",
        *,
        journal=None,
        status=ProviderStatus.SUCCESS,
        usage=_DEFAULT_USAGE,
        input_bound=10,
        output_cap=10,
    ):
        self.model_id = model_id
        self.counter_id = model_id + "-synthetic-v1"
        self.status, self.usage = status, usage
        self.input_bound, self.output_cap = input_bound, output_cap
        self.journal = [] if journal is None else journal
        self.calls, self.prepared = [], []
        self.gate = self.finish = self.close_gate = None
        self.resistant = self.close_error = False
        self.error = self.prepare_error = self.raw_result = None
        self.wrong_model = self.wrong_counter = False

    def prepare(self, text):
        if self.prepare_error is not None:
            raise self.prepare_error
        attempt = FakeAttempt(self, text)
        if self.wrong_model or self.wrong_counter:
            b = attempt.bounds
            attempt.bounds = ModelTokenBounds(
                "wrong" if self.wrong_model else b.model_id,
                b.input_tokens,
                b.output_tokens,
                "wrong" if self.wrong_counter else b.counter_id,
            )
        self.prepared.append(attempt)
        return attempt
