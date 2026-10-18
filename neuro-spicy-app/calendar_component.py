import json
import os
import uuid
from datetime import datetime, timedelta, time
import streamlit as st
from streamlit_calendar import calendar

EVENTS_FILE = "calendar_events.json"
MEDS_LOG_FILE = "medication_log.json"
MEAL_LOG_FILE = "meal_log.json"
ACTIVITY_LOG_FILE = "activity_log.json"


def load_events():
    """Loads saved calendar events from disk and validates/normalizes date strings."""
    if not os.path.exists(EVENTS_FILE):
        return []
    try:
        with open(EVENTS_FILE, "r") as f:
            raw_events = json.load(f)
            if not isinstance(raw_events, list):
                return []
    except (json.JSONDecodeError, ValueError):
        return []

    validated_events = []
    for event in raw_events:
        start_str = str(event.get("start", ""))

        # Guard against malformed start times missing the YYYY-MM-DD date prefix
        if "T" not in start_str and len(start_str) < 10:
            stored_date = event.get("date") or event.get("date_str")
            if stored_date:
                event["start"] = f"{stored_date}T{start_str}"
            else:
                continue  # Drop events missing valid date context to prevent leaking onto today's view

        validated_events.append(event)

    return validated_events


def save_events(events):
    """Saves calendar events to disk."""
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)


def _extract_item_date_and_time(item, default_time_str="12:00 PM"):
    """
    Extracts explicit date (YYYY-MM-DD) and 24h formatted time (HH:MM:SS)
    from a logged item dictionary. Returns None for event_date if no valid date is recorded.
    """
    # 1. Parse Date String strictly from recorded log attributes
    raw_date = item.get("date_str") or item.get("date")
    if not raw_date and item.get("timestamp"):
        try:
            raw_date = item.get("timestamp").split("T")[0]
        except Exception:
            raw_date = None

    event_date = raw_date  # Do NOT fallback to datetime.now() for historical items

    # 2. Parse Time String
    raw_time = (
            item.get("logged_at_time")
            or item.get("time")
            or item.get("time_str")
            or default_time_str
    )

    clean_time_str = str(raw_time).strip()
    parsed_dt = None

    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M:%S", "%H:%M"):
        try:
            parsed_dt = datetime.strptime(clean_time_str, fmt)
            break
        except (ValueError, AttributeError):
            continue

    if parsed_dt:
        parsed_time = parsed_dt.strftime("%H:%M:%S")
    else:
        parsed_time = "12:00:00"

    return event_date, parsed_time


def _create_iso_range(e_date, e_time, duration_minutes=30):
    """Helper to generate ISO start and end timestamps with explicit duration."""
    start_dt = datetime.strptime(f"{e_date} {e_time}", "%Y-%m-%d %H:%M:%S")
    end_dt = start_dt + timedelta(minutes=duration_minutes)
    return start_dt.strftime("%Y-%m-%dT%H:%M:%S"), end_dt.strftime(
        "%Y-%m-%dT%H:%M:%S")


