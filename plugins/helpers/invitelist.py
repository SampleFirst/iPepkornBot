from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors.exceptions import ChatAdminRequired, MessageTooLong
from database.users_chats_db import db
from info import ADMINS



# Define a constant for results per page
RESULTS_PER_PAGE = 10

# Helper function to paginate the results
def paginate_results(page_num):
    start_index = (page_num - 1) * RESULTS_PER_PAGE
    end_index = start_index + RESULTS_PER_PAGE
    return chat_invite_links[start_index:end_index]

@Client.on_message(filters.command('listallchats') & filters.private & filters.user(ADMINS))
async def list_all_chats_invites(bot: Client, message: Message):
    global chat_invite_links

    raju = await message.reply('Getting List Of Chat Invite Links')
    
    # Fetch chats using await
    chats_cursor = await db.get_all_chats()
    
    # Convert the cursor to a list of dictionaries
    chats = [chat async for chat in chats_cursor]

    chat_invite_links = []

    for chat in chats:
        try:
            link = await bot.create_chat_invite_link(chat['id'])
            chat_invite_links.append({
                'title': chat['title'],
                'invite_link': link.invite_link
            })
        except ChatAdminRequired:
            chat_invite_links.append({
                'title': chat['title'],
                'error': 'Admin privileges required to generate invite link'
            })
        except Exception as e:
            chat_invite_links.append({
                'title': chat['title'],
                'error': str(e)
            })

    page_num = 1

    while page_num <= ((len(chat_invite_links) - 1) // RESULTS_PER_PAGE) + 1:
        paginated_results = paginate_results(page_num)
        out = "List of Chat Invite Links:\n\n"

        for result in paginated_results:
            if 'error' in result:
                out += f"**Title:** `{result['title']}`\n**Error:** {result['error']}\n\n"
            else:
                out += f"**Title:** `{result['title']}`\n**Invite Link:** {result['invite_link']}\n\n"

        if page_num > 1:
            out += f"Page {page_num} of {((len(chat_invite_links) - 1) // RESULTS_PER_PAGE) + 1}\n\n"

        try:
            keyboard = []
            if len(chat_invite_links) > page_num * RESULTS_PER_PAGE:
                keyboard.append([InlineKeyboardButton("Next Page", callback_data=f"next_{page_num}")])
            if page_num > 1:
                keyboard.append([InlineKeyboardButton("Previous Page", callback_data=f"prev_{page_num}")])

            markup = InlineKeyboardMarkup(keyboard)
            await raju.edit_text(out, reply_markup=markup)
            
            page_num += 1
        except MessageTooLong:
            await raju.edit_text("The output is too long. Please download the file.")

@Client.on_callback_query(filters.regex(r'^(prev|next)_(\d+)$'))
async def handle_callback_query(bot: Client, query: CallbackQuery):
    global chat_invite_links

    # Extract the page number from the callback data
    callback_data = query.data.split("_")
    action = callback_data[0]
    page_num = int(callback_data[1])

    if action == "next":
        page_num += 1
    elif action == "prev":
        page_num -= 1

    paginated_results = paginate_results(page_num)
    out = "List of Chat Invite Links:\n\n"

    for result in paginated_results:
        if 'error' in result:
            out += f"**Title:** `{result['title']}`\n**Error:** {result['error']}\n\n"
        else:
            out += f"**Title:** `{result['title']}`\n**Invite Link:** {result['invite_link']}\n\n"

    if page_num > 1:
        out += f"Page {page_num} of {((len(chat_invite_links) - 1) // RESULTS_PER_PAGE) + 1}\n\n"

    try:
        keyboard = []
        if len(chat_invite_links) > page_num * RESULTS_PER_PAGE:
            keyboard.append([InlineKeyboardButton("Next Page", callback_data=f"next_{page_num}")])
        if page_num > 1:
            keyboard.append([InlineKeyboardButton("Previous Page", callback_data=f"prev_{page_num}")])

        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(out, reply_markup=markup)
    except MessageTooLong:
        await query.edit_message_text("The output is too long. Please download the file.")
