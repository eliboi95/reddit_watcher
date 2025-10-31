import os
from dotenv import load_dotenv

"""
Loading all env variables
"""

load_dotenv()
# Reddit API
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditWatcher/1.0")

# Telegram API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Poll intervals
REDDIT_POLL_INTERVAL = 5
TELEGRAM_POLL_INTERVAL = 5
