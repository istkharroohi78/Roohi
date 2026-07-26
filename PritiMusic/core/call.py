import asyncio
import os
import random
import logging
from datetime import datetime, timedelta
from typing import Union
from ntgcalls import ConnectionNotFound, TelegramServerError

from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

import config
from PritiMusic import LOGGER, YouTube, app
from PritiMusic.misc import db

# 🔥 Error fixed: is_autoplay_on removed from here 🔥
from PritiMusic.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)

# Autoplay Imports
from PritiMusic.utils.autoplay import fetch_autoplay_track, remember_played
from PritiMusic.utils.stream.queue import put_queue

from PritiMusic.utils.exceptions import AssistantErr
from PritiMusic.utils.formatters import check_duration, seconds_to_min, speed_converter
from PritiMusic.utils.inline.play import stream_markup, telegram_markup
from PritiMusic.utils.stream.autoclear import auto_clean
from strings import get_string
from PritiMusic.utils.thumbnails import get_thumb

# ==========================================
# 🛑 GLOBAL ERROR HANDLER & STATE SYNC
# ==========================================
def handle_asyncio_exceptions(loop, context):
    msg = context.get("exception", context.get("message"))
    msg_str = str(msg).lower()
    expected_sync_events = ["groupcall_forbidden", "setvideocallstatus", "groupcall_invalid", "no active group call", "already ended"]
    if any(err in msg_str for err in expected_sync_events):
        pass
    else:
        logging.getLogger("asyncio").error(f"❌ Unhandled Asyncio Error: {msg}")

try: loop = asyncio.get_running_loop()
except RuntimeError: loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_asyncio_exceptions)

autoend = {}
counter = {}

def get_random_img(img_list):
    if img_list:
        if isinstance(img_list, list): return random.choice(img_list)
        return img_list
    return "https://telegra.ph/file/2e3d368e77c449c287430.jpg" 

async def _clear_(chat_id: int):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)

