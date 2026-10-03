"""Write manifest.json for manually-downloaded GO files (browser fallback).

Usage: python scripts/write_go_manifest.py
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR  # noqa: E402
from src.ingestion import go as go_ingest  # noqa: E402

OUT_DIR = RAW_DIR / "go"
REQUIRED = ["go-basic.obo", "goa_human.gaf.gz", "goa_mouse.gaf.gz"]


def main() -> None:
    missing = [f for f in REQUIRED if not (OUT_DIR / f).exists()]
    if missing:
        sys.exit(f"Missing files in {OUT_DIR}: {missing}")

    obo_text = (OUT_DIR / "go-basic.obo").read_text(encoding="utf-8", errors="replace")
    release = go_ingest.parse_obo_release(obo_text)

    manifest = {
        "go_release": release,
        "download_date": date.today().isoformat(),
        "obo_source": go_ingest.OBO_URL + " (manual browser download)",
        "gaf_sources": go_ingest.GAF_URLS,
        "files": REQUIRED,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest.json written to {OUT_DIR} (GO release: {release})")


if __name__ == "__main__":
    main()