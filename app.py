import streamlit as st

from src.config import default_db_path
from src.database.connection import connect
from src.database.fetch import ensure_database
from src.services.gene_service import resolve_gene
from src.ui import branding, results
from src.ui.search import render_search
from src.ui.styles import CSS

st.set_page_config(page_title=branding.APP_NAME, page_icon=branding.page_icon(), layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
branding.render_header()


@st.cache_resource(show_spinner="Preparing the database (first start only, this can take a minute)...")
def _database_path() -> str | None:
    path = ensure_database()
    return str(path) if path else None


def _resolve_db() -> str | None:
    try:
        path = _database_path()
    except Exception as exc:  # download / unpack problems
        st.error(f"Could not prepare the database: {exc}")
        return None
    if path:
        return path
    fallback = default_db_path()
    return str(fallback) if fallback.exists() else None


db_path = _resolve_db()
if not db_path:
    st.warning("No database found. Run `python scripts/build_database.py` first.")
    branding.render_footer()
    st.stop()

conn = connect(db_path)
try:
    query = render_search(conn)
    if query:
        genes = resolve_gene(conn, query["source"], query["symbol"])
        if not genes:
            st.error(f"Gene '{query['symbol']}' was not found in {query['source']}.")
        else:
            for gene in genes:
                results.render_gene_result(conn, gene, query["source"], query["target"])
            results.render_footer(conn)
finally:
    conn.close()

branding.render_footer()