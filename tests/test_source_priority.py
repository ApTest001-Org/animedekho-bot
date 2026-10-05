"""Offline regression tests for deterministic fallback-source selection."""

import asyncio


def test_priority_order_and_priority_beats_fastest(monkeypatch):
    from extractors import multisource as module

    class FakeExtractor:
        def __init__(self, url):
            self.url = url

        async def resolve_episode(self, **_kwargs):
            return {
                "url": self.url,
                "quality": "1080p",
                "detected_quality": "1080p",
                "verified_quality": "1080p",
            }

    manager = module.MultiSourceManager()
    assert [name for name, _ in manager.sources[:4]] == [
        "AnimeDubHindi", "RareAnimes", "ToonWorld4All", "DeadToons"
    ]
    # Deliberately put the lower-priority provider on a URL that would be
    # considered first by a latency-only selector.
    manager.sources = [
        ("AnimeDubHindi", FakeExtractor("https://cdn.example/high.mp4")),
        ("RareAnimes", FakeExtractor("https://cdn.example/fast.mp4")),
    ]

    async def first_candidate(candidates, **_kwargs):
        return candidates[0], [{"source": candidates[0]["source"], "status": "Unprobed"}]

    monkeypatch.setattr(module, "select_fastest_healthy", first_candidate, raising=False)
    # The manager imports this function inside resolve_episode_stream, so patch
    # the health module as well.
    import extractors.health_probe as health_probe
    monkeypatch.setattr(health_probe, "select_fastest_healthy", first_candidate)

    result = asyncio.run(manager.resolve_episode_stream("Example", 1, 1, "1080p"))
    assert result is not None
    assert result["source"] == "AnimeDubHindi"
    assert result["url"].endswith("high.mp4")


def test_provider_error_falls_through_to_next_source(monkeypatch):
    from extractors import multisource as module
    import extractors.health_probe as health_probe

    class Broken:
        async def resolve_episode(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    class Working:
        async def resolve_episode(self, **_kwargs):
            return {"url": "https://cdn.example/fallback.mp4", "quality": "1080p"}

    async def first_candidate(candidates, **_kwargs):
        return candidates[0], []

    monkeypatch.setattr(health_probe, "select_fastest_healthy", first_candidate)
    manager = module.MultiSourceManager()
    manager.sources = [("AnimeDubHindi", Broken()), ("RareAnimes", Working())]
    result = asyncio.run(manager.resolve_episode_stream("Example", 1, 1, "1080p"))
    assert result is not None
    assert result["source"] == "RareAnimes"


def test_variant_selection_is_exact_only():
    from extractors.multisource import _choose_resolved_variant

    resolved = {
        "url": "https://cdn.example/master.m3u8",
        "qualities": [
            {"resolution": "720p", "url": "https://cdn.example/720.m3u8"},
            {"resolution": "1080p", "url": "https://cdn.example/1080.m3u8"},
        ],
    }
    assert _choose_resolved_variant(resolved, "1080p") == (
        "https://cdn.example/1080.m3u8", "1080p"
    )
    assert _choose_resolved_variant(resolved, "4K") is None


def test_relative_urls_and_season_safe_episode_matching():
    from utils.anime_match import matches_episode, normalize_provider_url

    assert normalize_provider_url("../episode/1x02", "https://rareanimes.mov/posts/show/") == (
        "https://rareanimes.mov/posts/episode/1x02"
    )
    assert normalize_provider_url("/episode/1x02", "https://deadtoons.sbs/posts/show") == (
        "https://deadtoons.sbs/episode/1x02"
    )
    assert matches_episode("Episode 01", "https://x.example/download", 1, 1)
    assert not matches_episode("S2E01", "https://x.example/download", 1, 1)
    assert matches_episode("", "https://x.example/show-2x01", 2, 1)
    assert not matches_episode("", "https://x.example/show-2x01", 1, 1)


def test_provider_pages_are_not_download_destinations():
    from extractors.multisource import _is_provider_catalog_page
    from extractors.shortener import is_valid_media_destination

    page = "https://www.rareanimes.mov/posts/example-season-1/"
    assert _is_provider_catalog_page("RareAnimes", page)
    assert not is_valid_media_destination(page)
    assert is_valid_media_destination("https://cdn.example/files/episode-1.mp4")
    assert not is_valid_media_destination("not-a-url")
