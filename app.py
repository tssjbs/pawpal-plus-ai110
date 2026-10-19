"""PawPal+ Streamlit UI — connected to pawpal_system logic layer."""

from datetime import date, time

import streamlit as st

from pathlib import Path

from pawpal_system import (
    DailyPlan,
    Owner,
    Pet,
    Scheduler,
    Task,
    load_from_json,
    save_to_json,
)

DATA_FILE = Path("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}
RECURRENCE_OPTIONS = ["none", "daily", "weekly"]


def init_session() -> None:
    """Create or restore the Owner in session memory across reruns."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name="Jordan", daily_minutes_available=120)
    if "last_plan" not in st.session_state:
        st.session_state.last_plan = None


def priority_label(value: int) -> str:
    for label, num in PRIORITY_MAP.items():
        if num == value:
            return label
    return str(value)


def task_table_rows(owner: Owner, tasks: list[Task]) -> list[dict]:
    rows = []
    for t in tasks:
        pref = t.preferred_time.strftime("%H:%M") if t.preferred_time else "—"
        due = t.due_date.isoformat() if t.due_date else "—"
        recur = t.recurrence_rule if t.is_recurring else "—"
        rows.append(
            {
                "Pet": owner.pet_name_for(t.pet_id),
                "Title": t.title,
                "Preferred": pref,
                "Minutes": t.duration_minutes,
                "Priority": priority_label(t.priority),
                "Recurring": recur,
                "Due": due,
                "Done": t.completed,
            }
        )
    return rows


def split_plan_notes(notes: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Split plan notes into warnings, explanations, and other lines."""
    warnings: list[str] = []
    explanations: list[str] = []
    for note in notes:
        lower = note.lower()
        if "conflict" in lower or "overlap" in lower or "same start" in lower:
            warnings.append(note)
        elif "deferred" in lower or "priority" in lower:
            explanations.append(note)
        else:
            explanations.append(note)
    return warnings, explanations, []


init_session()
owner: Owner = st.session_state.owner
scheduler = Scheduler()

st.title("🐾 PawPal+")
st.caption("Smart scheduling from `pawpal_system.py` · state in `st.session_state.owner`")

with st.sidebar:
    st.markdown("**Data persistence**")
    st.caption(f"File: `{DATA_FILE}`")
    if st.button("Save to data.json"):
        save_to_json(owner, DATA_FILE)
        st.success("Saved pets and tasks to disk.")
    if st.button("Load from data.json"):
        if not DATA_FILE.exists():
            st.error("No data.json yet — save first or run `python main.py`.")
        else:
            st.session_state.owner = load_from_json(DATA_FILE)
            st.session_state.last_plan = None
            st.success("Loaded from data.json. Refreshing…")
            st.rerun()

with st.expander("About this app", expanded=False):
    st.markdown(
        """
**PawPal+** tracks pets and care tasks, sorts and filters them, detects preferred-time
conflicts, and builds a daily plan from your time budget and priorities. Completing a
recurring task automatically adds the next occurrence.
"""
    )

st.subheader("Owner profile")
col_o1, col_o2 = st.columns(2)
with col_o1:
    owner_name = st.text_input("Owner name", value=owner.name, key="owner_name_input")
with col_o2:
    minutes = st.number_input(
        "Daily time budget (minutes)",
        min_value=15,
        max_value=480,
        value=int(owner.daily_minutes_available),
        step=15,
    )
if st.button("Save owner settings"):
    owner.name = owner_name.strip() or owner.name
    owner.daily_minutes_available = int(minutes)
    st.session_state.owner = owner
    st.success("Owner settings saved.")

st.divider()
st.subheader("Add a pet")

pet_name = st.text_input("Pet name", value="", placeholder="e.g. Biscuit")
species = st.selectbox("Species", ["dog", "cat", "other"], key="species_select")
breed = st.text_input("Breed (optional)", value="")

if st.button("Add pet"):
    if not pet_name.strip():
        st.error("Enter a pet name.")
    else:
        pet = Pet(
            name=pet_name.strip(),
            species=species,
            breed=breed.strip(),
            owner_id=owner.owner_id,
        )
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.success(f"Added pet **{pet.name}** ({pet.species}).")

pets = owner.get_pets()
if pets:
    st.markdown("**Your pets**")
    st.table(
        [
            {
                "Name": p.name,
                "Species": p.species,
                "Breed": p.breed or "—",
                "Tasks": len(p.list_tasks()),
            }
            for p in pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()
st.subheader("Add a task")

if not pets:
    st.warning("Add at least one pet before scheduling tasks.")
else:
    pet_labels = {f"{p.name} ({p.species})": p for p in pets}
    selected_label = st.selectbox("Pet", list(pet_labels.keys()))
    selected_pet = pet_labels[selected_label]

    c1, c2, c3 = st.columns(3)
    with c1:
        task_title = st.text_input("Task title", value="Morning walk")
    with c2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with c3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    category = st.selectbox(
        "Category",
        ["walk", "feeding", "meds", "grooming", "enrichment", "other"],
    )
    use_preferred = st.checkbox("Set preferred time", value=False)
    preferred = None
    if use_preferred:
        preferred = st.time_input("Preferred time", value=time(8, 0))

    recurrence = st.selectbox("Recurrence", RECURRENCE_OPTIONS, index=0)

    if st.button("Add task"):
        is_recurring = recurrence != "none"
        task = Task(
            pet_id=selected_pet.pet_id,
            title=task_title.strip() or "Untitled task",
            category=category,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority],
            preferred_time=preferred,
            is_recurring=is_recurring,
            recurrence_rule=recurrence if is_recurring else "daily",
        )
        selected_pet.add_task(task)
        st.session_state.owner = owner
        st.success(f"Task **{task.title}** added for {selected_pet.name}.")

    pending = [t for t in owner.get_all_tasks() if not t.completed]
    pre_conflicts = scheduler.detect_same_time_conflicts(pending, owner)
    if pre_conflicts:
        st.warning(
            "**Heads up — overlapping preferred times**  \n"
            + "  \n".join(f"• {w}" for w in pre_conflicts)
            + "  \n\nAdjust preferred times or priorities before generating today's plan."
        )

    st.markdown("**Browse tasks**")
    f1, f2 = st.columns(2)
    with f1:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["All pets"] + [p.name for p in pets],
            key="filter_pet",
        )
    with f2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Open only", "Completed only"],
            key="filter_status",
        )

    filtered = owner.get_all_tasks()
    if filter_pet != "All pets":
        filtered = owner.filter_tasks(pet_name=filter_pet)
    if filter_status == "Open only":
        filtered = [t for t in filtered if not t.completed]
    elif filter_status == "Completed only":
        filtered = [t for t in filtered if t.completed]

    if filtered:
        st.caption("Sorted by preferred time (`Scheduler.sort_by_time`)")
        sorted_tasks = scheduler.sort_by_time(filtered)
        st.table(task_table_rows(owner, sorted_tasks))
    else:
        st.info("No tasks match these filters.")

    open_tasks = [t for t in owner.get_all_tasks() if not t.completed]
    if open_tasks:
        st.markdown("**Mark a task complete**")
        by_pet: dict[str, Pet] = {p.pet_id: p for p in pets}
        options = {
            f"{owner.pet_name_for(t.pet_id)} · {t.title}": t for t in open_tasks
        }
        pick = st.selectbox("Task", list(options.keys()), key="complete_pick")
        if st.button("Mark complete"):
            task = options[pick]
            pet = by_pet.get(task.pet_id)
            if pet:
                spawned = pet.mark_task_complete(task.task_id, date.today())
                st.session_state.owner = owner
                if spawned:
                    st.success(
                        f"Completed **{task.title}**. Next **{spawned.recurrence_rule}** "
                        f"occurrence due **{spawned.due_date.isoformat()}**."
                    )
                else:
                    st.success(f"Completed **{task.title}**.")

