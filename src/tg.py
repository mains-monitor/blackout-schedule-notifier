import os
from telegram import Bot
import asyncio

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def post_message_with_image(chat_id, image_path, message_text):
    bot = Bot(token=BOT_TOKEN)
    async def _send_msg():
        await bot.send_photo(chat_id=chat_id, photo=open(image_path, 'rb'), caption=message_text)

    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_send_msg())
    loop.close()
