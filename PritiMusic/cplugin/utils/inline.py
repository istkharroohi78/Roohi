from pyrogram.types import InlineKeyboardMarkup
from button import styled_button, ButtonStyle

# --- OPTION 1: Static ---
buttons = InlineKeyboardMarkup(
    [
        [
            styled_button(text="▷", callback_data="resume_cb", style=ButtonStyle.SUCCESS),
            styled_button(text="II", callback_data="pause_cb", style=ButtonStyle.DANGER),
            styled_button(text="‣‣I", callback_data="skip_cb", style=ButtonStyle.PRIMARY),
            styled_button(text="▢", callback_data="end_cb", style=ButtonStyle.DANGER),
        ],
        [
            styled_button(text="ᴀᴅᴅ ᴍᴇ", url="https://t.me/SizzuMusicBot?startgroup=true", style=ButtonStyle.SUCCESS)
        ],
    ]
)

close_key = InlineKeyboardMarkup(
    [
        [
            styled_button(text="✯ CLOSE ✯", callback_data="close", style=ButtonStyle.DANGER)
        ]
    ]
)

# --- OPTION 2: Dynamic (RECOMMENDED) ---
def stream_markup(chat_id):
    return InlineKeyboardMarkup(
        [
            [
                styled_button(text="▷", callback_data=f"ADMIN Resume|{chat_id}", style=ButtonStyle.SUCCESS),
                styled_button(text="II", callback_data=f"ADMIN Pause|{chat_id}", style=ButtonStyle.DANGER),
                styled_button(text="‣‣I", callback_data=f"ADMIN Skip|{chat_id}", style=ButtonStyle.PRIMARY),
                styled_button(text="▢", callback_data=f"ADMIN Stop|{chat_id}", style=ButtonStyle.DANGER),
            ],
            [
                styled_button(text="<- 20s", callback_data=f"ADMIN SeekBack|{chat_id}", style=ButtonStyle.PRIMARY),
                styled_button(text="20s + ->", callback_data=f"ADMIN SeekForward|{chat_id}", style=ButtonStyle.PRIMARY),
            ],
            [
                styled_button(text="ᴀᴅᴅ ᴍᴇ", url="https://t.me/SizzuMusicBot?startgroup=true", style=ButtonStyle.SUCCESS),
                styled_button(text="✯ CLOSE ✯", callback_data="close", style=ButtonStyle.DANGER)
            ]
        ]
    )
    
