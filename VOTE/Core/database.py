from pymongo import MongoClient
from config import Config
from datetime import datetime

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client["vote_bot_db"]
        self.polls = self.db.polls
        self.users = self.db.users

    def create_poll(self, poll_data):
        return self.polls.insert_one(poll_data)

    def get_poll(self, poll_id):
        return self.polls.find_one({"poll_id": poll_id})

    def update_vote_count(self, poll_id, increment=True):
        return self.polls.update_one(
            {"poll_id": poll_id},
            {"$inc": {"vote_count": 1 if increment else -1}}
        )

    def add_voter(self, user_id, poll_id, channel_id):
        return self.users.insert_one({
            "user_id": user_id,
            "poll_id": poll_id,
            "channel_id": channel_id,
            "voted_at": datetime.now()
        })

    def remove_voter(self, user_id, poll_id):
        return self.users.delete_one({
            "user_id": user_id,
            "poll_id": poll_id
        })
