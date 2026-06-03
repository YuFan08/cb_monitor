from cb_monitor.room import parse_master_playlist


def test_parse_master_playlist_from_escaped_room_html() -> None:
    page = r"""
    <script>
    window.initialRoomDossier = {
        "hls_source": "https:\/\/edge.example.test\/hls\/master.m3u8?token=abc"
    };
    </script>
    """

    playlist = parse_master_playlist(page)

    assert str(playlist.url) == "https://edge.example.test/hls/master.m3u8?token=abc"


def test_parse_master_playlist_decodes_unicode_escapes() -> None:
    page = r"""
    <script>
    window.initialRoomDossier = {
        "hls_source": "https:\/\/edge2\u002Dlax.example.test\/hls\/master.m3u8"
    };
    </script>
    """

    playlist = parse_master_playlist(page)

    assert playlist.url == "https://edge2-lax.example.test/hls/master.m3u8"


def test_parse_master_playlist_strips_captured_js_quote_tail() -> None:
    page = r"""
    <script>
    const source = "https:\/\/edge.example.test\/hls\/master.m3u8?token=abc\",";
    </script>
    """

    playlist = parse_master_playlist(page)

    assert playlist.url == "https://edge.example.test/hls/master.m3u8?token=abc"
