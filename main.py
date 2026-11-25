import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# =========================
# CONFIGURATION
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = set()


# =========================
# START COMMAND
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👑 Welcome Admin!\n\n"
            "You can reply to users directly from this Telegram account.\n"
            "Use /users to see user statistics."
        )
        return

    users.add(message.from_user.id)

    await message.answer(
        "🌍 Welcome to IMMIGRANTS CHAT!\n\n"
        "Afaan Oromoo | አማርኛ | English\n\n"
        "Send your message here.\n"
        "Our Admin will reply to you soon. ❤️"
    )


# =========================
# ADMIN USERS COMMAND
# =========================

@dp.message(Command("users"))
async def show_users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        f"👥 Users since last restart: {len(users)}"
    )


# =========================
# ADMIN REPLY SYSTEM
# =========================

@dp.message(F.from_user.id == ADMIN_ID)
async def admin_messages(message: Message):

    if not message.reply_to_message:
        await message.answer(
            "👑 Admin Panel\n\n"
            "To reply to a user:\n"
            "1. Find the user's notification.\n"
            "2. Reply directly to that notification.\n"
            "3. Send your message.\n\n"
            "Use /users to see users."
        )
        return

    original = message.reply_to_message.text or ""

    if "User ID:" not in original:
        await message.answer(
            "⚠️ Please Reply directly to the user's notification."
        )
        return

    try:
        user_id = int(
            original.split("User ID:")[1].splitlines()[0].strip()
        )

        await message.copy_to(chat_id=user_id)

        await message.answer(
            "✅ Your reply has been delivered successfully!"
        )

    except Exception as error:
        logging.exception("Admin reply failed: %s", error)

        await message.answer(
            "❌ Message could not be delivered."
        )


# =========================
# USER MESSAGES
# =========================

@dp.message(F.from_user.id != ADMIN_ID)
async def receive_user_message(message: Message):

    user_id = message.from_user.id
    users.add(user_id)

    try:
        # Send notification containing the user ID.
        await bot.send_message(
            ADMIN_ID,
            f"📩 NEW MESSAGE\n\n"
            f"👤 Name: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username or 'None'}\n"
            f"User ID: {user_id}\n\n"
            f"👇 Reply directly to THIS notification."
        )

        # Send the original message separately.
        await message.copy_to(chat_id=ADMIN_ID)

        await message.answer(
            "✅ Your message has been sent to our Admin.\n\n"
            "Please wait for a reply. ❤️"
        )

    except Exception as error:
        logging.exception("Message delivery failed: %s", error)

        await message.answer(
            "⚠️ Sorry, your message could not be delivered. "
            "Please try again later."
        )


# =========================
# START BOT
# =========================

async def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    if not ADMIN_ID:
        raise ValueError("ADMIN_ID is missing!")

    logging.info("Immigrants Chat is starting...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())