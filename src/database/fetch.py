"""Make sure the SQLite database exists on a fresh server.

Hosted deployments start with only the Git repository, so data/ortholog.db is not there.
Order of preference:
  1. data/ortholog.db already exists            -> use it
  2. data/ortholog.db.gz exists (committed)     -> unpack it
  3. a download URL is configured               -> download the .gz, then unpack it
     (environment variable ORTHOLOG_DB_URL, or the same key in Streamlit secrets)
"""
import gzip
import os
import shutil
import sqlite3
from pathlib import Path

from src.config import PACKED_DB, PROD_DB

CHUNK = 1024 * 1024


def _db_url() -> str | None:
    url = os.environ.get("ORTHOLOG_DB_URL")
    if url:
        return url
    try:
        import streamlit as st

        return st.secrets.get("ORTHOLOG_DB_URL")
    except Exception:
        return None


def download(url: str, dest: Path) -> None:
    import requests

    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(CHUNK):
                f.write(chunk)
    os.replace(tmp, dest)


def unpack(gz_path: Path, db_path: Path) -> None:
    tmp = db_path.with_suffix(".part")
    try:
        with gzip.open(gz_path, "rb") as src, open(tmp, "wb") as dst:
            shutil.copyfileobj(src, dst, CHUNK)
        os.replace(tmp, db_path)
    finally:
        if tmp.exists():
            tmp.unlink()


def verify_database(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        n = conn.execute("SELECT COUNT(*) FROM genes").fetchone()[0]
    finally:
        conn.close()
    if n == 0:
        raise RuntimeError("the database is empty")


def ensure_database() -> Path | None:
    """Return the path of a usable database, preparing it if needed. None if no source is available."""
    if PROD_DB.exists():
        return PROD_DB
    PROD_DB.parent.mkdir(parents=True, exist_ok=True)

    if not PACKED_DB.exists():
        url = _db_url()
        if not url:
            return None
        download(url, PACKED_DB)

    try:
        unpack(PACKED_DB, PROD_DB)
        verify_database(PROD_DB)
    except Exception:
        if PROD_DB.exists():
            PROD_DB.unlink()
        raise
    return PROD_DB