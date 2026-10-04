"""Universal manual URL resolver — backing for /bypass (V2 #23).

Single generic interface over every supported extractor:

    /bypass <URL>
        ↓ Detect Website
        ↓ Select Website Resolver
        ↓ Resolve Page / Redirect Chain
        ↓ Validate Anime / Season / Episode
        ↓ Extract Available Qualities
        ↓ Extract Public Download / Media / Archive Links
        ↓ Return Detailed Result

Reusable: normal download flow can call ``resolve_bypass_url()`` directly
instead of duplicating resolver code. Only publicly accessible content is
resolved — no private login cookies, auth tokens, or session secrets are
ever read or echoed.
"""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urlparse

log = logging.getLogger(__name__)


# ── Supported-source registry (domain fragment → source name) ────────────
# Website-specific implementations live in their extractor modules; this
# table only routes. Add future extractors here — /bypass picks them up
# with no command changes.

SUPPORTED_SOURCES: dict[str, str] = {
    "animedubhindi": "AnimeDubHindi",
    "adhlinks.com": "AnimeDubHindi",
    "toonworld4all": "ToonWorld4All",
    "toonanime": "ToonAnime",
    "rareanimes": "RareAnimes",
    "deadtoons": "DeadToons",
    "toono.app": "TOONo",
    "animedrive": "AnimeDrive",
    "toonflix": "ToonFlix",
}


def detect_source(url: str) -> str | None:
    """Return the supported Source name for *url*, or None if unsupported."""
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return None
    for frag, name in SUPPORTED_SOURCES.items():
        if frag in host:
            return name
    return None


def _detect_quality_from_text(blob: str) -> str:
    b = (blob or "").lower()
    for q in ("2160p", "2160", "4k", "uhd"):
        if q in b:
            return "4K"
    for q in ("1080p", "1080"):
        if q in b:
            return "1080p"
    for q in ("720p", "720"):
        if q in b:
            return "720p"
    for q in ("480p", "480"):
        if q in b:
            return "480p"
    for q in ("360p", "360"):
        if q in b:
            return "360p"
    return ""


def _parse_title_season_episode(url: str, html: str = "") -> tuple[str, int | None, int | None]:
    """Best-effort anime/season/episode parse from URL + page title.

    Returns (anime, season, episode) with Nones when not confidently found —
    callers must reject wrong matches, never guess.
    """
    anime = ""
    season: int | None = None
    episode: int | None = None
    try:
        path = urlparse(url).path.strip("/")
        slug = path.split("/")[-1] if path else ""
        slug = re.sub(r"\.(html?|php)$", "", slug, flags=re.I)
        # Season/episode patterns: s1e10, 1x10, season-1-episode-10, ep-10
        m = re.search(r"[Ss](\d+)[Ee](\d+)", slug)
        if not m:
            m = re.search(r"(\d+)[xX](\d+)", slug)
        if m:
            season, episode = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.search(r"(?:season|s)[-_]?(\d+).*?(?:episode|ep)[-_]?(\d+)", slug, re.I)
            if m2:
                season, episode = int(m2.group(1)), int(m2.group(2))
            else:
                m3 = re.search(r"(?:episode|ep)[-_]?(\d+)", slug, re.I)
                if m3:
                    episode = int(m3.group(1))
        base = re.sub(
            r"(?i)[-_ ]?(season[-_ ]?\d+|s\d+e\d+|\d+x\d+|episode[-_ ]?\d+|ep[-_ ]?\d+|hindi|multi[-_ ]?audio|dubbed).*$",
            "",
            slug,
        )
        anime = re.sub(r"[-_]+", " ", base).strip().title()
    except Exception:
        pass
    if html and not anime:
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.get_text(strip=True):
                anime = soup.title.get_text(strip=True).split("|")[0].split("–")[0].strip()[:120]
        except Exception:
            pass
    return anime, season, episode


async def _fetch_public(url: str) -> tuple[str, str]:
    """GET a public page; returns (final_url, html). No auth/cookies sent."""
    from utils.http import http_client
    try:
        final_url, html = await http_client.get_with_redirects(url)
        return final_url, html or ""
    except Exception as e:
        log.warning("bypass fetch failed for %s: %s", url[:100], e)
        return url, ""


def _split_archive_vs_media(urls: list[str]) -> tuple[list[str], list[str]]:
    """Separate ZIP/archive links from direct video links."""
    archives, media = [], []
    for u in urls:
        low = u.lower()
        if any(k in low for k in (".zip", ".rar", ".7z", "archive.toonworld4all")):
            archives.append(u)
        else:
            media.append(u)
    return archives, media


