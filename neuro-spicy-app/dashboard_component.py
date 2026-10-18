import json
import os
import streamlit as st
from streamlit_elements import elements, mui, dashboard, sync
import calendar_component

LAYOUT_FILE = "dashboard_layout.json"

DEFAULT_LAYOUT = [
    {"i": "calendar_widget", "x": 0, "y": 0, "w": 8, "h": 10},
    {"i": "medication_widget", "x": 8, "y": 0, "w": 4, "h": 5},
    {"i": "meal_widget", "x": 8, "y": 5, "w": 4, "h": 5},
]

EXPECTED_WIDGET_KEYS = {"calendar_widget", "medication_widget", "meal_widget"}

def init_dashboard_layout():
    """Ensures st.session_state retains the active layout across tab navigations."""
    if "dashboard_layout" not in st.session_state:
        if os.path.exists(LAYOUT_FILE):
            try:
                with open(LAYOUT_FILE, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        st.session_state["dashboard_layout"] = data
                        return
            except Exception:
                pass
        st.session_state["dashboard_layout"] = DEFAULT_LAYOUT


def load_dashboard_layout():
    """Retrieves current layout from active session state."""
    init_dashboard_layout()
    return st.session_state["dashboard_layout"]


def save_dashboard_layout(raw_layout):
    """Automatically persists updated widget positions when dragged or resized."""
    if not raw_layout or not isinstance(raw_layout, list):
        return

    incoming_keys = {str(item.get("i")) for item in raw_layout if item.get("i")}

    # GUARD: Ignore unmount signals or incomplete payloads during tab switches
    if not EXPECTED_WIDGET_KEYS.issubset(incoming_keys):
        return

    clean_layout = []
    for item in raw_layout:
        clean_layout.append({
            "i": str(item.get("i")),
            "x": int(item.get("x", 0)),
            "y": int(item.get("y", 0)),
            "w": int(item.get("w", 4)),
            "h": int(item.get("h", 4)),
        })

    # Avoid redundant saves if positions haven't changed
    current = st.session_state.get("dashboard_layout", [])
    if clean_layout != current:
        st.session_state["dashboard_layout"] = clean_layout
        try:
            with open(LAYOUT_FILE, "w") as f:
                json.dump(clean_layout, f, indent=2)
        except Exception as e:
            st.error(f"Error auto-saving layout: {e}")


def render_dashboard():
    init_dashboard_layout()
    # 1. Capture and save drag/resize events automatically
    if "dashboard_layout_changed" in st.session_state:
        changed_data = st.session_state.get("dashboard_layout_changed")
        if changed_data:
            save_dashboard_layout(changed_data)

    current_layout = load_dashboard_layout()

    # 2. Dynamic key forces React to render saved positions on tab return
    layout_signature = json.dumps(current_layout, sort_keys=True)
    frame_key = f"dashboard_frame_{abs(hash(layout_signature))}"

    # 3. Render grid dashboard
    with elements(frame_key):
        with dashboard.Grid(
            layout=current_layout,
            onLayoutChange=sync("dashboard_layout_changed"),
            cols={"lg": 12, "md": 10, "sm": 6, "xs": 4, "xxs": 2},
            rowHeight=60,
            draggableHandle=".drag-handle",
        ):
            # Widget 1: Schedule / Calendar
            with mui.Paper(
                key="calendar_widget",
                elevation=2,
                sx={"padding": 2, "height": "100%", "overflow": "auto"},
            ):
                mui.Typography(
                    "📅 Schedule",
                    className="drag-handle",
                    variant="h6",
                    sx={"cursor": "grab", "marginBottom": 1},
                )
                calendar_component.render_calendar()

            # Widget 2: Medication Log
            with mui.Paper(
                key="medication_widget",
                elevation=2,
                sx={"padding": 2, "height": "100%", "overflow": "auto"},
            ):
                mui.Typography(
                    "💊 Medications",
                    className="drag-handle",
                    variant="h6",
                    sx={"cursor": "grab", "marginBottom": 1},
                )
                st.write("Medication logging interface.")

            # Widget 3: Meal Tracker
            with mui.Paper(
                key="meal_widget",
                elevation=2,
                sx={"padding": 2, "height": "100%", "overflow": "auto"},
            ):
                mui.Typography(
                    "🍽️ Meals",
                    className="drag-handle",
                    variant="h6",
                    sx={"cursor": "grab", "marginBottom": 1},
                )
                st.write("Meal tracking interface.")
