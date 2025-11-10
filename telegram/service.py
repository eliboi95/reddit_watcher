import asyncio
from db.models import Notification
from reddit.reddit_client import redditor_exists, subreddit_exists
from db.exceptions import (
    RedditorDoesNotExistError,
    SubredditDoesNotExistError,
)
from db.session import SessionLocal
from db.crud import (
    remove_watched_reddit,
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
    get_watched_users_with_rating,
)

"""GENERAL COMMANDS"""


def register_telegram_user(chat_id: int, username: str) -> str:
    session = SessionLocal()

    try:
        msg = add_telegram_user(session, chat_id, username)
        return msg
    finally:
        session.close()


def get_help() -> str:
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
    session = SessionLocal()

    try:
        list_of_redditors = get_watched_users_with_rating(session)
        return [f"{username} {rating * '🚀'}" for username, rating in list_of_redditors]

    finally:
        session.close()


async def add_redditor_to_db(username: str) -> None:
    exists = await asyncio.to_thread(redditor_exists, username)

    if not exists:
        raise RedditorDoesNotExistError

    session = SessionLocal()

    try:
        add_watched_redditor(session, username)

    finally:
        session.close()


def remove_redditor_from_db(username: str) -> None:
    session = SessionLocal()

    try:
        remove_watched_redditor(session, username)

    finally:
        session.close()


def mute_redditor(username: str, mute_time: float) -> None:
    session = SessionLocal()

    try:
        set_redditor_mute_timer(session, username, mute_time)

    finally:
        session.close()


def unmute_redditor(username: str) -> None:
    session = SessionLocal()

    try:
        unset_redditor_mute_timer(session, username)

    finally:
        session.close()


def rate_redditor(username: str, rating: int) -> None:
    session = SessionLocal()

    try:
        set_redditor_rating(session, username, rating)

    finally:
        session.close()


"""SUBREDDIT COMMANDS"""


def list_subreddits() -> str:
    session = SessionLocal()

    try:
        return "\n".join([subreddit for subreddit in get_watched_subreddits(session)])

    finally:
        session.close()


def add_subreddit_to_db(subreddit_name: str) -> None:
    exists = subreddit_exists(subreddit_name)

    if not exists:
        raise SubredditDoesNotExistError

    session = SessionLocal()

    try:
        add_watched_subreddit(session, subreddit_name)

    finally:
        session.close()


def remove_subreddit_from_db(subreddit_name: str) -> None:
    session = SessionLocal()

    try:
        remove_watched_reddit(session, subreddit_name)

    finally:
        session.close()


def list_pending_notifications() -> list[Notification]:
    session = SessionLocal()

    try:
        return get_pending_notifications(session)

    finally:
        session.close()


def list_active_telegram_users_chat_ids() -> list[str]:
    session = SessionLocal()

    try:
        return get_active_telegram_users_chat_ids(session)

    finally:
        session.close()
