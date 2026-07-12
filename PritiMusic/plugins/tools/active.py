from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from unidecode import unidecode
from PritiMusic import app
from PritiMusic.misc import SUDOERS
from PritiMusic.utils.database import get_active_chats, get_active_video_chats
from PritiMusic.utils.database.clonedb import get_served_chats_clone, clonebotdb

𝐏𝐎𝐖𝐄𝐑𝐄𝐃_𝐁𝐘 = "🤞 **𝐏ᴏᴡєʀєᴅ 𝐁ʏ ➛ 𝐁𝐄𝐓𝐀 𝐁𝐎𝐓𝐒.🙂❤️**"

async def get_chat_link(chat_id):
    try:
        chat = await app.get_chat(chat_id)
        return f"https://t.me/{chat.username}" if chat.username else f"https://t.me/c/{str(chat_id)[4:]}/1", chat.title
    except:
        return None, None

async def fetch_stats(message: Message, is_video: bool, is_clone: bool):
    mystic = await message.reply_text("🔄 **ᴄʜєᴄᴋɪɴɢ...**")
    raw = await (get_active_video_chats() if is_video else get_active_chats())
    clones = await clonebotdb.find({}).to_list(None)
    clone_ids = {int(c["chat_id"]) for clone in clones for c in await get_served_chats_clone(clone.get("bot_id"))}

    if not raw:
        return await mystic.edit_text(f"📭 **ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛꜱ.**\n\n{𝐏𝐎𝐖𝐄𝐑𝐄𝐃_𝐁𝐘}")

    text = f"🎤 **{'ᴄʟᴏɴᴇ' if is_clone else 'ᴍᴀɪɴ'} ᴀᴄᴛɪᴠᴇ {'ᴠɪᴅᴇᴏ ' if is_video else ''}ᴄʜᴀᴛꜱ:**\n\n"
    count = 0
    for cid in raw:
        cid = int(cid)
        if (is_clone and cid not in clone_ids) or (not is_clone and cid in clone_ids): continue
        link, title = await get_chat_link(cid)
        if link and title:
            count += 1
            text += f"**{count}.** [{unidecode(title)[:25]}]({link}) `[{cid}]`\n"

    if count == 0:
        return await mystic.edit_text(f"📭 **ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛꜱ.**\n\n{𝐏𝐎𝐖𝐄𝐑𝐄𝐃_𝐁𝐘}")
    await mystic.edit_text(f"{text}\n{𝐏𝐎𝐖𝐄𝐑𝐄𝐃_𝐁𝐘}", disable_web_page_preview=True)

@app.on_message(filters.command(["activevc", "vc", "activevideo", "av"]) & SUDOERS)
async def main_stats(c, m): await fetch_stats(m, "v" in m.command[0] and "vc" not in m.command[0], False)

@app.on_message(filters.command(["cvc", "cvvc"]) & SUDOERS)
async def clone_stats(c, m): await fetch_stats(m, "vv" in m.command[0], True)

@app.on_message(filters.command(["astats", "tvc"]) & SUDOERS)
async def astats(_, m):
    tvc, tvvc = len(await get_active_chats()), len(await get_active_video_chats())
    await m.reply_text(f"📊 **ꜱᴛᴀᴛꜱ:**\n\n🎙️ **ᴠᴄ:** `{tvc}` | 📹 **ᴠᴠᴄ:** `{tvvc}`\n\n{𝐏𝐎𝐖𝐄𝐑𝐄𝐃_𝐁𝐘}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎤 ᴍᴀɪɴ ᴠᴄ", "activevc_cb"), InlineKeyboardButton("📹 ᴍᴀɪɴ ᴠᴠᴄ", "activev_cb")],
            [InlineKeyboardButton("🤖 ᴄʟᴏɴᴇ ᴠᴄ", "cvc_cb"), InlineKeyboardButton("🤖 ᴄʟᴏɴᴇ ᴠᴠᴄ", "cvvc_cb")]
        ]))

@app.on_callback_query(filters.regex(r"(.+)_cb") & SUDOERS)
async def callbacks(_, q):
    await fetch_stats(q.message, "v" in q.data and "vv" not in q.data or "vv" in q.data, "c" in q.data)
    
