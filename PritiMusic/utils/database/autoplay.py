import glob
import os
import random
from typing import Dict

import yt_dlp
from py_yt import VideosSearch

from PritiMusic.core.mongo import mongodb

# =========================================================
# 🗄️ MONGODB AUTOPLAY SETTINGS (Database)
# =========================================================

# MongoDB mein autoplay ka collection
autoplaydb = mongodb.autoplay

# Cache dictionary: Isse bot har baar database check nahi karega, balki memory se fast read karega
autoplay_cache: Dict[int, bool] = {}


async def is_autoplay_group(chat_id: int) -> bool:
    """
    Check karta hai ki group mein autoplay enable hai ya nahi.
    Pehle cache mein check karega, agar nahi mila toh database mein.
    """
    if chat_id in autoplay_cache:
        return autoplay_cache[chat_id]

    chat = await autoplaydb.find_one({"chat_id": chat_id})
    if not chat:
        autoplay_cache[chat_id] = False
        return False

    autoplay_cache[chat_id] = True
    return True


async def add_autoplay_group(chat_id: int):
    """
    Group mein autoplay ON karta hai aur database me save karta hai.
    """
    is_on = await is_autoplay_group(chat_id)
    if not is_on:
        # Cache aur Database dono update karein
        autoplay_cache[chat_id] = True
        # insert_one ki jagah upsert=True use kiya hai taaki duplicate entry ka error na aaye
        await autoplaydb.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)


async def remove_autoplay_group(chat_id: int):
    """
    Group se autoplay OFF karta hai aur database se delete karta hai.
    """
    is_on = await is_autoplay_group(chat_id)
    if is_on:
        # Cache aur Database dono se remove karein
        autoplay_cache[chat_id] = False
        await autoplaydb.delete_one({"chat_id": chat_id})


# =========================================================
# 🧠 PER-CHAT PLAY HISTORY (Memory based tracker)
# =========================================================

_HISTORY_LIMIT = 50
_played_history: dict[int, list[str]] = {}


def remember_played(chat_id: int, vidid: str):
    """
    Jab bhi gaana chale, uski ID yaad rakhta hai taaki repeat na ho.
    """
    if not vidid:
        return
    hist = _played_history.setdefault(chat_id, [])
    if vidid in hist:
        hist.remove(vidid)
    hist.append(vidid)
    if len(hist) > _HISTORY_LIMIT:
        del hist[: len(hist) - _HISTORY_LIMIT]


def _history(chat_id: int) -> list:
    """
    Kisi bhi group ki aakhri 50 songs ki history return karta hai.
    """
    return _played_history.get(chat_id, [])


def clear_history(chat_id: int):
    """
    Group ki history memory se delete karta hai.
    """
    _played_history.pop(chat_id, None)


def _extract_candidates(results, chat_id: int, skip_history: bool):
    """
    YouTube results se un videos ko filter karta hai jo pehle play nahi huye.
    """
    candidates = []
    played = [] if skip_history else _history(chat_id)
    for video in results:
        vidid = video.get("id")
        title = video.get("title")
        link = video.get("link")
        duration = video.get("duration")
        
        if not (vidid and title and link and duration):
            continue
            
        if vidid in played:
            continue
            
        thumbs = video.get("thumbnails") or []
        thumb = thumbs[0].get("url", "").split("?")[0] if thumbs else None
        
        candidates.append(
            {
                "vidid": vidid,
                "title": title,
                "link": link,
                "duration_min": duration,
                "thumb": thumb,
            }
        )
    return candidates
