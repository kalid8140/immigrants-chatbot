import asyncio
import logging
import os
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramBadRequest,
    TelegramRetryAfter,
)

# =====================================
# SETTINGS
# =====================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = set()

# Admin 1
if os.getenv("ADMIN_ID"):
    ADMIN_IDS.add(int(os.getenv("ADMIN_ID")))

# Admin 2, 3, 4
if os.getenv("ADMIN_IDS"):
    for admin_id in os.getenv("ADMIN_IDS").split(","):
        admin_id = admin_id.strip()
        if admin_id:
            ADMIN_IDS.add(int(admin_id))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing!")

if not ADMIN_IDS:
    raise ValueError("No Admin IDs configured!")

DB_FILE = "immigrants_chat.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Adminoota broadcast eegalaniif
broadcast_waiting = set()


# =====================================
# DATABASE
# =====================================

def connect_db():
    return sqlite3.connect(DB_FILE)


def setup_database():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            active INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reply_map (
            admin_id INTEGER,
            admin_message_id INTEGER,
            user_id INTEGER,
            PRIMARY KEY (admin_id, admin_message_id)
        )
    """)

    conn.commit()
    conn.close()


def save_user(user):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (user_id, username, full_name, active)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name,
            active = 1
    """, (
        user.id,
        user.username or "",
        user.full_name or ""
    ))

    conn.commit()
    conn.close()


def get_users():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM users WHERE active = 1")
    users = [row[0] for row in cur.fetchall()]

    conn.close()
    return users


def count_users():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE active = 1")
    count = cur.fetchone()[0]

    conn.close()
    return count


def save_reply_map(admin_id, message_id, user_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR REPLACE INTO reply_map
        (admin_id, admin_message_id, user_id)
        VALUES (?, ?, ?)
    """, (admin_id, message_id, user_id))

    conn.commit()
    conn.close()


def get_reply_user(admin_id, message_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id FROM reply_map
        WHERE admin_id = ? AND admin_message_id = ?
    """, (admin_id, message_id))

    result = cur.fetchone()
    conn.close()

    return result[0] if result else None


def deactivate_user(user_id):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET active = 0 WHERE user_id = ?",
        (user_id,)
    )

    conn.commit()
    conn.close()


# =====================================
# START COMMAND
# =====================================

@dp.message(Command("start"))
async def start_command(message: Message):

    user_id = message.from_user.id

    if user_id in ADMIN_IDS:
        await message.answer(
            "👨‍💼 IMMIGRANTS CHAT ADMIN PANEL\n\n"
            "Welcome, Admin!\n\n"
            "Commands:\n"
            "/users - View registered users\n"
            "/broadcast - Send a message to all users\n"
            "/cancel - Cancel broadcast\n\n"
            "You can reply directly to a user's message "
            "to send them a response."
        )
        return

    save_user(message.from_user)

    welcome = """
🌍✨ WELCOME TO IMMIGRANTS CHAT! ✈️

We are happy to have you here! ❤️

🌎 YOUR DESTINATIONS:
🇺🇸 America
🇨🇦 Canada
🇪🇺 Europe
🇮🇹 Italy
🇦🇪 Dubai

📌 OUR SERVICES:
🛂 Visa Information
💼 Work Abroad
🎓 Study Abroad
✈️ Immigration Guidance
📄 Application Support

🌐 LANGUAGE SUPPORT:
You can communicate with us in ANY LANGUAGE you prefer.

🇪🇹 Afaan Oromoo
🇪🇹 Amharic
🇬🇧 English
🌍 And many other languages!

📩 HOW TO GET HELP:
Simply send us your message, question, or request in your preferred language.

👨‍💼 Our Admin Team will receive your message and reply as soon as possible.

❤️ IMMIGRANTS CHAT
🌍 Your Dream, Our Guidance!
"""

    await message.answer(welcome)


# =====================================
# USERS COMMAND
# =====================================

@dp.message(Command("users"))
async def users_command(message: Message):

    if message.from_user.id not in ADMIN_IDS:
        return

    total = count_users()

    await message.answer(
        f"👥 IMMIGRANTS CHAT USERS\n\n"
        f"Total active users: {total}"
    )


# =====================================
# BROADCAST COMMAND
# =====================================

