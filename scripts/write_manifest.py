"""Write manifest.json for manually-downloaded orthology TSV files.

Use this when scripts/download_orthology.py can't reach Ensembl but you've
downloaded the 4 TSV files yourself and placed them in data/raw/orthology/.

Usage: python scripts/write_manifest.py
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR  # noqa: E402

OUT_DIR = RAW_DIR / "orthology"
REQUIRED = ["human_genes.tsv", "mouse_genes.tsv", "human_to_mouse.tsv", "mouse_to_human.tsv"]


def main() -> None:
    missing = [f for f in REQUIRED if not (OUT_DIR / f).exists()]
    if missing:
        sys.exit(f"Missing files in {OUT_DIR}: {missing}")

    manifest = {
        "ensembl_release": "manual-download",
        "download_date": date.today().isoformat(),
        "source": "Ensembl BioMart / Compara (manual browser download)",
        "biomart_url": "https://www.ensembl.org/biomart/martservice",
        "files": REQUIRED,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest.json written to {OUT_DIR}")


if __name__ == "__main__":
    main()