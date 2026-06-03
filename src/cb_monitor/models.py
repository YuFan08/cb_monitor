"""Validated domain models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator


class Streamer(BaseModel):
    """A followed streamer parsed from the followed-cams page."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    username: str = Field(min_length=1, max_length=64)
    room_url: str = Field(pattern=r"^https://.+")

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Normalize room usernames because page text often includes badges."""
        return value.strip().strip("/").lower()


class MasterPlaylist(BaseModel):
    """A discovered HLS master playlist URL."""

    model_config = ConfigDict(frozen=True)

    url: str = Field(pattern=r"^https?://.+\.m3u8(?:\?.*)?$")


class StreamVariant(BaseModel):
    """A playable HLS variant."""

    model_config = ConfigDict(frozen=True)

    label: str = Field(min_length=1, max_length=64)
    url: str = Field(pattern=r"^https?://.+")
    bandwidth: PositiveInt | None = None
    width: PositiveInt | None = None
    height: PositiveInt | None = None
    codecs: str | None = None

    @property
    def sort_key(self) -> tuple[int, int]:
        """Sort by quality first, then bitrate."""
        return (self.height or 0, self.bandwidth or 0)
