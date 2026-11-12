import os
import re
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# =====================================================================
# 🔑 CONFIGURATION (the token is read from environment / .env, not from code!)
#   echo 'BOT_TOKEN=123:ABC' > .env && chmod 600 .env
#   export CREATOR_ID="8961301932"
# =====================================================================
def _load_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if token and token.strip():
        return token.strip()
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("BOT_TOKEN="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("BOT_TOKEN not found: set it in the environment or in .env")


API_TOKEN = _load_token()
ID_Creator = int(os.getenv("CREATOR_ID", "8961301932"))

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def safe_edit(message: Message, text: str, **kwargs) -> None:
    """edit_text that ignores the harmless "message is not modified" error.

    Without this, pressing the same inline button twice raised TelegramBadRequest
    and the handler died with a traceback.
    """
    kwargs.setdefault("parse_mode", "Markdown")
    try:
        await message.edit_text(text, **kwargs)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )
''')
conn.commit()


def esc(text: str) -> str:
    """Escape for legacy Markdown (nicknames with _ and * used to break formatting)."""
    return re.sub(r'([_*`\[])', r'\\\1', text)


# =====================================================================
# 🎛️ MENUS
# =====================================================================
def get_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚀 My Projects (Python)", callback_data="my_projects"))
    builder.add(InlineKeyboardButton(text="🎨 My Linux Setup (Arch)", callback_data="my_rice"))
    builder.add(InlineKeyboardButton(text="🌐 Official GitHub Profile", url="https://github.com/mraz0tix-code"))
    builder.add(InlineKeyboardButton(text="💼 Official GitHub Site", callback_data="Sites"))
    builder.add(InlineKeyboardButton(text="📩 Contact Me", callback_data="contact_me"))
    builder.adjust(1)
    return builder.as_markup()


def get_projects_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📊 SysPulse", callback_data="proj_syspulse"))
    builder.add(InlineKeyboardButton(text="⚡ FastSysPulse", callback_data="proj_fastsys"))
    builder.add(InlineKeyboardButton(text="📡 NetPulse", callback_data="proj_netpulse"))
    builder.add(InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_main"))
    builder.adjust(1)
    return builder.as_markup()


def get_back_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_main"))
    return builder.as_markup()


# =====================================================================
# 📡 COMMANDS
# =====================================================================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    nickname = message.from_user.username or message.from_user.first_name

    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, nickname))
        conn.commit()
        greeting = f"✨ **Welcome, {esc(nickname)}!**"
    else:
        greeting = f"👋 **Hello, {esc(nickname)}!**"

    welcome_text = (
        f"{greeting}\n\n"
        "Welcome to the interactive bot-portfolio of **mraz0tix** — Python Developer & Linux Systems Administrator! 🦾💻\n\n"
        "Here you can explore my open-source system utilities, check out my custom desktop environment, "
        "and navigate directly to my source code repositories.\n\n"
        "Select a section below to get started 👇"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")


# =====================================================================
# 🖲️ CALLBACKS
# =====================================================================
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    await callback.answer()
    await safe_edit(callback.message, 
        "🔮 **Main Portfolio Menu:**\nSelect a section to explore 👇",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "my_projects")
async def show_projects(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📦 **My Custom Python Projects:**\n\n"
        "I build lightweight console applications for system automation, "
        "resource monitoring, and network analysis. Select a utility to view details 👇"
    )
    await safe_edit(callback.message, text, reply_markup=get_projects_menu(), parse_mode="Markdown")


@dp.callback_query(F.data == "Sites")
async def Site_open(callback: CallbackQuery):
    await callback.answer()
    builder = InlineKeyboardBuilder()

    # web_app only accepts an https link to the site itself, not a t.me link
    builder.add(InlineKeyboardButton(
        text="✨ Open App Site",
        web_app=types.WebAppInfo(url="https://mraz0tix-code.github.io/")
    ))
    builder.add(InlineKeyboardButton(
        text="🌐 Open Site in Browser",
        url="https://mraz0tix-code.github.io/"
    ))
    builder.add(InlineKeyboardButton(text="🔙 Back to Menu", callback_data="back_to_main"))
    builder.adjust(1)

    await safe_edit(callback.message, 
        "🌐 **Choose how you want to open the portfolio website:**",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "my_rice")
async def show_rice(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🎨 **Arch Linux Customization (My Rice):**\n\n"
        "• **OS:** Arch Linux 🛸\n"
        "• **DE:** GNOME (Modified Blue WhiteSur Theme)\n"
        "• **Terminal:** Kitty + zsh Shell \n"
        "• **Compositor:** Blur my Shell (Deep window blur up to 60 radius)\n\n"
        "The entire system is deployed automatically via dotfiles. You can find the source link in the main menu!"
    )
    await safe_edit(callback.message, text, reply_markup=get_back_button(), parse_mode="Markdown")


@dp.callback_query(F.data == "contact_me")
async def contact_me_prompt(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📨 **Anonymous Feedback System:**\n\n"
        "You can type your message or question right below and send it to this chat.\n"
        "The bot will securely forward it directly to **mraz0tix**.\n\n"
        "❗ Your personal details are safe, and Max's real username remains private."
    )
    await safe_edit(callback.message, text, reply_markup=get_back_button(), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("proj_"))
async def show_project_details(callback: CallbackQuery):
    await callback.answer()
    proj = callback.data

    if proj == "proj_syspulse":
        text = (
            "📊 **SysPulse**\n\n"
            "• **Core:** Real-time terminal-based system monitor for server metrics.\n"
            "\n• **Codebase:** 422 lines of clean Python.\n"
            "\n• **Features:** Core interrupt tracking, multi-threaded CPU load graphing."
        )
    elif proj == "proj_fastsys":
        text = (
            "⚡ **FastSysPulse**\n\n"
            "• **Core:** High-speed asynchronous engine for instant system metrics fetching.\n"
            "\n• **Codebase:** 418 lines of asynchronous Python.\n"
            "\n• **Features:** Minimal RAM footprint, seamless JSON stream output generation."
        )
    else:
        text = (
            "📡 **NetPulse**\n\n"
            "• **Core:** Wireless packet analyzer and wireless spectrum scanner.\n"
            "\n• **Codebase:** 156 lines of Python.\n"
            "\n• **Features:** Packet metadata interception, low-level server ping metrics verification."
        )
    await safe_edit(callback.message, text, reply_markup=get_projects_menu(), parse_mode="Markdown")


# =====================================================================
# 📡 ANONYMOUS BRIDGE
# =====================================================================
# Creator's reply handler is registered FIRST and sends plain text (no markup)
@dp.message(F.text & (F.from_user.id == ID_Creator) & F.reply_to_message)
async def reply_to_user(message: Message):
    try:
        source = message.reply_to_message.text or ""
        match = re.search(r"ID:\s*`?(\d+)`?", source)
        if not match:
            await message.reply("❌ Error: Could not parse target User ID from the log message.")
            return

        user_id = int(match.group(1))
        reply_text = f"💬 Response from mraz0tix:\n\n{message.text}"
        await bot.send_message(chat_id=user_id, text=reply_text)
        await message.reply("🚀 Response successfully delivered to the user!")
    except Exception as e:
        await message.reply(f"🔴 Failed to deliver message: {e}")


@dp.message(F.text & (F.from_user.id != ID_Creator))
async def forward_to_max(message: Message):
    # No parse_mode: user text may contain _ * ` and break formatting
    log_text = (
        "🔔 New Message received!\n"
        f"From user: {message.from_user.full_name} (ID: {message.from_user.id})\n\n"
        f"💬 Text:\n{message.text}"
    )
    await bot.send_message(chat_id=ID_Creator, text=log_text)
    await message.reply("✅ Your message has been securely sent to Max! Thank you.")


# =====================================================================
# 🚀 RUNTIME START
# =====================================================================
async def main():
    print("[+] Portfolio bot successfully initialized. Ready for global production!")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
