from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from config import Config
from VOTE.core.database import Database
import logging
import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoteBot:
    def __init__(self):
        self.app = Client(
            "my_vote_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="VOTE/plugins")
        )
        self.db = Database()
        self._register_middleware()
        self._register_handlers()

    async def _check_subscription(self, user_id: int, chat: str):
        """Check if user is subscribed to a channel/group"""
        try:
            await self.app.get_chat_member(chat, user_id)
            return True
        except UserNotParticipant:
            try:
                chat_info = await self.app.get_chat(chat)
                invite_link = chat_info.invite_link if hasattr(chat_info, 'invite_link') else f"https://t.me/{chat}"
                
                await self.app.send_photo(
                    chat_id=user_id,
                    photo="https://graph.org/file/46412deeaab8e8b8c0b06-3bc9b2e0ae531f7b9c.jpg",
                    caption=f"⚠️ You must join @{chat} to continue!\n\nAfter joining, click the button below.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Join Channel", url=invite_link)],
                        [InlineKeyboardButton("✅ Verify Join", callback_data=f"checksub_{chat}")]
                    ])
                )
                return False
            except Exception as e:
                logger.error(f"Subscription check error for {chat}: {e}")
                return False

    def _register_middleware(self):
        @self.app.on_message(filters.incoming & filters.private, group=-1)
        async def force_subscribe(client: Client, message: Message):
            if not await self._check_subscription(message.from_user.id, Config.UPDATE_CHANNEL):
                await message.stop_propagation()

    def _register_handlers(self):
        from plugins import start, vote
        
        # Command handlers
        self.app.on_message(filters.command("start") & filters.private)(start.handle_start)
        self.app.on_message(filters.command("vote") & filters.private)(vote.handle_vote)
        
        # Callback handlers
        @self.app.on_callback_query(filters.regex(r"^checksub_"))
        async def verify_subscription(client: Client, callback_query: CallbackQuery):
            chat = callback_query.data.split("_")[1]
            if await self._check_subscription(callback_query.from_user.id, chat):
                await callback_query.message.edit_text("✅ Verified! You can now continue.")
            else:
                await callback_query.answer("You haven't joined yet!", show_alert=True)

        @self.app.on_callback_query(filters.regex(r"^vote_"))
        async def handle_vote_callback(client: Client, callback_query: CallbackQuery):
            await vote.handle_vote_action(self, callback_query)

    def run(self):
        self.app.run()
