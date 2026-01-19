"""Pytest configuration.

This ensures the backend package root is on sys.path when tests are executed.
Without this, imports like `import app...` may fail depending on how pytest is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
