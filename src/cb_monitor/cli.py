"""Command line interface."""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import Awaitable, Sequence
from dataclasses import dataclass
from datetime import datetime

import httpx
import questionary
from loguru import logger
from pydantic import ValidationError

from cb_monitor.config import Settings
from cb_monitor.errors import CbMonitorError
from cb_monitor.followed import fetch_followed_streamers
from cb_monitor.http_client import HttpClient, create_http_client
from cb_monitor.logging import configure_logging
from cb_monitor.models import Streamer, StreamVariant
from cb_monitor.player import launch_mpv
from cb_monitor.playlist import fetch_stream_variants
from cb_monitor.room import fetch_master_playlist

STREAMER_REFRESH_SECONDS = 600.0


@dataclass(frozen=True, slots=True)
class QuitAction:
    """User requested application exit."""


@dataclass(frozen=True, slots=True)
class BackAction:
    """User requested returning to the previous menu."""


@dataclass(frozen=True, slots=True)
class RefreshAction:
    """Streamer list selection timed out and should refresh."""


StreamerSelection = Streamer | QuitAction | RefreshAction
VariantSelection = StreamVariant | BackAction | QuitAction

QUIT = QuitAction()
BACK = BackAction()
REFRESH = RefreshAction()
MENU_STYLE = questionary.Style(
    [
        ("answer", "fg:#00d75f bold"),
        ("highlighted", "fg:#00ff87 bold"),
        ("instruction", "fg:#8a8a8a"),
        ("pointer", "fg:#00d75f bold"),
        ("selected", "fg:#00ff87 bold"),
        ("text", "fg:#00d75f"),
    ]
)


def main() -> None:
    """Run the CLI application."""
    asyncio.run(_main_async())


async def _main_async() -> None:
    try:
        settings = Settings()  # pyright: ignore[reportCallIssue]
    except ValidationError as exc:
        configure_logging("ERROR")
        logger.error("配置无效: 请确认 .env 中已设置 CB_COOKIE。")
        logger.debug("Pydantic validation details: {}", exc)
        return

    configure_logging(settings.log_level, settings.log_file)

    try:
        async with create_http_client(settings) as client:
            while True:
                _clear_screen()
                streamers = await _load_streamers(
                    client,
                    settings.base_url,
                    settings.followed_path,
                )
                selection = await _choose_streamer(
                    streamers, refreshed_at=datetime.now().astimezone()
                )
                if isinstance(selection, QuitAction):
                    logger.info("已退出。")
                    return
                if isinstance(selection, RefreshAction):
                    logger.info("超过 10 分钟未选择, 正在刷新主播列表...")
                    continue

                streamer = selection
                logger.info("正在解析直播流: {}", streamer.username)
                try:
                    playlist = await fetch_master_playlist(client, streamer)
                    variants = await fetch_stream_variants(client, playlist)
                except CbMonitorError as exc:
                    logger.error("{}", exc)
                    continue
                except httpx.HTTPError as exc:
                    logger.error("网络请求失败: {}", exc)
                    continue

                _clear_screen()
                variant = await _choose_variant(variants)
                if isinstance(variant, QuitAction):
                    logger.info("已退出。")
                    return
                if isinstance(variant, BackAction):
                    continue

                logger.opt(ansi=True).success(
                    "马上开始播放 <green>{}</green>",
                    _play_label(variant),
                )
                logger.info("正在启动 mpv...")
                launch_mpv(settings.mpv_path, variant)
    except CbMonitorError as exc:
        logger.error("{}", exc)
    except httpx.HTTPStatusError as exc:
        logger.error("HTTP {}: {}", exc.response.status_code, exc.request.url)
    except httpx.HTTPError as exc:
        logger.error("网络请求失败: {}", exc)
    except KeyboardInterrupt:
        logger.warning("已取消。")


async def _load_streamers(
    client: HttpClient,
    base_url: str,
    followed_path: str,
) -> list[Streamer]:
    logger.info("正在读取关注主播...")
    streamers = await fetch_followed_streamers(client, base_url, followed_path)
    logger.success("发现 {} 个在线关注主播", len(streamers))
    return streamers


