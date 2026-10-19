# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app plus Python logic layer that helps a busy pet owner plan daily care across one or more pets — with sorting, filtering, conflict warnings, and recurring routines.

## Features

- **Owner & pet profiles** — name, species, breed, and a shared **daily time budget** (minutes).
- **Task management** — walks, feeding, meds, and more with duration, priority, optional **preferred time**, and **daily/weekly recurrence**.
- **Multi-pet scheduling** — `Scheduler.schedule_day(owner, date)` loads every task via **`Owner.get_all_tasks()`**.
- **Sorting by time** — `Scheduler.sort_by_time()` orders tasks by preferred clock time (shown in the UI task table).
- **Sorting for the plan** — `Scheduler.sort_by_priority()` picks what fits today when time is limited.
- **Filtering** — `Owner.filter_tasks(pet_name=…, completed=…)` in the Streamlit task browser.
- **Conflict warnings** — `Scheduler.detect_same_time_conflicts()` alerts when two open tasks share the same preferred HH:MM; `detect_conflicts()` flags overlaps on the built timeline. Warnings appear in **`st.warning`** before and after generating a plan.
- **Recurring tasks** — completing a daily/weekly task via **`Pet.mark_task_complete()`** spawns the next occurrence with an updated **`due_date`**.
- **Automated tests** — 14 pytest cases for models, algorithms, and edge cases (see [Testing PawPal+](#-testing-pawpal)).

## Architecture

Final class diagram (Mermaid): **`diagrams/uml_final.mmd`** (Phase 1 draft: `diagrams/uml_draft.mmd`).

Core code: **`pawpal_system.py`** · UI: **`app.py`** · CLI demo: **`main.py`**.

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py        # UI
python main.py              # CLI demo (sorting, conflicts, recurrence)
python -m pytest            # tests
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting by clock time | `Scheduler.sort_by_time()` | Earliest `preferred_time` first; no preferred time → last. |
| Task sorting for the plan | `Scheduler.sort_by_priority()` | Drives `schedule_day`: higher priority, then preferred time. |
| Filtering | `Owner.filter_tasks(pet_name=…, completed=…)` | Case-insensitive pet name. |
| Preferred-time conflicts | `Scheduler.detect_same_time_conflicts()` | Warning strings; scheduling still runs. |
| Schedule slot conflicts | `Scheduler.detect_conflicts()` | Overlap / same start on generated slots. |
| Recurring tasks | `Task.create_next_occurrence()`, `Pet.mark_task_complete()` | Daily +1 day, weekly +7 days (`timedelta`). |

## 📸 Demo Walkthrough

Follow this workflow in **Streamlit** (`streamlit run app.py`):

1. **Set owner** — Enter your name and daily minutes (e.g. 120), click **Save owner settings**.
2. **Add pets** — e.g. Biscuit (dog) and Mochi (cat). They appear in the pets table.
3. **Add tasks** — Pick a pet, set title, duration, priority, optional preferred time, and recurrence (daily/weekly). If two tasks share the same preferred time, a yellow **Heads up** banner lists the conflict.
4. **Browse tasks** — Use **Filter by pet** / **Filter by status**; the table is sorted with **`sort_by_time`**. Mark a recurring task **complete** to see the next due date.
5. **Generate schedule** — Click **Generate schedule**. Review **Scheduling conflicts** (if any), the **Today's timeline** table, **Deferred** tasks when over budget, and **Why these tasks?** explanations.

**Scheduler behaviors you should see:** priority-based packing into your time budget, sequential time slots from 8:00, preferred-time conflict warnings, and deferred lower-priority work when minutes run out.

### Sample CLI output (`python main.py`)

```
=== Sort by preferred time (CLI) ===
  07:30  Biscuit: Daily breakfast
  08:00  Biscuit: Morning walk
  09:00  Mochi: Medication
  09:00  Mochi: Morning play
  18:00  Biscuit: Evening feeding

=== Generate schedule ===
Today's Schedule — Jordan Lee (2026-10-18)
Time budget: 120 minutes
========================================================
Notes / warnings:
  ⚠ Preferred-time conflict at 09:00 — Mochi: Medication; Mochi: Morning play
--------------------------------------------------------
  08:00–08:10  Mochi: Medication (10 min, priority 5)
  08:10–08:20  Biscuit: Daily breakfast (10 min, priority 4)
  ...
```

## 🧪 Testing PawPal+

Run the full suite from the project root (with your virtualenv active):

```bash
python -m pytest
```

Verbose names (useful when debugging a single failure):

```bash
python -m pytest tests/test_pawpal.py -v
```

Optional coverage:

```bash
python -m pytest --cov=pawpal_system
```

### What the tests cover

| Area | Examples |
|------|----------|
| **Core models** | `mark_complete`, `add_task`, multi-pet `get_all_tasks()` scheduling |
| **Sorting** | `sort_by_time()` chronological order; tasks without preferred time sort last |
| **Filtering** | `filter_tasks()` by pet name and completion status |
| **Recurrence** | Daily (+1 day) and weekly (+7 days) spawn after `mark_task_complete`; one-off tasks do not spawn |
| **Conflicts** | `detect_same_time_conflicts()` and conflict strings on `DailyPlan.notes` |
| **Edge cases** | Empty schedule (no tasks), time budget deferral, future `due_date` excluded until due |

### Sample test output

```
$ python -m pytest
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: ai110-module2show-pawpal-starter
collected 14 items

tests/test_pawpal.py ..............                                      [100%]

============================== 14 passed in 0.04s ==============================
```

**Confidence level:** ★★★★☆ (4/5) — core scheduling, algorithms, and recurrence paths are covered by automated tests; not yet stress-tested for large task lists or every recurrence rule variant.

## Optional extensions

| Challenge | Status | What we added |
|-----------|--------|----------------|
| **1 — Advanced algorithm** | Done | `Scheduler.next_available_slot()` — earliest gap for a new task (CLI + Streamlit info banner). |
| **2 — Data persistence** | Done | `save_to_json()` / `load_from_json()` in `pawpal_system.py` → `data.json`. Streamlit sidebar **Save** / **Load**; `main.py` auto-saves after demo. |
| **3 — Priority scheduling** | Already in core | `sort_by_priority()` + numeric priority (1 / 3 / 5 → Low / Medium / High). CLI table **Priority-first schedule order**. |
| **4 — CLI formatting** | Done | [`tabulate`](https://github.com/astanin/python-tabulate) tables, category emojis (`main.py`), `Task.priority_label()`. |
| **5 — Multi-model comparison** | Template | See **`ai_interactions.md`** → Prompt Comparison (fill in your second model run). |

### Persistence workflow

1. Use the app or `python main.py` to create pets and tasks.
2. **Streamlit:** sidebar → **Save to data.json** (writes project-root `data.json`).
3. Restart Streamlit → **Load from data.json** to restore `st.session_state.owner`.
4. Serialization uses plain dicts (ISO strings for dates/times) — see `_task_to_dict` in `pawpal_system.py`. `data.json` is gitignored so personal pet data is not committed.

**Modified files:** `pawpal_system.py`, `app.py`, `main.py`, `requirements.txt`, `.gitignore`, `ai_interactions.md`.

### CLI — priority-first + tabulated schedule

After `pip install -r requirements.txt` and `python main.py`, you should see priority-ordered rows and a rounded schedule table, for example:

```
=== Priority-first schedule order (sort_by_priority) ===
Pet      Task              Priority    Preferred
-----  ----------------  ----------  -----------
Mochi  Medication        High        09:00
...
Next available 20-minute slot today: 09:20
(Saved owner to data.json)
```

Agent workflow and prompt comparison notes: **`ai_interactions.md`**.
