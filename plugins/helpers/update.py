from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import ADMINS

# Define a command handler to trigger the bot
@Client.on_message(filters.command(["updates"]) & filters.user(ADMINS))
def show_updates_command(client, message):
    # Create a formatted update message
    update_message = (
        "👀 **Movies Hub Bot V2.0**\n\n"
        "What's New:\n"
        "● Latest Version Is 2.0.0 ✔️\n"
        "● Added Admin Status In Image\n"
        "● Changed Theme\n"
        "● Fixed Minor & Major Errors & Bugs\n"
        "● Try To Fix More Issues\n"
        "● Update Auto Delete Message\n"
        "● Added Rules For Group\n\n"
        "Official Update Date: 17/9/23 08:00PM\n\n"
        "Join And Enjoy..."
    )

    # Create an inline keyboard with a button
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Movies Hub Bot V2.0", url="https://t.me/Movies_Hole_Robot?start"),
            ],
            [
                InlineKeyboardButton("Add Me To Your Group", url="http://t.me/Movies_Hole_Robot?startgroup=true")
            ]
        ]
    )

    # Send the update message with the inline keyboard
    message.reply_text(update_message, reply_markup=keyboard)
