import json
import os
from datetime import datetime
import streamlit as st
from annotated_text import annotated_text
from json_store import save_json

ACTIVITY_LOG_FILE = "activity_log.json"


def load_activity_log():
    if not os.path.exists(ACTIVITY_LOG_FILE):
        return []
    try:
        with open(ACTIVITY_LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_activity_log(log):
    save_json(ACTIVITY_LOG_FILE, log)


def log_wake_sleep_event(name):
    """Record an 'I'm awake!' or 'Sleep time!' event with the current timestamp
    and date string in the activity tracker log for the day."""
    activities = load_activity_log()
    now = datetime.now()
    activities.append({
        "timestamp": now.isoformat(),
        "date_str": now.strftime("%Y-%m-%d"),
        "time_str": now.strftime("%I:%M %p"),
        "name": name,
        "duration": 0,
        "intensity": "N/A",
        "sensory": "N/A",
        "time": now.strftime("%I:%M %p"),
    })
    save_activity_log(activities)
    return now


def render_activity_card(bg_color="#FFFFFF", text_color="#2C3E50"):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    activities = load_activity_log()

    # Filter strictly for today's activity entries
    today_activities = [
        a for a in activities
        if a.get("date_str") == today_str or a.get("timestamp", "").startswith(today_str)
    ]

    st.subheader("🧘 Today's Activity Log")

    if not today_activities:
        st.info("No activity logged yet today.")
    else:
        for entry in reversed(today_activities):
            act_name = entry.get("name", "Activity")
            act_time = entry.get("time", entry.get("time_str", ""))
            dur = f" ({entry.get('duration')} mins)" if entry.get("duration") else ""
            st.write(f"• **{act_time}** - {act_name}{dur}")

    # --- ADD ACTIVITY FORM ---
    with st.form("add_activity_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            act_name = st.text_input("Activity Name", placeholder="e.g. Walking, Stretches, Dancing")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=300, value=15, step=5)
        with col2:
            intensity = st.selectbox("Intensity Level", ["Gentle / Low Demand", "Moderate", "High Energy"])
            sensory_env = st.selectbox("Sensory Environment", ["Calm & Quiet", "Outdoors / Nature", "Music / Upbeat", "High Stimulus"])

        if st.form_submit_button("Log Activity", use_container_width=True):
            if act_name.strip():
                log_time = datetime.now()
                activities.append({
                    "timestamp": log_time.isoformat(),
                    "date_str": log_time.strftime("%Y-%m-%d"),
                    "time_str": log_time.strftime("%I:%M %p"),
                    "time": log_time.strftime("%I:%M %p"),
                    "name": act_name,
                    "duration": duration,
                    "intensity": intensity,
                    "sensory": sensory_env
                })
                save_activity_log(activities)
                st.success(f"Logged {act_name}!")
                st.rerun()

    st.divider()

    # --- LOGGED ACTIVITIES DISPLAY (FILTERED TO TODAY ONLY) ---
    if today_activities:
        st.write(f"**Today's Logged Movement ({len(today_activities)}):**")
        for idx, entry in enumerate(today_activities):
            with st.container():
                st.markdown(f"**{idx + 1}. {entry['name']}**")

                intensity_color = {
                    "Gentle / Low Demand": "#bbf7d0",
                    "Moderate": "#fef08a",
                    "High Energy": "#fecaca"
                }.get(entry.get("intensity"), "#e2e8f0")

                sensory_color = {
                    "Calm & Quiet": "#bfdbfe",
                    "Outdoors / Nature": "#bbf7d0",
                    "Music / Upbeat": "#fed7aa",
                    "High Stimulus": "#ddd6fe"
                }.get(entry.get("sensory"), "#e2e8f0")

                if entry.get("intensity") == "N/A" and entry.get("sensory") == "N/A":
                    annotated_text(
                        ("Time", entry.get("time", entry.get("time_str", "")), "#fbcfe8"),
                    )
                else:
                    annotated_text(
                        ("Duration", f"{entry.get('duration', 0)} mins", "#e2e8f0"),
                        " ",
                        ("Intensity", entry.get("intensity", "N/A"), intensity_color),
                        " ",
                        ("Environment", entry.get("sensory", "N/A"), sensory_color),
                    )
                st.write("")
    else:
        st.info("No movement logged for today yet.")