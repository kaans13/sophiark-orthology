"""Build data/ortholog.db from downloaded raw files.

Phase 2: genes + orthologs. Phase 3: GO terms + gene_go (symbol-matched).
Usage: python scripts/build_database.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PROD_DB, RAW_DIR  # noqa: E402
from src.database.connection import create_database  # noqa: E402
from src.ingestion import go as go_ingest  # noqa: E402
from src.ingestion import orthology as orth  # noqa: E402

ORTH_DIR = RAW_DIR / "orthology"
GO_DIR = RAW_DIR / "go"
HUMAN, MOUSE = "Homo sapiens", "Mus musculus"


def read(name: str) -> str:
    return (ORTH_DIR / name).read_text(encoding="utf-8")


def build_orthology(conn) -> None:
    manifest = json.loads(read("manifest.json"))
    release = manifest["ensembl_release"]

    for species, fname in ((HUMAN, "human_genes.tsv"), (MOUSE, "mouse_genes.tsv")):
        n = orth.load_genes(conn, species, orth.parse_gene_table(read(fname)))
        print(f"{species}: {n} genes")

    for src, tgt, fname in ((HUMAN, MOUSE, "human_to_mouse.tsv"), (MOUSE, HUMAN, "mouse_to_human.tsv")):
        rows = orth.parse_homolog_table(read(fname))
        ins, skipped = orth.load_orthologs(conn, src, tgt, rows, release)
        print(f"{src} -> {tgt}: {ins} ortholog rows ({skipped} skipped, unknown gene)")

    rel_counts = conn.execute(
        "SELECT relationship, COUNT(*) AS n FROM orthologs GROUP BY relationship ORDER BY n DESC"
    ).fetchall()
    print("Relationship types found in the data:")
    for r in rel_counts:
        print(f"  {r['relationship']}: {r['n']}")


    conn.executemany(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        [("ensembl_release", release),
         ("ensembl_download_date", manifest["download_date"]),
         ("orthology_source", manifest["source"])],
    )
    conn.commit()


def build_go(conn) -> None:
    manifest = json.loads((GO_DIR / "manifest.json").read_text(encoding="utf-8"))
    release = manifest["go_release"]

    obo_text = (GO_DIR / "go-basic.obo").read_text(encoding="utf-8", errors="replace")
    terms = go_ingest.parse_obo(obo_text)
    n_terms = go_ingest.load_go_terms(conn, terms)
    print(f"GO terms: {n_terms} loaded ({len(terms)} parsed)")

    gaf_files = {HUMAN: "goa_human.gaf.gz", MOUSE: "goa_mouse.gaf.gz"}
    for species, fname in gaf_files.items():
        records = go_ingest.parse_gaf_file(GO_DIR / fname)
        inserted, matched_genes, skipped, via_synonym = go_ingest.load_gene_go(conn, species, records, release)
        print(f"{species}: {inserted} gene_go rows, {matched_genes} genes annotated "
              f"({via_synonym} matched via a GAF synonym, not the primary symbol), "
              f"{skipped} annotation lines skipped (symbol not found)")

    conn.executemany(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        [("go_release", release),
         ("go_download_date", manifest["download_date"]),
         ("go_source", "Gene Ontology (go-basic.obo) + GOA GAF (EBI)")],
    )
    conn.commit()


def main() -> None:
    if not (ORTH_DIR / "manifest.json").exists():
        sys.exit("Raw orthology files not found. Run scripts/download_orthology.py first.")
    if PROD_DB.exists():
        PROD_DB.unlink()
    conn = create_database(PROD_DB)
    build_orthology(conn)

    if (GO_DIR / "manifest.json").exists():
        build_go(conn)
    else:
        print("Raw GO files not found, skipping GO ingestion "
              "(run scripts/download_go.py to add GO annotations).")

    conn.close()
    print(f"Database written to {PROD_DB}")


if __name__ == "__main__":
    main()