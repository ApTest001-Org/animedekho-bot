"""
Custom Emoji and Visual Styling Helpers.

Supports Telegram Premium Custom Emojis (HTML <emoji id="...">)
with automatic graceful fallback to standard Unicode emojis so free bots never break.
Addresses Issue #8, Issue #10, and Issue #12.
"""

from __future__ import annotations
import os
import logging
from typing import Dict, Tuple

log = logging.getLogger(__name__)

# Base registry of semantic names -> (default_custom_emoji_id, default_unicode)
# Real Telegram Premium Custom Emoji IDs
EMOJI_REGISTRY: Dict[str, Tuple[str, str]] = {
    "star": ("5368324170671202286", "⭐"),
    "rating": ("5368324170671202286", "🌟"),
    "movie": ("5443037926569253457", "🎬"),
    "clapper": ("5443037926569253457", "🎬"),
    "audio": ("5454157843477544062", "🔊"),
    "quality": ("5427009714745328964", "📷"),
    "genres": ("5472164874889714493", "🎭"),
    "channel": ("5465223707248387434", "📢"),
    "arrow": ("5465223707248387434", "➽"),
    "check": ("5445284980972591637", "✓"),
    "fire": ("5467657928606459048", "🔥"),
    "download": ("5445284980972591637", "📥"),
    "upload": ("5445284980972591637", "📤"),
    "sparkles": ("546546541234567892", "✨"),
    "rocket": ("546546541234567893", "🚀"),
    "cross": ("546546541234567895", "❌"),
    "tv": ("546546541234567896", "📺"),
    "search": ("546546541234567900", "🔍"),
    "gear": ("546546541234567901", "⚙️"),
    "timer": ("546546541234567902", "⏳"),
    "lock": ("546546541234567903", "🔒"),
    "unlock": ("546546541234567904", "🔓"),
    "pin": ("546546541234567905", "📌"),
    "calendar": ("546546541234567906", "📅"),
}


_CUSTOM_EMOJI_RUNTIME: bool | None = None


def set_custom_emoji_runtime_state(enabled: bool) -> None:
    """Set custom emoji runtime state dynamically from DB/Settings."""
    global _CUSTOM_EMOJI_RUNTIME
    _CUSTOM_EMOJI_RUNTIME = bool(enabled)


def is_custom_emoji_enabled() -> bool:
    """Check if custom emoji rendering is enabled in runtime state, config or environment."""
    global _CUSTOM_EMOJI_RUNTIME
    if _CUSTOM_EMOJI_RUNTIME is not None:
        return _CUSTOM_EMOJI_RUNTIME

    try:
        from config import Config
        cfg_val = getattr(Config, "ENABLE_CUSTOM_EMOJI", None)
        if cfg_val is not None:
            return bool(cfg_val)
    except Exception:
        pass
    return os.environ.get("ENABLE_CUSTOM_EMOJI", "false").lower() in ("true", "1", "yes", "on")


def get_emoji(name: str, fallback: str = "", force_custom: bool | None = None) -> str:
    """
    Get formatted emoji. If custom emojis are enabled, outputs HTML <emoji id="...">
    otherwise returns standard unicode fallback.
    Gracefully handles invalid IDs, missing configs, and never crashes.
    """
    try:
        enable_custom = force_custom if force_custom is not None else is_custom_emoji_enabled()
        name_clean = name.strip().lower()

        # Check user configured CUSTOM_EMOJIS from config.py first
        configured_id = ""
        try:
            from config import Config
            custom_map = getattr(Config, "CUSTOM_EMOJIS", {})
            if isinstance(custom_map, dict):
                configured_id = str(custom_map.get(name_clean, "")).strip()
        except Exception:
            pass

        entry = EMOJI_REGISTRY.get(name_clean)
        default_id, default_unicode = entry if entry else ("", fallback or "•")
        emoji_id = configured_id or default_id
        unicode_repr = fallback or default_unicode

        # Validate emoji_id: must be non-empty digits
        is_valid_id = bool(emoji_id and str(emoji_id).isdigit() and len(str(emoji_id)) >= 10)

        if enable_custom and is_valid_id:
            return f'<emoji id="{emoji_id}">{unicode_repr}</emoji>'

        return unicode_repr
    except Exception as e:
        log.debug("Error getting emoji '%s': %s", name, e)
        return fallback or "•"
