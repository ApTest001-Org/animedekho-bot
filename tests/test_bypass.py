"""V2 #23: /bypass resolver tests — one success/failure case per website.

Offline where possible (detection, validation, quality parsing); network
fetch is mocked so CI stays deterministic.
"""

import asyncio

from extractors.bypass import (
    detect_source,
    _detect_quality_from_text,
    _parse_title_season_episode,
    resolve_bypass_url,
)


def test_detect_source_all_supported():
    cases = {
        "https://www.animedubhindi.link/jojos-bizarre-adventure-season-1-hindi-multi-audio/": "AnimeDubHindi",
        "https://new.adhlinks.com/episode/jojos-bizarre-adventure-s1/": "AnimeDubHindi",
        "https://toonworld4all.me/hanaori-san-still-wants-to-fight-in-the-next-life-season-1-multi-audio-hindi/": "ToonWorld4All",
        "https://archive.toonworld4all.me/episode/hanaori-san-still-wants-to-fight-in-the-next-life-1x10": "ToonWorld4All",
        "https://toonanime.tv/naruto-season-1-hindi/": "ToonAnime",
        "https://www.rareanimes.mov/naruto-hindi/": "RareAnimes",
        "https://deadtoons.sbs/search?q=naruto": "DeadToons",
        "https://toono.app/?s=naruto": "TOONo",
        "https://animedrive.cc/naruto-s1/": "AnimeDrive",
        "https://toonflix.in/naruto-s1/": "ToonFlix",
    }
    for url, expected in cases.items():
        assert detect_source(url) == expected, url


def test_detect_source_unsupported():
    assert detect_source("https://example.com/some-video") is None
    assert detect_source("not-a-url") is None


def test_quality_detection():
    assert _detect_quality_from_text("movie_1080p.mp4 1080p") == "1080p"
    assert _detect_quality_from_text("EP 720p x265") == "720p"
    assert _detect_quality_from_text("UHD 2160p WEB-DL") == "4K"
    assert _detect_quality_from_text("no quality here") == ""


def test_title_season_episode_parse():
    anime, s, e = _parse_title_season_episode(
        "https://archive.toonworld4all.me/episode/hanaori-san-still-wants-to-fight-in-the-next-life-1x10"
    )
    assert "Hanaori" in anime
    assert (s, e) == (1, 10)


def test_resolve_unsupported_source():
    res = asyncio.run(resolve_bypass_url("https://example.com/video/123"))
    assert res["ok"] is False
    assert "Unsupported Source" in res["error"]


def test_resolve_invalid_url():
    res = asyncio.run(resolve_bypass_url("not-a-url"))
    assert res["ok"] is False


def test_resolve_rejects_html_as_media(monkeypatch):
    """An HTML page must never be reported as a 480p media URL."""
    from extractors import bypass as bp

    async def fake_fetch(url):
        html = (
            "<html><head><title>Naruto Season 1</title></head><body>"
            "<a href='https://toonworld4all.me/naruto-season-1/'>480p Download Page</a>"
            "</body></html>"
        )
        return url, html

    async def fake_bypass(u):
        return u

    monkeypatch.setattr(bp, "_fetch_public", fake_fetch)
    import extractors.shortener as sh
    monkeypatch.setattr(sh, "detect_and_bypass", fake_bypass)
    # is_valid_media_destination must reject the HTML page URL
    res = asyncio.run(
        resolve_bypass_url("https://toonworld4all.me/naruto-season-1-hindi/")
    )
    assert res["ok"] is False  # no real media on the fake page
    for m in res.get("media_links", []):
        assert ".mp4" in m["url"] or ".m3u8" in m["url"] or ".mkv" in m["url"]
