from collections import Counter
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

from omnimatsoo.entities import PlaybackStatistics
from omnimatsoo.kvstorage import Client
from omnimatsoo.utils import serialize_dataclass


class PREFIXES(str, Enum):
    # Original payload
    ORIGINAL_EVENT = "ORGE:"
    # number of collected events by origin_type:video:device_tag
    AGGREGATION_EVENTS_HISTOGRAM = "AGGRHIST:"
    # "AGGR_TIME_PLAYABLE:S3:short.mp4:loadstart-loadeddata"
    AGGREGATION_TIME_BECOME_PLAYABLE_COUNTS = "AGGRTPLAYABLE_C:"
    AGGREGATION_TIME_BECOME_PLAYABLE_SUM = "AGGRTPLAYABLE_S:"
    # "AGGR_ACTUAL_PLAYBACK_DURATION"
    AGGREGATION_ACTUAL_PLAYBACK_DURATION_VIDEO_SUM = "AGGRADURATION_VS:"
    AGGREGATION_ACTUAL_PLAYBACK_DURATION_ACTUAL_SUM = "AGGRADURATION_AS:"


@dataclass
class RecordKey:
    __slots__ = ("origin", "device", "video", "id", "_k", "_seglen")
    origin: str
    device: str
    video: str
    id: str

    def __post_init__(self):
        self._seglen = [
            len(self.origin),
            len(self.device) + 1,
            len(self.video) + 1,
            len(self.id) + 1,
        ]
        for i, sl in enumerate(self._seglen[1:], 1):
            self._seglen[i] = self._seglen[i - 1] + sl
        self._k = f"{self.origin}:{self.device}:{self.video}:{self.id}"

    def __str__(self) -> str:
        return self._k

    def leveled_key(self, level=4):
        return self._k[: self._seglen[level - 1]]


class PlaybackBenchmark:
    def __init__(self):
        self.__storage = Client.get()

    def add(self, playback_statistics: PlaybackStatistics):
        key = self._compose_key(playback_statistics)
        self.__storage.set(
            f"{PREFIXES.ORIGINAL_EVENT}{key}", serialize_dataclass(playback_statistics)
        )
        self._aggr_hist(
            key=key.leveled_key(3), playback_events=playback_statistics.events
        )
        self._aggr_playback(
            key=key.leveled_key(3),
            playback_events=playback_statistics.events,
            duration=playback_statistics.duration,
        )

    def list(self) -> list:
        return self.__storage.get("")

    def _aggr_hist(self, key, playback_events):
        to_update = {}
        for evt_name, times in Counter(evt.type for evt in playback_events).items():
            key_name = PREFIXES.AGGREGATION_EVENTS_HISTOGRAM + evt_name + ":" + key
            to_update[key_name] = float(times)
        self.__storage.mupdate(to_update)

    def _aggr_playback(self, key, playback_events, duration):
        targets = {"loadstart": 0, "loadeddata": 0, "playing": 0, "ended": 0}
        for evt in playback_events:
            if evt.type in targets and not targets[evt.type]:
                targets[evt.type] = evt.timestamp
        to_update = {}
        if targets["loadstart"] and targets["loadeddata"]:
            to_update[PREFIXES.AGGREGATION_TIME_BECOME_PLAYABLE_COUNTS + key] = 1.0
            to_update[PREFIXES.AGGREGATION_TIME_BECOME_PLAYABLE_SUM + key] = float(
                targets["loadeddata"] - targets["loadstart"]
            )

        if targets["ended"] and targets["playing"]:
            to_update[PREFIXES.AGGREGATION_ACTUAL_PLAYBACK_DURATION_VIDEO_SUM + key] = (
                duration * 1000
            )
            to_update[
                PREFIXES.AGGREGATION_ACTUAL_PLAYBACK_DURATION_ACTUAL_SUM + key
            ] = (targets["ended"] - targets["playing"])

        self.__storage.mupdate(to_update)

    def _compose_key(self, playback_statistics: PlaybackStatistics) -> RecordKey:
        url_segments = urlsplit(playback_statistics.target)
        tag = self._get_origin_tag(url_segments.netloc)
        test_video_name = url_segments.path.rstrip("/").rsplit("/", 1)[1]
        return RecordKey(
            origin=tag,
            video=test_video_name,
            device=playback_statistics.device_tag,
            id=playback_statistics.id,
        )

    def _get_origin_tag(self, netloc: str) -> str:
        if netloc.endswith("s3.amazonaws.com"):
            return "S3"
        elif netloc.endswith("cloudfront.net"):
            return "CloudFront"
        else:
            return "Edge"


class ServiceClients:
    __playback_benchmark = None

    @classmethod
    def init_services(cls, *args, **kwargs):
        if not cls.__playback_benchmark:
            cls.__playback_benchmark = PlaybackBenchmark()

    @classmethod
    @property
    def playback_benchmark(cls):
        return cls.__playback_benchmark
