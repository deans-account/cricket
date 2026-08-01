from __future__ import annotations
import bz2
import io
import json
from typing import Any, Iterator

try:
    import orjson
    def loads(value: bytes) -> Any:
        return orjson.loads(value)
except ImportError:
    def loads(value: bytes) -> Any:
        return json.loads(value)

def iter_messages(raw_bz2: bytes) -> Iterator[dict[str, Any]]:
    with bz2.BZ2File(io.BytesIO(raw_bz2), "rb") as stream:
        for line in stream:
            if line.strip():
                yield loads(line)

def first_definition(raw_bz2: bytes):
    first_pt = None
    for message in iter_messages(raw_bz2):
        if first_pt is None:
            first_pt = message.get("pt")
        for change in message.get("mc", []):
            definition = change.get("marketDefinition")
            if definition:
                return change.get("id"), definition, first_pt
    return None, None, first_pt
