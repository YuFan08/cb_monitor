"""Room page stream discovery."""

from __future__ import annotations

import html
import json
import re
from urllib.parse import unquote

from cb_monitor.errors import RoomOfflineError
from cb_monitor.http_client import HttpClient
from cb_monitor.models import MasterPlaylist, Streamer

M3U8_RE = re.compile(r"https?:\\?/\\?/[^\"'<\s]+?\.m3u8[^\"'<\s]*")


async def fetch_master_playlist(
    client: HttpClient, streamer: Streamer
) -> MasterPlaylist:
    """Fetch a room page and return the first discovered master playlist."""
    page = await client.get_text(str(streamer.room_url), use_system_proxy=True)
    return parse_master_playlist(page)


def parse_master_playlist(room_html: str) -> MasterPlaylist:
    """Extract a playable m3u8 URL from a room HTML document."""
    for raw_url in M3U8_RE.findall(room_html):
        url = _clean_url(raw_url)
        if ".m3u8" in url:
            return MasterPlaylist(url=url)

    msg = "主播正在进行 Private Show 或者 Cam Hidden"
    raise RoomOfflineError(msg)


def _clean_url(raw_url: str) -> str:
    unescaped = _decode_javascript_string(html.unescape(raw_url))
    return unquote(unescaped).rstrip('\\",')


def _decode_javascript_string(value: str) -> str:
    try:
        decoded = json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace("\\/", "/")
    return decoded if isinstance(decoded, str) else value
