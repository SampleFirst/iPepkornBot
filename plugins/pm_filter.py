# Standard Library Imports
import asyncio
import datetime
import logging
import math
import random
import re
import ast
import shutil
import psutil
import time

# Third-Party Library Imports
from pytz import timezone
from pyrogram import Client, filters, enums, types
from pyrogram.errors import FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto

# Database Imports
from database.connections_mdb import (
    active_connection,
    all_connections,
    delete_connection,
    if_active,
    make_active,
    make_inactive,
)
from database.ia_filterdb import Media, get_file_details, get_search_results, get_bad_files
from database.filters_mdb import del_all, find_filter, get_filters
from database.gfilters_mdb import find_gfilter, get_gfilters
from database.users_chats_db import db

# Custom Configuration Imports
from info import (
    ADMINS,
    AUTH_CHANNEL,
    FILE_CHANNEL,
    AUTH_USERS,
    CUSTOM_FILE_CAPTION,
    NOR_IMG,
    AUTH_GROUPS,
    P_TTI_SHOW_OFF,
    IMDB,
    SINGLE_BUTTON,
    SPELL_CHECK_REPLY,
    IMDB_TEMPLATE,
    SPELL_IMG,
    MSG_ALRT,
    FILE_FORWARD,
    MAIN_CHANNEL,
    LOG_CHANNEL,
    PICS,
    SUPPORT_CHAT_ID,
)

# Custom Script and Utility Imports
from Script import script
from utils import (
    get_size,
    is_subscribed,
    get_poster,
    search_gagala,
    temp,
    get_settings,
    save_group_settings,
    get_shortlink,
    get_time,
    humanbytes,
)

# Set the logging level
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}
# Define a variable to store the rules status
rules_on = False 


