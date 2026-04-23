"""Servers page — data table from findings with DORA_RELEVANCE filter."""

import streamlit as st

from db_manager import get_audit_db_path, get_all_findings

nome = st.session_state.active_audit
db_path = get_audit_db_path(nome)

if not db_path:
    st.error("Impossibile trovare il database dell'audit selezionato.")
    if st.button("⬅ Torna alla Selezione"):
        st.session_state.active_audit = None
        st.switch_page("pages/home.py")
else:
    st.header(f"Servers — {nome}")

    data = get_all_findings(db_path)

    if not data:
        st.info("Nessun dato disponibile nel database.")
    else:
        # DORA_RELEVANCE filter
        if "DORA_RELEVANCE" in data[0]:
            dora_unique = sorted(set(str(r["DORA_RELEVANCE"]) for r in data))
            selected = st.multiselect(
                "Filtra per DORA_RELEVANCE",
                options=dora_unique,
                default=dora_unique,
                key="dora_filter_servers",
            )
            data = [r for r in data if str(r["DORA_RELEVANCE"]) in selected]

        st.dataframe(data, use_container_width=True, hide_index=True)
