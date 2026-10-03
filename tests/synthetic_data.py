"""Small synthetic dataset. No network needed."""
from src.database.connection import create_database

HUMAN, MOUSE = "Homo sapiens", "Mus musculus"


def build(db_path):
    conn = create_database(db_path)
    genes = [
        (1, HUMAN, "ENSG_A", "GENEA", "synthetic gene A", "P00001"),
        (2, MOUSE, "ENSMUSG_A", "Genea", "synthetic gene A (mouse)", "Q00001"),
        (3, HUMAN, "ENSG_B", "GENEB", "synthetic gene B", "P00002"),
        (4, MOUSE, "ENSMUSG_B1", "Geneb1", "synthetic gene B1", "Q00002"),
        (5, MOUSE, "ENSMUSG_B2", "Geneb2", "synthetic gene B2", "Q00003"),
        (6, HUMAN, "ENSG_C", "GENEC", "synthetic gene C (no ortholog)", "P00003"),
    ]
    conn.executemany("INSERT INTO genes VALUES (?,?,?,?,?,?)", genes)
    orth = [
        (1, 2, "ortholog_one2one", "1", "synthetic", "test"),
        (3, 4, "ortholog_one2many", "1", "synthetic", "test"),
        (3, 5, "ortholog_one2many", "0", "synthetic", "test"),
    ]
    conn.executemany("INSERT INTO orthologs VALUES (?,?,?,?,?,?)", orth)
    conn.executemany(
        "INSERT INTO metadata VALUES (?,?)",
        [("dataset", "synthetic test data"), ("ensembl_release", "n/a")],
    )
    conn.commit()
    return conn
