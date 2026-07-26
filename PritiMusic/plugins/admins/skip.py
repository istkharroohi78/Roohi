import random
from pyrogram import filters
from pyrogram.types import Message

import config
from PritiMusic import app
from PritiMusic.core.call import Lucky
from PritiMusic.misc import db
from PritiMusic.utils.database import get_loop
from PritiMusic.utils.decorators import AdminRightsCheck
from PritiMusic.utils.inline import close_markup
from PritiMusic.utils.stream.autoclear import auto_clean
from config import BANNED_USERS

@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"], prefixes=["/", "!"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    check = db.get(chat_id)
    if not check:
        return await message.reply_text(_["queue_2"])

    loop = await get_loop(chat_id)
    if loop != 0:
        return await message.reply_text(_["admin_8"])

    # Multi-skip logic
    if len(message.command) > 1:
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            count = len(check)
            if count > 2:
                count = int(count - 1)
                if 1 <= state <= count:
                    for x in range(state - 1):
                        try:
                            popped = check.pop(0)
                            if popped: await auto_clean(popped)
                        except: pass
                else:
                    return await message.reply_text(_["admin_11"].format(count))
            else:
                return await message.reply_text(_["admin_10"])
        else:
            return await message.reply_text(_["admin_11"].format(len(check)-1))

    try:
        # Pura lamba kachra hata kar seedha engine run kiya hai
        pytgcalls_client = Lucky.one
        if getattr(Lucky, "active_clients", None) and chat_id in Lucky.active_clients:
            val = Lucky.active_clients[chat_id]
            if isinstance(val, list) and val: pytgcalls_client = val[0]
            elif val and not isinstance(val, list): pytgcalls_client = val

        await message.reply_text(f"<blockquote>⏭️ <b>Sᴋɪᴘᴘᴇᴅ ʙʏ :</b> {message.from_user.mention}</blockquote>")
        await Lucky.change_stream(pytgcalls_client, chat_id)
    except Exception as e:
        await message.reply_text(f"❌ <b>Skip Error:</b> {e}")
