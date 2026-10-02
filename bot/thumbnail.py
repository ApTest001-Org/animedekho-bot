"""
Auto Thumbnail Generator for AnimeDekho Bot — Modular Multi-Template Architecture.

Supports 5 distinct visual designs + random mode:
1. 'modern': Modern vibrant gradient with high-contrast pills & badges.
2. 'cinematic': Moody widescreen letterbox with theatrical glow & silver frame.
3. 'movie_gold': Luxury obsidian & gold VIP aesthetic (tailored for movies).
4. 'neon_cyber': Futuristic cyberpunk with electric cyan & hot pink neon glow.
5. 'minimal': Clean frosted glass card with refined minimalist typography.

Supports template selection via config.py and /settings, plus automatic random template mode.
Addresses Issue #11 and Issue #12.
"""

from __future__ import annotations

import logging
import os
import random
import re
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, Type

from PIL import Image, ImageDraw, ImageFont, ImageFilter

log = logging.getLogger(__name__)

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

# System fonts priority
FONT_PATHS = [
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    # Windows
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNSText.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load system font if available, fallback to default."""
    for p in FONT_PATHS:
        if not bold and "Bold" in p:
            continue
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    # Fallback to any existing font path
    for p in FONT_PATHS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _round_corners(img: Image.Image, radius: int) -> Image.Image:
    """Round the corners of an image with smooth antialiasing."""
    mask = Image.new("L", (img.width * 2, img.height * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.width * 2, img.height * 2), radius * 2, fill=255)
    mask = mask.resize((img.width, img.height), Image.Resampling.LANCZOS)
    output = img.copy().convert("RGBA")
    output.putalpha(mask)
    return output


def _prepare_blurred_bg(poster_path: str, blur_radius: int = 28) -> Image.Image | None:
    """Scale, center-crop, and blur a poster to cover the 1280x720 canvas."""
    if not poster_path or not os.path.exists(poster_path):
        return None
    try:
        with Image.open(poster_path) as p_img:
            p_img = p_img.convert("RGBA")
            scale = max(CANVAS_WIDTH / p_img.width, CANVAS_HEIGHT / p_img.height)
            nw = int(p_img.width * scale)
            nh = int(p_img.height * scale)
            scaled = p_img.resize((nw, nh), Image.Resampling.LANCZOS)
            x1 = (nw - CANVAS_WIDTH) // 2
            y1 = (nh - CANVAS_HEIGHT) // 2
            cropped = scaled.crop((x1, y1, x1 + CANVAS_WIDTH, y1 + CANVAS_HEIGHT))
            return cropped.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    except Exception as e:
        log.debug("Failed preparing blurred background: %s", e)
        return None


def _clean_title(title: str, max_words_per_line: int = 24) -> list[str]:
    """Clean title tags and wrap into 1 or 2 lines."""
    clean = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip()
    if not clean:
        clean = title[:40]
    words = clean.split()
    lines = []
    cur_line = []
    for w in words:
        if len(" ".join(cur_line + [w])) <= max_words_per_line:
            cur_line.append(w)
        else:
            if cur_line:
                lines.append(" ".join(cur_line))
            cur_line = [w]
    if cur_line:
        lines.append(" ".join(cur_line))
    return lines[:2]


# ── Modular Template Base & Registry ───────────────────────────────────────

TEMPLATES: Dict[str, Type["BaseThumbnailTemplate"]] = {}


def register_template(name: str):
    """Decorator to register a thumbnail template class."""
    def decorator(cls: Type["BaseThumbnailTemplate"]):
        TEMPLATES[name.lower().strip()] = cls
        return cls
    return decorator


class BaseThumbnailTemplate:
    """Abstract base class for all auto-thumbnail templates."""
    name: str = "base"
    display_name: str = "Base Template"
    description: str = "Base thumbnail template"

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = False,
    ) -> str | None:
        raise NotImplementedError


# ── Template 1: Modern Gradient (Original Enhanced) ────────────────────────

@register_template("modern")
class ModernGradientTemplate(BaseThumbnailTemplate):
    """Modern vibrant gradient with high-contrast pills and gold badges."""
    name = "modern"
    display_name = "Modern Gradient"
    description = "Clean modern dark gradient with vibrant pills and bold typography."

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = False,
    ) -> str | None:
        try:
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (15, 17, 24, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=28)
            if bg:
                canvas.paste(bg, (0, 0))

            # Dark Cinematic Gradient Overlay
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(140 + (y / CANVAS_HEIGHT) * 90)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(10, 12, 18, alpha))
            for x in range(CANVAS_WIDTH):
                if x > 400:
                    alpha = int(((x - 400) / (CANVAS_WIDTH - 400)) * 90)
                    draw_ov.line([(x, 0), (x, CANVAS_HEIGHT)], fill=(6, 8, 14, alpha))
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Foreground Poster
            poster_w, poster_h = 360, 520
            poster_x, poster_y = 60, 100
            if poster_path and os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as p_img:
                        p_img = p_img.convert("RGBA")
                        p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                        p_rounded = _round_corners(p_resized, radius=18)
                        draw.rounded_rectangle(
                            (poster_x - 3, poster_y - 3, poster_x + poster_w + 3, poster_y + poster_h + 3),
                            radius=21, fill=(255, 255, 255, 30), outline=(255, 255, 255, 120), width=2,
                        )
                        canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Could not paste foreground poster: %s", pe)

            text_x = 470
            curr_y = 110
            font_pill = _get_font(22)
            font_title = _get_font(48)
            font_sub = _get_font(26)
            font_brand = _get_font(22)

            # Quality Pill
            q_label = quality.upper()
            if "1080" in q_label:
                q_text = "1080P • FULL HD"
                pill_color = (220, 38, 38, 230)
            elif "720" in q_label:
                q_text = "720P • HD"
                pill_color = (37, 99, 235, 230)
            elif "4K" in q_label or "2160" in q_label:
                q_text = "4K • ULTRA HD"
                pill_color = (147, 51, 234, 230)
            else:
                q_text = f"{q_label} • HD"
                pill_color = (13, 148, 136, 230)

            pw = 190
            ph = 42
            draw.rounded_rectangle((text_x, curr_y, text_x + pw, curr_y + ph), radius=10, fill=pill_color)
            draw.text((text_x + 16, curr_y + 9), q_text, font=font_pill, fill=(255, 255, 255, 255))

            # Audio Pill
            audio_text = f"🎙️ {audio}" if audio else "🎙️ Hindi Dub"
            aw = 220
            draw.rounded_rectangle(
                (text_x + pw + 15, curr_y, text_x + pw + 15 + aw, curr_y + ph),
                radius=10, fill=(30, 41, 59, 220), outline=(100, 116, 139, 180), width=1,
            )
            draw.text((text_x + pw + 28, curr_y + 9), audio_text, font=font_pill, fill=(241, 245, 249, 255))
            curr_y += 75

            # Title
            lines = _clean_title(title)
            for line in lines:
                draw.text((text_x + 2, curr_y + 2), line, font=font_title, fill=(0, 0, 0, 180))
                draw.text((text_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += 58
            curr_y += 15

            # Episode / Movie Badge
            ep_tag = "FEATURE FILM" if is_movie and not episode_info else (episode_info.upper() if episode_info else "COMPLETE RELEASE")
            ep_box_w = 360
            ep_box_h = 56
            draw.rounded_rectangle(
                (text_x, curr_y, text_x + ep_box_w, curr_y + ep_box_h),
                radius=12, fill=(245, 158, 11, 240),
            )
            draw.text((text_x + 22, curr_y + 13), ep_tag, font=_get_font(28), fill=(17, 24, 39, 255))
            curr_y += 85

            # Divider
            draw.line([(text_x, curr_y), (CANVAS_WIDTH - 60, curr_y)], fill=(255, 255, 255, 50), width=2)
            curr_y += 30

            # Features & Branding
            tagline = "⚡ Multi-Audio • High Speed Direct Play • Dual Audio"
            draw.text((text_x, curr_y), tagline, font=font_sub, fill=(148, 163, 184, 255))
            curr_y += 45
            brand_text = f"✦ Powered by @{bot_username.lstrip('@')}"
            draw.text((text_x, curr_y), brand_text, font=font_brand, fill=(96, 165, 250, 255))

            final_img = canvas.convert("RGB")
            final_img.save(output_path, "JPEG", quality=92, optimize=True)
            return output_path
        except Exception as e:
            log.error("ModernGradientTemplate generation error: %s", e)
            return None


# ── Template 2: Cinematic Glow ─────────────────────────────────────────────

@register_template("cinematic")
class CinematicGlowTemplate(BaseThumbnailTemplate):
    """Moody widescreen letterbox with theatrical glow and silver accents."""
    name = "cinematic"
    display_name = "Cinematic Glow"
    description = "Theatrical letterbox look with atmospheric indigo glow and silver borders."

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = False,
    ) -> str | None:
        try:
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (5, 7, 12, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=35)
            if bg:
                canvas.paste(bg, (0, 0))

            # Deep moody overlay with central blue/violet glow
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(170 + (y / CANVAS_HEIGHT) * 60)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(8, 10, 20, alpha))
            # Widescreen letterbox bars (top & bottom 35px)
            draw_ov.rectangle([(0, 0), (CANVAS_WIDTH, 38)], fill=(0, 0, 0, 255))
            draw_ov.rectangle([(0, CANVAS_HEIGHT - 38), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill=(0, 0, 0, 255))
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with silver double border
            poster_w, poster_h = 350, 500
            poster_x, poster_y = 70, 110
            if poster_path and os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as p_img:
                        p_img = p_img.convert("RGBA")
                        p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                        p_rounded = _round_corners(p_resized, radius=12)
                        # Silver outer border
                        draw.rounded_rectangle(
                            (poster_x - 4, poster_y - 4, poster_x + poster_w + 4, poster_y + poster_h + 4),
                            radius=16, fill=(0, 0, 0, 80), outline=(203, 213, 225, 200), width=2,
                        )
                        canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Cinematic poster error: %s", pe)

            text_x = 480
            curr_y = 125

            # Top Cinema Header
            draw.text((text_x, curr_y), "◆ THEATRICAL MASTER • HD RELEASE ◆", font=_get_font(20), fill=(148, 163, 184, 255))
            curr_y += 40

            # Title
            lines = _clean_title(title)
            for line in lines:
                draw.text((text_x + 2, curr_y + 2), line, font=_get_font(46), fill=(0, 0, 0, 220))
                draw.text((text_x, curr_y), line, font=_get_font(46), fill=(255, 255, 255, 255))
                curr_y += 56
            curr_y += 20

            # Cinema Badges
            ep_tag = "★ FULL MOVIE PRESENTATION ★" if is_movie or not episode_info else f"★ {episode_info.upper()} ★"
            bw = 420
            bh = 52
            draw.rounded_rectangle((text_x, curr_y, text_x + bw, curr_y + bh), radius=8, fill=(30, 41, 59, 230), outline=(56, 189, 248, 160), width=1)
            draw.text((text_x + 18, curr_y + 12), ep_tag, font=_get_font(24), fill=(224, 242, 254, 255))
            curr_y += 75

            # Quality & Audio Info
            draw.text((text_x, curr_y), f"RESOLUTION : {quality.upper()} ULTRA STREAM", font=_get_font(22), fill=(56, 189, 248, 255))
            curr_y += 34
            draw.text((text_x, curr_y), f"AUDIO TRACK : {audio.upper()}", font=_get_font(22), fill=(203, 213, 225, 255))
            curr_y += 45

            # Watermark in Letterbox bar
            draw.text((CANVAS_WIDTH - 300, CANVAS_HEIGHT - 30), f"@{bot_username.lstrip('@')} • CINEMA", font=_get_font(18), fill=(100, 116, 139, 255))

            final_img = canvas.convert("RGB")
            final_img.save(output_path, "JPEG", quality=92, optimize=True)
            return output_path
        except Exception as e:
            log.error("CinematicGlowTemplate generation error: %s", e)
            return None


# ── Template 3: Movie Gold (Luxury VIP) ────────────────────────────────────

@register_template("movie_gold")
class MovieGoldTemplate(BaseThumbnailTemplate):
    """Luxury obsidian and gold theme designed specifically for movies and VIP releases."""
    name = "movie_gold"
    display_name = "Movie Gold VIP"
    description = "Luxury gold borders and warm obsidian tones tailored for movie premieres."

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = True,
    ) -> str | None:
        try:
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (12, 10, 6, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=30)
            if bg:
                canvas.paste(bg, (0, 0))

            # Warm dark gold ambient gradient
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(160 + (y / CANVAS_HEIGHT) * 80)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(12, 10, 8, alpha))
            # Outer Gold Border frame
            draw_ov.rectangle([(15, 15), (CANVAS_WIDTH - 15, CANVAS_HEIGHT - 15)], outline=(212, 175, 55, 120), width=2)
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with Gold Frame
            poster_w, poster_h = 360, 520
            poster_x, poster_y = 65, 100
            if poster_path and os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as p_img:
                        p_img = p_img.convert("RGBA")
                        p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                        p_rounded = _round_corners(p_resized, radius=14)
                        # Double Gold Border
                        draw.rounded_rectangle(
                            (poster_x - 4, poster_y - 4, poster_x + poster_w + 4, poster_y + poster_h + 4),
                            radius=18, fill=(0, 0, 0, 100), outline=(212, 175, 55, 230), width=3,
                        )
                        canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Movie gold poster error: %s", pe)

            text_x = 480
            curr_y = 110

            # Gold VIP Header
            header_text = "★ OFFICIAL MOVIE PREMIERE ★" if is_movie else "★ SPECIAL VIP BROADCAST ★"
            draw.rounded_rectangle((text_x, curr_y, text_x + 360, curr_y + 36), radius=6, fill=(212, 175, 55, 40), outline=(212, 175, 55, 180), width=1)
            draw.text((text_x + 18, curr_y + 7), header_text, font=_get_font(18), fill=(245, 210, 100, 255))
            curr_y += 55

            # Title
            lines = _clean_title(title)
            for line in lines:
                draw.text((text_x + 2, curr_y + 2), line, font=_get_font(46), fill=(0, 0, 0, 240))
                draw.text((text_x, curr_y), line, font=_get_font(46), fill=(255, 255, 255, 255))
                curr_y += 56
            curr_y += 18

            # Golden Main Badge
            main_tag = "FEATURE FILM • DUAL AUDIO" if is_movie and not episode_info else (episode_info.upper() if episode_info else "SPECIAL EDITION")
            bw = 430
            bh = 58
            draw.rounded_rectangle((text_x, curr_y, text_x + bw, curr_y + bh), radius=10, fill=(212, 175, 55, 240))
            draw.text((text_x + 20, curr_y + 14), main_tag, font=_get_font(26), fill=(24, 18, 5, 255))
            curr_y += 85

            # Quality & Audio Pills
            draw.text((text_x, curr_y), f"👑 QUALITY: {quality.upper()} ULTRA HD", font=_get_font(22), fill=(245, 210, 100, 255))
            curr_y += 34
            draw.text((text_x, curr_y), f"🎙️ AUDIO: {audio}", font=_get_font(22), fill=(243, 244, 246, 255))
            curr_y += 45

            # Gold Divider & Branding
            draw.line([(text_x, curr_y), (CANVAS_WIDTH - 65, curr_y)], fill=(212, 175, 55, 80), width=2)
            curr_y += 20
            draw.text((text_x, curr_y), f"✦ VIP Release by @{bot_username.lstrip('@')}", font=_get_font(20), fill=(212, 175, 55, 220))

            final_img = canvas.convert("RGB")
            final_img.save(output_path, "JPEG", quality=92, optimize=True)
            return output_path
        except Exception as e:
            log.error("MovieGoldTemplate generation error: %s", e)
            return None


# ── Template 4: Neon Cyber (Cyberpunk Anime) ───────────────────────────────

@register_template("neon_cyber")
class NeonCyberTemplate(BaseThumbnailTemplate):
    """Cyberpunk neon aesthetic with electric cyan and hot magenta borders."""
    name = "neon_cyber"
    display_name = "Neon Cyber"
    description = "Cyberpunk glowing neon aesthetic with dual cyan and magenta accents."

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = False,
    ) -> str | None:
        try:
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (7, 7, 15, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=25)
            if bg:
                canvas.paste(bg, (0, 0))

            # Dark overlay with slight magenta bottom tint
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(160 + (y / CANVAS_HEIGHT) * 80)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(8, 8, 18, alpha))
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with Cyber Neon Dual Border (Cyan top/left, Pink bottom/right)
            poster_w, poster_h = 360, 520
            poster_x, poster_y = 65, 100
            if poster_path and os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as p_img:
                        p_img = p_img.convert("RGBA")
                        p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                        p_rounded = _round_corners(p_resized, radius=8)
                        # Cyan & Pink neon glow borders
                        draw.rounded_rectangle(
                            (poster_x - 5, poster_y - 5, poster_x + poster_w + 5, poster_y + poster_h + 5),
                            radius=12, fill=(0, 0, 0, 80), outline=(0, 240, 255, 230), width=2,
                        )
                        draw.rounded_rectangle(
                            (poster_x - 2, poster_y - 2, poster_x + poster_w + 2, poster_y + poster_h + 2),
                            radius=10, fill=None, outline=(255, 0, 128, 200), width=2,
                        )
                        canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Neon cyber poster error: %s", pe)

            text_x = 480
            curr_y = 105

            # Cyber Header Badge
            draw.text((text_x, curr_y), "// CYBER DIRECT LINK // SPEED 10Gbps", font=_get_font(20), fill=(0, 240, 255, 255))
            curr_y += 45

            # Title
            lines = _clean_title(title)
            for line in lines:
                # Cyan text glow
                draw.text((text_x + 2, curr_y + 2), line, font=_get_font(46), fill=(0, 240, 255, 160))
                draw.text((text_x, curr_y), line, font=_get_font(46), fill=(255, 255, 255, 255))
                curr_y += 56
            curr_y += 18

            # Cyber Episode Tag
            ep_tag = "// MOVIE RELEASE //" if is_movie or not episode_info else f"// {episode_info.upper()} //"
            bw = 420
            bh = 54
            draw.rectangle((text_x, curr_y, text_x + bw, curr_y + bh), fill=(255, 0, 128, 220), outline=(0, 240, 255, 255), width=2)
            draw.text((text_x + 22, curr_y + 12), ep_tag, font=_get_font(26), fill=(255, 255, 255, 255))
            curr_y += 82

            # Badges
            draw.text((text_x, curr_y), f"⚡ QUALITY: [ {quality.upper()} ]", font=_get_font(22), fill=(0, 240, 255, 255))
            curr_y += 34
            draw.text((text_x, curr_y), f"🎙️ AUDIO: [ {audio.upper()} ]", font=_get_font(22), fill=(255, 0, 128, 255))
            curr_y += 48

            # Neon Divider
            draw.line([(text_x, curr_y), (CANVAS_WIDTH - 60, curr_y)], fill=(0, 240, 255, 140), width=2)
            curr_y += 20
            draw.text((text_x, curr_y), f"SYS.OP: @{bot_username.lstrip('@')}", font=_get_font(20), fill=(148, 163, 184, 255))

            final_img = canvas.convert("RGB")
            final_img.save(output_path, "JPEG", quality=92, optimize=True)
            return output_path
        except Exception as e:
            log.error("NeonCyberTemplate generation error: %s", e)
            return None


# ── Template 5: Minimal Card (Frosted Glass) ──────────────────────────────

@register_template("minimal")
class MinimalCardTemplate(BaseThumbnailTemplate):
    """Clean frosted glass card with refined minimalist typography."""
    name = "minimal"
    display_name = "Minimal Card"
    description = "Refined frosted glass card with modern, uncluttered typography."

    def generate(
        self,
        title: str,
        episode_info: str = "",
        quality: str = "720p",
        audio: str = "Hindi Dub",
        poster_path: str = "",
        output_path: str = "",
        bot_username: str = "AnimeDekhoBot",
        is_movie: bool = False,
    ) -> str | None:
        try:
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (15, 23, 42, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=32)
            if bg:
                canvas.paste(bg, (0, 0))

            # Translucent Frosted Glass Card in Center
            card_x1, card_y1 = 40, 40
            card_x2, card_y2 = CANVAS_WIDTH - 40, CANVAS_HEIGHT - 40
            glass_card = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_card = ImageDraw.Draw(glass_card)
            draw_card.rounded_rectangle(
                (card_x1, card_y1, card_x2, card_y2),
                radius=24, fill=(15, 23, 42, 210), outline=(255, 255, 255, 60), width=1,
            )
            canvas = Image.alpha_composite(canvas, glass_card)
            draw = ImageDraw.Draw(canvas)

            # Poster
            poster_w, poster_h = 340, 500
            poster_x, poster_y = 80, 110
            if poster_path and os.path.exists(poster_path):
                try:
                    with Image.open(poster_path) as p_img:
                        p_img = p_img.convert("RGBA")
                        p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                        p_rounded = _round_corners(p_resized, radius=16)
                        draw.rounded_rectangle(
                            (poster_x - 2, poster_y - 2, poster_x + poster_w + 2, poster_y + poster_h + 2),
                            radius=18, fill=(0, 0, 0, 40), outline=(255, 255, 255, 90), width=1,
                        )
                        canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Minimal poster error: %s", pe)

            text_x = 470
            curr_y = 120

            # Minimal Pill Badge
            ep_tag = "Full Movie" if is_movie or not episode_info else episode_info
            pill_text = f"{quality.upper()} • {audio} • {ep_tag}"
            draw.rounded_rectangle((text_x, curr_y, text_x + 440, curr_y + 38), radius=8, fill=(255, 255, 255, 25), outline=(255, 255, 255, 60), width=1)
            draw.text((text_x + 18, curr_y + 8), pill_text, font=_get_font(20), fill=(241, 245, 249, 255))
            curr_y += 65

            # Title
            lines = _clean_title(title)
            for line in lines:
                draw.text((text_x, curr_y), line, font=_get_font(46), fill=(255, 255, 255, 255))
                curr_y += 56
            curr_y += 25

            # Subtle Divider
            draw.line([(text_x, curr_y), (card_x2 - 50, curr_y)], fill=(255, 255, 255, 30), width=1)
            curr_y += 35

            # Description features
            draw.text((text_x, curr_y), "• Original Studio Quality Stream", font=_get_font(22), fill=(148, 163, 184, 255))
            curr_y += 32
            draw.text((text_x, curr_y), "• Multi-Language Audio Tracks Included", font=_get_font(22), fill=(148, 163, 184, 255))
            curr_y += 32
            draw.text((text_x, curr_y), "• Instant Fast Telegram Playback", font=_get_font(22), fill=(148, 163, 184, 255))
            curr_y += 50

            # Branding
            draw.text((text_x, curr_y), f"@{bot_username.lstrip('@')}", font=_get_font(22), fill=(56, 189, 248, 255))

            final_img = canvas.convert("RGB")
            final_img.save(output_path, "JPEG", quality=92, optimize=True)
            return output_path
        except Exception as e:
            log.error("MinimalCardTemplate generation error: %s", e)
            return None


# ── Public API & Generator ─────────────────────────────────────────────────

def list_available_templates() -> list[str]:
    """Return all registered template names."""
    return list(TEMPLATES.keys())


def get_template(
    name: str = "",
    is_movie: bool = False,
    random_mode: bool = False,
) -> BaseThumbnailTemplate:
    """
    Resolve template instance:
    - If random_mode or name=='random', randomly choose from available templates.
    - If is_movie and no name provided, prefer 'movie_gold' or 'cinematic'.
    - Fallback to 'modern'.
    """
    if random_mode or name.lower() == "random":
        chosen_name = random.choice(list(TEMPLATES.keys()))
        cls = TEMPLATES.get(chosen_name, ModernGradientTemplate)
        return cls()

    key = name.lower().strip() if name else ""
    if not key and is_movie:
        key = "movie_gold"

    cls = TEMPLATES.get(key)
    if not cls:
        cls = ModernGradientTemplate
    return cls()


def generate_auto_thumbnail(
    title: str,
    episode_info: str = "",
    quality: str = "720p",
    audio: str = "Hindi Dub",
    poster_path: str = "",
    output_path: str = "",
    bot_username: str = "AnimeDekhoBot",
    template_name: str | None = None,
    is_movie: bool = False,
) -> str | None:
    """
    Generate a 1280x720 professional YouTube/Telegram video thumbnail using the selected template.
    Template resolution:
    1. Explicit `template_name` argument if provided.
    2. Config `RANDOM_THUMB_TEMPLATE` or DB `random_thumb_template` if enabled.
    3. Config `THUMB_TEMPLATE` or DB `thumb_template`.
    4. Fallback to 'modern' (or 'movie_gold' for movies).
    """
    try:
        if not output_path:
            output_path = os.path.join(
                gettempdir(),
                f"thumb_auto_{os.getpid()}_{int(os.times().elapsed * 1000)}_{random.randint(100, 999)}.jpg"
            )

        # Resolve template & random mode
        resolved_template_name = template_name
        is_random = False

        if not resolved_template_name:
            try:
                from config import Config
                resolved_template_name = getattr(Config, "THUMB_TEMPLATE", "modern")
                is_random = getattr(Config, "RANDOM_THUMB_TEMPLATE", False)
            except Exception:
                resolved_template_name = "modern"

        template = get_template(
            name=resolved_template_name or "modern",
            is_movie=is_movie,
            random_mode=is_random,
        )

        log.info("Generating auto-thumbnail for '%s' using template '%s' (is_movie=%s)", title, template.name, is_movie)
        result = template.generate(
            title=title,
            episode_info=episode_info,
            quality=quality,
            audio=audio,
            poster_path=poster_path,
            output_path=output_path,
            bot_username=bot_username,
            is_movie=is_movie,
        )
        return result
    except Exception as e:
        log.error("Failed generating auto thumbnail: %s", e, exc_info=True)
        return None


def generate_thumbnail(
    title: str,
    episode_info: str = "",
    quality: str = "720p",
    audio: str = "Hindi Dub",
    poster_path: str = "",
    output_path: str = "",
    bot_username: str = "AnimeDekhoBot",
    template: str | None = None,
    template_name: str | None = None,
    is_movie: bool = False,
    season: int = 1,
    episode: int = 1,
    **kwargs,
) -> str | None:
    """Compatibility wrapper for generate_auto_thumbnail."""
    if not episode_info and not is_movie:
        episode_info = f"S{season:02d} E{episode:02d}"
    return generate_auto_thumbnail(
        title=title,
        episode_info=episode_info,
        quality=quality,
        audio=audio,
        poster_path=poster_path,
        output_path=output_path,
        bot_username=bot_username,
        template_name=template or template_name,
        is_movie=is_movie,
    )

