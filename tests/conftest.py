import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("BOT_USERNAME", "dummy_username")
os.environ.setdefault("API_TOKEN", "dummy_token")
os.environ.setdefault("OPENAI_API_KEY", "dummy_openai")
