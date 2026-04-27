"""SQL page — run custom SQL queries on the audit database."""

import sqlite3

from nicegui import app, ui

from db_manager import get_audit_db_path
from ui_components import render_data_table


def _get_db_schema(db_path: str) -> dict[str, list[str]]:
    """Return {table_name: [col1, col2, ...]} from the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [row[0] for row in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    schema = {}
    for table in tables:
        cols = [row[1] for row in cur.execute(f"PRAGMA table_info('{table}')").fetchall()]
        schema[table] = cols
    conn.close()
    return schema


def render_sql(filter_drawer=None):
    if filter_drawer:
        filter_drawer.style("display: none")
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

    # Header with title and run button on the right
    with ui.row().classes("w-full items-center justify-between"):
        ui.label(f"SQL — {audit_name}").classes("text-h4")
        ui.button("Esegui Query", on_click=lambda: run_query()).props("color=primary")

    # Main content: editor+results on left, schema tree on right
    with ui.row().classes("w-full gap-4"):

        # Left: Code editor + results
        with ui.column().classes("flex-1 overflow-auto"):
            editor = ui.codemirror(
                value="SELECT * FROM findings LIMIT 100",
                language="sql",
            ).classes("w-full max-w-full").style("max-height: 200px; overflow: auto")

            error_label = ui.label("").classes("text-negative")
            result_container = ui.column().classes("w-full overflow-auto")

        # Right: DB schema tree
        with ui.card().classes("min-w-[250px] max-w-[250px] overflow-auto"):
            ui.label("Schema").classes("text-subtitle1 q-mb-sm")
            schema = _get_db_schema(db_path)
            tree_nodes = []
            for table, cols in schema.items():
                tree_nodes.append({
                    "id": table,
                    "label": table,
                    "children": [{"id": f"{table}.{c}", "label": c} for c in cols],
                })
            ui.tree(tree_nodes).expand()

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
