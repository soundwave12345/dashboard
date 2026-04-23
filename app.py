"""Audit Management Dashboard — main Streamlit application with routing."""

import streamlit as st

from db_manager import list_audits
from ui_components import render_sidebar

st.set_page_config(page_title="Audit Dashboard", layout="wide")

# ── Initialise session state ───────────────────────────────────────────────
if "active_audit" not in st.session_state:
    st.session_state.active_audit = None

# ── Load data ──────────────────────────────────────────────────────────────
audits = list_audits()

# ── Sidebar ────────────────────────────────────────────────────────────────
render_sidebar(audits)

# ── Routing ────────────────────────────────────────────────────────────────
if not st.session_state.active_audit:
    page = st.navigation(
        {
            "Home": [st.Page("pages/home.py", title="Home")],
        }
    )
else:
    page = st.navigation(
        {
            "Home": [st.Page("pages/home.py", title="Home")],
            "Dati": [
                st.Page("pages/applications.py", title="Applications"),
                st.Page("pages/servers.py", title="Servers"),
            ],
        }
    )
page.run()
