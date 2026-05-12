import asyncio
from types import SimpleNamespace

from queue_svc.bazos_api import auto_bazos_api


def _mock_sleep(monkeypatch, sleep_func_name: str):
    current_time = [1000.0]
    sleep_calls = []

    monkeypatch.setattr(auto_bazos_api.time, "monotonic", lambda: current_time[0])

    if sleep_func_name == "sleep":
        def fake_sleep(seconds):
            sleep_calls.append(seconds)
            current_time[0] += seconds

        monkeypatch.setattr(auto_bazos_api.time, "sleep", fake_sleep)
    else:
        async def fake_sleep(seconds):
            sleep_calls.append(seconds)
            current_time[0] += seconds

        monkeypatch.setattr(auto_bazos_api.asyncio, "sleep", fake_sleep)

    return sleep_calls


def test_get_waits_after_request_limit(monkeypatch):
    sleep_calls = _mock_sleep(monkeypatch, "sleep")
    requested_links = []
    monkeypatch.setattr(
        auto_bazos_api,
        "_request_rate_limiter",
        auto_bazos_api._RequestRateLimiter(request_limit=2, pause_seconds=30),
    )

    def fake_get(link):
        requested_links.append(link)
        return SimpleNamespace(status_code=200, text="ok")

    monkeypatch.setattr(auto_bazos_api.requests, "get", fake_get)

    for index in range(3):
        assert auto_bazos_api.get(f"https://example.com/{index}") == "ok"

    assert sleep_calls == [30]
    assert requested_links == [
        "https://example.com/0",
        "https://example.com/1",
        "https://example.com/2",
    ]


def test_aget_waits_while_pause_is_active(monkeypatch):
    current_time = [1000.0]
    sleep_calls = []
    original_sleep = asyncio.sleep

    monkeypatch.setattr(auto_bazos_api.time, "monotonic", lambda: current_time[0])

    async def fake_sleep(seconds):
        sleep_calls.append(seconds)
        await original_sleep(0)
        current_time[0] += seconds

    monkeypatch.setattr(auto_bazos_api.asyncio, "sleep", fake_sleep)
    limiter = auto_bazos_api._RequestRateLimiter(request_limit=2, pause_seconds=30)

    async def run_requests():
        await limiter.await_wait()
        await limiter.await_wait()

        paused_request = asyncio.create_task(limiter.await_wait())
        await original_sleep(0)

        await limiter.await_wait()
        await paused_request

    asyncio.run(run_requests())

    assert sleep_calls == [30, 30]


def test_aget_waits_after_request_limit(monkeypatch):
    sleep_calls = _mock_sleep(monkeypatch, "async_sleep")
    requested_links = []
    monkeypatch.setattr(
        auto_bazos_api,
        "_request_rate_limiter",
        auto_bazos_api._RequestRateLimiter(request_limit=2, pause_seconds=30),
    )

    class FakeResponse:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            pass

        async def text(self):
            return "ok"

    class FakeSession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            pass

        def get(self, link):
            requested_links.append(link)
            return FakeResponse()

    monkeypatch.setattr(auto_bazos_api.aiohttp, "ClientSession", FakeSession)

    async def run_requests():
        for index in range(3):
            text = await auto_bazos_api.aget(f"https://example.com/{index}")
            assert text == "ok"

    asyncio.run(run_requests())

    assert sleep_calls == [30]
    assert requested_links == [
        "https://example.com/0",
        "https://example.com/1",
        "https://example.com/2",
    ]
