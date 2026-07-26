import os
import time
import asyncio
import random
import string
import re
import unicodedata
import urllib.parse 
from urllib.parse import urlparse, unquote

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

import config
from PritiMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app, LOGGER
from PritiMusic.core.call import Lucky
from PritiMusic.utils import seconds_to_min, time_to_seconds
from PritiMusic.utils.channelplay import get_channeplayCB
from PritiMusic.utils.decorators.language import languageCB
from PritiMusic.utils.decorators.play import PlayWrapper
from PritiMusic.utils.formatters import formats
from PritiMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from PritiMusic.utils.logger import play_logs
from PritiMusic.utils.stream.stream import stream
from config import BANNED_USERS, lyrical

# =======================================================
# 🎨 PREMIUM TEXT STYLES & FALLBACKS
# =======================================================
MSG_DOWNLOADING = "➛ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐁𝐚𝐛𝐲 𝐩𝐥𝐞𝐚𝐬𝐞 𝐰𝐚𝐢𝐭😁...."
MSG_STARTING = "➛ 𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐒𝐭𝐫𝐞𝐚𝐦 𝐄𝐧𝐣𝐨𝐲🎵❤️...."
FALLBACK_IMG = "https://telegra.ph/file/2e3d368e77c449c287430.jpg" # CRITICAL FIX: Yeh crash rokega

def get_timer_text(start_time, end_time=None):
    if end_time is None:
        end_time = time.time()
    time_taken = round(end_time - start_time, 2)
    if time_taken < 1:
        return f"{int(time_taken * 1000)} ms"
    return f"{time_taken} sec"

# =======================================================
# 🚀 STYLISH LIVE PROGRESS BAR (MODERN DOTTED STYLE)
# =======================================================
EDIT_TIME = {}

async def stylish_progress_bar(current, total, msg, start_time, command_start_time=None):
    if total == 0:
        return
        
    now = time.time()
    if msg.id in EDIT_TIME:
        if now - EDIT_TIME[msg.id] < 2.0:
            return
    EDIT_TIME[msg.id] = now

    percentage = current * 100 / total
    downloaded = round(current / (1024 * 1024), 2)
    total_size = round(total / (1024 * 1024), 2)
    speed = round(downloaded / (now - start_time), 2) if (now - start_time) > 0 else 0
    eta = round((total - current) / (speed * 1024 * 1024)) if speed > 0 else 0
    
    filled = int(percentage / 10)
    empty = 10 - filled
    bar = "●" * filled + "○" * empty

    text = f"**{MSG_DOWNLOADING}**\n\n"
    text += f"**⚡ 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬:** `[{bar}] {round(percentage, 2)}%`\n"
    text += f"**📥 𝐒𝐢𝐳𝐞:** `{downloaded} MB / {total_size} MB`\n"
    text += f"**🚀 𝐒𝐩𝐞𝐞𝐝:** `{speed} MB/s`\n"
    text += f"**⏳ 𝐄𝐓𝐀:** `{eta} sec`\n"

    try:
        await msg.edit_text(text)
    except Exception:
        pass

# -------------------------------------------------------
# 🛡️ BULLETPROOF SECURITY & GOD-MODE WALL
# -------------------------------------------------------
BANNED_WORDS = [
    "porn", "pornhub", "xvideos", "xnxx", "brazzers", 
    "onlyfans", "xhamster", "hot bhabhi", "deskbabe", "redtube", "spankbang",
    "child porn", "pedophile", "pedo", "jailbait", "loli", "shota", "csam",
    "incest", "bestiality", "zoophilia", "snuff", "revenge porn", "nonconsensual"
]

SECURE_LOGGER_ID = -1003812209413 

def clean_invisible_chars(text):
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'[\u200B-\u200D\uFEFF\u202A-\u202E\u200e\u200f]', '', text)

def is_nsfw_content(text):
    if not text:
        return False
    text = clean_invisible_chars(unquote(str(text)).lower())
    for word in BANNED_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text):
            return True
    return False

def is_malicious_link(text):
    if not text:
        return False
    text = clean_invisible_chars(unquote(str(text)).lower())
    if re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text): return True
    bad_extensions = ["webhook", "ngrok", "localhost", "0.0.0.0", ".sh", ".txt", "payload", ".exe", ".bat", ".vbs", ".cmd", ".py", ".php"]
    if any(ext in text for ext in bad_extensions): return True
    dangerous_chars = ["rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval("]
    if any(char in text for char in dangerous_chars): return True
    return False

