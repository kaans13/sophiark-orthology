"""Ensembl Compara orthology ingestion (via Ensembl BioMart bulk export).

Pure parsing/loading functions live here so they can be tested offline.
Network access is isolated in `fetch_biomart` and `fetch_ensembl_release`.
"""
from __future__ import annotations

import re
from xml.sax.saxutils import quoteattr

BIOMART_URL = "https://www.ensembl.org/biomart/martservice"
REST_INFO_URL = "https://rest.ensembl.org/info/software"

# species name -> (BioMart dataset, homolog attribute prefix)
DATASETS = {
    "Homo sapiens": ("hsapiens_gene_ensembl", "hsapiens"),
    "Mus musculus": ("mmusculus_gene_ensembl", "mmusculus"),
}

GENE_ATTRIBUTES = ["ensembl_gene_id", "external_gene_name", "description"]


def homolog_attributes(target_prefix: str) -> list[str]:
    return [
        "ensembl_gene_id",
        "external_gene_name",
        f"{target_prefix}_homolog_ensembl_gene",
        f"{target_prefix}_homolog_associated_gene_name",
        f"{target_prefix}_homolog_orthology_type",
        f"{target_prefix}_homolog_orthology_confidence",
    ]


# ---------------------------------------------------------------- network
def build_query(dataset: str, attributes: list[str]) -> str:
    attrs = "".join(f"<Attribute name={quoteattr(a)}/>" for a in attributes)
    return (
        '<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE Query>'
        '<Query virtualSchemaName="default" formatter="TSV" header="0" '
        'uniqueRows="1" count="" datasetConfigVersion="0.6">'
        f"<Dataset name={quoteattr(dataset)} interface=\"default\">{attrs}</Dataset></Query>"
    )


def check_biomart_response(text: str) -> str:
    if text.lstrip().startswith(("Query ERROR", "Problem retrieving", "<html", "<!DOCTYPE")):
        raise RuntimeError(f"BioMart returned an error: {text[:200]!r}")
    return text


def fetch_biomart(dataset: str, attributes: list[str], timeout: int = 600) -> str:
    import requests

    resp = requests.get(
        BIOMART_URL,
        params={"query": build_query(dataset, attributes)},
        timeout=timeout,
    )
    resp.raise_for_status()
    return check_biomart_response(resp.text)


def fetch_ensembl_release(timeout: int = 60) -> str:
    import requests

    resp = requests.get(REST_INFO_URL, headers={"Content-Type": "application/json"}, timeout=timeout)
    resp.raise_for_status()
    release = resp.json().get("release")
    if not release:
        raise RuntimeError("Ensembl REST /info/software returned no release number")
    return str(release)


# ---------------------------------------------------------------- parsing
def clean_description(desc: str) -> str:
    """Strip the trailing '[Source:HGNC Symbol;Acc:...]' tag from Ensembl descriptions."""
    return re.sub(r"\s*\[Source:[^\]]*\]\s*$", "", desc or "").strip()


def confidence_label(value: str) -> str | None:
    return {"1": "high", "0": "low"}.get((value or "").strip())


def _rows(text: str, ncols: int):
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        parts += [""] * (ncols - len(parts))
        yield [p.strip() for p in parts[:ncols]]


def parse_gene_table(text: str) -> list[dict]:
    genes = []
    for ens_id, symbol, desc in _rows(text, 3):
        if not ens_id:
            continue
        genes.append({"ensembl_id": ens_id, "symbol": symbol or None,
                      "gene_name": clean_description(desc) or None})
    return genes


def parse_homolog_table(text: str) -> list[dict]:
    """Rows with an empty target gene (no homolog) are dropped."""
    out = []
    for src_id, src_sym, tgt_id, tgt_sym, rel, conf in _rows(text, 6):
        if not src_id or not tgt_id:
            continue
        out.append({
            "source_ensembl_id": src_id, "source_symbol": src_sym or None,
            "target_ensembl_id": tgt_id, "target_symbol": tgt_sym or None,
            "relationship": rel or None, "confidence": confidence_label(conf),
        })
    return out


# ---------------------------------------------------------------- loading
def load_genes(conn, species: str, genes: list[dict]) -> int:
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO genes (species, ensembl_id, symbol, gene_name) VALUES (?,?,?,?)",
        [(species, g["ensembl_id"], g["symbol"], g["gene_name"]) for g in genes],
    )
    conn.commit()
    return conn.total_changes - before


def _id_map(conn, species: str) -> dict[str, int]:
    return {r["ensembl_id"]: r["id"]
            for r in conn.execute("SELECT id, ensembl_id FROM genes WHERE species = ?", (species,))}


def load_orthologs(conn, source_species: str, target_species: str,
                   rows: list[dict], release: str, source_db: str = "Ensembl Compara"):
    """Insert ortholog rows. Returns (inserted, skipped_unknown_gene)."""
    src_map, tgt_map = _id_map(conn, source_species), _id_map(conn, target_species)
    batch, skipped = [], 0
    for r in rows:
        s, t = src_map.get(r["source_ensembl_id"]), tgt_map.get(r["target_ensembl_id"])
        if s is None or t is None:
            skipped += 1
            continue
        batch.append((s, t, r["relationship"], r["confidence"], source_db, release))
    conn.executemany("INSERT INTO orthologs VALUES (?,?,?,?,?,?)", batch)
    conn.commit()
    return len(batch), skipped