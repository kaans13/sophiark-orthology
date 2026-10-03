# data/

Local data lives here and is NOT committed to git (see `.gitignore`).

- `ortholog.db` : production SQLite database (built by `scripts/build_database.py`, Phase 2-3)
- `ortholog_synthetic.db` : tiny synthetic database for development (built by `scripts/seed_synthetic.py`)
- `raw/` : downloaded source files (GAF, OBO, Ensembl exports)
