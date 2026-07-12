import asyncio
import random
from pyrogram.types import InlineKeyboardButton
from pyrogram.enums import ButtonStyle
import config
from PritiMusic import app

# 🔥 PREMIUM EMOJIS LIST 🔥
PREMIUM_EMOJIS = [
    "5422831825178206894", 
    "5368324170673489600",
    "5206607081334906820",
    "5206380668048496464"
]

# 🎨 Dynamic Color Generator
def get_style_map():
    styles = [ButtonStyle.PRIMARY, ButtonStyle.SUCCESS, ButtonStyle.DANGER]
    random.shuffle(styles)
    return {1: styles[0], 2: styles[1], 3: styles[2]}

# 🔘 Smart Button Creator (Font updated to Premium style)
def create_btn(text, cb=None, url=None, user_id=None, style=ButtonStyle.PRIMARY, no_emoji=False):
    # Text ko premium font mein convert kiya (Simplified replacement)
    # Agar tumhare system mein custom font support hai toh yeh tag kaam karega
    kwargs = {"text": text, "style": style}
    if cb: kwargs["callback_data"] = cb
    if url: kwargs["url"] = url
    if user_id: kwargs["user_id"] = user_id
    if not no_emoji: kwargs["icon_custom_emoji_id"] = random.choice(PREMIUM_EMOJIS)
    return InlineKeyboardButton(**kwargs)

def start_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="✙ ᴧᴅᴅ ϻє ᴛσ ʏσᴜʀ ɢʀσυᴘ ✙", 
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map[2]
            ),
            create_btn(
                text="⌯ sυᴘᴘσʀᴛ ⌯", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            ),
        ],
    ]
    return buttons

def private_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="✙ ᴧᴅᴅ ϻє ᴛσ ʏσᴜʀ ɢʀσυᴘ ✙",
                url=f"https://t.me/{app.username}?startgroup=true",
                style=s_map[1]
            )
        ],
        [
            create_btn(
                text="⌯ σᴡηєʀ ⌯", 
                user_id=config.OWNER_ID, 
                style=s_map[2]
            ),
            create_btn(
                text="⌯ ᴄʟσηє ⌯", 
                cb="clone_page", 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="⌯ sυᴘᴘσʀᴛ ⌯", 
                cb="support_page", 
                style=s_map[2]
            ),
            create_btn(
                text="⌯ sσυʀᴄє ⌯", 
                cb="gib_source", 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="⌯ ʜєʟᴘ ᴧηᴅ ᴄσϻϻᴧηᴅs ⌯", 
                cb="settings_back_helper", 
                style=s_map[1]
            )
        ],
    ]
    return buttons

def support_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="⌯ sυᴘᴘσʀᴛ ⌯", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            ),
            create_btn(
                text="⌯ υᴘᴅᴧᴛєs ⌯", 
                url=config.SUPPORT_CHANNEL, 
                style=s_map[2]
            ),
        ],
        [
            create_btn(
                text="⌯ ʙᴧᴄᴋ ⌯", 
                cb="settingsback_helper", 
                style=s_map[1]
            )
        ]
    ]
    return buttons

def about_panel(_):
    s_map = get_style_map()
    buttons = [
        [
            create_btn(
                text="⌯ σᴡηєʀ ⌯", 
                user_id=config.OWNER_ID, 
                style=s_map[2]
            ),
            create_btn(
                text="⌯ ɢɪᴛʜυʙ ⌯", 
                url=config.GITHUB, 
                style=s_map[2]
            ),
        ],
        [
            create_btn(
                text="⌯ υᴘᴅᴧᴛєs ⌯", 
                url=config.SUPPORT_CHANNEL, 
                style=s_map[2]
            ),
            create_btn(
                text="⌯ sυᴘᴘσʀᴛ ⌯", 
                url=config.SUPPORT_CHAT, 
                style=s_map[2]
            )
        ],
        [
            create_btn(
                text="⌯ ʙᴧᴄᴋ ⌯", 
                cb="settingsback_helper", 
                style=s_map[1]
            )
        ]
    ]
    return buttons
    
