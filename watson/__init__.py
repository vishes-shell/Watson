from .jira import JiraMixin
from .watson import Watson as MainWatson
from .watson import __version__  # noqa
from .watson import WatsonError


class Watson(JiraMixin, MainWatson):
    pass


__all__ = ["Watson", "WatsonError"]
