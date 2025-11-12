import asyncio
from typing import cast
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config.config import TELEGRAM_BOT_TOKEN
from db.models import Notification
from telegram_bot.service import (
    add_redditor_to_db,
    add_subreddit_to_db,
    close_pending_notifications,
    list_active_telegram_users_chat_ids,
    list_pending_notifications,
    list_redditors_with_rating,
    list_subreddits,
    mute_redditor,
    rate_redditor,
    register_telegram_user,
    get_help,
    remove_redditor_from_db,
    remove_subreddit_from_db,
    unmute_redditor,
    get_rating_of_redditor,
)
import os

print(os.path.exists(os.path.expanduser("~/reddit_watcher/env/bot.env")))
TIME_UNITS = ["hours", "days", "years"]

"""Conversation States"""
# Add redditors conversation
ASK_FOR_REDDITORS_TO_ADD = 0

# Remove redditors conversation
ASK_FOR_REDDITORS_TO_REMOVE = 0

# Mute Redditor conversation
ASK_FOR_REDDITOR_TO_MUTE = 0
ASK_FOR_TIME_UNIT = 1
ASK_FOR_DURATION = 2

# Unmute Redditor conversation
ASK_FOR_REDDITOR_TO_UNMUTE = 0

# Rate redditor conversation
ASK_FOR_REDDITOR_TO_RATE = 0
ASK_FOR_AMOUNT_TO_RATE = 1

# Add subreddit conversation
ASK_FOR_SUBREDDITS_TO_ADD = 0

# Remove subreddit conversation
ASK_FOR_SUBREDDITS_TO_REMOVE = 0

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


async def cancel_conversation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Telegram Bot Command to cancel any conversation Command
    """
    assert update.message

    await update.message.reply_text("🚨 Command canceled 🚨")
    return ConversationHandler.END


"""REDDITOR COMMANDS"""


async def list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list all Redditors that are being watched.
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


async def add_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /add Command conversation
    """
    assert update.message
    await update.message.reply_text(
        "Who do you want to add?\nSend me a list of redditors separated by spaces.\nRedditor1 Redditor2 Redditor3"
    )

    return ASK_FOR_REDDITORS_TO_ADD


