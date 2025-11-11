import asyncio
from db.models import Notification
from reddit.reddit_client import redditor_exists, subreddit_exists
from db.exceptions import (
    RedditorDoesNotExistError,
    SubredditDoesNotExistError,
)
from db.session import SessionLocal
from db.crud import (
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
)

"""GENERAL COMMANDS"""


def register_telegram_user(chat_id: int, username: str) -> str:
    """
    Register a Telegram user in the database.

    Handles session management around `add_telegram_user`. Returns a
    descriptive message about the outcome (e.g., "User added" or
    "User already exists").
    """
    session = SessionLocal()

    try:
        msg = add_telegram_user(session, chat_id, username)
        return msg

    finally:
        session.close()


def get_help() -> str:
    """
    Returns a str of all commands exposed to the Telegram user.
    """
    return (
        "/list\n"
        "/listsubs\n"
        "/add <redditor>\n"
        "/addsub <subreddit>\n"
        "/remove <redditor>\n"
        "/mute <redditor> <time> <unit>\n"
        "/unmute <redditor>\n"
        "/rate <redditor> <amount>"
    )


"""REDDITOR COMMANDS"""


def list_redditors_with_rating() -> list[str]:
    """
    Returns a list of strings for each Redditor. Each String is the Username and the Rating of the Redditor.

    Handles session management around `get_watched_redditors_with_rating` and formatting the strings for each redditor.
    """
    session = SessionLocal()

    try:
        list_of_redditors = get_watched_redditors_with_rating(session)
        return [f"{username} {rating * '🚀'}" for username, rating in list_of_redditors]

    finally:
        session.close()


async def add_redditor_to_db(username: str) -> None:
    """
    Adds a Redditor to the db.

    Checks if the Redditor exists on Reddit and handles session management around `add_watched_redditor`.
    """
    exists = await asyncio.to_thread(redditor_exists, username)

    if not exists:
        raise RedditorDoesNotExistError

    session = SessionLocal()

    try:
        add_watched_redditor(session, username)

    finally:
        session.close()


def remove_redditor_from_db(username: str) -> None:
    """
    Removes / deactivates a redditor from the db.

    Handles Session management around `remove_watched_redditor`.
    """
    session = SessionLocal()

    try:
        remove_watched_redditor(session, username)

    finally:
        session.close()


def mute_redditor(username: str, mute_time: float) -> None:
    """
    Mutes a Redditor for a specified amount of time.

    Handles Session management around `set_redditor_mute_timer`.
    """
    session = SessionLocal()

    try:
        set_redditor_mute_timer(session, username, mute_time)

    finally:
        session.close()


def unmute_redditor(username: str) -> None:
    """
    Unmutes a Redditor.

    Handles Session management around `unset_redditor_mute_timer`.
    """
    session = SessionLocal()

    try:
        unset_redditor_mute_timer(session, username)

    finally:
        session.close()


def rate_redditor(username: str, rating: int) -> None:
    """
    Change the Rating of a Redditor by a specified amount. Negative Amount is used to reduce the Rating.

    Handles Session management around `set_redditor_rating`.
    """
    session = SessionLocal()

    try:
        set_redditor_rating(session, username, rating)

    finally:
        session.close()


"""SUBREDDIT COMMANDS"""


def list_subreddits() -> str:
    """
    Returns a list in form of a string of all watched Subreddits.

    Handles Session management around `get_watched_subreddits`.
    """
    session = SessionLocal()

    try:
        return "\n".join([subreddit for subreddit in get_watched_subreddits(session)])

    finally:
        session.close()


def add_subreddit_to_db(subreddit_name: str) -> None:
    """
    Adds a Subreddit to the DB.

    Checks if Subreddit exists on Reddit and handles Session management aroud `add_watched_subreddit`.
    """
    exists = subreddit_exists(subreddit_name)

    if not exists:
        raise SubredditDoesNotExistError

    session = SessionLocal()

    try:
        add_watched_subreddit(session, subreddit_name)

    finally:
        session.close()


def remove_subreddit_from_db(subreddit_name: str) -> None:
    """
    Removes / deactivates Subreddit from DB.

    Handles Session management around `remove_watched_subreddit`.
    """
    session = SessionLocal()

    try:
        remove_watched_subreddit(session, subreddit_name)

    finally:
        session.close()


def list_pending_notifications() -> list[Notification]:
    """
    Returns a List of all pendind Notifications.

    Handles Session management around `get_pending_notifications`.
    """
    session = SessionLocal()

    try:
        return get_pending_notifications(session)

    finally:
        session.close()


def list_active_telegram_users_chat_ids() -> list[str]:
    """
    Returns a List of all Telegram User Chat IDS.

    Handles Session management around `get_active_telegram_users_chat_ids`.
    """
    session = SessionLocal()

    try:
        return get_active_telegram_users_chat_ids(session)

    finally:
        session.close()
