from pyrogram import Client, filters
from pyrogram.types import ChatPermissions
from plugins.helper.admin_check import admin_check
from plugins.helper.extract import extract_time, extract_user


@Client.on_message(filters.group & filters.command("promote"))
async def promote_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        await message.reply_text("Admin privileges are required to perform this action.")
        return

    user_id, user_first_name = extract_user(message)
    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return

    user_member = await chat.get_member(user_id)
    if user_member.status in ['administrator', 'creator']:
        await message.reply_text("The user is already an admin.")
        return

    if user_id == bot.id:
        await message.reply_text("I can't promote myself!")
        return
        
    bot_member = await chat.get_member(bot.id)

    await bot.promote_chat_member(
        chat.id, user_id,
        can_change_info=bot_member.can_change_info,
        can_post_messages=bot_member.can_post_messages,
        can_edit_messages=bot_member.can_edit_messages,
        can_delete_messages=bot_member.can_delete_messages,
        can_invite_users=bot_member.can_invite_users,
        can_restrict_members=bot_member.can_restrict_members,
        can_pin_messages=bot_member.can_pin_messages,
        can_promote_members=bot_member.can_promote_members
    )
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(f"✨ {user_first_name} has been promoted to an admin! 🎉")

        
@Client.on_message(filters.group & filters.command("demote"))
async def demote_user(_, message):
    is_admin = await admin_check(message)
    if not is_admin:
        await message.reply_text("Admin privileges are required to perform this action.")
        return

    user_id, user_first_name = extract_user(message)
    if not user_id:
        await message.reply_text("You don't seem to be referring to a user.")
        return

    user_member = await chat.get_member(user_id)
    if user_member.status == 'creator':
        await message.reply_text("Cannot demote the chat creator.")
        return

    if user_member.status != 'administrator':
        await message.reply_text("The user is not an admin.")
        return

    if user_id == bot.id:
        await message.reply_text("I can't demote myself!")
        return

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False
        )

        await chat.restrict_member(user_id, ChatPermissions(can_send_messages=True))  # Assuming this is the desired restriction
    except Exception as error:
        await message.reply_text(str(error))
    else:
        await message.reply_text(f"🔥 {user_first_name} has been demoted to a regular member!")
