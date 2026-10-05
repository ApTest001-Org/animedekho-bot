"""ToonWorld4All extractor — fallback source for high quality anime & multi-audio series."""

from __future__ import annotations
import asyncio
import logging
import re
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import cloudscraper

from utils.anilist import is_valid_poster_url
from utils.anime_match import matches_episode, matches_season, normalize_provider_url

log = logging.getLogger(__name__)


def _extract_props_json(page: str) -> dict | None:
    """Extract nested ``window.__PROPS__`` JSON without a fragile regex.

    A non-greedy ``{.*?}`` stops at the first nested object and fails on the
    current archive payload.  This small scanner is string-aware, so braces in
    URLs or quoted JSON values do not corrupt the payload.
    """
    marker = re.search(r"(?:window\.|var\s+)?__PROPS__\s*=", page or "")
    if not marker:
        return None
    start = page.find("{", marker.end())
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(page)):
        char = page[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    import json
                    value = json.loads(page[start:idx + 1])
                    return value if isinstance(value, dict) else None
                except (TypeError, ValueError):
                    return None
    return None


def _get_scraper() -> cloudscraper.CloudScraper:
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )


class ToonWorld4AllExtractor:
    """Extracts anime and cartoons from ToonWorld4All (toonworld4all.me)."""

    def __init__(self):
        self._base_url = "https://toonworld4all.me"

    async def search(self, query: str) -> list[dict]:
        """Search ToonWorld4All catalog."""
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

            for art in soup.find_all("article"):
                a = art.find("a", href=True)
                title_el = art.find(["h2", "h3", "h4", "h1"])
                if not a or not title_el:
                    continue
                href = normalize_provider_url(a["href"], url)
                if not href or href in seen or "how-to-download" in href or "anime-shows-list" in href:
                    continue
                seen.add(href)
                title = title_el.get_text(strip=True)

                poster = ""
                img = art.find("img")
                if img:
                    p_url = img.get("src") or img.get("data-src", "")
                    if is_valid_poster_url(p_url):
                        poster = p_url

                results.append({
                    "title": title,
                    "url": href,
                    "poster": poster,
                    "source": "ToonWorld4All",
                })

            return results
        except Exception as e:
            log.warning("ToonWorld4All search failed for '%s': %s", query, e)
            return []

    async def resolve_episode(
        self,
        anime_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
    ) -> dict | None:
        """Resolve episode stream/download link from ToonWorld4All."""
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

        # V3 #5: confident title match (no single-keyword guess).
        from utils.anime_match import is_confident_match, matches_season
        target_post = None
        for res in search_results:
            t = res.get("title", "")
            href = res.get("url", "")
            if not is_confident_match(anime_title, t, href):
                continue
            if not matches_season(t, href, season):
                continue
            target_post = res
            break

        if not target_post:
            log.info("ToonWorld4All: No verified season %d post for '%s'", season, anime_title)
            return None

        post_url = target_post["url"]
        try:
            r = s.get(post_url, timeout=12)
            if r.status_code != 200:
                return None
            soup = BeautifulSoup(r.text, "html.parser")
            content = soup.find("div", class_=lambda c: c and ("entry-content" in c or "post-content" in c))
            if not content:
                content = soup

            # Match the requested episode without allowing another season's
            # 1x01/S2E01 link to win first.
            for a in content.find_all("a", href=True):
                href = normalize_provider_url(a["href"], post_url)
                txt = a.get_text(" ", strip=True)
                if a.parent:
                    txt = f"{a.parent.get_text(' ', strip=True)} {txt}"
                if not href or not matches_episode(txt, href, season, episode):
                    continue
                resolved_url = href

                # Unpack archive redirect pages when the provider has not
                # already exposed the final download URL.
                if "archive.toonworld4all" in href or "redirect" in href:
                    try:
                        r_arch = s.get(href, headers={"Referer": post_url}, timeout=10)
                        if r_arch.status_code == 200:
                            soup_arch = BeautifulSoup(r_arch.text, "html.parser")
                            for a_arch in soup_arch.find_all("a", href=True):
                                archive_href = normalize_provider_url(a_arch["href"], href)
                                if "redirect" not in archive_href.lower():
                                    continue
                                r_red = s.get(archive_href, headers={"Referer": href}, timeout=10)
                                props = _extract_props_json(r_red.text)
                                if not props:
                                    continue
                                link_info = props.get("link") or {}
                                if isinstance(link_info, dict):
                                    dom = normalize_provider_url(link_info.get("domain", ""), archive_href)
                                    hid = str(link_info.get("hidden", "")).strip()
                                    if dom and hid:
                                        resolved_url = urljoin(dom.rstrip("/") + "/", hid.lstrip("/"))
                                        resolved_url = resolved_url.replace("/video/", "/drive/")
                                        log.info("ToonWorld4All: Extracted root download URL: %s", resolved_url)
                                        break
                                destination = normalize_provider_url(str(props.get("destination", "")), archive_href)
                                if destination:
                                    resolved_url = destination
                                    break
                    except Exception as arch_err:
                        log.warning("ToonWorld4All archive unpack note: %s", arch_err)

                return {
                    "url": resolved_url,
                    "quality": "Unknown",
                    "requested_quality": quality_pref,
                    "detected_quality": "Unknown",
                    "verified_quality": "Unknown",
                    "source": "ToonWorld4All",
                    "poster": target_post.get("poster"),
                }

        except Exception as e:
            log.warning("ToonWorld4All resolve error for %s: %s", post_url, e)

        return None


toonworld4all = ToonWorld4AllExtractor()
