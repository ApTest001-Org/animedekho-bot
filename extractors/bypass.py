"""Universal manual URL resolver — backing for /bypass (V2 #23, V3 #3).

V3 #3: website-specific resolver dispatch (no generic-only scan).
V3 #4: detected/requested/verified quality stay separate; Unknown stays Unknown.
V3 #11: ToonWorld4All redirect/archive → resolve → refetch final page →
        destination validation; navigation/HTML/challenge rejected; failure
        stage reports the real failing stage (never "done" on failure).
V3 #12: AnimeDubHindi returns provider-grouped qualities
        (GDFLIX / FPGO / HubCloud … × 480p/720p/1080p).

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
    """V3 #4: return '' when unknown — callers map to 'Unknown', never to
    the requested quality."""
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
    """Separate ZIP/archive links from direct video links.

    V3 #11: only real archive *files* count — a bare
    ``archive.toonworld4all`` page or ``cdn-cgi/`` challenge asset is NOT an
    archive result.
    """
    archives, media = [], []
    for u in urls:
        low = u.lower()
        if re.search(r"\.(zip|rar|7z)(\?|#|$)", low):
            archives.append(u)
        else:
            media.append(u)
    return archives, media


# ── V3 #11: navigation / challenge rejection ─────────────────────────────

_NAVIGATION_HINTS = (
    "/tag/", "/tags/", "/category/", "/categories/", "/author/",
    "/contact", "/privacy", "/dmca", "/disclaimer", "/about",
    "cdn-cgi/", "/schedule", "schedule.php", "/page/",
)

_CHALLENGE_HINTS = (
    "just a moment", "cf-chl", "cf_turnstile", "turnstile",
    "g-recaptcha", "hcaptcha",
)


def _is_navigation_url(url: str, label: str = "") -> bool:
    """V3 #11: homepage / tag / contact / cdn-cgi must never be media links."""
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = (parsed.path or "/").lower()
        if not host:
            return True
        # Homepage / bare domain.
        if path in ("", "/"):
            return True
        if any(h in path or h in url.lower() for h in _NAVIGATION_HINTS):
            return True
        blob = f"{url} {label}".lower()
        if "telegram" in blob and not any(e in blob for e in (".mp4", ".mkv", ".m3u8", ".zip")):
            return True
        return False
    except Exception:
        return True


def _is_challenge_html(html: str) -> bool:
    h = (html or "").lower()
    return any(c in h for c in _CHALLENGE_HINTS)


def _infer_provider(url: str, label: str = "") -> str:
    try:
        from extractors.health_probe import infer_provider as _inf
        return _inf(url)
    except Exception:
        pass
    blob = f"{url} {label}".lower()
    for name in ("hubcloud", "gdflix", "gdflink", "fpgo", "filepress",
                 "mega", "drive.google", "mediafire", "multi"):
        if name in blob:
            return name.upper() if name in ("fpgo", "mega") else name.capitalize()
    return "Direct"


# ── V3 #3: website-specific resolvers ─────────────────────────────────────

