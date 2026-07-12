import asyncio
import random
import math
from pyrogram.types import CallbackQuery, InputMediaPhoto, InputMediaVideo, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from pyrogram.errors import WebpageMediaEmpty

from PritiMusic import YouTube, app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import SUDOERS, db
from PritiMusic.utils.database import (
    get_active_chats, get_lang, get_upvote_count, is_active_chat,
    is_music_playing, is_nonadmin_chat, music_off, music_on, set_loop, get_assistant
)
# ✅ Added Autoplay database imports
from PritiMusic.utils.database.autoplay import is_autoplay_group, add_autoplay_group, remove_autoplay_group

from PritiMusic.utils.decorators.language import languageCB
from PritiMusic.utils.formatters import seconds_to_min
from PritiMusic.utils.inline import close_markup, stream_markup, stream_markup_timer
from PritiMusic.utils.stream.autoclear import auto_clean
from PritiMusic.utils.thumbnails import get_thumb
import config
from config import (
    BANNED_USERS, SOUNCLOUD_IMG_URL, STREAM_IMG_URL, TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL, START_IMG_URL, adminlist, confirmer, votemode
)
from strings import get_string
from PritiMusic.utils.inline.start import private_panel

checker = {}
upvoters = {}

# --- BACK BUTTON HANDLER ---
@app.on_callback_query(filters.regex("settingsback_helper") & ~BANNED_USERS)
@languageCB
async def settings_back_helper(client, CallbackQuery, _):
    try:
        await CallbackQuery.answer()
    except:
        pass

    if isinstance(START_IMG_URL, list):
        img = random.choice(START_IMG_URL)
    else:
        img = START_IMG_URL

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media=img,
            caption=_["start_2"].format(CallbackQuery.from_user.mention, app.mention)
        ),
        reply_markup=InlineKeyboardMarkup(private_panel(_))
    )

# --- CLONE PAGE ---
@app.on_callback_query(filters.regex("clone_page") & ~BANNED_USERS)
@languageCB
async def clone_page_cb(client, CallbackQuery, _):
    await CallbackQuery.answer()
    clone_text = (
"<b>ϻᴧᴋє ʏσυʀ σᴡη ϻυsɪᴄ ʙσᴛ ᴡᴧᴛᴄʜɪηɢ ᴛʜє ᴠɪᴅєσ ᴄᴧʀєғυʟʟʏ.</b>\n\n"
"<blockquote><b><u>ᴄʟσηє ᴄσϻϻᴧηᴅs :</u></b>\n\n"
"<b><u>ᴧʟʟ υsєʀs :</u></b>\n"
"/clone – <b>ᴄʟσηє ʏσυʀ σᴡη ʙσᴛ υsɪηɢ ʙσᴛ ᴛσᴋєη ғʀσϻ @BotFather.</b>\n"
"<b>єxᴧϻᴘʟє:</b> /clone <code>ᴘᴧsᴛє_ᴛσᴋєη_ʜєʀє</code>\n\n"
"/rmbot – <b>ᴅєʟєᴛє ʏσυʀ ᴄʟσηєᴅ ʙσᴛ.</b>\n\n"
"/mybot – <b>ᴄʜєᴄᴋ ᴛʜє ʙσᴛs ʏσυ'ᴠє ᴄʟσηєᴅ.</b>\n\n"
"<b><u>σᴡηєʀs & sυᴅσєʀs :</u></b>\n"
"/cloned – <b>ᴄʜєᴄᴋ ʜσᴡ ϻᴧηʏ ʙσᴛs ʜᴧᴠє ʙєєη ᴄʟσηєᴅ.</b>\n\n"
"/totalbots – <b>ᴠɪєᴡ ᴛʜє ᴛσᴛᴧʟ ηυϻʙєʀ σғ ᴄʟσηєᴅ ʙσᴛs.</b>\n\n"
"/premiumbots – <b>ᴄʜєᴄᴋ ʜσᴡ ϻᴧηʏ ᴘʀєϻɪυϻ ʙσᴛs ᴧʀє ʀυηηɪηɢ.</b>\n\n"
"/addpremium – <b>ᴧᴅᴅ ᴘʀєϻɪυϻ sᴛᴧᴛυs ᴛσ ᴧ ʙσᴛ ʙʏ ɪᴅ.</b>\n\n"
"/removepremium – <b>ʀєϻσᴠє ᴘʀєϻɪυϻ sᴛᴧᴛυs ʙʏ ʙσᴛ ɪᴅ.</b>\n\n"
"/clonedinfo – <b>ᴠɪєᴡ ɪηғσʀϻᴧᴛɪση ᴧʙσυᴛ ᴄʟσηєᴅ ʙσᴛs.</b>\n\n"
"/delallclone – <b>ᴅєʟєᴛє ᴧʟʟ ᴄʟσηє ᴅᴧᴛᴧʙᴧsєs ᴧηᴅ ʙσᴛs.</b></blockquote>"
    )
    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media="https://files.catbox.moe/f09yfp.jpg", 
            caption=clone_text
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(text="⌯ ʙᴀᴄᴋ ⌯", callback_data="settingsback_helper")]
            ]
        )
    )

