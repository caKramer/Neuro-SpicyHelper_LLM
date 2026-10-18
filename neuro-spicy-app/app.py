import json
import os
import re
import urllib.parse
import activity_tracker as act
import calendar_component as cal
import meal_tracker as meal
import safe_food_library as sfl
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
from streamlit_elements import dashboard, elements, html, mui
from streamlit_option_menu import option_menu
import streamlit_shadcn_ui as ui
import medication_tracker as med_trk
from datetime import datetime
from dashboard_component import init_dashboard_layout
import requests

# Page Configuration & Layout Init
init_dashboard_layout()
st.set_page_config(page_title="Neuro-Spicy Support Assistant", layout="wide")

SETTINGS_FILE = "widget_settings.json"
CAPACITY_STATE_FILE = "capacity_state.json"

DEFAULT_LAYOUT = [
    {"i": "calendar", "x": 0, "y": 0, "w": 6, "h": 14},
    {"i": "activity", "x": 6, "y": 0, "w": 6, "h": 14},
    {"i": "meal", "x": 0, "y": 14, "w": 6, "h": 14},
    {"i": "foods", "x": 6, "y": 14, "w": 6, "h": 14},
]

def get_energy_from_spoons(spoons: int) -> tuple[str, int]:
    """
    Maps Spoons Capacity (0-12) to Energy Level and returns both
    the label string and the slider index position.
    """
    if spoons <= 1:
        return "None", 0
    elif spoons <= 5:
        return "Low", 1
    elif spoons <= 9:
        return "Medium", 2
    else:
        return "High", 3

def load_settings():
    default_settings = {
        "user_name": "",
        "colors": {
            "calendar": {"bg": "#ef95d7", "text": "#b61886"},
            "meal": {"bg": "#cb8bf5", "text": "#511ca5"},
            "activity": {"bg": "#3eb0e6", "text": "#0c3359"},
            "foods": {"bg": "#41efe7", "text": "#042c31"},
        },
        "layout": DEFAULT_LAYOUT,
    }
    if not os.path.exists(SETTINGS_FILE):
        return default_settings
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            if "layout" not in data or not isinstance(data["layout"], list) or len(data["layout"]) != 4:
                data["layout"] = DEFAULT_LAYOUT
            if "user_name" not in data:
                data["user_name"] = ""
            return data
    except Exception:
        return default_settings


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def load_capacity_state():
    default_state = {"spoons_count": 12, "water_count": 0, "synced_drink_count": 0}
    if not os.path.exists(CAPACITY_STATE_FILE):
        return default_state
    try:
        with open(CAPACITY_STATE_FILE, "r") as f:
            data = json.load(f)
            for key, default in default_state.items():
                data.setdefault(key, default)
            return data
    except (json.JSONDecodeError, ValueError):
        return default_state


def save_capacity_state():
    with open(CAPACITY_STATE_FILE, "w") as f:
        json.dump(
            {
                "spoons_count": st.session_state.spoons_count,
                "water_count": st.session_state.water_count,
                "synced_drink_count": st.session_state.synced_drink_count,
            },
            f,
            indent=2,
        )


settings = load_settings()

if "active_layout" not in st.session_state:
    st.session_state["active_layout"] = settings.get("layout", DEFAULT_LAYOUT)

# Global session state initializations
if "user_name" not in st.session_state:
    st.session_state.user_name = settings.get("user_name", "")
if "spoons_count" not in st.session_state:
    _capacity_state = load_capacity_state()
    st.session_state.spoons_count = _capacity_state["spoons_count"]
    st.session_state.water_count = _capacity_state["water_count"]
    st.session_state.synced_drink_count = _capacity_state["synced_drink_count"]

if "spoon_slider" not in st.session_state:
    st.session_state["spoon_slider"] = st.session_state.spoons_count
if "water_slider" not in st.session_state:
    st.session_state["water_slider"] = st.session_state.water_count
if "active_dialog" not in st.session_state:
    st.session_state.active_dialog = None


def _clear_active_dialog():
    st.session_state.active_dialog = None


# --- ONLY AUTOREFRESH ON MAIN PAGE, NOT INSIDE IFRAME TILES ---
if st.session_state.active_dialog is None and "embed_tile" not in st.query_params:
    st_autorefresh(interval=3000, key="dashboard_autorefresh")

