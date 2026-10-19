# PawPal+ — AI interaction log (optional extensions)

This file documents how AI (Cursor / Composer) was used for stretch goals beyond the base module.

---

## Agent Workflow — Extensions session

| Item | Detail |
|------|--------|
| **Goal** | Add persistence, next-available-slot scheduling, and polished CLI output. |
| **Files modified** | `pawpal_system.py`, `main.py`, `app.py`, `tests/test_pawpal.py`, `requirements.txt`, `README.md`, `ai_interactions.md` |
| **Prompt / request** | “Implement optional extensions: JSON persistence, third algorithm (`next_available_slot`), tabulate + emojis in CLI, document in README and `ai_interactions.md`.” |
| **Agent completed** | Dict-based `save_to_json` / `load_from_json`, `Scheduler.next_available_slot`, sidebar Save/Load in Streamlit, `tabulate` tables and category emojis in `main.py`, two new pytest cases. |
| **Manual corrections** | *(You)* Run Streamlit and confirm Load replaces session owner; *(You)* decide whether `data.json` is gitignored or committed as a sample. |

### Persistence design (why not marshmallow?)

Tasks store `time` and `date` objects. The agent used **explicit dict helpers** (`_task_to_dict` / `_task_from_dict`) with ISO strings so the stdlib `json` module works without extra dependencies. Marshmallow would be reasonable for a larger API; for one Owner graph, custom conversion stayed easier to read in a course repo.

---

## Prompt Comparison — Weekly recurrence logic

**Task:** When a weekly task is marked complete, create the next occurrence with the correct `due_date`.

| | **Strategy 1 — Cursor Composer (build prompt)** | **Strategy 2 — Architecture-only prompt (second chat)** |
|---|---------------------------------------------------|-----------------------------------------------------------|
| **Model / tool** | Cursor Composer (agent mode, repo context) | Same project, new chat: “Design a `RecurrenceEngine` service class” (simulates a second model focused on patterns) |
| **Useful output** | `Task.create_next_occurrence()` + `Pet.mark_task_complete()` with `timedelta` (+1 / +7 days), wired to pytest. | Clear boundary for future rules (monthly, holidays) and test doubles. |
| **Problems** | Recurrence logic stays on `Task`; could grow large. | Overkill for two rules; extra files and indirection for a 20-point scope. |
| **Final decision** | **Shipped Strategy 1** in `pawpal_system.py`; documented Strategy 2 in this file only. |

**Manual correction:** Ensured spawned tasks set `due_date` so `is_due_on()` excludes them until the next day (see `test_future_due_recurring_not_scheduled_until_due`).

---

## Your turn (interactive checklist)

Work through these with your AI assistant or on your own:

- [ ] Run `python main.py` — confirm table output and `(Saved owner to data.json)`.
- [ ] Run `streamlit run app.py` — add a pet, **Save to data.json**, restart Streamlit, **Load from data.json**.
- [ ] Confirm **Next open slot** appears after generating a schedule.
- [ ] Run `python -m pytest` — expect **16 passed**.
- [ ] Fill in **Manual corrections** above if you changed anything the agent suggested.
