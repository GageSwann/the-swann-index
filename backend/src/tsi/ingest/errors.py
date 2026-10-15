"""CFBD client errors. Messages never contain the API key."""


class CfbdError(RuntimeError):
    """A CFBD request failed."""


class BudgetExceededError(CfbdError):
    """This month's call budget is used up; no request was sent."""
