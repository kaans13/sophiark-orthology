import pytest

from src.services.gene_service import resolve_gene
from src.services.orthology_service import find_orthologs
from tests.synthetic_data import HUMAN, MOUSE, build


@pytest.fixture
def conn(tmp_path):
    c = build(tmp_path / "t.db")
    yield c
    c.close()


def _gid(conn, symbol):
    return resolve_gene(conn, HUMAN, symbol)[0]["id"]


def test_one_to_one(conn):
    r = find_orthologs(conn, _gid(conn, "GENEA"), MOUSE)
    assert r["count"] == 1 and r["relationships"] == ["ortholog_one2one"]


def test_one_to_many_kept_separate(conn):
    r = find_orthologs(conn, _gid(conn, "GENEB"), MOUSE)
    assert r["count"] == 2
    assert [t["target_symbol"] for t in r["targets"]] == ["Geneb1", "Geneb2"]


def test_no_ortholog(conn):
    r = find_orthologs(conn, _gid(conn, "GENEC"), MOUSE)
    assert r["found"] is False and r["targets"] == []


def test_symbol_is_case_insensitive(conn):
    assert resolve_gene(conn, HUMAN, "genea")[0]["ensembl_id"] == "ENSG_A"
