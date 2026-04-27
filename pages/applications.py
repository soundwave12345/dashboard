"""Applications page — data table with DORA/GDPR relevance filters."""

from nicegui import app, ui

from db_manager import get_audit_db_path, get_all_findings
from ui_components import render_data_table, render_filters_drawer


def render_applications(filter_drawer=None):
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

    ui.label(f"Applications — {audit_name}").classes("text-h4 q-mb-md")

    data = get_all_findings(db_path)
    if not data:
        ui.label("Nessun dato disponibile nel database.").classes("text-grey")
        return

    table_container = ui.column().classes("w-full")
    table = render_data_table(table_container, data)

    if filter_drawer:
        render_filters_drawer(filter_drawer, data, table)