@dp.message(Command("broadcast"))
async def broadcast_command(message: Message):

    admin_id = message.from_user.id

    if admin_id not in ADMIN_IDS:
        return

    broadcast_waiting.add(admin_id)

    await message.answer(
        "📢 BROADCAST MODE\n\n"
        "Now send the message you want to deliver to all users.\n\n"
        "You can send:\n"
        "📝 Text\n"
        "🖼 Photo\n"
        "🎥 Video\n"
        "📄 PDF or document\n"
        "🎵 Audio or voice message\n\n"
        "To cancel, send /cancel"
    )


# =====================================
# CANCEL BROADCAST
# =====================================

@dp.message(Command("cancel"))
async def cancel_command(message: Message):

    admin_id = message.from_user.id

    if admin_id not in ADMIN_IDS:
        return

    if admin_id in broadcast_waiting:
        broadcast_waiting.remove(admin_id)

        await message.answer(
            "❌ Broadcast cancelled."
        )
    else:
        await message.answer(
            "There is no active broadcast."
        )


# =====================================
# BROADCAST MESSAGE HANDLER
# =====================================

@dp.message(F.from_user.id.in_(ADMIN_IDS))
async def admin_message_handler(message: Message):

    admin_id = message.from_user.id

    # Broadcast mode
    if admin_id in broadcast_waiting:

        broadcast_waiting.remove(admin_id)

        users = get_users()

        success = 0
        failed = 0

        status = await message.answer(
            "⏳ Broadcasting started..."
        )

        for user_id in users:

            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )

                success += 1
                await asyncio.sleep(0.05)

            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after + 1)

                try:
                    await bot.copy_message(
                        chat_id=user_id,
                        from_chat_id=message.chat.id,
                        message_id=message.message_id
                    )
                    success += 1
                except Exception:
                    failed += 1

            except (TelegramForbiddenError, TelegramBadRequest):
                deactivate_user(user_id)
                failed += 1

            except Exception as e:
                logging.exception("Broadcast error: %s", e)
                failed += 1

        await status.edit_text(
            "✅ BROADCAST FINISHED!\n\n"
            f"👥 Total users: {len(users)}\n"
            f"✅ Successfully sent: {success}\n"
            f"❌ Failed: {failed}"
        )

        return

    # Admin reply to a user's notification
    if message.reply_to_message:

        original_message_id = message.reply_to_message.message_id

        user_id = get_reply_user(
            admin_id,
            original_message_id
        )

        if user_id:

            try:
                await bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )

                await message.reply(
                    "✅ Your reply has been sent to the user."
                )

            except Exception as e:
                logging.exception("Reply error: %s", e)

                await message.reply(
                    "❌ Could not send the reply. "
                    "The user may have blocked the bot."
                )

            return

    # Other admin messages
    await message.answer(
        "Admin commands:\n"
        "/users - View users\n"
        "/broadcast - Broadcast to all users\n"
        "/cancel - Cancel broadcast\n\n"
        "To reply to a user, use Reply on their notification."
    )


# =====================================
# USER MESSAGE HANDLER
# =====================================

@dp.message()
async def user_message_handler(message: Message):

    user = message.from_user

    if not user:
        return

    if user.id in ADMIN_IDS:
        return

    # Save user
    save_user(user)

    username = (
        f"@{user.username}"
        if user.username
        else "No username"
    )

    admin_notification = (
        "📩 NEW MESSAGE - IMMIGRANTS CHAT\n\n"
        f"👤 Name: {user.full_name}\n"
        f"🔹 Username: {username}\n"
        f"🆔 User ID: {user.id}\n\n"
        "👇 Reply directly to this notification "
        "or the copied message to answer the user."
    )

    # Send notification to all admins
    for admin_id in ADMIN_IDS:

        try:
            header = await bot.send_message(
                chat_id=admin_id,
                text=admin_notification
            )

            copied = await bot.copy_message(
                chat_id=admin_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            # Both messages can be used to reply
            save_reply_map(
                admin_id,
                header.message_id,
                user.id
            )

            save_reply_map(
                admin_id,
                copied.message_id,
                user.id
            )

        except Exception as e:
            logging.exception(
                "Could not notify admin %s: %s",
                admin_id,
                e
            )

    await message.answer(
        "✅ Your message has been received!\n\n"
        "Our Admin Team will review your request "
        "and reply as soon as possible. ❤️"
    )


# =====================================
# MAIN
# =====================================

async def main():

    setup_database()

    logging.info("IMMIGRANTS CHAT BOT is starting...")
    logging.info("Admin count: %s", len(ADMIN_IDS))

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())