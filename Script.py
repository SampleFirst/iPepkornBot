class script(object):
    SURPRISE_TXT = """<b>Hello {},
My Name Is <a href=https://t.me/{}>{}</a>. I Can Provide Movies, Just Add Me To Your Group And Enjoy...</b>"""

    START_TXT = """<b>Hello {},
My Name Is <a href=https://t.me/{}>{}</a>. I Can Provide Movies, Just Add Me To Your Group And Enjoy...</b>"""

    HELP_TXT = """<b>Hey {}
Here Is The Help For My Commands.</b>"""

    ABOUT_TXT = """<b>✯ My Name: {}
✯ Creator: <a href=https://t.me/+PTh5LZg1rG9lNzA1>iPApkoRn BOTs</a>
✯ Library: Python
✯ Language: Python 3
✯ Database: MongoDB
✯ Bot Server: Koyeb
✯ Build Status: v2.0.1 [Alpha]</b>"""

    MORE_BOTS = """<b>⍟────[ More Bots ]────⍟

• My name: <a href="https://t.me/PremiumMHBot?start">PremiumMHBot</a> 🤖
• Bot Two: <a href="https://t.me/Movies_Hole_Robot?start">Movies Hole Bot</a> 🎥
• Bot Three: <a href="https://t.me/iPopkonBot?start">iPapkornBot</a> 🍿
• Bot Four: <a href="https://t.me/HDCinemasBot?start">HDCinemasBot</a> 🎬
• Bot Fifth: <a href="https://t.me/TrueDealsMasterBot?start">TrueDealsMasterBot</a> 💰</b>"""

    FILTER_TXT = """👋 Hey {}, 
These are my three types of filters..."""

    AUTOFILTER_TXT = """<b>AutoFilter Help</b>

<i>AutoFilter is a feature that allows you to automatically filter and save files from a channel to a group. You can use the following commands to control AutoFilter in your chat:</i>

• /autofilter on - Enable AutoFilter in your chat
• /autofilter off - Disable AutoFilter in your chat

<b>Other Commands:</b>
• /set_template - Set an IMDb Template for your group
• /get_template - Get the current IMDb Template for your group"""

    MANUELFILTER_TXT = """<b>ManuelFilters Help</b>

Filters enable users to set up automated replies for specific keywords, and the bot will respond whenever it detects these keywords in messages. Here are some important notes and commands:

Note:
1. This bot should have admin privileges.
2. Only admins can add filters to a chat.
3. Alert buttons have a limit of 64 characters.

Commands and Usage:
- /filter: Add a filter to the chat
- /filters: List all the filters in the chat
- /del: Delete a specific filter in the chat
- /delall: Delete all filters in the chat (Chat owner only)"""

    GLOBALFILTER_TXT = """<b>Global Filters Help</b>

<i>Global Filters allow users to set automated replies for specific keywords, and the bot will respond whenever it detects these keywords in messages. Please note that this module only works for my admins.</i>

<b>Commands and Usage:</b>
• /gfilter - Add Global Filters
• /gfilters - View a list of all Global Filters
• /delg - Delete a specific Global Filter
• /delallg - Delete all Global Filters

To control Global Filters in your group, use the command /g_filter followed by on/off."""

    BUTTON_TXT = """<b>Buttons Help</b>

<i>This bot supports both URL and Alert Inline buttons.</i>

<b>Notes:</b>
1. Telegram requires content with buttons, so content is mandatory.
2. This bot supports buttons with any Telegram media type.
3. Buttons should be properly parsed in Markdown format.

<b>URL Buttons:</b>
[Button Text](buttonurl:xxxxxxxxxxxx)

<b>Alert Buttons:</b>
[Button Text](buttonalert:This Is An Alert Message)"""

    CONNECTION_TXT = """<b>Connections Help</b>

<i>Used to connect the bot to PM for managing filters. It helps to avoid spamming in groups.</i>

<b>Note:</b>
• Only admins can add a connection.
• Send /connect to connect a particular chat to your PM

<b>Commands & Usage:</b>
• /connect - Connect a particular chat to your PM
• /disconnect - Disconnect from a chat
• /connections - List all your connections"""

    ADMIN_TXT = """<b>Admin Help</b>

<i>This module only works for my admins.</i>

<b>Commands & Usage:</b>
• /logs - Get the recent errors
• /delete - Delete a specific file from the DB
• /deleteall - Delete all files from DB
• /users - Get a list of my users and IDs
• /chats - Get a list of my chats and IDs
• /channel - Get a list of total connected channels
• /broadcast - Broadcast a message to all users
• /group_broadcast - Broadcast a message to all connected groups
• /leave - With chat ID, leave from a chat
• /disable - With chat ID, disable a chat
• /invite - With chat ID, get the invite link of any chat where the bot is admin
• /ban_user - With ID, ban a user
• /unban_user - With ID, unban a user
• /restart - Restart the bot
• /clear_junk - Clear all deleted accounts and blocked accounts in the database
• /clear_junk_group - Clear added or removed groups or deactivated groups on DB"""

    GROUPMANAGER_TXT = """<b>GroupManager Help</b>

<i>This is the help for your Group Management. This will work only for Group admins.</i>

<b>Commands & Usage:</b>
• /inkick - Command with required arguments, and I will kick members from the Group.
• /instatus - Check the current status of chat members in the Group.
• /dkick - Kick deleted accounts
• /ban - Ban a user from the Group
• /unban - Unban a banned user
• /tban - Temporarily ban a user
• /mute - Mute a user
• /unmute - Unmute a muted user
• /tmute - Use with a value to mute a user for a specific time, e.g., <code>/tmute 2h</code> to mute for 2 hours (values: m/h/d).
• /pin - Pin a message in your chat
• /unpin - Unpin a message in your chat
• /purge - Delete all messages from the replied-to message, or to the current message"""

    EXTRAMOD_TXT = """<b>ExtraModule Help</b>

<i>Just send any image to edit the image ✨</i>

<b>Commands & Usage:</b>
• /id - Get the ID of a specified user
• /info - Get information about a user
• /imdb - Get film information from IMDb source
• /paste [text] - Paste the given text on Paste
• /tts [text] - Convert text to speech
• /telegraph - Send me this command, reply with a picture or video under (5MB)
• /json - Reply with any message to get message info (useful for groups)
• /written - Reply with text to get a file (useful for coders)
• /carbon - Reply with text to get carbonated image
• /font [text] - To change your text fonts to fancy fonts
• /share - Reply with text to get text shareable link
• /song [name] - To search the song on YouTube
• /video [link] - To download the YouTube video"""    
    
    STATUS_TXT = """<b>★ Total Files: <code>{}</code>
★ Total Users: <code>{}</code>
★ Total Chats: <code>{}</code>
★ Used Storage: <code>{}</code> MIB
★ Free Storage: <code>{}</code> MIB</b>"""

    SOURCE_TXT = """<b>NOTE:</b>
This is not open-source project...

- <a href=https://t.me/+PTh5LZg1rG9lNzA1>iPAPKORN BOTS</a>"""

    LOG_TEXT_G = """#NewGroup 😎

Group: {a}
Group ID: <code>{b}</code>
Group UN: @{c}

Total Members: <code>{d}</code>
Total Groups: <code>{e}</code>
Today Groups: <code>{f}</code>

Date: <code>{g}</code>
Time: <code>{h}</code>

Added By: {i}
By {j}

#{k}
#Chats_{k}
"""
    
    LOG_TEXT_P = """NewUsers 😀
    
ID: <code>{a}</code>
Name: {b}
Username: @{c}

Total Users: {d}
Today Users: {e}

Date: <code>{f}</code>
Time: <code>{g}</code>

By {h}
#{i}
#Users_{i}
"""
    
    NEW_MEMBER = """#NewMember 😀

Group = {a}
Group ID = <code>{b}</code>
Group UN = @{c}
Total Member = <code>{d}</code>
Invite = {e}
           
Member = {f}
Member ID = <code>{g}</code>
Member UN = @{h}

Date = <code>{i}</code>
Time = <code>{j}</code>

#{k}
#NewMem_{k}
"""

    LEFT_MEMBER = """#LeftMember 😔

Group = {a}
Group ID = <code>{b}</code>
Group UN = @{c}
Total Member = <code>{d}</code>
Invite = {e}
           
Member = {f}
Member ID = <code>{g}</code>
Member UN = @{h}

Date = <code>{i}</code>
Time = <code>{j}</code>

#{k}
#LeftMem_{k}
"""

    REPORT_TXT = """#Daily_Report

Date = {a}
Time = {c}

Total
Total Users = <code>{d}</code>
Total Chats = <code>{e}</code>

Yesterday
{b} Users = <code>{f}</code>
{b} Chats = <code>{g}</code>

#{h}
#Report_{h}"""

    SERVER_STATS = """Server Stats:

Uptime: {}
CPU Usage: {}%
RAM Usage: {}%
Total Disk: {}
Used Disk: {} ({}%)
Free Disk: {}"""

    NORSLTS = """#NO_RESULT 
ID <b>: {}</b>
Name <b>: {}</b>
Message <b>: {}</b>
Date <b>: {}</b>
Time <b>: {}</b>
#iPepkorn_Bot
#No_iPepkorn_Bot"""

    FILE_MSG = """
<b>Hai 👋 {} </b>😍

<b>📫 Your File is Ready</b>

<b>📂 Fɪʟᴇ Nᴀᴍᴇ</b> : <code>{}</code>              

<b>⚙️ Fɪʟᴇ Sɪᴢᴇ</b> : <b>{}</b>
"""
    CHANNEL_CAP = """
<b>Hai 👋 {}</b> 😍

<code>{}</code>

<b>Dᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ᴛʜᴇ ғɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ғʀᴏᴍ ʜᴇʀᴇ ɪɴ 10 ᴍɪɴᴜᴛᴇs sᴏ ᴅᴏᴡɴʟᴏᴀᴅ ᴀғᴛᴇʀ ᴍᴏᴠɪɴɢ ғʀᴏᴍ ʜᴇʀᴇ ᴛᴏ sᴏᴍᴇᴡʜᴇʀᴇ ᴇʟsᴇ!</b>

<b>© Powered by {}</b>
"""

    IMDB_TEMPLATE_TXT = """
<b>🔖 ᴛɪᴛʟᴇ :<a href={url}>{title}</a>

🎭 ɢᴇɴʀᴇs : {genres}
🎖 ʀᴀᴛɪɴɢ : <a href={url}/ratings>{rating}</a> / 10 (ʙᴀsᴇᴅ ᴏɴ {votes} ᴜsᴇʀ ʀᴀᴛɪɴɢ.)
📆 ʏᴇᴀʀ : {release_date}
🗞 ʟᴀɴɢᴜᴀɢᴇ : {languages}
🌎 ᴄᴏᴜɴᴛʀʏ : {countries}

©{message.chat.title}</b>
"""

    CUSTOM_FILE_CAPTION = """<b>📂 Fɪʟᴇ ɴᴀᴍᴇ : {file_name}</b>"""

    MELCOW_ENG = """<b>Hello {} 😍, And Welcome To {} Group ❤️</b>"""

    ALRT_TXT = """This is not for you, sir."""

    OLD_ALRT_TXT = """You are using one of my old messages, please send the request again."""

    TOP_ALRT_MSG = """Checking file on my database... """

    MVE_NT_FND = """<b>This movie is not yet released or added to the database</b>"""

    I_CUDNT = """<b>Hello {} I couldn't find any movies in that name.

Movie request format:

➠ Go to Google
➠ Type movie name
➠ Copy correct name
➠ Paste this group

Example: Kantara 2022

🚯 Don't use ➠ ' : ( ! , . / )</b>"""

    I_CUD_NT = """<b>Hello {} I couldn't find anything related to that. Check your spelling.</b>"""

    CUDNT_FND = """<b>Hello {} I couldn't find anything related to that. Did you mean any one of these?</b>"""

    REPRT_MSG = """ Reported To Admin"""

    DISC_TXT = """ᴀʟʟ ᴛʜᴇ ꜰɪʟᴇꜱ ɪɴ ᴛʜɪꜱ ʙᴏᴛ ᴀʀᴇ ꜰʀᴇᴇʟʏ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ ᴛʜᴇ ɪɴᴛᴇʀɴᴇᴛ ᴏʀ ᴘᴏꜱᴛᴇᴅ ʙʏ ꜱᴏᴍᴇʙᴏᴅʏ ᴇʟꜱᴇ.ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ɪɴᴅᴇxɪɴɢ ꜰɪʟᴇꜱ ᴡʜɪᴄʜ ᴀʀᴇ ᴀʟʀᴇᴀᴅʏ ᴜᴘʟᴏᴀᴅᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ ꜰᴏʀ ᴇᴀꜱʏ ᴏꜰ ꜱᴇᴀʀᴄʜɪɴɢ, ᴡᴇ ʀᴇꜱᴘᴇᴄᴛ ᴀʟʟ ᴛʜᴇ ᴄᴏᴘʏʀɪɢʜᴛ ʟᴀᴡꜱ ᴀɴᴅ ᴡᴏʀᴋꜱ ɪɴ ᴄᴏᴍᴘʟɪᴀɴᴄᴇ ᴡɪᴛʜ ᴅᴍᴄᴀ ᴀɴᴅ ᴇᴜᴄᴅ. ɪꜰ ᴀɴʏᴛʜɪɴɢ ɪꜱ ᴀɢᴀɪɴꜱᴛ ʟᴀᴡ ᴘʟᴇᴀꜱᴇ ᴄᴏɴᴛᴀᴄᴛ ᴜꜱ ꜱᴏ ᴛʜᴀᴛ ɪᴛ ᴄᴀɴ ʙᴇ ʀᴇᴍᴏᴠᴇᴅ ᴀꜱᴀᴘ"""

    RESTART_TXT = """#Restarted

🔄 Bot Restarted!
📅 Date: <code>{a}</code>
⏰ Time: <code>{b}</code>
🌐 Timezone: <code>Asia/Kolkata</code>

#{c}
#Restart_{c}"""