# --- SUPPORT PAGE ---
@app.on_callback_query(filters.regex("support_page") & ~BANNED_USERS)
@languageCB
async def support_page_cb(client, CallbackQuery, _):
    await CallbackQuery.answer()
    support_text = (
        "**✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ sᴜᴘᴘᴏʀᴛ ᴍᴇɴᴜ ✨**\n\n"
        "ɪғ ʏᴏᴜ ɴᴇᴇᴅ ᴀɴʏ ʜᴇʟᴘ ʀᴇɢᴀʀᴅɪɴɢ ᴛʜᴇ ʙᴏᴛ ᴏʀ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴘᴏʀᴛ ᴀ ʙᴜɢ, "
        "ᴊᴏɪɴ ᴏᴜʀ sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ ᴏʀ ᴄʜᴀɴɴᴇʟ ʙᴇʟᴏᴡ."
    )

    custom_support_buttons = [
        [
            InlineKeyboardButton(text="📢 ᴜᴘᴅᴀᴛᴇs", url="https://t.me/betabot_hub"),
            InlineKeyboardButton(text="💬 sᴜᴘᴘᴏʀᴛ", url="https://t.me/betabot_support")
        ],
        [
            InlineKeyboardButton(text="⌯ ʙᴀᴄᴋ ⌯", callback_data="settingsback_helper")
        ]
    ]

    await CallbackQuery.edit_message_media(
        media=InputMediaPhoto(
            media="https://files.catbox.moe/lcw2m5.jpg", 
            caption=support_text
        ),
        reply_markup=InlineKeyboardMarkup(custom_support_buttons)
    )

# --- SOURCE PAGE (UPDATED TO PHOTO) ---
@app.on_callback_query(filters.regex("gib_source"))
async def gib_repo_callback(_, callback_query):
    try:
        image_url = "https://files.catbox.moe/lcw2m5.jpg"

        await callback_query.edit_message_media(
            media=InputMediaPhoto(
                media=image_url, 
                caption="REPO = ||ɪsᴛᴋʜᴀʀ ᴅᴇᴠɪʟ ᴋᴏ ᴘᴀᴘᴀ ʙᴏʟ ᴄʜᴀʟ ʙᴏʟ😎||"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="• ʙᴀᴄᴋ •", callback_data="settingsback_helper"),
                        InlineKeyboardButton(text="• ᴄʟᴏsᴇ •", callback_data="close")
                    ]
                ]
            ),
        )
    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("unban_assistant"))
