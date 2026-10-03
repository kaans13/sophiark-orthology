from src.analysis.overlap import compare_sets
from src.ingestion.go import NAMESPACES
from src.services.go_service import aggregate_by_term, get_annotations


def compare_gene_pair(conn, source_gene_id: int, target_gene_id: int) -> dict:
    """Per-namespace GO annotation overlap between two genes (one ortholog pair).

    Each term carries ALL evidence codes seen for that gene (lists, sorted).
    """
    src_ann = get_annotations(conn, source_gene_id)
    tgt_ann = get_annotations(conn, target_gene_id)

    result = {}
    for ns in NAMESPACES:
        src_terms = aggregate_by_term(src_ann[ns])
        tgt_terms = aggregate_by_term(tgt_ann[ns])
        overlap = compare_sets(set(src_terms), set(tgt_terms))

        def enrich(go_ids):
            rows = []
            for gid in go_ids:
                base = src_terms.get(gid) or tgt_terms.get(gid)
                rows.append({
                    "go_id": gid,
                    "name": base["name"],
                    "source_evidence": src_terms.get(gid, {}).get("evidence", []),
                    "target_evidence": tgt_terms.get(gid, {}).get("evidence", []),
                })
            return sorted(rows, key=lambda r: r["go_id"])

        result[ns] = {
            "shared": enrich(overlap["shared"]),
            "source_only": enrich(overlap["source_only"]),
            "target_only": enrich(overlap["target_only"]),
            "jaccard": overlap["jaccard"],
            "shared_count": len(overlap["shared"]),
            "source_only_count": len(overlap["source_only"]),
            "target_only_count": len(overlap["target_only"]),
        }
    return result