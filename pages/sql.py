"""SQL page — run custom SQL queries on the audit database."""

import sqlite3

from nicegui import app, ui

from db_manager import get_audit_db_path
from ui_components import render_data_table


def render_sql():
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

    ui.label(f"SQL — {audit_name}").classes("text-h4 q-mb-md")

    editor = ui.codemirror(
        value="SELECT * FROM findings LIMIT 100",
        language="sql",
    ).classes("w-full").props('style="height: 150px"')

    result_container = ui.column().classes("w-full q-mt-md")
    error_label = ui.label("").classes("text-negative")

    async def run_query():
        query = (editor.value or "").strip()
        if not query:
            return

        error_label.set_text("")

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query)
            rows = cur.fetchall()
            conn.close()

            if not rows:
                result_container.clear()
                with result_container:
                    ui.label("Query eseguita. Nessun risultato.").classes("text-grey")
                return

            data = [dict(r) for r in rows]
            render_data_table(result_container, data)

        except sqlite3.Error as exc:
            error_label.set_text(f"SQL Error: {exc}")
        except Exception as exc:
            error_label.set_text(f"Errore: {exc}")

    ui.button("Esegui Query", on_click=run_query).props("color=primary").classes("q-mt-sm")
