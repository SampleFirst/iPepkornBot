# Standard Library Imports
import asyncio
import datetime
from typing import Union, Optional, AsyncGenerator
from datetime import date, datetime 

# Third-Party Library Imports
import logging
import logging.config
import pytz
from aiohttp import web
from pyrogram import Client, __version__, filters, types
from pyrogram.raw.all import layer

# Custom Module Imports
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import (
    SESSION,
    API_ID,
    API_HASH,
    BOT_TOKEN,
    LOG_STR,
    LOG_CHANNEL,
    PORT,
    UPTIME,
)
from utils import temp
from plugins import web_server
from Script import script

# Get logging configurations
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)


class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=150,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats
        await super().start()
        await Media.ensure_indexes()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        self.uptime = UPTIME
        logging.info(f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}.")
        logging.info(LOG_STR)
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        await self.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(a=today, b=time, c=temp.U_NAME))
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        # Add a job to send a message at 11:59 PM daily
        await self.send_report_message()
    
    async def send_report_message(self):
        while True:
            tz = pytz.timezone('Asia/Kolkata')
            today = date.today()
            now = datetime.now(tz)
            formatted_date_1 = now.strftime("%d-%B-%Y")
            formatted_date_2 = today.strftime("%d %b")
            time = now.strftime("%H:%M:%S %p")

            total_users = await db.total_users_count()
            total_chats = await db.total_chat_count()
            today_users = await db.daily_users_count(today) + 1
            today_chats = await db.daily_chats_count(today) + 1

            if now.hour == 23 and now.minute == 59:
                await self.send_message(
                    chat_id=LOG_CHANNEL, 
                    text=script.REPORT_TXT.format(
                        a=formatted_date_1,
                        b=formatted_date_2,
                        c=time,
                        d=total_users, 
                        e=total_chats,
                        f=today_users, 
                        g=today_chats,
                        h=temp.U_NAME
                    )
                )
                # Sleep for 1 minute to avoid sending multiple messages
                await asyncio.sleep(60)
            else:
                # Sleep for 1 minute and check again
                await asyncio.sleep(60)
                
    async def stop(self, *args):
        await super().stop()
        logging.info("Bot stopped. Bye.")
    
    async def iter_messages(
        self,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0,
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """Iterate through a chat sequentially.
        This convenience method does the same as repeatedly calling :meth:`~pyrogram.Client.get_messages` in a loop, thus saving
        you from the hassle of setting up boilerplate code. It is useful for getting the whole chat messages with a
        single call.
        Parameters:
            chat_id (``int`` | ``str``):
                Unique identifier (int) or username (str) of the target chat.
                For your personal cloud (Saved Messages) you can simply use "me" or "self".
                For a contact that exists in your Telegram address book you can use his phone number (str).
                
            limit (``int``):
                Identifier of the last message to be returned.
                
            offset (``int``, *optional*):
                Identifier of the first message to be returned.
                Defaults to 0.
        Returns:
            ``Generator``: A generator yielding :obj:`~pyrogram.types.Message` objects.
        Example:
            .. code-block:: python
                for message in app.iter_messages("pyrogram", 1, 15000):
                    print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1

app = Bot()
app.run()
