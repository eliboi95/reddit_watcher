import time
from .models import WatchedSubreddit, WatchedRedditor, TelegramUser, Notification
from praw.models import Comment, Submission
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from .exceptions import (
    RedditorDoesNotExistError,
    RedditorAlreadyActiveError,
    RedditorNotFoundInDBError,
    RedditorAlreadyMutedError,
    RedditorAlreadyInactiveError,
    SubredditAlreadyInactiveError,
    SubredditAlreadyActiveError,
    SubredditNotFoundError,
)


def safe_commit(session: Session, retries: int = 3, delay: float = 0.5) -> None:
    """
    Commit the current session with retries in case of 'database is locked' errors.
    """
    for attempt in range(retries):
        try:
            session.commit()
            return

        except OperationalError as e:
            if "database is locked" in str(e).lower():
                print(f"[DB] Database is locked, retrying ({attempt+1}/{retries})...")
                time.sleep(delay)

            else:
                session.rollback()
                raise

    session.rollback()

    raise RuntimeError("[DB] Failed to commit after multiple retries.")


"""SUBREDDITS"""


def get_watched_subreddits(session: Session) -> list[str]:
    """
    Gets all watched subreddits
    """
    rows = session.query(WatchedSubreddit.name).filter_by(active=True).all()

    return [row[0] for row in rows]


def add_watched_subreddit(session: Session, subreddit_name: str) -> str:
    """
    Adds a subreddit to the watchlist
    """
    name = subreddit_name.strip()

    existing = session.query(WatchedSubreddit).filter_by(name=name).first()

    if existing:
        if not existing.active:
            existing.active = True
            safe_commit(session)
            return f"Reactivated subreddit: {name}"

        raise SubredditAlreadyActiveError(f"{name} is already beeing watched")

    new_subreddit = WatchedSubreddit(name=name, active=True)
    session.add(new_subreddit)
    safe_commit(session)

    return f"Added new subreddit: {name}"


def remove_watched_reddit(session: Session, subreddit_name: str) -> str:
    """
    Deactivates a Subreddit so it doesnt get watched anymore
    """
    name = subreddit_name.strip()

    subreddit = session.query(WatchedSubreddit).filter_by(name=name).first()

    if not subreddit:
        raise SubredditNotFoundError(f"Subreddit not found: {name}")

    if not subreddit.active:
        raise SubredditAlreadyInactiveError(f"{name} already inactive")

    subreddit.active = False
    safe_commit(session)

    return f"{name} deactivated"


"""REDDITORS"""


def get_watched_users(session: Session) -> list[str]:
    """
    Gets all the redditors on the watchlist
    """
    return [
        row.username
        for row in session.query(WatchedRedditor).filter_by(active=True).all()
    ]


def get_watched_users_with_rating(session: Session) -> list[tuple[str, int]]:
    """
    Gets all the redditors on the watchlist including the rating
    """
    return [
        (row.username, row.rating)
        for row in session.query(WatchedRedditor).filter_by(active=True).all()
    ]


def add_watched_redditor(session: Session, username: str) -> None:
    """
    Add a redditor to the watched_users table if not already present.
    """
    username = username.strip()

    existing = session.query(WatchedRedditor).filter_by(username=username).first()
    if existing:
        if not existing.active:
            existing.active = True
            safe_commit(session)
            raise RedditorDoesNotExistError(f"User does not exist on Reddit {username}")

        raise RedditorAlreadyActiveError(f"User already being watched: {username}")

    new_user = WatchedRedditor(username=username, active=True)
    session.add(new_user)
    safe_commit(session)

    return


def remove_watched_redditor(session: Session, username: str) -> None:
    """
    Deactivates a redditor the watched_users table.
    """
    username = username.strip()

    user = session.query(WatchedRedditor).filter_by(username=username).first()
    if not user:
        raise RedditorNotFoundInDBError(f"User not found: {username}")

    if not user.active:
        raise RedditorAlreadyInactiveError(f"User already inactive: {username}")

    user.active = False
    safe_commit(session)

    return


def is_muted(session: Session, username: str) -> bool:
    """
    Implement is_muted Check
    """
    username = username.strip()
    user = session.query(WatchedRedditor).filter_by(username=username).first()

    if not user:
        return True
    elif time.time() - user.muted_until < 0:
        return True
    else:
        return False


