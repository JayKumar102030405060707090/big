import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from time import sleep

# MongoDB Client Setup
client = MongoClient("mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")
db = client['telegram_bot_db']
users_collection = db['users']

# Telegram Bot Setup
api_id = "28609964"  # Your API ID from my.telegram.org
api_hash = "3236bdf1e11a0fb8091495e083857621"  # Your API hash from my.telegram.org
bot_token = "7614916680:AAEVOATGqMzDOfIpDCJ36_1K_7ONnt2vXis"  # Your Bot Token

app = Client("force_subscribe_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Channels for Force Subscribe
force_subscribe_channels = [
    "https://t.me/+G-y93SIcREY3YTg9",
    "https://t.me/Jalwagame_Hack",
    "https://t.me/sureshot101game"
]

# Admin Details
owner_id = 7168729089
owner_username = "@INNOCENT_FUCKER"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper Functions
def check_force_subscribe(user_id):
    try:
        user = app.get_chat_member(force_subscribe_channels[0], user_id)
        if user.status not in ['member', 'administrator', 'creator']:
            return False
        for channel in force_subscribe_channels[1:]:
            user = app.get_chat_member(channel, user_id)
            if user.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except:
        return False

# Start Command
@app.on_message(filters.command("start"))
def start(client, message):
    user_id = message.from_user.id
    user_name = message.from_user.username
    user_first_name = message.from_user.first_name

    # Check if user already in database
    existing_user = users_collection.find_one({"user_id": user_id})

    if not existing_user:
        # Add new user to DB
        users_collection.insert_one({
            "user_id": user_id,
            "username": user_name,
            "first_name": user_first_name,
            "joined_channels": []
        })
    
    if check_force_subscribe(user_id):
        # User is already subscribed to all channels
        app.send_message(
            user_id,
            f"Welcome {user_first_name}!\n\nYou are successfully subscribed to all required channels.\nChoose any action below:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join 91 Club", url="https://www.dmwin3.com/#/register?invitationCode=137222244286")],
                [InlineKeyboardButton("Become Agent (₹500 - ₹50,000/day)", callback_data="agent_work")],
                [InlineKeyboardButton("Get Predictions", callback_data="predictions")]
            ])
        )
    else:
        # User not subscribed to all channels
        app.send_message(
            user_id,
            "You need to join the required channels first to proceed.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channels", url=force_subscribe_channels[0])],
                [InlineKeyboardButton("Join Channels", url=force_subscribe_channels[1])],
                [InlineKeyboardButton("Join Channels", url=force_subscribe_channels[2])]
            ])
        )

# Handle Agent Work
@app.on_callback_query(filters.regex("agent_work"))
def agent_work(client, callback_query):
    user_id = callback_query.from_user.id
    app.send_message(
        user_id,
        "To become an agent, please contact @INNOCENT_FUCKER.\n\nYou will earn ₹500 - ₹50,000 daily based on your work. Minimum target: 1 user per day."
    )

# Handle Predictions
@app.on_callback_query(filters.regex("predictions"))
def predictions(client, callback_query):
    user_id = callback_query.from_user.id
    app.send_message(
        user_id,
        "Here are your predictions for today:\n\nColor: Red\nTrick: Odd\nDigit: 5\nGood luck!"
    )

# Broadcast Message (only for owner)
@app.on_message(filters.command("broadcast") & filters.user(owner_id))
def broadcast(client, message):
    text = message.text.split(maxsplit=1)[1]
    for user in users_collection.find():
        try:
            app.send_message(user["user_id"], text)
        except:
            continue
    app.send_message(owner_id, "Broadcast message sent successfully!")

# Stats Command (only for owner)
@app.on_message(filters.command("stats") & filters.user(owner_id))
def stats(client, message):
    total_users = users_collection.count_documents({})
    active_users = 0
    for user in users_collection.find():
        if check_force_subscribe(user["user_id"]):
            active_users += 1
    app.send_message(
        owner_id,
        f"Total Users: {total_users}\nActive Users: {active_users}\nTotal Registered in 91 Club: {total_users}"
    )

# Running the bot
if __name__ == "__main__":
    app.run()
