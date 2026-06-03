"""Cookie loading helpers."""

from __future__ import annotations

from pathlib import Path

from cb_monitor.errors import AuthRequiredError

NETSCAPE_COOKIE_FIELD_COUNT = 7


def load_cookie_header(
    cookie: str | None,
    cookie_file: Path | None,
    *,
    cf_clearance: str | None = None,
) -> str:
    """Load a Cookie header from direct text or a Netscape cookies.txt file."""
    if cookie:
        normalized = cookie.strip().strip("\"'")
        if _has_cookie_pairs(normalized):
            return _merge_cf_clearance(normalized, cf_clearance)
        if _looks_like_cookie_file(normalized):
            return _merge_cf_clearance(
                parse_netscape_cookie_file(Path(normalized)), cf_clearance
            )
    if cookie_file is None:
        msg = "请设置 CB_COOKIE 或 CB_COOKIE_FILE。"
        raise AuthRequiredError(msg)
    return _merge_cf_clearance(parse_netscape_cookie_file(cookie_file), cf_clearance)


def parse_netscape_cookie_file(path: Path) -> str:
    """Parse Netscape cookies.txt into a browser-style Cookie header."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        msg = f"Cookie 文件不存在: {path}"
        raise AuthRequiredError(msg) from exc
    except OSError as exc:
        msg = f"Cookie 文件读取失败: {exc.strerror or exc}"
        raise AuthRequiredError(msg) from exc

    pairs = [
        f"{name}={value}"
        for line in lines
        if (parts := _parse_netscape_line(line)) is not None
        for name, value in [parts]
    ]

    if not pairs:
        msg = "Cookie 文件中没有解析到有效 Cookie。"
        raise AuthRequiredError(msg)

    return "; ".join(pairs)


def _parse_netscape_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("#") and not stripped.startswith("#HttpOnly_"):
        return None
    if stripped.startswith("#HttpOnly_"):
        stripped = stripped.removeprefix("#HttpOnly_")

    parts = stripped.split("\t")
    if len(parts) != NETSCAPE_COOKIE_FIELD_COUNT:
        return None

    name = parts[5].strip()
    value = parts[6].strip()
    if not name or not value:
        return None
    return (name, value)


def _has_cookie_pairs(cookie: str) -> bool:
    return any(
        "=" in part and part.split("=", maxsplit=1)[0].strip()
        for part in cookie.split(";")
    )


def _looks_like_cookie_file(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    return path.suffix.lower() == ".txt" or path.exists()


def _merge_cf_clearance(cookie_header: str, cf_clearance: str | None) -> str:
    token = cf_clearance.strip().strip("\"'") if cf_clearance is not None else ""
    if not token:
        return cookie_header

    pairs = [
        part.strip()
        for part in cookie_header.split(";")
        if part.strip()
        and part.split("=", maxsplit=1)[0].strip().lower() != "cf_clearance"
    ]
    pairs.append(f"cf_clearance={token}")
    return "; ".join(pairs)
