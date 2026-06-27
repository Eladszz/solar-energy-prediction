from __future__ import annotations

import os


BACKEND_URL = os.getenv("SOLAR_BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("SOLAR_REQUEST_TIMEOUT_SECONDS", "45"))
