"""Audit Management Dashboard — main Streamlit application."""

import streamlit as st

from db_manager import get_audit_db_path, list_audits
from ui_components import (
    render_audit_dashboard,
    render_selection_view,
    render_sidebar,
)

st.set_page_config(page_title="Audit Dashboard", layout="wide")

# ── Initialise session state ───────────────────────────────────────────────
if "active_audit" not in st.session_state:
    st.session_state.active_audit = None

# ── Load data ──────────────────────────────────────────────────────────────
audits = list_audits()

# ── Sidebar ────────────────────────────────────────────────────────────────
render_sidebar(audits)

# ── Main content ───────────────────────────────────────────────────────────
if st.session_state.active_audit:
    db_path = get_audit_db_path(st.session_state.active_audit)
    if db_path:
        render_audit_dashboard(db_path, st.session_state.active_audit)
    else:
        st.error("Impossibile trovare il database dell'audit selezionato.")
        if st.button("⬅ Torna alla Selezione"):
            st.session_state.active_audit = None
            st.rerun()
else:
    st.title("Audit Management Dashboard")
    st.markdown("Seleziona un audit esistente oppure creane uno nuovo.")
    render_selection_view(audits)