async def resolve_bypass_url(url: str, quality_pref: str = "1080p") -> dict:
    """Generic resolver used by /bypass AND reusable by download flow.

    Never returns fake results: unsupported sites → {"ok": False,
    "error": "Unsupported Source ..."}; HTML pages are never reported as
    media URLs (validated via is_valid_media_destination).
    """
    from extractors.shortener import detect_and_bypass, is_shortener, is_valid_media_destination

    original_url = (url or "").strip()
    result: dict = {
        "ok": False,
        "source": None,
        "original_url": original_url,
        "final_url": original_url,
        "anime": "",
        "season": None,
        "episode": None,
        "qualities": [],
        "media_links": [],
        "archive_links": [],
        "stage": "detect",
        "error": "",
    }
    if not original_url or not original_url.lower().startswith(("http://", "https://")):
        result["error"] = "Provide a public http(s) page/episode URL: /bypass <URL>"
        return result

    source = detect_source(original_url)
    if not source:
        result["stage"] = "detect"
        result["error"] = f"Unsupported Source for {urlparse(original_url).netloc or original_url} — no resolver registered."
        return result
    result["source"] = source

    # ── Stage: redirect chain ──────────────────────────────────────────
    curr = original_url
    try:
        if is_shortener(curr) or "redirect" in curr.lower():
            bypassed = await detect_and_bypass(curr)
            if bypassed and bypassed != curr:
                curr = bypassed
        final_url, html = await _fetch_public(curr)
        result["final_url"] = final_url or curr
        result["stage"] = "fetch"
    except Exception as e:
        result["stage"] = "fetch"
        result["error"] = f"Fetch failed: {e}"
        return result

    if not html or len(html) < 500:
        result["error"] = "Page fetch returned empty/blocked content (Cloudflare/antibot?)."
        return result

    # ── Stage: validate anime/season/episode ─────────────────────────
    anime, season, episode = _parse_title_season_episode(result["final_url"], html)
    result["anime"] = anime
    result["season"] = season
    result["episode"] = episode
    result["stage"] = "validate"
    if not anime or len(anime) < 3:
        result["error"] = "Could not validate anime title from URL/page — refusing to guess."
        return result

    # ── Stage: website-specific resolution ───────────────────────────
    # Prefer the extractor's own resolver when the URL is an episode page;
    # otherwise fall back to generic public-link scan below.
    result["stage"] = "resolve"
    try:
        if source == "ToonWorld4All" and ("archive.toonworld4all" in curr.lower() or "archive.toonworld4all" in result["final_url"].lower()):
            from extractors.shortener import detect_and_bypass as _dab
            dest = await _dab(result["final_url"])
            if dest and dest != result["final_url"]:
                result["final_url"] = dest
    except Exception as e:
        log.debug("bypass source-specific step failed: %s", e)

    # ── Stage: extract qualities + public links (generic scan) ───────
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        found: list[tuple[str, str]] = []  # (url, quality)
        for a in soup.find_all("a", href=True):
            href = (a["href"] or "").strip()
            if not href.startswith("http") or len(href) < 12:
                continue
            label = a.get_text(" ", strip=True)[:200]
            q = _detect_quality_from_text(href + " " + label) or quality_pref
            found.append((href, q))
        for iframe in soup.find_all("iframe"):
            src = (iframe.get("src") or "").strip()
            if src.startswith("http") and len(src) > 12:
                q = _detect_quality_from_text(src) or quality_pref
                found.append((src, q))

        # Resolve shorteners/redirects one hop, then keep ONLY real media
        # destinations — an HTML page must never be reported as a 480p link.
        media_links: list[dict] = []
        archive_urls: list[str] = []
        seen: set[str] = set()
        for href, q in found:
            try:
                dest = href
                if is_shortener(href) or "redirect" in href.lower() or "archive.toonworld4all" in href.lower():
                    dest = await detect_and_bypass(href)
                    if not dest:
                        continue
                if dest in seen:
                    continue
                seen.add(dest)
                low = dest.lower()
                if any(k in low for k in (".zip", ".rar", ".7z", "archive.toonworld4all")):
                    archive_urls.append(dest)
                    continue
                if not is_valid_media_destination(dest):
                    continue
                media_links.append({"quality": q, "url": dest})
            except Exception:
                continue

        # Dedupe by URL, collect quality set
        uniq: dict[str, dict] = {}
        for m in media_links:
            uniq.setdefault(m["url"], m)
        media_links = list(uniq.values())
        qualities = sorted({m["quality"] for m in media_links},
                           key=lambda x: {"480p": 0, "720p": 1, "1080p": 2, "4K": 3}.get(x, 9))
        _, _ = _split_archive_vs_media([])  # keep helper referenced for reuse
        result["media_links"] = media_links
        result["archive_links"] = sorted(set(archive_urls))
        result["qualities"] = qualities or ([quality_pref] if media_links else [])
        result["stage"] = "done"
        if not media_links and not archive_urls:
            result["error"] = "No public download/media/archive links found on this page."
            return result
        result["ok"] = True
        return result
    except Exception as e:
        result["stage"] = "extract"
        result["error"] = f"Extraction failed: {e}"
        return result
