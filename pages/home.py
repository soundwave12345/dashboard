"""Home page — audit selection, creation, and active audit details."""

import streamlit as st

from ui_components import render_selection_view
from db_manager import list_audits, get_audit_db_path

audits = list_audits()

if st.session_state.active_audit:
    # Find current audit details
    audit_info = next(
        (a for a in audits if a["nome_audit"] == st.session_state.active_audit),
        None,
    )

    st.title(f"Audit: {st.session_state.active_audit}")

    if audit_info:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Data creazione:** {audit_info['data_creazione']}")
            st.markdown(f"**Directory:** `{audit_info['directory_path']}`")
            st.markdown(f"**Database:** `{audit_info['db_path']}`")
        with col2:
            db_path = get_audit_db_path(st.session_state.active_audit)
            if db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
                conn.close()
                st.markdown(f"**Record findings:** {count}")

    st.divider()
    st.subheader("Navigazione")
    col_app, col_srv = st.columns(2)
    with col_app:
        if st.button("🖥️ Vai ad Applications", use_container_width=True):
            st.switch_page("pages/applications.py")
    with col_srv:
        if st.button("🖧 Vai a Servers", use_container_width=True):
            st.switch_page("pages/servers.py")
else:
    st.title("Audit Management Dashboard")
    st.markdown("Seleziona un audit esistente oppure creane uno nuovo.")
    render_selection_view(audits)
