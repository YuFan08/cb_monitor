import httpx
import pytest

from cb_monitor.errors import CloudflareChallengeError
from cb_monitor.http_client import HttpClient


@pytest.mark.asyncio
async def test_get_text_raises_cloudflare_challenge_on_403() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            403,
            request=request,
            text="<title>Just a moment...</title>",
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as async_client:
        client = HttpClient(
            client=async_client,
            retry_attempts=3,
            headers={},
            timeout=httpx.Timeout(1.0),
        )

        with pytest.raises(CloudflareChallengeError):
            await client.get_text("https://chaturbate.com/followed-cams/")

    assert calls == 1


@pytest.mark.asyncio
async def test_get_text_sends_extra_headers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            json={"accept": request.headers["accept"]},
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
    ) as async_client:
        client = HttpClient(
            client=async_client,
            retry_attempts=1,
            headers={},
            timeout=httpx.Timeout(1.0),
        )

        text = await client.get_text(
            "https://chaturbate.com/api/ts/roomlist/room-list/",
            extra_headers={"accept": "application/json, text/plain, */*"},
        )

    assert "application/json" in text
