# Ortholog Detective

Compare a gene with its ortholog(s) in another species using Ensembl Compara
orthology and Gene Ontology annotation overlap.

**MVP scope:** Homo sapiens <-> Mus musculus only. English-only interface.

> Annotation overlap reflects database annotations and should not be interpreted
> as evidence of functional equivalence.

## Status

Phase 1 (structure, schema, synthetic data, search UI) and Phase 2 (Ensembl orthology ingestion) are complete.

## Quick start (Windows)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_synthetic.py
streamlit run app.py
```

Try the synthetic genes: `GENEA` (1:1), `GENEB` (1:many), `GENEC` (no ortholog).

## Build the real orthology database (Phase 2)

```
python scripts/download_orthology.py
python scripts/build_database.py
streamlit run app.py
```

The app automatically uses `data/ortholog.db` when it exists, otherwise the synthetic DB.
Orthology comes from Ensembl Compara through BioMart; the Ensembl release and download
date are stored in the `metadata` table and shown in the app.

## Tests

```
pytest
```

## Roadmap

1. Structure, schema, synthetic data, search UI  (done)
2. Ensembl orthology ingestion  (done)
3. GO ingestion + Ensembl<->UniProt mapping + comparison
4. Result UI, overlap metrics, CSV/JSON export
5. Optional Reactome pathways
6. Tests, README, reproducible data build
