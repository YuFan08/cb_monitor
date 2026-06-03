from cb_monitor.playlist import parse_stream_variants


def test_parse_stream_variants_sorts_by_quality() -> None:
    playlist = """#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=854x480,CODECS="avc1"
480/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1920x1080,CODECS="avc1"
1080/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=1280x720,CODECS="avc1"
720/index.m3u8
"""

    variants = parse_stream_variants(playlist, "https://example.com/master.m3u8")

    assert [variant.label for variant in variants] == ["1080p", "720p", "480p"]
    assert str(variants[0].url) == "https://example.com/1080/index.m3u8"


def test_parse_media_playlist_as_source() -> None:
    playlist = """#EXTM3U
#EXT-X-TARGETDURATION:4
#EXTINF:4.0,
segment.ts
"""

    variants = parse_stream_variants(playlist, "https://example.com/source.m3u8")

    assert len(variants) == 1
    assert variants[0].label == "source"
