"""PawPal+ Streamlit UI — connected to pawpal_system logic layer."""

from datetime import date, time

import streamlit as st

from pawpal_system import DailyPlan, Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}


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


init_session()
owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")
st.caption("Pet care planning — logic from `pawpal_system.py`, state in `st.session_state`.")

with st.expander("About this app", expanded=False):
    st.markdown(
        """
**PawPal+** tracks pets and care tasks, then builds a daily schedule from your
time budget and task priorities. Data persists in **`st.session_state.owner`**
while you use the app.
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
        [{"Name": p.name, "Species": p.species, "Breed": p.breed or "—", "Tasks": len(p.list_tasks())} for p in pets]
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

    if st.button("Add task"):
        task = Task(
            pet_id=selected_pet.pet_id,
            title=task_title.strip() or "Untitled task",
            category=category,
            duration_minutes=int(duration),
            priority=PRIORITY_MAP[priority],
            preferred_time=preferred,
        )
        selected_pet.add_task(task)
        st.session_state.owner = owner
        st.success(f"Task **{task.title}** added for {selected_pet.name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.markdown("**All tasks (all pets)**")
        rows = []
        for t in all_tasks:
            rows.append(
                {
                    "Pet": owner.pet_name_for(t.pet_id),
                    "Title": t.title,
                    "Category": t.category,
                    "Minutes": t.duration_minutes,
                    "Priority": priority_label(t.priority),
                    "Done": t.completed,
                }
            )
        st.table(rows)

st.divider()
st.subheader("Build schedule")
st.caption("Calls `Scheduler.schedule_day(owner, …)` using `owner.get_all_tasks()`.")

if st.button("Generate schedule"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler()
        plan = scheduler.schedule_day(owner, date.today())
        st.session_state.last_plan = plan
        st.session_state.owner = owner

plan: DailyPlan | None = st.session_state.last_plan
if plan:
    st.markdown(f"### Plan for **{owner.name}** — {plan.plan_date.isoformat()}")
    if plan.items:
        for item in plan.items:
            pet = owner.pet_name_for(item.task.pet_id)
            st.markdown(
                f"- **{item.start_time.strftime('%H:%M')}–{item.end_time.strftime('%H:%M')}** "
                f"· {pet}: **{item.task.title}** ({item.task.duration_minutes} min, "
                f"priority {priority_label(item.task.priority)})  \n"
                f"  _{item.reason}_"
            )
    else:
        st.info("No tasks scheduled (all complete or none added).")

    if plan.deferred_tasks:
        st.markdown("**Deferred**")
        for task in plan.deferred_tasks:
            st.markdown(
                f"- {owner.pet_name_for(task.pet_id)}: {task.title} "
                f"({task.duration_minutes} min)"
            )
