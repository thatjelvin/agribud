"""pytest configuration: ensure both the backend and the ml/ package are importable."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
for p in (str(BACKEND_ROOT), str(REPO_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
