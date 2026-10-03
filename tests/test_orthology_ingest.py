import pytest

from src.database.connection import create_database
from src.ingestion import orthology as orth
from src.services.gene_service import resolve_gene
from src.services.orthology_service import find_orthologs

HUMAN, MOUSE = "Homo sapiens", "Mus musculus"

HUMAN_GENES = "ENSG1\tGENEA\tgene A [Source:HGNC Symbol;Acc:HGNC:1]\nENSG2\tGENEB\tgene B\nENSG3\tGENEC\t\n"
MOUSE_GENES = "ENSMUSG1\tGenea\tgene a\nENSMUSG2\tGeneb1\t\nENSMUSG3\tGeneb2\t\n"
H2M = (
    "ENSG1\tGENEA\tENSMUSG1\tGenea\tortholog_one2one\t1\n"
    "ENSG2\tGENEB\tENSMUSG2\tGeneb1\tortholog_one2many\t1\n"
    "ENSG2\tGENEB\tENSMUSG3\tGeneb2\tortholog_one2many\t0\n"
    "ENSG3\tGENEC\t\t\t\t\n"
    "ENSG9\tGHOST\tENSMUSG1\tGenea\tortholog_one2one\t1\n"
)
M2H = (
    "ENSMUSG1\tGenea\tENSG1\tGENEA\tortholog_one2one\t1\n"
    "ENSMUSG2\tGeneb1\tENSG2\tGENEB\tortholog_many2one\t1\n"
)


@pytest.fixture
def conn(tmp_path):
    c = create_database(tmp_path / "t.db")
    orth.load_genes(c, HUMAN, orth.parse_gene_table(HUMAN_GENES))
    orth.load_genes(c, MOUSE, orth.parse_gene_table(MOUSE_GENES))
    orth.load_orthologs(c, HUMAN, MOUSE, orth.parse_homolog_table(H2M), "115")
    orth.load_orthologs(c, MOUSE, HUMAN, orth.parse_homolog_table(M2H), "115")
    yield c
    c.close()


def test_description_source_tag_removed():
    genes = orth.parse_gene_table(HUMAN_GENES)
    assert genes[0]["gene_name"] == "gene A"
    assert genes[2]["gene_name"] is None


def test_homolog_rows_without_target_dropped():
    assert len(orth.parse_homolog_table(H2M)) == 4


def test_confidence_labels():
    assert orth.confidence_label("1") == "high"
    assert orth.confidence_label("0") == "low"
    assert orth.confidence_label("") is None


def test_unknown_source_gene_skipped(tmp_path):
    c = create_database(tmp_path / "x.db")
    orth.load_genes(c, HUMAN, orth.parse_gene_table(HUMAN_GENES))
    orth.load_genes(c, MOUSE, orth.parse_gene_table(MOUSE_GENES))
    ins, skipped = orth.load_orthologs(c, HUMAN, MOUSE, orth.parse_homolog_table(H2M), "115")
    assert (ins, skipped) == (3, 1)


def test_one_to_one_and_release_stored(conn):
    g = resolve_gene(conn, HUMAN, "GENEA")[0]
    r = find_orthologs(conn, g["id"], MOUSE)
    assert r["count"] == 1
    assert r["targets"][0]["source_release"] == "115"
    assert r["targets"][0]["confidence"] == "high"


def test_one_to_many_separate_targets(conn):
    g = resolve_gene(conn, HUMAN, "GENEB")[0]
    r = find_orthologs(conn, g["id"], MOUSE)
    assert [t["target_symbol"] for t in r["targets"]] == ["Geneb1", "Geneb2"]
    assert r["relationships"] == ["ortholog_one2many"]


def test_no_ortholog(conn):
    g = resolve_gene(conn, HUMAN, "GENEC")[0]
    assert find_orthologs(conn, g["id"], MOUSE)["found"] is False


def test_reverse_direction_uses_source_perspective(conn):
    g = resolve_gene(conn, MOUSE, "Geneb1")[0]
    r = find_orthologs(conn, g["id"], HUMAN)
    assert r["relationships"] == ["ortholog_many2one"]


def test_query_xml_contains_dataset_and_attributes():
    xml = orth.build_query("hsapiens_gene_ensembl", orth.homolog_attributes("mmusculus"))
    assert 'name="hsapiens_gene_ensembl"' in xml
    assert "mmusculus_homolog_orthology_type" in xml


def test_biomart_error_detected():
    with pytest.raises(RuntimeError):
        orth.check_biomart_response("Query ERROR: caught BioMart::Exception")