async def _choose_streamer(
    streamers: Sequence[Streamer],
    *,
    refreshed_at: datetime,
) -> StreamerSelection:
    number_width = len(str(len(streamers)))
    deadline = time.monotonic() + STREAMER_REFRESH_SECONDS
    logger.opt(ansi=True).info("请选择主播: <green>方向键选择, Enter 确认</green>")
    choices = [
        questionary.Choice(
            title=_indexed_title(index, streamer.username, number_width),
            value=streamer,
        )
        for index, streamer in enumerate(streamers, start=1)
    ]
    choices.append(
        questionary.Choice(
            title=_menu_action_title("手动刷新列表", number_width),
            value=REFRESH,
        )
    )
    choices.append(
        questionary.Choice(title=_menu_action_title("退出", number_width), value=QUIT)
    )
    selected = await _ask_with_timeout(
        questionary.select(
            _refresh_message(refreshed_at, number_width),
            choices=choices,
            qmark="",
            style=MENU_STYLE,
            erase_when_done=True,
            instruction=" ",
            rprompt=lambda: _countdown_toolbar(deadline),
            refresh_interval=1.0,
        ).ask_async(),
        timeout_seconds=STREAMER_REFRESH_SECONDS,
    )
    if isinstance(selected, RefreshAction | QuitAction):
        return selected
    if not isinstance(selected, Streamer):
        msg = "未选择主播。"
        raise CbMonitorError(msg)
    return selected


async def _choose_variant(variants: Sequence[StreamVariant]) -> VariantSelection:
    number_width = len(str(len(variants)))
    logger.opt(ansi=True).info("请选择清晰度: <green>方向键选择, Enter 确认</green>")
    choices = [
        questionary.Choice(
            title=_indexed_title(index, _variant_title(variant), number_width),
            value=variant,
        )
        for index, variant in enumerate(variants, start=1)
    ]
    choices.extend(
        [
            questionary.Choice(
                title=_menu_action_title("返回主播列表", number_width),
                value=BACK,
            ),
            questionary.Choice(
                title=_menu_action_title("退出", number_width),
                value=QUIT,
            ),
        ]
    )
    selected = await questionary.select(
        "",
        choices=choices,
        qmark="",
        style=MENU_STYLE,
        erase_when_done=True,
        instruction=" ",
    ).ask_async()
    if isinstance(selected, BackAction | QuitAction):
        return selected
    if not isinstance(selected, StreamVariant):
        msg = "未选择清晰度。"
        raise CbMonitorError(msg)
    return selected


async def _ask_with_timeout(
    awaitable: Awaitable[object],
    *,
    timeout_seconds: float,
) -> object:
    try:
        return await asyncio.wait_for(awaitable, timeout=timeout_seconds)
    except TimeoutError:
        return REFRESH


def _indexed_title(index: int, text: str, number_width: int) -> str:
    return f"{index:>{number_width}}. {text}"


def _menu_action_title(text: str, number_width: int) -> str:
    return f"{'':>{number_width}}  {text}"


def _countdown_toolbar(deadline: float) -> str:
    remaining = max(0, round(deadline - time.monotonic()))
    minutes, seconds = divmod(remaining, 60)
    return f"自动刷新倒计时: {minutes:02d}:{seconds:02d}"


def _refresh_message(refreshed_at: datetime, number_width: int) -> str:
    indent = " " * (number_width + 1)
    return f"{indent}本次刷新时间: {refreshed_at:%H:%M:%S}"


def _variant_title(variant: StreamVariant) -> str:
    bitrate = f" · {variant.bandwidth // 1000} kbps" if variant.bandwidth else ""
    size = (
        f" · {variant.width}x{variant.height}"
        if variant.width and variant.height
        else ""
    )
    return f"{variant.label}{size}{bitrate}"


def _play_label(variant: StreamVariant) -> str:
    return variant.label.upper()


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