@Client.on_message(filters.command('autofilter') & filters.user(ADMINS))
async def toggle_autofilter(client, message):
    chat_id = message.chat.id
    current_mode = FILTER_MODE.get(chat_id, False)
    
    # Create inline keyboard with toggle buttons
    keyboard = [
        [
            InlineKeyboardButton("On" if current_mode else "Off", callback_data="toggle_filter"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.reply("Toggle Auto Filter:", reply_markup=reply_markup)

@Client.on_callback_query(filters.regex(r'^toggle_filter$'))
async def toggle_filter_callback(client, query):
    chat_id = query.message.chat.id
    current_mode = FILTER_MODE.get(chat_id, False)
    
    # Toggle the filter mode
    FILTER_MODE[chat_id] = not current_mode
    
    # Update the message text and inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("On" if not current_mode else "Off", callback_data="toggle_filter"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(f"Auto Filter is {'On' if not current_mode else 'Off'}", reply_markup=reply_markup)


@Client.on_message(filters.command("rules") & filters.group)
async def toggle_rules(client, message):
    global rules_on  # Access the global rules_on variable

    if rules_on:
        rules_on = False
        button_text = "Group rules are now OFF."
    else:
        rules_on = True
        button_text = "Group rules are now ON."

    # Create toggle buttons
    buttons = [
        [
            InlineKeyboardButton(button_text, callback_data="toggle_rules"),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    await message.reply_text("You've toggled the group rules.", reply_markup=keyboard)

@Client.on_callback_query(filters.regex(r'^toggle_rules'))
async def toggle_rules_callback(client, callback_query):
    global rules_on
    # Toggle the rules state
    rules_on = not rules_on
    if rules_on:
        button_text = "Group rules are now ON."
    else:
        button_text = "Group rules are now OFF."

    # Edit the original message with the updated button text
    await callback_query.edit_message_text(button_text)


@Client.on_message((filters.group) & filters.text & filters.incoming)
async def give_filter(client, message):
    group_id = message.chat.id
    name = message.text

    settings = await get_settings(group_id)

    if rules_on:  # Check if rules are enabled
        violations = []
        if re.search(r'http://|https://', name):
            violations.append("rule 1: Don't post messages with links.")
        if re.search(r'@\w+', name):
            violations.append("rule 2: Don't mention usernames.")
        if re.search(r'\b(join|bio)\b', name, flags=re.IGNORECASE):
            violations.append("rule 3: Don't use banned words (e.g., 'join' or 'bio').")

        if violations:
            violation_message = "\n".join(violations)
            reply = await message.reply_text(f"Sorry, {message.from_user.mention}, you violated the following rules:\n\n{violation_message}")
            
            # Delete the original violated message
            await message.delete()

            # Log the violation in LOG_CHANNEL
            group_name = message.chat.title  # Get the group name
            user_name = message.from_user.first_name  # Get the user's first name
            log_message = f"#Violation\nUser {user_name} violated rules in group {group_name}:\n{violation_message}\n\nViolated Message:\n{name}"
            await client.send_message(
                chat_id=LOG_CHANNEL,
                text=log_message
            )
            
            # Auto-delete the reply after 10 seconds
            await asyncio.sleep(10)
            await reply.delete()
        else:
            await global_filters(client, message)
            keywords = await get_filters(group_id)
            for keyword in reversed(sorted(keywords, key=len)):
                pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
                if re.search(pattern, name, flags=re.IGNORECASE):
                    reply_text, btn, alert, fileid = await find_filter(group_id, keyword)
                    if reply_text:
                        reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")
                    try:
                        if fileid == "None":
                            if btn == "[]":
                                await message.reply_text(reply_text, disable_web_page_preview=True)
                            else:
                                button = eval(btn)
                                await message.reply_text(
                                    reply_text,
                                    disable_web_page_preview=True,
                                    reply_markup=InlineKeyboardMarkup(button)
                                )
                        elif btn == "[]":
                            await message.reply_cached_media(
                                fileid,
                                caption=reply_text or ""
                            )
                        else:
                            button = eval(btn)
                            await message.reply_cached_media(
                                fileid,
                                caption=reply_text or "",
                                reply_markup=InlineKeyboardMarkup(button)
                            )
                    except Exception as e:
                        print(e)
                    break
            else:
                if FILTER_MODE.get(str(message.chat.id)) == "False":
                    return
                else:
                    await auto_filter(client, message)
                    
            if settings['auto_delete']:
                await asyncio.sleep(600)
                await message.delete()
    else:
        await global_filters(client, message)
        keywords = await get_filters(group_id)
        for keyword in reversed(sorted(keywords, key=len)):
            pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
            if re.search(pattern, name, flags=re.IGNORECASE):
                reply_text, btn, alert, fileid = await find_filter(group_id, keyword)
                if reply_text:
                    reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await message.reply_text(reply_text, disable_web_page_preview=True)
                        else:
                            button = eval(btn)
                            await message.reply_text(
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button)
                            )
                    elif btn == "[]":
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or ""
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button)
                        )
                except Exception as e:
                    print(e)
                break
        else:
            if FILTER_MODE.get(str(message.chat.id)) == "False":
                return
            else:
                await auto_filter(client, message)
                
        if settings['auto_delete']:
            await asyncio.sleep(600)
            await message.delete()
            
                
@Client.on_message(filters.private & filters.text & filters.incoming)
async def pm_text(bot, message):
    content = message.text
    user = message.from_user.first_name
    user_id = message.from_user.id

    # Set the timezone to India
    india_timezone = timezone('Asia/Kolkata')
    now = datetime.datetime.now(india_timezone)

    # Get the current time of day and date
    current_hour = now.hour
    time_suffix = "AM" if current_hour < 12 else "PM"
    formatted_time = now.strftime('%I:%M %p').lstrip('0')

    # Get the current date in Day-Month Name-Year format
    formatted_date = now.strftime('%d %B %Y')

    if 5 <= current_hour < 12:
        greeting = "Good morning ☀️"
    elif 12 <= current_hour < 18:
        greeting = "Good afternoon 🌤️"
    elif 18 <= current_hour < 22:
        greeting = "Good evening 🌇"
    else:
        greeting = "Good night 🌙"

    if content.startswith("/") or content.startswith("#"):
        return  # Ignore commands and hashtags

    # Get the total users count (implement this function)
    total_users = await db.total_users_count()
    
    if user_id in ADMINS:
        reply_text = f"{greeting} {user}!\n\nNice to meet you, you are an admin! Have a nice day.🌟\nTotal Users: {total_users}"
        
        # Send the reply message with buttons
        reply_message = await message.reply_text(
            text=reply_text,
            quote=True
        )

        # Send the log message to the specified channel with a button to show user info
        buttons = [
            [
                InlineKeyboardButton("User info", callback_data=f'user_info_{user_id}')
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
    
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=f"#PM_MSG\n\nUser: {user}\nID: {user_id}\n\nMessage: {content}\n\nDate: {formatted_date}\nTime: {formatted_time}\nTotal Users: {total_users}\n\n#iPepkorn_Bot\n#pm_iPepkorn_Bot",
            reply_markup=keyboard,
        )
    else:
        reply_text = f"{greeting} {user}!\n\nThanks For Choosing Us 🎉...\n\nJoin Our **𝙿𝚄𝙱𝙻𝙸𝙲 𝙶𝚁𝙾𝚄𝙿** For Sending Movie Names in Group Bot Reply Movies\n\nIf You Want Private Search Movies, Join Our **𝙿𝙼 𝚂𝙴𝙰𝚁𝙲𝙷** Bot to Send Movie Names. Bot Will Reply with Movies\n\nIf Any Bot Is Down, Check the Alternatives in **𝙼𝙾𝚁𝙴 𝙱𝙾𝚃𝚂** Official Channel"
    
        # Create buttons for the reply message
        buttons = [
            [
                InlineKeyboardButton("𝙿𝚄𝙱𝙻𝙸𝙲 𝙶𝚁𝙾𝚄𝙿", url="https://t.me/MoviesHubBotGroup")
            ],
            [
                InlineKeyboardButton("𝙼𝙾𝚁𝙴 𝙱𝙾𝚃𝚂", url="https://t.me/iPepkornBots/8")
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
    
        # Send the reply message with buttons
        reply_message = await message.reply_text(
            text=reply_text,
            reply_markup=keyboard,
            quote=True
        )
        
        # Schedule a task to delete the reply_message after 30 seconds (adjust as needed)
        await asyncio.sleep(300)
        await message.delete()
        await reply_message.delete()
    
        # Send the log message to the specified channel with a button to show user info
        log_buttons = [
            [
                InlineKeyboardButton("User info", callback_data=f'user_info_{user_id}')
            ]
        ]
        log_keyboard = InlineKeyboardMarkup(log_buttons)
    
        await bot.send_message(
            chat_id=LOG_CHANNEL,
            text=f"#PM_MSG\n\nUser: {user}\nID: {user_id}\n\nMessage: {content}\n\nDate: {formatted_date}\nTime: {formatted_time}\nTotal Users: {total_users}\n\n#iPepkorn_Bot\n#pm_iPepkorn_Bot",
            reply_markup=log_keyboard,
        )

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name),show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name),show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    settings = await get_settings(query.message.chat.id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(query.message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    if ENABLE_SHORTLINK == True:
        if settings['button']:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"[{get_size(file.file_size)}] {file.file_name}", url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}", url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        url=await get_shortlink(query.message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
    else:
        if settings['button']:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'files#{file.file_id}'
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}", callback_data=f'files#{file.file_id}'
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        callback_data=f'files_#{file.file_id}',
                    ),
                ]
                for file in files
        ]
    btn.insert(0, 
        [
            InlineKeyboardButton(f' ♀️ {search} ♀️ ', 'qinfo')
        ]
    )
    btn.insert(1, 
         [
             InlineKeyboardButton(f'ɪɴꜰᴏ', 'reqinfo'),
             InlineKeyboardButton(f'ᴍᴏᴠɪᴇ', 'minfo'),
             InlineKeyboardButton(f'sᴇʀɪᴇs', 'sinfo'),
             InlineKeyboardButton(f'ᴛɪᴘs', 'tinfo')
         ]
    )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"𝐏𝐀𝐆𝐄 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"{math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton("⌫ 𝐁𝐀𝐂𝐊", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(f"𝐏𝐀𝐆𝐄 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()

# spellcheck error fixing
@Client.on_callback_query(filters.regex(r"^spol"))
async def advantage_spoll_choker(bot, query):
    _, user, movie_ = query.data.split('#')
    movies = SPELL_CHECK.get(query.message.reply_to_message.id)
    if not movies:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if int(user) != 0 and query.from_user.id != int(user):
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name),show_alert=True)
    if movie_ == "close_spellcheck":
        return await query.message.delete()
    movie = movies[(int(movie_))]
    await query.answer(script.TOP_ALRT_MSG)
    k = await manual_filters(bot, query.message, text=movie)
    if k == False:
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            k = (movie, files, offset, total_results)
            await auto_filter(bot, query, k)
        else:
            reqstr1 = query.from_user.id if query.from_user else 0
            reqstr = await bot.get_users(reqstr1)
            await bot.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, movie)))
            k = await query.message.edit(script.MVE_NT_FND)
            await asyncio.sleep(10)
            await k.delete()


