from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from VOTE.core.database import Database
import datetime

db = Database()

async def handle_vote(client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("**Usage:** `/vote @channelusername`")

    channel_username = message.command[1].strip('@')
    try:
        chat = await client.get_chat(f"@{channel_username}")
        if chat.type not in ["channel", "supergroup"]:
            return await message.reply_text("❌ Only channels and supergroups are supported!")

        # Check bot admin status
        bot_member = await client.get_chat_member(chat.id, client.me.id)
        if bot_member.status not in ["administrator", "creator"]:
            return await message.reply_text(f"⚠️ Please make me admin in @{channel_username} first!")

        # Create poll
        poll_id = f"{chat.id}_{message.from_user.id}"
        poll_data = {
            "poll_id": poll_id,
            "channel_id": chat.id,
            "channel_username": channel_username,
            "creator_id": message.from_user.id,
            "vote_count": 0,
            "subscriber_only": True,
            "created_at": datetime.datetime.now()
        }
        db.create_poll(poll_data)
        
        participation_link = f"https://t.me/{client.me.username}?start={channel_username}"
        
        await message.reply_photo(
            photo="https://graph.org/file/46412deeaab8e8b8c0b06-3bc9b2e0ae531f7b9c.jpg",
            caption=f"**✅ VOTE POLL CREATED**\n\n"
                    f"Channel: @{channel_username}\n"
                    f"Vote Type: Subscriber-only\n\n"
                    f"Participation Link:\n{participation_link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("VOTE NOW", url=participation_link)],
                [InlineKeyboardButton("View Channel", url=f"https://t.me/{channel_username}")]
            ])
        )

    except Exception as e:
        await message.reply_text(f"🚫 Error: {str(e)}")

async def handle_vote_action(bot: VoteBot, callback_query: CallbackQuery):
    poll_id = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    
    poll = db.get_poll(poll_id)
    if not poll:
        return await callback_query.answer("Poll not found!", show_alert=True)

    # Check if already voted
    existing_vote = db.users.find_one({"user_id": user_id, "poll_id": poll_id})
    if existing_vote:
        return await callback_query.answer("You've already voted!", show_alert=True)

    # Check channel subscription if subscriber-only
    if poll.get("subscriber_only", True):
        is_subscribed = await bot._check_subscription(user_id, poll["channel_username"])
        if not is_subscribed:
            return await callback_query.answer(
                "You must join the channel to vote!", 
                show_alert=True
            )

    # Process vote
    db.update_vote_count(poll_id, increment=True)
    db.add_voter(user_id, poll_id, poll["channel_id"])
    
    # Update button
    updated_poll = db.get_poll(poll_id)
    await callback_query.message.edit_reply_markup(
        InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"👍 VOTES: {updated_poll['vote_count']}", 
                callback_data=f"vote_{poll_id}"
            )
        ]])
    )
    await callback_query.answer("Your vote has been counted!")
