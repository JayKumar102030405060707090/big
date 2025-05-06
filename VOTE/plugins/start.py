from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

async def handle_start(client, message: Message):
    await message.reply_photo(
        photo="https://graph.org/file/46412deeaab8e8b8c0b06-3bc9b2e0ae531f7b9c.jpg",
        caption="**🏆 VOTE BOT**\n\n"
                "Create subscriber-only vote polls for your channels\n"
                "Only channel subscribers can vote in polls\n\n"
                "🔹 /vote - Create new poll\n"
                "🔹 /help - Bot instructions",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add to Channel", url=f"https://t.me/{client.me.username}?startgroup=true")],
            [
                InlineKeyboardButton("Updates", url=f"https://t.me/{Config.UPDATE_CHANNEL}"),
                InlineKeyboardButton("Support", url=f"https://t.me/{Config.SUPPORT_GROUP}")
            ]
        ])
    )