@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer(MSG_ALRT)
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer(MSG_ALRT)

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer(MSG_ALRT)

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)
    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer(script.ALRT_TXT.format(query.from_user.first_name),show_alert=True)
    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "CONNECT"
            cb = "connectcb"
        else:
            stat = "DISCONNECT"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("DELETE", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("BACK", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"Group Name : **{title}**\nGroup ID : `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer(MSG_ALRT)
    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"Connected to **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer(MSG_ALRT)
    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"Disconnected from **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer(MSG_ALRT)
    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer(MSG_ALRT)
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    elif "gfilteralert" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_gfilter('gfilters', keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)
    if query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        clicked = query.from_user.id #fetching the ID of the user who clicked the button
        try:
            typed = query.message.reply_to_message.from_user.id #fetching user ID of the user who sent the movie request
        except:
            typed = clicked #if failed, uses the clicked user's ID as requested user ID
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            elif settings['botpm']:
                if clicked == typed:
                    await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                    return
                else:
                    await query.answer(f"Hᴇʏ {query.from_user.first_name}, Tʜɪs Is Nᴏᴛ Yᴏᴜʀ Mᴏᴠɪᴇ Rᴇǫᴜᴇsᴛ. Rᴇǫᴜᴇsᴛ Yᴏᴜʀ's !", show_alert=True)
            else:
                if clicked == typed:
                    file_send=await client.send_cached_media(
                        chat_id=FILE_CHANNEL,
                        file_id=file_id,
                        caption=script.CHANNEL_CAP.format(query.from_user.mention, title, query.message.chat.title),
                        protect_content=True if ident == "filep" else False,
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton("🔥 ᴄʜᴀɴɴᴇʟ 🔥", url=(MAIN_CHANNEL))
                                ]
                            ]
                        )
                    )
                    Joel_tgx = await query.message.reply_text(
                        script.FILE_MSG.format(query.from_user.mention, title, size),
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(
                            [
                             [
                              InlineKeyboardButton('📥 𝖣𝗈𝗐𝗇𝗅𝗈𝖺𝖽 𝖫𝗂𝗇𝗄 📥 ', url = file_send.link)
                           ],[
                              InlineKeyboardButton("⚠️ 𝖢𝖺𝗇'𝗍 𝖠𝖼𝖼𝖾𝗌𝗌 ❓ 𝖢𝗅𝗂𝖼𝗄 𝖧𝖾𝗋𝖾 ⚠️", url=(FILE_FORWARD))
                             ]
                            ]
                        )
                    )
                    await query.answer('Files Sent')
    
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await Joel_tgx.delete()
                        await file_send.delete()
    
                else:
                    await query.answer(f"Hey {query.from_user.first_name}, This is not your movie request. Request yours!", show_alert=True)
                    await query.answer('Check PM, I have sent files in PM', show_alert=True)
        except UserIsBlocked:
            await query.answer('User blocked the bot!', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
    elif query.data.startswith("checksub"):
        if AUTH_CHANNEL and not await is_subscribed(client, query):
            await query.answer("𝑰 𝑳𝒊𝒌𝒆 𝒀𝒐𝒖𝒓 𝑺𝒎𝒂𝒓𝒕𝒏𝒆𝒔𝒔, 𝑩𝒖𝒕 𝑫𝒐𝒏'𝒕 𝑩𝒆 𝑶𝒗𝒆𝒓𝒔𝒎𝒂𝒓𝒕 😒\n@𝒄𝒊𝒏𝒆𝒎𝒂𝒍𝒂.𝒄𝒐𝒎", show_alert=True)
            return
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{title}"
        await query.answer()
        await client.send_cached_media(
            chat_id=query.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if ident == 'checksubp' else False
        )
    elif query.data == "predvd":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Deleting PreDVDs... Please wait...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'predvd',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('PreDVD File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Successfully deleted {deleted} PreDVD files.</b>")

    elif query.data == "camrip":
        k = await client.send_message(chat_id=query.message.chat.id, text="<b>Deleting CamRips... Please wait...</b>")
        files, next_offset, total = await get_bad_files(
                                                  'camrip',
                                                  offset=0)
        deleted = 0
        for file in files:
            file_ids = file.file_id
            result = await Media.collection.delete_one({
                '_id': file_ids,
            })
            if result.deleted_count:
                logger.info('CamRip File Found ! Successfully deleted from database.')
            deleted+=1
        deleted = str(deleted)
        await k.edit_text(text=f"<b>Successfully deleted {deleted} CamRip files.</b>")

    elif query.data == "pages":
        await query.answer()

    elif query.data == "reqinfo":
        await query.answer("⚠ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ⚠\n\nᴀꜰᴛᴇʀ 10 ᴍɪɴᴜᴛᴇꜱ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴡɪʟʟ ʙᴇ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇᴅ\n\nɪꜰ ʏᴏᴜ ᴅᴏ ɴᴏᴛ ꜱᴇᴇ ᴛʜᴇ ʀᴇǫᴜᴇsᴛᴇᴅ ᴍᴏᴠɪᴇ / sᴇʀɪᴇs ꜰɪʟᴇ, ʟᴏᴏᴋ ᴀᴛ ᴛʜᴇ ɴᴇxᴛ ᴘᴀɢᴇ\n\n❣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴄɪɴᴇᴍᴀʟᴀ.ᴄᴏᴍ", show_alert=True)

    elif query.data == "minfo":
        await query.answer("⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\nᴍᴏᴠɪᴇ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀᴍᴀᴛ\n⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀꜱᴛᴇ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : ᴀᴠᴀᴛᴀʀ: ᴛʜᴇ ᴡᴀʏ ᴏғ ᴡᴀᴛᴇʀ\n\n🚯 ᴅᴏɴᴛ ᴜꜱᴇ ➠ ':(!,./)\n\n©️ ᴄɪɴᴇᴍᴀʟᴀ.ᴄᴏᴍ", show_alert=True)

    elif query.data == "sinfo":
        await query.answer("⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\nꜱᴇʀɪᴇꜱ ʀᴇǫᴜᴇꜱᴛ ꜰᴏʀᴍᴀᴛ\n⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯⋯\n\nɢᴏ ᴛᴏ ɢᴏᴏɢʟᴇ ➠ ᴛʏᴘᴇ ᴍᴏᴠɪᴇ ɴᴀᴍᴇ ➠ ᴄᴏᴘʏ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ➠ ᴘᴀꜱᴛᴇ ᴛʜɪꜱ ɢʀᴏᴜᴘ\n\nᴇxᴀᴍᴘʟᴇ : ᴍᴏɴᴇʏ ʜᴇɪsᴛ S01E01\n\n🚯 ᴅᴏɴᴛ ᴜꜱᴇ ➠ ':(!,./)\n\n©️ ᴄɪɴᴇᴍᴀʟᴀ.ᴄᴏᴍ", show_alert=True)      

    elif query.data == "tinfo":
        await query.answer("▣ ᴛɪᴘs ▣\n\n★ ᴛʏᴘᴇ ᴄᴏʀʀᴇᴄᴛ sᴘᴇʟʟɪɴɢ (ɢᴏᴏɢʟᴇ)\n\n★ ɪғ ʏᴏᴜ ɴᴏᴛ ɢᴇᴛ ʏᴏᴜʀ ғɪʟᴇ ɪɴ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ᴛʜᴇɴ ᴛʜᴇ ɴᴇxᴛ sᴛᴇᴘ ɪs ᴄʟɪᴄᴋ ɴᴇxᴛ ʙᴜᴛᴛᴏɴ.\n\n★ ᴄᴏɴᴛɪɴᴜᴇ ᴛʜɪs ᴍᴇᴛʜᴏᴅ ᴛᴏ ɢᴇᴛᴛɪɴɢ ʏᴏᴜ ғɪʟᴇ\n\n❣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ ᴄɪɴᴇᴍᴀʟᴀ. ᴄᴏᴍ", show_alert=True)

    elif query.data == "surprise":
        btn = [
            [
                InlineKeyboardButton('surprise', callback_data='start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(btn)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.SURPRISE_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "start":
        buttons = [
            [
                InlineKeyboardButton('➕️ Add Me To Your Group ➕️', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
            ],
            [
                InlineKeyboardButton('🔍 Search', switch_inline_query_current_chat=''),
                InlineKeyboardButton("📢 Channel", url="https://t.me/+R9B3Qma6ZkE5ZWI1"),
            ],
            [
                InlineKeyboardButton('ℹ️ Help', callback_data='help'),
                InlineKeyboardButton('📚 About', callback_data='about')
            ],
            [
                InlineKeyboardButton('Back to Start', callback_data='surprise')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.START_TXT.format(query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is Start Page...")

    elif query.data == "help":
        buttons = [
            [
                InlineKeyboardButton('⚙️ Admin Panel ⚙️', callback_data='admin'),
            ],
            [
                InlineKeyboardButton('Filters', callback_data='filters'),
                InlineKeyboardButton('Connection', callback_data='conn'),
            ],
            [
                InlineKeyboardButton('Extra Mods', callback_data='mods'),
                InlineKeyboardButton('Group Manager', callback_data='gpmanager'),
            ],
            [
                InlineKeyboardButton('Support', url='https://t.me/+JnZ3tuWbYqlmNWU9'),
                InlineKeyboardButton('Home', callback_data='start'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is the Help Page...")

    elif query.data == "about":
        buttons = [
            [
                InlineKeyboardButton('Status', callback_data='stats'),
                InlineKeyboardButton('Source', callback_data='source'),
            ],
            [
                InlineKeyboardButton('Bots', callback_data='bots'),
                InlineKeyboardButton('Home', callback_data='start')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is the About Page...")

    elif query.data == "admin":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='help')
            ]
        ]
        if query.from_user.id not in ADMINS:
            return await query.answer("Sorry This Menu Only For My Admins...", show_alert=True)
        await query.message.edit("Processing...\nWait For 15 Sec...")
        total, used, free = shutil.disk_usage(".")
        stats = script.SERVER_STATS.format(get_time(time.time() - client.uptime), psutil.cpu_percent(), psutil.virtual_memory().percent, humanbytes(total), humanbytes(used), psutil.disk_usage('/').percent, humanbytes(free))
        stats_pic = await make_carbon(stats, True)
        await query.edit_message_media(
            InputMediaPhoto(stats_pic, script.ADMIN_TXT, enums.ParseMode.HTML),
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif query.data == "filters":
        buttons = [
            [
                InlineKeyboardButton('Auto Filter', callback_data='autofilter'),
                InlineKeyboardButton('Manual Filter', callback_data='manuelfilter'),
            ],
            [
                InlineKeyboardButton('Global Filter', callback_data='globalfilter'),
                InlineKeyboardButton('Back', callback_data='help'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.FILTER_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is the Filters Page...")

    elif query.data == "conn":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "mods":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='help'),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is the Extra Modes Page...")

    elif query.data == "gpmanager":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        await query.message.edit_text(
            text=script.GROUPMANAGER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        await query.answer("This is the Group Manager Page...")
        
    elif query.data == "stats":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='about'),
                InlineKeyboardButton('Refreash', callback_data='rfrsh')
            ]
        ]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "rfrsh":
        await query.answer("Fetching Database...")
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='about'),
                InlineKeyboardButton('Refreash', callback_data='rfrsh')
            ]
        ]
        await client.edit_message_media(
            query.message.chat.id,
            query.message.id,
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(buttons)
        total = await Media.count_documents()
        users = await db.total_users_count()
        chats = await db.total_chat_count()
        monsize = await db.get_db_size()
        free = 536870912 - monsize
        monsize = get_size(monsize)
        free = get_size(free)
        await query.message.edit_text(
            text=script.STATUS_TXT.format(total, users, chats, monsize, free),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "source":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='about')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.SOURCE_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "bots":
        btn = [
            [
                InlineKeyboardButton("Channel", url="https://t.me/+9Z1w2KOebaliYzdl"),
                InlineKeyboardButton("Back", callback_data="about")
            ]
        ]
        await client.edit_message_media(
            query.message.chat.id, 
            query.message.id, 
            InputMediaPhoto(random.choice(PICS))
        )
        reply_markup = InlineKeyboardMarkup(btn)
        await query.message.edit_text(
            text=script.MORE_BOTS,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "autofilter":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='filters')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        
    elif query.data == "manuelfilter":
        buttons = [
            [
                InlineKeyboardButton('Buttons', callback_data='button'),
                InlineKeyboardButton('Back', callback_data='filters')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "globalfilter":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='filters')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.GLOBALFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data == "button":
        buttons = [
            [
                InlineKeyboardButton('Back', callback_data='help')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("Your Active Connection Has Been Changed. Go To /settings.")
            return await query.answer(MSG_ALRT)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await get_settings(grpid)
        try:
            if settings['auto_delete']:
                settings = await get_settings(grp_id)
        except KeyError:
            await save_group_settings(grp_id, 'auto_delete', True)
            settings = await get_settings(grp_id)

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('Filter Button',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Single' if settings["button"] else 'Double',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Redirect To', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('Bot PM' if settings["botpm"] else 'Channel',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('File Secure',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["file_secure"] else '❌ No',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('IMDB', callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["imdb"] else '❌ No',
                                         callback_data=f'setgs#imdb#{settings["imdb"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Spell Check',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["spell_check"] else '❌ No',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Welcome', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ Yes' if settings["welcome"] else '❌ No',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('Auto Delete',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}'),
                    InlineKeyboardButton('10 Mins' if settings["auto_delete"] else 'OFF',
                                         callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ShortLink',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ ON' if settings["is_shortlink"] else '❌ OFF',
                                         callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{str(grp_id)}')
                ]
                
            ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
            await query.answer(MSG_ALRT)


async def auto_filter(client, msg, spoll=False):
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    if not spoll:
        message = msg
        settings = await get_settings(message.chat.id)
        if message.text.startswith("/"): return  # ignore commands
        if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
            return
        if len(message.text) < 100:
            search = message.text
            files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
            if not files:
                if settings["spell_check"]:
                    return await advantage_spell_chok(client, msg)
                else:
                    await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, search)))
                    return
        else:
            return
    else:
        message = msg.message.reply_to_message  # msg will be callback query
        search, files, offset, total_results = spoll
        settings = await get_settings(message.chat.id)
    if 'is_shortlink' in settings.keys():
        ENABLE_SHORTLINK = settings['is_shortlink']
    else:
        await save_group_settings(message.chat.id, 'is_shortlink', False)
        ENABLE_SHORTLINK = False
    pre = 'filep' if settings['file_secure'] else 'file'
    if ENABLE_SHORTLINK == True:
        if settings["button"]:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"[{get_size(file.file_size)}] {file.file_name}", url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}",
                        url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        url=await get_shortlink(message.chat.id, f"https://telegram.me/{temp.U_NAME}?start=files_{file.file_id}")
                    ),
                ]
                for file in files
            ]
    else:
        if settings["button"]:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"[{get_size(file.file_size)}] {file.file_name}", callback_data=f'{pre}#{file.file_id}'
                    ),
                ]
                for file in files
            ]
        else:
            btn = [
                [
                    InlineKeyboardButton(
                        text=f"{file.file_name}",
                        callback_data=f'{pre}#{file.file_id}',
                    ),
                    InlineKeyboardButton(
                        text=f"{get_size(file.file_size)}",
                        callback_data=f'{pre}#{file.file_id}',
                    ),
                ]
                for file in files
            ]
    btn.insert(0, 
        [
            InlineKeyboardButton(f' ♀️ {search} ♀️ ', 'qinfo')
        ]
    )
    btn.insert(1, 
         [
             InlineKeyboardButton(f'ɪɴꜰᴏ', 'reqinfo'),
             InlineKeyboardButton(f'ᴍᴏᴠɪᴇ', 'minfo'),
             InlineKeyboardButton(f'sᴇʀɪᴇs', 'sinfo'),
             InlineKeyboardButton(f'ᴛɪᴘs', 'tinfo')
         ]
    )

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"𝐏𝐀𝐆𝐄 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="𝐍𝐄𝐗𝐓 ⌦", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="𝐍𝐎 𝐌𝐎𝐑𝐄 𝐏𝐀𝐆𝐄𝐒 𝐀𝐕𝐀𝐈𝐋𝐀𝐁𝐋𝐄", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b><i>𝙃𝙚𝙧𝙚 𝙞𝙨 𝙬𝙝𝙖𝙩 𝙞𝙨 𝙛𝙤𝙪𝙣𝙙 𝙮𝙤𝙪𝙧 𝙦𝙪𝙚𝙧𝙮:\n {search}\n👤𝙍𝙚𝙦𝙪𝙚𝙨𝙩𝙚𝙙 𝘽𝙮 : {message.from_user.mention}\n👥𝙂𝙧𝙤𝙪𝙥 : {message.chat.title}</i></b>"
    if imdb and imdb.get('poster'):
        try:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴏʀ ᴍᴀᴋᴇ ᴀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴀᴅᴅ ᴍᴇ ᴀs ᴀᴅᴍɪɴ ᴛᴏ ɢᴇᴛ ᴍᴏᴠɪᴇ ғɪʟᴇs. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await hehe.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await hehe.delete()
                        await message.delete()
        except (MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty):
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴏʀ ᴍᴀᴋᴇ ᴀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴀᴅᴅ ᴍᴇ ᴀs ᴀᴅᴍɪɴ ᴛᴏ ɢᴇᴛ ᴍᴏᴠɪᴇ ғɪʟᴇs. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                pic = imdb.get('poster')
                poster = pic.replace('.jpg', "._V1_UX360.jpg")
                hmm = await message.reply_photo(photo=poster, caption=cap[:1024], reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await hmm.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await hmm.delete()
                        await message.delete()
        except Exception as e:
            if message.chat.id == SUPPORT_CHAT_ID:
                await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴏʀ ᴍᴀᴋᴇ ᴀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴀᴅᴅ ᴍᴇ ᴀs ᴀᴅᴍɪɴ ᴛᴏ ɢᴇᴛ ᴍᴏᴠɪᴇ ғɪʟᴇs. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
            else:
                logger.exception(e)
                fek = await message.reply_photo(photo=NOR_IMG, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                try:
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await fek.delete()
                        await message.delete()
                except KeyError:
                    grpid = await active_connection(str(message.from_user.id))
                    await save_group_settings(grpid, 'auto_delete', True)
                    settings = await get_settings(message.chat.id)
                    if settings['auto_delete']:
                        await asyncio.sleep(600)
                        await fek.delete()
                        await message.delete()
    else:
        if message.chat.id == SUPPORT_CHAT_ID:
            await message.reply_text(f"<b>Hᴇʏ {message.from_user.mention}, {str(total_results)} ʀᴇsᴜʟᴛs ᴀʀᴇ ғᴏᴜɴᴅ ɪɴ ᴍʏ ᴅᴀᴛᴀʙᴀsᴇ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {search}. Kɪɴᴅʟʏ ᴜsᴇ ɪɴʟɪɴᴇ sᴇᴀʀᴄʜ ᴏʀ ᴍᴀᴋᴇ ᴀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴀᴅᴅ ᴍᴇ ᴀs ᴀᴅᴍɪɴ ᴛᴏ ɢᴇᴛ ᴍᴏᴠɪᴇ ғɪʟᴇs. Tʜɪs ɪs ᴀ sᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ sᴏ ᴛʜᴀᴛ ʏᴏᴜ ᴄᴀɴ'ᴛ ɢᴇᴛ ғɪʟᴇs ғʀᴏᴍ ʜᴇʀᴇ...</b>")
        else:
            fuk = await message.reply_photo(photo=NOR_IMG, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            try:
                if settings['auto_delete']:
                    await asyncio.sleep(600)
                    await fuk.delete()
                    await message.delete()
            except KeyError:
                grpid = await active_connection(str(message.from_user.id))
                await save_group_settings(grpid, 'auto_delete', True)
                settings = await get_settings(message.chat.id)
                if settings['auto_delete']:
                    await asyncio.sleep(600)
                    await fuk.delete()
                    await message.delete()
    
    if spoll:
        await msg.message.delete()


async def advantage_spell_chok(client, msg):
    mv_id = msg.id
    mv_rqst = msg.text
    reqstr1 = msg.from_user.id if msg.from_user else 0
    reqstr = await client.get_users(reqstr1)
    settings = await get_settings(msg.chat.id)
    query = re.sub(
        r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)",
        "", msg.text, flags=re.IGNORECASE)  # plis contribute some common words
    RQST = query.strip()
    query = query.strip() + " movie"
    try:
        movies = await get_poster(mv_rqst, bulk=True)
    except Exception as e:
        logger.exception(e)
        await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply(script.I_CUDNT.format(reqstr.mention))
        await asyncio.sleep(8)
        await k.delete()
        return
    movielist = []
    if not movies:
        reqst_gle = mv_rqst.replace(" ", "+")
        button = [[
                   InlineKeyboardButton("Gᴏᴏɢʟᴇ", url=f"https://www.google.com/search?q={reqst_gle}")
        ]]
        await client.send_message(chat_id=LOG_CHANNEL, text=(script.NORSLTS.format(reqstr.id, reqstr.mention, mv_rqst)))
        k = await msg.reply_photo(
            photo=SPELL_IMG, 
            caption=script.I_CUDNT.format(mv_rqst),
            reply_markup=InlineKeyboardMarkup(button)
        )
        await asyncio.sleep(30)
        await k.delete()
        return
    movielist += [movie.get('title') for movie in movies]
    movielist += [f"{movie.get('title')} {movie.get('year')}" for movie in movies]
    SPELL_CHECK[mv_id] = movielist
    btn = [
        [
            InlineKeyboardButton(
                text=movie_name.strip(),
                callback_data=f"spol#{reqstr1}#{k}",
            )
        ]
        for k, movie_name in enumerate(movielist)
    ]
    btn.append([InlineKeyboardButton(text="Close", callback_data=f'spol#{reqstr1}#close_spellcheck')])
    spell_check_del = await msg.reply_photo(
        photo=(SPELL_IMG),
        caption=(script.CUDNT_FND.format(reqstr.mention)),
        reply_markup=InlineKeyboardMarkup(btn)
        )

    try:
        if settings['auto_delete']:
            await asyncio.sleep(600)
            await spell_check_del.delete()
    except KeyError:
            grpid = await active_connection(str(message.from_user.id))
            await save_group_settings(grpid, 'auto_delete', True)
            settings = await get_settings(message.chat.id)
            if settings['auto_delete']:
                await asyncio.sleep(600)
                await spell_check_del.delete()

async def manual_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            elsa = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await elsa.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await elsa.delete()

                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                protect_content=True if settings["file_secure"] else False,
                                reply_to_message_id=reply_id
                            )
                            try:
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_ffilter', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_ffilter']:
                                    await auto_filter(client, message)
                            try:
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await hmm.delete()
                            except KeyError:
                                grpid = await active_connection(str(message.from_user.id))
                                await save_group_settings(grpid, 'auto_delete', True)
                                settings = await get_settings(message.chat.id)
                                if settings['auto_delete']:
                                    await asyncio.sleep(600)
                                    await hmm.delete()

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            protect_content=True if settings["file_secure"] else False,
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await oto.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await oto.delete()

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                        try:
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_ffilter', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_ffilter']:
                                await auto_filter(client, message)
                        try:
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await dlt.delete()
                        except KeyError:
                            grpid = await active_connection(str(message.from_user.id))
                            await save_group_settings(grpid, 'auto_delete', True)
                            settings = await get_settings(message.chat.id)
                            if settings['auto_delete']:
                                await asyncio.sleep(600)
                                await dlt.delete()

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False

async def global_filters(client, message, text=False):
    settings = await get_settings(message.chat.id)
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_gfilters('gfilters')
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_gfilter('gfilters', keyword)

            if reply_text:
                reply_text = reply_text.replace("\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            joelkb = await client.send_message(
                                group_id, 
                                reply_text, 
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id
                            )
                            
                        else:
                            button = eval(btn)
                            hmm = await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )

                    elif btn == "[]":
                        oto = await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )

                    else:
                        button = eval(btn)
                        dlt = await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )                       

                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
