"""
AnimeDubHindi extractor — scrapes https://www.animedubhindi.link/
Provides high quality multi-audio Hindi anime episodes with direct download sources.
"""

from __future__ import annotations

import asyncio
import base64
import html
import logging
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

BASE_URL = "https://www.animedubhindi.link"


def _get_scraper():
    import cloudscraper
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )


class AnimeDubHindiExtractor:
    """Extractor for AnimeDubHindi (https://www.animedubhindi.link/)."""

    def __init__(self):
        self.base_url = BASE_URL

    async def search(self, query: str) -> list[dict]:
        """Search AnimeDubHindi for anime matching *query*."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_search, query)

    def _sync_search(self, query: str) -> list[dict]:
        s = _get_scraper()
        # Clean season suffix and special chars for WordPress search so all seasons are retrieved
        clean = re.sub(
            r"(?i)\s*(—|-|season\s*\d+|s\d+|hindi|dubbed|multi-audio|tamil|telugu|uncensored|episodes).*$",
            "",
            query,
        ).strip()
        search_query = clean or query
        clean_q = re.sub(r"[’'\"\-_:!?]+", " ", search_query).strip()
        clean_q = re.sub(r"\s+", " ", clean_q)
        search_url = f"{self.base_url}/?s={clean_q}"
        try:
            r = s.get(search_url, timeout=12)
            if r.status_code != 200:
                log.warning("AnimeDubHindi search returned HTTP %d for '%s'", r.status_code, query)
                return []

            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            seen_urls = set()

            # Inspect post entries
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href in seen_urls:
                    continue
                if not href.startswith("http") or href.rstrip("/") == self.base_url.rstrip("/"):
                    continue

                title = a.get_text(strip=True) or (a.get("title") or "").strip()
                # Skip navigation links
                if not title or len(title) < 4:
                    continue
                if any(bad in title.lower() for bad in ("home", "contact", "telegram", "author", "dmca", "privacy", "category", "tag")):
                    continue
                if any(bad in href.lower() for bad in ("/author/", "/category/", "/tag/", "/contact", "/page/")):
                    continue

                # Look for poster thumbnail in parent element
                poster = ""
                parent = a.find_parent(["article", "div", "li"])
                if parent:
                    img = parent.find("img")
                    if img:
                        poster = img.get("src") or img.get("data-src") or ""

                seen_urls.add(href)
                results.append({
                    "title": title,
                    "url": href,
                    "poster": poster,
                    "source": "AnimeDubHindi",
                })

            log.info("AnimeDubHindi search for '%s' returned %d results", query, len(results))
            return results
        except Exception as e:
            log.warning("AnimeDubHindi search failed for '%s': %s", query, e)
            return []

    async def resolve_episode(
        self,
        anime_title: str,
        season: int = 1,
        episode: int = 1,
        quality_pref: str = "1080p",
    ) -> dict | None:
        """Resolve an episode stream or direct download link from AnimeDubHindi."""
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
            # Verify title similarity - at least one key word must match
            if q_words and not any(w in t or w in href for w in q_words):
                continue

            # Strict season matching
            s_patterns = (
                f"season {season}",
                f"season {season:02d}",
                f"season-{season}",
                f"season-{season:02d}",
                f"s{season}",
                f"s{season:02d}",
            )
            if any(p in t or p in href for p in s_patterns) or (season == 1 and "season" not in t and "season" not in href):
                target_post = res
                break

        if not target_post:
            log.info("AnimeDubHindi: No matching season %d post found for '%s'", season, anime_title)
            return None

        post_url = target_post["url"]
        log.info("AnimeDubHindi: Found target post: %s (%s)", target_post["title"], post_url)

        try:
            r = s.get(post_url, timeout=12)
            if r.status_code != 200:
                return None

            soup = BeautifulSoup(r.text, "html.parser")

            # Look for episode directory link (e.g. https://new.adhlinks.com/episode/{slug}/)
            ep_directory_url = None
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if "/episode/" in href or "adhlinks" in href:
                    ep_directory_url = href
                    break

            page_soup = soup
            base_dir_url = post_url
            if ep_directory_url:
                log.info("AnimeDubHindi: Fetching episode directory: %s", ep_directory_url)
                r_dir = s.get(ep_directory_url, headers={"Referer": post_url}, timeout=12)
                if r_dir.status_code == 200:
                    page_soup = BeautifulSoup(r_dir.text, "html.parser")
                    base_dir_url = ep_directory_url

            # Search for the requested episode header
            # Examples: "Episode: 01", "Episode 1", "Episode: 1", "Episode 01"
            ep_patterns = [
                re.compile(rf"Episode\s*:\s*0*{episode}\b", re.I),
                re.compile(rf"Episode\s+0*{episode}\b", re.I),
                re.compile(rf"\bEp\s*:\s*0*{episode}\b", re.I),
                re.compile(rf"\bEp\s+0*{episode}\b", re.I),
            ]

            found_header = None
            for h in page_soup.find_all(["h2", "h3", "h4", "p", "div"]):
                txt = h.get_text(strip=True)
                if any(p.search(txt) for p in ep_patterns) and len(txt) < 40:
                    found_header = h
                    break

            if not found_header:
                log.info("AnimeDubHindi: Episode %d header not found on %s", episode, base_dir_url)
                return None

            # Collect link groups under this episode header
            # Links are divided into qualities (480P, 720P, 1080P)
            curr = found_header.find_next_sibling()
            quality_map: dict[str, list[tuple[str, str]]] = {
                "480p": [],
                "720p": [],
                "1080p": [],
                "other": [],
            }

            while curr and curr.name not in ["h2", "h3"]:
                # Often all qualities are in a single <h4> tag with text like:
                # 480P [Size: ...] MEGA | Multi ... 720P [Size: ...] MEGA | Multi ...
                # Or separate paragraphs
                elem_text = curr.get_text(" ", strip=True)
                all_links = [(a.get_text(strip=True), urljoin(base_dir_url, a["href"])) for a in curr.find_all("a", href=True)]

                # Check if links can be mapped by chunks
                if "480p" in elem_text.lower() and "720p" in elem_text.lower():
                    # 5 links per quality typically (MEGA, Multi, GDT, Tera, Fpress)
                    # Divide evenly or assign based on index
                    n = len(all_links)
                    if n >= 15:
                        quality_map["480p"].extend(all_links[:5])
                        quality_map["720p"].extend(all_links[5:10])
                        quality_map["1080p"].extend(all_links[10:15])
                    elif n >= 10:
                        quality_map["480p"].extend(all_links[:n // 2])
                        quality_map["720p"].extend(all_links[n // 2:])
                    else:
                        quality_map["other"].extend(all_links)
                elif "480p" in elem_text.lower():
                    quality_map["480p"].extend(all_links)
                elif "720p" in elem_text.lower():
                    quality_map["720p"].extend(all_links)
                elif "1080p" in elem_text.lower():
                    quality_map["1080p"].extend(all_links)
                else:
                    quality_map["other"].extend(all_links)

                curr = curr.find_next_sibling()

            # Quality preference order: requested quality first, then remaining
            pref_norm = quality_pref.lower()
            q_order = [pref_norm]
            for fallback_q in ["1080p", "720p", "480p", "other"]:
                if fallback_q not in q_order:
                    q_order.append(fallback_q)

            # Try resolving direct link from the chosen quality bucket
            for q_cand in q_order:
                candidates = quality_map.get(q_cand, [])
                if not candidates:
                    continue

                # Link preference: Multi (direct FilesForever worker) -> MEGA -> Fpress -> others
                def _link_priority(item: tuple[str, str]) -> int:
                    label, u = item[0].lower(), item[1].lower()
                    if "multi" in label or "re.php" in u:
                        return 0
                    if "fpress" in label or "filepress" in u or "fpgo" in u:
                        return 1
                    if "mega" in label or "redirect.php" in u:
                        return 2
                    return 3

                candidates.sort(key=_link_priority)

                for label, target_url in candidates:
                    log.info("AnimeDubHindi: Trying %s link (%s) [%s]: %s", label, q_cand, target_url[:80], target_url)

                    # 1. Multi link via /re.php?data=...
                    if "re.php" in target_url:
                        try:
                            r_re = s.get(target_url, headers={"Referer": base_dir_url}, timeout=10)
                            m_redir = re.search(r'redirectUrl\s*=\s*["\']([^"\']+)["\']', r_re.text)
                            if m_redir:
                                target_dest = base64.b64decode(m_redir.group(1)).decode("utf-8", errors="ignore").strip()
                                log.info("AnimeDubHindi: Decoded re.php destination: %s", target_dest)

                                # If destination is filesforever.link
                                if "filesforever" in target_dest:
                                    r_ff = s.get(target_dest, timeout=10)
                                    m_src = re.search(r'name=["\']source_url["\']\s+value=["\']([^"\']+)["\']', r_ff.text)
                                    if m_src:
                                        worker_url = html.unescape(m_src.group(1).strip())
                                        log.info("AnimeDubHindi: Extracted direct worker URL: %s", worker_url[:80])
                                        return {
                                            "url": worker_url,
                                            "quality": q_cand if q_cand != "other" else quality_pref,
                                            "source": "AnimeDubHindi",
                                            "poster": target_post.get("poster"),
                                        }
                                return {
                                    "url": target_dest,
                                    "quality": q_cand if q_cand != "other" else quality_pref,
                                    "source": "AnimeDubHindi",
                                    "poster": target_post.get("poster"),
                                }
                        except Exception as e:
                            log.warning("AnimeDubHindi re.php resolution failed: %s", e)

                    # 2. MEGA link via /redirect.php?data=...
                    elif "redirect.php" in target_url:
                        try:
                            r_red = s.get(target_url, headers={"Referer": base_dir_url}, allow_redirects=False, timeout=10)
                            loc = r_red.headers.get("Location")
                            if loc:
                                log.info("AnimeDubHindi: redirect.php 302 -> %s", loc)
                                return {
                                    "url": loc,
                                    "quality": q_cand if q_cand != "other" else quality_pref,
                                    "source": "AnimeDubHindi",
                                    "poster": target_post.get("poster"),
                                }
                        except Exception as e:
                            log.warning("AnimeDubHindi redirect.php resolution failed: %s", e)

                    # 3. Fpress / Filepress link
                    elif any(k in target_url.lower() for k in ("fpgo.xyz", "filepress")):
                        return {
                            "url": target_url,
                            "quality": q_cand if q_cand != "other" else quality_pref,
                            "source": "AnimeDubHindi",
                            "poster": target_post.get("poster"),
                        }

                    # 4. Direct stream/mkv/mp4 link
                    elif any(ext in target_url.lower() for ext in (".mkv", ".mp4", ".m3u8")):
                        return {
                            "url": target_url,
                            "quality": q_cand if q_cand != "other" else quality_pref,
                            "source": "AnimeDubHindi",
                            "poster": target_post.get("poster"),
                        }

            return None
        except Exception as e:
            log.warning("AnimeDubHindi resolution error for '%s' S%dE%d: %s", anime_title, season, episode, e)
            return None


animedubhindi = AnimeDubHindiExtractor()
