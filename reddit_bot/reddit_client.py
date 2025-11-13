import time
from typing import Generator, cast

from praw.models import Comment, Submission
from prawcore.exceptions import (RequestException, ResponseException,
                                 ServerError)

from config.config import REDDIT_POLL_INTERVAL, WATCHLIST_UPDATE_INTERVAL
from reddit_bot.reddit_service import (add_comment, add_submission, get_reddit,
                                       get_redditor_list,
                                       get_subreddits_string,
                                       is_author_of_parent, muted)


def watch_loop():
    reddit = get_reddit()
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
            if time.time() - last_reload > WATCHLIST_UPDATE_INTERVAL:

                try:
                    subs = get_subreddits_string()
                    users = get_redditor_list()
                except Exception as e:
                    continue

                new_sub_str = subs if subs else "test"

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

                author = comment.author.name
                if author not in users:
                    continue

                if is_author_of_parent(author, comment):
                    continue

                if muted(author):
                    continue

                add_comment(comment)
                print(f"added comment: {author}")

            # process submissions similarly...
            for submission in submission_stream:
                if submission is None:
                    time.sleep(1)
                    break

                author = submission.author.name

                if author not in users:
                    continue

                if muted(author):
                    continue

                add_submission(submission)

            time.sleep(REDDIT_POLL_INTERVAL)

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


if __name__ == "__main__":
    watch_loop()
