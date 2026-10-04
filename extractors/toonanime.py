"""ToonAnime extractor — fallback source for Hindi & Multi-Audio anime series & movies."""

from __future__ import annotations
import asyncio
import logging
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import cloudscraper

from utils.anilist import is_valid_poster_url
from extractors.resolver import resolve_player_url
from extractors.shortener import is_shortener, detect_and_bypass, is_valid_media_destination

log = logging.getLogger(__name__)


def _get_scraper() -> cloudscraper.CloudScraper:
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )


class ToonAnimeExtractor:
    """Extracts Multi-Audio & Hindi anime series from ToonAnime."""

    def __init__(self):
        self._base_urls = [
            "https://toonanime.cc",
            "https://toonanime.biz",
            "https://toonanime.tv",
            "https://toonanimes.com",
        ]
        self._base_url = self._base_urls[0]

    async def search(self, query: str) -> list[dict]:
        """Search ToonAnime for anime series or movies."""
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

        for base in self._base_urls:
            url = f"{base}/?s={quote_plus(search_query)}"
            try:
                r = s.get(url, timeout=10)
                # Check for JS challenge redirect
                m = re.search(r"window\.location\.replace\('([^']+)'\)", r.text)
                if m:
                    r = s.get(m.group(1), headers={"Referer": url}, timeout=10)

                if r.status_code != 200 or len(r.text) < 1000:
                    continue

                soup = BeautifulSoup(r.text, "html.parser")
                results = []
                seen = set()

                for art in soup.find_all(["article", "div"], class_=lambda c: c and any(k in str(c) for k in ("post", "item", "result", "anime", "film"))):
                    a = art.find("a", href=True)
                    if not a:
                        continue
                    href = a["href"]
                    if href in seen:
                        continue
                    seen.add(href)
                    full_url = href if href.startswith("http") else f"{base}{href}"

                    h = art.find(["h1", "h2", "h3", "h4", "h5", "header", "span"])
                    title = h.get_text(strip=True) if h else a.get_text(strip=True)
                    title = re.sub(r"\d{4}$", "", title).strip()
                    if not title or len(title) < 3 or title.lower() in ("watch series", "series", "movies", "menu", "home"):
                        continue

                    poster = ""
                    img = art.find("img")
                    if img:
                        p_url = img.get("src") or img.get("data-src", "")
                        if is_valid_poster_url(p_url):
                            poster = p_url

                    results.append({
                        "title": title,
                        "url": full_url,
                        "poster": poster,
                        "source": "ToonAnime",
                    })

                if results:
                    self._base_url = base
                    return results

            except Exception as e:
                log.debug("ToonAnime search attempt on %s failed: %s", base, e)

        return []

    async def resolve_episode(
        self,
        anime_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
    ) -> dict | None:
        """Resolve direct stream/download link from ToonAnime."""
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

        # Best match series
        target_series = search_results[0]
        series_url = target_series["url"]

        try:
            r = s.get(series_url, timeout=12)
            m = re.search(r"window\.location\.replace\('([^']+)'\)", r.text)
            if m:
                r = s.get(m.group(1), headers={"Referer": series_url}, timeout=10)

            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")

            # Look for episode matching season and episode
            ep_url = None
            pat = re.compile(rf"[-_]{season}x0*{episode}\b|episode[-_]0*{episode}\b|ep[-_]0*{episode}\b", re.I)
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if pat.search(href) or pat.search(a.get_text()):
                    ep_url = href if href.startswith("http") else f"{self._base_url}{href}"
                    break

            if not ep_url:
                # If single movie page, current page might be the watch page
                if "movie" in anime_title.lower() or "film" in anime_title.lower():
                    ep_url = series_url
                else:
                    return None

            r_ep = s.get(ep_url, timeout=12)
            if r_ep.status_code != 200:
                return None
            soup_ep = BeautifulSoup(r_ep.text, "html.parser")

            # Check iframes for player embeds
            for iframe in soup_ep.find_all("iframe"):
                src = iframe.get("src", "")
                if src:
                    return {
                        "url": src,
                        "quality": quality_pref,
                        "source": "ToonAnime",
                        "poster": target_series.get("poster"),
                    }

            # Check for direct download links
            for a in soup_ep.find_all("a", href=True):
                href = a["href"]
                if any(x in href.lower() for x in ("drive.google", "mega.nz", "mediafire", "streamwish", "hubcloud")):
                    return {
                        "url": href,
                        "quality": quality_pref,
                        "source": "ToonAnime",
                        "poster": target_series.get("poster"),
                    }
        except Exception as e:
            log.warning("ToonAnime resolve error for '%s' S%dE%d: %s", anime_title, season, episode, e)

        return None


toonanime = ToonAnimeExtractor()