st.divider()
st.subheader("Build schedule")
st.caption("`Scheduler.schedule_day(owner, today)` — priority order, time budget, conflict notes.")

if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task first.")
    else:
        plan = scheduler.schedule_day(owner, date.today())
        st.session_state.last_plan = plan
        st.session_state.owner = owner
        st.success("Schedule generated.")

plan: DailyPlan | None = st.session_state.last_plan
if plan:
    st.markdown(f"### Plan for **{owner.name}** — {plan.plan_date.isoformat()}")

    warn_notes, explain_notes, _ = split_plan_notes(plan.notes)
    if warn_notes:
        st.warning(
            "**Scheduling conflicts to review**  \n"
            + "  \n".join(f"• {n}" for n in warn_notes)
        )

    if plan.items:
        st.markdown("**Today's timeline** (sequential slots from 8:00)")
        timeline = []
        for item in plan.items:
            pet = owner.pet_name_for(item.task.pet_id)
            timeline.append(
                {
                    "Start": item.start_time.strftime("%H:%M"),
                    "End": item.end_time.strftime("%H:%M"),
                    "Pet": pet,
                    "Task": item.task.title,
                    "Min": item.task.duration_minutes,
                    "Priority": priority_label(item.task.priority),
                }
            )
        st.table(timeline)
    else:
        st.info("No tasks scheduled (all complete, not due today, or none added).")

    if plan.deferred_tasks:
        st.markdown("**Deferred** (over daily time budget)")
        st.table(
            [
                {
                    "Pet": owner.pet_name_for(t.pet_id),
                    "Task": t.title,
                    "Minutes": t.duration_minutes,
                    "Priority": priority_label(t.priority),
                }
                for t in plan.deferred_tasks
            ]
        )

    if explain_notes:
        with st.expander("Why these tasks?", expanded=False):
            for line in explain_notes:
                st.markdown(f"- {line}")

    gap = scheduler.next_available_slot(plan, duration_minutes=20)
    if gap:
        st.info(
            f"**Next open slot:** a **20-minute** task could start at **{gap.strftime('%H:%M')}** "
            f"(`Scheduler.next_available_slot`)."
        )
    else:
        st.caption("No 20-minute gap before 22:00 on today's timeline.")
