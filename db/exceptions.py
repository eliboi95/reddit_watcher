"""
DEFINING CUSTOM EXCEPTIONS
"""


class UserNotFoundError(Exception):
    pass


class UserAlreadyInactiveError(Exception):
    pass


class UserAlreadyActiveError(Exception):
    pass


class UserAlreadyMutedError(Exception):
    pass


class SubredditNotFoundError(Exception):
    pass


class SubredditAlreadyInactiveError(Exception):
    pass


class SubredditAlreadyActiveError(Exception):
    pass
