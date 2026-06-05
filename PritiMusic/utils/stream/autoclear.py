import os
from config import autoclean
from PritiMusic import LOGGER

async def auto_clean(popped):
    try:
        if not popped:
            return
            
        rem = popped.get("file")
        if not rem:
            return

        # List se current song ko remove karo (Clone aur Main bot dono isi list ko use karte hain)
        try:
            autoclean.remove(rem)
        except ValueError:
            pass

        # Check karo ki kya koi aur chat (ya clone bot) same file ko play toh nahi kar raha
        count = autoclean.count(rem)
        if count == 0:
            # Agar file live_ ya index_ nahi hai, tabhi delete karo
            if "live_" not in rem and "index_" not in rem:
                if os.path.exists(rem):
                    try:
                        os.remove(rem)
                        LOGGER(__name__).info(f"🗑️ Auto-Cleaned temporary file: {rem}")
                    except Exception as e:
                        LOGGER(__name__).warning(f"⚠️ Failed to clean {rem}: {e}")
    except Exception as e:
        LOGGER(__name__).error(f"Auto-Clean Error: {e}")
