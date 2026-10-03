"""HTML building blocks for GO annotation cards (rendered with st.markdown).

Every builder returns ONE line of HTML (no newlines / blank lines), because a blank
line would end the raw-HTML block in Markdown and break the layout.
"""
from html import escape

# GO evidence code groups (Gene Ontology Consortium categories)
EVIDENCE_GROUPS = {
    "exp": {"EXP", "IDA", "IPI", "IMP", "IGI", "IEP", "HTP", "HDA", "HMP", "HGI", "HEP"},
    "inf": {"ISS", "ISO", "ISA", "ISM", "IGC", "RCA", "IBA", "IBD", "IKR", "IRD"},
    "auth": {"TAS", "NAS", "IC", "ND"},
    "iea": {"IEA"},
}
EVIDENCE_LEGEND = [
    ("exp", "Experimental"),
    ("inf", "Inferred"),
    ("auth", "Author / curator"),
    ("iea", "Automatic (IEA)"),
]


def evidence_class(code: str) -> str:
    for cls, codes in EVIDENCE_GROUPS.items():
        if code in codes:
            return cls
    return "iea"


def _badges(codes, who: str) -> str:
    return "".join(
        f'<span class="od-ev od-ev-{evidence_class(c)}" title="{escape(who)}: {escape(c)}">{escape(c)}</span>'
        for c in (codes or [])
    )


def evidence_legend_html() -> str:
    items = "".join(f'<span class="od-ev od-ev-{cls}">{escape(label)}</span>' for cls, label in EVIDENCE_LEGEND)
    return f'<div class="od-evlegend">Evidence type: {items}</div>'


def term_card(term: dict, kind: str, source_symbol: str, target_symbol: str) -> str:
    name = escape(term["name"] or term["go_id"])
    src = _badges(term.get("source_evidence"), source_symbol)
    tgt = _badges(term.get("target_evidence"), target_symbol)
    if kind == "shared":
        badges = f'{src}<span class="od-sep">|</span>{tgt}' if src and tgt else (src or tgt)
    elif kind == "source":
        badges = src
    else:
        badges = tgt
    return (f'<div class="od-term"><div class="od-term-name">{name}</div>'
            f'<div class="od-term-meta"><span class="od-id">{escape(term["go_id"])}</span>{badges}</div></div>')


def term_group(title: str, terms: list[dict], kind: str, source_symbol: str, target_symbol: str,
               open_: bool = False) -> str:
    if not terms:
        return f'<div class="od-empty">{escape(title)}: none</div>'
    ordered = sorted(terms, key=lambda t: (t["name"] or "").lower())
    items = "".join(term_card(t, kind, source_symbol, target_symbol) for t in ordered)
    return (f'<details class="od-group od-group-{kind}"{" open" if open_ else ""}>'
            f'<summary><span class="od-dot od-dot-{kind}"></span>{escape(title)}'
            f'<span class="od-count">{len(terms)}</span></summary>'
            f'<div class="od-terms">{items}</div></details>')


def summary_card(label: str, comp: dict, source_symbol: str, target_symbol: str, delay: float = 0.0) -> str:
    s, a, t = comp["shared_count"], comp["source_only_count"], comp["target_only_count"]
    total_source, total_target = s + a, s + t
    head = f'<div class="od-cat-title">{escape(label)}</div>'

    if total_source == 0 and total_target == 0:
        body = '<div class="od-muted">No annotations found for either gene in this database.</div>'
    elif total_source == 0 or total_target == 0:
        missing = source_symbol if total_source == 0 else target_symbol
        body = (f'<div class="od-gap">No annotations found for {escape(missing)} in this database. '
                f'Overlap cannot be assessed &mdash; this is a data gap, not evidence of difference.</div>')
    else:
        union = s + a + t
        j = comp["jaccard"]

        def w(n: int) -> str:
            return f"{n / union * 100:.2f}"

        body = (
            f'<div class="od-big">{j * 100:.0f}%</div>'
            f'<div class="od-cap">of the GO annotations found for either gene are shared '
            f'(annotation overlap, Jaccard {j:.2f})</div>'
            f'<div class="od-bar">'
            f'<span class="od-seg od-seg-shared" style="width:{w(s)}%"></span>'
            f'<span class="od-seg od-seg-source" style="width:{w(a)}%"></span>'
            f'<span class="od-seg od-seg-target" style="width:{w(t)}%"></span></div>'
            f'<div class="od-leg">'
            f'<span><i class="od-dot od-dot-shared"></i>{s} shared</span>'
            f'<span><i class="od-dot od-dot-source"></i>{a} only in {escape(source_symbol)}</span>'
            f'<span><i class="od-dot od-dot-target"></i>{t} only in {escape(target_symbol)}</span></div>'
        )
    return f'<div class="od-card od-cat od-fade" style="animation-delay:{delay:.2f}s">{head}{body}</div>'