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

    @abstractmethod
    def mupdate(self, mapping: dict[Union[str, bytes], float]) -> list[float]:
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

    def mupdate(self, mapping: dict[Union[str, bytes], float]) -> list[float]:
        ret = []
        for id, delta in mapping.items():
            self._storage[id] = (v := float(self._storage.get(id, 0.0) + delta))
            ret.append(v)
        return ret


class RedisBackend(Storage):
    TYPE = SUPPORTED.REDIS
    MEMBER_SET_KEY = "__MEMS__"

    def __init__(self, host="redis", port=6379, **kwargs):
        self.redis_client = Redis(host=host, port=port, **kwargs)

    def get(self, id_prefix_range: Union[str, bytes] = "") -> list[Union[str, bytes]]:
        if v := self.redis_client.get(id_prefix_range):
            return v
        if not id_prefix_range or id_prefix_range[-1] != "*":
            id_prefix_range += "*"
        keys = []
        for found in self.redis_client.scan_iter(match=id_prefix_range, _type="STRING"):
            keys.append(found)
        return self.redis_client.mget(keys=keys)

    def set(self, id: Union[str, bytes], content: Union[str, bytes]) -> bool:
        keys = [self.MEMBER_SET_KEY, id]
        self._pipe(
            funcs=["set", "sadd"],
            func_args=[((), {"name": id, "value": content}), ((keys), {})],
            watch_parameters=keys,
        )
        return True

    def mset(
        self, ids: list[Union[str, bytes]], contents: list[Union[str, bytes]]
    ) -> bool:
        if len(contents) != len(ids):
            return False
        to_set_map = {id: content for id, content in zip(ids, contents)}
        keys = [self.MEMBER_SET_KEY, *ids]
        self._pipe(
            funcs=["mset", "sadd"],
            func_args=[
                ((to_set_map,), {}),
                ((keys,), {}),
            ],
            watch_parameters=keys,
        )
        return True

    def contains(self, id: Union[str, bytes]) -> bool:
        return self.redis_client.sismember(name=self.MEMBER_SET_KEY, value=id)

    def mupdate(self, mapping: dict[Union[str, bytes], float]) -> list[float]:
        args = []
        for id, delta in mapping.items():
            args.append(((id, delta), {}))
        funcs = ["incrbyfloat"] * len(mapping)
        funcs.append("sadd")
        keys = [self.MEMBER_SET_KEY, *mapping.keys()]
        args.append((keys, {}))
        return self._pipe(
            funcs=funcs,
            func_args=args,
            watch_parameters=keys,
        )

    def _pipe(
        self, funcs: list, func_args: list, watch_parameters: Optional[list] = None
    ):
        ret = []
        with self.redis_client.pipeline() as pipe:
            while True:
                try:
                    if watch_parameters:
                        pipe.watch(*watch_parameters)
                    pipe.multi()
                    for f, (fargs, fkwargs) in zip(funcs, func_args):
                        ret.append(getattr(pipe, f)(*fargs, **fkwargs))
                    pipe.execute()
                    break
                except WatchError:
                    continue
        return ret


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
