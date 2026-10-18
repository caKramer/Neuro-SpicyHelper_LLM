import json
import os
import uuid
import pandas as pd
import streamlit as st
from json_store import save_json

SAFE_FOODS_FILE = "safe_foods.json"
SHOPPING_FILE = "shopping_list.json"

DEFAULT_SAFE_FOODS = [
    {
        "id": "food_mac_and_cheese",
        "name": "Mac & Cheese",
        "category": "Lunch",
        "texture": "Soft",
        "taste": "Savory",
        "temp": "Warm",
        "effort": "Low",
        "notes": "Easy comfort food",
    },
    {
        "id": "food_apple_pb",
        "name": "Apple Slices & Peanut Butter",
        "category": "Snack",
        "texture": "Crunchy",
        "taste": "Sweet",
        "temp": "Room Temperature",
        "effort": "Low",
        "notes": "Quick energy",
    },
    {
        "id": "food_greek_yogurt",
        "name": "Greek Yogurt",
        "category": "Snack",
        "texture": "Smooth",
        "taste": "Sour",
        "temp": "Cold",
        "effort": "Low",
        "notes": "High protein",
    },
]


def load_safe_foods():
    if not os.path.exists(SAFE_FOODS_FILE):
        save_safe_foods(DEFAULT_SAFE_FOODS)
        return pd.DataFrame(DEFAULT_SAFE_FOODS)
    try:
        with open(SAFE_FOODS_FILE, "r") as f:
            data = json.load(f)

            # Auto-backfill missing IDs for existing legacy records
            updated = False
            for item in data:
                if "id" not in item or not item["id"]:
                    item["id"] = f"food_{uuid.uuid4().hex[:8]}"
                    updated = True

            if updated:
                save_safe_foods(data)

            return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame(DEFAULT_SAFE_FOODS)


def save_safe_foods(foods_list):
    save_json(SAFE_FOODS_FILE, foods_list)


def load_shopping_list():
    if not os.path.exists(SHOPPING_FILE):
        return []
    try:
        with open(SHOPPING_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def save_shopping_list(items):
    save_json(SHOPPING_FILE, items)


def render_safe_food_tracker():
    st.subheader("🍱 Favorite Food Registry")
    st.write("A low-demand registry of go-to favorite foods and meal options.")

    df_foods = load_safe_foods()

    # --- TOP CONTROL BAR: ADD NEW FOOD ---
    col_add, col_search = st.columns([1, 2])

    with col_add:
        with st.popover("➕ Add Favorite Food", use_container_width=True):
            st.markdown("### Add New Favorite Food")
            with st.form("add_food_form", clear_on_submit=True):
                name = st.text_input("Food Name:")
                category = st.selectbox(
                    "Category:",
                    ["Breakfast", "Lunch", "Dinner", "Snack", "Drink",
                     "Other"],
                )
                texture = st.selectbox(
                    "Texture:",
                    ["Soft", "Crunchy", "Smooth", "Chewy", "Liquid", "Gloopy",
                     "Other"],
                )
                taste = st.selectbox(
                    "Taste:",
                    ["Sweet", "Sour", "Salty", "Savory", "Other"],
                )
                temperature = st.selectbox(
                    "Temperature:",
                    ["Cold", "Room Temperature", "Warm", "Hot", "Any"]
                )
                effort = st.select_slider(
                    "Preparation Effort:",
                    options=["None", "Low", "Medium", "High"]
                )
                notes = st.text_area(
                    "Notes / Prep Tips:", placeholder="e.g. Microwave for 90s"
                )

                if st.form_submit_button("Save Food to Registry",
                                         use_container_width=True):
                    if name.strip():
                        current_data = load_safe_foods().to_dict(
                            orient="records")
                        current_data.append(
                            {
                                "id": f"food_{uuid.uuid4().hex[:8]}",
                                "name": name.strip(),
                                "category": category,
                                "texture": texture,
                                "taste": taste,
                                "temp": temperature,
                                "effort": effort,
                                "notes": notes.strip(),
                            }
                        )
                        save_safe_foods(current_data)
                        st.toast(f"Added {name}!", icon="✅")
                        st.rerun()

    with col_search:
        search_query = st.text_input(
            "Filter foods...",
            placeholder="Search by name, category, or texture...",
            label_visibility="collapsed",
        )

    if search_query:
        mask = (
                df_foods["name"].str.contains(search_query, case=False,
                                              na=False)
                | df_foods["category"].str.contains(search_query, case=False,
                                                    na=False)
                | df_foods["taste"].str.contains(search_query, case=False,
                                                 na=False)
                | df_foods["effort"].str.contains(search_query, case=False,
                                                  na=False)
                | df_foods["texture"].str.contains(search_query, case=False,
                                                   na=False)
                | df_foods["temp"].str.contains(search_query, case=False,
                                                na=False)
                | df_foods["notes"].str.contains(search_query, case=False,
                                                 na=False)
        )
        display_df = df_foods[mask]
    else:
        display_df = df_foods

    st.write("")

    if not display_df.empty:
        edited_df = st.data_editor(
            display_df,
            column_config={
                "id": None,  # Hide ID column in the Streamlit UI table
                "name": st.column_config.TextColumn(
                    "Food Item",
                    help="Name of the favorite food",
                    width="medium",
                    required=True,
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    width="small",
                    options=["Breakfast", "Lunch", "Dinner", "Snack", "Drink",
                             "Other"],
                    required=True,
                ),
                "texture": st.column_config.SelectboxColumn(
                    "Texture",
                    width="small",
                    options=["Soft", "Crunchy", "Smooth", "Chewy", "Liquid",
                             "Gloopy", "Any"],
                    required=True,
                ),
                "taste": st.column_config.SelectboxColumn(
                    "Taste",
                    width="small",
                    options=["Sweet", "Sour", "Salty", "Savory", "Other"],
                    required=True,
                ),
                "effort": st.column_config.SelectboxColumn(
                    "Effort Level",
                    width="small",
                    options=["None", "Low", "Medium", "High"],
                    required=True,
                ),
                "temp": st.column_config.SelectboxColumn(
                    "Temperature",
                    width="small",
                    options=["Cold", "Room Temperature", "Warm", "Hot", "Any"],
                    required=True,
                ),
                "notes": st.column_config.TextColumn(
                    "Notes & Preparation Tips",
                    width="large",
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="safe_foods_editor",
        )

        col_save, _ = st.columns([1, 3])
        with col_save:
            if st.button("💾 Save Table Changes", use_container_width=True):
                edited_records = edited_df.to_dict(orient="records")

                # Backfill IDs for newly added table rows from data_editor
                for rec in edited_records:
                    if not isinstance(rec.get("id"), str) or not rec["id"]:
                        rec["id"] = f"food_{uuid.uuid4().hex[:8]}"

                # The editor only shows rows matching the search filter, so merge
                # its edits into the full registry instead of replacing it.
                visible_ids = set(display_df["id"])
                edited_by_id = {rec["id"]: rec for rec in edited_records}
                updated_records = []
                for rec in df_foods.to_dict(orient="records"):
                    if rec["id"] not in visible_ids:
                        updated_records.append(rec)
                    elif rec["id"] in edited_by_id:
                        updated_records.append(edited_by_id.pop(rec["id"]))
                updated_records.extend(edited_by_id.values())

                save_safe_foods(updated_records)
                st.toast("Favorite foods registry updated!", icon="✅")
                st.rerun()
    else:
        st.info("No favorite foods found matching your search.")