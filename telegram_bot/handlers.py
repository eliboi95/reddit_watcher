import asyncio
import logging
from typing import Any, cast

from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
    Update,
    User,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config.config import TELEGRAM_BOT_TOKEN
from db.exceptions import (
    RedditorAlreadyActiveError,
    RedditorAlreadyInactiveError,
    SubredditAlreadyActiveError,
    SubredditAlreadyInactiveError,
)
from telegram_bot.decorators.handler_decorators import Check, require_checks
from telegram_bot.service import (
    add_redditor_to_db,
    add_subreddit_to_db,
    close_pending_notifications,
    get_help,
    get_rating_of_redditor,
    list_active_telegram_users_chat_ids,
    list_muted_redditors,
    list_pending_notifications,
    list_redditors,
    list_redditors_with_rating,
    list_subreddits,
    list_subreddits_str,
    mute_redditor,
    rate_redditor,
    register_telegram_user,
    remove_redditor_from_db,
    remove_subreddit_from_db,
    unmute_redditor,
)

"""InlineKeyboard Buttons"""
TIME_UNITS = ["hours", "days", "years"]
TIME = [1, 10, 100]
RATING = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]

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

logger = logging.getLogger("reddit_watcher.telegram_bot.handlers")

"""GENERAL COMMANDS"""


@require_checks([Check.MESSAGE, Check.CHAT, Check.USER])
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to add the User to active telegram users in DB.
    """
    chat: Chat = cast(Chat, update.effective_chat)
    user: User = cast(User, update.effective_user)
    message: Message = cast(Message, update.message)

    chat_id = chat.id
    username = user.username

    try:
        msg = register_telegram_user(chat_id, username)

    except Exception as e:
        await message.reply_text("⚠️ Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")
        return

    await message.reply_text(f"👋 Hello {username or 'there'}!\n{msg}")


@require_checks([Check.MESSAGE])
async def help(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to get a list of all available commands.
    """
    message: Message = cast(Message, update.message)

    try:
        msg = get_help()

    except Exception as e:
        await message.reply_text("⚠️ Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")
        return

    await message.reply_text(f"🛠️ Available Bot Commands:\n{msg}")


@require_checks([Check.MESSAGE])
async def cancel_conversation(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Telegram Bot Command to cancel any conversation Command
    """
    message: Message = cast(Message, update.message)

    await message.reply_text("🚨 Command canceled 🚨")
    return ConversationHandler.END


"""REDDITOR COMMANDS"""


@require_checks([Check.MESSAGE])
async def list(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list all Redditors that are being watched.
    """
    message: Message = cast(Message, update.message)

    try:
        msg = list_redditors_with_rating()

    except Exception as e:
        await message.reply_text("⚠️ Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")
        return

    await message.reply_text(f"📋 Watched Redditors 👀:\n{msg}")


@require_checks([Check.MESSAGE])
async def add_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /add Command conversation
    """
    message: Message = cast(Message, update.message)

    await message.reply_text(
        "Who do you want to add?\nSend me a list of redditors separated by spaces.\nRedditor1 Redditor2 Redditor3"
    )

    return ASK_FOR_REDDITORS_TO_ADD


@require_checks([Check.MESSAGE])
async def add_redditors(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the Redditors in a str, splitting it and for each Redditor try to add it to the db.
    Respond to User with the Redditors that were added and those that failed.
    """
    message: Message = cast(Message, update.message)

    if not message.text:
        await message.reply_text("I need at least one redditor name to continue 🙂")

        return ASK_FOR_REDDITORS_TO_ADD

    redditors = message.text.split()
    added = []
    failed = []

    for redditor in redditors:
        try:
            await add_redditor_to_db(redditor)
            added.append(redditor)

        except RedditorAlreadyActiveError as e:
            added.append(redditor)
            logger.info(f"{e}")

        except Exception as e:
            failed.append(redditor)
            logger.exception(f"{e}")

    msg = ""

    if added:
        msg += f"✅ Added:\n{'\n'.join(added)}\n"

    if failed:
        msg += f"🚨 Failed to add:\n{'\n'.join(failed)}\n"

    await message.reply_text(msg)

    return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def remove_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /remove Command conversation
    """
    message: Message = cast(Message, update.message)

    redditors = list_redditors()

    if not redditors:
        await message.reply_text("No Redditors found in the DB")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"remove: {name}")]
        for name in redditors
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text("Who do you want to remove?", reply_markup=reply_markup)

    return ASK_FOR_REDDITORS_TO_REMOVE


@require_checks([Check.CALLBACK_QUERY])
async def remove_redditor_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles when a redditor button is pressed.
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    redditor = query.data.split(":", 1)[1]

    try:
        remove_redditor_from_db(redditor)
        await query.edit_message_text(f"✅ Removed {redditor} from the database.")
    except RedditorAlreadyInactiveError as e:
        await query.edit_message_text(f"✅ Removed {redditor} from the database.")
        logger.info(f"{redditor} is allready inactive in DB: {e}")

    except Exception as e:
        await query.edit_message_text(f"🚨 Failed to remove {redditor}: {e}")

    return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def mute_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of /mute Command conversation
    """
    message: Message = cast(Message, update.message)

    redditors = list_redditors()

    if not redditors:
        await message.reply_text("No Redditors found in the DB")
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"mute:{name}")] for name in redditors
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "Which Redditor do you want to mute?", reply_markup=reply_markup
    )

    return ASK_FOR_REDDITOR_TO_MUTE


