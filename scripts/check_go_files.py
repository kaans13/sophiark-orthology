"""Sanity check on the 3 GO files before building the database.

Usage: python scripts/check_go_files.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR  # noqa: E402
from src.ingestion import go as go_ingest  # noqa: E402

OUT_DIR = RAW_DIR / "go"
EXPECTED = {
    "go-basic.obo": "text",
    "goa_human.gaf.gz": "gaf",
    "goa_mouse.gaf.gz": "gaf",
}


def main() -> None:
    ok = True
    for name, kind in EXPECTED.items():
        path = OUT_DIR / name
        if not path.exists():
            print(f"[MISSING] {name}")
            ok = False
            continue
        size_mb = path.stat().st_size / (1024 * 1024)
        if kind == "text":
            text = path.read_text(encoding="utf-8", errors="replace")
            n_terms = text.count("\n[Term]")
            release = go_ingest.parse_obo_release(text)
            print(f"[OK]    {name}: {size_mb:.1f} MB, {n_terms} terms, release {release}")
        else:
            first = None
            n = 0
            for line in go_ingest.iter_gaf_lines(path):
                if first is None:
                    first = line
                n += 1
                if n >= 5000:  # enough for a sanity read without scanning the whole file
                    break
            if first is None:
                print(f"[EMPTY] {name}")
                ok = False
                continue
            cols = first.split("\t")
            status = "OK" if len(cols) >= 9 else "WARN"
            if status == "WARN":
                ok = False
            print(f"[{status}]    {name}: {size_mb:.1f} MB, first data row has {len(cols)} columns (expected >= 9)")
            print(f"          e.g. {first[:100]}")

    print()
    print("All files look OK, ready for: python scripts/build_database.py" if ok
          else "Some files are missing/wrong - fix them before continuing.")


if __name__ == "__main__":
    main()