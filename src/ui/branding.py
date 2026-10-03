"""Sophiark branding: header (logo + name) and footer (credit + links to other Sophiark tools).

Builders return ONE line of HTML (no blank lines) so Markdown keeps the block intact.
The logo is read from assets/logo-transparan.png at runtime; if it is missing the page
still works, just without the image.
"""
import base64
import io
from functools import lru_cache
from html import escape

import streamlit as st

from src.config import ROOT

LOGO_PATH = ROOT / "assets" / "logo-transparan.png"
APP_NAME = "Sophiark Orthology"
AUTHOR = "Metin Kaan TEMİZER"
AUTHOR_ROLE = "Founder / Developer"
SITE_URL = "https://sophiark.com.tr/"
NETWORK_URL = "https://sophiark.com.tr/network-analysis/"
WORKPLACE_URL = "https://sophiark.com.tr/workplace/"
WORKPLACE_DOWNLOAD_URL = "https://sophiark.com.tr/workplace/#download"
DESCRIPTION = ("Compare a gene with its ortholog(s) in another species using Ensembl "
               "Compara orthology and Gene Ontology annotations.")


@lru_cache(maxsize=4)
def _logo_uri(path_str: str, mtime: float, max_height: int) -> str | None:
    """Downscaled logo as a data URI (small, so it is cheap to resend on every Streamlit rerun)."""
    try:
        raw = open(path_str, "rb").read()
    except OSError:
        return None
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(raw)).convert("RGBA")
        if img.height > max_height:
            img = img.resize((max(1, round(img.width * max_height / img.height)), max_height), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
    except Exception:
        pass  # fall back to the original bytes
    return "data:image/png;base64," + base64.b64encode(raw).decode()


def logo_data_uri(max_height: int = 160) -> str | None:
    mtime = LOGO_PATH.stat().st_mtime if LOGO_PATH.exists() else 0.0
    return _logo_uri(str(LOGO_PATH), mtime, max_height)


def page_icon():
    """PIL image for the browser tab, or None when the logo file is missing."""
    if not LOGO_PATH.exists():
        return None
    try:
        from PIL import Image

        return Image.open(LOGO_PATH).convert("RGBA")
    except Exception:
        return None


def header_html() -> str:
    uri = logo_data_uri()
    logo = f'<img class="od-logo" src="{uri}" alt="Sophiark logo">' if uri else ""
    return (f'<div class="od-header od-fade">{logo}<div>'
            f'<div class="od-app-title">Sophiark <span>Orthology</span></div>'
            f'<div class="od-app-sub">{escape(DESCRIPTION)}</div></div></div>')


def footer_html() -> str:
    uri = logo_data_uri(max_height=96)
    logo = f'<img class="od-foot-logo" src="{uri}" alt="Sophiark logo">' if uri else ""
    link = 'target="_blank" rel="noopener noreferrer"'
    return (
        f'<div class="od-footer od-fade">'
        f'<div class="od-foot-main">{logo}<div>'
        f'<div class="od-foot-name">{escape(APP_NAME)}</div>'
        f'<div class="od-foot-tag">Independent research software for computational biology and experimental work.</div>'
        f'</div></div>'
        f'<div class="od-foot-by">Developed by <b>{escape(AUTHOR)}</b> &middot; {escape(AUTHOR_ROLE)}</div>'
        f'<div class="od-foot-try">Try the other Sophiark tools</div>'
        f'<div class="od-prods">'
        f'<a class="od-prod" href="{NETWORK_URL}" {link}><b>Sophiark Network Analysis</b>'
        f'<span>Explore how biological perturbations propagate through connected networks.</span>'
        f'<em>Explore / request a private preview &rarr;</em></a>'
        f'<a class="od-prod" href="{WORKPLACE_DOWNLOAD_URL}" {link}><b>Sophiark Workplace</b>'
        f'<span>A free, open-source, local-first workspace for experiments, protocols and samples.</span>'
        f'<em>Download for Windows &rarr;</em></a></div>'
        f'<div class="od-foot-links"><a class="od-btn" href="{SITE_URL}" {link}>sophiark.com.tr &#8599;</a></div>'
        f'<div class="od-foot-copy">&copy; 2026 Sophiark &middot; Research software &middot; Independent initiative</div>'
        f'</div>'
    )


def render_header() -> None:
    st.markdown(header_html(), unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown(footer_html(), unsafe_allow_html=True)