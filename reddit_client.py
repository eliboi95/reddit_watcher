import praw
import config
import time
from prawcore.exceptions import RequestException, ResponseException, ServerError
from db.models import (
    get_watched_subreddits,
    get_watched_users,
    add_comment,
    add_submission,
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


def is_muted(session, redditor):
    """
    TODO: Implement is_muted Check
    """
    return


def redditor_exists():
    """
    TODO: Implement function to check if redditor exists function to be called in telegram_client (probably)
    """
    return


def watch_loop():
    reddit = get_reddit()
    session = SessionLocal()

    last_reload = 0

    while True:
        try:
            """
            When 60 seconds have passed since the last time the watched lists for redditors and subredditor
            and the Telegram Users has been loaded, it loads it in
            """
            if time.time() - last_reload > 2:
                subs = get_watched_subreddits(session)
                users = get_watched_users(session)

                sub_str = "+".join(subs) if subs else "test"
                subreddit = reddit.subreddit(sub_str)

                last_reload = time.time()

            # print("looking for coments")

            for comment in subreddit.stream.comments(
                skip_existing=False, pause_after=0
            ):
                """
                Start to look for commends. skip_existing needs to be false or comments get missed.
                Allready seen comments get filtered on the DB level.
                TODO: implement Muted Check
                """
                if comment is None:
                    print("breaking comments loop")
                    break
                if str(comment.author) not in users:
                    print("not watching author")
                    continue
                add_comment(session, comment)
                print(f"added comment:\n{comment.author}")

            for submission in subreddit.stream.submissions(
                skip_existing=False, pause_after=0
            ):
                """
                Start to look for submissions. skip_existing needs to be false or submissions get missed.
                Allready seen submissions get filterd on the DB level.
                TODO: implement Muted Check
                """
                if submission is None:
                    break
                if str(submission.author) not in users:
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


if __name__ == "__main__":
    watch_loop()
