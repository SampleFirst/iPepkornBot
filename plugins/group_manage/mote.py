from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from plugins.helper.admin_check import admin_check
from plugins.helper.extract import extract_time, extract_user

@Client.on_message(filters.command("promote"))
async def promote_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        await message.reply_text(
            "Attention: Admin Privileges Required\n\n"
            "Dear member,\n\n"
            "However, to access this, we kindly request that you ensure you have admin privileges within our group."
        )
        return

    user_id, user_first_name = extract_user(message)

    try:
        await message.chat.promote_member(user_id)
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(
            f"✨ {user_first_name} has been promoted to an admin! 🎉"
        )


@Client.on_message(filters.command("demote"))
async def demote_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        await message.reply_text(
            "Attention: Admin Privileges Required\n\n"
            "Dear member,\n\n"
            "To access this, we kindly request that you ensure you have admin privileges within our group."
        )
        return

    user_id, user_first_name = extract_user(message)

    try:
        await message.chat.restrict_member(user_id, ChatPermissions())
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(
            f"🔥 {user_first_name} has been demoted to a regular member!"
        )
