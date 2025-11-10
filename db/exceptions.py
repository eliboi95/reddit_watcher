"""
DEFINING CUSTOM EXCEPTIONS
"""


class RedditorDoesNotExistError(Exception):
    pass


class RedditorNotFoundInDBError(Exception):
    pass


class RedditorAlreadyInactiveError(Exception):
    pass


class RedditorAlreadyActiveError(Exception):
    pass


class RedditorAlreadyMutedError(Exception):
    pass


class SubredditDoesNotExistError(Exception):
    pass


class SubredditNotFoundError(Exception):
    pass


class SubredditAlreadyInactiveError(Exception):
    pass


class SubredditAlreadyActiveError(Exception):
    pass
