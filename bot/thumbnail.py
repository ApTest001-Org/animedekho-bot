"""
Auto Thumbnail Generator for AnimeDekho Bot — Modular Multi-Template Architecture.

Supports 5 distinct visual designs + random mode:
1. 'modern': Ultra-modern frosted glassmorphism card with high-contrast pills.
2. 'cinematic': Moody widescreen theatrical master with silver frame & cinematic bars.
3. 'movie_gold': Luxury obsidian & champagne gold VIP aesthetic (tailored for movies).
4. 'neon_cyber': Futuristic cyberpunk with electric cyan & hot magenta neon glow.
5. 'minimal': Clean frosted studio matte card with refined minimalist typography.

Also includes `enhance_custom_thumbnail` to fix low-quality / blurry custom thumbnails,
ensuring razor-sharp text, proper 16:9 framing, and Telegram video player optimization.
"""

from __future__ import annotations

import logging
import math
import os
import random
import re
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, Type

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

log = logging.getLogger(__name__)

CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

ASSETS_FONT_DIR = Path(__file__).parent.parent / "assets" / "fonts"

# System and bundled fonts priority
FONT_PATHS = [
    # Bundled Montserrat in repo
    str(ASSETS_FONT_DIR / "Montserrat-Bold.ttf"),
    str(ASSETS_FONT_DIR / "Montserrat-ExtraBold.ttf"),
    str(ASSETS_FONT_DIR / "Montserrat-SemiBold.ttf"),
    str(ASSETS_FONT_DIR / "Montserrat-Regular.ttf"),
    # Linux system fonts
    "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/montserrat/Montserrat-ExtraBold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    r"C:\Windows\Fonts\arialbd.ttf",
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeuib.ttf",
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial.ttf",
]


