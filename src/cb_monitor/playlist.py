"""HLS master playlist parsing."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from cb_monitor.errors import PlaylistParseError
from cb_monitor.http_client import HttpClient
from cb_monitor.models import MasterPlaylist, StreamVariant

ATTRIBUTE_RE = re.compile(r'([A-Z0-9-]+)=("[^"]*"|[^,]*)')
RESOLUTION_RE = re.compile(r"(?P<width>\d+)x(?P<height>\d+)")


async def fetch_stream_variants(
    client: HttpClient,
    playlist: MasterPlaylist,
) -> list[StreamVariant]:
    """Fetch and parse stream variants from a master playlist."""
    text = await client.get_text(str(playlist.url), use_system_proxy=True)
    return parse_stream_variants(text, str(playlist.url))


def parse_stream_variants(playlist_text: str, playlist_url: str) -> list[StreamVariant]:
    """Parse HLS stream variants sorted from highest to lowest quality."""
    lines = [line.strip() for line in playlist_text.splitlines() if line.strip()]
    variants: list[StreamVariant] = []

    for index, line in enumerate(lines):
        if not line.startswith("#EXT-X-STREAM-INF:"):
            continue
        if index + 1 >= len(lines):
            continue

        uri = lines[index + 1]
        if uri.startswith("#"):
            continue

        attrs = _parse_attributes(line.removeprefix("#EXT-X-STREAM-INF:"))
        width, height = _parse_resolution(attrs.get("RESOLUTION"))
        bandwidth = _parse_positive_int(attrs.get("BANDWIDTH"))
        label = _build_label(height=height, bandwidth=bandwidth)

        variants.append(
            StreamVariant(
                label=label,
                url=urljoin(playlist_url, uri),
                bandwidth=bandwidth,
                width=width,
                height=height,
                codecs=_strip_quotes(attrs.get("CODECS")),
            )
        )

    if not variants and "#EXTM3U" in playlist_text:
        variants.append(StreamVariant(label="source", url=playlist_url))

    if not variants:
        msg = "m3u8 清晰度列表解析失败。"
        raise PlaylistParseError(msg)

    return sorted(variants, key=lambda variant: variant.sort_key, reverse=True)


def _parse_attributes(raw: str) -> dict[str, str]:
    return dict(ATTRIBUTE_RE.findall(raw))


def _parse_resolution(value: str | None) -> tuple[int | None, int | None]:
    if value is None:
        return (None, None)
    match = RESOLUTION_RE.fullmatch(value)
    if match is None:
        return (None, None)
    return (int(match.group("width")), int(match.group("height")))


def _parse_positive_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _build_label(*, height: int | None, bandwidth: int | None) -> str:
    if height is not None:
        return f"{height}p"
    if bandwidth is not None:
        return f"{bandwidth // 1000} kbps"
    return "source"


def _strip_quotes(value: str | None) -> str | None:
    return value.strip('"') if value is not None else None
