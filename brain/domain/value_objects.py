from dataclasses import dataclass


@dataclass(frozen=True)
class LinkInterval:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start

    def __lt__(self, other):
        if not isinstance(other, LinkInterval):
            return NotImplemented
        return self.start < other.start
