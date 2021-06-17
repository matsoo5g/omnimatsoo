from typing import Any
import dataclasses
import json


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj):
            return dataclasses.asdict(obj)
        return super().default(obj)


def serialize_dataclass(obj: Any) -> str:
    return json.dumps(obj, cls=DataclassJSONEncoder, separators=(",", ":"))
