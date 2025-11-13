import os
from dotenv import load_dotenv

"""
Loading all env variables
"""
dotenv_path = os.path.expanduser("~/reddit_watcher/env/bot.env")
load_dotenv(dotenv_path)

print("TELEGRAM_BOT_TOKEN:", os.getenv("TELEGRAM_BOT_TOKEN"))

# Reddit API
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "RedditWatcher/1.0")

# Telegram API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Poll intervals
REDDIT_POLL_INTERVAL = 5

"""
Database URL
"""
DB_URL = "sqlite:///reddit_watcher.db"
