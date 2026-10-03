"""Diagnose GO annotation coverage for one gene symbol.

Usage: python scripts/check_gene_annotations.py "Mus musculus" Trp53
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import default_db_path  # noqa: E402
from src.database.connection import connect  # noqa: E402


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit('Usage: python scripts/check_gene_annotations.py "Mus musculus" Trp53')
    species, symbol = sys.argv[1], sys.argv[2]

    conn = connect(default_db_path())
    genes = conn.execute(
        "SELECT * FROM genes WHERE species = ? AND symbol = ? COLLATE NOCASE", (species, symbol)
    ).fetchall()
    if not genes:
        print(f"No gene row found for symbol={symbol!r} species={species!r}")
        return

    for g in genes:
        print(f"gene_id={g['id']}  ensembl_id={g['ensembl_id']}  symbol={g['symbol']}  "
              f"uniprot_id={g['uniprot_id']}")
        n = conn.execute("SELECT COUNT(*) AS n FROM gene_go WHERE gene_id = ?", (g["id"],)).fetchone()["n"]
        print(f"  gene_go rows for this gene_id: {n}")
        by_ns = conn.execute(
            "SELECT t.namespace, COUNT(*) AS n FROM gene_go g JOIN go_terms t ON t.go_id = g.go_id "
            "WHERE g.gene_id = ? GROUP BY t.namespace",
            (g["id"],),
        ).fetchall()
        for r in by_ns:
            print(f"    {r['namespace']}: {r['n']}")

    total_gene_go = conn.execute("SELECT COUNT(*) AS n FROM gene_go").fetchone()["n"]
    print(f"\nTotal gene_go rows in database: {total_gene_go}")
    conn.close()


if __name__ == "__main__":
    main()