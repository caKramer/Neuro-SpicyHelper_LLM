import json
import os
from datetime import datetime
import streamlit as st

MEDS_LOG_FILE = "medication_log.json"


def load_medications():
    """Loads medication entries from the JSON file."""
    if not os.path.exists(MEDS_LOG_FILE):
        return []
    try:
        with open(MEDS_LOG_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def save_medications(meds):
    """Saves medication entries to the JSON file."""
    with open(MEDS_LOG_FILE, "w") as f:
        json.dump(meds, f, indent=2)


def log_medication_taken(med_index):
    """Marks a medication as taken and records the exact current timestamp."""
    meds = load_medications()
    if 0 <= med_index < len(meds):
        meds[med_index]["taken"] = True
        meds[med_index]["logged_at_time"] = datetime.now().strftime("%I:%M %p").lstrip("0")
        save_medications(meds)
        return True
    return False


def render_medication_tracker():
    """Renders medication content directly without adding an inner @st.dialog decorator."""
    st.subheader("💊 Medication Tracker")

    meds = load_medications()

    # --- ADD NEW MEDICATION FORM ---
    with st.expander("➕ Add New Medication Schedule", expanded=False):
        with st.form("add_med_form", clear_on_submit=True):
            med_name = st.text_input("Medication Name", placeholder="e.g. Advil, Vitamin D")
            dosage = st.text_input("Dosage", placeholder="e.g. 200mg, 1 tablet")
            sched_time = st.time_input("Scheduled Time", datetime.now().time())

            submitted = st.form_submit_button("Add Medication", use_container_width=True)

            if submitted:
                if med_name.strip():
                    new_med = {
                        "name": med_name.strip(),
                        "dosage": dosage.strip(),
                        "time": sched_time.strftime("%I:%M %p").lstrip("0"),
                        "taken": False,
                        "logged_at_time": None
                    }
                    meds.append(new_med)
                    save_medications(meds)
                    st.toast(f"Added {med_name.strip()} to schedule!", icon="💊")
                    st.rerun()
                else:
                    st.warning("Please enter a medication name.")

    st.divider()

    # --- MEDICATION LIST AND LOGGING ---
    if meds:
        st.write("**Today's Medications:**")
        for idx, med in enumerate(meds):
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{med.get('name')}** (`{med.get('dosage', 'N/A')}`)")
                st.caption(f"Scheduled: {med.get('time', 'N/A')}")

            with col2:
                if med.get("taken", False):
                    logged_time = med.get("logged_at_time", "N/A")
                    st.success(f"Taken at {logged_time}")
                else:
                    st.info("Pending")

            with col3:
                if not med.get("taken", False):
                    if st.button("Mark Taken", key=f"med_btn_{idx}", use_container_width=True):
                        log_medication_taken(idx)
                        st.toast(f"Logged {med.get('name')} as taken!", icon="✅")
                        st.rerun()
                else:
                    if st.button("Reset", key=f"med_reset_btn_{idx}", use_container_width=True):
                        meds[idx]["taken"] = False
                        meds[idx]["logged_at_time"] = None
                        save_medications(meds)
                        st.rerun()
            st.divider()
    else:
        st.info("No medications added yet. Use the form above to schedule your doses.")


def render_medication_dialog():
    """Alias pointing to render_medication_tracker for backwards compatibility."""
    render_medication_tracker()