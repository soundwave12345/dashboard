"""Reusable UI components for the audit dashboard."""

import subprocess
import sys

import plotly.express as px
import streamlit as st

from db_manager import (
    create_audit_directories,
    get_findings_by_category,
    get_findings_by_severity,
    register_audit,
    seed_placeholder_data,
)


# ── Sidebar ────────────────────────────────────────────────────────────────

def render_sidebar(audits: list[dict]) -> None:
    """Render the dynamic sidebar."""
    with st.sidebar:
        st.title("Audit Manager")

        if st.session_state.get("active_audit"):
            st.markdown(
                f"**Audit attivo:**  \n"
                f"<span style='color:#00b4d8;font-size:1.1em'>"
                f"{st.session_state.active_audit}</span>",
                unsafe_allow_html=True,
            )
            if st.button("⬅ Torna alla Selezione"):
                st.session_state.active_audit = None
                st.rerun()
        else:
            st.subheader("Audit esistenti")
            if not audits:
                st.info("Nessun audit trovato.")
            else:
                for a in audits:
                    st.markdown(
                        f"- **{a['nome_audit']}**  "
                        f"_{a['data_creazione']}_"
                    )


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
    st.rerun()


def ingest_available(path: str) -> bool:
    """Check whether the ingest script exists on disk."""
    import os
    return os.path.isfile(path)


# ── Audit Dashboard ────────────────────────────────────────────────────────

SEVERITY_COLORS = {"High": "#e63946", "Medium": "#f4a261", "Low": "#2a9d8f"}
CATEGORY_COLORS = {
    "Access Control": "#264653",
    "Cryptography": "#2a9d8f",
    "Data Protection": "#e9c46a",
    "Network": "#f4a261",
    "Compliance": "#e76f51",
}


def render_audit_dashboard(db_path: str, nome: str) -> None:
    """Show two pie charts (by category and severity) using audit data."""
    st.header(f"Dashboard — {nome}")

    cat_data = get_findings_by_category(db_path)
    sev_data = get_findings_by_severity(db_path)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Findings per Categoria")
        if cat_data:
            fig_cat = px.pie(
                cat_data,
                names="category",
                values="count",
                color="category",
                color_discrete_map=CATEGORY_COLORS,
                hole=0.35,
            )
            fig_cat.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_cat, use_container_width=True)
        else:
            st.info("Nessun dato disponibile.")

    with col2:
        st.subheader("Findings per Severità")
        if sev_data:
            fig_sev = px.pie(
                sev_data,
                names="severity",
                values="count",
                color="severity",
                color_discrete_map=SEVERITY_COLORS,
                hole=0.35,
            )
            fig_sev.update_layout(margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_sev, use_container_width=True)
        else:
            st.info("Nessun dato disponibile.")
