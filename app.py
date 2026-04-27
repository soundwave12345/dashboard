"""Audit Management Dashboard — NiceGUI application."""

from nicegui import app, ui

from ui_components import render_sidebar


# ── Shared layout ──────────────────────────────────────────────────────────

def layout(active_tab: str, content_fn):
    """Shared layout: sidebar + top nav + right drawer + page content."""
    # ── Left sidebar ───────────────────────────────────────────────────
    with ui.left_drawer(bordered=True).classes("q-pa-md"):
        render_sidebar()

    # ── Right drawer for filters (closed by default) ───────────────────
    filter_drawer = ui.right_drawer(bordered=True, fixed=False).classes("q-pa-md")

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
                ui.button("SQL", on_click=lambda: ui.navigate.to("/sql")).props(
                    f"flat {'color=primary' if active_tab == 'SQL' else 'color=grey'}"
                )
        ui.space()
        ui.button(icon="menu", on_click=filter_drawer.toggle).props("flat dense").tooltip("Filtri")

    # ── Page content ───────────────────────────────────────────────────
    with ui.column().classes("w-full q-pa-lg"):
        content_fn(filter_drawer)


# ── Routes ─────────────────────────────────────────────────────────────────

@ui.page("/")
def home_page():
    from pages.home import render_home
    layout("Home", render_home)


@ui.page("/applications")
def applications_page():
    from pages.applications import render_applications
    layout("Applications", render_applications)


@ui.page("/servers")
def servers_page():
    from pages.servers import render_servers
    layout("Servers", render_servers)


@ui.page("/sql")
def sql_page():
    from pages.sql import render_sql
    layout("SQL", render_sql)


# ── Run ────────────────────────────────────────────────────────────────────
ui.run(title="Audit Dashboard", storage_secret="audit-dashboard-secret")
