import random
import asyncio
from pyrogram import filters, Client
from pyrogram.types import CallbackQuery, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton

import config
from PritiMusic import app, YouTube
from PritiMusic.core.call import Lucky
from PritiMusic.misc import SUDOERS, db
from PritiMusic.utils.database import (
    get_active_chats, get_lang, get_upvote_count, is_active_chat,
    is_music_playing, is_nonadmin_chat, music_off, music_on, set_loop
)
from PritiMusic.utils.database.autoplay import is_autoplay_group, add_autoplay_group, remove_autoplay_group
from PritiMusic.utils.decorators.language import languageCB
from PritiMusic.utils.formatters import seconds_to_min
from PritiMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from PritiMusic.utils.thumbnails import get_thumb
from config import BANNED_USERS, STREAM_IMG_URL, adminlist
from strings import get_string
from PritiMusic.utils.inline.start import private_panel

# --- FIXED HANDLERS FOR CLONE & SUPPORT ---

@app.on_callback_query(filters.regex("support_callback"))
async def support_callback(client, CallbackQuery):
    await CallbackQuery.answer("Support ke liye yahan contact karein!", show_alert=True)
    # Yahan apna support link add karein
    await CallbackQuery.message.reply_text("📞 **Support Desk**\n\nKisi bhi samasya ke liye hamare group mein join karein.")

@app.on_callback_query(filters.regex("clone_callback"))
async def clone_callback(client, CallbackQuery):
    await CallbackQuery.answer("Clone system abhi update ho raha hai!", show_alert=True)

# --- BACK BUTTON HANDLER ---
@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_helper(client, CallbackQuery, _):
    await CallbackQuery.answer()
    img = random.choice(config.START_IMG_URL) if isinstance(config.START_IMG_URL, list) else config.START_IMG_URL
    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(media=img, caption=_["start_2"].format(CallbackQuery.from_user.mention, app.mention)),
        reply_markup=InlineKeyboardMarkup(private_panel(_))
    )

# --- ADMIN COMMANDS HANDLER ---
@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    
    mention = CallbackQuery.from_user.mention
    
    # Check Admin/Sudo Rights
    if not await is_nonadmin_chat(chat_id):
        if CallbackQuery.from_user.id not in SUDOERS:
            admins = adminlist.get(chat_id)
            if not admins or CallbackQuery.from_user.id not in admins:
                return await CallbackQuery.answer(_["admin_14"], show_alert=True)
                
    if command == "Pause":
        if not await is_music_playing(chat_id): return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await Lucky.pause_stream(chat_id)
        await CallbackQuery.message.reply_text(_["admin_2"].format(mention), reply_markup=close_markup(_))
        
    elif command == "Resume":
        if await is_music_playing(chat_id): return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await Lucky.resume_stream(chat_id)
        await CallbackQuery.message.reply_text(_["admin_4"].format(mention), reply_markup=close_markup(_))
        
    elif command in ["Stop", "End"]:
        await CallbackQuery.answer()
        await Lucky.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await CallbackQuery.message.reply_text(_["admin_5"].format(mention), reply_markup=close_markup(_))
        try: await CallbackQuery.message.delete()
        except: pass
            
    elif command in ["Skip", "Replay"]:
        check = db.get(chat_id)
        if not check:
            return await CallbackQuery.answer("Queue khali hai!", show_alert=True)
            
        if command == "Skip":
            await CallbackQuery.answer("Skipping...", show_alert=True)
            clients = await Lucky.get_active_clients(chat_id)
            pytgcalls_client = clients[0] if clients else Lucky.one
            await Lucky.change_stream(pytgcalls_client, chat_id)
            await CallbackQuery.edit_message_text(f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n└ʙʏ : {mention}", reply_markup=close_markup(_))
                elif command == "Autoplay":
        state = await is_autoplay_group(chat_id)
        if state:
            await remove_autoplay_group(chat_id)
            await CallbackQuery.answer("🔴 Autoplay Disabled!", show_alert=True)
            await CallbackQuery.message.reply_text(f"**🎧 𝐀𝐮𝐭𝐨𝐩𝐥𝐚𝐲 𝐒𝐲𝐬𝐭𝐞𝐦**\n\nStatus: **Disabled 🔴**\n└ ʙʏ : {mention}", reply_markup=close_markup(_))
        else:
            await add_autoplay_group(chat_id)
            await CallbackQuery.answer("🟢 Autoplay Enabled!", show_alert=True)
            await CallbackQuery.message.reply_text(f"**🎧 𝐀𝐮𝐭𝐨𝐩𝐥𝐚𝐲 𝐒𝐲𝐬𝐭𝐞𝐦**\n\nStatus: **Enabled 🟢**\n└ ʙʏ : {mention}", reply_markup=close_markup(_))
            
    else: # Replay Logic
        await CallbackQuery.answer("Replaying...", show_alert=True)
        txt = f"➻ sᴛʀᴇᴀᴍ ʀᴇ-ᴘʟᴀʏᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
        check = db.get(chat_id)
        db[chat_id][0]["played"] = 0
        img = await get_thumb(check[0]["vidid"], CallbackQuery.from_user.id, client) or \
              (random.choice(STREAM_IMG_URL) if isinstance(STREAM_IMG_URL, list) else STREAM_IMG_URL)
        await Lucky.skip_stream(chat_id, check[0]["file"], video=True if check[0]["streamtype"]=="video" else False)
        run = await CallbackQuery.message.reply_photo(
            photo=img,
            caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{check[0]['vidid']}", check[0]['title'][:23], check[0]['dur'], check[0]['by']),
            reply_markup=InlineKeyboardMarkup(stream_markup(_, chat_id)),
        )
        if chat_id in db and db[chat_id]:
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
        await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))

# --- TIMER MARKUP UPDATER ---
async def markup_timer():
    while True:
        await asyncio.sleep(7)
        try:
            active_chats = await get_active_chats()
            for chat_id in active_chats:
                try:
                    if not await is_music_playing(chat_id): continue
                    playing = db.get(chat_id)
                    if not playing or int(playing[0].get("seconds", 0)) == 0: continue
                    mystic = playing[0].get("mystic")
                    if not mystic: continue
                    try:
                        language = await get_lang(chat_id)
                        _ = get_string(language)
                    except: _ = get_string("en")
                    buttons = stream_markup_timer(_, chat_id, seconds_to_min(playing[0]["played"]), playing[0]["dur"])
                    await mystic.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
                except: continue
        except: pass

asyncio.create_task(markup_timer())
            