# --- AUTOMATIC HYDRATION SLIDER & METRIC SYNC ---
_meal_log = meal.load_meal_log()
_today_str = datetime.now().strftime("%Y-%m-%d")

# Count drinks logged today specifically
_today_drinks = sum(
    1 for m in _meal_log
    if m.get("type") == "Drink" and m.get("date_str", "") == _today_str
)

_new_drinks = _today_drinks - st.session_state.synced_drink_count

if _new_drinks > 0:
    st.session_state.water_count = min(16, st.session_state.water_count + _new_drinks)
    st.session_state["water_slider"] = st.session_state.water_count
    st.session_state.synced_drink_count = _today_drinks
    save_capacity_state()
elif _today_drinks != st.session_state.synced_drink_count:
    st.session_state.synced_drink_count = _today_drinks
    save_capacity_state()

# Calendar Sync
if hasattr(cal, "sync_end_of_day_summary_to_calendar"):
    cal.sync_end_of_day_summary_to_calendar()

# --- QUERY PARAM ROUTER FOR EMBEDDED TILES ---
query_params = st.query_params
if "embed_tile" in query_params:
    tile_type = query_params["embed_tile"]

    st.markdown(
        """
        <style>
            html, body, #root, .stAppViewContainer, .stApp {
                padding: 6px !important;
                margin: 0 !important;
                background-color: transparent !important;
                box-sizing: border-box !important;
            }
            .stMainBlockContainer, div[data-testid="stMainBlockContainer"], .main .block-container {
                padding: 0px !important;
                margin: 0px !important;
                max-width: 100% !important;
                width: 100% !important;
            }
            header, footer, [data-testid="stHeader"], [data-testid="stToolbar"] { 
                display: none !important; 
                height: 0px !important;
            }
            div[data-testid="stVerticalBlock"] {
                gap: 0.25rem !important;
                padding: 0px !important;
                margin: 0px !important;
                width: 100% !important;
                height: 100% !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if tile_type == "calendar":
        bg = query_params.get("bg", "#FFFFFF")
        txt = query_params.get("txt", "#2C3E50")
        cal.render_calendar(bg_color=bg, text_color=txt)

    elif tile_type == "meal":
        bg = query_params.get("bg", "#FFFFFF")
        txt = query_params.get("txt", "#2C3E50")

        # Auto-refresh loop inside meal iframe to pick up external file changes without reloading full window
        st_autorefresh(interval=2000, key="meal_iframe_autorefresh")

        meal.render_meal_card(bg_color=bg, text_color=txt)

    elif tile_type == "activity":
        bg = query_params.get("bg", "#FFFFFF")
        txt = query_params.get("txt", "#2C3E50")
        act.render_activity_card(bg_color=bg, text_color=txt)

    elif tile_type in ["foods", "safe_foods"]:
        bg = query_params.get("bg", "#FFFFFF")
        txt = query_params.get("txt", "#2C3E50")

        st.markdown(
            f"""
                <style>
                    html, body, .stApp, p, span, label, h1, h2, h3, h4, h5, h6, div {{
                        color: {txt} !important;
                    }}
                    div[data-testid="stSegmentedControl"] button {{
                        border-radius: 20px !important;
                        font-weight: 600 !important;
                    }}
                </style>
                """,
            unsafe_allow_html=True,
        )

        st.subheader("🍱 Decision Assistant")
        st.write("Need help deciding what to eat, breaking down a task, or de-escalating overload?")

        pill_options = [
            "Food Options",
            "Task Breakdown",
            "Chat Help with Overwhelm",
            "Custom Prompt Input"
        ]

        if "assistant_mode" not in st.session_state:
            st.session_state["assistant_mode"] = "Food Options"

        if hasattr(st, "segmented_control"):
            selected_pill = st.segmented_control(
                "Mode",
                options=pill_options,
                default=st.session_state["assistant_mode"],
                label_visibility="collapsed",
                key="assistant_pill_selector",
            )
        else:
            selected_pill = st.radio(
                "Mode",
                options=pill_options,
                index=0,
                horizontal=True,
                label_visibility="collapsed",
                key="assistant_pill_selector",
            )

        # Clear output when switching tabs
        if selected_pill != st.session_state.get("last_selected_pill"):
            st.session_state["assistant_response"] = None
            st.session_state["last_selected_pill"] = selected_pill

        def run_ollama_generation(sys_prompt_text: str, usr_prompt_text: str, temp_val: float = 0.2):
            clean_sys = str(sys_prompt_text).strip()
            clean_usr = str(usr_prompt_text).strip()

            # Safeguard: Prevent empty/corrupted string inputs from reaching Ollama
            if not clean_usr or len(clean_usr) < 2:
                st.session_state["assistant_response"] = "Error: Please enter a valid prompt before generating."
                return

            # Construct explicit, raw Llama 3 header tokens
            formatted_raw_prompt = (
                f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
                f"{clean_sys}<|eot_id|>"
                f"<|start_header_id|>user<|end_header_id|>\n\n"
                f"{clean_usr}<|eot_id|>"
                f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            )

            payload = {
                "model": "llama3.2-3b-ft",
                "prompt": formatted_raw_prompt,
                "raw": True,  # Completely bypasses Ollama's Go template processing
                "stream": False,
                "keep_alive": 0,
                "options": {
                    "temperature": float(temp_val),
                    "repeat_penalty": 1.18,
                    "top_p": 0.9,
                    "stop": ["<|eot_id|>", "<|eom_id|>", "<|start_header_id|>", "<|end_header_id|>"],
                    "num_predict": 200,
                }
            }

            try:
                # Target /api/generate instead of /api/chat
                res = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=30)
                if res.status_code == 200:
                    res_json = res.json()
                    res_content = str(res_json.get("response", "")).strip()
                    st.session_state["assistant_response"] = res_content if res_content else "No output returned."
                else:
                    st.session_state["assistant_response"] = f"HTTP Error {res.status_code}: {res.text}"
            except Exception as e:
                st.session_state["assistant_response"] = f"Connection Error: {str(e)}"

        # ----------------------------------------------------
        # 1. FOOD OPTIONS MODE
        # ----------------------------------------------------
        if selected_pill == "Food Options":
            current_spoons = st.session_state.get("spoons_count", 2)
            default_energy_label, _ = get_energy_from_spoons(current_spoons)
            energy_options = ["None", "Low", "Medium", "High"]

            col1, col2 = st.columns(2)
            with col1:
                energy_input = st.select_slider(
                    f"Energy Level (Auto-set from {current_spoons} Spoons):",
                    options=energy_options,
                    value=default_energy_label,
                    key="food_energy_slider"
                )
            with col2:
                texture_input = st.selectbox(
                    "Texture Preference:",
                    ["Soft", "Crunchy", "Smooth", "Chewy", "Any", "Gloopy", "Liquid"],
                    key="food_texture_select"
                )

            df_foods = sfl.load_safe_foods()
            foods_json = df_foods.to_json(orient="records") if not df_foods.empty else "[]"

            sys_p = f"You are a helpful peer assistant. Suggest 2 safe foods from this registry matching energy '{energy_input}' and texture '{texture_input}': {foods_json}"
            usr_p = f"Suggest 2 quick safe food ideas for Energy Level: {energy_input} and Texture Preference: {texture_input}."

            if st.button("✨ Generate Food Options", use_container_width=True, type="primary", key="btn_gen_food"):
                with st.spinner("Generating response with local Llama 3.2..."):
                    run_ollama_generation(sys_p, usr_p, temp_val=0.2)
                    st.rerun()

        # ----------------------------------------------------
        # 2. TASK BREAKDOWN MODE
        # ----------------------------------------------------
        elif selected_pill == "Task Breakdown":
            st.caption("Enter a task causing executive paralysis. The assistant will split it into ≤3 tiny steps.")
            task_desc_input = st.text_input(
                "What task feels overwhelming right now?",
                placeholder="e.g. Cleaning the kitchen sink, sending a work email, folding laundry",
                key="task_desc_text_input"
            )

            sys_p = "You are a low-demand executive dysfunction coach. Break tasks into 3 tiny, friction-free micro-steps."
            usr_p = f"Task to break down: {task_desc_input}" if task_desc_input.strip() else "Task: Clean my desk space"

            if st.button("✨ Break Down Task", use_container_width=True, type="primary", key="btn_gen_task"):
                with st.spinner("Generating response with local Llama 3.2..."):
                    run_ollama_generation(sys_p, usr_p, temp_val=0.2)
                    st.rerun()

        # ----------------------------------------------------
        # 3. CHAT HELP WITH OVERWHELM MODE
        # ----------------------------------------------------
        elif selected_pill == "Chat Help with Overwhelm":
            st.caption("Use this when overstimulated or in a brain freeze.")
            overwhelm_text_input = st.text_area(
                "What is overwhelming you right now?",
                value="Everything is too loud and I have too many things on my to-do list.",
                key="overwhelm_text_area"
            )

            sys_p = "You are a warm, low-demand support assistant. Provide short de-escalation guidance."
            usr_p = str(overwhelm_text_input)

            if st.button("✨ Get Support & De-stress", use_container_width=True, type="primary", key="btn_gen_overwhelm"):
                with st.spinner("Generating response with local Llama 3.2..."):
                    run_ollama_generation(sys_p, usr_p, temp_val=0.3)
                    st.rerun()

        # ----------------------------------------------------
        # 4. CUSTOM PROMPT INPUT MODE
        # ----------------------------------------------------
        elif selected_pill == "Custom Prompt Input":
            custom_sys_input = st.text_area(
                "System Prompt:",
                value="You are an empathetic, low-demand assistant. Help the user gently.",
                key="custom_sys_area"
            )
            custom_usr_input = st.text_area(
                "User Input:",
                value="I need help deciding what to do next.",
                key="custom_usr_area"
            )
            custom_temp_input = st.slider("Temperature:", 0.0, 1.0, 0.2, key="custom_temp_slider")

            if st.button("✨ Generate Custom Response", use_container_width=True, type="primary", key="btn_gen_custom"):
                with st.spinner("Generating response with local Llama 3.2..."):
                    run_ollama_generation(custom_sys_input, custom_usr_input, temp_val=custom_temp_input)
                    st.rerun()

        # ----------------------------------------------------
        # PERSISTENT RENDER LOGIC
        # ----------------------------------------------------
        saved_result = st.session_state.get("assistant_response")

        if saved_result:
            if saved_result.startswith("Error:") or saved_result.startswith("Connection Error:") or saved_result.startswith("HTTP Error"):
                st.error(saved_result)
            else:
                def _log_selection(item_name):
                    item_lower = item_name.lower()
                    item_type = (
                        "Drink"
                        if any(w in item_lower for w in ["water", "shake", "juice", "drink", "tea", "coffee", "smoothie", "liquid"])
                        else "Meal"
                    )
                    meal.log_meal_entry(item_name, item_type)

                st.success("**Assistant Response:**")
                st.write(saved_result)

                # Parse bold items into interactive meal buttons (food suggestions only)
                bold_matches = []
                if selected_pill == "Food Options":
                    bold_matches = re.findall(r'\d+\.\s*\*\*([^*]+)\*\*', saved_result)
                if selected_pill == "Food Options" and not bold_matches:
                    bold_matches = re.findall(r'\*\*([^*]+)\*\*', saved_result)

                if bold_matches:
                    st.markdown("**Quick Actions:**")
                    cols = st.columns(min(len(bold_matches[:2]), 2))
                    for idx, item in enumerate(bold_matches[:2]):
                        clean_item = item.strip()
                        with cols[idx]:
                            if st.button(f"🍱 Log {clean_item}", key=f"btn_prose_{idx}", use_container_width=True):
                                _log_selection(clean_item)
                                st.toast(f"Logged {clean_item} to Today's Meals!")

    st.stop()

# --- SIDEBAR: USER PROFILE & STYLE CONTROLS ---
st.sidebar.title("👤 User Profile")
name_input = st.sidebar.text_input(
    "Enter your name:",
    value=st.session_state.get("user_name", ""),
    placeholder="e.g. Callista",
)

if name_input != st.session_state.user_name:
    st.session_state.user_name = name_input
    settings["user_name"] = name_input
    save_settings(settings)

st.sidebar.divider()
st.sidebar.title("🎨 Style Customization")

bg_cal = settings["colors"]["calendar"]["bg"]
txt_cal = settings["colors"]["calendar"]["text"]
bg_meal = settings["colors"]["meal"]["bg"]
txt_meal = settings["colors"]["meal"]["text"]
bg_act = settings["colors"]["activity"]["bg"]
txt_act = settings["colors"]["activity"]["text"]
bg_foods = settings["colors"]["foods"]["bg"]
txt_foods = settings["colors"]["foods"]["text"]

with st.sidebar.expander("📅 Calendar Colors", expanded=False):
    bg_cal_input = st.color_picker("Background", bg_cal, key="c_bg")
    txt_cal_input = st.color_picker("Text", txt_cal, key="c_txt")

with st.sidebar.expander("🍽️ Meal Tracker Colors", expanded=False):
    bg_meal_input = st.color_picker("Background", bg_meal, key="m_bg")
    txt_meal_input = st.color_picker("Text", txt_meal, key="m_txt")

with st.sidebar.expander("🧘 Activity Colors", expanded=False):
    bg_act_input = st.color_picker("Background", bg_act, key="a_bg")
    txt_act_input = st.color_picker("Text", txt_act, key="a_txt")

with st.sidebar.expander("🍱 Safe Food Colors", expanded=False):
    bg_foods_input = st.color_picker("Background", bg_foods, key="f_bg")
    txt_foods_input = st.color_picker("Text", txt_foods, key="f_txt")

if st.sidebar.button("💾 Save Style Preferences", use_container_width=True):
    settings["colors"] = {
        "calendar": {"bg": bg_cal_input, "text": txt_cal_input},
        "meal": {"bg": bg_meal_input, "text": txt_meal_input},
        "activity": {"bg": bg_act_input, "text": txt_act_input},
        "foods": {"bg": bg_foods_input, "text": txt_foods_input},
    }
    save_settings(settings)
    st.sidebar.success("Preferences saved!")
    st.rerun()

# --- TOP NAVIGATION BAR ---
selected_tab = option_menu(
    menu_title=None,
    options=["Dashboard", "Settings"],
    icons=["speedometer2", "gear"],
    orientation="horizontal",
    styles={
        "container": {"2px padding": "0!important", "background-color": "#f8fafc"},
        "icon": {"color": "#b61886", "font-size": "16px"},
        "nav-link-selected": {"background-color": "#cb8bf5", "color": "white"},
    },
)

# --- DYNAMIC USER TITLE ---
if st.session_state.user_name.strip():
    user = st.session_state.user_name.strip()
    title_text = f"{user}' Daily Dashboard" if user.endswith("s") else f"{user}'s Daily Dashboard"
else:
    title_text = "Daily Capacity & Dashboard"

title_col, wake_col, sleep_col = st.columns([6, 1, 1])
with title_col:
    st.title(title_text)
with wake_col:
    st.write("")
    if st.button("☀ I'm awake!", use_container_width=True):
        wake_time = act.log_wake_sleep_event("Woke Up")
        st.toast(f"Wake time logged at {wake_time.strftime('%I:%M %p')}!")
with sleep_col:
    st.write("")
    if st.button("🌙 Sleep time!", use_container_width=True):
        sleep_time = act.log_wake_sleep_event("Went to Sleep")
        st.toast(f"Sleep time logged at {sleep_time.strftime('%I:%M %p')}!")

# --- TOP TRACKERS HEADER (SHADCN UI INTEGRATION) ---
if selected_tab == "Dashboard":
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        _spoons_display = st.session_state["spoon_slider"]
        ui.metric_card(
            "🥄 Spoons Capacity",
            f"{_spoons_display} / 12",
            description="Daily energy units remaining",
            key="spoons_kpi",
        )
        st.caption("How much energy do you have today?")
        _prev_spoons = st.session_state.spoons_count
        st.session_state.spoons_count = st.slider(
            "Adjust Spoons:", 0, 12, key="spoon_slider"
        )
        if st.session_state.spoons_count != _prev_spoons:
            save_capacity_state()

    with col2:
        _water_display = st.session_state["water_slider"]
        ui.metric_card(
            "🥛 Hydration Log",
            f"{_water_display} / 12 Cups",
            description="Daily water tracking",
            key="water_kpi",
        )
        st.caption("Have you had anything to drink today?")
        _prev_water = st.session_state.water_count
        st.session_state.water_count = st.slider(
            "Adjust Cups:", 0, 16, key="water_slider"
        )
        if st.session_state.water_count != _prev_water:
            save_capacity_state()

    with col3:
        ui.metric_card(
            "💊 Medications",
            "Daily Log",
            description="Track dosage & status",
            key="meds_kpi",
        )
        st.caption("Did you remember to take your meds?")

        @st.dialog("Medication Tracker", on_dismiss=_clear_active_dialog)
        def manage_medications():
            med_trk.render_medication_tracker()

        if st.button(
            "Open Meds Log",
            use_container_width=True,
            on_click=lambda: st.session_state.update(active_dialog="meds"),
        ):
            manage_medications()

    with col4:
        ui.metric_card(
            "🛒 Shopping List",
            "Manage Items",
            description="Pantry & grocery list",
            key="shopping_kpi",
        )
        st.caption("What groceries or supplies do you need?")

        @st.dialog("Shopping List", on_dismiss=_clear_active_dialog)
        def manage_shopping():
            items = sfl.load_shopping_list()
            new_item = st.text_input("Add Item:")
            new_cat = st.selectbox(
                "Category:", ["Produce", "Dairy", "Pantry", "Fridge", "Frozen", "Other"]
            )
            if st.button("Add Item", use_container_width=True):
                if new_item:
                    items.append({"item": new_item, "category": new_cat, "bought": False})
                    sfl.save_shopping_list(items)
                    st.rerun()
            st.divider()
            updated_items = []
            for idx, entry in enumerate(items):
                checked = st.checkbox(
                    f"{entry['item']} ({entry['category']})",
                    value=entry["bought"],
                    key=f"shop_{idx}",
                )
                updated_items.append(
                    {"item": entry["item"], "category": entry["category"], "bought": checked}
                )
            if st.button("Save Changes", use_container_width=True):
                sfl.save_shopping_list(updated_items)
                st.success("Updated!")

        if st.button(
            "Open Shopping List",
            use_container_width=True,
            on_click=lambda: st.session_state.update(active_dialog="shopping"),
        ):
            manage_shopping()

    with col5:
        ui.metric_card(
            "🍱 Favorite Foods",
            "Registry",
            description="Low-demand meal options",
            key="foods_kpi",
        )
        st.caption("What are your favorite foods right now?")

        @st.dialog("Favorite Foods", width="large", on_dismiss=_clear_active_dialog)
        def manage_safe_foods():
            sfl.render_safe_food_tracker()

        if st.button(
            "Open Favorite Foods",
            use_container_width=True,
            on_click=lambda: st.session_state.update(active_dialog="foods"),
        ):
            manage_safe_foods()

    st.divider()

    def build_iframe_url(tile_name, bg_color, text_color):
        # Escape '#' and special characters so iframe URLs don't truncate
        safe_bg = urllib.parse.quote_plus(str(bg_color))
        safe_txt = urllib.parse.quote_plus(str(text_color))
        return f"/?embed_tile={tile_name}&bg={safe_bg}&txt={safe_txt}"

    layout_to_render = st.session_state["active_layout"]

    def handle_layout_change(new_layout):
        pass

    def persist_layout_from_frontend():
        raw = st.session_state.get("streamlit_elements.core.frame.elements_frame.dashboard_canvas")
        if not raw:
            return
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except ValueError:
            return
        expected = {"calendar", "activity", "meal", "foods"}
        for params in payload.values() if isinstance(payload, dict) else []:
            new_layout = params.get("new_layout") if isinstance(params, dict) else None
            if not isinstance(new_layout, list):
                continue
            clean = [
                {
                    "i": str(item["i"]),
                    "x": int(item.get("x", 0)),
                    "y": int(item.get("y", 0)),
                    "w": int(item.get("w", 6)),
                    "h": int(item.get("h", 14)),
                }
                for item in new_layout
                if "i" in item
            ]
            if {c["i"] for c in clean} != expected:
                continue
            if clean != st.session_state["active_layout"]:
                st.session_state["active_layout"] = clean
                settings["layout"] = clean
                save_settings(settings)

    persist_layout_from_frontend()
    layout_to_render = st.session_state["active_layout"]

    # --- DRAGGABLE & RESIZABLE DASHBOARD CANVAS ---
    with elements("dashboard_canvas"):
        html.style(
            """
            .react-grid-layout {
                min-height: 950px !important;
                width: 100% !important;
            }
            .react-grid-item {
                box-sizing: border-box !important;
            }
            """
        )

        with dashboard.Grid(
            layout=layout_to_render,
            cols={"lg": 12, "md": 12, "sm": 6, "xs": 4, "xxs": 2},
            rowHeight=30,
            margin=[16, 16],
            draggableHandle=".drag-handle",
            onLayoutChange=handle_layout_change,
        ):
            # Calendar Widget
            with mui.Card(
                key="calendar",
                sx={
                    "display": "flex",
                    "flexDirection": "column",
                    "backgroundColor": bg_cal,
                    "color": txt_cal,
                    "borderRadius": "8px",
                    "boxShadow": 3,
                    "height": "100%",
                    "minHeight": "400px",
                    "overflow": "hidden",
                    "padding": "6px",
                    "boxSizing": "border-box",
                },
            ):
                mui.Typography(
                    className="drag-handle",
                    sx={"padding": "8px 12px", "cursor": "grab", "fontWeight": "bold", "fontSize": "0.95rem"},
                )
                html.iframe(
                    src=build_iframe_url("calendar", bg_cal, txt_cal),
                    style={"width": "100%", "height": "100%", "border": "none", "flex": 1},
                )

            # Physical Activity Widget
            with mui.Card(
                key="activity",
                sx={
                    "display": "flex",
                    "flexDirection": "column",
                    "backgroundColor": bg_act,
                    "color": txt_act,
                    "borderRadius": "8px",
                    "boxShadow": 3,
                    "height": "100%",
                    "minHeight": "400px",
                    "padding": "6px",
                    "boxSizing": "border-box",
                },
            ):
                mui.Typography(
                    className="drag-handle",
                    sx={"padding": "8px 12px", "cursor": "grab", "fontWeight": "bold", "fontSize": "0.95rem"},
                )
                html.iframe(
                    src=build_iframe_url("activity", bg_act, txt_act),
                    style={"width": "100%", "height": "100%", "border": "none", "flex": 1},
                )

            # Meal Tracker Widget
            with mui.Card(
                key="meal",
                sx={
                    "display": "flex",
                    "flexDirection": "column",
                    "backgroundColor": bg_meal,
                    "color": txt_meal,
                    "borderRadius": "8px",
                    "boxShadow": 3,
                    "height": "100%",
                    "minHeight": "400px",
                    "overflow": "hidden",
                    "padding": "6px",
                    "boxSizing": "border-box",
                },
            ):
                mui.Typography(
                    className="drag-handle",
                    sx={"padding": "8px 12px", "cursor": "grab", "fontWeight": "bold", "fontSize": "0.95rem"},
                )
                html.iframe(
                    src=build_iframe_url("meal", bg_meal, txt_meal),
                    style={"width": "100%", "height": "100%", "border": "none", "flex": 1},
                )

            # Decision Assistant Widget
            with mui.Card(
                key="foods",
                sx={
                    "display": "flex",
                    "flexDirection": "column",
                    "backgroundColor": bg_foods,
                    "color": txt_foods,
                    "borderRadius": "8px",
                    "boxShadow": 3,
                    "height": "100%",
                    "minHeight": "400px",
                    "overflow": "hidden",
                    "padding": "6px",
                    "boxSizing": "border-box",
                },
            ):
                mui.Typography(
                    className="drag-handle",
                    sx={"padding": "8px 12px", "cursor": "grab", "fontWeight": "bold", "fontSize": "0.95rem"},
                )
                html.iframe(
                    src=build_iframe_url("foods", bg_foods, txt_foods),
                    style={"width": "100%", "height": "100%", "border": "none", "flex": 1},
                )

elif selected_tab == "Safe Food Registry":
    sfl.render_safe_food_tracker()

elif selected_tab == "Settings":
    st.subheader("⚙️ Global Settings & Data Management")
    st.write("Manage app settings, saved preferences, and JSON data files.")

    if st.button("Reset Dashboard Layout to Default (2x2 Grid)"):
        st.session_state["active_layout"] = DEFAULT_LAYOUT
        settings["layout"] = DEFAULT_LAYOUT
        save_settings(settings)
        st.success("Layout reset to full 2x2 grid! Reloading...")
        st.rerun()

    if st.button("🧹 Purge Duplicate/Past Calendar Sync Events"):
        events = cal.load_events()
        today_str = datetime.now().strftime("%Y-%m-%d")

        cleaned_events = []
        seen = set()
        for e in events:
            eid = e.get("id")
            if eid and eid in seen:
                continue
            if eid:
                seen.add(eid)
            cleaned_events.append(e)

        cal.save_events(cleaned_events)
        st.success("Calendar cleaned up!")
        st.rerun()