def _get_font(size: int, bold: bool = True, weight: str = "") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load bundled or system font with proper weights, falling back gracefully."""
    weight_map = {
        "extrabold": "Montserrat-ExtraBold.ttf",
        "bold": "Montserrat-Bold.ttf",
        "semibold": "Montserrat-SemiBold.ttf",
        "medium": "Montserrat-Medium.ttf",
        "regular": "Montserrat-Regular.ttf",
    }
    
    # Check bundled font first
    if weight and weight.lower() in weight_map:
        bundled = ASSETS_FONT_DIR / weight_map[weight.lower()]
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception:
                pass
    elif bold:
        bundled = ASSETS_FONT_DIR / "Montserrat-Bold.ttf"
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception:
                pass
    else:
        bundled = ASSETS_FONT_DIR / "Montserrat-Medium.ttf"
        if bundled.exists():
            try:
                return ImageFont.truetype(str(bundled), size)
            except Exception:
                pass

    # Fallback to system font paths
    for p in FONT_PATHS:
        if not bold and ("Bold" in p or "bd" in p):
            continue
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass

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


def _clean_text(text: str) -> str:
    """Strip emojis and unsupported unicode symbols to avoid broken square glyphs."""
    if not text:
        return ""
    # Strip high unicode emojis (U+1F000..U+1FFFF), misc symbols (U+2600..U+27BF), etc.
    cleaned = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b55\u200d\ufe0f]", "", text)
    return " ".join(cleaned.split()).strip()


def _draw_vector_star(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    r_outer: float,
    r_inner: float,
    fill: tuple[int, int, int, int] | tuple[int, int, int],
    points: int = 5,
) -> None:
    """Draw a mathematically antialiased vector star directly on canvas."""
    coords = []
    angle = -math.pi / 2
    step = math.pi / points
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        coords.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        angle += step
    draw.polygon(coords, fill=fill)


def _round_corners(img: Image.Image, radius: int) -> Image.Image:
    """Round the corners of an image with smooth antialiasing."""
    mask = Image.new("L", (img.width * 2, img.height * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.width * 2, img.height * 2), radius * 2, fill=255)
    mask = mask.resize((img.width, img.height), Image.Resampling.LANCZOS)
    output = img.copy().convert("RGBA")
    output.putalpha(mask)
    return output


def _prepare_blurred_bg(poster_path: str, blur_radius: int = 34) -> Image.Image | None:
    """Scale, center-crop, and blur a poster to cover the 1280x720 canvas."""
    target_path = poster_path
    if not target_path or not os.path.exists(target_path):
        banner_fallback = Path(__file__).parent.parent / "assets" / "banner.png"
        if banner_fallback.exists():
            target_path = str(banner_fallback)
        else:
            return None

    try:
        with Image.open(target_path) as p_img:
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


def _resolve_poster_image(poster_path: str) -> Image.Image | None:
    """Load poster image with fallback to assets/banner.png if missing."""
    target = poster_path
    if not target or not os.path.exists(target):
        banner = Path(__file__).parent.parent / "assets" / "banner.png"
        if banner.exists():
            target = str(banner)
        else:
            return None
    try:
        return Image.open(target).convert("RGBA")
    except Exception as e:
        log.debug("Failed loading poster image: %s", e)
        return None


def _wrap_and_fit_title(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_w: int,
    base_size: int = 46,
    min_size: int = 32,
    max_lines: int = 2,
) -> tuple[list[str], ImageFont.FreeTypeFont | ImageFont.ImageFont, int]:
    """Dynamically wrap and scale font size so title fits neatly within max_w and max_lines."""
    clean = _clean_text(re.sub(r"\[.*?\]|\(.*?\)", "", title).strip())
    if not clean:
        clean = title[:40]
    words = clean.split()

    for size in range(base_size, min_size - 1, -2):
        font = _get_font(size, bold=True, weight="extrabold")
        lines = []
        curr = []
        fits = True
        for w in words:
            cand = " ".join(curr + [w])
            bb = draw.textbbox((0, 0), cand, font=font)
            if (bb[2] - bb[0]) <= max_w:
                curr.append(w)
            else:
                if curr:
                    lines.append(" ".join(curr))
                curr = [w]
                if len(lines) >= max_lines:
                    fits = False
                    break
        if curr and fits:
            lines.append(" ".join(curr))

        if fits and len(lines) <= max_lines:
            line_height = int(size * 1.22)
            return lines[:max_lines], font, line_height

    # Final fallback with min_size
    font = _get_font(min_size, bold=True, weight="extrabold")
    lines = []
    curr = []
    for w in words:
        cand = " ".join(curr + [w])
        bb = draw.textbbox((0, 0), cand, font=font)
        if (bb[2] - bb[0]) <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    return lines[:max_lines], font, int(min_size * 1.22)


def _get_quality_pill(quality: str) -> tuple[str, tuple[int, int, int, int]]:
    """Return stylized quality label and background color."""
    q_up = (quality or "720P").upper().strip()
    if "4K" in q_up or "2160" in q_up:
        return "4K • ULTRA HD", (139, 92, 246, 240)  # Royal Violet
    elif "1080" in q_up:
        return "1080P • FULL HD", (225, 29, 72, 240)  # Crimson Ruby
    elif "720" in q_up:
        return "720P • HD", (37, 99, 235, 240)  # Sapphire Blue
    elif "480" in q_up:
        return "480P • SD", (13, 148, 136, 240)  # Teal
    else:
        label = f"{q_up} • HD" if "HD" not in q_up else q_up
        return label, (13, 148, 136, 240)


def _format_audio_tag(audio: str) -> str:
    """Format audio tag cleanly without broken glyphs."""
    aud = _clean_text(audio).strip().upper()
    if not aud:
        return "HINDI DUBBED"
    if "HINDI" in aud and "DUB" not in aud:
        return "HINDI DUBBED"
    if "MULTI" in aud and "AUDIO" not in aud:
        return "MULTI AUDIO"
    return aud


def _format_episode_tag(episode_info: str, is_movie: bool) -> str:
    """Format episode or movie banner tag."""
    if is_movie and not episode_info:
        return "FEATURE FILM • OFFICIAL RELEASE"
    if episode_info:
        clean_ep = _clean_text(episode_info).strip().upper()
        return clean_ep
    return "COMPLETE SERIES • ALL EPISODES"


def _save_optimized_jpeg(img: Image.Image, output_path: str, max_kb: int = 285) -> str:
    """Save image with optimal quality, unsharp mask, and ensure size is strictly under Telegram's limit."""
    final = img.convert("RGB")
    final = ImageEnhance.Contrast(final).enhance(1.05)
    final = final.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))

    q = 95
    while q >= 75:
        final.save(output_path, "JPEG", quality=q, optimize=True, subsampling=0)
        try:
            if os.path.getsize(output_path) <= max_kb * 1024:
                break
        except Exception:
            break
        q -= 4
    return output_path


# ── Custom Thumbnail Enhancement Function ──────────────────────────────────

