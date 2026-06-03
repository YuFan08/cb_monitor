import pytest

from cb_monitor.errors import AuthRequiredError
from cb_monitor.followed import ensure_authenticated, parse_followed_roomlist


def test_parse_followed_roomlist_from_api_json() -> None:
    api_text = """
    {
      "rooms": [
        {"username": "xxx_leila", "is_following": true},
        {"username": "lovepill", "is_following": true}
      ]
    }
    """

    streamers = parse_followed_roomlist(api_text, "https://chaturbate.com")

    assert [streamer.username for streamer in streamers] == ["xxx_leila", "lovepill"]
    assert streamers[0].room_url == "https://chaturbate.com/xxx_leila/"


def test_ensure_authenticated_rejects_login_page() -> None:
    with pytest.raises(AuthRequiredError):
        ensure_authenticated('<form id="login_form"></form>')
