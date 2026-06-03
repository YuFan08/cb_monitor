"""Async HTTP client with retries and timeouts."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import getproxies

import httpx
from loguru import logger
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from cb_monitor.config import Settings
from cb_monitor.cookies import load_cookie_header


@dataclass(frozen=True, slots=True)
class HttpClient:
    """Small wrapper around httpx.AsyncClient."""

    client: httpx.AsyncClient
    retry_attempts: int
    headers: dict[str, str]
    timeout: httpx.Timeout

    async def get_text(self, url: str, *, use_system_proxy: bool = False) -> str:
        """Fetch text with retry on transient HTTP failures."""
        retrying = AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
            retry=retry_if_exception_type(
                (
                    httpx.ConnectError,
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.RemoteProtocolError,
                    httpx.HTTPStatusError,
                )
            ),
        )

        async for attempt in retrying:
            with attempt:
                logger.debug("HTTP GET {}", _safe_url(url))
                response = await self._get(url, use_system_proxy=use_system_proxy)
                response.raise_for_status()
                return response.text

        msg = f"Request retry loop exited unexpectedly: {url}"
        raise httpx.RequestError(msg)

    async def _get(self, url: str, *, use_system_proxy: bool) -> httpx.Response:
        if not use_system_proxy:
            return await self.client.get(url)

        proxy = _system_proxy_for_url(url)
        if proxy is None:
            logger.warning("未检测到系统代理, 将直接请求: {}", _safe_url(url))
            return await self.client.get(url)

        logger.debug("使用系统代理请求: {}", _safe_url(url))
        async with httpx.AsyncClient(
            headers=self.headers,
            timeout=self.timeout,
            follow_redirects=True,
            proxy=proxy,
        ) as proxy_client:
            return await proxy_client.get(url)


@asynccontextmanager
async def create_http_client(settings: Settings) -> AsyncGenerator[HttpClient]:
    """Create a configured async HTTP client."""
    cookie_header = load_cookie_header(
        settings.cookie.get_secret_value() if settings.cookie is not None else None,
        settings.cookie_file,
    )
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "cookie": cookie_header,
        "pragma": "no-cache",
        "referer": f"{settings.base_url}{settings.followed_path}",
        "upgrade-insecure-requests": "1",
        "user-agent": settings.user_agent,
    }
    timeout = httpx.Timeout(settings.timeout_seconds)

    async with httpx.AsyncClient(
        headers=headers,
        timeout=timeout,
        follow_redirects=True,
    ) as client:
        yield HttpClient(
            client=client,
            retry_attempts=settings.retry_attempts,
            headers=headers,
            timeout=timeout,
        )


def _system_proxy_for_url(url: str) -> str | None:
    proxies = getproxies()
    scheme = urlsplit(url).scheme.lower()
    proxy = proxies.get(scheme) or proxies.get("all")
    if proxy is None and scheme == "https":
        proxy = proxies.get("http")
    return proxy


def _safe_url(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url

    query = urlencode(
        [
            (key, "***" if key.lower() in {"token", "auth", "sig"} else value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
