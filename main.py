
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.enums import ParseMode

# ==============================
# BOT CONFIGURATION
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Store users
users = set()


# ==============================
# START COMMAND
# ==============================

@dp.message(CommandStart())
async def start(message: Message):

    users.add(message.from_user.id)

    await message.answer(
        "👋 Welcome to IMMIGRANTS CHAT!\n\n"
        "🌍 Afaan Oromoo | Amharic | English\n\n"
        "You can send us any message.\n"
        "👨‍💼 Our Admin will reply to you soon.\n\n"
        "Thank you for contacting us! ❤️"
    )

    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 New user started the bot!\n\n"
            f"Name: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username}\n"
            f"User ID: {message.from_user.id}"
        )


# ==============================
# ADMIN COMMANDS
# ==============================

@dp.message(Command("users"))
async def show_users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        f"👥 Users seen since bot startup: {len(users)}"
    )


# ==============================
# USER MESSAGES TO ADMIN
# ==============================

@dp.message(F.from_user.id != ADMIN_ID)
async def user_message(message: Message):

    users.add(message.from_user.id)

    await bot.send_message(
        ADMIN_ID,
        f"📩 NEW MESSAGE\n\n"
        f"👤 Name: {message.from_user.full_name}\n"
        f"🆔 User ID: {message.from_user.id}\n"
        f"💬 Reply directly to this message."
    )

    await message.copy_to(ADMIN_ID)

    await message.answer(
        "✅ Your message has been sent to the Admin.\n"
        "Please wait for a reply. ❤️"
    )


# ==============================
# ADMIN REPLY TO USER
# ==============================

@dp.message(F.from_user.id == ADMIN_ID)
async def admin_reply(message: Message):

    if not message.reply_to_message:
        await message.answer(
            "👑 To reply to a user:\n\n"
            "1. Find the user's message above.\n"
            "2. Tap Reply.\n"
            "3. Write your response."
        )
        return

    original = message.reply_to_message.text or ""

    if "User ID:" not in original:
        await message.answer(
            "⚠️ Reply directly to the user's message notification."
        )
        return

    try:
        user_id = int(original.split("User ID:")[1].split()[0])

        await message.copy_to(user_id)

        await message.answer("✅ Reply sent successfully!")

    except Exception as e:
        logging.error(e)
        await message.answer("❌ Could not send the reply.")


# ==============================
# RUN BOT
# ==============================

async def main():

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing!")

    if not ADMIN_ID:
        raise ValueError("ADMIN_ID is missing!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())