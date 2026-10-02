"""Multi-Source Fallback Architecture — orchestrates primary and fallback scrapers."""

from __future__ import annotations
import asyncio
import logging
import re
from typing import TYPE_CHECKING

from api.models import SearchResult
from utils.helpers import clean_title, slug_to_title
from extractors.animedrive import animedrive
from extractors.toonflix import toonflix
from extractors.rareanimes import rareanimes
from extractors.deadtoons import deadtoons
from extractors.toonworld4all import toonworld4all
from extractors.toono import toono
from extractors.resolver import resolve_player_url

log = logging.getLogger(__name__)


class MultiSourceManager:
    """Manages secondary, tertiary, and fallback sources so the bot never reports false 'Not Found' errors."""

    def __init__(self):
        self.sources = [
            ("RareAnimes", rareanimes),
            ("ToonWorld4All", toonworld4all),
            ("DeadToons", deadtoons),
            ("TOONo", toono),
            ("AnimeDrive", animedrive),
            ("ToonFlix", toonflix),
        ]

    async def search_fallback(self, query: str) -> list[SearchResult]:
        """Search fallback sources when primary AnimeDekho returns 0 results."""
        results: list[SearchResult] = []
        seen_slugs = set()

        for name, extractor in self.sources:
            try:
                raw_items = await extractor.search(query)
                if not raw_items:
                    continue

                for item in raw_items:
                    raw_title = item.get("title", "")
                    title = clean_title(raw_title) or raw_title
                    url = item.get("url", "")
                    poster = item.get("poster", "")

                    # Generate clean slug
                    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
                    if not slug or slug in seen_slugs:
                        continue
                    seen_slugs.add(slug)

                    is_movie = "movie" in title.lower() or "film" in title.lower()
                    results.append(SearchResult(
                        title=f"{title} [{name}]",
                        slug=slug,
                        url=url,
                        content_type="movie" if is_movie else "series",
                        poster=poster,
                    ))

                if len(results) >= 10:
                    break
            except Exception as e:
                log.warning("Fallback search on %s failed for '%s': %s", name, query, e)

        return results

    async def resolve_episode_stream(
        self,
        series_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
        series_slug: str = "",
    ) -> dict | None:
        """
        Iterate through fallback scrapers to resolve an episode stream.
        Never fails prematurely if an episode exists on another source!
        """
        clean_title = re.sub(r"(?i)\s*(?:season\s*\d+|s\d+|hindi|dubbed|subbed|multi-audio|tamil|telugu).*$", "", series_title).strip()
        search_title = clean_title or series_title or slug_to_title(series_slug)

        for name, extractor in self.sources:
            try:
                log.info("Trying fallback source '%s' for '%s' S%dE%d [%s]...", name, search_title, season, episode, quality_pref)
                res = await extractor.resolve_episode(
                    anime_title=search_title,
                    season=season,
                    episode=episode,
                    quality_pref=quality_pref,
                )
                if not res or not res.get("url"):
                    continue

                raw_url = res["url"]
                # If the URL is an embed/player page, attempt player resolution to extract direct m3u8/mp4
                if any(k in raw_url.lower() for k in ("embed", "player", "trembed", "trid")):
                    resolved = await resolve_player_url(raw_url)
                    if resolved and resolved.get("url"):
                        log.info("Successfully resolved player embed via %s -> %s", name, resolved["url"])
                        return {
                            "url": resolved["url"],
                            "quality": resolved.get("quality", res.get("quality", quality_pref)),
                            "source": name,
                            "poster": res.get("poster"),
                        }

                # Otherwise direct URL or hubcloud/filepress link
                log.info("Fallback source '%s' provided downloadable stream [%s]", name, res.get("quality", quality_pref))
                return {
                    "url": raw_url,
                    "quality": res.get("quality", quality_pref),
                    "source": name,
                    "poster": res.get("poster"),
                }
            except Exception as e:
                log.warning("Fallback resolver '%s' failed for '%s' S%dE%d: %s", name, search_title, season, episode, e)

        return None


multi_source_manager = MultiSourceManager()
