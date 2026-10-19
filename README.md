# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## Implementation summary (Phase 2)

The backend lives in `pawpal_system.py`:

- **Owner** — stores `daily_minutes_available`, owns **Pet** instances, and exposes **`get_all_tasks()`** so the scheduler sees every pet's tasks.
- **Pet** — profile fields plus **`add_task`** / **`list_tasks`**.
- **Task** — description (`title`), duration, priority, optional **`preferred_time`**, recurrence flags, and **`completed`** with **`mark_complete()`**.
- **Scheduler** — pulls tasks only through **`owner.get_all_tasks()`**, sorts by priority, fits tasks into the owner's time budget, assigns sequential time slots, and returns a **DailyPlan** with deferred tasks and notes.

Run the CLI demo: `python main.py` (see sample output below). Tests: `python -m pytest`.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule — Jordan Lee (2026-10-18)
Time budget: 120 minutes
========================================================
  08:00–08:10  Mochi: Medication (10 min, priority 5)
  08:10–08:40  Biscuit: Morning walk (30 min, priority 3)
  08:40–08:55  Biscuit: Evening feeding (15 min, priority 3)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
python -m pytest tests/test_pawpal.py -v

tests/test_pawpal.py::test_mark_complete_changes_status PASSED
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED
tests/test_pawpal.py::test_scheduler_uses_owner_get_all_tasks PASSED
3 passed
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
