import random
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from pyrogram.errors import MessageNotModified

from PritiMusic import app
from PritiMusic.utils.database.autoplay import (
    is_autoplay_group,
    add_autoplay_group,
    remove_autoplay_group,
)
# Assuming AdminActualCheck or a similar decorator exists for callbacks
from PritiMusic.utils.decorators import AdminRightsCheck
from config import BANNED_USERS

PHOTO_URL = "https://files.catbox.moe/6r97s4.jpg"

# 🔥 PREMIUM EMOJIS LIST 🔥
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

def get_panel(chat_id, enabled):
    status = "🟢 𝐄ɴᴀʙʟᴇᴅ" if enabled else "🔴 𝐃ɪsᴀʙʟᴇᴅ"

    caption = f"""
**🎵 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ 𝐒ᴇᴛᴛɪɴɢ𝐬**

➻ 𝐌ᴀɴᴀɢᴇ 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ ғᴇᴀᴛᴜʀᴇ ғᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.

**✦ 𝐂ᴜʀʀᴇɴᴛ 𝐒ᴛᴀᴛᴜ𝐬**
{status}

━━━━━━━━━━━━━━━
⚡ 𝐏ᴏᴡᴇʀᴇᴅ ʙʏ ➛ 𝐁ᴇᴛᴀ𝐁ᴏᴛ𝐬
"""

    buttons = InlineKeyboardMarkup(
        [
            [
                # ButtonStyle and custom emojis require specific Pyrogram forks.
                # Using standard InlineKeyboardButton format to prevent errors.
                InlineKeyboardButton(
                    "𝐄ɴᴀʙʟᴇ",
                    callback_data=f"AUTOPLAY_ENABLE|{chat_id}"
                ),
                InlineKeyboardButton(
                    "𝐃ɪsᴀʙʟᴇ",
                    callback_data=f"AUTOPLAY_DISABLE|{chat_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    f"𝐀ᴜᴛᴏ 𝐏ʟᴀʏ : {status}",
                    callback_data="AUTOPLAY_STATUS"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑 𝐂ʟᴏsᴇ",
                    callback_data="AUTOPLAY_CLOSE"
                )
            ]
        ]
    )

    return caption, buttons


@app.on_message(
    filters.command(["autoplay"])
    & filters.group
    & ~BANNED_USERS
)
@AdminRightsCheck
async def autoplay_mode(client, message: Message, _, chat_id):
    # Check if the user passed 'enable' or 'disable' arguments with the command
    if len(message.command) > 1:
        action = message.command[1].lower()
        
        if action == "enable":
            await add_autoplay_group(chat_id)
            return await message.reply_text("> **✅ 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ ʜᴀs ʙᴇᴇɴ ᴇɴᴀʙʟᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ!**")
            
        elif action == "disable":
            await remove_autoplay_group(chat_id)
            return await message.reply_text("> **❌ 𝐀ᴜᴛᴏ 𝐏ʟᴀʏ ʜᴀs ʙᴇᴇɴ ᴅɪsᴀʙʟᴇᴅ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ!**")
            
        else:
            return await message.reply_text("> **⚠️ 𝐈ɴᴠᴀʟɪᴅ ᴄᴏᴍᴍᴀɴᴅ! 𝐔sᴇ :** `/autoplay enable` **or** `/autoplay disable`")

    # If only /autoplay is sent, display the panel
    enabled = await is_autoplay_group(chat_id)
    caption, buttons = get_panel(chat_id, enabled)

    await message.reply_photo(
        photo=PHOTO_URL,
        caption=caption,
        reply_markup=buttons,
    )


@app.on_callback_query(filters.regex("^AUTOPLAY_ENABLE") & ~BANNED_USERS)
async def autoplay_enable(_, query: CallbackQuery):
    chat_id = int(query.data.split("|")[1])

    member = await app.get_chat_member(chat_id, query.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await query.answer("❌ You must be an admin to change this setting!", show_alert=True)

    await add_autoplay_group(chat_id)
    caption, buttons = get_panel(chat_id, True)

    try:
        await query.message.edit_caption(
            caption=caption,
            reply_markup=buttons,
        )
    except MessageNotModified:
        pass

    await query.answer("Auto Play Enabled ✅")


@app.on_callback_query(filters.regex("^AUTOPLAY_DISABLE") & ~BANNED_USERS)
async def autoplay_disable(_, query: CallbackQuery):
    chat_id = int(query.data.split("|")[1])

    member = await app.get_chat_member(chat_id, query.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await query.answer("❌ You must be an admin to change this setting!", show_alert=True)

    await remove_autoplay_group(chat_id)
    caption, buttons = get_panel(chat_id, False)

    try:
        await query.message.edit_caption(
            caption=caption,
            reply_markup=buttons,
        )
    except MessageNotModified:
        pass

    await query.answer("Auto Play Disabled ❌")


@app.on_callback_query(filters.regex("^AUTOPLAY_STATUS"))
async def autoplay_status(_, query: CallbackQuery):
    await query.answer(
        "Auto Play Status Panel",
        show_alert=False,
    )


@app.on_callback_query(filters.regex("^AUTOPLAY_CLOSE") & ~BANNED_USERS)
async def autoplay_close(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    member = await app.get_chat_member(chat_id, query.from_user.id)
    
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await query.answer("❌ Only Admins can close this panel!", show_alert=True)
        
    await query.message.delete()
