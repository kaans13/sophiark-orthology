from src.database import queries


def classify_relationship(n_targets: int, max_sources_per_target: int) -> str | None:
    """Relationship type from the actual gene counts, seen from the searched (source) gene.

    Ensembl's own label (one2many ...) does not say which species is the 'many' side,
    so we derive it: number of orthologs found for the source gene, and how many
    source-species genes each of those orthologs is linked to.
    """
    if n_targets == 0:
        return None
    if n_targets == 1:
        return "1:1" if max_sources_per_target <= 1 else "many:1"
    return "1:many" if max_sources_per_target <= 1 else "many:many"


def find_orthologs(conn, source_gene_id: int, target_species: str) -> dict:
    """Look up orthologs of a source gene in the target species.

    Each target is kept separate; `also_linked` lists other source-species genes
    that share that same target ortholog (e.g. FCGR3A and FCGR3B -> Fcgr4).
    """
    row = conn.execute("SELECT species FROM genes WHERE id = ?", (source_gene_id,)).fetchone()
    source_species = row["species"] if row else None

    targets = queries.get_orthologs(conn, source_gene_id, target_species)
    for t in targets:
        t["also_linked"] = (
            queries.get_linked_genes(conn, t["target_id"], source_species, source_gene_id)
            if source_species else []
        )

    max_sources = max((len(t["also_linked"]) + 1 for t in targets), default=0)
    return {
        "found": len(targets) > 0,
        "count": len(targets),
        "relationship_type": classify_relationship(len(targets), max_sources),
        "relationships": sorted({t["relationship"] for t in targets if t["relationship"]}),
        "targets": targets,
    }