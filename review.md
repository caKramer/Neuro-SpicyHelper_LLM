# Code Review: Neuro-SpicyHelper

**Scope:** all of `neuro-spicy-app/`: `app.py`, the tracker modules, `calendar_component.py`, `dashboard_component.py`, `safe_food_library.py`, `setup_model.sh`, `model/`. Reviewed on the `jason` branch at commit `0667e9b`.

**How findings were checked:** **Confirmed** means reproduced, either by running the code on a scratch copy of the app or by inspecting the data files. **From code** means the cause is directly visible in the code but wasn't exercised by running it.

## Summary

| # | Severity | Issue | Status | Fixed? |
|---|---|---|---|---|
| 1 | High | Filtering the Favorite Foods table, then saving, deletes every food that didn't match the filter | Confirmed | ✅ |
| 2 | High | Deleting a calendar event deletes every event with the same title | Confirmed | ✅ |
| 3 | High | Medications never appear on the calendar | Confirmed | ✅ |
| 11 | High | **Open Shopping List** crashes: `load_shopping_list` / `save_shopping_list` don't exist | Confirmed | ✅ |
| 4 | Medium | "Taken" status for medications never resets, so yesterday's doses show as taken today | Confirmed | ✅ |
| 5 | Medium | Hydration count and spoons never reset at the start of a new day | Confirmed | ✅ |
| 6 | Medium | Deleted synced calendar events come back within seconds | Confirmed | ✅ |
| 7 | Medium | JSON files can be wiped if a write and a read overlap | From code (timing-dependent) | ✅ |
| 8 | Low | Assorted UI and consistency issues | From code | — |
| 9 | Low | Dead code and unused dependencies | From code | — |
| 10 | Low | `model/README.md` says the setup script patches the config; it doesn't | From code | — |

Every fix marked ✅ has a regression test that fails on the pre-fix code and passes after it (see "Fixes applied" at the end).
---

## High

### 1. Saving a filtered Favorite Foods table deletes the hidden foods
`safe_food_library.py:140-227`

When the search box has text, `display_df` holds only the matching rows. `st.data_editor` edits that subset, and **💾 Save Table Changes** writes `edited_df` to `safe_foods.json`, replacing the whole registry with the visible rows.

**Example:** type "yogurt", fix a typo in one row, click Save. Every non-yogurt food is gone permanently.

**Fix:** always edit the full table and filter some other way, or merge the edited rows back into the full list by `id` before saving.

### 2. Deleting one calendar event deletes all events with the same title
`calendar_component.py:331-336` (delete), `319-325` (update)

```python
e.get("id") != event_id and e.get("title") != event_data.get("title")
```

An event is kept only if it has a different id **and** a different title. So every event that shares the deleted one's title is removed too. Synced titles repeat a lot ("🍽️ Drink: Glass of Water", recurring appointments), so this will hit real data.

**Reproduced:** with two "Doctor" events (ids `a` and `b`) and one "Gym" event, deleting `a` left only "Gym".

The update loop has the mirror-image problem: it matches `id == event_id or title == title`, so it can edit an earlier event that has the same title instead of the one clicked.

**Fix:** match on `id` only; every event already gets an id.

### 11. Open Shopping List crashes
`app.py:601-623`, `safe_food_library.py`

The shopping list dialog calls `sfl.load_shopping_list()` and `sfl.save_shopping_list()`, but neither function exists, so opening it raises `AttributeError: module 'safe_food_library' has no attribute 'load_shopping_list'`. Found while fixing the findings above.

**Fix:** add both functions to `safe_food_library.py`, reading and writing `shopping_list.json` (the `SHOPPING_FILE` constant was already defined).

### 3. Medications never sync to the calendar
`medication_tracker.py:55-61`, `calendar_component.py:116-121`

New medication entries are saved without a date (`name`, `dosage`, `time`, `taken`, `logged_at_time`). `_extract_item_date_and_time` returns `None` for the date, and the sync skips anything whose date isn't today. So medication events are never created.

**Confirmed:** both entries in `medication_log.json` have no date field, and `calendar_events.json` contains 0 `med_` events.

**Fix:** in `log_medication_taken`, also save `date_str` and `timestamp`.

---

## Medium

### 4. Medication "taken" status never resets
`medication_tracker.py:27-35, 72-99`

`taken` is a single boolean stored per medication, with no date attached, and nothing resets it. A dose marked taken yesterday still shows "Taken at 8:05 AM" today. Someone checking whether they took today's dose would get the wrong answer. That's the core job of this feature, and it matters especially for this app's audience.

**Fix:** store which date the dose was taken (for example a `taken_on` date field) and treat it as taken only when that date is today. A history of doses taken would also fix #3.

### 5. Hydration and spoons don't reset at a new day
`app.py:140-154`, `capacity_state.json`

When the date changes, today's drink count drops to 0. The `elif` branch then resets `synced_drink_count`, but `water_count` keeps yesterday's value. Spoons have no daily reset either.

**Reproduced:** with state `water_count=5, synced_drink_count=5`, five drinks logged yesterday and none today, the dashboard showed 5 cups and 4 spoons.

**Fix:** store the date in `capacity_state.json` and reset both counts when it isn't today.

### 6. Deleted synced calendar events come back
`app.py:157-158`, `calendar_component.py:98-234`

`sync_end_of_day_summary_to_calendar()` runs at the top of every script run. The main page refreshes every 3 s and the meal tile every 2 s, so it runs constantly. When a user deletes a synced meal, med or activity event, its id is no longer in `existing_ids`, so the next sync adds it back. Edits to synced events survive, but only because the id stays the same.

**Fix:** keep a list of deleted synced-event ids and skip those during sync. Or only sync when the user clicks 🔄.

