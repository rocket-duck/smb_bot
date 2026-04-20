import logging
from pathlib import Path

_DATA_DIR = Path("data")


def init_data_dirs() -> None:
    """Create data subdirectories if they don't exist."""
    for subdir in ("img", "dicts", "morning_pic"):
        path = _DATA_DIR / subdir
        path.mkdir(parents=True, exist_ok=True)
    logging.info("Директории data/ проверены")
