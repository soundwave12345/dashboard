"""Audit Management Dashboard — main Streamlit application with routing."""

import streamlit as st

from db_manager import list_audits
from ui_components import render_sidebar

st.set_page_config(page_title="Audit Dashboard", layout="wide")

# ── Restore session from query params (survives refresh) ───────────────────
if "active_audit" not in st.session_state:
    qp = st.query_params.get("audit")
    if qp:
        st.session_state.active_audit = qp
    else:
        st.session_state.active_audit = None
elif st.session_state.active_audit:
    # Keep query params in sync
    st.query_params["audit"] = st.session_state.active_audit

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
