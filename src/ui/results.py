"""Result page: card-based layout, one block per ortholog gene (rendered with st.markdown HTML)."""
from html import escape

import streamlit as st

from src.database.queries import get_metadata
from src.services.comparison_service import compare_gene_pair
from src.services.go_service import aggregate_by_term, get_annotations
from src.services.orthology_service import find_orthologs
from src.ui import go_panel

NS_LABEL = {
    "biological_process": "Biological Process",
    "molecular_function": "Molecular Function",
    "cellular_component": "Cellular Component",
}
META_LABELS = {
    "ensembl_release": "Ensembl release",
    "ensembl_download_date": "Orthology downloaded",
    "orthology_source": "Orthology source",
    "go_release": "GO release",
    "go_download_date": "GO downloaded",
    "go_source": "GO source",
}
NOTE = ("Annotation overlap reflects database annotations and should not be "
        "interpreted as evidence of functional equivalence.")


def _conf(confidence) -> str:
    if not confidence:
        return ""
    c = escape(str(confidence))
    return f'<span class="od-conf od-conf-{c}">{c} confidence</span>'


def _also(target: dict, source_species: str) -> str:
    linked = target.get("also_linked") or []
    if not linked:
        return ""
    names = ", ".join(escape(g["symbol"] or g["ensembl_id"]) for g in linked)
    return f'<div class="od-also">Also the ortholog of ({escape(source_species)}): {names}</div>'


def hero_html(gene: dict, source_species: str, target_species: str, orth: dict) -> str:
    sym = escape(gene["symbol"] or gene["ensembl_id"])
    desc = f'<div class="od-desc">{escape(gene["gene_name"])}</div>' if gene.get("gene_name") else ""
    left = (f'<div><div class="od-species">{escape(source_species)}</div><div class="od-symbol">{sym}</div>'
            f'<div class="od-sub">{escape(gene["ensembl_id"])}</div>{desc}</div>')

    if orth["found"]:
        n = orth["count"]
        labels = ", ".join(r.replace("ortholog_", "") for r in orth["relationships"])
        ensembl = f'<div class="od-sub">Ensembl label: {escape(labels)}</div>' if labels else ""
        middle = (f'<div class="od-link"><div class="od-arrow">&rarr;</div>'
                  f'<span class="od-badge">{escape(orth["relationship_type"])} ortholog</span>'
                  f'<div class="od-sub">{n} ortholog{"s" if n != 1 else ""} found</div>{ensembl}</div>')
        items = "".join(
            f'<div class="od-tgt"><div class="od-symbol od-symbol-sm">'
            f'{escape(t["target_symbol"] or t["target_ensembl_id"])}</div>'
            f'<div class="od-sub">{escape(t["target_ensembl_id"])}</div>'
            + (f'<div class="od-desc">{escape(t["target_gene_name"])}</div>' if t.get("target_gene_name") else "")
            + _conf(t.get("confidence")) + _also(t, source_species) + '</div>'
            for t in orth["targets"]
        )
        right = f'<div><div class="od-species">{escape(target_species)}</div>{items}</div>'
    else:
        middle = '<div class="od-link"><div class="od-arrow od-arrow-off">&times;</div></div>'
        right = (f'<div><div class="od-species">{escape(target_species)}</div>'
                 f'<div class="od-desc">No ortholog found in the selected target species.</div></div>')
    return f'<div class="od-card od-hero od-fade">{left}{middle}{right}</div>'


def _render_pair(conn, gene: dict, target: dict) -> None:
    src = gene["symbol"] or gene["ensembl_id"]
    tgt = target["target_symbol"] or target["target_ensembl_id"]
    comp = compare_gene_pair(conn, gene["id"], target["target_id"])

    cards = "".join(
        go_panel.summary_card(NS_LABEL[ns], comp[ns], src, tgt, delay=0.08 * i)
        for i, ns in enumerate(NS_LABEL)
    )
    st.markdown(f'<div class="od-grid3">{cards}</div>', unsafe_allow_html=True)

    st.markdown('<div class="od-section-title">Explore the annotations</div>' + go_panel.evidence_legend_html(),
                unsafe_allow_html=True)
    tabs = st.tabs(list(NS_LABEL.values()))
    for tab, ns in zip(tabs, NS_LABEL):
        with tab:
            c = comp[ns]
            html = (
                go_panel.term_group("Shared by both genes", c["shared"], "shared", src, tgt, open_=True)
                + go_panel.term_group(f"Only in {src}", c["source_only"], "source", src, tgt)
                + go_panel.term_group(f"Only in {tgt}", c["target_only"], "target", src, tgt)
            )
            st.markdown(html, unsafe_allow_html=True)


def _render_source_only(conn, gene: dict) -> None:
    sym = gene["symbol"] or gene["ensembl_id"]
    own = get_annotations(conn, gene["id"])
    st.markdown(f'<div class="od-section-title">GO annotations for {escape(sym)}</div>'
                + go_panel.evidence_legend_html(), unsafe_allow_html=True)
    tabs = st.tabs([f"{NS_LABEL[ns]} ({len(aggregate_by_term(own[ns]))})" for ns in NS_LABEL])
    for tab, ns in zip(tabs, NS_LABEL):
        with tab:
            terms = [
                {"go_id": t["go_id"], "name": t["name"], "source_evidence": t["evidence"], "target_evidence": []}
                for t in aggregate_by_term(own[ns]).values()
            ]
            st.markdown(go_panel.term_group(f"{sym} annotations", terms, "source", sym, "", open_=True),
                        unsafe_allow_html=True)


def render_gene_result(conn, gene: dict, source_species: str, target_species: str) -> None:
    orth = find_orthologs(conn, gene["id"], target_species)
    st.markdown(hero_html(gene, source_species, target_species, orth), unsafe_allow_html=True)

    if not orth["found"]:
        _render_source_only(conn, gene)
        return

    targets = orth["targets"]
    if len(targets) == 1:
        _render_pair(conn, gene, targets[0])
    else:
        st.markdown(f'<div class="od-section-title">{len(targets)} orthologs &mdash; each compared separately</div>',
                    unsafe_allow_html=True)
        tabs = st.tabs([t["target_symbol"] or t["target_ensembl_id"] for t in targets])
        for tab, target in zip(tabs, targets):
            with tab:
                _render_pair(conn, gene, target)


def render_footer(conn) -> None:
    st.markdown(f'<div class="od-note">{escape(NOTE)}</div>', unsafe_allow_html=True)
    with st.expander("Data sources & versions"):
        rows = "".join(
            f'<span>{escape(META_LABELS.get(k, k))}</span><span>{escape(str(v))}</span>'
            for k, v in get_metadata(conn).items()
        )
        st.markdown(f'<div class="od-kvs">{rows}</div>', unsafe_allow_html=True)