from abc import abstractmethod, ABC
from enum import Enum
from typing import Any, Optional


class SUPPORTED(Enum):
    MEMORY: str = "memory"
    REDIS: str = "redis"


class Storage(ABC):
    @abstractmethod
    def get(self, id_prefix_range: Optional[str]) -> list[Any]:
        pass

    @abstractmethod
    def set(self, id: str, content: Any) -> bool:
        pass


class MemoryBackend(Storage):
    TYPE = SUPPORTED.MEMORY

    def __init__(self):
        self._storage = {}

    def get(self, id_prefix_range: Optional[str] = "") -> list[Any]:
        return [v for k, v in self._storage.items() if k.startswith(id_prefix_range)]

    def set(self, id: str, content: Any) -> bool:
        self._storage[id] = content


class Client:
    __instance = None

    @classmethod
    def init(cls, type: SUPPORTED, **kwargs):
        if not cls.__instance or cls.__instance.TYPE != type:
            cls.__instance = {SUPPORTED.MEMORY: MemoryBackend}[type](**kwargs)

    @classmethod
    def get(cls):
        if not cls.__instance:
            raise RuntimeError("Configuration not loaded yet")
        return cls.__instance
