from omnimatsoo.entities import PlaybackStatistics
from omnimatsoo.kvstorage import Client


class PlaybackBenchmark:
    def __init__(self):
        self.__storage = Client.get()

    def add(self, playback_statistics: PlaybackStatistics):
        key = self._compose_key(playback_statistics)
        self.__storage.set(key, playback_statistics)

    def list(self) -> list:
        return self.__storage.get("")

    def _compose_key(self, playback_statistics: PlaybackStatistics) -> str:
        target = playback_statistics.target
        return ":".join((target, playback_statistics.id))


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
