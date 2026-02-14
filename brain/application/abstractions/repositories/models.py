from dataclasses import dataclass
from datetime import date


@dataclass
class WikilinkSuggestion:
    title: str
    represents_keyword: bool


@dataclass
class NoteCreationStat:
    date: date
    count: int


@dataclass
class DraftCreationStat:
    date: date
    count: int
