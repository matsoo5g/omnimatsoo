from dataclasses import dataclass


@dataclass
class DomEvent:
    # see MediaEvents@ https://github.com/matsoo5g/omnimatsoo/blob/main/test_client/js/benchmarkcontroller.js
    # ref: https://html.spec.whatwg.org/multipage/media.html
    timestamp: float
    type: str

    @classmethod
    def from_tuple(cls, event: tuple):
        return cls(*event)


@dataclass
class PlaybackQualitySample:
    # https://developer.mozilla.org/en-US/docs/Web/API/VideoPlaybackQuality
    # the measured data doesn't make sense at all, unused.
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
    device_tag: str
    playbackquality: PlaybackQualitySample

    def __post_init__(self):
        self.playbackquality = PlaybackQualitySample(**self.playbackquality)
        for i, e in enumerate(self.events):
            self.events[i] = DomEvent.from_tuple(e)
