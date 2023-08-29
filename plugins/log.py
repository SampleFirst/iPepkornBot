from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import datetime
import pytz
from info import ADMINS, LOG_CHANNEL

# Convert UTC time to Indian Timezone
def get_indian_time(hour=0, minute=0):
    utc_now = datetime.datetime.now(pytz.utc)
    indian_timezone = pytz.timezone("Asia/Kolkata")
    return utc_now.replace(hour=hour, minute=minute).astimezone(indian_timezone)

# Dictionary to keep track of active tasks
active_tasks = {}

# Modify the send_log_message function
async def send_log_message(chat_id, hour, minute):
    while True:
        indian_now = get_indian_time(hour, minute)
        message = f"This is a daily log message. Current Indian Time: {indian_now.strftime('%Y-%m-%d %H:%M:%S')}"
        await bot.send_message(LOG_CHANNEL, message)
        await bot.send_message(chat_id, message)  # Send the message to ADMINS
        await asyncio.sleep(60)  # Sleep for 1 minute
        
        # Check if the task needs to be stopped
        if chat_id not in active_tasks:
            break


@Client.on_message(filters.command('Report') & filters.user(ADMINS))
async def report_send(_, message):
    chat_id = message.chat.id
    keyboard = None

    if chat_id in active_tasks:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Stop Reporting", callback_data="stop_log"),
                    InlineKeyboardButton("Change Time", callback_data="change_time"),
                ],
                [
                    InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                ]
            ]
        )
        status_text = "You have an active reporting task."
        await message.reply(status_text, reply_markup=keyboard)
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Start Reporting", callback_data="start_log"),
                    InlineKeyboardButton("Change Time", callback_data="change_time"),
                ],
                [
                    InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                ]
            ]
        )
        status_text = "You currently don't have an active reporting task."
        await message.reply(status_text, reply_markup=keyboard)


# Modify the callback_handler function
@Client.on_callback_query(filters.user(ADMINS))
async def callback_handler(_, query: CallbackQuery):
    chat_id = query.message.chat.id
    data = query.data

    if data == "start_log":
        if chat_id not in active_tasks:
            active_tasks[chat_id] = asyncio.create_task(send_log_message(chat_id, 0, 0))
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Stop Reporting", callback_data="stop_log"),
                        InlineKeyboardButton("Change Time", callback_data="change_time"),
                    ],
                    [
                        InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                    ]
                ]
            )
            await query.message.edit_text("Reporting started.", reply_markup=keyboard)
    
    elif data == "stop_log":
        if chat_id in active_tasks:
            active_tasks[chat_id].cancel()
            del active_tasks[chat_id]
            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Start Reporting", callback_data="start_log"),
                        InlineKeyboardButton("Change Time", callback_data="change_time"),
                    ],
                    [
                        InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                    ]
                ]
            )
            await query.message.edit_text("Reporting stopped.", reply_markup=keyboard)
    
    elif data == "change_time":
        # Create 4 toggle buttons for each digit
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("0", callback_data="set_digit_0"),
                    InlineKeyboardButton("0", callback_data="set_digit_1"),
                    InlineKeyboardButton("0", callback_data="set_digit_2"),
                    InlineKeyboardButton("0", callback_data="set_digit_3"),
                ],
                [
                    InlineKeyboardButton("Set Time", callback_data="confirm_time"),
                    InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                ]
            ]
        )
        await query.message.edit_text("Please select the new time in HH:MM format.", reply_markup=keyboard)
    
    elif data.startswith("set_digit_"):
        digit_index = int(data.split("_")[2])
        keyboard = query.message.reply_markup.inline_keyboard
        current_digit = int(keyboard[0][digit_index].text)
        
        # Toggle the current digit between 0 and 1
        new_digit = 1 - current_digit
        keyboard[0][digit_index].text = str(new_digit)
        await query.message.edit_reply_markup(InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    elif data == "confirm_time":
        keyboard = query.message.reply_markup.inline_keyboard
        new_hour = int(keyboard[0][1].text + keyboard[0][0].text)
        new_minute = int(keyboard[0][3].text + keyboard[0][2].text)
        
        if 0 <= new_hour < 24 and 0 <= new_minute < 60:
            if chat_id in active_tasks:
                active_tasks[chat_id].cancel()
                del active_tasks[chat_id]
            active_tasks[chat_id] = asyncio.create_task(send_log_message(chat_id, new_hour, new_minute))
            status_text = f"Reporting time changed. Reporting started at {new_hour:02d}:{new_minute:02d}."
        else:
            status_text = "Invalid time format. Please enter a valid time."
        
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Stop Reporting", callback_data="stop_log"),
                    InlineKeyboardButton("Change Time", callback_data="change_time"),
                ],
                [
                    InlineKeyboardButton("Cancel", callback_data="cancel_log"),
                ]
            ]
        )
        await query.message.edit_text(status_text, reply_markup=keyboard)
    
    elif data == "cancel_log":
        await query.message.edit_text("Action canceled.")
