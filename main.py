import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)
from pymongo import MongoClient
import config

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(config.MONGODB_URI)
db = client.get_database()
vote_collection = db[config.VOTE_COLLECTION]

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.first_name}, Voting Bot mein aapka swagat hai!\n\n"
        f"Hissa lene ke liye pehle channel join karein:\n{config.CHANNEL_LINK}"
    )

# Dummy subscription check
def check_subscription(user_id):
    return True  # Actual API logic baad mein add karna

# /createvote command
async def create_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("Aap vote banane ke liye authorized nahi hain!")
        return

    try:
        question = context.args[0]
        options = context.args[1:]
        if len(options) < 2:
            await update.message.reply_text("Kam se kam do options dena zaroori hai.")
            return
    except IndexError:
        await update.message.reply_text("Question aur options sahi format mein bhejein.")
        return

    keyboard = [[InlineKeyboardButton(option, callback_data=option) for option in options]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(question, reply_markup=reply_markup)

    vote_data = {
        "question": question,
        "options": options,
        "votes": {option: 0 for option in options},
        "status": "active"
    }
    vote_collection.insert_one(vote_data)

    await update.message.reply_text("Vote successfully create ho gaya!")

# Callback button click handler
async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not check_subscription(user_id):
        await query.answer("Pehle channel join karein!", show_alert=True)
        return

    vote_data = vote_collection.find_one({"status": "active"})

    if not vote_data:
        await query.answer("Koi active vote nahi mila.", show_alert=True)
        return

    selected_option = query.data
    vote_collection.update_one(
        {"_id": vote_data["_id"]},
        {"$inc": {f"votes.{selected_option}": 1}}
    )

    await query.answer(f"Aapka vote '{selected_option}' ke liye record ho gaya!")

# /results command
async def vote_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vote_data = vote_collection.find_one({"status": "active"})

    if not vote_data:
        await update.message.reply_text("Koi active vote nahi mila.")
        return

    results = "\n".join([f"{option}: {vote_data['votes'][option]} votes" for option in vote_data['options']])
    await update.message.reply_text(f"Vote Results:\n{results}")

# /stopvote command
async def stop_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.ADMIN_ID:
        await update.message.reply_text("Aap authorized nahi hain!")
        return

    vote_data = vote_collection.find_one({"status": "active"})
    if vote_data:
        vote_collection.update_one({"_id": vote_data["_id"]}, {"$set": {"status": "inactive"}})
        await update.message.reply_text("Vote stop kar diya gaya.")
    else:
        await update.message.reply_text("Koi active vote nahi mila.")

# Unknown command handler
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yeh command samajh nahi aayi.")

# Main function
def main():
    app = ApplicationBuilder().token(config.TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createvote", create_vote))
    app.add_handler(CommandHandler("results", vote_results))
    app.add_handler(CommandHandler("stopvote", stop_vote))
    app.add_handler(CallbackQueryHandler(vote))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("Bot started...")
    app.run_polling()

if __name__ == '__main__':
    main()
