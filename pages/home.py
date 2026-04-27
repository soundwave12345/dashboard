"""Home page — audit selection, creation, and active audit details."""

import sqlite3

from nicegui import app, ui

from db_manager import get_audit_db_path, list_audits
from ui_components import render_selection_view


def render_home(filter_drawer=None):
    if filter_drawer:
        filter_drawer.visible = False
        filter_drawer.classes(remove="w-[300px]")
    audit_name = app.storage.user.get("active_audit")

    if audit_name:
        render_audit_detail(audit_name)
    else:
        render_welcome()


def render_audit_detail(audit_name: str):
    audits = list_audits()
    audit_info = next((a for a in audits if a["nome_audit"] == audit_name), None)

    ui.label(f"Audit: {audit_name}").classes("text-h4")

    if audit_info:
        with ui.row().classes("gap-8 q-mt-md"):
            with ui.card().classes("min-w-[300px]"):
                ui.label("Dettagli Audit").classes("text-h6")
                ui.label(f"Data creazione: {audit_info['data_creazione']}")
                ui.label(f"Directory: {audit_info['directory_path']}")
                ui.label(f"Database: {audit_info['db_path']}")
            with ui.card().classes("min-w-[300px]"):
                db_path = get_audit_db_path(audit_name)
                if db_path:
                    conn = sqlite3.connect(db_path)
                    count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
                    conn.close()
                    ui.label(f"Record findings: {count}")

    ui.separator().classes("q-my-md")
    ui.label("Navigazione").classes("text-h6")
    with ui.row().classes("gap-4"):
        ui.button("Applications", on_click=lambda: ui.navigate.to("/applications")).props("color=primary")
        ui.button("Servers", on_click=lambda: ui.navigate.to("/servers")).props("color=primary")
        ui.button("SQL", on_click=lambda: ui.navigate.to("/sql")).props("color=primary")


def render_welcome():
    ui.label("Audit Management Dashboard").classes("text-h4")
    ui.label("Seleziona un audit esistente oppure creane uno nuovo.")
    render_selection_view()