class Call(PyTgCalls):
    def __init__(self):
        PyTgCallsSession.notice_displayed = True
        self.userbot1 = Client(name="LuckyAss1", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING1))
        self.one = PyTgCalls(self.userbot1, cache_duration=100)

        self.two = None
        if getattr(config, "STRING2", None):
            self.userbot2 = Client(name="LuckyAss2", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING2))
            self.two = PyTgCalls(self.userbot2, cache_duration=100)

        self.three = None
        if getattr(config, "STRING3", None):
            self.userbot3 = Client(name="LuckyAss3", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING3))
            self.three = PyTgCalls(self.userbot3, cache_duration=100)

        self.four = None
        if getattr(config, "STRING4", None):
            self.userbot4 = Client(name="LuckyAss4", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING4))
            self.four = PyTgCalls(self.userbot4, cache_duration=100)

        self.five = None
        if getattr(config, "STRING5", None):
            self.userbot5 = Client(name="LuckyAss5", api_id=config.API_ID, api_hash=config.API_HASH, session_string=str(config.STRING5))
            self.five = PyTgCalls(self.userbot5, cache_duration=100)
            
        self.active_clients = {}

    def _build_stream(self, source: str, video: bool, ffmpeg: str | None = None) -> types.MediaStream:
        return types.MediaStream(
            media_path=source,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(types.MediaStream.Flags.AUTO_DETECT if video else types.MediaStream.Flags.IGNORE),
            ffmpeg_parameters=ffmpeg,
        )

    async def _play_on_assistant(self, client: PyTgCalls, chat_id: int, stream: types.MediaStream):
        try:
            await client.play(chat_id=chat_id, stream=stream, config=types.GroupCallConfig(auto_start=False))
        except exceptions.NoActiveGroupCall: raise
        except exceptions.NoAudioSourceFound: raise
        except (ConnectionNotFound, TelegramServerError): raise
        except Exception: raise
    async def pause_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

    async def resume_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    async def stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_call(chat_id, close=False)
        except Exception: pass
        if chat_id in self.active_clients: self.active_clients.pop(chat_id, None)

    async def stop_stream_force(self, chat_id: int):
        for string, client in [(config.STRING1, self.one), (config.STRING2, self.two), (config.STRING3, self.three), (config.STRING4, self.four), (config.STRING5, self.five)]:
            if not string or not client: continue
            try: await client.leave_call(chat_id, close=False)
            except Exception: pass
        try: await _clear_(chat_id)
        except Exception: pass
        if chat_id in self.active_clients: self.active_clients.pop(chat_id, None)

    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir): os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                vs = {"0.5": 2.0, "0.75": 1.35, "1.5": 0.68, "2.0": 0.5}.get(str(speed), 1.0)
                proc = await asyncio.create_subprocess_shell(
                    cmd=(f"ffmpeg -i {file_path} -filter:v setpts={vs}*PTS -filter:a atempo={speed} {out}"),
                    stdin=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
        else: out = file_path
        dur = int(await asyncio.get_event_loop().run_in_executor(None, check_duration, out))
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        xx = f"-ss {played} -to {duration}"
        video_mode = playing[0]["streamtype"] == "video"
        stream = self._build_stream(out, video=video_mode, ffmpeg=xx)
        if str(db[chat_id][0]["file"]) == str(file_path):
            await self._play_on_assistant(assistant, chat_id, stream)
        else: raise AssistantErr("Umm")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception: pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try: await assistant.leave_call(chat_id, close=False)
        except Exception: pass

    async def skip_stream(self, chat_id: int, link: str, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        stream = self._build_stream(link, video=bool(video))
        await self._play_on_assistant(assistant, chat_id, stream)

    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        ffmpeg = f"-ss {to_seek} -to {duration}"
        video_mode = mode == "video"
        stream = self._build_stream(file_path, video=video_mode, ffmpeg=ffmpeg)
        await self._play_on_assistant(assistant, chat_id, stream)

    # 🔥 AUTOPLAY SYSTEM 🔥
    async def autoplay_start(self, chat_id: int, original_chat_id: int, seed_title: str, seed_vidid: str = None, client: PyTgCalls = None) -> bool:
        if seed_vidid: remember_played(chat_id, seed_vidid)
        status_msg = None
        try:
            status_msg = await app.send_message(original_chat_id, "<blockquote>🎧 <b>𝗔ᴜᴛᴏ𝗣𝗹𝗮𝘆 𝗜s 𝗘ɴᴀ𝗯ʟᴇᴅ</b>\n\n🔍 <i>Sᴇᴀʀᴄʜɪɴɢ ɴᴇxᴛ sᴏɴɢ ғᴏʀ ʏᴏᴜ...</i></blockquote>")
        except Exception: pass

        async def _fail() -> bool:
            if status_msg:
                try: await status_msg.delete()
                except Exception: pass
            return False

        track = await fetch_autoplay_track(chat_id, seed_title, seed_vidid)
        if not track: return await _fail()

        language = await get_lang(chat_id)
        _ = get_string(language)

        try: file_path, direct = await YouTube.download(track["vidid"], None, videoid=True)
        except Exception: return await _fail()
        if not file_path: return await _fail()

        remember_played(chat_id, track["vidid"])
        title = track["title"].title()
        duration_min = track["duration_min"]

        await put_queue(chat_id, original_chat_id, file_path if direct else f"vid_{track['vidid']}", title, duration_min, "🔁 ᴀᴜᴛᴏᴘʟᴀʏ", track["vidid"], 1, "audio", forceplay=True)

        stream = self._build_stream(file_path, video=False)
        assistant = client or await group_assistant(self, chat_id)
        try: await self._play_on_assistant(assistant, chat_id, stream)
        except Exception: return await _fail()

        try:
            img = await get_thumb(track["vidid"], 0, app)
            if not img: img = "https://telegra.ph/file/2e3d368e77c449c287430.jpg"
            button = stream_markup(_, chat_id)
            run = await app.send_photo(
                chat_id=original_chat_id,
                photo=img,
                caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{track['vidid']}", title[:23], duration_min, "ᴀᴜᴛᴏᴘʟᴀʏ 🎧"),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
        except Exception: pass

        if status_msg:
            try: await status_msg.delete()
            except Exception: pass

        return True

    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOG_GROUP_ID)
        stream = self._build_stream(link, video=True)
        await self._play_on_assistant(assistant, config.LOG_GROUP_ID, stream)
        await asyncio.sleep(0.2)
        try: await assistant.leave_call(config.LOG_GROUP_ID, close=False)
        except Exception: pass

    async def join_call(self, chat_id: int, original_chat_id: int, link, video: Union[bool, str] = None, image: Union[bool, str] = None):
        assistant = await group_assistant(self, chat_id)
        try: language = await get_lang(chat_id); _ = get_string(language)
        except: _ = get_string("en")
        stream = self._build_stream(link, video=bool(video))
        try:
            await self._play_on_assistant(assistant, chat_id, stream)
            if chat_id not in self.active_clients: self.active_clients[chat_id] = []
            if assistant not in self.active_clients[chat_id]: self.active_clients[chat_id].append(assistant)
        except exceptions.NoActiveGroupCall: raise AssistantErr(_["call_8"])
        except Exception: raise AssistantErr(_["call_10"])
        
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video: await add_active_video_chat(chat_id)
        
        if await is_autoend():
            counter[chat_id] = {}
            try:
                users = len(await assistant.get_participants(chat_id))
                if users == 1: autoend[chat_id] = datetime.now() + timedelta(minutes=1)
            except: pass

    async def auto_end_task(self):
        empty_vcs = {}
        while True:
            await asyncio.sleep(60) 
            try:
                active_chats = list(self.active_clients.keys())
                for chat_id in active_chats:
                    if not self.active_clients.get(chat_id): continue
                    assistant = self.active_clients[chat_id][0]
                    try:
                        participants = await assistant.get_participants(chat_id)
                        if len(participants) <= 1:
                            if chat_id not in empty_vcs: empty_vcs[chat_id] = datetime.now()
                            elif (datetime.now() - empty_vcs[chat_id]).total_seconds() >= 600:
                                try:
                                    await self.stop_stream(chat_id)
                                    LOGGER(__name__).info(f"Bot left VC {chat_id} after 10 min inactivity.")
                                except: pass
                                empty_vcs.pop(chat_id, None)
                        else: empty_vcs.pop(chat_id, None)
                    except Exception: pass
            except Exception: pass
    async def change_stream(self, client: PyTgCalls, chat_id: int):
        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)

        try:
            if loop == 0:
                if check: popped = check.pop(0)
            else:
                loop = loop - 1
                await set_loop(chat_id, loop)

            if popped: await auto_clean(popped)

            # 🔥 DYNAMIC AUTOPLAY TRIGGER 🔥
            if not check:
                # Naya database function call (Error free)
                from PritiMusic.utils.database.autoplay import is_autoplay_group
                auto_on = await is_autoplay_group(chat_id)
                
                if auto_on and popped:
                    started = await self.autoplay_start(
                        chat_id,
                        popped.get("chat_id", chat_id),
                        popped.get("title"),
                        popped.get("vidid"),
                        client=client,
                    )
                    if started:
                        return
                
                await _clear_(chat_id)
                if chat_id in self.active_clients: self.active_clients.pop(chat_id, None)
                try: return await client.leave_call(chat_id, close=False)
                except Exception: return

        except Exception as e:
            LOGGER(__name__).error(f"❌ change_stream error: {e}")
            try: await _clear_(chat_id); await client.leave_call(chat_id, close=False)
            except Exception: pass
            return

        if db.get(chat_id):
            queued = db[chat_id][0]["file"]
            original_chat_id = db[chat_id][0]["chat_id"]
            streamtype = db[chat_id][0]["streamtype"]
            videoid = db[chat_id][0]["vidid"]
            chat_client = db[chat_id][0].get("client") or app

            db[chat_id][0]["played"] = 0
            exis = db[chat_id][0].get("old_dur")
            if exis:
                db[chat_id][0]["dur"] = exis
                db[chat_id][0]["seconds"] = db[chat_id][0]["old_second"]
                db[chat_id][0]["speed_path"] = None
                db[chat_id][0]["speed"] = 1.0
            video = True if str(streamtype) == "video" else False

            try: language = await get_lang(chat_id); _ = get_string(language)
            except: _ = get_string("en")

            if not db.get(chat_id): return
            
            raw_title = db[chat_id][0].get("title")
            title = str(raw_title).title() if raw_title else "Unknown Title"
            user = str(db[chat_id][0].get("by", "Unknown User"))
            user_id = db[chat_id][0].get("user_id", 0) 
            duration_str = db[chat_id][0].get("dur", "0:00")

            # 🔥 PLAY LOGGER (Global Logger Group ke liye) 🔥
            logger_id = getattr(config, "LOG_GROUP_ID", getattr(config, "LOGGER_ID", None))
            if logger_id:
                try:
                    chat_obj = await app.get_chat(original_chat_id)
                    chat_name = chat_obj.title or "Unknown Chat"
                    chat_url = f"https://t.me/{chat_obj.username}" if chat_obj.username else f"https://t.me/c/{str(original_chat_id).replace('-100', '')}/1"
                    log_text = (
                        f"🎵 **NEW MEDIA PLAYED** ❞\n\n"
                        f"🥀 **CHAT :** {chat_name} [`{original_chat_id}`]\n"
                        f"👤 **USER :** {user} [`{user_id}`]\n"
                        f"📝 **TITLE :** {title[:40]}\n"
                        f"⏳ **DURATION :** {duration_str}"
                    )
                    await app.send_message(int(logger_id), log_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 CHAT LINK", url=chat_url)]]))
                except Exception: pass

            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await chat_client.send_message(original_chat_id, text=_["call_6"])
                stream = self._build_stream(link, video=video)
                try: await self._play_on_assistant(client, chat_id, stream)
                except Exception: return await chat_client.send_message(original_chat_id, text=_["call_6"])
                button = stream_markup(_, chat_id)
                try:
                    run = await chat_client.send_photo(chat_id=original_chat_id, photo=get_random_img(config.STREAM_IMG_URL), caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], duration_str, user), reply_markup=InlineKeyboardMarkup(button))
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                except: pass

            elif "vid_" in queued:
                mystic = await chat_client.send_message(original_chat_id, _["call_7"])
                try: file_path, direct = await YouTube.download(videoid, mystic, videoid=True, video=video)
                except Exception:
                    try: await mystic.edit_text("⚠️ **YouTube Timeout! Skipping...**")
                    except: pass
                    await asyncio.sleep(2)
                    return await self.change_stream(client, chat_id)
                if not file_path or str(file_path) == "None":
                    return await self.change_stream(client, chat_id)
                stream = self._build_stream(file_path, video=video)
                try: await self._play_on_assistant(client, chat_id, stream)
                except Exception: return await chat_client.send_message(original_chat_id, text=_["call_6"])
                img = await get_thumb(videoid, user_id, chat_client) or get_random_img(config.PLAYLIST_IMG_URL)
                button = stream_markup(_, chat_id)
                try: await mystic.delete()
                except: pass
                try:
                    run = await chat_client.send_photo(chat_id=original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], duration_str, user), reply_markup=InlineKeyboardMarkup(button))
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "stream"
                except: pass

            elif "index_" in queued:
                stream = self._build_stream(videoid, video=video)
                try: await self._play_on_assistant(client, chat_id, stream)
                except Exception: return await chat_client.send_message(original_chat_id, text=_["call_6"])
                button = stream_markup(_, chat_id)
                try:
                    run = await chat_client.send_photo(chat_id=original_chat_id, photo=get_random_img(config.STREAM_IMG_URL), caption=_["stream_2"].format(user), reply_markup=InlineKeyboardMarkup(button))
                    db[chat_id][0]["mystic"] = run
                    db[chat_id][0]["markup"] = "tg"
                except: pass

            else:
                stream = self._build_stream(queued, video=video)
                try: await self._play_on_assistant(client, chat_id, stream)
                except Exception: return await chat_client.send_message(original_chat_id, text=_["call_6"])
                
                if videoid == "telegram":
                    button = stream_markup(_, chat_id)
                    tg_img = get_random_img(config.TELEGRAM_AUDIO_URL) if not video else get_random_img(config.TELEGRAM_VIDEO_URL)
                    try:
                        run = await chat_client.send_photo(chat_id=original_chat_id, photo=tg_img, caption=_["stream_1"].format(config.SUPPORT_GROUP, title[:23], duration_str, user), reply_markup=InlineKeyboardMarkup(button))
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    except: pass
                elif videoid in ["soundcloud", "spotify", "apple", "jiosaavn"]:
                    button = stream_markup(_, chat_id)
                    try:
                        run = await chat_client.send_photo(chat_id=original_chat_id, photo=get_random_img(config.SOUNCLOUD_IMG_URL), caption=_["stream_1"].format(config.SUPPORT_GROUP, title[:23], duration_str, user), reply_markup=InlineKeyboardMarkup(button))
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "tg"
                    except: pass
                else:
                    img = await get_thumb(videoid, user_id, chat_client) or get_random_img(config.PLAYLIST_IMG_URL)
                    button = stream_markup(_, chat_id)
                    try:
                        run = await chat_client.send_photo(chat_id=original_chat_id, photo=img, caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], duration_str, user), reply_markup=InlineKeyboardMarkup(button))
                        db[chat_id][0]["mystic"] = run
                        db[chat_id][0]["markup"] = "stream"
                    except: pass

    async def ping(self):
        pings = []
        if getattr(config, "STRING1", None) and self.one: pings.append(self.one.ping)
        if getattr(config, "STRING2", None) and self.two: pings.append(self.two.ping)
        if getattr(config, "STRING3", None) and self.three: pings.append(self.three.ping)
        if getattr(config, "STRING4", None) and self.four: pings.append(self.four.ping)
        if getattr(config, "STRING5", None) and self.five: pings.append(self.five.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Clients...\n")
        if getattr(config, "STRING1", None): await self.one.start()
        if getattr(config, "STRING2", None): await self.two.start()
        if getattr(config, "STRING3", None): await self.three.start()
        if getattr(config, "STRING4", None): await self.four.start()
        if getattr(config, "STRING5", None): await self.five.start()
        asyncio.create_task(self.auto_end_task())

    async def decorators(self):
        async def _update_handler(client, update: types.Update):
            try:
                c_id = getattr(update, "chat_id", None)
                if not c_id: return
                if isinstance(update, types.StreamEnded) and update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self.change_stream(client, c_id)
                elif isinstance(update, types.ChatUpdate) and update.status in [types.ChatUpdate.Status.KICKED, types.ChatUpdate.Status.LEFT_GROUP, types.ChatUpdate.Status.CLOSED_VOICE_CHAT]:
                    await self.stop_stream(c_id)
            except Exception as e:
                LOGGER(__name__).error(f"Update error: {e}")

        if getattr(config, "STRING1", None): self.one.on_update()(_update_handler)
        if getattr(config, "STRING2", None): self.two.on_update()(_update_handler)
        if getattr(config, "STRING3", None): self.three.on_update()(_update_handler)
        if getattr(config, "STRING4", None): self.four.on_update()(_update_handler)
        if getattr(config, "STRING5", None): self.five.on_update()(_update_handler)

Lucky = Call()
