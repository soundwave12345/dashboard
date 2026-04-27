"""Applications page — async data table with DORA/GDPR relevance filters."""

import asyncio

from nicegui import app, ui

from db_manager import get_audit_db_path, get_all_findings
from ui_components import render_data_table, render_filters_drawer, render_skeleton


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

    # Show skeleton immediately
    table_container = ui.column().classes("w-full")
    render_skeleton(table_container)

    # Load data asynchronously
    async def load_data():
        data = await asyncio.to_thread(get_all_findings, db_path)

        if not data:
            table_container.clear()
            with table_container:
                ui.label("Nessun dato disponibile nel database.").classes("text-grey")
            return

        table_container.clear()
        table = render_data_table(table_container, data)

        if filter_drawer and table:
            render_filters_drawer(filter_drawer, data, table)

    ui.timer(0, load_data, once=True)