def enhance_custom_thumbnail(
    input_path: str,
    output_path: str | None = None,
    target_width: int = 1280,
    target_height: int = 720,
) -> str | None:
    """
    Transform ANY custom uploaded image into a high-end, razor-sharp 1280x720 video thumbnail.
    
    Solves low quality & unreadable text issues on custom thumbnails:
    - Aspect Ratio Fix: Non-16:9 images (portraits, squares) are framed onto a 16:9 canvas
      with a cinema-grade blurred ambient background and subtle drop shadow (no stretching/cropping).
    - Clarity Enhancement: UnsharpMask filtering and contrast/color boosting make all text glyphs,
      logos, and episode labels crisp and easily legible on both mobile and desktop screens.
    - Lossless Chroma Subsampling: Saved with `subsampling=0` (4:4:4) to eliminate JPEG edge-blur on text.
    - Size Optimization: Kept strictly under 285 KB to prevent Telegram server recompression artifacts.
    """
    if not input_path or not os.path.exists(input_path):
        return None

    if not output_path:
        output_path = os.path.join(
            gettempdir(),
            f"enhanced_thumb_{os.getpid()}_{random.randint(1000, 9999)}.jpg",
        )

    try:
        with Image.open(input_path) as im:
            im = im.convert("RGBA")
            w, h = im.size
            if w <= 0 or h <= 0:
                return None

            aspect = w / h

            # Case 1: Already widescreen (~16:9, between 1.65 and 1.90)
            if 1.65 <= aspect <= 1.90:
                resized = im.resize((target_width, target_height), Image.Resampling.LANCZOS)
                canvas = resized.convert("RGB")
            else:
                # Case 2: Portrait poster, square, or irregular aspect ratio
                # Ambient blurred backdrop framing (Netflix / Crunchyroll / Disney+ aesthetic)
                canvas = Image.new("RGBA", (target_width, target_height), (10, 12, 20, 255))

                # Background scaled & blurred
                scale_bg = max(target_width / w, target_height / h)
                bg_w, bg_h = int(w * scale_bg), int(h * scale_bg)
                bg = im.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
                bg_x = (bg_w - target_width) // 2
                bg_y = (bg_h - target_height) // 2
                bg_cropped = bg.crop((bg_x, bg_y, bg_x + target_width, bg_y + target_height))
                bg_blurred = bg_cropped.filter(ImageFilter.GaussianBlur(radius=36))

                # Atmospheric vignette overlay
                overlay = Image.new("RGBA", (target_width, target_height), (8, 10, 18, 140))
                bg_composite = Image.alpha_composite(bg_blurred, overlay)
                canvas.paste(bg_composite, (0, 0))

                # Sharp foreground image (fitted within bounds)
                pad = 24
                max_fg_h = target_height - (pad * 2)
                max_fg_w = target_width - (pad * 2)
                scale_fg = min(max_fg_w / w, max_fg_h / h)
                fg_w, fg_h = int(w * scale_fg), int(h * scale_fg)
                fg_resized = im.resize((fg_w, fg_h), Image.Resampling.LANCZOS)

                fg_x = (target_width - fg_w) // 2
                fg_y = (target_height - fg_h) // 2

                # Soft realistic ambient drop shadow
                shadow = Image.new("RGBA", (fg_w + 30, fg_h + 30), (0, 0, 0, 0))
                draw_sh = ImageDraw.Draw(shadow)
                draw_sh.rounded_rectangle((15, 15, fg_w + 15, fg_h + 15), radius=18, fill=(0, 0, 0, 210))
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
                canvas.paste(shadow, (fg_x - 15, fg_y - 15), shadow)

                # Delicate outer glass border stroke
                draw = ImageDraw.Draw(canvas)
                draw.rounded_rectangle(
                    (fg_x - 3, fg_y - 3, fg_x + fg_w + 3, fg_y + fg_h + 3),
                    radius=16, outline=(255, 255, 255, 100), width=2
                )
                canvas.paste(fg_resized, (fg_x, fg_y), fg_resized)
                canvas = canvas.convert("RGB")

            # High-Impact Clarity & Readability Enhancements
            canvas = ImageEnhance.Contrast(canvas).enhance(1.08)
            canvas = ImageEnhance.Color(canvas).enhance(1.06)
            canvas = ImageEnhance.Sharpness(canvas).enhance(1.25)
            canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.6, percent=135, threshold=3))

            # Optimize JPEG file size strictly for Telegram
            q = 95
            while q >= 75:
                canvas.save(output_path, "JPEG", quality=q, optimize=True, subsampling=0)
                try:
                    if os.path.getsize(output_path) <= 285 * 1024:
                        break
                except Exception:
                    break
                q -= 4

            log.info("Enhanced custom thumbnail created: %s (%d bytes)", output_path, os.path.getsize(output_path))
            return output_path
    except Exception as e:
        log.error("Failed enhancing custom thumbnail: %s", e, exc_info=True)
        return None


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


# ── Template 1: Modern Glassmorphism Card ──────────────────────────────────

