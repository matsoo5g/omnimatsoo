from dataclasses import dataclass


@dataclass
class DomEvent:
    timestamp: float
    type: str

    @classmethod
    def from_tuple(cls, event: tuple):
        return cls(*event)


@dataclass
class PlaybackStatistics:
    id: str
    timestamp: int
    target: str
    events: list[DomEvent]

    def __post_init__(self):
        for i in range(len(self.events)):
            self.events[i] = DomEvent.from_tuple(self.events[i])


@dataclass
class Test:
    id: str
    timestamp: int
    events: list[DomEvent]

    def __post_init__(self):
        for i in range(len(self.events)):
            self.events[i] = DomEvent.from_tuple(self.events[i])
