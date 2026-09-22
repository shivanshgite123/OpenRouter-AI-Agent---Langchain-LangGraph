import os

os.environ.setdefault("MOCK_MODE", "true")
os.environ.setdefault("MODEL_PROVIDER", "openai")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
