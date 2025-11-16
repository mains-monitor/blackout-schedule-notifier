import os
import json
from zoneinfo import ZoneInfo
from telegram import Bot
import asyncio
from datetime import datetime
from config import config

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
    
    # Path to telegram metadata file
    meta_file_path = os.path.join(config.out_dir, 'telegram-meta.json')
    
    async def _send_msg():
        # Check if it's quiet hours in Kyiv (22:00 - 08:00)
        kyiv_time = datetime.now(KYIV_TZ)
        is_quiet_hours = kyiv_time.hour >= 22 or kyiv_time.hour < 8
        
        if send_with_image:
            message = await bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)
        else:
            message = await bot.send_message(chat_id=chat_id, text=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)
        
        # Read existing metadata or create new dictionary
        if os.path.exists(meta_file_path):
            with open(meta_file_path, 'r') as f:
                meta_data = json.load(f)
        else:
            meta_data = {}
        
        # Update with new message ID
        meta_data[str(chat_id)] = str(message.message_id)
        
        # Save updated metadata
        with open(meta_file_path, 'w') as f:
            json.dump(meta_data, f, indent=2)

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_msg())
    loop.close()
