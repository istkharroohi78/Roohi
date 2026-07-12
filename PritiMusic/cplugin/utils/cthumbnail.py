import asyncio
import os
import re
import uuid
import math
import random
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL

try:
    from PritiMusic.core.dir import CACHE_DIR
except ImportError:
    CACHE_DIR = "cache"

LOGGER = __import__('logging').getLogger(__name__)

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS = Image.LANCZOS

TITLE_FONT_PATH = "PritiMusic/assets/font2.ttf"
META_FONT_PATH = "PritiMusic/assets/font.ttf"
CANVAS_SIZE = (1280, 720)
TEXT_GRAY = (180, 180, 180)
WHITE = (255, 255, 255)
NEON_COLORS = [(255, 40, 130), (0, 204, 255), (255, 220, 0), (20, 100, 255)]

def fit_cover(image, size):
    ratio = max(size[0] / image.size[0], size[1] / image.size[1])
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    resized = image.resize(new_size, LANCZOS)
    left = (new_size[0] - size[0]) // 2
    top = (new_size[1] - size[1]) // 2
    return resized.crop((left, top, left + size[0], top + size[1]))

def get_mask(size, radius, antialias=4):
    mask = Image.new("L", (size[0] * antialias, size[1] * antialias), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] * antialias, size[1] * antialias), radius=radius * antialias, fill=255)
    return mask.resize(size, LANCZOS)

def load_font(path, size):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

def format_views(view_count_str):
    try:
        views_num = int(re.sub(r"\D", "", str(view_count_str)))
        if views_num >= 1000000000: return f"{views_num / 1000000000:.1f} B"
        elif views_num >= 1000000: return f"{views_num // 1000000} M"
        elif views_num >= 1000: return f"{views_num // 1000} K"
        return str(views_num)
    except: return "Unknown"

def trim_text(text: str, limit: int) -> str:
    clean_text = " ".join(str(text or "").split())
    if len(clean_text) <= limit: return clean_text
    return clean_text[: max(limit - 3, 0)].rstrip() + "..."

def draw_exact_icons(draw, cx, cy, icon, fill=WHITE):
    if icon == "prev":
        draw.polygon([(cx + 12, cy - 14), (cx - 2, cy), (cx + 12, cy + 14)], fill=fill)
        draw.polygon([(cx - 2, cy - 14), (cx - 16, cy), (cx - 16, cy + 14)], fill=fill)
        draw.rounded_rectangle([(cx - 22, cy - 14), (cx - 16, cy + 14)], radius=2, fill=fill)
    elif icon == "pause":
        draw.rounded_rectangle([(cx - 12, cy - 16), (cx - 4, cy + 16)], radius=3, fill=fill)
        draw.rounded_rectangle([(cx + 4, cy - 16), (cx + 12, cy + 16)], radius=3, fill=fill)
    elif icon == "next":
        draw.polygon([(cx - 12, cy - 14), (cx + 2, cy), (cx - 12, cy + 14)], fill=fill)
        draw.polygon([(cx + 2, cy - 14), (cx + 16, cy), (cx + 16, cy + 14)], fill=fill)
        draw.rounded_rectangle([(cx + 16, cy - 14), (cx + 22, cy + 14)], radius=2, fill=fill)

