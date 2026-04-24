"""Audit Management Dashboard — NiceGUI application."""

from nicegui import app, ui

from db_manager import list_audits
from ui_components import render_sidebar


# ── Shared layout ──────────────────────────────────────────────────────────

@ui.page("/")
def home_page():
    layout("Home", render_home)


@ui.page("/applications")
def applications_page():
    layout("Applications", render_applications)


@ui.page("/servers")
def servers_page():
    layout("Servers", render_servers)


def layout(active_tab: str, content_fn):
    """Shared layout: sidebar + top nav + page content."""
    # ── Sidebar ────────────────────────────────────────────────────────
    with ui.left_drawer(bordered=True).classes("q-pa-md"):
        render_sidebar()

    # ── Top navigation tabs ────────────────────────────────────────────
    with ui.header().classes("items-center justify-start gap-4 q-px-md"):
        ui.label("Audit Dashboard").classes("text-h6 q-mr-lg")
        with ui.row().classes("gap-1"):
            ui.button("Home", on_click=lambda: ui.navigate.to("/")).props(
                f"flat {'color=primary' if active_tab == 'Home' else 'color=grey'}"
            )
            audit_name = app.storage.user.get("active_audit")
            if audit_name:
                ui.button("Applications", on_click=lambda: ui.navigate.to("/applications")).props(
                    f"flat {'color=primary' if active_tab == 'Applications' else 'color=grey'}"
                )
                ui.button("Servers", on_click=lambda: ui.navigate.to("/servers")).props(
                    f"flat {'color=primary' if active_tab == 'Servers' else 'color=grey'}"
                )

    # ── Page content ───────────────────────────────────────────────────
    with ui.column().classes("w-full q-pa-lg"):
        content_fn()


# ── Page renderers ─────────────────────────────────────────────────────────

def render_home():
    audit_name = app.storage.user.get("active_audit")

    if audit_name:
        render_audit_detail(audit_name)
    else:
        render_welcome()


def render_audit_detail(audit_name: str):
    from db_manager import get_audit_db_path
    import sqlite3

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


def render_welcome():
    from ui_components import render_selection_view
    ui.label("Audit Management Dashboard").classes("text-h4")
    ui.label("Seleziona un audit esistente oppure creane uno nuovo.")
    render_selection_view()


def render_applications():
    from ui_components import render_data_page
    render_data_page("Applications")


def render_servers():
    from ui_components import render_data_page
    render_data_page("Servers")


# ── Run ────────────────────────────────────────────────────────────────────
ui.run(title="Audit Dashboard", storage_secret="audit-dashboard-secret")
