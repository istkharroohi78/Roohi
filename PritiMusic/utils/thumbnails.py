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

# 🟢 IMPORT ERROR FIX: Agar CACHE_DIR dir.py mein nahi mila, toh crash nahi hoga
try:
    from PritiMusic.core.dir import CACHE_DIR
except ImportError:
    CACHE_DIR = "cache"

LOGGER = __import__('logging').getLogger(__name__)

# 🟢 PILLOW COMPATIBILITY FIX
try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS = Image.LANCZOS

TITLE_FONT_PATH = "PritiMusic/assets/font2.ttf"
META_FONT_PATH = "PritiMusic/assets/font.ttf"
CANVAS_SIZE = (1280, 720)

TEXT_GRAY = (180, 180, 180)
WHITE = (255, 255, 255)

# 🎨 PREDEFINED PREMIUM GLOW COLORS (Pink, Sky Blue, Yellow, Blue)
NEON_COLORS = [
    (255, 40, 130),   # Neon Pink
    (0, 204, 255),    # Sky Blue
    (255, 220, 0),    # Neon Yellow
    (20, 100, 255)    # Neon Blue
]

# ----------------- HELPER FUNCTIONS ----------------- #

def fit_cover(image, size):
    ratio = max(size[0] / image.size[0], size[1] / image.size[1])
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    resized = image.resize(new_size, LANCZOS)
    
    left = (new_size[0] - size[0]) // 2
    top = (new_size[1] - size[1]) // 2
    right = left + size[0]
    bottom = top + size[1]
    
    return resized.crop((left, top, right, bottom))

def get_mask(size, radius, antialias=4):
    mask = Image.new("L", (size[0] * antialias, size[1] * antialias), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] * antialias, size[1] * antialias), radius=radius * antialias, fill=255)
    return mask.resize(size, LANCZOS)

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

def format_views(view_count_str):
    try:
        views_num = int(re.sub(r"\D", "", str(view_count_str)))
        if views_num >= 1_000_000_000:
            return f"{views_num / 1_000_000_000:.1f} B"
        elif views_num >= 1_000_000:
            return f"{views_num // 1_000_000} M"
        elif views_num >= 1_000:
            return f"{views_num // 1_000} K"
        return str(views_num)
    except:
        return "Unknown"

def trim_text(text: str, limit: int) -> str:
    clean_text = " ".join(str(text or "").split())
    if len(clean_text) <= limit:
        return clean_text
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
    # ----------------- MAIN THUMBNAIL GENERATOR ----------------- #

