import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix

@Client.on_message(filters.command(["add", "c"], prefix) & filters.me)
async def add_contact(c: Client, message: Message):
    try:
        user = await c.get_users(message.chat.id)
        if user.is_bot:
            return await message.edit("You can't add bots to contacts.")

        args = message.text.split(maxsplit=1)[1:] if len(message.command) > 1 else []

        if not args and message.reply_to_message and message.reply_to_message.text:
            args = [message.reply_to_message.text.strip()]

        first_name = args[0] if args else (user.first_name or "Unknown")
        last_name = args[1] if len(args) > 1 else ""

        await c.add_contact(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone_number="",
            share_phone_number=False
        )

        user = await c.get_users(user.id)
        full_name = f"{first_name} {last_name}".strip()
        mutual_status = " (Mutual)" if user.is_mutual_contact else " (Not Mutual)"

        await message.edit(f"<b>Contact added:</b> <a href='tg://user?id={user.id}'>{full_name}</a>{mutual_status}")
    except Exception as e:
        await message.edit(f"Failed to add contact: <code>{e}</code>")

    await asyncio.sleep(1)
    await message.delete()

@Client.on_message(filters.command(["remove", "r"], prefix) & filters.me)
async def remove_contact(c: Client, message: Message):
    try:
        user = message.reply_to_message.from_user if message.reply_to_message else await c.get_users(message.chat.id)
        if user.is_self:
            return await message.edit("You can't remove yourself.")

        await c.delete_contacts(user_ids=user.id)
        await message.edit(f"<b>Contact removed:</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>")
    except Exception as e:
        await message.edit(f"Failed to remove contact: <code>{e}</code>")

    await asyncio.sleep(5)
    await message.delete()

@Client.on_message(filters.command("mutual", prefix) & filters.me)
async def check_mutual(c: Client, message: Message):
    try:
        user = message.reply_to_message.from_user if message.reply_to_message else await c.get_users(message.chat.id)
        if user.is_self:
            return await message.edit("That's you.")

        status = [
            f"<b>Checking mutual status for</b> <a href='tg://user?id={user.id}'>{user.first_name}</a>:\n",
            "- You have <b>added</b> them to your contacts." if user.is_contact else "- You have <b>not added</b> them.",
            "- They have also <b>added you</b>. You're <b>mutual contacts</b>." if user.is_mutual_contact else "- They <b>haven't added</b> you back."
        ]
        await message.edit("\n".join(status))
    except Exception as e:
        await message.edit(f"Error: <code>{e}</code>")

    await asyncio.sleep(5)
    await message.delete()

@Client.on_message(filters.command(["clearchat", "cc"], prefix) & filters.me)
async def clear_chat(c: Client, message: Message):
    try:
        async for msg in c.get_chat_history(message.chat.id):
            if msg.from_user and msg.from_user.id == (await c.get_me()).id:
                try:
                    await c.delete_messages(message.chat.id, msg.id)
                except:
                    pass

        await c.send_message("me", "Your messages have been deleted from both sides.")
    except Exception as e:
        await c.send_message("me", f"Error while clearing chat: <code>{e}</code>")

    try:
        await message.delete()
    except:
        pass

modules_help["contact"] = {
    "add [optional name]": "Add the current user to your contacts. You can also reply to a message to use it as the name. Displays (Mutual) or (Not Mutual).",
    "mutual": "Check if you're mutual contacts with the replied user or private chat user.",
    "remove": "Remove the current user or replied user from your contacts.",
    "clearchat": "Delete own messages in chat.",
}
