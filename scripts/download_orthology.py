"""Download Human <-> Mouse orthology from Ensembl (BioMart bulk export).

Usage: python scripts/download_orthology.py [--force]

Writes TSV files and manifest.json to data/raw/orthology/.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR  # noqa: E402
from src.ingestion import orthology as orth  # noqa: E402

OUT_DIR = RAW_DIR / "orthology"
HUMAN, MOUSE = "Homo sapiens", "Mus musculus"

FILES = {
    "human_genes.tsv": (HUMAN, None),
    "mouse_genes.tsv": (MOUSE, None),
    "human_to_mouse.tsv": (HUMAN, MOUSE),
    "mouse_to_human.tsv": (MOUSE, HUMAN),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    release = None
    for attempt in range(3):
        try:
            release = orth.fetch_ensembl_release()
            break
        except Exception as e:  # Ensembl REST is sometimes briefly unavailable (503)
            print(f"could not reach Ensembl REST for release number ({e}); retrying..."
                  if attempt < 2 else f"giving up on release number ({e})")
    if release is None:
        release = "unknown"
    print(f"Ensembl release: {release}")

    for name, (src, tgt) in FILES.items():
        path = OUT_DIR / name
        if path.exists() and not args.force:
            print(f"skip {name} (exists)")
            continue
        dataset, _ = orth.DATASETS[src]
        attrs = (orth.GENE_ATTRIBUTES if tgt is None
                 else orth.homolog_attributes(orth.DATASETS[tgt][1]))
        print(f"downloading {name} ...")
        text = None
        for attempt in range(3):
            try:
                text = orth.fetch_biomart(dataset, attrs)
                break
            except Exception as e:
                print(f"  attempt {attempt + 1} failed ({e})"
                      + ("; retrying..." if attempt < 2 else ""))
        if text is None:
            sys.exit(f"Could not download {name} after 3 attempts. "
                      f"Ensembl may be temporarily down; try again in a few minutes.")
        path.write_text(text, encoding="utf-8")

    manifest = {
        "ensembl_release": release,
        "download_date": date.today().isoformat(),
        "source": "Ensembl BioMart / Compara",
        "biomart_url": orth.BIOMART_URL,
        "files": list(FILES),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()