async def get_thumb(videoid, user_id=None):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_{user_id}_premium_v6.png")
    
    if os.path.isfile(cache_path):
        return cache_path

    url = f"https://www.youtube.com/watch?v={videoid}"
    unique_id = uuid.uuid4().hex[:8]
    temp_thumb_path = os.path.join(CACHE_DIR, f"temp_{videoid}_{unique_id}.png")

    try:
        results = VideosSearch(url, limit=1)
        results_data = (await results.next()).get("result", [])
        if not results_data:
            return YOUTUBE_IMG_URL

        result = results_data[0]
        title = trim_text(re.sub(r"[^\w\s&\-']", " ", result.get("title", "")).strip(), 28)
        duration = str(result.get("duration") or "00:00")
        views_str = format_views((result.get("viewCount") or {}).get("text") or "0")
        channel = trim_text(str((result.get("channel") or {}).get("name") or "Unknown Artist"), 20)
        
        thumbnails = result.get("thumbnails", [{}])
        thumbnail_url = thumbnails[-1].get("url", thumbnails[0].get("url", "")).split("?")[0]

        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            async with session.get(thumbnail_url) as resp:
                if resp.status == 200:
                    # 🟢 FILE HANDLING FIX: async with use kiya hai to close automatic ho jayega
                    async with aiofiles.open(temp_thumb_path, mode="wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL

        source_image = Image.open(temp_thumb_path).convert("RGBA")
        
        # 🎨 RANDOMLY SELECT ONE OF THE 4 PREMIUM COLORS
        theme_color = random.choice(NEON_COLORS)
        glow_color = (*theme_color, 160) # 160 is for Alpha (Transparency)

        background = fit_cover(source_image, CANVAS_SIZE)
        
        # 🟢 डार्क सिनेमैटिक ब्लर (Modified for attractive look)
        background = background.filter(ImageFilter.GaussianBlur(65))
        background = ImageEnhance.Brightness(background).enhance(0.20)
        background = ImageEnhance.Color(background).enhance(1.2)
        scene = background.copy()
        
        # 🟢 Fonts 
        font_title = load_font(TITLE_FONT_PATH, 42)
        font_stats_label = load_font(TITLE_FONT_PATH, 32)
        font_stats_value = load_font(TITLE_FONT_PATH, 32)
        font_pill = load_font(TITLE_FONT_PATH, 24)
        font_time = load_font(TITLE_FONT_PATH, 22)

        # --------------------------------------------------
        # 1. LEFT SIDE: SQUARE ART CARD WITH SELECTED GLOW
        # --------------------------------------------------
        art_size = 520 
        art_x, art_y = 70, 100
        
        # सॉफ्ट और अट्रैक्टिव ग्लो इफ़ेक्ट
        glow_layer = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)
        glow_spread = 25 
        glow_draw.rounded_rectangle(
            [(art_x - glow_spread, art_y - glow_spread), (art_x + art_size + glow_spread, art_y + art_size + glow_spread)],
            radius=45, fill=glow_color
        )
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(50))
        scene.paste(glow_layer, (0, 0), glow_layer)
        
        art_content = fit_cover(source_image, (art_size, art_size))
        art_mask = get_mask((art_size, art_size), 35)
        scene.paste(art_content, (art_x, art_y), art_mask)
        draw = ImageDraw.Draw(scene, "RGBA")
        
        draw.rounded_rectangle([(art_x, art_y), (art_x + art_size, art_y + art_size)], radius=35, outline=theme_color, width=5)

        # --------------------------------------------------
        # 2. RIGHT SIDE: NOW PLAYING PILL
        # --------------------------------------------------
        right_x = 650
        pill_w = 230
        pill_h = 45
        draw.rounded_rectangle([(right_x, art_y), (right_x + pill_w, art_y + pill_h)], radius=20, fill=theme_color)
        draw.text((right_x + 30, art_y + 6), "NOW PLAYING", fill=(0, 0, 0), font=font_pill)

        # --------------------------------------------------
        # 3. TITLE & NEON LINE
        # --------------------------------------------------
        title_y = art_y + 80
        draw.text((right_x, title_y), title, fill=WHITE, font=font_title)
        draw.line([(right_x, title_y + 60), (1200, title_y + 60)], fill=theme_color, width=3)

        # --------------------------------------------------
        # 4. STATS (Duration, Views, Player)
        # --------------------------------------------------
        stat_y = title_y + 110
        spacing = 55
        
        draw.text((right_x, stat_y), "Duration:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y), duration, fill=theme_color, font=font_stats_value)
        
        draw.text((right_x, stat_y + spacing), "Views:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y + spacing), f"{views_str} views", fill=theme_color, font=font_stats_value)
        
        draw.text((right_x, stat_y + spacing*2), "Player:", fill=TEXT_GRAY, font=font_stats_label)
        draw.text((right_x + 180, stat_y + spacing*2), f"@{channel}", fill=theme_color, font=font_stats_value)

        # --------------------------------------------------
        # 5. GLOWING PROGRESS BAR
        # --------------------------------------------------
        bar_y = stat_y + spacing*3 + 30
        bar_w = 550
        prog_w = int(bar_w * 0.20) 
        
        draw.rounded_rectangle([(right_x, bar_y), (right_x + bar_w, bar_y + 8)], radius=3, fill=(255, 255, 255, 40))
        
        bar_glow = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        bar_glow_draw = ImageDraw.Draw(bar_glow)
        bar_glow_draw.rounded_rectangle([(right_x, bar_y - 2), (right_x + prog_w, bar_y + 10)], radius=4, fill=theme_color)
        bar_glow = bar_glow.filter(ImageFilter.GaussianBlur(8))
        scene.paste(bar_glow, (0, 0), bar_glow)
        
        draw = ImageDraw.Draw(scene, "RGBA") 
        draw.rounded_rectangle([(right_x, bar_y), (right_x + prog_w, bar_y + 8)], radius=3, fill=theme_color)
        draw.ellipse([(right_x + prog_w - 9, bar_y - 6), (right_x + prog_w + 9, bar_y + 14)], fill=WHITE)
        
        draw.text((right_x, bar_y + 22), "00:00", fill=WHITE, font=font_time)
        
        # 🟢 PILLOW TEXT SIZE FALLBACK FIX
        try:
            dur_w = draw.textlength(duration, font=font_time)
        except AttributeError:
            try:
                dur_w = draw.textsize(duration, font=font_time)[0]
            except AttributeError:
                dur_w = 40 # Ultimate fallback 
                
        draw.text((right_x + bar_w - dur_w, bar_y + 22), duration, fill=WHITE, font=font_time)

        # --------------------------------------------------
        # 6. MEDIA CONTROLS
        # --------------------------------------------------
        ctrl_y = bar_y + 70
        draw_exact_icons(draw, right_x + 220, ctrl_y, "prev", fill=WHITE)
        draw_exact_icons(draw, right_x + 275, ctrl_y, "pause", fill=theme_color)
        draw_exact_icons(draw, right_x + 330, ctrl_y, "next", fill=WHITE)

        try:
            if os.path.exists(temp_thumb_path):
                os.remove(temp_thumb_path)
        except:
            pass

        scene.save(cache_path)
        return cache_path

    except Exception as e:
        LOGGER.error(f"Thumbnail Error: {e}")
        try:
            if os.path.exists(temp_thumb_path):
                os.remove(temp_thumb_path)
        except:
            pass
        return YOUTUBE_IMG_URL
    
