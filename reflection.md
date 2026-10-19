# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

PawPal+ helps a busy owner stay consistent with pet care by tracking routines and turning them into a realistic daily plan. From the README scenario, three core actions the user should be able to perform are:

1. **Set up owner and pet profiles** — register who cares for the pet and basic pet info (name, species, breed) plus how much time the owner has per day.
2. **Add and manage care tasks** — create tasks such as walks, feeding, medications, or grooming with at least duration and priority (and optionally recurrence).
3. **Generate and review today’s plan** — see an ordered schedule for the day that respects time limits and priorities, with short explanations for why tasks were included or left out.

**UML classes and responsibilities**

| Class | Responsibility |
|-------|----------------|
| **Owner** | Holds identity, `daily_minutes_available`, and preferences; owns one or more pets. |
| **Pet** | Holds pet profile data and the list of care tasks for that animal. |
| **Task** | One care action: title, category, duration, priority, recurrence flags; belongs to a pet. |
| **Scheduler** | Algorithm layer: sort by priority, fit tasks into available minutes, detect time conflicts, build a **DailyPlan**, and explain choices. |
| **DailyPlan** | Result object for one pet/day: scheduled items, notes, and tasks deferred when time runs out. |
| **ScheduledItem** | Links a task to a start/end time on the plan plus a `reason` string for the UI. |

Relationships: one Owner has many Pets; one Pet has many Tasks; Scheduler reads Owner constraints and Pet tasks and produces a DailyPlan composed of ScheduledItems.

The Mermaid source for this design is saved as `diagrams/uml_draft.mmd`. Python skeletons live in `pawpal_system.py` (dataclasses for Task, Pet, Owner, DailyPlan, ScheduledItem; a regular class for Scheduler with method stubs).

**b. Design changes**

After reviewing the skeleton against the UML, two small adjustments were made before the first commit:

1. **Explicit `DailyPlan` and `ScheduledItem` types** — The brainstorm centered on Owner, Pet, Task, and Scheduler; adding plan/line-item types avoids passing loose tuples and gives `detect_conflicts` and `explain_plan` a clear structure to work on in Phase 2.
2. **`Task.pet_id` enforced in `Pet.add_task`** — If a task is added with a mismatched `pet_id`, the pet updates it so tasks cannot accidentally float between pets.

The final architecture is captured in **`diagrams/uml_final.mmd`** (updated from the Phase 1 draft to include `get_all_tasks`, `filter_tasks`, recurrence helpers, and the owner-scoped `schedule_day` signature).

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler uses **`Owner.daily_minutes_available`** as a hard cap, **`Task.priority`** (higher number first), and optional **`preferred_time`** as a tie-breaker when sorting. It skips tasks already marked **`completed`**. Priority mattered most because meds and feeding should win over lower-priority enrichment when time is tight; the time budget is the second gate so the plan stays realistic for a busy owner.

**b. Tradeoffs**

When total task duration exceeds the budget, lower-priority tasks move to **`deferred_tasks`** even if they have an early preferred time. That tradeoff is reasonable here because the scenario asks for a feasible daily plan, not an impossible full wish list—the owner sees what fits today and what to roll forward.

For **conflict detection**, PawPal+ uses two lightweight checks instead of a full interval-timeline solver. **`detect_same_time_conflicts`** only warns when two *pending* tasks share the exact same **`preferred_time`** (same HH:MM), and **`detect_conflicts`** on the built plan flags adjacent slots that overlap or share the same **start** time. We do **not** model “busy blocks” where a long task would collide with another task that starts mid-duration unless the sequential schedule places them that way. That keeps the code readable for a class project, but it would miss subtle overlaps if an owner manually pinned many tasks to overlapping windows; a production app might merge intervals or use minute-granularity bitmaps.

---

## 3. AI Collaboration

**a. How you used AI**

AI (Cursor) helped across phases: UML and skeletons (Phase 1), implementing **`pawpal_system.py`** and **`main.py`** (Phase 2), Streamlit **`st.session_state`** wiring (Phase 3), algorithm methods and pytest cases (Phases 4–5), and final README/UML/UI polish (Phase 6). The most effective features were **multi-file edits** (logic + tests together), **terminal-backed verification** (`pytest`, `main.py`), and **focused prompts** with files attached (“use `Owner.get_all_tasks()` only”, “warn don’t crash on conflicts”).

**b. Judgment and verification**

AI initially shaped **`schedule_day`** around a single **Pet** argument; the rubric requires the scheduler to use **`Owner.get_all_tasks()`**, so that signature was changed to **`schedule_day(owner, plan_date)`** only. Another suggestion was a heavier interval-merge conflict engine; I kept **exact preferred-time** and **adjacent-slot** checks for readability and matched them with 14 targeted tests. Verification: **`python main.py`**, **`streamlit run app.py`**, and **`python -m pytest`** after each phase.

**c. AI strategy (Phase 6)**

- **Most effective tools:** codebase search, parallel file reads, and running pytest in the integrated terminal so AI could fix failures in the same turn.
- **Rejected / modified suggestion:** a Streamlit-only task store separate from **`Owner`** — rejected to keep a single source of truth in **`pawpal_system.py`**.
- **Separate chat sessions per phase:** planning (UML), implementation, algorithms, testing, and polish stayed scoped; fewer mixed context bugs and cleaner commit boundaries.
- **Lead architect role:** AI drafts quickly, but I owned requirements (multi-pet entry point, warning-not-crash conflicts, recurrence rules), chose tradeoffs in **`reflection.md` §2b**, and only merged changes after CLI/tests passed.

---

## 4. Testing and Verification

**a. What you tested**

The suite in `tests/test_pawpal.py` checks **happy paths** (add pet/task, schedule across two pets, sort by clock time, filter by pet/status, daily and weekly recurrence, preferred-time conflict warnings) and **edge cases** (owner with zero tasks → empty plan, 30-minute budget deferring a low-priority task, non-recurring completion with no spawn, tasks without preferred time sorting last, future `due_date` hidden until that day). These matter because they mirror real owner mistakes—double-booking the same hour, running out of time, and completing a routine that should reappear tomorrow.

**b. Confidence**

**4/5 stars** for day-to-day use: `python -m pytest` gives 14 green tests on the logic layer. I would add tests next for unknown recurrence rules, many pets with mixed due dates, and Streamlit session behavior (UI is still manual).

---

## 5. Reflection

**a. What went well**

The split between **`pawpal_system.py`** (pure logic) and **`app.py`** (presentation) made Phase 4 algorithms testable without touching Streamlit. Surfacing **`detect_same_time_conflicts`** in the UI as an upfront **`st.warning`** gives owners actionable feedback before they generate a plan.

**b. What you would improve**

Next iteration: edit/delete tasks in the UI, persist data to a file or database, and stretch tests to cover unknown recurrence rules and larger schedules. I would also export **`uml_final.mmd`** to PNG in CI for the README.

**c. Key takeaway**

Powerful AI assistants speed up implementation, but **design contracts** (who owns tasks — Owner vs Pet, what “conflict” means, how recurrence spawns) must stay human-owned. Short verification loops (pytest + one CLI script) are the difference between demo-ware and a system you can explain to a grader or teammate.
