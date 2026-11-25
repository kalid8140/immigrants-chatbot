import asyncio
import logging
import os
import re

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin 1: ID duraan Render keessa jiru
ADMIN_IDS = set()

old_admin = os.getenv("ADMIN_ID", "").strip()
if old_admin:
    ADMIN_IDS.add(int(old_admin))

# Admin 2, 3, 4: IDwwan haaraa
extra_admins = os.getenv("ADMIN_IDS", "")

for admin_id in extra_admins.split(","):
    admin_id = admin_id.strip()
    if admin_id:
        ADMIN_IDS.add(int(admin_id))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = set()


@dp.message(CommandStart())
async def start(message: Message):
    if message.from_user.id in ADMIN_IDS:
        await message.answer(
            "👑 Welcome Admin!\n\n"
            "You are an administrator of IMMIGRANTS CHAT.\n\n"
            "Use /users to see user statistics.\n"
            "Reply directly to a user's notification to respond."
        )
        return

    users.add(message.from_user.id)

    await message.answer(
        "🌍 Welcome to IMMIGRANTS CHAT!\n\n"
        "Afaan Oromoo | አማርኛ | English\n\n"
        "Send your message here.\n"
        "Our Admin team will reply to you soon. ❤️"
    )


@dp.message(Command("users"))
async def show_users(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        f"👥 Users since last restart: {len(users)}\n"
        f"👑 Total Admins: {len(ADMIN_IDS)}"
    )


@dp.message(F.from_user.id.in_(ADMIN_IDS))
async def admin_messages(message: Message):

    if not message.reply_to_message:
        await message.answer(
            "👑 ADMIN PANEL\n\n"
            "To reply to a user:\n"
            "1. Find the user's notification.\n"
            "2. Reply directly to the notification.\n"
            "3. Send your reply.\n\n"
            "Use /users for statistics."
        )
        return

    original = message.reply_to_message.text or ""

    match = re.search(r"User ID:\s*(\d+)", original)

    if not match or "IMMIGRANTS_CHAT_REPLY" not in original:
        await message.answer(
            "⚠️ Please reply directly to the user's notification."
        )
        return

    user_id = int(match.group(1))

    try:
        await message.copy_to(chat_id=user_id)

        await message.answer(
            "✅ Your reply has been delivered successfully!"
        )

    except Exception as error:
        logging.exception("Admin reply failed: %s", error)

        await message.answer(
            "❌ Message could not be delivered."
        )


@dp.message()
async def receive_user_message(message: Message):

    if message.from_user.id in ADMIN_IDS:
        return

    user_id = message.from_user.id
    users.add(user_id)

    delivered = 0

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "📩 NEW MESSAGE\n\n"
                f"👤 Name: {message.from_user.full_name}\n"
                f"Username: @{message.from_user.username or 'None'}\n"
                f"IMMIGRANTS_CHAT_REPLY\n"
                f"User ID: {user_id}\n\n"
                "👇 Reply directly to THIS notification."
            )

            await message.copy_to(chat_id=admin_id)
            delivered += 1

        except Exception as error:
            logging.exception(
                "Could not send message to admin %s: %s",
                admin_id,
                error
            )

    if delivered > 0:
        await message.answer(
            "✅ Your message has been sent to our Admin team.\n"
            "Please wait for a reply. ❤️"
        )
    else:
        await message.answer(
            "⚠️ Our Admin team could not receive your message.\n"
            "Please try again later."
        )


async def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    if not ADMIN_IDS:
        raise ValueError("No ADMIN IDs configured!")

    logging.info("Immigrants Chat is starting...")
    logging.info("Total Admins: %s", len(ADMIN_IDS))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())