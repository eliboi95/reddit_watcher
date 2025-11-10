import asyncio
from typing import cast
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
from service import register_telegram_user

"""GENERAL COMMANDS"""


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command so the Chatter gets added to the active telegram users in DB
    """

    assert update.message
    assert update.effective_chat
    assert update.effective_user

    chat_id = update.effective_chat.id
    username = update.effective_user.username

    try:
        msg = register_telegram_user(chat_id, username)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    await update.message.reply_text(f"👋 Hello {username or 'there'}!\n{msg}")
