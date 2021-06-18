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

    S3 = "S3"
    CloudFront = "CloudFront"
    Edge = "Edge"


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

    def list_all(self) -> list:
        items = self.__storage.get_items()
        if not items:
            return items
        k, v = items.popitem()
        items[k] = v
        is_bytes = hasattr(k, "decode")

        if not is_bytes:
            return items
        return {k.decode("utf-8"): v.decode("utf-8") for k, v in items.items()}

    def group_by_nodes_playable(self, nodes: list[int]) -> dict[str, float]:
        return self._fraction_aggretation(
            fetch_prefix=PREFIXES.AGGREGATION_TIME_BECOME_PLAYABLE_COUNTS[:-3],
            dividend_prefix=PREFIXES.AGGREGATION_TIME_BECOME_PLAYABLE_SUM[:-1],
            divisor_prefix=PREFIXES.AGGREGATION_TIME_BECOME_PLAYABLE_COUNTS[:-1],
            nodes=nodes,
        )

    def group_by_nodes_playback_duration(self, nodes: list[int]) -> dict[str, float]:
        return self._fraction_aggretation(
            fetch_prefix=PREFIXES.AGGREGATION_ACTUAL_PLAYBACK_DURATION_VIDEO_SUM[:-3],
            dividend_prefix=PREFIXES.AGGREGATION_ACTUAL_PLAYBACK_DURATION_ACTUAL_SUM[
                :-1
            ],
            divisor_prefix=PREFIXES.AGGREGATION_ACTUAL_PLAYBACK_DURATION_VIDEO_SUM[:-1],
            nodes=nodes,
        )

    def group_by_nodes_num_events(
        self, event_name: str, nodes: list[int]
    ) -> dict[str, int]:
        if not (
            pairs := self.__storage.get_items(
                f"{PREFIXES.AGGREGATION_EVENTS_HISTOGRAM}{event_name}"
            )
        ):
            return {}
        k, v = pairs.popitem()
        pairs[k] = v
        IS_SOURCE_BYTES = hasattr(k, "decode")
        bucket = {}
        for k, v in pairs.items():
            if IS_SOURCE_BYTES:
                k = k.decode("utf-8")
            total_nodes = k.split(":")
            node_key = ":".join(total_nodes[node_idx + 2] for node_idx in nodes)
            bucket[node_key] = bucket.get(node_key, 0) + int(v)
        return bucket

    def _fraction_aggretation(
        self,
        fetch_prefix: str,
        dividend_prefix: str,
        divisor_prefix: str,
        nodes: list[int],
    ):
        if not (pairs := self.__storage.get_items(fetch_prefix)):
            return {}
        k, v = pairs.popitem()
        pairs[k] = v
        IS_SOURCE_BYTES = hasattr(k, "decode")
        buckets = {
            dividend_prefix: {},
            divisor_prefix: {},
        }

        for k, v in pairs.items():
            if IS_SOURCE_BYTES:
                k = k.decode("utf-8")
            total_nodes = k.split(":")
            node_key = ":".join(total_nodes[node_idx + 1] for node_idx in nodes)
            bucket = buckets.get(total_nodes[0])
            if bucket is None:
                raise ValueError(f'Malformed key found: "{k}"')
            bucket[node_key] = bucket.get(node_key, 0.0) + float(v)
        return {
            k: buckets[dividend_prefix][k] / v
            for k, v in buckets[divisor_prefix].items()
        }

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
            return PREFIXES.S3.value
        elif netloc.endswith("cloudfront.net"):
            return PREFIXES.CloudFront.value
        else:
            return PREFIXES.Edge.value


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
