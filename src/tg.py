import os
from zoneinfo import ZoneInfo
from telegram import Bot
import asyncio
from datetime import datetime

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
# Europe/Kyiv timezone
KYIV_TZ = ZoneInfo("Europe/Kyiv")

def post_message_with_image(chat_id, image_path, message_text):
    """Send a message with an image. If image_path doesn't exist or is not an image, sends text only."""
    bot = Bot(token=BOT_TOKEN)
    
    # Check if image exists and is actually an image file
    send_with_image = (
        image_path and 
        os.path.exists(image_path) and 
        os.path.isfile(image_path) and
        not image_path.endswith('.json')
    )
    
    async def _send_msg():
        # Check if it's quiet hours in Kyiv (22:00 - 08:00)
        kyiv_time = datetime.now(KYIV_TZ)
        is_quiet_hours = kyiv_time.hour >= 22 or kyiv_time.hour < 8
        
        if send_with_image:
            await bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)
        else:
            await bot.send_message(chat_id=chat_id, text=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_msg())
    loop.close()
