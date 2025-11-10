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

    session = SessionLocal()

    try:
        msg = add_telegram_user(session, chat_id, username)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    finally:
        session.close()

    await update.message.reply_text(f"👋 Hello {username or 'there'}!\n{msg}")


async def help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lists the available commands
    """
    assert update.message

    await update.message.reply_text(
        "/list\n/listsubs\n/add <redditor>\n/addsub <subreddit>\n/remove <redditor>\n/mute <redditor> <time> <unit>\n/unmute <redditor>\n/rate <redditor> <amount>"
    )


"""REDDITOR COMMANDS"""


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list all the watched redditors. /list
    """
    assert update.message
    assert update.effective_chat

    session = SessionLocal()

    try:
        user_ratings = get_watched_users_with_rating(session)
        users = [f"{user} {rating*'🚀'}" for user, rating in user_ratings]

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    finally:
        session.close()

    user_list = "\n".join(users) or "No users being watched"

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"List of redditors:\n{user_list}"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to add a redditor to be watched. Rating system needs to be implemented. /add <redditor> *<rating>*
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 1:
        await update.message.reply_text(
            "🤪 Please use the commands correctly you dummy 🤪\n/add <redditor>\nCase sensitive btw...."
        )
        return

    redditor = context.args[0]
    exists = await asyncio.to_thread(redditor_exists, redditor)

    if not exists:
        await update.message.reply_text("Sorry that redditor does not exist")
        return

    session = SessionLocal()

    try:
        add_watched_user(session, redditor)

    except UserAlreadyActiveError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added {redditor}"
    )


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to deactivate a redditor. /remove <redditor>
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 1:
        await update.message.reply_text(
            "👺Just try to use the commands as intended please👺\n/remove <redditor>"
        )
        return

    redditor = context.args[0]
    session = SessionLocal()

    try:
        remove_watched_user(session, redditor)

    except UserNotFoundError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except UserAlreadyInactiveError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected error: {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"removed {redditor}"
    )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to mute a reditor (logic in reddit client not implemented). /mute <redditor> <time> *h, d, y*
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 3:
        await update.message.reply_text(
            "Okay i understand missusing this command. It's pretty dogshit💩\n/mute <redditor> <time> <unit>\nunits h: hours, d: days, y: years"
        )
        return

    redditor = context.args[0]
    mute_time = int(context.args[1])
    timescale = (
        60 * 60
        if context.args[2] == "h"
        else (
            60 * 60 * 24
            if context.args[2] == "d"
            else 60 * 60 * 24 * 365 if context.args[2] == "y" else 60
        )
    )

    session = SessionLocal()

    try:
        mute_user(session, redditor, mute_time * timescale)

    except UserNotFoundError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except UserAlreadyMutedError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"muted {redditor}"
    )


async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Unmute a Redditor
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 1:
        await update.message.reply_text(
            "This one is easy to use....🤷\n/unmute <redditor>"
        )
        return

    redditor = context.args[0]
    session = SessionLocal()

    try:
        unmute_user(session, redditor)

    except UserNotFoundError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"unmuted {redditor}"
    )


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to rate a redditor. Logic not implemented. /rate <redditor> <int>
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 2:
        await update.message.reply_text(
            "You can change the rating of specified redditor🤓\n/rate <redditor> <int>\nnegative or positiv int can be used"
        )
        return

    redditor = context.args[0]
    rating = context.args[1]
    session = SessionLocal()

    try:
        rate_user(session, redditor, int(rating))
        rating = get_rating(session, redditor)

    except UserNotFoundError as e:
        await update.message.reply_text(f"⚠️{e}")
        return

    except Exception as e:
        await update.message.reply_text(f"Unexpected Error: {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"changed rating of {redditor} {rating * '🚀'}",
    )


"""SUBREDDIT COMMANDS"""


async def listsubs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Implement listsubs command for subreddits
    """
    assert update.message
    assert update.effective_chat

    session = SessionLocal()

    try:
        subreddits = get_watched_subreddits(session)
        subreddits = [sub for sub in subreddits]

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    finally:
        session.close()

    subreddits_list = "\n".join(subreddits) or "No subreddits beeing watched"

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"List of subreddits:\n{subreddits_list}"
    )


async def addsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to add a Subreddit to be watched. /addsub <subreddit>
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 1:
        await update.message.reply_text(
            "🤪 Please use the commands correctly you dummy 🤪\n/add <subreddit>\nCase sensitive btw...."
        )
        return

    subreddit = context.args[0]
    exists = await asyncio.to_thread(subreddit_exists, subreddit)

    if not exists:
        await update.message.reply_text("Sorry that Subreddit does not exist")
        return

    session = SessionLocal()

    try:
        add_watched_reddit(session, subreddit)

    except SubredditAlreadyActiveError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"Unexpected Error: {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added sub: {subreddit}"
    )


async def rmsub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Deactivate a subreddit
    """
    assert update.message
    assert update.effective_chat

    if context.args is None or len(context.args) != 1:
        await update.message.reply_text("Usage /rmsub <subreddit>")
        return

    subreddit = context.args[0]
    session = SessionLocal()

    try:
        remove_watched_reddit(session, subreddit)

    except SubredditNotFoundError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except SubredditAlreadyInactiveError as e:
        await update.message.reply_text(f"⚠️ {e}")
        return

    except Exception as e:
        await update.message.reply_text(f"⚠️ Unexpected Error: {e}")
        return

    finally:
        session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"removed {subreddit}"
    )


async def send_pending_notifications(bot) -> None:
    """
    Background task to check DB for new notifications and send them.
    """
    while True:
        session = SessionLocal()

        try:
            new_items = get_pending_notifications(session)
            chat_ids = get_active_telegram_users(session)

            for note in new_items:

                try:
                    rating = get_rating(session, cast(str, note.author))

                except UserNotFoundError as e:
                    print(f"⚠️{e}")
                    continue

                except Exception as e:
                    print(f"Unexpected Erorr: {e}")
                    continue

                message = (
                    f"📢 New {note.type} by {note.author}{'🚀' * rating}\n{note.url}"
                )

                for chat_id in chat_ids:
                    try:
                        await bot.send_message(chat_id=chat_id, text=message)

                    except Exception as e:
                        print(f"Failed to send to {chat_id}: {e}")

                note.delivered = True  # type: ignore[attr-defined]

            safe_commit(session)

        finally:
            session.close()

        await asyncio.sleep(5)


if __name__ == "__main__":

    assert TELEGRAM_BOT_TOKEN

    init_db()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    list_handler = CommandHandler("list", list)
    add_handler = CommandHandler("add", add)
    remove_handler = CommandHandler("remove", remove)
    mute_handler = CommandHandler("mute", mute)
    unmute_handler = CommandHandler("unmute", unmute)
    rate_handler = CommandHandler("rate", rate)
    addsub_handler = CommandHandler("addsub", addsub)
    listsubs_handler = CommandHandler("listsubs", listsubs)
    rmsub_handler = CommandHandler("rmsub", rmsub)

    app.add_handlers(
        [
            start_handler,
            help_handler,
            list_handler,
            add_handler,
            mute_handler,
            unmute_handler,
            rate_handler,
            remove_handler,
            addsub_handler,
            listsubs_handler,
            rmsub_handler,
        ]
    )

    async def on_startup(app):
        asyncio.create_task(send_pending_notifications(app.bot))

    app.post_init = on_startup

    app.run_polling()
