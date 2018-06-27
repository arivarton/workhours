class StampError(Exception):
    pass


class TagOutsideTimeBoundaryError(StampError):
    pass


class NoMatchingDatabaseEntryError(StampError):
    pass


class TooManyMatchingDatabaseEntriesError(StampError):
    pass


class TooManyMatchesError(StampError):
    pass


class NoMatchesError(StampError):
    pass


class ArgumentError(StampError):
    pass


class CurrentStampNotFoundError(StampError):
    pass
