"""Followed cams page parsing."""

from __future__ import annotations

import json
from collections.abc import Iterable
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from cb_monitor.errors import AuthRequiredError, EmptyFollowedListError
from cb_monitor.http_client import HttpClient
from cb_monitor.models import Streamer

FOLLOWED_ROOMLIST_PATH = "/api/ts/roomlist/room-list/?follow=true&limit=90&offset=0"


class FollowedRoom(BaseModel):
    """A room entry returned by Chaturbate's room-list API."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=64)
    current_show: str | None = None
    is_following: bool = True


class FollowedRoomList(BaseModel):
    """Room-list API response."""

    model_config = ConfigDict(extra="ignore")

    rooms: list[FollowedRoom]


async def fetch_followed_streamers(
    client: HttpClient, base_url: str, path: str
) -> list[Streamer]:
    """Fetch and parse live followed streamers."""
    html = await client.get_text(urljoin(base_url, path))
    ensure_authenticated(html)

    api_text = await client.get_text(urljoin(base_url, FOLLOWED_ROOMLIST_PATH))
    return parse_followed_roomlist(api_text, base_url)


def parse_followed_roomlist(api_text: str, base_url: str) -> list[Streamer]:
    """Parse followed live room data from the room-list API JSON response."""
    try:
        payload = json.loads(api_text)
        room_list = FollowedRoomList.model_validate(payload)
    except json.JSONDecodeError as exc:
        msg = "关注主播 API 返回了非 JSON 响应。"
        raise EmptyFollowedListError(msg) from exc
    except ValidationError as exc:
        msg = "关注主播 API 数据结构解析失败。"
        raise EmptyFollowedListError(msg) from exc

    streamers = _unique_streamers(
        Streamer(
            username=room.username,
            room_url=urljoin(base_url, f"/{room.username}/"),
        )
        for room in room_list.rooms
        if room.is_following
    )

    if not streamers:
        msg = "未解析到正在直播的关注主播。"
        raise EmptyFollowedListError(msg)
    return streamers


def ensure_authenticated(html: str) -> None:
    """Fail fast when the followed page is actually a login page."""
    if "/auth/login" in html or 'id="login_form"' in html:
        msg = "登录 Cookie 缺失或已失效, 请更新 CB_COOKIE。"
        raise AuthRequiredError(msg)


def _unique_streamers(streamers: Iterable[Streamer]) -> list[Streamer]:
    seen: set[str] = set()
    result: list[Streamer] = []

    for streamer in streamers:
        if streamer.username in seen:
            continue
        seen.add(streamer.username)
        result.append(streamer)

    return result
