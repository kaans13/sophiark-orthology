import streamlit as st
from streamlit_searchbox import st_searchbox

from src.config import SPECIES


def suggest_symbols(conn, species: str, prefix: str, limit: int = 15) -> list[str]:
    if not prefix or not prefix.strip():
        return []
    rows = conn.execute(
        "SELECT DISTINCT symbol FROM genes WHERE species = ? AND symbol LIKE ? "
        "ORDER BY symbol LIMIT ?",
        (species, prefix.strip() + "%", limit),
    ).fetchall()
    return [r["symbol"] for r in rows]


def render_search(conn) -> dict | None:
    """Render the search form. The gene field live-filters as the user types."""
    names = list(SPECIES.keys())
    c1, c2 = st.columns(2)
    source = c1.selectbox("Source species", names, index=0)
    target = c2.selectbox("Target species", names, index=1)

    symbol = st_searchbox(
        lambda term: suggest_symbols(conn, source, term),
        placeholder="Type a gene symbol, e.g. TP53",
        label="Gene symbol",
        key="gene_symbol_searchbox",
    )

    submitted = st.button("→ Compare", type="primary")
    if not submitted:
        return None
    if source == target:
        st.error("Source and target species must be different.")
        return None
    if not symbol or not symbol.strip():
        st.error("Please enter a gene symbol.")
        return None
    return {"source": source, "target": target, "symbol": symbol.strip()}