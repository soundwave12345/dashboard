"""Applications page — data table with DORA_RELEVANCE filter."""

from nicegui import app, ui

from db_manager import get_audit_db_path, get_all_findings
from ui_components import render_data_table


def render_applications():
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

    # DORA_RELEVANCE filter
    if "DORA_RELEVANCE" in data[0]:
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
            render_data_table(table_container, filtered)

        filter_select.on("update:model-value", update_table)
        update_table()
    else:
        with ui.column().classes("w-full") as table_container:
            render_data_table(table_container, data)
