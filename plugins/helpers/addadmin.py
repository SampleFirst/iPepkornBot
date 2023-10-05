from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatPermissions
from info import ADMINS


# Define your command handler for adding admin in a group
@Client.on_message(filters.command("addgroupadmin") & filters.group)
async def add_group_admin(client, message):
    
    if message.from_user.id not in ADMINS:
        await message.reply("You must be an admin to use this command.")
        return

    if len(message.command) != 2:
        await message.reply("Usage: /addgroupadmin user_id")
        return

    user_id = int(message.command[1])

    for chat_id in chat_group_id:
        try:
            chat_info = await client.get_chat(chat_id)
            chat_type = chat_info.type
            
            if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                privileges = ChatPrivileges(
                    can_change_info=True,
                    can_delete_messages=True,
                    can_manage_video_chats=True,
                    can_restrict_members=True,
                    can_promote_members=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    is_anonymous=True,
                    can_manage_chat=True
                )
                await message.reply(f"User added as an admin in {chat_type} {chat_id} with specified privileges.")
                await client.promote_chat_member(chat_id, user_id, privileges=privileges)
            else:
                await message.reply(f"This command can only be used in groups or supergroups.")
        except UserNotParticipant:
            await message.reply(f"The user must be a member of the chat {chat_id} to use this command.")
        except Exception as e:
            await message.reply(f"An error occurred: {str(e)}")


# Define a command handler for /checkchattype
@Client.on_message(filters.command("checkchattype"))
async def check_chat_type(client, message):
    chat_id = message.chat.id
    chat_info = await client.get_chat(chat_id)

    if chat_info.type == "group":
        await message.reply("This is a Group chat.")
    elif chat_info.type == "supergroup":
        await message.reply("This is a Supergroup chat.")
    elif chat_info.type == "channel":
        await message.reply("This is a Channel chat.")
    else:
        await message.reply("This is an unknown chat type.")
