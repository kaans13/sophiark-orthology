"""Build the tiny synthetic dev database: python scripts/seed_synthetic.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SYNTHETIC_DB  # noqa: E402
from tests.synthetic_data import build  # noqa: E402

if __name__ == "__main__":
    if SYNTHETIC_DB.exists():
        SYNTHETIC_DB.unlink()
    build(SYNTHETIC_DB).close()
    print(f"Synthetic database written to {SYNTHETIC_DB}")
