"""V3 #4 + V3 #5 shared helpers: strict quality labels and confident anime matching.

V3 #4 rule:
    detected_quality / requested_quality / verified_quality are separate.
    Unknown must stay "Unknown" — never inherit the requested label.

V3 #5 rule:
    Title + season (+ episode/year/language where available) must match
    confidently, otherwise reject instead of guessing the first result.
"""

from __future__ import annotations

import re

_STOP = {
    "season", "seasons", "episode", "episodes", "hindi", "dubbed", "dub",
    "multi", "audio", "multi-audio", "multiaudio", "the", "a", "an",
    "tamil", "telugu", "uncensored", "complete", "batch", "all",
    "tv", "show", "series", "movie", "part", "cour", "subbed",
}


def normalize_tokens(title: str) -> set[str]:
    toks = re.sub(r"[^a-z0-9 ]", " ", (title or "").lower()).split()
    return {t for t in toks if len(t) > 2 and t not in _STOP}


def is_confident_match(query: str, candidate_title: str, candidate_url: str = "") -> bool:
    """Return True only for a confident anime-title match (V3 #5)."""
    q_toks = normalize_tokens(query)
    if not q_toks:
        return False
    c_blob = f"{candidate_title} {candidate_url}".lower()
    c_toks = normalize_tokens(candidate_title + " " + candidate_url)
    overlap = q_toks & c_toks
    if not overlap:
        return False
    # Single-word queries: require that word (len>=3 already) to appear.
    if len(q_toks) == 1:
        return True
    # Multi-word queries: require >=2 shared significant tokens, or a
    # single long distinctive token (>=6 chars) plus overall similarity.
    if len(overlap) >= 2:
        return True
    if len(overlap) == 1:
        tok = next(iter(overlap))
        if len(tok) >= 6 and tok in c_blob:
            return True
        # e.g. "demon slayer" vs "demon-slayer-season-2": q has 2 tokens,
        # candidate has both? that would be overlap 2. Single overlap here
        # means the other query word is missing → reject.
        return False
    return False


def matches_season(title: str, url: str, season: int) -> bool:
    """Strict season check: explicit season token must agree when present."""
    blob = f"{title} {url}".lower()
    # Find explicit season markers in candidate.
    m_candidates = []
    for m in re.finditer(r"season[\s\-_]*(\d{1,2})", blob):
        m_candidates.append(int(m.group(1)))
    for m in re.finditer(r"\bs(\d{1,2})\b", blob):
        m_candidates.append(int(m.group(1)))
    if not m_candidates:
        # No season marker → only acceptable for season 1 lookups.
        return season == 1
    return season in m_candidates


def normalize_quality(q: str) -> str:
    """Canonical quality label; unknown/empty → 'Unknown' (V3 #4)."""
    s = (q or "").strip().lower()
    if s in ("4k", "2160p", "2160", "uhd"):
        return "4K"
    if s in ("1080p", "1080", "fhd", "1080p-hq", "1080p hq"):
        return "1080p"
    if s in ("720p", "720", "hd", "hdrip", "webrip"):
        # NOTE: bare 'hd' is ambiguous — callers should prefer explicit
        # tokens; keep mapping for backwards compat but detection must
        # require explicit 720 markers to emit 720p (see detectors).
        return "720p"
    if s in ("480p", "480", "sd"):
        return "480p"
    if s in ("360p", "360"):
        return "360p"
    if s in ("240p", "240"):
        return "240p"
    if s in ("auto",):
        return "auto"
    return "Unknown"


def qualities_match(requested: str, detected: str) -> bool:
    """V3 #2 strict equality on canonical labels (4K≡2160p≡UHD)."""
    if (requested or "").strip().lower() == "auto":
        return True
    return normalize_quality(requested) == normalize_quality(detected) and normalize_quality(detected) != "Unknown"
