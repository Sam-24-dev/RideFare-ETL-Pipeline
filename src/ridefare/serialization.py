"""JSON serialization helpers for ML artifacts."""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def make_json_safe(value: Any) -> Any:
    """Convert Python, NumPy, and pandas objects into JSON-safe primitives."""

    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [make_json_safe(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, datetime | date | pd.Timestamp):
        return value.isoformat()
    if value is None or value is pd.NA:
        return None
    if isinstance(value, np.generic):
        return make_json_safe(value.item())
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    if isinstance(value, str | int | bool):
        return value
    if pd.isna(value):
        return None
    return value


def write_json(path: Path, payload: Any) -> None:
    """Write JSON with stable formatting and strict numeric safety."""

    path.parent.mkdir(parents=True, exist_ok=True)
    safe_payload = make_json_safe(payload)
    path.write_text(
        json.dumps(safe_payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