@register_template("modern")
class ModernGradientTemplate(BaseThumbnailTemplate):
    """Ultra-modern frosted glassmorphism card with high-contrast pills and crisp typography."""
    name = "modern"
    display_name = "Modern Glass"
    description = "Sleek frosted glass card with vibrant resolution pills and crystal-clear hierarchy."

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
            canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (10, 12, 20, 255))
            bg = _prepare_blurred_bg(poster_path, blur_radius=32)
            if bg:
                canvas.paste(bg, (0, 0))

            # Dark Atmospheric Gradient Overlay
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(140 + (y / CANVAS_HEIGHT) * 90)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(8, 10, 18, alpha))
            for x in range(CANVAS_WIDTH):
                if x > 380:
                    alpha = int(((x - 380) / (CANVAS_WIDTH - 380)) * 110)
                    draw_ov.line([(x, 0), (x, CANVAS_HEIGHT)], fill=(6, 8, 16, alpha))
            canvas = Image.alpha_composite(canvas, overlay)

            # Frosted Glass Card on Right
            card_x1, card_y1 = 450, 65
            card_x2, card_y2 = CANVAS_WIDTH - 50, CANVAS_HEIGHT - 65
            glass_card = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_card = ImageDraw.Draw(glass_card)
            draw_card.rounded_rectangle(
                (card_x1, card_y1, card_x2, card_y2),
                radius=22, fill=(15, 23, 42, 215), outline=(56, 189, 248, 65), width=1,
            )
            canvas = Image.alpha_composite(canvas, glass_card)
            draw = ImageDraw.Draw(canvas)

            # Foreground Poster on Left
            poster_w, poster_h = 350, 510
            poster_x, poster_y = 65, 105
            p_img = _resolve_poster_image(poster_path)
            if p_img:
                try:
                    p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    p_rounded = _round_corners(p_resized, radius=18)

                    # Ambient Drop Shadow behind poster
                    shadow = Image.new("RGBA", (poster_w + 30, poster_h + 30), (0, 0, 0, 0))
                    draw_sh = ImageDraw.Draw(shadow)
                    draw_sh.rounded_rectangle((15, 15, poster_w + 15, poster_h + 15), radius=22, fill=(0, 0, 0, 220))
                    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
                    canvas.paste(shadow, (poster_x - 15, poster_y - 15), shadow)

                    # Outer glass stroke
                    draw.rounded_rectangle(
                        (poster_x - 3, poster_y - 3, poster_x + poster_w + 3, poster_y + poster_h + 3),
                        radius=21, outline=(255, 255, 255, 120), width=2,
                    )
                    canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Modern poster error: %s", pe)

            # Typography & Content inside Glass Card
            curr_x = card_x1 + 42
            curr_y = card_y1 + 42
            available_w = (card_x2 - curr_x) - 40

            font_pill = _get_font(20, bold=True, weight="bold")

            # 1. Quality Pill
            q_label, q_color = _get_quality_pill(quality)
            q_bbox = draw.textbbox((0, 0), q_label, font=font_pill)
            qw = (q_bbox[2] - q_bbox[0]) + 32
            qh = 38
            draw.rounded_rectangle((curr_x, curr_y, curr_x + qw, curr_y + qh), radius=8, fill=q_color)
            draw.text((curr_x + 16, curr_y + 8), q_label, font=font_pill, fill=(255, 255, 255, 255))

            # 2. Audio Pill
            audio_text = _format_audio_tag(audio)
            a_bbox = draw.textbbox((0, 0), audio_text, font=font_pill)
            aw = (a_bbox[2] - a_bbox[0]) + 32
            ax = curr_x + qw + 14
            draw.rounded_rectangle(
                (ax, curr_y, ax + aw, curr_y + qh),
                radius=8, fill=(30, 41, 59, 230), outline=(100, 116, 139, 160), width=1,
            )
            draw.text((ax + 16, curr_y + 8), audio_text, font=font_pill, fill=(241, 245, 249, 255))
            curr_y += qh + 24

            # 3. Main Title (Auto-scaling and wrapping)
            title_lines, font_title, line_height = _wrap_and_fit_title(
                draw, title, max_w=available_w, base_size=46, min_size=32, max_lines=2,
            )
            for line in title_lines:
                draw.text((curr_x + 2, curr_y + 2), line, font=font_title, fill=(0, 0, 0, 240))
                draw.text((curr_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += line_height
            curr_y += 14

            # 4. Episode / Movie Ribbon
            ep_tag = _format_episode_tag(episode_info, is_movie)
            font_ep = _get_font(23, bold=True, weight="extrabold")
            ep_bbox = draw.textbbox((0, 0), ep_tag, font=font_ep)
            ep_w = (ep_bbox[2] - ep_bbox[0]) + 40
            ep_h = 48
            draw.rounded_rectangle(
                (curr_x, curr_y, curr_x + ep_w, curr_y + ep_h),
                radius=10, fill=(245, 158, 11, 245),
            )
            draw.text((curr_x + 20, curr_y + 11), ep_tag, font=font_ep, fill=(15, 23, 42, 255))
            curr_y += ep_h + 26

            # 5. Divider
            draw.line([(curr_x, curr_y), (card_x2 - 40, curr_y)], fill=(255, 255, 255, 35), width=1)
            curr_y += 22

            # 6. Tech Features & Branding
            font_sub = _get_font(20, bold=False, weight="medium")
            tagline = "MULTI-AUDIO  •  FAST DIRECT PLAY  •  HD MASTER"
            draw.text((curr_x, curr_y), tagline, font=font_sub, fill=(148, 163, 184, 255))
            curr_y += 34

            font_brand = _get_font(20, bold=True, weight="semibold")
            brand_text = f"ANIMEDEKHO  •  @{bot_username.lstrip('@')}"
            draw.text((curr_x, curr_y), brand_text, font=font_brand, fill=(56, 189, 248, 255))

            return _save_optimized_jpeg(canvas, output_path)
        except Exception as e:
            log.error("ModernGradientTemplate generation error: %s", e, exc_info=True)
            return None


# ── Template 2: Cinematic Glow (Theatrical Letterbox) ──────────────────────

@register_template("cinematic")
class CinematicGlowTemplate(BaseThumbnailTemplate):
    """Moody widescreen letterbox with theatrical bars, silver frame, and cyan accents."""
    name = "cinematic"
    display_name = "Cinematic Glow"
    description = "Theatrical widescreen look with atmospheric indigo glow and silver metallic borders."

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
            bg = _prepare_blurred_bg(poster_path, blur_radius=38)
            if bg:
                canvas.paste(bg, (0, 0))

            # Deep moody overlay with letterbox bars
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(160 + (y / CANVAS_HEIGHT) * 75)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(6, 8, 16, alpha))

            # 42px Widescreen letterbox bars
            lb_h = 42
            draw_ov.rectangle([(0, 0), (CANVAS_WIDTH, lb_h)], fill=(2, 3, 6, 255))
            draw_ov.rectangle([(0, CANVAS_HEIGHT - lb_h), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill=(2, 3, 6, 255))
            draw_ov.line([(0, lb_h), (CANVAS_WIDTH, lb_h)], fill=(56, 189, 248, 120), width=1)
            draw_ov.line([(0, CANVAS_HEIGHT - lb_h), (CANVAS_WIDTH, CANVAS_HEIGHT - lb_h)], fill=(56, 189, 248, 120), width=1)
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with double metallic silver frame
            poster_w, poster_h = 340, 490
            poster_x, poster_y = 75, 115
            p_img = _resolve_poster_image(poster_path)
            if p_img:
                try:
                    p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    p_rounded = _round_corners(p_resized, radius=14)
                    draw.rounded_rectangle(
                        (poster_x - 4, poster_y - 4, poster_x + poster_w + 4, poster_y + poster_h + 4),
                        radius=18, outline=(226, 232, 240, 200), width=2,
                    )
                    canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Cinematic poster error: %s", pe)

            text_x = 470
            curr_y = 135
            available_w = CANVAS_WIDTH - text_x - 60

            # Theatrical Header with Vector Gold Stars
            font_hdr = _get_font(20, bold=True, weight="bold")
            hdr_text = "THEATRICAL MASTER • ULTRA HD STREAM"
            _draw_vector_star(draw, text_x + 8, curr_y + 11, r_outer=7, r_inner=3, fill=(245, 158, 11, 240))
            draw.text((text_x + 24, curr_y), hdr_text, font=font_hdr, fill=(148, 163, 184, 255))
            curr_y += 42

            # Title
            title_lines, font_title, line_height = _wrap_and_fit_title(
                draw, title, max_w=available_w, base_size=44, min_size=32, max_lines=2,
            )
            for line in title_lines:
                draw.text((text_x + 2, curr_y + 2), line, font=font_title, fill=(0, 0, 0, 240))
                draw.text((text_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += line_height
            curr_y += 18

            # Cinema Badge
            badge_text = _format_episode_tag(episode_info, is_movie)
            font_badge = _get_font(22, bold=True, weight="extrabold")
            b_bb = draw.textbbox((0, 0), badge_text, font=font_badge)
            bw = (b_bb[2] - b_bb[0]) + 44
            bh = 48
            draw.rounded_rectangle(
                (text_x, curr_y, text_x + bw, curr_y + bh),
                radius=8, fill=(15, 23, 42, 240), outline=(56, 189, 248, 220), width=2,
            )
            draw.text((text_x + 22, curr_y + 11), badge_text, font=font_badge, fill=(224, 242, 254, 255))
            curr_y += bh + 28

            # Specs
            q_label = (quality or "1080P").upper()
            draw.text((text_x, curr_y), f"RESOLUTION : {q_label} ULTRA STREAM", font=_get_font(22, bold=True, weight="bold"), fill=(56, 189, 248, 255))
            curr_y += 34
            audio_text = _format_audio_tag(audio)
            draw.text((text_x, curr_y), f"AUDIO TRACK : {audio_text} (ORIGINAL)", font=_get_font(22, bold=False, weight="semibold"), fill=(226, 232, 240, 255))

            # Watermark in Letterbox bar
            wm_text = f"ANIMEDEKHO THEATRICAL • @{bot_username.lstrip('@')}"
            draw.text((CANVAS_WIDTH - 390, CANVAS_HEIGHT - 30), wm_text, font=_get_font(16, bold=True, weight="bold"), fill=(148, 163, 184, 255))

            return _save_optimized_jpeg(canvas, output_path)
        except Exception as e:
            log.error("CinematicGlowTemplate generation error: %s", e, exc_info=True)
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
            bg = _prepare_blurred_bg(poster_path, blur_radius=32)
            if bg:
                canvas.paste(bg, (0, 0))

            # Warm dark gold ambient gradient
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(160 + (y / CANVAS_HEIGHT) * 80)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(12, 10, 8, alpha))
            # Outer Gold Border frame
            draw_ov.rectangle([(16, 16), (CANVAS_WIDTH - 16, CANVAS_HEIGHT - 16)], outline=(212, 175, 55, 140), width=2)
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with Gold Frame
            poster_w, poster_h = 350, 500
            poster_x, poster_y = 70, 110
            p_img = _resolve_poster_image(poster_path)
            if p_img:
                try:
                    p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    p_rounded = _round_corners(p_resized, radius=14)
                    draw.rounded_rectangle(
                        (poster_x - 4, poster_y - 4, poster_x + poster_w + 4, poster_y + poster_h + 4),
                        radius=18, outline=(212, 175, 55, 230), width=3,
                    )
                    canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Movie gold poster error: %s", pe)

            text_x = 475
            curr_y = 115
            available_w = CANVAS_WIDTH - text_x - 65

            # Gold VIP Header
            header_text = "OFFICIAL VIP PREMIERE" if is_movie else "SPECIAL VIP BROADCAST"
            font_vip = _get_font(18, bold=True, weight="bold")
            v_bb = draw.textbbox((0, 0), header_text, font=font_vip)
            vw = (v_bb[2] - v_bb[0]) + 60
            vh = 38
            draw.rounded_rectangle((text_x, curr_y, text_x + vw, curr_y + vh), radius=6, fill=(212, 175, 55, 230))
            _draw_vector_star(draw, text_x + 16, curr_y + 19, r_outer=7, r_inner=3, fill=(24, 18, 5, 255))
            draw.text((text_x + 30, curr_y + 9), header_text, font=font_vip, fill=(24, 18, 5, 255))
            _draw_vector_star(draw, text_x + vw - 16, curr_y + 19, r_outer=7, r_inner=3, fill=(24, 18, 5, 255))
            curr_y += vh + 20

            # Title
            title_lines, font_title, line_height = _wrap_and_fit_title(
                draw, title, max_w=available_w, base_size=46, min_size=32, max_lines=2,
            )
            for line in title_lines:
                draw.text((text_x + 2, curr_y + 2), line, font=font_title, fill=(0, 0, 0, 240))
                draw.text((text_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += line_height
            curr_y += 16

            # Golden Main Ribbon
            main_tag = _format_episode_tag(episode_info, is_movie)
            font_ribbon = _get_font(23, bold=True, weight="extrabold")
            m_bb = draw.textbbox((0, 0), main_tag, font=font_ribbon)
            mw = (m_bb[2] - m_bb[0]) + 44
            mh = 50
            draw.rounded_rectangle((text_x, curr_y, text_x + mw, curr_y + mh), radius=10, fill=(212, 175, 55, 240))
            draw.text((text_x + 22, curr_y + 12), main_tag, font=font_ribbon, fill=(24, 18, 5, 255))
            curr_y += mh + 26

            # Quality & Audio Pills
            q_label = (quality or "1080P").upper()
            draw.text((text_x, curr_y), f"QUALITY : {q_label} ULTRA HD MASTER", font=_get_font(22, bold=True, weight="bold"), fill=(245, 210, 100, 255))
            curr_y += 34
            audio_text = _format_audio_tag(audio)
            draw.text((text_x, curr_y), f"AUDIO : {audio_text} / DUAL AUDIO", font=_get_font(22, bold=False, weight="semibold"), fill=(243, 244, 246, 255))
            curr_y += 45

            # Gold Divider & Branding
            draw.line([(text_x, curr_y), (CANVAS_WIDTH - 65, curr_y)], fill=(212, 175, 55, 80), width=2)
            curr_y += 20
            draw.text((text_x, curr_y), f"VIP RELEASE BY @{bot_username.lstrip('@')}", font=_get_font(20, bold=True, weight="semibold"), fill=(212, 175, 55, 220))

            return _save_optimized_jpeg(canvas, output_path)
        except Exception as e:
            log.error("MovieGoldTemplate generation error: %s", e, exc_info=True)
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
            bg = _prepare_blurred_bg(poster_path, blur_radius=28)
            if bg:
                canvas.paste(bg, (0, 0))

            # Dark overlay with slight magenta tint
            overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_ov = ImageDraw.Draw(overlay)
            for y in range(CANVAS_HEIGHT):
                alpha = int(160 + (y / CANVAS_HEIGHT) * 80)
                draw_ov.line([(0, y), (CANVAS_WIDTH, y)], fill=(8, 8, 18, alpha))
            canvas = Image.alpha_composite(canvas, overlay)
            draw = ImageDraw.Draw(canvas)

            # Poster with Cyber Neon Dual Border (Cyan top/left, Pink bottom/right)
            poster_w, poster_h = 350, 500
            poster_x, poster_y = 70, 110
            p_img = _resolve_poster_image(poster_path)
            if p_img:
                try:
                    p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    p_rounded = _round_corners(p_resized, radius=10)
                    draw.rounded_rectangle(
                        (poster_x - 5, poster_y - 5, poster_x + poster_w + 5, poster_y + poster_h + 5),
                        radius=14, outline=(0, 240, 255, 230), width=2,
                    )
                    draw.rounded_rectangle(
                        (poster_x - 2, poster_y - 2, poster_x + poster_w + 2, poster_y + poster_h + 2),
                        radius=11, outline=(255, 0, 128, 200), width=2,
                    )
                    canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Neon cyber poster error: %s", pe)

            text_x = 475
            curr_y = 115
            available_w = CANVAS_WIDTH - text_x - 65

            # Cyber Header Badge
            draw.text((text_x, curr_y), "// CYBER DIRECT LINK // SPEED 10Gbps", font=_get_font(20, bold=True, weight="bold"), fill=(0, 240, 255, 255))
            curr_y += 44

            # Title
            title_lines, font_title, line_height = _wrap_and_fit_title(
                draw, title, max_w=available_w, base_size=46, min_size=32, max_lines=2,
            )
            for line in title_lines:
                draw.text((text_x + 2, curr_y + 2), line, font=font_title, fill=(0, 240, 255, 140))
                draw.text((text_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += line_height
            curr_y += 18

            # Cyber Episode Tag
            ep_tag = _format_episode_tag(episode_info, is_movie)
            cyber_ep = f"// {ep_tag} //"
            font_ep = _get_font(23, bold=True, weight="extrabold")
            e_bb = draw.textbbox((0, 0), cyber_ep, font=font_ep)
            ew = (e_bb[2] - e_bb[0]) + 44
            eh = 50
            draw.rectangle((text_x, curr_y, text_x + ew, curr_y + eh), fill=(255, 0, 128, 220), outline=(0, 240, 255, 255), width=2)
            draw.text((text_x + 22, curr_y + 12), cyber_ep, font=font_ep, fill=(255, 255, 255, 255))
            curr_y += eh + 26

            # Badges
            q_label = (quality or "1080P").upper()
            draw.text((text_x, curr_y), f"QUALITY : [ {q_label} ]", font=_get_font(22, bold=True, weight="bold"), fill=(0, 240, 255, 255))
            curr_y += 34
            audio_text = _format_audio_tag(audio)
            draw.text((text_x, curr_y), f"AUDIO : [ {audio_text} ]", font=_get_font(22, bold=False, weight="semibold"), fill=(255, 0, 128, 255))
            curr_y += 46

            # Neon Divider
            draw.line([(text_x, curr_y), (CANVAS_WIDTH - 65, curr_y)], fill=(0, 240, 255, 140), width=2)
            curr_y += 20
            draw.text((text_x, curr_y), f"SYS.OP: @{bot_username.lstrip('@')}", font=_get_font(20, bold=True, weight="semibold"), fill=(148, 163, 184, 255))

            return _save_optimized_jpeg(canvas, output_path)
        except Exception as e:
            log.error("NeonCyberTemplate generation error: %s", e, exc_info=True)
            return None


# ── Template 5: Minimal Card (Frosted Matte Studio) ───────────────────────

@register_template("minimal")
class MinimalCardTemplate(BaseThumbnailTemplate):
    """Clean frosted glass card with refined minimalist typography and high-contrast badges."""
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
            bg = _prepare_blurred_bg(poster_path, blur_radius=34)
            if bg:
                canvas.paste(bg, (0, 0))

            # Translucent Frosted Glass Card in Center
            card_x1, card_y1 = 45, 45
            card_x2, card_y2 = CANVAS_WIDTH - 45, CANVAS_HEIGHT - 45
            glass_card = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
            draw_card = ImageDraw.Draw(glass_card)
            draw_card.rounded_rectangle(
                (card_x1, card_y1, card_x2, card_y2),
                radius=24, fill=(15, 23, 42, 220), outline=(255, 255, 255, 60), width=1,
            )
            canvas = Image.alpha_composite(canvas, glass_card)
            draw = ImageDraw.Draw(canvas)

            # Poster
            poster_w, poster_h = 340, 500
            poster_x, poster_y = 80, 110
            p_img = _resolve_poster_image(poster_path)
            if p_img:
                try:
                    p_resized = p_img.resize((poster_w, poster_h), Image.Resampling.LANCZOS)
                    p_rounded = _round_corners(p_resized, radius=16)
                    draw.rounded_rectangle(
                        (poster_x - 2, poster_y - 2, poster_x + poster_w + 2, poster_y + poster_h + 2),
                        radius=18, outline=(255, 255, 255, 90), width=1,
                    )
                    canvas.paste(p_rounded, (poster_x, poster_y), p_rounded)
                except Exception as pe:
                    log.debug("Minimal poster error: %s", pe)

            text_x = 470
            curr_y = 120
            available_w = card_x2 - text_x - 50

            # Minimal High-Contrast Dark Pill Badge (Prevents white-on-white washed out text)
            q_label, _ = _get_quality_pill(quality)
            audio_text = _format_audio_tag(audio)
            ep_tag = _format_episode_tag(episode_info, is_movie)
            pill_text = f"{q_label}  •  {audio_text}  •  {ep_tag}"

            font_pill = _get_font(20, bold=True, weight="bold")
            p_bb = draw.textbbox((0, 0), pill_text, font=font_pill)
            pw = (p_bb[2] - p_bb[0]) + 36
            ph = 40
            draw.rounded_rectangle(
                (text_x, curr_y, text_x + pw, curr_y + ph),
                radius=8, fill=(30, 41, 59, 240), outline=(56, 189, 248, 140), width=1,
            )
            draw.text((text_x + 18, curr_y + 9), pill_text, font=font_pill, fill=(56, 189, 248, 255))
            curr_y += ph + 24

            # Title
            title_lines, font_title, line_height = _wrap_and_fit_title(
                draw, title, max_w=available_w, base_size=46, min_size=32, max_lines=2,
            )
            for line in title_lines:
                draw.text((text_x, curr_y), line, font=font_title, fill=(255, 255, 255, 255))
                curr_y += line_height
            curr_y += 20

            # Subtle Divider
            draw.line([(text_x, curr_y), (card_x2 - 50, curr_y)], fill=(255, 255, 255, 30), width=1)
            curr_y += 30

            # Description features
            font_feat = _get_font(21, bold=False, weight="medium")
            draw.text((text_x, curr_y), "• Original Studio Quality Direct Stream", font=font_feat, fill=(148, 163, 184, 255))
            curr_y += 32
            draw.text((text_x, curr_y), "• Multi-Language Audio Tracks Included", font=font_feat, fill=(148, 163, 184, 255))
            curr_y += 32
            draw.text((text_x, curr_y), "• Instant Fast Telegram Playback", font=font_feat, fill=(148, 163, 184, 255))
            curr_y += 48

            # Branding
            draw.text((text_x, curr_y), f"@{bot_username.lstrip('@')}", font=_get_font(22, bold=True, weight="bold"), fill=(56, 189, 248, 255))

            return _save_optimized_jpeg(canvas, output_path)
        except Exception as e:
            log.error("MinimalCardTemplate generation error: %s", e, exc_info=True)
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
    if random_mode or (name and name.lower() == "random"):
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
