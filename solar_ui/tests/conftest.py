"""Pytest configuration for frontend tests.

This keeps the repository root on ``sys.path`` so imports like ``solar_ui...`` work
regardless of how pytest is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
