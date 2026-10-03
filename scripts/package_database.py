"""Shrink and compress the database for deployment.

Usage: python scripts/package_database.py [source.db] [output.db.gz]
Default: data/ortholog.db  ->  data/ortholog.db.gz
"""
import gzip
import hashlib
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PACKED_DB, PROD_DB  # noqa: E402

LIMIT_MIB = 90  # GitHub blocks single files above 100 MiB


def mib(path: Path) -> float:
    return path.stat().st_size / (1024 * 1024)


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else PROD_DB
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else PACKED_DB
    if not src.exists():
        sys.exit(f"Database not found: {src}  (run scripts/build_database.py first)")

    print(f"source:      {src}  ({mib(src):.1f} MiB)")
    tmp = src.with_suffix(".packed.tmp")
    if tmp.exists():
        tmp.unlink()

    conn = sqlite3.connect(str(src))
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orthologs_target ON orthologs (target_gene_id)")
    conn.execute("ANALYZE")
    conn.commit()
    conn.execute("VACUUM INTO '" + str(tmp).replace("'", "''") + "'")
    conn.close()
    print(f"compacted:   {mib(tmp):.1f} MiB")

    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "rb") as f_in, gzip.open(dest, "wb", compresslevel=9) as f_out:
        shutil.copyfileobj(f_in, f_out, 1024 * 1024)
    tmp.unlink()

    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    size = mib(dest)
    print(f"compressed:  {dest}  ({size:.1f} MiB)")
    print(f"sha256:      {sha}")
    print()
    if size <= LIMIT_MIB:
        print(f"OK: {size:.1f} MiB is under {LIMIT_MIB} MiB. You can commit this file to GitHub as it is.")
    else:
        print(f"TOO BIG for a normal Git commit ({size:.1f} MiB > {LIMIT_MIB} MiB).")
        print("Upload it as an asset of a GitHub Release instead, and set ORTHOLOG_DB_URL to its download link.")


if __name__ == "__main__":
    main()