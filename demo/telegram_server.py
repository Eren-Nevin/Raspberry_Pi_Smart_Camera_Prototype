import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import re
from typing import Dict, List

from pyrogram import Client, filters
from pyrogram.types.messages_and_media.message import Message

from user_command_handler import handle_command

# THIS IS THE BOT TOKEN
token = '5346807516:AAFyn5Uij3Al2gtQ3mHZ1Yp8DrDzwNslP1E'
api_id = 19463946
api_hash = 'c57f3113a0f5e54d603f838725e9f754'

app = Client(
    'smart_kamera_bot',
    bot_token=token,
    api_id=api_id,
    api_hash=api_hash
)

# Important: Each handler is called in a new thread.

# TODO: Add Appropriate metadata especially to audio media (ID3, ...)

@app.on_message(filters.command(['start']))
async def start_handler(client: Client, message: Message):
    start_message =\
        'Hello To Smart Cam'
    await message.reply_text(start_message)


@app.on_message(filters.text)
async def message_handler(client: Client, message: Message):
    await handle_text_message(client, message)


async def handle_text_message(client: Client, message: Message):
    raw_query = message.text
    chat_id = message.chat.id
    print(f"Query: {raw_query}")
    await handle_command(raw_query, client, message)

app.run()
