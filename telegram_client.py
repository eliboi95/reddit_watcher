import asyncio
from telegram import Update
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from config import TELEGRAM_BOT_TOKEN
from db.models import (
    remove_watched_user,
    add_watched_user,
    get_watched_users,
    get_pending_notifications,
    add_telegram_user,
    get_active_telegram_users,
    add_watched_reddit,
    safe_commit,
    SessionLocal,
    init_db,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot Command so the Chatter gets added to the active telegram users in DB
    """
    chat_id = update.effective_chat.id
    username = update.effective_user.username

    session = SessionLocal()
    msg = add_telegram_user(session, chat_id, username)
    session.close()

    await update.message.reply_text(f"👋 Hello {username or 'there'}!\n{msg}")


async def list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot Command to list all the watched redditors. /list
    """
    session = SessionLocal()
    users = get_watched_users(session)
    session.close()

    user_list = "\n".join(users) or "No users being watched"
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"List of redditors:\n{user_list}"
    )


async def listsubs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    TODO: Implement listsubs command for subreddits
    """


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot Command to add a redditor to be watched. Rating system needs to be implemented. /add <redditor> *<rating>*
    """

    redditor = update.message.text.split(" ")[1:2][0]
    session = SessionLocal()
    add_watched_user(session, redditor)
    session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added {redditor}"
    )


async def addsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot Command to add a Subreddit to be watched. /addsub <subreddit>
    """
    subreddit = update.message.text.split(" ")[1:2][0]
    session = SessionLocal()
    add_watched_reddit(session, subreddit)
    session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"added sub: {subreddit}"
    )


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram Bot Command to deactivate a redditor. /remove <redditor>
    """
    redditor = update.message.text.split(" ")[1:2][0]
    session = SessionLocal()
    remove_watched_user(session, redditor)
    session.close()

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"removed {redditor}"
    )


async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    TODO: Telegram Bot Command to mute a reditor (logic in reddit client not implemented). /mute <redditor> <time> *h, d, y*
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="muted {redditor}"
    )


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    TODO: Telegram Bot Command to rate a redditor. Logic not implemented. /rate <redditor> <int>
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="changed rating"
    )


async def send_pending_notifications(bot):
    """
    Background task to check DB for new notifications and send them.
    """
    while True:
        session = SessionLocal()
        new_items = get_pending_notifications(session)
        chat_ids = get_active_telegram_users(session)

        for note in new_items:
            message = f"📢 New {note.type} by {note.author}\n{note.url}"
            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id=chat_id, text=message)
                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}")

            note.delivered = True

        safe_commit(session)
        session.close()
        await asyncio.sleep(30)


if __name__ == "__main__":

    init_db()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    list_handler = CommandHandler("list", list)
    add_handler = CommandHandler("add", add)
    remove_handler = CommandHandler("remove", remove)
    mute_handler = CommandHandler("mute", mute)
    rate_handler = CommandHandler("rate", rate)
    addsub_handler = CommandHandler("addsub", addsub)

    app.add_handlers(
        [
            start_handler,
            list_handler,
            add_handler,
            mute_handler,
            rate_handler,
            remove_handler,
            addsub_handler,
        ]
    )

    async def on_startup(app):
        asyncio.create_task(send_pending_notifications(app.bot))

    app.post_init = on_startup

    app.run_polling()
