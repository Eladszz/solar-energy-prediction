from __future__ import annotations

from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CATALOG_PATH = REPO_ROOT / "demo" / "catalog.json"
BACKEND_URL = os.getenv("SOLAR_BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("SOLAR_REQUEST_TIMEOUT_SECONDS", "45"))
DEMO_MODE_DEFAULT = os.getenv("SOLAR_UI_DEMO_MODE", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


@lru_cache()
def load_demo_catalog() -> dict[str, Any]:
    return json.loads(DEMO_CATALOG_PATH.read_text())


def get_demo_scenarios() -> list[dict[str, Any]]:
    return list(load_demo_catalog()["scenarios"])


def get_default_demo_scenario_id() -> str:
    return str(load_demo_catalog()["default_scenario_id"])


def get_demo_scenario_by_id(scenario_id: str) -> dict[str, Any]:
    for scenario in get_demo_scenarios():
        if scenario["id"] == scenario_id:
            return scenario
    raise KeyError(f"Unknown demo scenario: {scenario_id}")
