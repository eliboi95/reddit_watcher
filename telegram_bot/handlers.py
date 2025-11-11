import asyncio
from typing import cast
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config.config import TELEGRAM_BOT_TOKEN
from reddit_bot.reddit_client import redditor_exists, subreddit_exists
from db.exceptions import (
    RedditorNotFoundInDBError,
    RedditorAlreadyActiveError,
    RedditorAlreadyInactiveError,
    RedditorAlreadyMutedError,
    SubredditAlreadyActiveError,
    SubredditAlreadyInactiveError,
    SubredditNotFoundError,
)
from db.session import SessionLocal, init_db
from db.crud import (
    get_rating,
    remove_watched_subreddit,
    remove_watched_redditor,
    add_watched_redditor,
    get_pending_notifications,
    add_telegram_user,
    get_active_telegram_users_chat_ids,
    add_watched_subreddit,
    get_watched_subreddits,
    set_redditor_mute_timer,
    unset_redditor_mute_timer,
    set_redditor_rating,
    get_watched_redditors_with_rating,
    safe_commit,
)
from service import list_redditors_with_rating, register_telegram_user, get_help

"""GENERAL COMMANDS"""


async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to add the User to active telegram users in DB.
    """

    assert update.message
    assert update.effective_chat
    assert update.effective_user

    chat_id = update.effective_chat.id
    username = update.effective_user.username

    try:
        msg = register_telegram_user(chat_id, username)

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Sorry we have encountered an unexpected Error"
        )
        return

    await update.message.reply_text(f"👋 Hello {username or 'there'}!\n{msg}")


async def help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to get a list of all available commands.
    """
    assert update.message

    try:
        msg = get_help()

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Sorry we have encountered an unexpected Error"
        )
        return

    await update.message.reply_text(f"🛠️ Available Bot Commands:\n{msg}")


"""REDDITOR COMMANDS"""


async def list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list all Redditors that are beeing watched.
    """
    assert update.message

    try:
        msg = list_redditors_with_rating()

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Sorry we have encountered an unexpected Error"
        )
        return

    await update.message.reply_text(f"📋 Watched Redditors 👀:\n{msg}")
