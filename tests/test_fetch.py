import gzip
import shutil

import pytest

from src.database import fetch
from tests.synthetic_data import build


@pytest.fixture
def paths(tmp_path, monkeypatch):
    db = tmp_path / "data" / "ortholog.db"
    packed = tmp_path / "data" / "ortholog.db.gz"
    monkeypatch.setattr(fetch, "PROD_DB", db)
    monkeypatch.setattr(fetch, "PACKED_DB", packed)
    monkeypatch.delenv("ORTHOLOG_DB_URL", raising=False)
    monkeypatch.setattr(fetch, "_db_url", lambda: None)
    return db, packed


def _make_gz(tmp_path, dest):
    src = tmp_path / "src.db"
    build(src).close()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as f_in, gzip.open(dest, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def test_existing_database_is_used_as_is(paths, tmp_path):
    db, _ = paths
    db.parent.mkdir(parents=True)
    build(db).close()
    assert fetch.ensure_database() == db


def test_packed_database_is_unpacked(paths, tmp_path):
    db, packed = paths
    _make_gz(tmp_path, packed)
    assert fetch.ensure_database() == db and db.exists()
    assert not list(db.parent.glob("*.part"))


def test_no_source_returns_none(paths):
    assert fetch.ensure_database() is None


def test_download_when_url_configured(paths, tmp_path, monkeypatch):
    db, packed = paths
    source_gz = tmp_path / "remote.gz"
    _make_gz(tmp_path, source_gz)
    calls = []

    def fake_download(url, dest):
        calls.append(url)
        shutil.copy(source_gz, dest)

    monkeypatch.setattr(fetch, "_db_url", lambda: "https://example.com/ortholog.db.gz")
    monkeypatch.setattr(fetch, "download", fake_download)
    assert fetch.ensure_database() == db
    assert calls == ["https://example.com/ortholog.db.gz"]


def test_corrupt_archive_raises_and_leaves_no_database(paths):
    db, packed = paths
    packed.parent.mkdir(parents=True)
    packed.write_bytes(b"this is not a gzip file")
    with pytest.raises(Exception):
        fetch.ensure_database()
    assert not db.exists()