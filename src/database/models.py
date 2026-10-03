"""SQLite schema. Kept as plain SQL for transparency."""

SCHEMA = """
CREATE TABLE IF NOT EXISTS genes (
    id INTEGER PRIMARY KEY,
    species TEXT NOT NULL,
    ensembl_id TEXT NOT NULL,
    symbol TEXT,
    gene_name TEXT,
    uniprot_id TEXT,
    UNIQUE (species, ensembl_id)
);
CREATE INDEX IF NOT EXISTS idx_genes_species_symbol ON genes (species, symbol COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS orthologs (
    source_gene_id INTEGER NOT NULL REFERENCES genes(id),
    target_gene_id INTEGER NOT NULL REFERENCES genes(id),
    relationship TEXT,
    confidence TEXT,
    source_db TEXT,
    source_release TEXT
);
CREATE INDEX IF NOT EXISTS idx_orthologs_source ON orthologs (source_gene_id);
CREATE INDEX IF NOT EXISTS idx_orthologs_target ON orthologs (target_gene_id);

CREATE TABLE IF NOT EXISTS go_terms (
    go_id TEXT PRIMARY KEY,
    name TEXT,
    namespace TEXT,
    is_obsolete INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS gene_go (
    gene_id INTEGER NOT NULL REFERENCES genes(id),
    go_id TEXT NOT NULL REFERENCES go_terms(go_id),
    evidence_code TEXT,
    source TEXT,
    release TEXT
);
CREATE INDEX IF NOT EXISTS idx_gene_go_gene ON gene_go (gene_id);

CREATE TABLE IF NOT EXISTS pathways (
    pathway_id TEXT PRIMARY KEY,
    name TEXT,
    species TEXT,
    source TEXT,
    release TEXT
);

CREATE TABLE IF NOT EXISTS gene_pathways (
    gene_id INTEGER NOT NULL REFERENCES genes(id),
    pathway_id TEXT NOT NULL REFERENCES pathways(pathway_id),
    source TEXT
);
CREATE INDEX IF NOT EXISTS idx_gene_pathways_gene ON gene_pathways (gene_id);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""