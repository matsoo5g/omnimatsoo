from dataclasses import dataclass


@dataclass
class DomEvent:
    timestamp: float
    type: str

    @classmethod
    def from_tuple(cls, event: tuple):
        return cls(*event)


@dataclass
class PlaybackQualitySample:
    # https://developer.mozilla.org/en-US/docs/Web/API/VideoPlaybackQuality
    samples: int
    creationTimes: list[float]
    droppedVideoFrames: list[int]
    totalVideoFrames: list[int]


@dataclass
class PlaybackStatistics:
    id: str
    timestamp: int
    target: str
    events: list[DomEvent]
    playbackquality: PlaybackQualitySample

    def __post_init__(self):
        self.playbackquality = PlaybackQualitySample(**self.playbackquality)
        for i, e in enumerate(self.events):
            self.events[i] = DomEvent.from_tuple(e)


@dataclass
class Test:
    id: str
    timestamp: int
    events: list[DomEvent]

    def __post_init__(self):
        for i in range(len(self.events)):
            self.events[i] = DomEvent.from_tuple(self.events[i])
