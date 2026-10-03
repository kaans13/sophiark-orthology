"""List real examples from your database, grouped by relationship type (human -> mouse).

Usage: python scripts/find_orthology_examples.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import default_db_path  # noqa: E402
from src.database.connection import connect  # noqa: E402
from src.services.orthology_service import find_orthologs  # noqa: E402

SOURCE, TARGET = "Homo sapiens", "Mus musculus"

CANDIDATES = """
SELECT g.id AS gid, g.symbol AS symbol, COUNT(*) AS n,
       (SELECT COUNT(*) FROM gene_go x WHERE x.gene_id = g.id) AS go_rows
FROM orthologs o
JOIN genes g ON g.id = o.source_gene_id
JOIN genes t ON t.id = o.target_gene_id
WHERE g.species = ? AND t.species = ? AND g.symbol IS NOT NULL
GROUP BY g.id HAVING n > 1
"""


def show(title: str, items: list[dict]) -> None:
    print(f"\n{title}")
    if not items:
        print("  (none found)")
    for it in items:
        names = ", ".join(t["target_symbol"] or t["target_ensembl_id"] for t in it["targets"])
        names = names if len(names) <= 70 else names[:67] + "..."
        print(f"  {it['symbol']:<12} {it['n']} mouse orthologs  ({it['go_rows']} GO rows)  ->  {names}")


def main() -> None:
    db = sys.argv[1] if len(sys.argv) > 1 else default_db_path()
    conn = connect(db)

    by_type: dict[str, list[dict]] = {"1:many": [], "many:many": [], "many:1": []}
    for row in conn.execute(CANDIDATES, (SOURCE, TARGET)).fetchall():
        r = find_orthologs(conn, row["gid"], TARGET)
        if r["relationship_type"] in by_type:
            by_type[r["relationship_type"]].append({**dict(row), "targets": r["targets"]})

    print("Human genes with more than one mouse ortholog, by type:")
    for k, v in by_type.items():
        print(f"  {k}: {len(v)}")

    one_many = sorted(by_type["1:many"], key=lambda d: (d["n"] != 2, -d["go_rows"]))
    show("1:many - one human gene, several mouse genes (best to test first; 2 orthologs, rich GO):",
         one_many[:8])
    show("1:many with the most mouse orthologs:", sorted(by_type["1:many"], key=lambda d: -d["n"])[:5])
    show("many:many examples:", sorted(by_type["many:many"], key=lambda d: -d["go_rows"])[:5])
    print("\nType a symbol in the search box (source: Homo sapiens, target: Mus musculus).")
    conn.close()


if __name__ == "__main__":
    main()