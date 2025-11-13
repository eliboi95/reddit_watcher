import praw
from praw.models import Comment, Submission
from prawcore.exceptions import NotFound, Redirect

from config.config import (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
                           REDDIT_USER_AGENT)
from db.crud import (add_comment_to_db, add_submission_to_db,
                     get_watched_redditors, get_watched_subreddits, is_muted)
from db.session import SessionLocal


def get_reddit() -> praw.Reddit:
    """
    Create and return a Reddit client.
    """
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def redditor_exists(name: str) -> bool:
    """
    Function to check if redditor exists
    """
    try:
        reddit = get_reddit()
        reddit.redditor(name).id

    except NotFound:
        return False

    except Redirect:
        return False

    except AttributeError:
        return False

    return True


def subreddit_exists(name: str) -> bool:
    """
    Function to check if subreddit exists
    """
    try:
        reddit = get_reddit()
        reddit.subreddit(name).id

    except NotFound:
        return False

    except Redirect:
        return False

    except AttributeError:
        return False

    return True


def is_author_of_parent(author_name: str, comment: Comment) -> bool:
    try:
        parent_author_name = comment.parent().author.name

    except Exception as e:
        return False

    return author_name == parent_author_name


def get_subreddits_string() -> str:
    session = SessionLocal()

    try:
        subreddits = get_watched_subreddits(session)
        subreddit_string = "+".join(subreddits)
        return subreddit_string

    finally:
        session.close()


def get_redditor_list() -> list[str]:
    session = SessionLocal()

    try:
        redditors = get_watched_redditors(session)
        return redditors

    finally:
        session.close()


def muted(redditor: str) -> bool:
    session = SessionLocal()

    try:
        return is_muted(session, redditor)

    finally:
        session.close()


def add_comment(comment: Comment) -> None:
    session = SessionLocal()

    try:
        add_comment_to_db(session, comment)

    finally:
        session.close()


def add_submission(submission: Submission) -> None:
    session = SessionLocal()

    try:
        add_submission_to_db(session, submission)

    finally:
        session.close()
