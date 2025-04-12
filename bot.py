import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.constants import ChatType
import os

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN")

# केवल चैनल या ग्रुप के एडमिन/ओनर को अनुमति दें
async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL]:
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    return False

# सामान्य हैंडलर टेम्पलेट
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    if await check_admin(update, context):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        await update.message.reply_text("सिर्फ एडमिन्स इस कमांड का उपयोग कर सकते हैं।")

async def big(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "Big")

async def small(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "Small")

async def red(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "Red")

async def green(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_command(update, context, "Green")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("big", big))
    app.add_handler(CommandHandler("small", small))
    app.add_handler(CommandHandler("red", red))
    app.add_handler(CommandHandler("green", green))

    print("Bot is running...")
    app.run_polling()
