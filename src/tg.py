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

def _save_message_metadata(chat_id, schedule_date_time, message_id):
    # Path to telegram metadata file
    meta_file_path = os.path.join(config.out_dir, 'telegram-meta-v2.json')
    schedule_date_str = schedule_date_time.strftime("%d.%m.%Y")
    # Read existing metadata or create new dictionary
    if os.path.exists(meta_file_path):
        with open(meta_file_path, 'r') as f:
            meta_data = json.load(f)
    else:
        meta_data = {}
    
    if str(chat_id) not in meta_data:
        meta_data[str(chat_id)] = {}
    
    # Update with new message ID
    meta_data[str(chat_id)][schedule_date_str] = str(message_id)

    if len(meta_data[str(chat_id)].keys()) > 3:
        # Keep only the latest 3 entries
        sorted_dates = sorted(meta_data[str(chat_id)].keys(), key=lambda date: datetime.strptime(date, "%d.%m.%Y"))
        for old_date in sorted_dates[:-3]:
            del meta_data[str(chat_id)][old_date]
    
    # Save updated metadata
    with open(meta_file_path, 'w') as f:
        json.dump(meta_data, f, indent=2)

def _get_last_message_id(chat_id, schedule_date_time):
    meta_file_path = os.path.join(config.out_dir, 'telegram-meta-v2.json')
    schedule_date_str = schedule_date_time.strftime("%d.%m.%Y")
    
    if not os.path.exists(meta_file_path):
        return None
    
    with open(meta_file_path, 'r') as f:
        meta_data = json.load(f)
    
    return meta_data.get(str(chat_id), {}).get(schedule_date_str, None)

def remove_old_message(chat_id, schedule_date_time):
    bot = Bot(token=BOT_TOKEN)
    last_message_id = _get_last_message_id(chat_id, schedule_date_time)
    if last_message_id:
        async def _delete_msg():
            try:
                await bot.delete_message(chat_id=chat_id, message_id=int(last_message_id))
            except Exception as e:
                print(f"Failed to delete message {last_message_id} for chat {chat_id}: {e}")

        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_delete_msg())
        loop.close()

def post_message_with_image(chat_id, image_path, message_text, schedule_date_time):
    """Send a message with an image. If image_path doesn't exist or is not an image, sends text only."""
    bot = Bot(token=BOT_TOKEN)
    
    # Check if image exists and is actually an image file
    send_with_image = (
        image_path and 
        os.path.exists(image_path) and 
        os.path.isfile(image_path) and
        not image_path.endswith('.json')
    )

    remove_old_message(chat_id, schedule_date_time)
    
    async def _send_msg():
        # Check if it's quiet hours in Kyiv (22:00 - 08:00)
        kyiv_time = datetime.now(KYIV_TZ)
        is_quiet_hours = kyiv_time.hour >= 22 or kyiv_time.hour < 8
        
        if send_with_image:
            message = await bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)
        else:
            message = await bot.send_message(chat_id=chat_id, text=message_text, parse_mode='MarkdownV2', disable_notification=is_quiet_hours)

        _save_message_metadata(chat_id, schedule_date_time, message.message_id)

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_msg())
    loop.close()
