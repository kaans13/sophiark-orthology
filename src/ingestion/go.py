"""Gene Ontology ingestion: go-basic.obo + GOA GAF files (human, mouse).

Identifiers: GAF files are keyed by UniProt accession, but also carry the
gene SYMBOL (DB_Object_Symbol, column 3). Since our `genes` table already
has Ensembl-derived symbols per species (from Phase 2), we match GO
annotations to genes by symbol (case-insensitive) within the same species,
rather than building a separate Ensembl<->UniProt cross-reference table.
This is a deliberate MVP simplification: it is transparent, done once at
build time (never per UI request), and avoids a second fragile network
dependency. The UniProt accession is still stored on the gene row when a
match is found, so it stays visible in the data.
"""
from __future__ import annotations

import gzip
import re
from pathlib import Path

OBO_URL = "http://purl.obolibrary.org/obo/go/go-basic.obo"
GAF_URLS = {
    "Homo sapiens": "https://ftp.ebi.ac.uk/pub/databases/GO/goa/HUMAN/goa_human.gaf.gz",
    "Mus musculus": "https://ftp.ebi.ac.uk/pub/databases/GO/goa/MOUSE/goa_mouse.gaf.gz",
}

ASPECT_TO_NAMESPACE = {
    "P": "biological_process",
    "F": "molecular_function",
    "C": "cellular_component",
}
NAMESPACES = ["biological_process", "molecular_function", "cellular_component"]


# ---------------------------------------------------------------- network
def fetch_url(url: str, timeout: int = 900) -> bytes:
    import requests

    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content


# ---------------------------------------------------------------- OBO parsing
def parse_obo_release(text: str) -> str:
    m = re.search(r"^data-version:\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else "unknown"


def parse_obo(text: str) -> list[dict]:
    """Minimal OBO parser: only [Term] stanzas, only the fields we store."""
    terms = []
    current: dict | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == "[Term]":
            if current is not None:
                terms.append(current)
            current = {"go_id": None, "name": None, "namespace": None, "is_obsolete": 0}
            continue
        if line.startswith("[") and line.endswith("]"):
            if current is not None:
                terms.append(current)
            current = None
            continue
        if current is None or not line:
            continue
        if line.startswith("id:"):
            current["go_id"] = line[3:].strip()
        elif line.startswith("name:"):
            current["name"] = line[5:].strip()
        elif line.startswith("namespace:"):
            current["namespace"] = line[10:].strip()
        elif line.startswith("is_obsolete:"):
            current["is_obsolete"] = 1 if line[12:].strip() == "true" else 0
    if current is not None:
        terms.append(current)
    return [t for t in terms if t["go_id"]]


# ---------------------------------------------------------------- GAF parsing
def is_negated(qualifier: str) -> bool:
    return "NOT" in (qualifier or "").split("|")


def iter_gaf_lines(path: Path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("!") or not line.strip():
                continue
            yield line.rstrip("\n")


def parse_gaf_line(line: str) -> dict | None:
    cols = line.split("\t")
    if len(cols) < 9:
        return None
    symbol, qualifier, go_id, evidence_code, aspect = cols[2], cols[3], cols[4], cols[6], cols[8]
    namespace = ASPECT_TO_NAMESPACE.get(aspect)
    if not symbol or not go_id or not namespace or is_negated(qualifier):
        return None
    synonyms = [s.strip() for s in cols[10].split("|")] if len(cols) > 10 and cols[10] else []
    return {
        "uniprot_id": cols[1] or None,
        "symbol": symbol,
        "synonyms": [s for s in synonyms if s],
        "go_id": go_id,
        "evidence_code": evidence_code or None,
        "namespace": namespace,
    }


def parse_gaf_file(path: Path):
    for line in iter_gaf_lines(path):
        rec = parse_gaf_line(line)
        if rec is not None:
            yield rec


# ---------------------------------------------------------------- loading
def load_go_terms(conn, terms: list[dict]) -> int:
    before = conn.total_changes
    conn.executemany(
        "INSERT OR IGNORE INTO go_terms (go_id, name, namespace, is_obsolete) VALUES (?,?,?,?)",
        [(t["go_id"], t["name"], t["namespace"], t["is_obsolete"]) for t in terms],
    )
    conn.commit()
    return conn.total_changes - before


def _symbol_map(conn, species: str) -> dict[str, list[int]]:
    """Map lowercase symbol -> list of gene IDs.

    Some symbols belong to more than one Ensembl gene row (patches, alt
    haplotypes, gene-family duplicates: ~1% of genes in this dataset). GO
    annotations for that symbol are attached to ALL matching gene IDs so a
    real gene is never silently left with zero annotations because a
    same-named row happened to be inserted later.
    """
    rows = conn.execute(
        "SELECT id, symbol FROM genes WHERE species = ? AND symbol IS NOT NULL", (species,)
    )
    out: dict[str, list[int]] = {}
    for r in rows:
        out.setdefault(r["symbol"].lower(), []).append(r["id"])
    return out


def load_gene_go(conn, species: str, records_iter, release: str, source: str = "GOA",
                 batch_size: int = 50_000):
    """Match GAF records to local genes by symbol (falling back to GAF synonyms
    when the primary symbol has no matching gene - GOA and Ensembl sometimes
    disagree on which name is "primary", e.g. GOA's current mouse Tp53 vs
    Ensembl's Trp53; the GAF lists both as synonyms of the same UniProt entry).

    Deduplicates identical (gene_id, go_id, evidence_code) triples.
    Also backfills genes.uniprot_id the first time a symbol matches.
    Returns (inserted, matched_genes, skipped_no_gene, matched_via_synonym).
    """
    gene_by_symbol = _symbol_map(conn, species)
    seen: set[tuple[int, str, str | None]] = set()
    batch: list[tuple] = []
    uniprot_updates: dict[int, str] = {}
    matched_genes: set[int] = set()
    skipped = 0
    inserted = 0
    via_synonym = 0

    def flush():
        nonlocal batch, inserted
        if batch:
            conn.executemany(
                "INSERT INTO gene_go (gene_id, go_id, evidence_code, source, release) "
                "VALUES (?,?,?,?,?)",
                batch,
            )
            inserted += len(batch)
            batch = []

    for rec in records_iter:
        gene_ids = gene_by_symbol.get(rec["symbol"].lower())
        if not gene_ids:
            for syn in rec.get("synonyms", []):
                gene_ids = gene_by_symbol.get(syn.lower())
                if gene_ids:
                    via_synonym += 1
                    break
        if not gene_ids:
            skipped += 1
            continue
        for gene_id in gene_ids:
            matched_genes.add(gene_id)
            if gene_id not in uniprot_updates and rec["uniprot_id"]:
                uniprot_updates[gene_id] = rec["uniprot_id"]
            key = (gene_id, rec["go_id"], rec["evidence_code"])
            if key in seen:
                continue
            seen.add(key)
            batch.append((gene_id, rec["go_id"], rec["evidence_code"], source, release))
            if len(batch) >= batch_size:
                flush()
    flush()
    conn.executemany(
        "UPDATE genes SET uniprot_id = ? WHERE id = ? AND uniprot_id IS NULL",
        [(v, k) for k, v in uniprot_updates.items()],
    )
    conn.commit()
    return inserted, len(matched_genes), skipped, via_synonym