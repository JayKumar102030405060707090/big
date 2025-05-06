from .bot import VoteBot

def start_bot():
    bot = VoteBot()
    bot.run()

if __name__ == "__main__":
    start_bot()
