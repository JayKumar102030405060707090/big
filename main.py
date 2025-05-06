import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import UserNotParticipant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot configuration with YOUR CREDENTIALS
API_ID = 12380656
API_HASH = "d927c13beaaf5110f25c505b7c071273"
BOT_TOKEN = "7745907443:AAG3JwUAsQ-VpTjSzfssKy16BcZivppojV0"
UPDATE_CHANNEL = "@KomalmusicUpdate"  # Create this channel for force subscribe
BOT_OWNER = 7168729089  # Your owner ID
MONGODB_URI = "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority"

# Database setup
from pymongo import MongoClient
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["vote_bot_db"]
polls_collection = db["polls"]
users_collection = db["users"]

# Initialize Pyrogram client
app = Client(
    "my_vote_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Helper functions
async def force_subscribe(user_id):
    try:
        user = await app.get_chat_member(UPDATE_CHANNEL, user_id)
        if user.status in ["left", "kicked"]:
            return False
        return True
    except UserNotParticipant:
        return False
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

async def update_vote_count(poll_id, user_id, channel_id, increment=True):
    try:
        poll = polls_collection.find_one({"poll_id": poll_id})
        if not poll:
            return False
        
        user_voted = users_collection.find_one({
            "user_id": user_id,
            "poll_id": poll_id
        })
        
        if increment:
            # Check if user is subscribed to channel
            try:
                member = await app.get_chat_member(channel_id, user_id)
                if member.status in ["left", "kicked"]:
                    return "not_subscribed"
            except Exception as e:
                logger.error(f"Subscription check error: {e}")
                return "error"
            
            if user_voted:
                return "already_voted"
            
            # Add vote
            polls_collection.update_one(
                {"poll_id": poll_id},
                {"$inc": {"vote_count": 1}}
            )
            users_collection.insert_one({
                "user_id": user_id,
                "poll_id": poll_id,
                "channel_id": channel_id,
                "voted_at": datetime.datetime.now()
            })
        else:
            # Remove vote
            if user_voted:
                polls_collection.update_one(
                    {"poll_id": poll_id},
                    {"$inc": {"vote_count": -1}}
                )
                users_collection.delete_one({
                    "user_id": user_id,
                    "poll_id": poll_id
                })
        
        return True
    except Exception as e:
        logger.error(f"Vote update error: {e}")
        return "error"

# Start command with force subscribe
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if user is subscribed to update channel
    is_subscribed = await force_subscribe(user_id)
    if not is_subscribed:
        await message.reply_text(
            f"**⚠️ Please Join My Updates Channel to use this Bot!**\n\n"
            f"Due to Telegram Users Traffic, Only Channel Subscribers can use the Bot!\n\n"
            f"👉 {UPDATE_CHANNEL}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("JOIN UPDATE CHANNEL", url=f"https://t.me/{UPDATE_CHANNEL[1:]}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_sub")]
            ])
        )
        return
    
    # Check if start parameter contains channel username
    if len(message.command) > 1:
        channel_username = message.command[1]
        try:
            chat = await client.get_chat(channel_username)
            poll_id = f"{chat.id}_{chat.id}"  # Unique poll ID
            
            poll = polls_collection.find_one({"poll_id": poll_id})
            if not poll:
                await message.reply_text("No active poll found for this channel!")
                return
            
            # Send voting interface
            await message.reply_text(
                f"**Vote for {channel_username}**\n\n"
                "Click the button below to vote:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"VOTES: {poll['vote_count']}", callback_data=f"vote_{poll_id}")]
                ])
            )
            return
        except Exception as e:
            logger.error(f"Error handling start parameter: {e}")
    
    # Normal start command
    await message.reply_text(
        "**🏆 VOTE BOT**\n\n"
        "➤ TO CREATE AUTO VOTE POLL FOR YOUR CHANNEL, USE /vote COMMAND.\n\n"
        "➤ FEATURES:\n"
        "- Subscriber-only voting\n"
        "- Real-time vote counting\n"
        "- Vote management\n\n"
        f"OWNER: {BOT_OWNER}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Me To Your Channel", url=f"https://t.me/{client.me.username}?startgroup=true")],
            [InlineKeyboardButton("📢 Updates Channel", url=f"https://t.me/{UPDATE_CHANNEL[1:]}")]
        ])
    )

# Handle subscription check callback
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    is_subscribed = await force_subscribe(user_id)
    
    if is_subscribed:
        await callback_query.message.edit_text(
            "✅ Thanks for joining! Now you can use the bot.\n\n"
            "Use /vote command to create a new poll."
        )
    else:
        await callback_query.answer("You haven't joined the channel yet!", show_alert=True)