async def unban_assistant(_, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    userbot = await get_assistant(chat_id)
    try:
        await app.unban_chat_member(chat_id, userbot.id)
        await callback.answer("Assistant Unbanned Successfully!", show_alert=True)
    except Exception:
        await callback.answer("Failed to unban. Give me Admin permissions.", show_alert=True)

# --- ADMIN COMMANDS ---
@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention

    if command == "UpVote":
        if chat_id not in votemode: votemode[chat_id] = {}
        if chat_id not in upvoters: upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters: upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote: votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(CallbackQuery.from_user.id)
            votemode[chat_id][CallbackQuery.message.id] += 1

        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])

        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
                if current["vidid"] != exists["vidid"] or current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message_text(_["admin_35"])
            except:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except:
                pass
            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"
        else:
            if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)
            upl = InlineKeyboardMarkup([[InlineKeyboardButton(text=f"👍 {get_upvotes}", callback_data=f"ADMIN  UpVote|{chat_id}_{counter}")]])
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
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
    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await Lucky.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await CallbackQuery.message.reply_text(_["admin_5"].format(mention), reply_markup=close_markup(_))
        await CallbackQuery.message.delete()

    # ✅ AUTOPLAY BUTTON LOGIC ADDED HERE
    elif command == "Autoplay":
        state = await is_autoplay_group(chat_id)
        if state:
            await remove_autoplay_group(chat_id)
            await CallbackQuery.answer("🔴 Autoplay Disabled!", show_alert=True)
            await CallbackQuery.message.reply_text(
                f"**🎧 𝐀ᴜᴛᴏᴘʟᴀʏ 𝐒ʏsᴛᴇᴍ**\n\nᴀᴜᴛᴏᴘʟᴀʏ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ ɪs ɴᴏᴡ **ᴅɪsᴀʙʟᴇᴅ 🔴**.\n└ ʙʏ : {mention}",
                 reply_markup=close_markup(_)
            )
        else:
            await add_autoplay_group(chat_id)
            await CallbackQuery.answer("🟢 Autoplay Enabled!", show_alert=True)
            await CallbackQuery.message.reply_text(
                f"🎧 𝐀ᴜᴛᴏᴘʟᴀʏ 𝐒ʏsᴛᴇᴍ\n\nᴀᴜᴛᴏᴘʟᴀʏ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ ɪs ɴᴏᴡ ᴇɴᴀʙʟᴇᴅ 🟢.\n└ ʙʏ : {mention}",
                  reply_markup=close_markup(_)
            )

    elif command == "Skip" or command == "Replay":
        check = db.get(chat_id)
        if not check or len(check) == 0:
            return await CallbackQuery.answer("ǫᴜᴇᴜᴇ ɪs ᴇᴍᴘᴛʏ ᴏʀ ᴛʜᴇ ᴘʟᴀʏʟɪsᴛ ʜᴀs ʙᴇᴇɴ ᴄʟᴇᴀʀᴇᴅ!", show_alert=True)
        if command == "Skip":
            txt = f"➻ sᴛʀᴇᴀᴍ sᴋɪᴩᴩᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"
            try:
                popped = check.pop(0)
                if popped: await auto_clean(popped)
                if not check:
                    await CallbackQuery.edit_message_text(txt)
                    await CallbackQuery.message.reply_text(_["admin_6"].format(mention, CallbackQuery.message.chat.title), reply_markup=close_markup(_))
                    return await Lucky.stop_stream(chat_id)
            except:
                return await Lucky.stop_stream(chat_id)
        else:
            txt = f"➻ sᴛʀᴇᴀᴍ ʀᴇ-ᴘʟᴀʏᴇᴅ 🎄\n│ \n└ʙʏ : {mention} 🥀"

        await CallbackQuery.answer()
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        duration = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0

        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None

        try:
            if "live_" in queued:
                n, link = await YouTube.video(videoid, True)
                if n == 0: return await CallbackQuery.message.reply_text(_["admin_7"].format(title))
                await Lucky.skip_stream(chat_id, link, video=status, image=image)
            elif "vid_" in queued:
                 await Lucky.skip_stream(chat_id, queued, video=status, image=image)
            else:
                 await Lucky.skip_stream(chat_id, queued, video=status, image=image)
        except:
            return await CallbackQuery.message.reply_text(_["call_6"])

        button = stream_markup(_, chat_id)
        img = await get_thumb(videoid, CallbackQuery.from_user.id, client)
        run = await CallbackQuery.message.reply_photo(
            photo=img if img else STREAM_IMG_URL,
            caption=_["stream_1"].format(f"https://t.me/{app.username}?start=info_{videoid}", title[:23], duration, user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        if chat_id in db and len(db[chat_id]) > 0:
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))

async def markup_timer():
    while not await asyncio.sleep(7):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id): continue
                playing = db.get(chat_id)
                if not playing or int(playing[0]["seconds"]) == 0: continue
                mystic = playing[0]["mystic"]
                try:
                    if checker[chat_id][mystic.id] is False: continue
                except: pass

                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except: _ = get_string("en")

                try:
                    buttons = stream_markup_timer(_, chat_id, seconds_to_min(playing[0]["played"]), playing[0]["dur"])
                    await mystic.edit_reply_markup(reply_markup=InlineKeyboardMarkup(buttons))
                except: continue
            except: continue

asyncio.create_task(markup_timer()) 

# --- YAHAN SE FILE ID NIKALNE WALA CODE START HOTA HAI ---
@app.on_message(filters.video & filters.private)
async def get_my_own_file_id(client, message):
    await message.reply_text(f"**Mera Video File ID (Isko Copy Karo):**\n`{message.video.file_id}`")
# --- YAHAN KHATAM ---