def set_redditor_mute_timer(session: Session, username: str, mute_time: float) -> str:
    """
    Mute a user for a specified time
    """
    username = username.strip()

    user = session.query(WatchedRedditor).filter_by(username=username).first()
    if not user:
        raise RedditorNotFoundInDBError(f"User not found: {username}")

    if is_muted(session, username):
        raise RedditorAlreadyMutedError(f"User already muted: {username}")

    user.muted_until = mute_time + time.time()
    safe_commit(session)

    return f"Muted user: {username}"


def unset_redditor_mute_timer(session: Session, username: str) -> str:
    """
    Unmute User
    """

    username = username.strip()

    user = session.query(WatchedRedditor).filter_by(username=username).first()

    if not user:
        raise RedditorNotFoundInDBError(f"User not found: {username}")

    user.muted_until = time.time() - 1
    safe_commit(session)

    return f"unmuted {username}"


def set_redditor_rating(session: Session, username: str, rating: int) -> str:
    """
    Rate a User by a int amount. Negative ints are possible
    """
    username = username.strip()

    user = session.query(WatchedRedditor).filter_by(username=username).first()
    if not user:
        raise RedditorNotFoundInDBError(f"User not found: {username}")

    user.rating += rating
    safe_commit(session)

    return f"Changed rating for: {username}"


def get_rating(session: Session, username: str) -> int:
    """
    Get the rating of a redditor
    """
    username = username.strip()

    user = session.query(WatchedRedditor).filter_by(username=username).first()
    if not user:
        raise RedditorNotFoundInDBError(f"User not found: {username}")

    return user.rating


"""SUBMISSIONS"""


def add_comment(session: Session, comment: Comment) -> str:
    """
    Adds a comment to the notifications table
    """
    notification = Notification(
        id=comment.id,
        type="comment",
        author=str(comment.author),
        content=comment.body,
        url=f"https://reddit.com{comment.permalink}",
        created_utc=int(comment.created_utc),
    )
    session.merge(notification)
    safe_commit(session)

    return "comment added"


def add_submission(session: Session, submission: Submission) -> str:
    """
    Adds a submission to the notifications table
    """
    notfication = Notification(
        id=submission.id,
        type="submission",
        author=str(submission.author),
        content=submission.title,
        url=f"https://reddit.com{submission.permalink}",
        created_utc=int(submission.created_utc),
    )
    session.merge(notfication)
    safe_commit(session)

    return "submission added"


def get_pending_notifications(session: Session) -> list[Notification]:
    """
    Return all undelivered notifications
    """
    return (
        session.query(Notification)
        .filter_by(delivered=False)
        .order_by(Notification.created_utc.asc())
        .all()
    )


def get_notifications(session: Session) -> list[list[str]]:
    """
    Return all notifications
    """
    return [[n.type, n.author, n.content] for n in session.query(Notification).all()]


"""TELEGRAM USERS"""


def get_active_telegram_users_chat_ids(session: Session) -> list[str]:
    """
    Get all active Telegram user chat IDs. They need to have written /start in the botchat to be listed
    """
    return [u.chat_id for u in session.query(TelegramUser).filter_by(active=True).all()]


def add_telegram_user(session: Session, chat_id: int, username: str | None) -> str:
    """
    Add or reactivate a Telegram user in the database.
    """
    name = username or "Anonymous"
    existing = session.query(TelegramUser).filter_by(chat_id=chat_id).first()

    if existing:
        if not existing.active:
            existing.active = True
            safe_commit(session)
            return f"Reactivated Telegram user {name}"
        return f"Telegram user already active: {name}"

    user = TelegramUser(chat_id=str(chat_id), username=name, active=True)
    session.add(user)
    safe_commit(session)

    return f"Added new Telegram user: {name}"


def remove_telegram_user(session: Session, chat_id: str) -> str:
    """
    Deactivate a Telegram user.
    """
    user = session.query(TelegramUser).filter_by(chat_id=chat_id).first()

    if not user:
        return f"Telegram user not found: {chat_id}"

    if not user.active:
        return f"Telegram user already inactive: {chat_id}"

    user.active = False
    safe_commit(session)

    return f"Deactivated Telegram user: {chat_id}"