# Vote command to create new poll
@app.on_message(filters.command("vote"))
async def create_poll(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Force subscribe check
    is_subscribed = await force_subscribe(user_id)
    if not is_subscribed:
        await message.reply_text(
            f"**Please join our updates channel first:** {UPDATE_CHANNEL}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{UPDATE_CHANNEL[1:]}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_sub")]
            ])
        )
        return
    
    if len(message.command) < 2:
        await message.reply_text(
            "**Enter Channel Username With @**\n\n"
            "Example: `/vote @channelusername`"
        )
        return
    
    channel_username = message.command[1].lower()
    try:
        chat = await client.get_chat(channel_username)
        if chat.type not in ["channel", "supergroup"]:
            await message.reply_text("This is not a valid channel or group!")
            return
        
        # Check if bot is admin in channel
        member = await client.get_chat_member(chat.id, client.me.id)
        if member.status not in ["administrator", "creator"]:
            await message.reply_text("I need to be admin in that channel to create polls!")
            return
        
        # Create new poll
        poll_id = f"{chat.id}_{chat.id}"  # Using channel ID for uniqueness
        poll_data = {
            "poll_id": poll_id,
            "channel_id": chat.id,
            "channel_username": channel_username,
            "creator_id": user_id,
            "vote_count": 0,
            "created_at": datetime.datetime.now()
        }
        
        # Check if poll already exists
        existing_poll = polls_collection.find_one({"poll_id": poll_id})
        if existing_poll:
            participation_link = f"https://t.me/{client.me.username}?start={channel_username}"
            await message.reply_text(
                f"**Poll already exists for this channel!**\n\n"
                f"Participation Link:\n{participation_link}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("VOTE NOW", url=participation_link)]
                ])
            )
            return
        
        polls_collection.insert_one(poll_data)
        
        participation_link = f"https://t.me/{client.me.username}?start={channel_username}"
        
        await message.reply_text(
            f"**➤ SUCCESSFULLY VOTE-POLL CREATED.**\n"
            f"• CHAT: {channel_username}\n\n"
            f"• EMOJI: 👍\n\n"
            f"**Participation Link:**\n{participation_link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("VOTE NOW", url=participation_link)],
                [InlineKeyboardButton("VIEW POLL", callback_data=f"view_{poll_id}")]
            ])
        )
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

# Handle vote button clicks
@app.on_callback_query(filters.regex(r"^vote_"))
async def handle_vote_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    poll_id = callback_query.data.split("_", 1)[1]
    
    poll = polls_collection.find_one({"poll_id": poll_id})
    if not poll:
        await callback_query.answer("Poll not found!", show_alert=True)
        return
    
    channel_id = poll["channel_id"]
    
    # Check subscription status
    try:
        member = await client.get_chat_member(channel_id, user_id)
        if member.status in ["left", "kicked"]:
            await callback_query.answer(
                "You must subscribe to the channel to vote!",
                show_alert=True
            )
            
            # Send message with join button
            await callback_query.message.reply_text(
                f"**You must join this channel to vote:**\n{poll['channel_username']}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Join Channel", url=f"https://t.me/{poll['channel_username'][1:]}")],
                    [InlineKeyboardButton("✅ I've Joined", callback_data=f"resume_vote_{poll_id}")]
                ])
            )
            return
    except Exception as e:
        logger.error(f"Subscription check error: {e}")
        await callback_query.answer("Error checking subscription!", show_alert=True)
        return
    
    # Update vote
    result = await update_vote_count(poll_id, user_id, channel_id)
    
    if result == "already_voted":
        await callback_query.answer("You've already voted!", show_alert=True)
    elif result == True:
        # Get updated vote count
        updated_poll = polls_collection.find_one({"poll_id": poll_id})
        vote_count = updated_poll["vote_count"]
        
        # Edit message with new count
        await callback_query.message.edit_reply_markup(
            InlineKeyboardMarkup([
                [InlineKeyboardButton(f"VOTES: {vote_count}", callback_data=f"vote_{poll_id}")]
            ])
        )
        await callback_query.answer("✓ Vote counted!")
    else:
        await callback_query.answer("Error processing your vote!", show_alert=True)

# Handle resume vote after joining channel
@app.on_callback_query(filters.regex(r"^resume_vote_"))
async def resume_vote_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    poll_id = callback_query.data.split("_", 2)[2]
    
    poll = polls_collection.find_one({"poll_id": poll_id})
    if not poll:
        await callback_query.answer("Poll not found!", show_alert=True)
        return
    
    # Check if user joined the channel
    try:
        member = await client.get_chat_member(poll["channel_id"], user_id)
        if member.status in ["left", "kicked"]:
            await callback_query.answer("You still haven't joined the channel!", show_alert=True)
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await callback_query.answer("Error verifying your subscription!", show_alert=True)
        return
    
    # Proceed with voting
    result = await update_vote_count(poll_id, user_id, poll["channel_id"])
    
    if result == True:
        updated_poll = polls_collection.find_one({"poll_id": poll_id})
        await callback_query.message.edit_text(
            f"✅ Thanks for joining {poll['channel_username']}!\n"
            f"Your vote has been counted.\n\n"
            f"Total Votes: {updated_poll['vote_count']}"
        )
    else:
        await callback_query.answer("Error processing your vote!", show_alert=True)

# Run the bot
if __name__ == "__main__":
    logger.info("Starting My Vote Bot...")
    app.run()
