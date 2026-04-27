"""Reusable UI components for the audit dashboard — NiceGUI version."""

import os
import queue
import subprocess
import sys
import threading

from nicegui import app, ui

from db_manager import (
    create_audit_directories,
    get_all_findings,
    get_audit_db_path,
    list_audits,
    register_audit,
)


# ── Sidebar ────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    """Render the dynamic sidebar inside the left drawer."""
    audit_name = app.storage.user.get("active_audit")

    if audit_name:
        ui.label("Audit attivo:").classes("text-caption")
        ui.label(audit_name).classes("text-subtitle1 text-primary")
        ui.button(
            "⬅ Torna alla Selezione",
            on_click=_clear_audit,
        ).props("flat dense").classes("q-mb-md")
        ui.separator()

        with ui.column().classes("q-mt-md gap-2"):
            ui.button("Home", on_click=lambda: ui.navigate.to("/")).props("flat")
            ui.button("Applications", on_click=lambda: ui.navigate.to("/applications")).props("flat")
            ui.button("Servers", on_click=lambda: ui.navigate.to("/servers")).props("flat")
    else:
        ui.label("Audit Manager").classes("text-h6")
        ui.separator()
        ui.label("Audit esistenti").classes("text-subtitle2 q-mt-md")
        audits = list_audits()
        if not audits:
            ui.label("Nessun audit trovato.").classes("text-grey")
        else:
            for a in audits:
                ui.label(f"• {a['nome_audit']}  ({a['data_creazione']})").classes("text-body2")


async def _clear_audit():
    app.storage.user["active_audit"] = None
    ui.navigate.to("/")


# ── Audit Selection / Creation ────────────────────────────────────────────

def render_selection_view() -> None:
    """Tabs for selecting or creating an audit."""
    with ui.tabs().classes("w-full") as tabs:
        ui.tab("Seleziona", label="Seleziona Audit Esistente")
        ui.tab("Crea", label="Crea Nuovo Audit")
    with ui.tab_panels(tabs, value="Seleziona").classes("w-full"):
        with ui.tab_panel("Seleziona"):
            _render_select_tab()
        with ui.tab_panel("Crea"):
            _render_create_tab()


def _render_select_tab() -> None:
    audits = list_audits()
    if not audits:
        ui.label("Nessun audit disponibile. Creane uno nuovo.").classes("text-orange")
        return

    select = ui.select(
        options=[a["nome_audit"] for a in audits],
        value=audits[0]["nome_audit"],
        with_input=True,
        label="Scegli un audit",
    ).classes("w-full q-mb-md")

    async def open_audit():
        app.storage.user["active_audit"] = select.value
        ui.navigate.to("/")

    ui.button("Apri Audit", on_click=open_audit).props("color=primary")


def _render_create_tab() -> None:
    name_input = ui.input(label="Nome Audit").classes("w-full q-mb-md")

    async def start_ingest():
        nome = (name_input.value or "").strip()
        if not nome:
            ui.notify("Il nome dell'audit è obbligatorio.", type="warning")
            return

        # Floating log dialog
        with ui.dialog().props("persistent") as dialog, ui.card().classes("w-[600px]"):
            ui.label(f"Ingest — {nome}").classes("text-h6 q-mb-sm")
            log_area = ui.log().classes("w-full h-[300px]")
            close_btn = ui.button("Chiudi")
            close_btn.set_visibility(False)

        dialog.open()

        # Create directories
        try:
            dir_path, db_path = create_audit_directories(nome)
            log_area.push(f"[OK] Directory creata: {dir_path}")
            log_area.push(f"[OK] Database: {db_path}")
        except FileExistsError as exc:
            log_area.push(f"[ERRORE] {exc}")
            close_btn.set_visibility(True)
            return
        except Exception as exc:
            log_area.push(f"[ERRORE] Creazione directory fallita: {exc}")
            close_btn.set_visibility(True)
            return

        # Run ingest script in a background thread
        ingest_script = os.path.join(os.path.dirname(__file__), "ingest", "ingest.py")
        cmd = [sys.executable, "-u", ingest_script, "--all", "--db", nome, "--project-dir", dir_path]
        log_area.push(f"[INGEST] comando: {' '.join(cmd)}")

        log_queue: queue.Queue = queue.Queue()

        def run_ingest():
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                for line in proc.stdout:
                    log_queue.put(line.rstrip())
                proc.wait()
                log_queue.put(("RETURN_CODE", proc.returncode))
            except Exception as exc:
                log_queue.put(("ERROR", str(exc)))

        thread = threading.Thread(target=run_ingest, daemon=True)
        thread.start()

        # Poll the queue and update log in real-time
        def poll():
            drained = False
            while not log_queue.empty():
                item = log_queue.get_nowait()
                if isinstance(item, tuple):
                    tag, value = item
                    if tag == "RETURN_CODE":
                        timer.active = False
                        if value != 0:
                            log_area.push(f"[ERRORE] Ingest terminato con codice {value}.")
                            close_btn.set_visibility(True)
                        else:
                            _finish_ingest(nome, dir_path, db_path, log_area, close_btn, dialog)
                    elif tag == "ERROR":
                        timer.active = False
                        log_area.push(f"[ERRORE] {value}")
                        close_btn.set_visibility(True)
                    drained = True
                    break
                else:
                    log_area.push(item)
            if not drained:
                # Keep polling
                pass

        timer = ui.timer(0.2, poll)

    ui.button("Avvia Ingest", on_click=start_ingest).props("color=primary")


