from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any


def _data_dir() -> Path:
    return Path(os.getenv("HOLIDAYS_DATA_DIR", "data/holidays"))


@lru_cache(maxsize=32)
def load_holidays_payload(year: int) -> dict[str, Any]:
    path = _data_dir() / f"{year}.json"
    if not path.exists():
        raise FileNotFoundError(str(path))

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, dict) or payload.get("year") != year:
        raise ValueError(f"Invalid payload in {path}")

    return payload