async def _resolve_animedubhindi_page(
    html: str, base_url: str, quality_pref: str,
    detect_and_bypass, is_shortener, is_valid_media_destination,
) -> tuple[list[dict], dict]:
    """V3 #12: provider-grouped AnimeDubHindi parse.

    Returns (media_links, providers) where providers is
    {provider: {quality: [url, ...]}} for GDFLIX/FPGO/HubCloud/….
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    providers: dict[str, dict[str, list[str]]] = {}
    media_links: list[dict] = []
    seen: set[str] = set()

    def _bucket_for(elem_text: str) -> str:
        low = elem_text.lower()
        if "480p" in low and "720p" not in low and "1080p" not in low:
            return "480p"
        if "720p" in low and "1080p" not in low:
            # element header names one quality; mixed headers handled by link labels
            return "720p"
        if "1080p" in low:
            return "1080p"
        return ""

    # Strategy A: pro-ep-card layout with per-quality wrappers.
    cards = soup.find_all(class_="pro-ep-card")
    scoped = False
    for card in cards:
        for qw in card.find_all(class_="pro-quality-wrapper"):
            q_el = qw.find(class_="pro-ep-quality")
            q_txt = q_el.get_text(strip=True) if q_el else qw.get_text(" ", strip=True)[:120]
            bucket = _detect_quality_from_text(q_txt) or _bucket_for(q_txt) or "Unknown"
            for a in qw.find_all("a", href=True):
                href = a["href"].strip()
                if not href.startswith("http"):
                    continue
                label = a.get_text(" ", strip=True)[:120]
                # Per-link quality wins over wrapper header.
                link_q = _detect_quality_from_text(href + " " + label) or bucket
                if _is_navigation_url(href, label):
                    continue
                dest = href
                if is_shortener(href) or "redirect" in href.lower():
                    dest = await detect_and_bypass(href)
                    if not dest:
                        continue
                if dest in seen:
                    continue
                seen.add(dest)
                if not is_valid_media_destination(dest):
                    continue
                provider = _infer_provider(dest, label)
                # V3 #11: archive pages are not media; real zips go to archives.
                if re.search(r"\.(zip|rar|7z)(\?|#|$)", dest.lower()):
                    continue
                providers.setdefault(provider, {}).setdefault(link_q, []).append(dest)
                media_links.append({
                    "quality": link_q, "url": dest, "provider": provider,
                    "requested_quality": quality_pref, "detected_quality": link_q,
                    "verified_quality": link_q, "label": label,
                })
                scoped = True

    if scoped:
        return media_links, providers

    # Strategy B: generic strict scan (still provider-grouped, Unknown-safe).
    for a in soup.find_all("a", href=True):
        href = (a["href"] or "").strip()
        if not href.startswith("http") or len(href) < 12:
            continue
        label = a.get_text(" ", strip=True)[:200]
        if _is_navigation_url(href, label):
            continue
        q = _detect_quality_from_text(href + " " + label) or "Unknown"
        dest = href
        if is_shortener(href) or "redirect" in href.lower():
            dest = await detect_and_bypass(href)
            if not dest:
                continue
        if dest in seen:
            continue
        seen.add(dest)
        if re.search(r"\.(zip|rar|7z)(\?|#|$)", dest.lower()):
            continue
        if not is_valid_media_destination(dest):
            continue
        provider = _infer_provider(dest, label)
        providers.setdefault(provider, {}).setdefault(q, []).append(dest)
        media_links.append({
            "quality": q, "url": dest, "provider": provider,
            "requested_quality": quality_pref, "detected_quality": q,
            "verified_quality": q, "label": label,
        })
    for iframe in soup.find_all("iframe"):
        src = (iframe.get("src") or "").strip()
        if not src.startswith("http") or len(src) <= 12:
            continue
        if _is_navigation_url(src):
            continue
        q = _detect_quality_from_text(src) or "Unknown"
        if src in seen:
            continue
        seen.add(src)
        if not is_valid_media_destination(src):
            continue
        provider = _infer_provider(src)
        providers.setdefault(provider, {}).setdefault(q, []).append(src)
        media_links.append({
            "quality": q, "url": src, "provider": provider,
            "requested_quality": quality_pref, "detected_quality": q,
            "verified_quality": q, "label": "iframe",
        })
    return media_links, providers


async def _resolve_toonworld_url(
    page_url: str, html: str, quality_pref: str,
    detect_and_bypass, is_shortener, is_valid_media_destination,
) -> tuple[list[dict], list[str], str]:
    """V3 #11: real redirect resolve → final page refetch → validation.

    Returns (media_links, archive_urls, note). Archive *pages* are followed;
    only real archive *files* are reported as archives; cdn-cgi/navigation
    is rejected; HTML/challenge pages are never media.
    """
    from bs4 import BeautifulSoup
    media_links: list[dict] = []
    archive_urls: list[str] = []
    seen: set[str] = set()
    # Live-discovered budget: a season page can list 30+ episode/zip links;
    # resolving every one sequentially takes minutes. Bound bypass attempts
    # and prefer links matching the parsed episode.
    budget = {"n": 6}

    async def _bounded_bypass(href: str) -> str | None:
        if budget["n"] <= 0:
            return None
        budget["n"] -= 1
        try:
            return await detect_and_bypass(href)
        except Exception:
            return None

    def _ep_priority(href: str, label: str) -> int:
        if episode is not None and re.search(rf"{season}x0*{episode}\b", f"{href} {label}", re.I):
            return 0
        if "/zip/" in href.lower():
            return 2  # batch archives last; skipped below unless nothing else
        return 1

    async def _refetch_and_extract(target: str, depth: int = 0) -> None:
        if depth > 2:
            return
        final_url, page_html = await _fetch_public(target)
        if not page_html or len(page_html) < 300 or _is_challenge_html(page_html):
            return
        soup = BeautifulSoup(page_html, "html.parser")
        links: list[tuple[str, str]] = []
        for a in soup.find_all("a", href=True):
            links.append(((a["href"] or "").strip(), a.get_text(" ", strip=True)[:200]))
        links.sort(key=lambda hl: _ep_priority(hl[0], hl[1]))
        for href, label in links:
            if not href.startswith("http"):
                continue
            if _is_navigation_url(href, label):
                continue
            if "/zip/" in href.lower():
                continue  # batch-archive pages: not episode files, skip fast
            dest = href
            # Follow nested archive/redirect one more hop, then refetch.
            if "archive.toonworld4all" in href.lower() or "redirect" in href.lower() or is_shortener(href):
                nxt = await _bounded_bypass(href)
                if nxt and nxt != href:
                    # If bypass lands on another HTML page, refetch it.
                    if not is_valid_media_destination(nxt) and nxt.startswith("http") \
                            and not _is_navigation_url(nxt):
                        await _refetch_and_extract(nxt, depth + 1)
                        continue
                    dest = nxt
                else:
                    continue
            if dest in seen:
                continue
            seen.add(dest)
            # Real archive files only.
            if re.search(r"\.(zip|rar|7z)(\?|#|$)", dest.lower()):
                archive_urls.append(dest)
                continue
            if "archive.toonworld4all" in dest.lower():
                continue  # intermediate page, not a file
            if not is_valid_media_destination(dest):
                continue
            q = _detect_quality_from_text(dest + " " + label) or "Unknown"
            media_links.append({
                "quality": q, "url": dest, "provider": _infer_provider(dest, label),
                "requested_quality": quality_pref, "detected_quality": q,
                "verified_quality": q, "label": label,
            })
        for iframe in soup.find_all("iframe"):
            src = (iframe.get("src") or "").strip()
            if not src.startswith("http") or _is_navigation_url(src):
                continue
            if src in seen:
                continue
            seen.add(src)
            if not is_valid_media_destination(src):
                continue
            q = _detect_quality_from_text(src) or "Unknown"
            media_links.append({
                "quality": q, "url": src, "provider": _infer_provider(src),
                "requested_quality": quality_pref, "detected_quality": q,
                "verified_quality": q, "label": "iframe",
            })

    # If the input itself is an archive/redirect link, resolve first.
    start = page_url
    if "archive.toonworld4all" in page_url.lower() or "redirect" in page_url.lower() or is_shortener(page_url):
        dest = await detect_and_bypass(page_url)
        if dest and dest != page_url:
            start = dest
    await _refetch_and_extract(start, 0)
    # Also scan the original page HTML for direct episode links.
    if not media_links and not archive_urls and html:
        soup0 = BeautifulSoup(html, "html.parser")
        links0: list[tuple[str, str]] = []
        for a in soup0.find_all("a", href=True):
            links0.append(((a["href"] or "").strip(), a.get_text(" ", strip=True)[:200]))
        links0.sort(key=lambda hl: _ep_priority(hl[0], hl[1]))
        for href, label in links0:
            if not href.startswith("http"):
                continue
            if _is_navigation_url(href, label):
                continue
            if "/zip/" in href.lower():
                continue
            if "archive.toonworld4all" in href.lower() or "redirect" in href.lower() or is_shortener(href):
                dest = await _bounded_bypass(href)
                if dest and dest != href and dest not in seen:
                    seen.add(dest)
                    if re.search(r"\.(zip|rar|7z)(\?|#|$)", dest.lower()):
                        archive_urls.append(dest)
                    elif is_valid_media_destination(dest):
                        q = _detect_quality_from_text(dest + " " + label) or "Unknown"
                        media_links.append({
                            "quality": q, "url": dest, "provider": _infer_provider(dest, label),
                            "requested_quality": quality_pref, "detected_quality": q,
                            "verified_quality": q, "label": label,
                        })
    note = "redirect→refetch→validate" if ("redirect" in page_url.lower() or "archive" in page_url.lower()) else "page-scan"
    return media_links, sorted(set(archive_urls)), note


async def _resolve_generic_page(
    html: str, quality_pref: str,
    detect_and_bypass, is_shortener, is_valid_media_destination,
) -> list[dict]:
    """Strict generic scan for remaining sources (Unknown-safe)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = (a["href"] or "").strip()
        if not href.startswith("http") or len(href) < 12:
            continue
        label = a.get_text(" ", strip=True)[:200]
        if _is_navigation_url(href, label):
            continue
        q = _detect_quality_from_text(href + " " + label) or "Unknown"
        dest = href
        if is_shortener(href) or "redirect" in href.lower():
            dest = await detect_and_bypass(href)
            if not dest:
                continue
        if dest in seen:
            continue
        seen.add(dest)
        if _is_navigation_url(dest):
            continue
        if not is_valid_media_destination(dest):
            continue
        out.append({
            "quality": q, "url": dest, "provider": _infer_provider(dest, label),
            "requested_quality": quality_pref, "detected_quality": q,
            "verified_quality": q, "label": label,
        })
    for iframe in soup.find_all("iframe"):
        src = (iframe.get("src") or "").strip()
        if not src.startswith("http") or len(src) <= 12:
            continue
        if _is_navigation_url(src):
            continue
        q = _detect_quality_from_text(src) or "Unknown"
        if src in seen:
            continue
        seen.add(src)
        if not is_valid_media_destination(src):
            continue
        out.append({
            "quality": q, "url": src, "provider": _infer_provider(src),
            "requested_quality": quality_pref, "detected_quality": q,
            "verified_quality": q, "label": "iframe",
        })
    return out