@require_checks([Check.CALLBACK_QUERY, Check.USER_DATA])
async def mute_redditor_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Step 1: Save Redditor to context and get Unit of time from User h/d/y
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    redditor = query.data.split(":", 1)[1]

    user_data: dict[Any, Any] = cast(dict[Any, Any], context.user_data)

    user_data["redditor"] = redditor

    keyboard = [
        [
            InlineKeyboardButton(unit, callback_data=f"unit:{unit}")
            for unit in TIME_UNITS
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"Ok, which unit of time are we using to mute {redditor}?",
        reply_markup=reply_markup,
    )

    return ASK_FOR_TIME_UNIT


@require_checks([Check.CALLBACK_QUERY, Check.USER_DATA])
async def mute_unit_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 2: Getting the amount of time from User
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    unit = query.data.split(":", 1)[1]

    user_data: dict[Any, Any] = cast(dict[Any, Any], context.user_data)

    user_data["unit"] = unit
    redditor = user_data["redditor"]

    keyboard = [[InlineKeyboardButton(str(t), callback_data=f"time:{t}") for t in TIME]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Ok! How many {unit} do you want to mute {redditor} for?",
        reply_markup=reply_markup,
    )

    return ASK_FOR_DURATION


@require_checks([Check.CALLBACK_QUERY, Check.USER_DATA])
async def mute_time_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 3: Confirm mute of Redditor
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()
    assert query.data

    if query.data is None:
        return ConversationHandler.END

    duration_text = query.data.split(":", 1)[1]

    user_data: dict[Any, Any] = cast(dict[Any, Any], context.user_data)

    duration = int(duration_text)
    redditor = user_data["redditor"]
    unit = user_data["unit"]

    try:
        mute_redditor(redditor, unit, duration)

        await query.edit_message_text(
            f"{redditor} has been muted for {duration} {unit}"
        )

        return ConversationHandler.END

    except Exception as e:
        await query.edit_message_text("Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")

        return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def mute_cancel(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    User cancels and we remove any replykeayboard
    """
    message: Message = cast(Message, update.message)

    await message.reply_text(
        "Mute Command cancelled.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def unmute_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /unmute Command conversation
    """
    message: Message = cast(Message, update.message)

    try:
        muted_redditors = list_muted_redditors()

    except Exception as e:
        logger.exception(f"{e}")

        return ConversationHandler.END

    if not muted_redditors:
        await message.reply_text("No muted Redditors found in the DB")

        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(name, callback_data=f"unmute:{name}")]
        for name in muted_redditors
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "Which Redditor do you want to unmute?", reply_markup=reply_markup
    )

    return ASK_FOR_REDDITOR_TO_UNMUTE


