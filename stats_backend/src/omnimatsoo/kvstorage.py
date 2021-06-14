from abc import abstractmethod, ABC

from enum import Enum
from typing import Any, Optional, Union

from redis import Redis, WatchError


class SUPPORTED(Enum):
    MEMORY: str = "memory"
    REDIS: str = "redis"


class Storage(ABC):
    @abstractmethod
    def get(self, id_prefix_range: Optional[Union[str, bytes]]) -> list[Any]:
        pass

    @abstractmethod
    def set(self, id: Union[str, bytes], content: Union[str, bytes]) -> bool:
        pass

    @abstractmethod
    def mset(self, ids: list[Union[str, bytes]], contents: list[Any]) -> bool:
        pass

    @abstractmethod
    def contains(self, id: Union[str, bytes]) -> bool:
        pass


class MemoryBackend(Storage):
    TYPE = SUPPORTED.MEMORY

    def __init__(self, **kwargs):
        self._storage = {}

    def get(
        self, id_prefix_range: Optional[Union[str, bytes]] = ""
    ) -> list[Union[str, bytes]]:
        return [v for k, v in self._storage.items() if k.startswith(id_prefix_range)]

    def set(self, id: Union[str, bytes], content: Union[str, bytes]) -> bool:
        self._storage[id] = content
        return True

    def mset(
        self, ids: list[Union[str, bytes]], contents: list[Union[str, bytes]]
    ) -> bool:
        if len(contents) != len(ids):
            return False
        for id, content in zip(ids, contents):
            self._storage[id] = content
        return True

    def contains(self, id: Union[str, bytes]) -> bool:
        return id in self._storage


class RedisBackend(Storage):
    TYPE = SUPPORTED.REDIS
    MEMBER_SET_KEY = "__MEMS__"

    def __init__(self, host="redis", port=6379, **kwargs):
        self.redis_client = Redis(host=host, port=port, **kwargs)

    def get(
        self, id_prefix_range: Optional[Union[str, bytes]] = ""
    ) -> list[Union[str, bytes]]:
        if not id_prefix_range or id_prefix_range[-1] != "*":
            id_prefix_range += "*"
        keys = []
        for found in self.redis_client.scan_iter(match=id_prefix_range, _type="STRING"):
            keys.append(found)
        return self.redis_client.mget(keys=keys)

    def set(self, id: Union[str, bytes], content: Union[str, bytes]) -> bool:
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(id, self.MEMBER_SET_KEY)
                    pipe.multi()
                    pipe.set(name=id, value=content)
                    pipe.sadd(self.MEMBER_SET_KEY, id)
                    pipe.execute()
                    break
                except WatchError:
                    continue

    def mset(
        self, ids: list[Union[str, bytes]], contents: list[Union[str, bytes]]
    ) -> bool:
        if len(contents) != len(ids):
            return False
        to_set_map = {id: content for id, content in zip(ids, contents)}
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(*ids, self.MEMBER_SET_KEY)
                    pipe.multi()
                    pipe.mset(to_set_map)
                    pipe.sadd(self.MEMBER_SET_KEY, *ids)
                    pipe.execute()
                    break
                except WatchError:
                    continue
        return True

    def contains(self, id: Union[str, bytes]) -> bool:
        return self.redis_client.sismember(name=self.MEMBER_SET_KEY, value=id)


class Client:
    __instance = None

    @classmethod
    def init(cls, type: SUPPORTED, *args, **kwargs):
        if not cls.__instance or cls.__instance.TYPE != type:
            cls.__instance = {
                SUPPORTED.MEMORY: MemoryBackend,
                SUPPORTED.REDIS: RedisBackend,
            }[type](*args, **kwargs)

    @classmethod
    def get(cls):
        if not cls.__instance:
            raise RuntimeError("Configuration not loaded yet")
        return cls.__instance
