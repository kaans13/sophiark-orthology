"""Show, for one human gene, what the raw Ensembl files and the database say about its mouse orthologs.

Usage: python scripts/check_gene_orthologs.py FCGR3A
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import RAW_DIR, default_db_path  # noqa: E402
from src.database.connection import connect  # noqa: E402

ORTH_DIR = RAW_DIR / "orthology"


def raw_lines(fname: str, column: int, value: str) -> list[str]:
    out = []
    for line in (ORTH_DIR / fname).read_text(encoding="utf-8").splitlines():
        cols = line.split("\t")
        if len(cols) > column and cols[column].strip() == value:
            out.append(line)
    return out


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/check_gene_orthologs.py FCGR3A")
    symbol = sys.argv[1]
    conn = connect(default_db_path())
    genes = conn.execute(
        "SELECT * FROM genes WHERE species = 'Homo sapiens' AND symbol = ? COLLATE NOCASE", (symbol,)
    ).fetchall()
    if not genes:
        sys.exit(f"No human gene with symbol {symbol!r} in the database.")

    for g in genes:
        eid = g["ensembl_id"]
        print(f"\n=== {g['symbol']} ({eid}) ===")

        print("\n[raw] human_to_mouse.tsv, rows starting with this human gene:")
        for line in raw_lines("human_to_mouse.tsv", 0, eid):
            print("   ", line.replace("\t", "  |  "))

        print("\n[raw] mouse_to_human.tsv, rows that point AT this human gene:")
        for line in raw_lines("mouse_to_human.tsv", 2, eid):
            print("   ", line.replace("\t", "  |  "))

        print("\n[database] mouse orthologs stored for this gene:")
        for r in conn.execute(
            "SELECT t.ensembl_id, t.symbol, o.relationship, o.confidence FROM orthologs o "
            "JOIN genes t ON t.id = o.target_gene_id WHERE o.source_gene_id = ? AND t.species = 'Mus musculus'",
            (g["id"],),
        ):
            print(f"    {r['symbol']}  {r['ensembl_id']}  {r['relationship']}  {r['confidence']}")


if __name__ == "__main__":
    main()
