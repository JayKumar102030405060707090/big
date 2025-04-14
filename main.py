import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pymongo import MongoClient
from time import sleep
MongoDB Client Setup

client = MongoClient("mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority") db = client['telegram_bot_db'] users_collection = db['users']

Telegram Bot Setup

api_id = "28609964" api_hash = "3236bdf1e11a0fb8091495e083857621" bot_token = "7614916680:AAEVOATGqMzDOfIpDCJ36_1K_7ONnt2vXis"

app = Client("force_subscribe_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

Channels for Force Subscribe

force_subscribe_channels = [ "https://t.me/+G-y93SIcREY3YTg9", "https://t.me/Jalwagame_Hack", "https://t.me/sureshot101game" ]

Channel usernames for checking subscription

channel_usernames = [ "@G_y93SIcREY3YTg9", "@Jalwagame_Hack", "@sureshot101game" ]

Admin Details

owner_id = 7168729089 owner_username = "@INNOCENT_FUCKER"

Logging setup

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) logger = logging.getLogger(name)

Helper Functions

def check_force_subscribe(user_id): try: for username in channel_usernames: member = app.get_chat_member(username, user_id) if member.status not in ['member', 'administrator', 'creator']: return False return True except: return False

Start Command

@app.on_message(filters.command("start")) def start(client, message): user_id = message.from_user.id user_name = message.from_user.username user_first_name = message.from_user.first_name

existing_user = users_collection.find_one({"user_id": user_id})
if not existing_user:
    users_collection.insert_one({
        "user_id": user_id,
        "username": user_name,
        "first_name": user_first_name,
        "joined_channels": []
    })

if check_force_subscribe(user_id):
    send_main_menu(user_id, user_first_name)
else:
    send_force_subscribe(user_id)

Send Main Menu

def send_main_menu(user_id, name): app.send_message( user_id, f"Welcome {name}! \nYou are successfully subscribed to all required channels.", reply_markup=InlineKeyboardMarkup([ [InlineKeyboardButton("Join 91 Club", url="https://www.dmwin3.com/#/register?invitationCode=137222244286")], [InlineKeyboardButton("Become Agent (₹500 - ₹50,000/day)", callback_data="agent_work")], [InlineKeyboardButton("Get Predictions", callback_data="predictions")] ]) )

Send Force Subscribe Menu

def send_force_subscribe(user_id): app.send_message( user_id, "Aapko neeche diye gaye sabhi channel join karne honge:", reply_markup=InlineKeyboardMarkup([ [ InlineKeyboardButton("🔗 Channel 1", url=force_subscribe_channels[0]), InlineKeyboardButton("🔗 Channel 2", url=force_subscribe_channels[1]) ], [ InlineKeyboardButton("🔗 Channel 3", url=force_subscribe_channels[2]), InlineKeyboardButton("✅ Maine Join Kar Liya", callback_data="check_sub") ] ]) )

Handle "✅ Maine Join Kar Liya"

@app.on_callback_query(filters.regex("check_sub")) def check_subscription_callback(client, callback_query: CallbackQuery): user_id = callback_query.from_user.id if check_force_subscribe(user_id): send_main_menu(user_id, callback_query.from_user.first_name) else: callback_query.answer("Abhi tak aapne sabhi channels join nahi kiye.", show_alert=True)

Handle Agent Work

@app.on_callback_query(filters.regex("agent_work")) def agent_work(client, callback_query): user_id = callback_query.from_user.id app.send_message( user_id, "Agent banne ke liye @INNOCENT_FUCKER se contact karein.\nDaily earning ₹500 - ₹50,000." )

Handle Predictions

@app.on_callback_query(filters.regex("predictions")) def predictions(client, callback_query): user_id = callback_query.from_user.id app.send_message( user_id, "Aaj ke predictions:\nColor: Red\nTrick: Odd\nDigit: 5\nGood Luck!" )

Broadcast (only for owner)

@app.on_message(filters.command("broadcast") & filters.user(owner_id)) def broadcast(client, message): text = message.text.split(maxsplit=1)[1] for user in users_collection.find(): try: app.send_message(user["user_id"], text) except: continue app.send_message(owner_id, "Broadcast message sent successfully!")

Stats Command

@app.on_message(filters.command("stats") & filters.user(owner_id)) def stats(client, message): total_users = users_collection.count_documents({}) active_users = 0 for user in users_collection.find(): if check_force_subscribe(user["user_id"]): active_users += 1 app.send_message( owner_id, f"Total Users: {total_users}\nActive Users: {active_users}\nRegistered in 91 Club: {total_users}" )

Run Bot

if name == "main": app.run()

