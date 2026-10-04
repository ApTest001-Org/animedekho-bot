"""Owner/admin-only /bypass manual resolver (V2 #23)."""

from __future__ import annotations

import logging

from bot.telegram import Client, enums
from bot.telegram.types import Message
from bot.auth import require_owner
from utils.helpers import esc

log = logging.getLogger(__name__)


@require_owner
async def cmd_bypass(client: Client, message: Message):
    """Resolve a supported public page/episode URL into download info.

    Usage:
        /bypass https://toonworld4all.me/...
        /bypass https://archive.toonworld4all.me/episode/...
    """
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.reply_text(
            "🔗 <b>/bypass Manual Resolver</b>\n\n"
            "Usage: <code>/bypass &lt;public page/episode URL&gt;</code>\n\n"
            "Supported: AnimeDubHindi, ToonWorld4All, ToonAnime, RareAnimes, "
            "DeadToons, TOONo, AnimeDrive, ToonFlix.",
            parse_mode=enums.ParseMode.HTML,
        )
        return

    target_url = parts[1].strip().split()[0]
    status = await message.reply_text(
        f"🔎 <b>Resolving source...</b>\n<code>{esc(target_url[:120])}</code>",
        parse_mode=enums.ParseMode.HTML,
    )
    try:
        from extractors.bypass import resolve_bypass_url
        res = await resolve_bypass_url(target_url)
    except Exception as e:
        log.exception("bypass resolve crashed for %s", target_url[:100])
        try:
            await status.edit_text(f"❌ <b>Bypass crashed:</b> {esc(str(e)[:200])}", parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
        return

    if not res.get("ok"):
        stage = res.get("stage", "?")
        err = res.get("error", "resolution failed")
        src = res.get("source") or "unknown"
        try:
            await status.edit_text(
                f"❌ <b>Automatic resolution failed</b>\n\n"
                f"🔗 Source: {esc(str(src))}\n"
                f"🌐 URL: <code>{esc(target_url[:150])}</code>\n"
                f"🧩 Failed Stage: {esc(str(stage))}\n"
                f"📝 Reason: {esc(str(err)[:400])}",
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception:
            pass
        return

    lines = [
        f"✅ <b>Source:</b> {esc(str(res.get('source')))}",
        f"🎬 <b>Anime:</b> {esc(str(res.get('anime')))}",
    ]
    if res.get("season") is not None:
        lines.append(f"📂 <b>Season:</b> {res.get('season')}")
    if res.get("episode") is not None:
        lines.append(f"🎞️ <b>Episode/Page:</b> {res.get('episode')}")
    quals = res.get("qualities") or []
    if quals:
        lines.append(f"🎚️ <b>Available Qualities:</b> {esc(' / '.join(quals))}")
    lines.append(f"🌐 <b>Final URL:</b> <code>{esc(str(res.get('final_url'))[:200])}</code>")
    lines.append("")
    lines.append("✅ <b>Resolved Download/Media Links:</b>")
    for m in (res.get("media_links") or [])[:10]:
        q = esc(str(m.get("quality", "?")))
        u = esc(str(m.get("url", ""))[:200])
        lines.append(f"   • {q} → <code>{u}</code>")
    if res.get("archive_links"):
        lines.append("")
        lines.append("📦 <b>ZIP/Archive Links:</b>")
        for u in (res.get("archive_links") or [])[:5]:
            lines.append(f"   • <code>{esc(str(u)[:200])}</code>")
    lines.append("")
    lines.append(f"🧩 Resolver stage: {esc(str(res.get('stage')))}")
    text = "\n".join(lines)[:4000]
    try:
        await status.edit_text(text, parse_mode=enums.ParseMode.HTML)
    except Exception:
        try:
            await message.reply_text(text, parse_mode=enums.ParseMode.HTML)
        except Exception:
            pass