def sync_daily_logs_to_calendar():
    """
    Reads logged Medications, Meals, and Activities and places them ONLY on
    the exact calendar date/time they were actually logged for today.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    events = load_events()
    existing_ids = {e.get("id") for e in events if e.get("id")}
    updated = False

    # 1. Sync Medication Events
    if os.path.exists(MEDS_LOG_FILE):
        try:
            with open(MEDS_LOG_FILE, "r") as f:
                meds = json.load(f)
                if isinstance(meds, list):
                    for m in meds:
                        if m.get("taken", True):
                            e_date, e_time = _extract_item_date_and_time(m,
                                                                         "08:00 AM")

                            # Strict date check: skip if item is not from today or has no explicit date
                            if e_date != today_str:
                                continue

                            med_name = m.get("name", "Medication")
                            dosage = f" ({m.get('dosage')})" if m.get(
                                "dosage") else ""

                            stamp = m.get(
                                "timestamp") or f"{e_date}_{m.get('time', '08:00')}"
                            event_id = f"med_{stamp}_{med_name}".replace(" ",
                                                                         "_")

                            if event_id not in existing_ids:
                                start_iso, end_iso = _create_iso_range(e_date,
                                                                       e_time,
                                                                       duration_minutes=15)
                                events.append({
                                    "id": event_id,
                                    "title": f"💊 {med_name}{dosage}",
                                    "start": start_iso,
                                    "end": end_iso,
                                    "date": e_date,
                                    "allDay": False,
                                    "backgroundColor": "#3B82F6",
                                    "borderColor": "#1D4ED8"
                                })
                                existing_ids.add(event_id)
                                updated = True
        except Exception:
            pass

    # 2. Sync Meal Events
    if os.path.exists(MEAL_LOG_FILE):
        try:
            with open(MEAL_LOG_FILE, "r") as f:
                meals = json.load(f)
                if isinstance(meals, list):
                    for meal in meals:
                        e_date, e_time = _extract_item_date_and_time(meal,
                                                                     "12:00 PM")

                        # Strict date check: skip if item is not from today or has no explicit date
                        if e_date != today_str:
                            continue

                        m_type = meal.get("type", "Meal")
                        m_name = meal.get("name", "Food")

                        stamp = meal.get(
                            "timestamp") or f"{e_date}_{meal.get('time', '12:00')}"
                        event_id = f"meal_{stamp}_{m_name}".replace(" ", "_")

                        if event_id not in existing_ids:
                            start_iso, end_iso = _create_iso_range(e_date,
                                                                   e_time,
                                                                   duration_minutes=30)
                            events.append({
                                "id": event_id,
                                "title": f"🍽️ {m_type}: {m_name}",
                                "start": start_iso,
                                "end": end_iso,
                                "date": e_date,
                                "allDay": False,
                                "backgroundColor": "#10B981",
                                "borderColor": "#047857"
                            })
                            existing_ids.add(event_id)
                            updated = True
        except Exception:
            pass

    # 3. Sync Activity Events
    if os.path.exists(ACTIVITY_LOG_FILE):
        try:
            with open(ACTIVITY_LOG_FILE, "r") as f:
                acts = json.load(f)
                if isinstance(acts, list):
                    for act in acts:
                        e_date, e_time = _extract_item_date_and_time(act,
                                                                     "05:00 PM")

                        # Strict date check: skip if item is not from today or has no explicit date
                        if e_date != today_str:
                            continue

                        act_name = act.get("name", "Activity")
                        duration = int(act.get("duration", 30)) if act.get(
                            "duration") else 30
                        dur_str = f" ({duration}m)"

                        stamp = act.get(
                            "timestamp") or f"{e_date}_{act.get('time', '17:00')}"
                        event_id = f"act_{stamp}_{act_name}".replace(" ", "_")

                        if event_id not in existing_ids:
                            start_iso, end_iso = _create_iso_range(e_date,
                                                                   e_time,
                                                                   duration_minutes=duration)
                            events.append({
                                "id": event_id,
                                "title": f"🧘 {act_name}{dur_str}",
                                "start": start_iso,
                                "end": end_iso,
                                "date": e_date,
                                "allDay": False,
                                "backgroundColor": "#8B5CF6",
                                "borderColor": "#6D28D9"
                            })
                            existing_ids.add(event_id)
                            updated = True
        except Exception:
            pass

    if updated:
        save_events(events)


def sync_end_of_day_summary_to_calendar():
    """Alias to satisfy app.py imports."""
    return sync_daily_logs_to_calendar()


def clear_stale_synced_events():
    """Utility function to clear out older mis-indexed sync events from disk."""
    events = load_events()
    manual_events = [
        e for e in events if not any(
            e.get("id", "").startswith(prefix) for prefix in
            ("med_", "meal_", "act_")
        )
    ]
    save_events(manual_events)


@st.dialog("➕ Add Schedule Event")
def add_event_dialog(start_str, end_str):
    st.write(f"**Selected Date Range:** `{start_str}`")

    date_part = start_str.split("T")[0] if "T" in start_str else start_str

    with st.form("add_event_form"):
        title = st.text_input(
            "Event Name",
            placeholder="e.g., Take Morning Vitamin, Doctor Visit"
        )

        all_day = st.checkbox("All Day Event", value=False)

        col_start, col_end = st.columns(2)
        with col_start:
            start_time = st.time_input("Start Time", value=time(9, 0))
        with col_end:
            end_time = st.time_input("End Time", value=time(10, 0))

        col_save, col_cancel = st.columns([1, 1])
        with col_save:
            submitted = st.form_submit_button(
                "Save Event", type="primary", use_container_width=True
            )

        if submitted:
            if not title.strip():
                st.error("Please enter an event name.")
                return

            if all_day:
                final_start = date_part
                final_end = date_part
            else:
                final_start = f"{date_part}T{start_time.strftime('%H:%M:%S')}"
                final_end = f"{date_part}T{end_time.strftime('%H:%M:%S')}"

            events = load_events()
            events.append({
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "start": final_start,
                "end": final_end,
                "date": date_part,
                "allDay": all_day,
                "backgroundColor": "#6366F1",
                "borderColor": "#4338CA"
            })
            save_events(events)
            st.rerun()


@st.dialog("✏ Edit or Delete Event")
def edit_event_dialog(event_data):
    events = load_events()
    event_id = event_data.get("id")

    title = st.text_input("Event Title", value=event_data.get("title", ""))
    start = st.text_input("Start Time", value=event_data.get("start", ""))
    end = st.text_input("End Time", value=event_data.get("end", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Update Event", type="primary", use_container_width=True):
            for e in events:
                if e.get("id") == event_id or e.get("title") == event_data.get(
                        "title"):
                    e["title"] = title
                    e["start"] = start
                    e["end"] = end
                    break
            save_events(events)
            st.rerun()

    with col2:
        if st.button("🗑️ Delete Event", use_container_width=True):
            events = [
                e for e in events
                if
                e.get("id") != event_id and e.get("title") != event_data.get(
                    "title")
            ]
            save_events(events)
            st.rerun()


def render_calendar(bg_color="#FFFFFF", text_color="#2C3E50",
                    initial_view="timeGridDay"):
    col_title, col_clean, col_sync = st.columns([2, 1, 1])
    with col_title:
        st.markdown(
            f"""
            <div style="background-color: {bg_color}; color: {text_color}; padding: 8px 12px; border-radius: 8px;">
                <h4 style="margin: 0; color: {text_color};">📅 Schedule & Calendar</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_clean:
        if st.button("🧹 Clean Stale Syncs", use_container_width=True):
            clear_stale_synced_events()
            sync_daily_logs_to_calendar()
            st.toast("Cleaned and re-indexed calendar events!", icon="✨")
            st.rerun()

    with col_sync:
        if st.button("🔄 Sync Today's Logs", use_container_width=True):
            sync_daily_logs_to_calendar()
            st.toast("Synced daily logs to schedule!", icon="✅")
            st.rerun()

    events = load_events()

    iframe_css = f"""
        .fc {{ background-color: {bg_color} !important; color: {text_color} !important; font-family: system-ui, sans-serif !important; }}
        .fc-theme-standard td, .fc-theme-standard th {{ border: 1px solid #E2E8F0 !important; }}
        .fc-timegrid-slot {{ height: 45px !important; }}
        .fc-timegrid-slot-label {{ color: {text_color} !important; font-weight: 500; text-decoration: none !important; }}
        .fc-col-header-cell-cushion {{ color: {text_color} !important; text-decoration: none !important; }}
        .fc-button-primary {{ background-color: #F1F5F9 !important; border-color: #CBD5E1 !important; color: #334155 !important; font-weight: 600; }}
        .fc-event {{ border-radius: 4px; padding: 2px 4px; font-size: 0.85rem; }}
    """

    calendar_options = {
        "editable": True,
        "selectable": True,
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "timeGridDay,timeGridWeek,dayGridMonth",
        },
        "initialView": initial_view,
        "slotDuration": "00:30:00",
        "slotMinTime": "06:00:00",
        "slotMaxTime": "23:00:00",
        "height": "700px",
        "allDaySlot": True,
        "timeFormat": "h:mm a",
        "eventTimeFormat": {
            "hour": "numeric",
            "minute": "2-digit",
            "meridiem": "short"
        }
    }

    cal_state = calendar(
        events=events,
        options=calendar_options,
        custom_css=iframe_css,
        key="modular_cal",
    )

    if cal_state.get("select"):
        add_event_dialog(
            cal_state["select"]["start"], cal_state["select"]["end"]
        )
    elif cal_state.get("dateClick"):
        add_event_dialog(
            cal_state["dateClick"]["date"], cal_state["dateClick"]["date"]
        )
    elif cal_state.get("eventClick"):
        edit_event_dialog(cal_state["eventClick"]["event"])