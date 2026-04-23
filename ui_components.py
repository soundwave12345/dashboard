"""Reusable UI components for the audit dashboard."""

import subprocess
import sys

import streamlit as st

from db_manager import (
    create_audit_directories,
    get_all_findings,
    register_audit,
    seed_placeholder_data,
)


# ── Sidebar ────────────────────────────────────────────────────────────────

def render_sidebar(audits: list[dict]) -> None:
    """Render the dynamic sidebar."""
    with st.sidebar:
        if not st.session_state.get("active_audit"):
            st.title("Audit Manager")
            st.subheader("Audit esistenti")
            if not audits:
                st.info("Nessun audit trovato.")
            else:
                for a in audits:
                    st.markdown(
                        f"- **{a['nome_audit']}**  "
                        f"_{a['data_creazione']}_"
                    )
        else:
            st.markdown(
                f"**Audit attivo:**  "
                f"<span style='color:#00b4d8;font-size:1.1em'>"
                f"{st.session_state.active_audit}</span>",
                unsafe_allow_html=True,
            )
            if st.button("⬅ Torna alla Selezione"):
                st.session_state.active_audit = None
                if "audit" in st.query_params:
                    del st.query_params["audit"]
                st.rerun()

            st.divider()
            if st.button("Applications", use_container_width=True):
                st.switch_page("pages/applications.py")
            if st.button("Servers", use_container_width=True):
                st.switch_page("pages/servers.py")


# ── Audit Selection / Creation ────────────────────────────────────────────

def render_selection_view(audits: list[dict]) -> None:
    """Show tabs for selecting or creating an audit."""
    tab_sel, tab_new = st.tabs(
        ["Seleziona Audit Esistente", "Crea Nuovo Audit"]
    )

    # ── Select existing ────────────────────────────────────────────────
    with tab_sel:
        if not audits:
            st.warning("Nessun audit disponibile. Creane uno nuovo.")
        else:
            chosen = st.selectbox(
                "Scegli un audit:",
                options=[a["nome_audit"] for a in audits],
                key="select_audit",
            )
            if st.button("Apri Audit", key="btn_open"):
                st.session_state.active_audit = chosen
                st.query_params["audit"] = chosen
                st.rerun()

    # ── Create new ─────────────────────────────────────────────────────
    with tab_new:
        nome = st.text_input("Nome Audit", key="new_audit_name")

        if st.button("Avvia Ingest", key="btn_ingest"):
            if not nome.strip():
                st.error("Il nome dell'audit è obbligatorio.")
                return

            from datetime import date
            _run_ingest(nome.strip(), date.today().strftime("%Y-%m-%d"))


def _run_ingest(nome: str, data: str) -> None:
    """Execute ingest.py, stream its output, then register the audit."""
    log_area = st.empty()
    lines: list[str] = []

    try:
        dir_path, db_path = create_audit_directories(nome)
    except FileExistsError as exc:
        st.error(str(exc))
        return

    ingest_script = "ingest/ingest.py"
    if not ingest_available(ingest_script):
        lines.append(
            f"[PLACEHOLDER] ingest.py non trovato – "
            f"simulazione completata per '{nome}'."
        )
        log_area.code("\n".join(lines))
    else:
        # Real subprocess execution
        try:
            proc = subprocess.Popen(
                [sys.executable, ingest_script, "--all", "--db", nome, "--project-dir", dir_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                lines.append(line.rstrip())
                log_area.code("\n".join(lines))
            proc.wait()
            if proc.returncode != 0:
                st.error(f"Ingest terminato con codice {proc.returncode}.")
                return
        except Exception as exc:
            st.error(f"Errore esecuzione ingest: {exc}")
            return

    # Register in master DB and seed placeholder data
    try:
        register_audit(nome, dir_path, db_path)
    except ValueError as exc:
        st.error(str(exc))
        return

    seed_placeholder_data(db_path)

    st.success(f"Audit '{nome}' creato con successo!")
    st.session_state.active_audit = nome
    st.query_params["audit"] = nome
    st.rerun()


def ingest_available(path: str) -> bool:
    """Check whether the ingest script exists on disk."""
    import os
    return os.path.isfile(path)


# ── Audit Dashboard ────────────────────────────────────────────────────────

def render_audit_dashboard(db_path: str, nome: str) -> None:
    """Show a data table with all findings from the audit database."""
    st.header(f"Dashboard — {nome}")

    data = get_all_findings(db_path)

    if not data:
        st.info("Nessun dato disponibile nel database.")
        return

    # DORA_RELEVANCE filter
    if "DORA_RELEVANCE" in data[0]:
        dora_unique = sorted(set(str(r["DORA_RELEVANCE"]) for r in data))
        selected = st.multiselect(
            "Filtra per DORA_RELEVANCE",
            options=dora_unique,
            default=dora_unique,
            key="dora_filter",
        )
        data = [r for r in data if str(r["DORA_RELEVANCE"]) in selected]

    st.dataframe(data, use_container_width=True, hide_index=True)
