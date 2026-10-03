"""DeadToons extractor — fallback source for Hindi & Multi-Audio anime."""

from __future__ import annotations
import asyncio
import logging
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import cloudscraper

from utils.anilist import is_valid_poster_url

log = logging.getLogger(__name__)


def _get_scraper() -> cloudscraper.CloudScraper:
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )


class DeadToonsExtractor:
    """Extracts Multi-Audio & Hindi anime series from DeadToons (deadtoons.sbs)."""

    def __init__(self):
        self._base_url = "https://deadtoons.sbs"

    async def search(self, query: str) -> list[dict]:
        """Search DeadToons for anime series or movies."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_search, query)

    def _sync_search(self, query: str) -> list[dict]:
        s = _get_scraper()
        clean = re.sub(
            r"(?i)\s*(season\s*\d+|s\d+|hindi|dubbed|multi-audio|tamil|telugu).*$",
            "",
            query,
        ).strip()
        search_query = clean or query
        url = f"{self._base_url}/search?q={quote_plus(search_query)}"

        try:
            r = s.get(url, timeout=12)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            seen = set()

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/posts/" not in href or href in seen:
                    continue
                seen.add(href)
                full_url = href if href.startswith("http") else f"{self._base_url}{href}"
                title = a.get_text(strip=True)
                if not title or len(title) < 3 or title.lower() in ("completed", "ongoing", "movie"):
                    continue

                poster = ""
                img = a.find("img") or (a.parent.find("img") if a.parent else None)
                if img:
                    p_url = img.get("src") or img.get("data-src", "")
                    if is_valid_poster_url(p_url):
                        poster = p_url

                results.append({
                    "title": title,
                    "url": full_url,
                    "poster": poster,
                    "source": "DeadToons",
                })

            return results
        except Exception as e:
            log.warning("DeadToons search failed for '%s': %s", query, e)
            return []

    async def resolve_episode(
        self,
        anime_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
    ) -> dict | None:
        """Resolve an episode stream/download link from DeadToons."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self._sync_resolve, anime_title, season, episode, quality_pref
        )

    def _sync_resolve(
        self,
        anime_title: str,
        season: int,
        episode: int,
        quality_pref: str,
    ) -> dict | None:
        s = _get_scraper()
        search_results = self._sync_search(anime_title)
        if not search_results:
            return None

        # Clean title keywords for matching
        q_words = [w.lower() for w in re.findall(r"\w+", anime_title) if len(w) > 2]

        target_post = None
        for res in search_results:
            t = res["title"].lower()
            href = res["url"].lower()
            if q_words and not any(w in t or w in href for w in q_words):
                continue
            if (
                f"season {season}" in t
                or f"season {season:02d}" in t
                or f"s{season}" in t
                or f"s{season:02d}" in t
                or (season == 1 and "season" not in t and "s0" not in t and "s1" not in t)
            ):
                target_post = res
                break

        if not target_post:
            log.info("DeadToons: No verified season %d post for '%s'", season, anime_title)
            return None

        post_url = target_post["url"]
        try:
            r = s.get(post_url, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")

            # Look for episode download link (e.g., /episode/.../{season}x{episode})
            pattern = re.compile(rf"/{season}x0*{episode}\b", re.I)
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if pattern.search(href) or f"episode/{season}x{episode}" in href.lower():
                    return {
                        "url": href,
                        "quality": quality_pref,
                        "source": "DeadToons",
                        "poster": target_post.get("poster"),
                    }
        except Exception as e:
            log.warning("DeadToons resolve error for %s: %s", post_url, e)

        return None


deadtoons = DeadToonsExtractor()
