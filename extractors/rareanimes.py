"""RareAnimes extractor — fallback source for Hindi dubbed anime."""

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


class RareAnimesExtractor:
    """Extracts Hindi dubbed anime episodes from RareAnimes (rareanimes.mov)."""

    def __init__(self):
        self._base_url = "https://www.rareanimes.mov"

    async def search(self, query: str) -> list[dict]:
        """Search RareAnimes catalog for anime series."""
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
        url = f"{self._base_url}/?s={quote_plus(search_query)}"

        try:
            r = s.get(url, timeout=12)
            if r.status_code != 200:
                return []
            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            seen = set()

            for h2 in soup.find_all(["h2", "h3", "h1"], class_=lambda c: c and "entry-title" in c):
                a = h2.find("a", href=True)
                if not a:
                    continue
                href = a["href"]
                if href in seen:
                    continue
                seen.add(href)
                title = a.get_text(strip=True)

                # Look for poster thumbnail in parent article
                art = h2.find_parent("article")
                poster = ""
                if art:
                    img = art.find("img")
                    if img:
                        p_url = img.get("src") or img.get("data-src", "")
                        if is_valid_poster_url(p_url):
                            poster = p_url

                results.append({
                    "title": title,
                    "url": href,
                    "poster": poster,
                    "source": "RareAnimes",
                })

            return results
        except Exception as e:
            log.warning("RareAnimes search failed for '%s': %s", query, e)
            return []

    async def resolve_episode(
        self,
        anime_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
    ) -> dict | None:
        """Resolve an episode stream/download link from RareAnimes."""
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

        # Pick best season matching post with strict title verification
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
            log.info("RareAnimes: No verified season %d post for '%s'", season, anime_title)
            return None

        post_url = target_post["url"]
        try:
            r = s.get(post_url, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            content = soup.find("div", class_=lambda c: c and "entry-content" in c)
            if not content:
                content = soup

            # Search for episode-specific link or download section
            for a in content.find_all("a", href=True):
                txt = a.get_text(" ", strip=True).lower()
                href = a["href"]
                # Match episode number e.g. "Ep 1", "Episode 01", "1x01"
                ep_match = re.search(r"(?:ep|episode|e)\s*0*(\d+)\b", txt)
                if ep_match and int(ep_match.group(1)) == episode:
                    if "http" in href:
                        return {
                            "url": href,
                            "quality": quality_pref,
                            "source": "RareAnimes",
                            "poster": target_post.get("poster"),
                        }
        except Exception as e:
            log.warning("RareAnimes resolve error for %s: %s", post_url, e)

        return None


rareanimes = RareAnimesExtractor()