async def resolve_bypass_url(url: str, quality_pref: str = "1080p") -> dict:
    """Website-dispatched universal resolver (V3 #3).

    Never returns fake results: unsupported sites → {"ok": False,
    "error": "Unsupported Source ..."}; HTML/navigation pages are never
    reported as media URLs (validated via is_valid_media_destination +
    navigation rejection). Failure keeps the real stage (never "done").
    """
    from extractors.shortener import detect_and_bypass, is_shortener, is_valid_media_destination

    original_url = (url or "").strip()
    result: dict = {
        "ok": False,
        "source": None,
        "provider": None,
        "original_url": original_url,
        "final_url": original_url,
        "resolved_url": original_url,
        "anime": "",
        "season": None,
        "episode": None,
        "qualities": [],
        "media_links": [],
        "archive_links": [],
        "providers": {},
        "resolver_stage": "detect",
        "fallback_stage": "",
        "failure_reason": "",
        "stage": "detect",
        "error": "",
    }
    if not original_url or not original_url.lower().startswith(("http://", "https://")):
        result["error"] = "Provide a public http(s) page/episode URL: /bypass <URL>"
        result["failure_reason"] = result["error"]
        return result

    source = detect_source(original_url)
    if not source:
        result["stage"] = "detect"
        result["resolver_stage"] = "detect"
        result["error"] = f"Unsupported Source for {urlparse(original_url).netloc or original_url} — no resolver registered."
        result["failure_reason"] = result["error"]
        return result
    result["source"] = source
    result["resolver_stage"] = f"{source} dispatcher"

    # ── Stage: redirect chain ──────────────────────────────────────────
    curr = original_url
    try:
        if is_shortener(curr) or "redirect" in curr.lower():
            bypassed = await detect_and_bypass(curr)
            if bypassed and bypassed != curr:
                curr = bypassed
        final_url, html = await _fetch_public(curr)
        result["final_url"] = final_url or curr
        result["resolved_url"] = result["final_url"]
        result["stage"] = "fetch"
        result["resolver_stage"] = f"{source} → fetch"
    except Exception as e:
        result["stage"] = "fetch"
        result["resolver_stage"] = f"{source} → fetch (failed)"
        result["error"] = f"Fetch failed: {e}"
        result["failure_reason"] = result["error"]
        return result

    if not html or len(html) < 500:
        result["stage"] = "fetch"
        result["error"] = "Page fetch returned empty/blocked content (Cloudflare/antibot?)."
        result["failure_reason"] = result["error"]
        return result
    if _is_challenge_html(html):
        result["stage"] = "fetch"
        result["error"] = "Page is behind a bot challenge/CAPTCHA — refusing to guess links."
        result["failure_reason"] = result["error"]
        return result

    # ── Stage: validate anime/season/episode ─────────────────────────
    anime, season, episode = _parse_title_season_episode(result["final_url"], html)
    result["anime"] = anime
    result["season"] = season
    result["episode"] = episode
    result["stage"] = "validate"
    result["resolver_stage"] = f"{source} → validate"
    if not anime or len(anime) < 3:
        result["error"] = "Could not validate anime title from URL/page — refusing to guess."
        result["failure_reason"] = result["error"]
        return result

    # ── Stage: website-specific resolution (V3 #3 dispatch) ──────────
    result["stage"] = "resolve"
    try:
        media_links: list[dict] = []
        archive_urls: list[str] = []
        providers: dict = {}
        if source == "AnimeDubHindi":
            result["resolver_stage"] = "AnimeDubHindi → provider blocks → Direct Media"
            media_links, providers = await _resolve_animedubhindi_page(
                html, result["final_url"], quality_pref,
                detect_and_bypass, is_shortener, is_valid_media_destination,
            )
            result["providers"] = providers
        elif source == "ToonWorld4All":
            result["resolver_stage"] = "ToonWorld4All → redirect → refetch → Direct Media"
            media_links, archive_urls, note = await _resolve_toonworld_url(
                result["final_url"], html, quality_pref,
                detect_and_bypass, is_shortener, is_valid_media_destination,
            )
            result["fallback_stage"] = note
        else:
            result["resolver_stage"] = f"{source} → page scan → Direct Media"
            media_links = await _resolve_generic_page(
                html, quality_pref, detect_and_bypass, is_shortener, is_valid_media_destination,
            )

        # Dedupe by URL, collect quality set (Unknown-safe, V3 #4).
        uniq: dict[str, dict] = {}
        for m in media_links:
            uniq.setdefault(m["url"], m)
        media_links = list(uniq.values())
        qualities = sorted({m["quality"] for m in media_links},
                           key=lambda x: {"480p": 0, "720p": 1, "1080p": 2, "4K": 3, "Unknown": 9}.get(x, 9))
        result["media_links"] = media_links
        result["archive_links"] = sorted(set(archive_urls))
        result["qualities"] = qualities
        if media_links:
            bymedia = {}
            for m in media_links:
                bymedia[m.get("provider", "Direct")] = bymedia.get(m.get("provider", "Direct"), 0) + 1
            top_provider = max(bymedia, key=bymedia.get)
            result["provider"] = top_provider

        if not media_links and not archive_urls:
            # V3 #11: failure stage is the real stage, never "done".
            result["stage"] = "extract"
            result["error"] = "No public download/media/archive links found on this page."
            result["failure_reason"] = result["error"]
            return result
        result["stage"] = "done"
        result["ok"] = True
        return result
    except Exception as e:
        result["stage"] = "extract"
        result["error"] = f"Extraction failed: {e}"
        result["failure_reason"] = result["error"]
        return result
