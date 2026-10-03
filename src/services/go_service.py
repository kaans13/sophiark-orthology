from src.ingestion.go import NAMESPACES


def get_annotations(conn, gene_id: int) -> dict[str, list[dict]]:
    """GO annotations for one gene, grouped by namespace."""
    rows = conn.execute(
        """
        SELECT g.go_id, t.name, t.namespace, g.evidence_code
        FROM gene_go g JOIN go_terms t ON t.go_id = g.go_id
        WHERE g.gene_id = ?
        ORDER BY t.namespace, g.go_id
        """,
        (gene_id,),
    ).fetchall()
    out: dict[str, list[dict]] = {ns: [] for ns in NAMESPACES}
    for r in rows:
        out[r["namespace"]].append(
            {"go_id": r["go_id"], "name": r["name"], "evidence_code": r["evidence_code"]}
        )
    return out


def get_go_id_sets(conn, gene_id: int) -> dict[str, set[str]]:
    annotations = get_annotations(conn, gene_id)
    return {ns: {a["go_id"] for a in terms} for ns, terms in annotations.items()}


def aggregate_by_term(annotations: list[dict]) -> dict[str, dict]:
    """Collapse per-evidence rows into one entry per GO term with all its evidence codes."""
    out: dict[str, dict] = {}
    for a in annotations:
        entry = out.setdefault(
            a["go_id"], {"go_id": a["go_id"], "name": a["name"], "evidence": set()}
        )
        if a["evidence_code"]:
            entry["evidence"].add(a["evidence_code"])
    for entry in out.values():
        entry["evidence"] = sorted(entry["evidence"])
    return out