from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import asyncio
import datetime
import pytz
from info import ADMINS, LOG_CHANNEL

# Initialize a list to keep track of the current digit values
current_digits = [0, 0, 0, 0]

# Dictionary to keep track of active tasks
active_tasks = {}

# Add AM/PM toggle button state
am_pm_toggle = 0  # 0 for AM, 1 for PM

# Function to send log message
async def send_log_message(chat_id, new_hour, new_minute):
    while True:
        now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
        current_hour = now.hour if am_pm_toggle == 0 else (now.hour + 12) % 24
        if current_hour == new_hour and now.minute == new_minute:
            message_text = f"Reporting time has arrived for user {chat_id}."
            await bot.send_message(LOG_CHANNEL, message_text)
        await asyncio.sleep(60)  # Check every minute

# Add command handler and callback handler
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
        await message.reply(status_text, reply_markup=keyboard, quote=True)
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
        await message.reply(status_text, reply_markup=keyboard, quote=True)

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
        global am_pm_toggle
        # Create toggle buttons for each digit and AM/PM toggle
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(str(current_digits[0]), callback_data="set_digit_0"),
                    InlineKeyboardButton(str(current_digits[1]), callback_data="set_digit_1"),
                    InlineKeyboardButton(str(current_digits[2]), callback_data="set_digit_2"),
                    InlineKeyboardButton(str(current_digits[3]), callback_data="set_digit_3"),
                ],
                [
                    InlineKeyboardButton("AM" if am_pm_toggle == 0 else "PM", callback_data="toggle_am_pm"),
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
        current_digit = current_digits[digit_index]

        # Cycle the current digit value from 0 to 9
        new_digit = (current_digit + 1) % 10
        current_digits[digit_index] = new_digit

        # Update the button text with the new digit value
        keyboard = query.message.reply_markup.inline_keyboard
        keyboard[0][digit_index].text = str(new_digit)
        await query.message.edit_reply_markup(InlineKeyboardMarkup(inline_keyboard=keyboard))
    
    elif data == "toggle_am_pm":
        am_pm_toggle = 1 - am_pm_toggle  # Toggle between AM and PM
        keyboard = query.message.reply_markup.inline_keyboard
        keyboard[1][0].text = "AM" if am_pm_toggle == 0 else "PM"
        await query.message.edit_reply_markup(InlineKeyboardMarkup(inline_keyboard=keyboard))
        
    elif data == "confirm_time":
        new_hour = current_digits[1] * 10 + current_digits[0]
        new_minute = current_digits[3] * 10 + current_digits[2]
        
        if 0 <= new_hour < 24 and 0 <= new_minute < 60:
            if chat_id in active_tasks:
                active_tasks[chat_id].cancel()
                del active_tasks[chat_id]
            active_tasks[chat_id] = asyncio.create_task(send_log_message(chat_id, new_hour, new_minute))
            am_pm_text = "AM" if am_pm_toggle == 0 else "PM"
            status_text = f"Reporting time changed. Reporting started at {new_hour:02d}:{new_minute:02d} {am_pm_text}."
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
        await asyncio.sleep(5)
        await query.message.delete()
        