async def add_redditors(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the Redditors in a str, splitting it and for each Redditor try to add it to the db.
    Respond to User with the Redditors that were added and those that failed.
    """
    assert update.message

    if not update.message.text:
        await update.message.reply_text(
            "I need at least one redditor name to continue 🙂"
        )
        return ASK_FOR_REDDITORS_TO_ADD

    redditors = update.message.text.split()
    added = []
    failed = []

    for redditor in redditors:
        try:
            await add_redditor_to_db(redditor)
            added.append(redditor)

        except Exception as e:
            failed.append(redditor)

    msg = ""

    if added:
        msg += f"✅ Added:\n{'\n'.join(added)}\n"
    if failed:
        msg += f"🚨 Failed to add:\n{'\n'.join(failed)}\n"

    await update.message.reply_text(msg)
    return ConversationHandler.END


async def remove_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /remove Command conversation
    """
    assert update.message

    await update.message.reply_text(
        "Who do you want to remove?\nSend me a list of redditors separated by spaces.\nRedditor1 Redditor2 Redditor3"
    )
    return ASK_FOR_REDDITORS_TO_REMOVE


async def remove_redditors(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the Redditors in a str, splitting it and for each Redditor try to remove it from the db.
    Respond to User with the Redditors that were removed and those that failed.
    """
    assert update.message

    if not update.message.text:
        await update.message.reply_text(
            "I need at least one redditor name to continue 🙂"
        )
        return ASK_FOR_REDDITORS_TO_REMOVE

    redditors = update.message.text.split()
    removed = []
    failed = []

    for redditor in redditors:
        try:
            remove_redditor_from_db(redditor)
            removed.append(redditor)

        except Exception as e:
            failed.append(redditor)

    msg = ""

    if removed:
        msg += f"✅ Removed: \n{'\n'.join(removed)}\n"
    if failed:
        msg += f"🚨 Failed to remove:\n{'\n'.join(failed)}\n"

    await update.message.reply_text(msg)
    return ConversationHandler.END


async def mute_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of /mute Command conversation
    """
    assert update.message

    await update.message.reply_text("Which Redditor do you want to mute?")
    return ASK_FOR_REDDITOR_TO_MUTE


async def mute_choose_unit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Save Redditor to context and get Unit of time from User h/d/y
    """
    assert context.user_data
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need a redditor name to continue 🙂")
        return ASK_FOR_REDDITOR_TO_MUTE

    redditor = update.message.text.strip()
    context.user_data["redditor"] = redditor

    reply_keyboard = [TIME_UNITS]
    await update.message.reply_text(
        f"Ok, which unit of time are we using to mute {redditor}?",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )
    return ASK_FOR_TIME_UNIT


async def mute_ask_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 2: Getting the amount of time from User
    """
    assert update.message
    assert context.user_data

    if not update.message.text:
        await update.message.reply_text("I need a Time Unit to continue 🙂")
        return ASK_FOR_TIME_UNIT

    unit = update.message.text.lower()

    context.user_data["unit"] = unit
    redditor = context.user_data["redditor"]

    await update.message.reply_text(
        f"Ok! How many {unit} do you want to mute {redditor} for?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ASK_FOR_DURATION


async def mute_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 3: Confirm mute of Redditor
    """
    assert update.message
    assert context.user_data

    if not update.message.text:
        await update.message.reply_text("I need an amount of Time to continue")
        return ASK_FOR_DURATION

    duration_text = update.message.text.strip()

    if not duration_text.isdigit():
        await update.message.reply_text("Please enter a valid number.")
        return ASK_FOR_DURATION

    duration = int(duration_text)
    redditor = context.user_data["redditor"]
    unit = context.user_data["unit"]

    try:
        mute_redditor(redditor, unit, duration)
        await update.message.reply_text(
            f"{redditor} has been muted for {duration} {unit}"
        )
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text("Sorry we have encountered an unexpected Error")
        return ConversationHandler.END


async def mute_cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    User cancels and we remove any replykeayboard
    """
    assert update.message

    await update.message.reply_text(
        "Mute Command cancelled.", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def unmute_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /unmute Command conversation
    """
    assert update.message
    await update.message.reply_text("Who do you want to unmute?")

    return ASK_FOR_REDDITOR_TO_UNMUTE


async def unmute_confirm(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving Redditor to unmute and unmute it.
    """
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need a redditor name to continue")
        return ASK_FOR_REDDITOR_TO_UNMUTE

    redditor = update.message.text.strip()

    try:
        unmute_redditor(redditor)
        await update.message.reply_text(f"{redditor} unmuted")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("Sorry we have encountered an unexpected Error")
        return ConversationHandler.END


async def rate_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of /rate Command conversation
    """
    assert update.message
    await update.message.reply_text("Which Redditors rating do you want to change?")

    return ASK_FOR_REDDITOR_TO_RATE


async def rate_ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Save Redditor to context and getting an amount for the rating change
    """
    assert context.user_data
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need a redditor name to continue 🙂")
        return ASK_FOR_REDDITOR_TO_RATE

    redditor = update.message.text.strip()
    context.user_data["redditor"] = redditor

    await update.message.reply_text(
        f"OK by how much do you want to change the rating of {redditor}"
    )
    return ASK_FOR_AMOUNT_TO_RATE


async def rate_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 2: Receive the amount for the rating change and changing the rating of specified redditor
    """
    assert context.user_data
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need an amount to continue 🙂")
        return ASK_FOR_AMOUNT_TO_RATE

    rating_text = update.message.text.strip()

    if not rating_text.isdigit():
        await update.message.reply_text("I need a valid number 🙂")
        return ASK_FOR_AMOUNT_TO_RATE

    rating = int(rating_text)
    redditor = context.user_data["redditor"]
    try:
        rate_redditor(redditor, rating)
        await update.message.reply_text(f"Changed rating of {redditor} by {rating}")
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text("Sorry we have encountered an unexpected Error")
        return ConversationHandler.END


"""SUBREDDIT COMMANDS"""


async def listsubs(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list Subreddits that are being watched.
    """
    assert update.message

    try:
        msg = list_subreddits()

    except Exception as e:
        await update.message.reply_text(
            "⚠️ Sorry we have encountered an unexpected Error"
        )
        return

    await update.message.reply_text(f"📋 Watched Subreddits👀:\n{msg}")


async def addsubs_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /addsubs Command conversation
    """
    assert update.message

    await update.message.reply_text(
        "Which Subreddits do you want to add?\nSend me a list of Subreddits separated by spaces.\nSubreddit1 Subreddit2 Subreddit3"
    )

    return ASK_FOR_SUBREDDITS_TO_ADD


async def add_subreddits(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the SUbreddits in a str, splitting it and for each Subreddit try to add it to the db.
    Respond to User with the Subreddits that were added and those that failed.
    """
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need at least one subreddit to continue 🙂")
        return ASK_FOR_SUBREDDITS_TO_ADD

    subreddits = update.message.text.split()
    added = []
    failed = []

    for sub in subreddits:
        try:
            await add_subreddit_to_db(sub)
            added.append(sub)

        except Exception as e:
            failed.append(sub)

    msg = ""

    if added:
        msg += f"✅ Added:\n{'\n'.join(added)}\n"
    if failed:
        msg += f"🚨 Failed to add:\n{'\n'.join(failed)}\n"

    await update.message.reply_text(msg)
    return ConversationHandler.END


async def removesubs_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /removesubs Command conversation
    """
    assert update.message

    await update.message.reply_text(
        "Which Subreddit do you want to remove?\nSend me a list of redditors separated by spaces.\nSubreddit1 Subreddit2 Subreddit3"
    )
    return ASK_FOR_SUBREDDITS_TO_REMOVE


async def remove_subreddits(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the Subreddits in a str, splitting it and for each Subreddit try to remove it from the db.
    Respond to User with the Subreddits that were removed and those that failed.
    """
    assert update.message

    if not update.message.text:
        await update.message.reply_text("I need at least one subreddit to continue 🙂")
        return ASK_FOR_SUBREDDITS_TO_REMOVE

    subreddits = update.message.text.split()
    removed = []
    failed = []

    for sub in subreddits:
        try:
            remove_subreddit_from_db(sub)
            removed.append(sub)

        except Exception as e:
            failed.append(sub)

    msg = ""

    if removed:
        msg += f"✅ Removed: \n{'\n'.join(removed)}\n"
    if failed:
        msg += f"🚨 Failed to remove:\n{'\n'.join(failed)}\n"

    await update.message.reply_text(msg)
    return ConversationHandler.END


async def send_pending_notifications(bot) -> None:
    """
    Background task to check DB for new notifications and send them.
    """
    while True:

        new_items = list_pending_notifications()
        chat_ids = list_active_telegram_users_chat_ids()

        for note in new_items:

            try:
                rating = get_rating_of_redditor(cast(str, note.author))

            except Exception as e:
                print(f"Unexpected Erorr: {e}")
                continue

            message = f"📢 New {note.type} by {note.author}{'🚀' * rating}\n{note.url}"

            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id=chat_id, text=message)

                except Exception as e:
                    print(f"Failed to send to {chat_id}: {e}")

        notification_ids = [n.id for n in new_items]

        try:
            close_pending_notifications(notification_ids)
        except Exception as e:
            print(f"{e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    assert TELEGRAM_BOT_TOKEN

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # --- General Commands ---
    start_handler = CommandHandler("start", start)
    help_handler = CommandHandler("help", help)
    list_handler = CommandHandler("list", list)
    listsubs_handler = CommandHandler("listsubs", listsubs)

    # --- Conversation Handlers ---

    # Add Redditors
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            ASK_FOR_REDDITORS_TO_ADD: [
                CommandHandler("cancel", cancel_conversation),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_redditors),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Remove Redditors
    remove_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("remove", remove_start)],
        states={
            ASK_FOR_REDDITORS_TO_REMOVE: [
                CommandHandler("cancel", cancel_conversation),
                MessageHandler(filters.TEXT & ~filters.COMMAND, remove_redditors),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Mute Redditor
    mute_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("mute", mute_start)],
        states={
            ASK_FOR_REDDITOR_TO_MUTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mute_choose_unit)
            ],
            ASK_FOR_TIME_UNIT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mute_ask_duration)
            ],
            ASK_FOR_DURATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mute_confirm)
            ],
        },
        fallbacks=[CommandHandler("cancel", mute_cancel)],
    )

    # Unmute Redditor
    unmute_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("unmute", unmute_start)],
        states={
            ASK_FOR_REDDITOR_TO_UNMUTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, unmute_confirm)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Rate Redditor
    rate_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("rate", rate_start)],
        states={
            ASK_FOR_REDDITOR_TO_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, rate_ask_amount)
            ],
            ASK_FOR_AMOUNT_TO_RATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, rate_confirm)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Add Subreddits
    addsub_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addsub", addsubs_start)],
        states={
            ASK_FOR_SUBREDDITS_TO_ADD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_subreddits)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # Remove Subreddits
    rmsub_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("rmsub", removesubs_start)],
        states={
            ASK_FOR_SUBREDDITS_TO_REMOVE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, remove_subreddits)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    # --- Register all handlers ---
    app.add_handlers(
        [
            start_handler,
            help_handler,
            list_handler,
            listsubs_handler,
            add_conv_handler,
            remove_conv_handler,
            mute_conv_handler,
            unmute_conv_handler,
            rate_conv_handler,
            addsub_conv_handler,
            rmsub_conv_handler,
        ]
    )

    # --- Startup event ---
    async def on_startup(app):
        asyncio.create_task(send_pending_notifications(app.bot))

    app.post_init = on_startup
    app.run_polling()