async def get_thumb(videoid, user_id=None, app=None):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_{user_id}_premium_v6.png")
    if os.path.isfile(cache_path): return cache_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    unique_id = uuid.uuid4().hex[:8]
    temp_thumb_path = os.path.join(CACHE_DIR, f"temp_{videoid}_{unique_id}.png")

    try:
        results = VideosSearch(url, limit=1)
        results_data = (await results.next()).get("result", [])
        if not results_data: return YOUTUBE_IMG_URL
        result = results_data[0]
        title = trim_text(re.sub(r"[^\w\s&\-']", " ", result.get("title", "")).strip(), 28)
        duration = str(result.get("duration") or "00:00")
        views_str = format_views((result.get("viewCount") or {}).get("text") or "0")
        channel = trim_text(str((result.get("channel") or {}).get("name") or "Unknown Artist"), 20)
        thumbnail_url = result.get("thumbnails", [{}])[-1].get("url", "").split("?")[0]

        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    async with aiofiles.open(temp_thumb_path, mode="wb") as f:
                        await f.write(await resp.read())
                else: return YOUTUBE_IMG_URL

        source_image = Image.open(temp_thumb_path).convert("RGBA")
        theme_color = random.choice(NEON_COLORS)
        glow_color = (*theme_color, 160)
        background = fit_cover(source_image, CANVAS_SIZE).filter(ImageFilter.GaussianBlur(65))
        background = ImageEnhance.Brightness(background).enhance(0.20)
        scene = background.copy()
        
        font_title = load_font(TITLE_FONT_PATH, 42)
        font_stats_label = load_font(TITLE_FONT_PATH, 32)
        font_stats_value = load_font(TITLE_FONT_PATH, 32)
        font_pill = load_font(TITLE_FONT_PATH, 24)
        font_time = load_font(TITLE_FONT_PATH, 22)

        art_size, art_x, art_y = 520, 70, 100
        glow_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_draw.rounded_rectangle([(art_x-25, art_y-25), (art_x+art_size+25, art_y+art_size+25)], radius=45, fill=glow_color)
        scene.paste(glow_layer.filter(ImageFilter.GaussianBlur(50)), (0, 0), glow_layer)
        scene.paste(fit_cover(source_image, (art_size, art_size)), (art_x, art_y), get_mask((art_size, art_size), 35))
        draw = ImageDraw.Draw(scene, "RGBA")
        draw.rounded_rectangle([(art_x, art_y), (art_x + art_size, art_y + art_size)], radius=35, outline=theme_color, width=5)

        right_x = 650
        draw.rounded_rectangle([(right_x, art_y), (right_x + 230, art_y + 45)], radius=20, fill=theme_color)
        draw.text((right_x + 30, art_y + 6), "NOW PLAYING", fill=(0, 0, 0), font=font_pill)
        draw.text((right_x, art_y + 80), title, fill=WHITE, font=font_title)
        draw.line([(right_x, art_y + 140), (1200, art_y + 140)], fill=theme_color, width=3)

        stat_y = art_y + 190
        draw.text((right_x, stat_y), "Duration:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y), duration, fill=theme_color, font=font_stats_value)
        draw.text((right_x, stat_y + 55), "Views:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y + 55), f"{views_str} views", fill=theme_color, font=font_stats_value)
        draw.text((right_x, stat_y + 110), "Player:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y + 110), f"@{channel}", fill=theme_color, font=font_stats_value)

        bar_y = stat_y + 190
        draw.rounded_rectangle([(right_x, bar_y), (right_x + 550, bar_y + 8)], radius=3, fill=(255, 255, 255, 40))
        draw.rounded_rectangle([(right_x, bar_y), (right_x + 110, bar_y + 8)], radius=3, fill=theme_color)
        draw.ellipse([(right_x + 101, bar_y - 6), (right_x + 119, bar_y + 14)], fill=WHITE)
        draw.text((right_x, bar_y + 22), "00:00", fill=WHITE, font=font_time)
        draw.text((right_x + 510, bar_y + 22), duration, fill=WHITE, font=font_time)

        draw_exact_icons(draw, right_x + 220, bar_y + 70, "prev")
        draw_exact_icons(draw, right_x + 275, bar_y + 70, "pause", fill=theme_color)
        draw_exact_icons(draw, right_x + 330, bar_y + 70, "next")

        if os.path.exists(temp_thumb_path): os.remove(temp_thumb_path)
        scene.save(cache_path)
        return cache_path
    except Exception as e:
        LOGGER.error(f"Thumbnail Error: {e}")
        return YOUTUBE_IMG_URL
        
