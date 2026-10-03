from src.database import queries


def resolve_gene(conn, species: str, symbol: str) -> list[dict]:
    """Return all genes in `species` matching the symbol (case-insensitive)."""
    if not symbol or not symbol.strip():
        return []
    return queries.find_genes_by_symbol(conn, species, symbol)
