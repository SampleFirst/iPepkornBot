from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPrivileges
from info import ADMINS

# Replace this with your actual group chat ID and channel ID
chat_channel_id = [-1001913586283, -1001835657274]
chat_group_id = 

# Define your command handler for adding admin in a channel
@Client.on_message(filters.command("addchanneladmin") & filters.private)
async def add_channel_admin(client, message):
    chat_id = chat_channel_id

    if message.from_user.id not in ADMINS:
        await message.reply("You must be an admin to use this command.")
        return

    if len(message.command) != 2:
        await message.reply("Usage: /addchanneladmin user_id")
        return

    user_id = int(message.command[1])

    try:
        await client.promote_chat_member(
            chat_id,
            user_id,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_invite_users=True,
                can_manage_chat=True,
                can_promote_members=True
            ),
        )

        await message.reply("User added as an admin in the channel with specified privileges.")
    except UserNotParticipant:
        await message.reply("The user must be a member of the channel to use this command.")
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")

# Define your command handler for adding admin in a group
@Client.on_message(filters.command("addgroupadmin") & filters.private)
async def add_group_admin(client, message):
    chat_id = chat_group_id

    if message.from_user.id not in ADMINS:
        await message.reply("You must be an admin to use this command.")
        return

    if len(message.command) != 2:
        await message.reply("Usage: /addgroupadmin user_id")
        return

    user_id = int(message.command[1])

    try:
        await client.promote_chat_member(
            chat_id,
            user_id,
            privileges=ChatPrivileges(
                can_change_info=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_invite_users=True,
                can_pin_messages=True,
                is_anonymous=True,
                can_manage_chat=True
            ),
        )

        await message.reply("User added as an admin in the group with specified privileges.")
    except UserNotParticipant:
        await message.reply("The user must be a member of the group to use this command.")
    except Exception as e:
        await message.reply(f"An error occurred: {str(e)}")
        
