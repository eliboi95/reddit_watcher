"""
DEFINING CUSTOM EXCEPTIONS
"""


class AppError(Exception):
    """Base Class for all custom App exceptions"""

    pass


class RedditorError(AppError):
    """All Redditor related Errors"""

    pass


class RedditorDoesNotExistError(RedditorError):
    pass


class RedditorNotFoundInDBError(RedditorError):
    pass


class RedditorAlreadyInactiveError(RedditorError):
    pass


class RedditorAlreadyActiveError(RedditorError):
    pass


class RedditorAlreadyMutedError(RedditorError):
    pass


class SubredditError(AppError):
    """All Subreddit related Errors"""

    pass


class SubredditDoesNotExistError(SubredditError):
    pass


class SubredditNotFoundError(SubredditError):
    pass


class SubredditAlreadyInactiveError(SubredditError):
    pass


class SubredditAlreadyActiveError(SubredditError):
    pass
