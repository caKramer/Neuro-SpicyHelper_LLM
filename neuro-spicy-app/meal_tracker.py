import json
import os
import streamlit as st
from annotated_text import annotated_text
from datetime import datetime
from json_store import save_json

MEAL_LOG_FILE = "meal_log.json"


def load_meal_log():
    if not os.path.exists(MEAL_LOG_FILE):
        return []
    try:
        with open(MEAL_LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []


def save_meal_log(log):
    save_json(MEAL_LOG_FILE, log)


def log_meal_entry(meal_name, meal_type="Meal", calories=0, effort="None"):
    now = datetime.now()
    log = load_meal_log()
    new_entry = {
        "timestamp": now.isoformat(),
        "time_str": now.strftime("%I:%M %p"),
        "date_str": now.strftime("%Y-%m-%d"),
        "name": meal_name,
        "type": meal_type,
        "calories": calories,
        "effort": effort,
    }
    log.append(new_entry)
    save_meal_log(log)


def render_meal_card(bg_color="#FFFFFF", text_color="#2C3E50"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    all_meals = load_meal_log()

    # Filter strictly for today's log entries
    today_meals = [
        m for m in all_meals
        if m.get("date_str") == today_str or m.get("timestamp", "").startswith(today_str)
    ]

    # Quick Log Water Button
    if st.button("🥛 Quick Log Water", use_container_width=True, type="secondary"):
        log_meal_entry("Glass of Water", meal_type="Drink")
        st.toast("Logged 1 cup of water!")
        st.rerun()

    st.subheader("🍽️ Today's Meal Tracker")
    if not today_meals:
        st.info("No meals logged yet today.")
    else:
        for entry in reversed(today_meals):
            item_name = entry.get("name", entry.get("item", "Meal"))
            item_time = entry.get("time_str", entry.get("time", ""))
            item_type = entry.get("type", "Meal")
            st.write(f"• **{item_time}** - {item_name} *({item_type})*")

    # --- ADD MEAL FORM ---
    with st.form("add_meal_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            meal_name = st.text_input("Meal / Food Item", placeholder="e.g. Oatmeal with berries")
            meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snack", "Drink"])
        with col2:
            calories = st.number_input("Est. Calories", min_value=0, max_value=3000, value=300, step=50)
            prep_effort = st.selectbox("Prep Effort", ["None", "Low", "Medium", "High"])

        if st.form_submit_button("Log Meal", use_container_width=True):
            if meal_name.strip():
                log_meal_entry(
                    meal_name=meal_name,
                    meal_type=meal_type,
                    calories=calories,
                    effort=prep_effort
                )
                st.success(f"Logged {meal_name}!")
                st.rerun()

    st.divider()

    # --- LOGGED MEALS DISPLAY (FILTERED TO TODAY ONLY) ---
    if today_meals:
        st.write(f"**Today's Logged Items ({len(today_meals)}):**")
        for idx, entry in enumerate(today_meals):
            with st.container():
                st.markdown(f"**{idx + 1}. {entry['name']}**")

                type_color = {
                    "Breakfast": "#fef08a",
                    "Lunch": "#bbf7d0",
                    "Dinner": "#bfdbfe",
                    "Snack": "#fed7aa",
                    "Drink": "#AAFEE5"
                }.get(entry.get("type"), "#e2e8f0")

                effort_color = {
                    "None": "#bbf7d0",
                    "Low": "#bfdbfe",
                    "Medium": "#fef08a",
                    "High": "#fecaca"
                }.get(entry.get("effort"), "#e2e8f0")

                time_display = entry.get("time_str", entry.get("time", ""))

                annotated_text(
                    ("Time", time_display, "#fbcfe8") if time_display else "",
                    " " if time_display else "",
                    ("Type", entry.get("type", "Meal"), type_color),
                    " ",
                    ("Calories", f"{entry.get('calories', 0)} kcal", "#e2e8f0"),
                    " ",
                    ("Prep Effort", entry.get("effort", "N/A"), effort_color),
                )
                st.write("")
    else:
        st.info("No meals logged yet today.")