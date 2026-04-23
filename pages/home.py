"""Home page — audit selection and creation."""

import streamlit as st

from ui_components import render_selection_view
from db_manager import list_audits

audits = list_audits()

if st.session_state.active_audit:
    st.title(f"Audit attivo: {st.session_state.active_audit}")
    st.info("Usa il menu in alto per navigare tra Applications e Servers.")
else:
    st.title("Audit Management Dashboard")
    st.markdown("Seleziona un audit esistente oppure creane uno nuovo.")
    render_selection_view(audits)
