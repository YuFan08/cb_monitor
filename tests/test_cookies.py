from pathlib import Path

import pytest

from cb_monitor.cookies import load_cookie_header, parse_netscape_cookie_file
from cb_monitor.errors import AuthRequiredError


def test_parse_netscape_cookie_file(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "\n".join(
            [
                "# Netscape HTTP Cookie File",
                ".chaturbate.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tabc",
                "#HttpOnly_.chaturbate.com\tTRUE\t/\tTRUE\t2147483647\tcsrftoken\txyz",
            ]
        ),
        encoding="utf-8",
    )

    header = parse_netscape_cookie_file(cookie_file)

    assert header == "sessionid=abc; csrftoken=xyz"


def test_load_cookie_header_prefers_direct_cookie(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        ".chaturbate.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tabc",
        encoding="utf-8",
    )

    header = load_cookie_header("direct=value", cookie_file)

    assert header == "direct=value"


def test_load_cookie_header_ignores_blank_direct_cookie(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        ".chaturbate.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tabc",
        encoding="utf-8",
    )

    header = load_cookie_header('""', cookie_file)

    assert header == "sessionid=abc"


def test_load_cookie_header_accepts_txt_path_in_cookie(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        ".chaturbate.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tabc",
        encoding="utf-8",
    )

    header = load_cookie_header(str(cookie_file), None)

    assert header == "sessionid=abc"


def test_load_cookie_header_requires_source() -> None:
    with pytest.raises(AuthRequiredError):
        load_cookie_header(None, None)
