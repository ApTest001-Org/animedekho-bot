#!/usr/bin/env python3
"""AnimeDekho Telegram Bot — entrypoint (WZGram/MTProto)."""

import logging
import sys

from config.settings import settings
from bot.app import create_app


import asyncio
try:
    from wzgram import idle
except ImportError:
    from pyrogram import idle

async def async_main():
    app = create_app()
    await app.start()
    
    if hasattr(app, "on_start") and callable(app.on_start):
        await app.on_start(app)
        
    await idle()
    
    if hasattr(app, "on_stop") and callable(app.on_stop):
        await app.on_stop(app)
        
    await app.stop()

def main():
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass

    logging.basicConfig(
        level=getattr(logging, settings.bot.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # Filter routine 1-2s internal SaveBigFilePart floodwait warnings (Issue #7)
    class UploadFloodWaitFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            msg = record.getMessage()
            if "SaveBigFilePart" in msg and ("Waiting for 1" in msg or "Waiting for 2" in msg):
                return False
            return True

    logging.getLogger("pyrogram.session.session").addFilter(UploadFloodWaitFilter())
    logging.getLogger("wzgram.session.session").addFilter(UploadFloodWaitFilter())

    log = logging.getLogger("animedekho")
    log.info("Starting AnimeDekho Bot (WZGram/MTProto)...")

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        log.info("Shutting down...")
    except Exception as e:
        log.critical("Fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