def _finish_ingest(nome, dir_path, db_path, log_area, close_btn, dialog):
    """Register audit in master DB and show close button."""
    try:
        register_audit(nome, dir_path, db_path)
        log_area.push(f"[OK] Audit registrato nel master DB.")
    except ValueError as exc:
        log_area.push(f"[ERRORE] {exc}")
        close_btn.set_visibility(True)
        return

    log_area.push(f"[OK] Audit '{nome}' creato con successo!")

    app.storage.user["active_audit"] = nome
    close_btn.set_visibility(True)

    async def finish():
        dialog.close()
        ui.navigate.to("/")

    close_btn.on_click(finish)


# ── Data page (Applications / Servers) ────────────────────────────────────

def render_data_page(page_name: str) -> None:
    """Render a data table page (Applications or Servers)."""
    audit_name = app.storage.user.get("active_audit")

    if not audit_name:
        ui.label("Nessun audit selezionato.").classes("text-h5")
        ui.button("Torna alla Home", on_click=lambda: ui.navigate.to("/"))
        return

    db_path = get_audit_db_path(audit_name)
    if not db_path:
        ui.label("Impossibile trovare il database dell'audit.").classes("text-negative")
        ui.button("Torna alla Home", on_click=lambda: ui.navigate.to("/"))
        return

    ui.label(f"{page_name} — {audit_name}").classes("text-h4 q-mb-md")

    data = get_all_findings(db_path)
    if not data:
        ui.label("Nessun dato disponibile nel database.").classes("text-grey")
        return

    # DORA_RELEVANCE filter
    filtered_data = data
    if data and "DORA_RELEVANCE" in data[0]:
        dora_unique = sorted(set(str(r["DORA_RELEVANCE"]) for r in data))

        filter_select = ui.select(
            options=dora_unique,
            multiple=True,
            value=dora_unique,
            label="Filtra per DORA_RELEVANCE",
        ).classes("w-full q-mb-md")

        table_container = ui.column().classes("w-full")

        def update_table():
            selected = filter_select.value or []
            filtered = [r for r in data if str(r["DORA_RELEVANCE"]) in selected] if selected else data
            _render_table(table_container, filtered)

        filter_select.on("update:model-value", update_table)
        update_table()
    else:
        with ui.column().classes("w-full") as table_container:
            _render_table(table_container, data)


def _render_table(container: ui.column, data: list[dict]) -> None:
    """Render a paginated ui.table inside the given container."""
    container.clear()
    if not data:
        with container:
            ui.label("Nessun dato.").classes("text-grey")
        return

    columns = [
        {"name": k, "label": k, "field": k, "sortable": True}
        for k in data[0].keys()
    ]

    with container:
        ui.table(
            columns=columns,
            rows=data,
            pagination=20,
        ).classes("w-full")
