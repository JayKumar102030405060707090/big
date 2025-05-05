import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from pymongo import MongoClient
from telegram.ext import CallbackContext
import config

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(config.MONGODB_URI)
db = client.get_database()
vote_collection = db[config.VOTE_COLLECTION]

# Function to start the bot
def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    update.message.reply_text(f"Hello {user.first_name}, Welcome to the Voting Bot!\n\nPlease join our channel to participate in voting.\n{config.CHANNEL_LINK}")

# Function to check if user is in the required channel
def check_subscription(user_id):
    # Here you need to use the Telegram API to check if the user is subscribed to the channel
    # For now, it just returns True for simplicity
    return True

# Function to create a vote
def create_vote(update: Update, context: CallbackContext):
    if update.message.from_user.id != config.ADMIN_ID:
        update.message.reply_text("You are not authorized to create a vote!")
        return

    # Extract vote details from message
    try:
        question = context.args[0]
        options = context.args[1:]
        if len(options) < 2:
            update.message.reply_text("Please provide at least two options for the vote.")
            return
    except IndexError:
        update.message.reply_text("Please provide a question and options.")
        return

    # Generate vote message and inline buttons
    keyboard = [[InlineKeyboardButton(option, callback_data=option) for option in options]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send vote message to the group or channel
    update.message.reply_text(question, reply_markup=reply_markup)

    # Save vote to database
    vote_data = {
        "question": question,
        "options": options,
        "votes": {option: 0 for option in options},
        "status": "active"
    }
    vote_collection.insert_one(vote_data)

    update.message.reply_text("Vote created successfully!")

# Function to handle vote selection
def vote(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    # Check if the user is subscribed to the required channel
    if not check_subscription(user_id):
        query.answer("You must join the channel to vote!")
        return

    # Get vote data
    vote_data = vote_collection.find_one({"status": "active"})

    if not vote_data:
        query.answer("No active vote found!")
        return

    # Update vote count
    selected_option = query.data
    vote_collection.update_one(
        {"_id": vote_data["_id"]},
        {"$inc": {f"votes.{selected_option}": 1}}
    )

    query.answer(f"Your vote for '{selected_option}' has been recorded.")

# Function to display vote results
def vote_results(update: Update, context: CallbackContext):
    vote_data = vote_collection.find_one({"status": "active"})

    if not vote_data:
        update.message.reply_text("No active vote found!")
        return

    results = "\n".join([f"{option}: {vote_data['votes'][option]} votes" for option in vote_data['options']])
    update.message.reply_text(f"Vote Results:\n{results}")

# Command to stop the vote
def stop_vote(update: Update, context: CallbackContext):
    if update.message.from_user.id != config.ADMIN_ID:
        update.message.reply_text("You are not authorized to stop the vote!")
        return

    # Mark the vote as stopped
    vote_data = vote_collection.find_one({"status": "active"})
    if vote_data:
        vote_collection.update_one({"_id": vote_data["_id"]}, {"$set": {"status": "inactive"}})
        update.message.reply_text("Vote has been stopped!")
    else:
        update.message.reply_text("No active vote found!")

# Function to handle unknown commands
def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, I didn't understand that command.")

# Main function to start the bot
def main():
    # Create the Updater and pass it your bot's token
    updater = Updater(config.TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("createvote", create_vote))
    dispatcher.add_handler(CommandHandler("results", vote_results))
    dispatcher.add_handler(CommandHandler("stopvote", stop_vote))

    # Register callback handler for votes
    dispatcher.add_handler(CallbackQueryHandler(vote))

    # Register message handler for unknown commands
    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