### 7. Overlapping file reads and writes can wipe JSON files
All `load_*` / `save_*` helpers

Saves use `open(path, "w")`, which empties the file before writing the new contents. The dashboard runs several Streamlit sessions at once (the main page plus four iframe tiles), each refreshing every 2-3 s. A session that reads a file mid-write sees an empty or partial file, and the loaders turn the resulting `JSONDecodeError` into `[]`.

If that empty result then gets saved, the whole file is lost. For example, `log_meal_entry` loads, appends and saves, and the calendar sync saves after adding events. The window is small but it repeats constantly.

**Fix:** write to a temporary file and `os.replace()` it over the original, which swaps it in all at once. Also, don't save after a load that failed to parse.

---

## Low

### 8. UI and consistency issues
- **Hydration display:** `app.py:558` shows "/ 12 Cups", but the slider and auto-sync cap at 16 (`app.py:565`, `app.py:148`).
- **Texture options don't match:** the add form offers "Other", but the table editor offers "Any" instead (`safe_food_library.py:93` vs `184`). A food saved with texture "Other" isn't a valid choice in the table's dropdown.
- **Calendar drag-and-drop:** the calendar is set to `editable: True`, but changes from dragging and resizing aren't handled, so moved events snap back (`calendar_component.py:380, 408-417`).
- **Purge button:** Settings' "Purge Duplicate/Past Calendar Sync Events" only removes duplicate ids. It doesn't remove past or synced events (`app.py:839-853`).
- **Task Breakdown with no input:** it silently sends "Clean my desk space" (`app.py:361`). Disabling the button or showing a prompt would be clearer.
- **Model reload delay:** `keep_alive: 0` (`app.py:293`) unloads the model after every request, so each click waits for a reload. With the 30 s timeout, a slow machine may fail on the first request. Consider `keep_alive: "5m"`.
- **Raw HTML from URL parameters:** `bg` and `txt` from the URL are inserted into raw HTML/CSS (`app.py:215-230`, `calendar_component.py:347`). This matters little for a local app, but validating them as hex colors closes off HTML injection.

### 9. Dead code and unused dependencies
- **`dashboard_component.py`:** only `init_dashboard_layout()` is used, and its `dashboard_layout` session key is never read. `render_dashboard`, `save_dashboard_layout` and `load_dashboard_layout` are unused.
- **Unreachable menu branch:** `app.py:825` handles a "Safe Food Registry" tab that isn't in the menu options.
- **Unused aliases:** `render_medication_dialog` (`medication_tracker.py:105`) is unused. `sync_end_of_day_summary_to_calendar` is just an alias.
- **`requirements.txt`:** `torch` and `transformers` are never imported but add several GB to installs.

### 10. Model README doesn't match the setup script
`neuro-spicy-app/model/README.md:30`

The README says `setup_model.sh` "downloads any missing files, applies the config patch". The script now downloads only `model.safetensors` and relies on the already-patched `config.json` being committed. If someone replaces `config.json` with a fresh copy from Hugging Face, the script imports it unpatched, and long prompts produce garbage again.

**Fix:** correct the wording, or have the script check for `rope_scaling` and stop or re-apply the patch.

---

## Checked and fine
- **Log-button change:** limiting the "🍱 Log …" buttons to `selected_pill == "Food Options"` (`app.py:430-434`) is safe. Switching modes clears `assistant_response`, so an old food answer can't appear under another mode.
- **`model/config.json`:** it only adds `rope_theta` and `rope_scaling`, with the same values as `rope_parameters`.
- **`.gitignore`:** it excludes the 6.4 GB weights and the HF download cache.
- **`Modelfile`:** its relative `FROM .` works because `setup_model.sh` changes into `model/` first.
- **Stop tokens:** the Modelfile and `app.py` stop on the same tokens.
- **Smoke tests:** all dashboard tiles render without exceptions, and all four assistant modes return coherent responses from `llama3.2-3b-ft`.

---

## Fixes applied

Findings 1-7 and 11 are fixed in the working tree (not yet committed).

| # | Change |
|---|---|
| 1 | `safe_food_library.py`: Save merges the edited rows back into the full registry by `id`. Hidden rows are kept, rows deleted in the editor are removed, and new rows are appended. New rows also get an id when pandas gives them `NaN` (the old `not rec["id"]` check missed that). |
| 2 | `calendar_component.py`: Update and Delete match on `id` only. |
| 3, 4 | `medication_tracker.py`: Mark Taken also saves `date_str` and `timestamp`. A new `is_taken_today()` decides Taken vs Pending, so the status resets each day. The calendar sync now has a date to work with, and it no longer defaults missing `taken` to `True`. |
| 5 | `app.py`: `capacity_state.json` now stores a `date`. A stale file loads as a fresh day (12 spoons, 0 cups), and sessions that stay open past midnight reload and save. Files written before this change, with no date, are treated as today's, so nobody loses today's values on upgrade. |
| 6 | `calendar_component.py`: deleting a synced (`med_`/`meal_`/`act_`) event records its id in `calendar_dismissed_syncs.json`, and the sync skips those ids. |
| 7 | New `json_store.save_json()`: writes to a temp file in the same folder, fsyncs, then `os.replace()`s it over the target. Readers see either the old file or the new one, never an empty or partial one. All modules' save functions use it. |
| 11 | `safe_food_library.py`: added `load_shopping_list()` / `save_shopping_list()`. |

**Verification:**
- **Regression tests:** one per fix, run on a scratch copy of the app with fabricated data. All pass. On the pre-fix code they fail; the run stops at the medication test, because the old code shows yesterday's dose as taken and never offers Mark Taken.
- **Smoke tests:** the full dashboard and all four tiles render without exceptions.
- **Assistant:** all four modes return coherent `llama3.2-3b-ft` responses.
