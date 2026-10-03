"""All SQL used by the services lives here."""


def find_genes_by_symbol(conn, species: str, symbol: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM genes WHERE species = ? AND symbol = ? COLLATE NOCASE",
        (species, symbol.strip()),
    ).fetchall()
    return [dict(r) for r in rows]


_TARGET_COLS = """o.relationship, o.confidence, o.source_db, o.source_release,
       g.id AS target_id, g.ensembl_id AS target_ensembl_id,
       g.symbol AS target_symbol, g.gene_name AS target_gene_name"""


def get_orthologs(conn, source_gene_id: int, target_species: str) -> list[dict]:
    """Orthologs of a gene in `target_species`.

    Uses rows stored in either direction (Compara pairs are symmetric), so a pair
    that only appears in the reverse file is still found. Forward rows win on ties.
    """
    forward = [dict(r) for r in conn.execute(
        f"SELECT {_TARGET_COLS} FROM orthologs o JOIN genes g ON g.id = o.target_gene_id "
        "WHERE o.source_gene_id = ? AND g.species = ?", (source_gene_id, target_species))]
    reverse = [dict(r) for r in conn.execute(
        f"SELECT {_TARGET_COLS} FROM orthologs o JOIN genes g ON g.id = o.source_gene_id "
        "WHERE o.target_gene_id = ? AND g.species = ?", (source_gene_id, target_species))]
    seen = {r["target_id"] for r in forward}
    merged = forward + [r for r in reverse if r["target_id"] not in seen]
    return sorted(merged, key=lambda r: (r["target_symbol"] or "", r["target_ensembl_id"]))


def get_linked_genes(conn, gene_id: int, species: str, exclude_id: int) -> list[dict]:
    """Genes of `species` (other than `exclude_id`) that are orthologs of `gene_id`."""
    rows = conn.execute(
        """
        SELECT g.id, g.ensembl_id, g.symbol
        FROM (SELECT source_gene_id AS gid FROM orthologs WHERE target_gene_id = ?
              UNION
              SELECT target_gene_id AS gid FROM orthologs WHERE source_gene_id = ?) x
        JOIN genes g ON g.id = x.gid
        WHERE g.species = ? AND g.id != ?
        ORDER BY g.symbol
        """,
        (gene_id, gene_id, species, exclude_id),
    ).fetchall()
    return [dict(r) for r in rows]


def get_metadata(conn) -> dict:
    return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM metadata")}