def bouncer_check(_, __, message: Message):
    if not message.text: return True
    text = clean_invisible_chars(unquote(message.text).lower())
    dangerous_symbols = ["ifs", "/etc/passwd", ".env", "webhook.site", "rm -rf", "wget ", "curl ", "chmod ", "bash -c", "eval("]
    if any(sym in text for sym in dangerous_symbols): return False 
    return True

god_mode_filter = filters.create(bouncer_check)

async def delete_after_delay(msg, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await msg.delete()
    except:
        pass

async def send_security_log(message: Message, breach_type: str, payload: str):
    try:
        video_url = "https://files.catbox.moe/5qgzw1.mp4"
        
        if message.from_user:
            user_id = message.from_user.id
            user_mention = message.from_user.mention
            username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
        else:
            user_id = "Unknown (Anonymous)"
            user_mention = "Anonymous Admin"
            username = "None"

        chat_id = message.chat.id
        chat_title = message.chat.title if message.chat.title else "Private/Unknown"
        
        if message.chat and message.chat.username:
            chat_link = f"https://t.me/{message.chat.username}"
        else:
            chat_link = f"`{chat_id}` (Private Group)"
            
        # USER REQUESTED LOG FORMAT
        log_text = (
            f"🚨 **sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: {breach_type}** 🚨\n\n"
            f"👤 **User:** {user_mention}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"📛 **Username:** {username}\n"
            f"👥 **Group Name:** {chat_title}\n"
            f"🔗 **Group Link/ID:** {chat_link}\n\n"
            f"⚠️ **Payload/Link:**\n`{payload}`"
        )
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🚫 Block User", callback_data=f"block_user_{user_id}"),
                InlineKeyboardButton("🛑 Block Chat", callback_data=f"block_chat_{chat_id}")
            ]
        ])
        
        try:
            await app.send_message(SECURE_LOGGER_ID, log_text, reply_markup=buttons)
        except Exception as e:
            print(f"Logger Error: {e}")

        try:
            await message.delete()
        except:
            pass
            
        sent_msg = await message.reply_video(
            video=video_url, 
            caption="⚠️ **Malicious content detected. This action is not allowed.**\n\n_This message will auto-delete in 10 min._"
        )
        
        try:
            message.stop_propagation()
        except:
            pass
        
        asyncio.create_task(delete_after_delay(sent_msg, 600))
        
    except Exception as e:
        print(f"Security Log Error: {e}")

def is_malicious_play(text):
    if not text:
        return False
        
    decoded_text = unquote(text)
    
    play_commands = ("/play", "/vplay", "/cplay", ".play", "!play")
    if not any(decoded_text.lower().startswith(cmd) for cmd in play_commands):
        return False  
        
    patterns = [
        r"webhook\.site",
        r"requestbin\.com",
        r"ngrok\.io",
        r"t\.ly",
        r"bit\.ly"
    ]
    
    return any(re.search(p, decoded_text, re.IGNORECASE) for p in patterns)

@app.on_message(filters.text | filters.caption, group=-5)
async def handle_security(client, message: Message):
    text = message.text or message.caption
    
    if text and is_malicious_play(text):
        await send_security_log(message, "ᴍᴀʟɪᴄɪᴏᴜs ᴘʟᴀʏ ᴀᴛᴛᴇᴍᴘᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ", text)
# =======================================================

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list):
            return random.choice(img_list)
        return img_list
    return FALLBACK_IMG

def clean_youtube_url(url):
    if not isinstance(url, str): return url, None, "unknown"
    
    list_match = re.search(r"list=([a-zA-Z0-9_-]+)", url)
    if list_match and ("youtube.com" in url or "youtu.be" in url):
        return f"https://www.youtube.com/playlist?list={list_match.group(1)}", list_match.group(1), "playlist"
        
    yt_match = re.search(r"(?:v=|youtu\.be/|shorts/|live/|embed/|watch\?v=|music\.youtube\.com/watch\?v=|/v/)([a-zA-Z0-9_-]{11})", url)
    if yt_match:
        return f"https://www.youtube.com/watch?v={yt_match.group(1)}", yt_match.group(1), "video"
        
    return url, None, "unknown"

