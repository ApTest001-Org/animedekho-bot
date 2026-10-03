"""Multi-Source Fallback Architecture — orchestrates primary and fallback scrapers."""

from __future__ import annotations
import asyncio
import logging
import re
from typing import TYPE_CHECKING

from api.models import SearchResult
from utils.helpers import clean_title, slug_to_title
from extractors.animedubhindi import animedubhindi
from extractors.animedrive import animedrive
from extractors.toonflix import toonflix
from extractors.rareanimes import rareanimes
from extractors.deadtoons import deadtoons
from extractors.toonworld4all import toonworld4all
from extractors.toono import toono
from extractors.resolver import resolve_player_url
from extractors.shortener import is_shortener, detect_and_bypass, is_valid_media_destination

log = logging.getLogger(__name__)


class MultiSourceManager:
    """Manages primary, secondary, and fallback download/streaming sources."""

    def __init__(self):
        # Direct download/video sources prioritized first (Issue #22 & #23)
        self.sources = [
            ("AnimeDubHindi", animedubhindi),
            ("ToonWorld4All", toonworld4all),
            ("RareAnimes", rareanimes),
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
        Applies full resolver pipeline (shortener -> HubCloud -> player embed -> validation).
        Never returns intermediate HTML or ad pages!
        """
        clean_title = re.sub(r"(?i)\s*(?:season\s*\d+|s\d+|hindi|dubbed|subbed|multi-audio|tamil|telugu).*$", "", series_title).strip()
        search_title = clean_title or series_title or slug_to_title(series_slug)
        search_title = re.sub(r"[’'\"\-_:!?]+", " ", search_title).strip()
        search_title = re.sub(r"\s+", " ", search_title)

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

                curr_url = res["url"].strip()
                log.info("Source '%s' returned initial URL: %s", name, curr_url[:80])

                # Stage 1: Shortener / Redirect resolution
                if is_shortener(curr_url) or "redirect" in curr_url.lower() or "archive.toonworld4all" in curr_url.lower():
                    bypassed = await detect_and_bypass(curr_url)
                    if bypassed and bypassed != curr_url:
                        log.info("Bypassed intermediate redirect/shortener on %s: %s -> %s", name, curr_url[:60], bypassed[:60])
                        curr_url = bypassed
                    elif is_shortener(curr_url):
                        log.warning("Shortener bypass failed for %s on %s; skipping source", curr_url[:60], name)
                        continue

                # Stage 2: HubCloud provider resolution
                if any(x in curr_url.lower() for x in ("hubcloud", "gamerxyt")):
                    try:
                        loop = asyncio.get_running_loop()
                        hub_res = await loop.run_in_executor(
                            None, animedrive._resolve_hubcloud, animedrive._get_scraper(), curr_url
                        )
                        if hub_res and is_valid_media_destination(hub_res):
                            log.info("HubCloud resolved via animedrive helper: %s -> %s", curr_url[:60], hub_res[:60])
                            curr_url = hub_res
                        else:
                            log.warning("HubCloud resolution returned unplayable target: %s", hub_res)
                            continue
                    except Exception as he:
                        log.warning("HubCloud resolution failed for %s: %s", curr_url, he)
                        continue

                # Stage 3: Player / Embed resolution
                is_player = any(k in curr_url.lower() for k in (
                    "embed", "player", "trembed", "trid", "streamwish", "playerwish",
                    "filemoon", "kerapoxy", "vidstream", "rabbitstream", "megacloud",
                    "vidsrc", "xerver.xyz", "turboviplay", "turbosplayer", "emturbovid",
                    "doodstream", "dood.", "streamtape", "strtape", "mp4upload", "vidguard", "vgfplay"
                ))
                if is_player and not any(ext in curr_url.lower() for ext in (".m3u8", ".mp4", ".mkv", ".webm")):
                    resolved = await resolve_player_url(curr_url)
                    if resolved and resolved.get("url") and is_valid_media_destination(resolved["url"]):
                        log.info("Successfully resolved player embed via %s -> %s", name, resolved["url"][:80])
                        return {
                            "url": resolved["url"],
                            "quality": resolved.get("quality", res.get("quality", quality_pref)),
                            "source": name,
                            "poster": res.get("poster"),
                        }
                    else:
                        log.warning("Player embed resolution failed or returned invalid media for %s on %s; rejecting embed page", curr_url[:60], name)
                        continue

                # Stage 4: Final Validation
                if not is_valid_media_destination(curr_url):
                    log.warning("Candidate URL failed media destination validation (%s) on %s; rejecting", curr_url[:80], name)
                    continue

                log.info("Fallback source '%s' provided valid downloadable stream [%s]: %s", name, res.get("quality", quality_pref), curr_url[:80])
                return {
                    "url": curr_url,
                    "quality": res.get("quality", quality_pref),
                    "source": name,
                    "poster": res.get("poster"),
                }
            except Exception as e:
                log.warning("Fallback resolver '%s' failed for '%s' S%dE%d: %s", name, search_title, season, episode, e)

        return None


multi_source_manager = MultiSourceManager()
