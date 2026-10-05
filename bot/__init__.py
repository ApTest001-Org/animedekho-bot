"""AnimeDekho bot package.

The application factory is imported lazily so lightweight modules (database
helpers, parser tests, and maintenance scripts) do not require the Telegram
runtime just to import ``bot``.
"""

from __future__ import annotations
from typing import Any


__all__ = ["create_app"]


def create_app(*args: Any, **kwargs: Any):
    """Build the Telegram application on demand.

    Keeping this import lazy avoids importing WZGram/Pyrogram, image helpers,
    and all handler modules for callers that only need a bot utility module.
    """
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)
