import praw
import config
import time
from typing import Generator, cast
from praw.models import Comment, Submission
from prawcore.exceptions import (
    RequestException,
    ResponseException,
    ServerError,
    NotFound,
    Redirect,
)
from db.models import (
    get_watched_subreddits,
    get_watched_users,
    add_comment,
    add_submission,
    is_muted,
    SessionLocal,
)


def get_reddit():
    """
    Create and return a Reddit client.
    """
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )


def redditor_exists(name):
    """
    Function to check if redditor exists
    """
    try:
        reddit = get_reddit()
        reddit.redditor(name).id

    except NotFound:
        return False

    return True


def subreddit_exists(name):
    """
    Function to check if subreddit exists
    """
    try:
        reddit = get_reddit()
        reddit.subreddit(name).id

    except Redirect:
        return False

    return True


def watch_loop():
    reddit = get_reddit()
    session = None
    last_reload = 0
    sub_str = ""
    comment_stream: Generator[Comment | None, None, None] = cast(
        Generator[Comment | None, None, None], iter([])
    )
    submission_stream: Generator[Submission | None, None, None] = cast(
        Generator[Submission | None, None, None], iter([])
    )
    users = []
    subs = []

    while True:
        try:
            if time.time() - last_reload > 2:
                if session:
                    session.close()

                session = SessionLocal()
                subs = get_watched_subreddits(session)
                subnames = [str(s) for s in subs]
                users = get_watched_users(session)
                new_sub_str = "+".join(subnames) if subs else "test"
                print(new_sub_str)
                if new_sub_str != sub_str:
                    sub_str = new_sub_str
                    subreddit = reddit.subreddit(sub_str)
                    comment_stream: Generator[Comment | None, None, None] = (
                        subreddit.stream.comments(skip_existing=False, pause_after=-1)
                    )
                    submission_stream: Generator[Submission | None, None, None] = (
                        subreddit.stream.submissions(
                            skip_existing=False, pause_after=-1
                        )
                    )

                last_reload = time.time()

            # process comments
            for comment in comment_stream:
                if comment is None:
                    time.sleep(1)
                    break

                author = str(comment.author)
                if author not in users:
                    continue

                if is_muted(session, author):
                    continue

                add_comment(session, comment)
                print(f"added comment: {author}")

            # process submissions similarly...
            for submission in submission_stream:
                if submission is None:
                    time.sleep(1)
                    break

                author = str(submission.author)

                if author not in users:
                    continue

                if is_muted(session, author):
                    continue

                add_submission(session, submission)

            time.sleep(config.REDDIT_POLL_INTERVAL)

        except (RequestException, ResponseException, ServerError) as e:
            print(f"[Error] {e}. Sleeping 30s before retry...")
            time.sleep(30)

        except KeyboardInterrupt:
            print("🛑 Shutting down watcher.")
            break

        except Exception as e:
            print(f"[Unexpected Error] {e}")
            time.sleep(10)

        finally:
            pass

    if session:
        session.close()


if __name__ == "__main__":
    watch_loop()
