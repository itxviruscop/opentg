import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix


@Client.on_message(filters.command("add", prefix) & filters.me)
async def add_contact(c: Client, message: Message):
    try:
        user = await c.get_users(message.chat.id)
        if user.is_bot:
            return await message.edit("You can't add bots to contacts.")
        # Get optional custom name
        name = message.text.split(maxsplit=1)[1:] or [user.first_name or "Unknown", user.last_name or ""]
        name += [""] * (2 - len(name))  # Ensure 2 elements
        first_name, last_name = name[0], name[1]

        await c.add_contact(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            phone_number="",
            share_phone_number=False
        )

        full_name = f"{first_name} {last_name}".strip()
        await message.edit(f"<b>Contact added:</b> <a href='tg://user?id={user.id}'>{full_name}</a>")
    except Exception as e:
        await message.edit(f"Failed to add contact: <code>{e}</code>")

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
            "- You have <b>added</b> them to your contacts." if getattr(user, "is_contact", False)
            else "- You have <b>not added</b> them to your contacts.",
            "- They have also <b>added you</b>. You're <b>mutual contacts</b>." if getattr(user, "is_mutual_contact", False)
            else "- They <b>haven't added</b> you back."
        ]
        await message.edit("\n".join(status))
    except Exception as e:
        await message.edit(f"Error: <code>{e}</code>")

    await asyncio.sleep(5)
    await message.delete()


modules_help["contact"] = {
    "add [optional name]": "Add the current user to your contacts.",
    "mutual": "Check if you're mutual contacts with the replied user or private chat user.",
}