@require_checks([Check.CALLBACK_QUERY])
async def unmute_redditor_button(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving Redditor to unmute and unmute it.
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    redditor = query.data.split(":", 1)[1]

    try:
        unmute_redditor(redditor)
        await query.edit_message_text(f"{redditor} unmuted")

        return ConversationHandler.END

    except Exception as e:
        await query.edit_message_text("Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")

        return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def rate_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of /rate Command conversation
    """
    message: Message = cast(Message, update.message)

    redditors = list_redditors()

    if not redditors:
        await message.reply_text("Sry No Redditors found in DB")

    keyboard = [
        [InlineKeyboardButton(text=f"{username}", callback_data=f"rate:{username}")]
        for username in redditors
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "Which Redditors rating do you want to change?", reply_markup=reply_markup
    )

    return ASK_FOR_REDDITOR_TO_RATE


@require_checks([Check.CALLBACK_QUERY, Check.USER_DATA])
async def rate_redditor_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Step 1: Save Redditor to context and getting an amount for the rating change
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    user_data: dict[Any, Any] = cast(dict[Any, Any], context.user_data)

    redditor = query.data.split(":", 1)[1]

    user_data["redditor"] = redditor

    keybord = [
        [
            InlineKeyboardButton(text=f"{rating}", callback_data=f"rating:{rating}")
            for rating in RATING[:5]
        ],
        [
            InlineKeyboardButton(text=f"+{rating}", callback_data=f"rating:{rating}")
            for rating in RATING[5:]
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keybord)

    await query.edit_message_text(
        f"OK by how much do you want to change the rating of {redditor}",
        reply_markup=reply_markup,
    )

    return ASK_FOR_AMOUNT_TO_RATE


@require_checks([Check.CALLBACK_QUERY, Check.USER_DATA])
async def rate_rating_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 2: Receive the amount for the rating change and changing the rating of specified redditor
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    user_data: dict[Any, Any] = cast(dict[Any, Any], context.user_data)

    redditor = user_data["redditor"]

    rating_text = query.data.split(":", 1)[1]

    rating = int(rating_text)

    try:
        rate_redditor(redditor, rating)
        await query.edit_message_text(f"Changed rating of {redditor} by {rating}")

        return ConversationHandler.END

    except Exception as e:
        await query.edit_message_text("Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")

        return ConversationHandler.END


"""SUBREDDIT COMMANDS"""


@require_checks([Check.MESSAGE])
async def listsubs(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Telegram Bot Command to list Subreddits that are being watched.
    """
    message: Message = cast(Message, update.message)

    try:
        msg = list_subreddits_str()

    except Exception as e:
        await message.reply_text("⚠️ Sorry we have encountered an unexpected Error")
        logger.exception(f"{e}")

        return

    await message.reply_text(f"📋 Watched Subreddits👀:\n{msg}")


@require_checks([Check.MESSAGE])
async def addsubs_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /addsubs Command conversation
    """
    message: Message = cast(Message, update.message)

    await message.reply_text(
        "Which Subreddits do you want to add?\nSend me a list of Subreddits separated by spaces.\nSubreddit1 Subreddit2 Subreddit3"
    )

    return ASK_FOR_SUBREDDITS_TO_ADD


@require_checks([Check.MESSAGE])
async def add_subreddits(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the SUbreddits in a str, splitting it and for each Subreddit try to add it to the db.
    Respond to User with the Subreddits that were added and those that failed.
    """
    message: Message = cast(Message, update.message)

    if not message.text:
        await message.reply_text("I need at least one subreddit to continue 🙂")
        return ASK_FOR_SUBREDDITS_TO_ADD

    subreddits = message.text.split()
    added = []
    failed = []

    for sub in subreddits:
        try:
            await add_subreddit_to_db(sub)
            added.append(sub)

        except SubredditAlreadyActiveError as e:
            added.append(sub)
            logger.info(f"{e}")

        except Exception as e:
            failed.append(sub)
            logger.exception(f"{e}")

    msg = ""

    if added:
        msg += f"✅ Added:\n{'\n'.join(added)}\n"
    if failed:
        msg += f"🚨 Failed to add:\n{'\n'.join(failed)}\n"

    await message.reply_text(msg)
    return ConversationHandler.END


@require_checks([Check.MESSAGE])
async def removesubs_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry Point: Start of the /removesubs Command conversation
    """
    message: Message = cast(Message, update.message)

    subs = list_subreddits()

    keyboard = [
        [
            InlineKeyboardButton(f"{sub}", callback_data=f"removesub:{sub}")
            for sub in subs
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        "Which Subreddit do you want to remove?\nSend me a list of redditors separated by spaces.\nSubreddit1 Subreddit2 Subreddit3",
        reply_markup=reply_markup,
    )

    return ASK_FOR_SUBREDDITS_TO_REMOVE


@require_checks([Check.CALLBACK_QUERY])
async def remove_subreddit_button(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Step 1: Receiving the Subreddits in a str, splitting it and for each Subreddit try to remove it from the db.
    Respond to User with the Subreddits that were removed and those that failed.
    """
    query: CallbackQuery = cast(CallbackQuery, update.callback_query)
    await query.answer()

    if query.data is None:
        return ConversationHandler.END

    subreddit = query.data.split(":", 1)[1]

    try:
        remove_subreddit_from_db(subreddit)
        await query.edit_message_text(f"{subreddit} removed")

    except Exception as e:
        logger.exception(f"{e}")

    return ConversationHandler.END


async def send_pending_notifications(bot) -> None:
    """
    Background task to check DB for new notifications and send them.
    """
    while True:

        new_items = list_pending_notifications()
        chat_ids = list_active_telegram_users_chat_ids()
        notification_ids = []

        for note in new_items:

            try:
                rating = get_rating_of_redditor(cast(str, note.author))

            except Exception as e:
                logger.exception(f"{e}")
                continue

            message = f"📢 New {note.type} by {note.author}{'🚀' * rating}\n{note.url}"

            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id=chat_id, text=message)
                    logger.info(f"Sent message to {chat_id}")

                except Exception as e:
                    logger.exception(f"Failed to send to {chat_id}: {e}")
            notification_ids.append(note.id)

        try:
            close_pending_notifications(notification_ids)
            notification_ids = []
        except Exception as e:
            logger.exception(f"{e}")
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
        per_chat=True,
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
        per_chat=True,
        entry_points=[CommandHandler("remove", remove_start)],
        states={
            ASK_FOR_REDDITORS_TO_REMOVE: [
                CallbackQueryHandler(remove_redditor_button, pattern=r"^remove:")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
    )

    mute_conv_handler = ConversationHandler(
        per_chat=True,
        entry_points=[CommandHandler("mute", mute_start)],
        states={
            ASK_FOR_REDDITOR_TO_MUTE: [
                CallbackQueryHandler(mute_redditor_button, pattern=r"^mute:")
            ],
            ASK_FOR_TIME_UNIT: [
                CallbackQueryHandler(mute_unit_button, pattern=r"^unit:")
            ],
            ASK_FOR_DURATION: [
                CallbackQueryHandler(mute_time_button, pattern=r"^time:")
            ],
        },
        fallbacks=[CommandHandler("mute", mute_start)],
    )

    # Unmute Redditor
    unmute_conv_handler = ConversationHandler(
        per_chat=True,
        entry_points=[CommandHandler("unmute", unmute_start)],
        states={
            ASK_FOR_REDDITOR_TO_UNMUTE: [
                CallbackQueryHandler(unmute_redditor_button, pattern=r"^unmute:")
            ],
        },
        fallbacks=[CommandHandler("unmute", unmute_start)],
    )

    # Rate Redditor
    rate_conv_handler = ConversationHandler(
        per_chat=True,
        entry_points=[CommandHandler("rate", rate_start)],
        states={
            ASK_FOR_REDDITOR_TO_RATE: [
                CallbackQueryHandler(rate_redditor_button, pattern="^rate:")
            ],
            ASK_FOR_AMOUNT_TO_RATE: [
                CallbackQueryHandler(rate_rating_button, pattern="^rating:")
            ],
        },
        fallbacks=[CommandHandler("rate", rate_start)],
    )

    # Add Subreddits
    addsub_conv_handler = ConversationHandler(
        per_chat=True,
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
        per_chat=True,
        entry_points=[CommandHandler("rmsub", removesubs_start)],
        states={
            ASK_FOR_SUBREDDITS_TO_REMOVE: [
                CallbackQueryHandler(remove_subreddit_button, pattern=r"^removesub:")
            ],
        },
        fallbacks=[CommandHandler("rmsub", removesubs_start)],
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
