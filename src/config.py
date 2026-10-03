from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"

PROD_DB = DATA_DIR / "ortholog.db"
PACKED_DB = DATA_DIR / "ortholog.db.gz"  # compressed copy used for deployment
SYNTHETIC_DB = DATA_DIR / "ortholog_synthetic.db"

# MVP: Homo sapiens <-> Mus musculus only
SPECIES = {
    "Homo sapiens": "homo_sapiens",
    "Mus musculus": "mus_musculus",
}


def default_db_path() -> Path:
    """Use the production DB if present, otherwise the synthetic dev DB."""
    return PROD_DB if PROD_DB.exists() else SYNTHETIC_DB