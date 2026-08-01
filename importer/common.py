from __future__ import annotations
import hashlib
import re
from pathlib import Path

DRAW_NAMES = {"draw", "the draw"}
TEST_NATIONS = {
    "afghanistan", "australia", "bangladesh", "england", "india", "ireland",
    "new zealand", "pakistan", "south africa", "sri lanka", "west indies", "zimbabwe"
}
NEGATIVE_TERMS = {
    "t20", "t20i", "odi", "one day", "hundred", "big bash", "ipl", "blast",
    "county championship", "sheffield shield", "ranji", "first class"
}

def norm(value: str | None) -> str:
    text = (value or "").lower().strip()
    text = re.sub(r"\*+test file\*+", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