# -------------------------------------------------------

@app.on_message(
    filters.command(["play", "vplay", "cplay", "cvplay", "playforce", "vplayforce", "cplayforce", "cvplayforce"] ,prefixes=["/", "!", "%", ".", "@", "#"])
    & filters.group
    & ~BANNED_USERS
    & god_mode_filter
)
@PlayWrapper
async def play_commnd(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    command_start_time = time.time()
    mystic = await message.reply_text(MSG_DOWNLOADING)
    
    plist_id = None
    slider = None
    plist_type = None
    spotify = None
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    audio_telegram = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )

    video_telegram = (
        (message.reply_to_message.video or message.reply_to_message.document)
        if message.reply_to_message
        else None
    )
    
    if audio_telegram:
        if audio_telegram.file_size > 419430400: # 400MB LIMIT
            return await mystic.edit_text("❌ **File is too large! Maximum allowed limit is 400 MB BECAUSE OF HEAVY LOAD BOAT BECOME SLOW SO WE CAN'T SORRY.**")
            
        duration_min = seconds_to_min(audio_telegram.duration) if hasattr(audio_telegram, 'duration') and audio_telegram.duration else "Unknown"
        if hasattr(audio_telegram, 'duration') and audio_telegram.duration and audio_telegram.duration > config.DURATION_LIMIT:
            return await mystic.edit_text(
                _["play_6"].format(config.DURATION_LIMIT_MIN, app.mention)
            )
            
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if audio_telegram.file_size > 20971520: 
            from PritiMusic.utils.database import get_assistant
            userbot = await get_assistant(chat_id)
            if not userbot:
                return await mystic.edit_text("❌ **Assistant Required!**\nTo play files larger than 20MB, the assistant account must be active.")
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"❌ **Assistant Access Error:** Assistant cannot see this message. `{e}`")

        start_dl_time = time.time()
        
        try:
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_dl_time, command_start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"❌ **Download Failed:**\n`{str(e)}`")

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = audio_telegram.file_name if hasattr(audio_telegram, 'file_name') else "Audio File"
            dur = await Telegram.get_duration(audio_telegram, file_path)
            
            # ✅ FIX: Missing Thumbnail added to prevent crashing in stream.py
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
                "thumb": get_random_img(getattr(config, "TELEGRAM_AUDIO_URL", None)) or FALLBACK_IMG
            }
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Audio)", details.get("title", ""))
                return await mystic.edit_text("**🚫 sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                try:
                    return await mystic.edit_text(f"❌ **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴀᴜᴅɪᴏ):**\n\n`{str(e)}`")
                except: return
            return await mystic.delete()
        else:
            return await mystic.edit_text("❌ **Download Failed:** The file is empty or corrupted.")
            
    elif video_telegram:
        if message.reply_to_message.document:
            try:
                ext = video_telegram.file_name.split(".")[-1]
                if ext.lower() not in formats:
                    return await mystic.edit_text(
                        _["play_7"].format(f"{' | '.join(formats)}")
                    )
            except:
                pass
                
        if video_telegram.file_size > 419430400: # 400MB Limit
            return await mystic.edit_text("❌ **File is too large! Maximum allowed limit is 400 MB BECAUSE OF HEAVY LOAD BOAT BECOME SLOW SO WE CAN'T SORRY.**")
            
        dl_client = client
        msg_to_dl = message.reply_to_message
        
        if video_telegram.file_size > 20971520:
            from PritiMusic.utils.database import get_assistant
            userbot = await get_assistant(chat_id)
            if not userbot:
                return await mystic.edit_text("❌ **Assistant Required!**\nTo play files larger than 20MB, the assistant account must be active.")
            dl_client = userbot
            try:
                msg_to_dl = await userbot.get_messages(message.chat.id, message.reply_to_message.id)
            except Exception as e:
                return await mystic.edit_text(f"❌ **Assistant Access Error:** Assistant cannot see this message. `{e}`")

        start_dl_time = time.time()

        try:
            file_path = await dl_client.download_media(
                msg_to_dl,
                file_name="downloads/",
                progress=stylish_progress_bar,
                progress_args=(mystic, start_dl_time, command_start_time)
            )
        except Exception as e:
            return await mystic.edit_text(f"❌ **Download Failed:**\n`{str(e)}`")

        if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            message_link = await Telegram.get_link(message)
            file_name = video_telegram.file_name if hasattr(video_telegram, 'file_name') else "Video File"
            dur = await Telegram.get_duration(video_telegram, file_path)
            
            # ✅ FIX: Missing Thumbnail added here to prevent "Invalid File" error!
            details = {
                "title": file_name,
                "link": message_link,
                "path": file_path,
                "dur": dur,
                "thumb": get_random_img(getattr(config, "TELEGRAM_VIDEO_URL", None)) or FALLBACK_IMG
            }
            
            if is_nsfw_content(details.get("title", "")):
                await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ (Telegram Video)", details.get("title", ""))
                return await mystic.edit_text("**🚫 sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

            try:
                if getattr(mystic, "text", None):
                    await mystic.edit_text(MSG_STARTING)
                    await asyncio.sleep(0.5)
            except: pass

            try:
                await stream(
                    _,
                    mystic,
                    user_id,
                    details,
                    chat_id,
                    user_name,
                    message.chat.id,
                    video=True,
                    streamtype="telegram",
                    forceplay=fplay,
                )
            except Exception as e:
                try:
                    return await mystic.edit_text(f"❌ **sᴛʀᴇᴀᴍ ᴇʀʀᴏʀ (ᴠɪᴅᴇᴏ):**\n\n`{str(e)}`")
                except: return
            return await mystic.delete()
        else:
            return await mystic.edit_text("❌ **Download Failed!** The file is empty.\n\n_Note: Assistant accounts can download up to 2GB max (4GB if premium)._")
            
    elif url:
        if not url.startswith(("http://", "https://")):
            return await mystic.edit_text("❌ **Security Error:** Local files are not allowed.")
            
        if is_malicious_link(url):
            await send_security_log(message, "ᴍᴀʟɪᴄɪᴏᴜs ʜᴀᴄᴋ ʟɪɴᴋ", url)
            return await mystic.edit_text("**🚫 sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴍᴀʟɪᴄɪᴏᴜs ʟɪɴᴋ ʙʟᴏᴄᴋᴇᴅ!**")

        if is_nsfw_content(url):
            await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", url)
            return await mystic.edit_text("**🚫 sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")

        allowed_domains = [
            "youtube.com", "youtu.be",
            "spotify.com", "open.spotify.com",
            "soundcloud.com", "m.soundcloud.com",
            "music.apple.com", "resso.com"
        ]
        
        if not any(domain in url for domain in allowed_domains):
             return await mystic.edit_text(
                 "❌ **Unsupported Link!**\n\n"
                 "Only YouTube, Spotify, SoundCloud, Apple Music, and Resso are supported."
             )

        if await YouTube.exists(url):
            clean_url, ext_id, y_type = clean_youtube_url(url)
            
            if y_type == "playlist":
                try:
                    details = await YouTube.playlist(
                        clean_url,
                        config.PLAYLIST_FETCH_LIMIT,
                        message.from_user.id,
                    )
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                streamtype = "playlist"
                plist_type = "yt"
                plist_id = ext_id
                
                img = get_random_img(config.PLAYLIST_IMG_URL)
                cap = _["play_10"]
                
            elif y_type == "video":
                try:
                    details, track_id = await YouTube.track(clean_url)
                except Exception as e:
                    print(e)
                    return await mystic.edit_text(_["play_3"])
                    
                if not details:
                    return await mystic.edit_text("❌ **Error:** Failed to fetch track details from the server.")
                if is_nsfw_content(details.get("title", "")):
                    await send_security_log(message, "ɴsғᴡ ᴠɪᴏʟᴀᴛɪᴏɴ", details.get("title", ""))
                    return await mystic.edit_text("**🚫 sᴇᴄᴜʀɪᴛʏ ᴀʟᴇʀᴛ: ᴀᴅᴜʟᴛ ᴄᴏɴᴛᴇɴᴛ ɪs sᴛʀɪᴄᴛʟʏ ᴘʀᴏʜɪʙɪᴛᴇᴅ!**")