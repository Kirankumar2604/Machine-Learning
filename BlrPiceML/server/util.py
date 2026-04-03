from __future__ import annotations

import json
from pathlib import Path

NUMERIC_FEATURES = ["total_sqft", "bath", "bhk"]

BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
COLUMNS_PATH = ARTIFACTS_DIR / "columns.json"


def _load_columns() -> list[str]:
    with open(COLUMNS_PATH, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload["data_columns"]


# Load once at import time; used for both dropdown values and one-hot encoding.
DATA_COLUMNS: list[str] = _load_columns()
FEATURE_INDEX = {name: i for i, name in enumerate(DATA_COLUMNS)}


def get_location_names() -> list[str]:
    """Return valid location values for the UI dropdown."""
    return [c for c in DATA_COLUMNS if c not in NUMERIC_FEATURES]

