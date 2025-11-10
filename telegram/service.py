import asyncio
from typing import cast
from db import exceptions
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config.config import TELEGRAM_BOT_TOKEN
from reddit.reddit_client import redditor_exists, subreddit_exists
from db.exceptions import (
    UserNotFoundError,
    UserAlreadyActiveError,
    UserAlreadyInactiveError,
    UserAlreadyMutedError,
    SubredditAlreadyActiveError,
    SubredditAlreadyInactiveError,
    SubredditNotFoundError,
)
from db.session import SessionLocal, init_db
from db.crud import (
    get_rating,
    remove_watched_reddit,
    remove_watched_user,
    add_watched_user,
    get_pending_notifications,
    add_telegram_user,
    get_active_telegram_users,
    add_watched_reddit,
    get_watched_subreddits,
    mute_user,
    unmute_user,
    rate_user,
    get_watched_users_with_rating,
    safe_commit,
)

"""GENERAL COMMANDS"""


def register_telegram_user(chat_id: int, username: str) -> str:
    session = SessionLocal()

    try:
        msg = add_telegram_user(session, chat_id, username)
        return msg
    finally:
        session.close()
