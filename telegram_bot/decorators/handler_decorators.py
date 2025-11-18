from enum import Enum, auto
from functools import wraps
from typing import Iterable

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


class Check(Enum):
    MESSAGE = auto()
    CHAT = auto()
    USER = auto()
    USER_DATA = auto()
    CALLBACK_QUERY = auto()


def require_checks(checks: Iterable[Check]):
    """Decorator to validate Update/Context before running a handler."""

    def decorator(func):
        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):

            for check in checks:
                if check is Check.MESSAGE and update.message is None:
                    return ConversationHandler.END

                if check is Check.CHAT and update.effective_chat is None:
                    return ConversationHandler.END

                if check is Check.USER and update.effective_user is None:
                    return ConversationHandler.END

                if check is Check.USER_DATA and context.user_data is None:
                    return ConversationHandler.END

                if check is Check.CALLBACK_QUERY and update.callback_query is None:
                    return ConversationHandler.END

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
