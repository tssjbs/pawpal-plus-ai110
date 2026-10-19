"""CLI demo for PawPal+ — sorting, filtering, conflicts, and recurrence."""

from datetime import date, time

from pawpal_system import Owner, Pet, Scheduler, Task


def format_schedule(owner: Owner, plan) -> str:
    """Render the daily plan as readable terminal text."""
    lines = [
        f"Today's Schedule — {owner.name} ({plan.plan_date.isoformat()})",
        f"Time budget: {owner.daily_minutes_available} minutes",
        "=" * 56,
    ]
    if plan.notes:
        lines.append("Notes / warnings:")
        for note in plan.notes:
            if "deferred" in note.lower() or "Priority" in note:
                continue
            lines.append(f"  ⚠ {note}")
        lines.append("-" * 56)
    if not plan.items:
        lines.append("  (no tasks scheduled)")
    for item in plan.items:
        pet = owner.pet_name_for(item.task.pet_id)
        start = item.start_time.strftime("%H:%M")
        end = item.end_time.strftime("%H:%M")
        lines.append(
            f"  {start}–{end}  {pet}: {item.task.title} "
            f"({item.task.duration_minutes} min, priority {item.task.priority})"
        )
    if plan.deferred_tasks:
        lines.append("-" * 56)
        lines.append("Deferred (over time budget):")
        for task in plan.deferred_tasks:
            pet = owner.pet_name_for(task.pet_id)
            lines.append(f"  • {pet}: {task.title} ({task.duration_minutes} min)")
    return "\n".join(lines)


def main() -> None:
    owner = Owner(name="Jordan Lee", daily_minutes_available=120)
    biscuit = Pet(name="Biscuit", species="dog", breed="Golden Retriever", owner_id=owner.owner_id)
    mochi = Pet(name="Mochi", species="cat", breed="Domestic Shorthair", owner_id=owner.owner_id)
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Tasks added out of preferred-time order on purpose.
    biscuit.add_task(
        Task(
            pet_id=biscuit.pet_id,
            title="Evening feeding",
            category="feeding",
            duration_minutes=15,
            priority=3,
            preferred_time=time(18, 0),
        )
    )
    mochi.add_task(
        Task(
            pet_id=mochi.pet_id,
            title="Medication",
            category="meds",
            duration_minutes=10,
            priority=5,
            preferred_time=time(9, 0),
        )
    )
    biscuit.add_task(
        Task(
            pet_id=biscuit.pet_id,
            title="Morning walk",
            category="walk",
            duration_minutes=30,
            priority=3,
            preferred_time=time(8, 0),
        )
    )
    # Same preferred time — conflict detection should warn.
    mochi.add_task(
        Task(
            pet_id=mochi.pet_id,
            title="Morning play",
            category="enrichment",
            duration_minutes=15,
            priority=2,
            preferred_time=time(9, 0),
        )
    )
    daily_feed = Task(
        pet_id=biscuit.pet_id,
        title="Daily breakfast",
        category="feeding",
        duration_minutes=10,
        priority=4,
        preferred_time=time(7, 30),
        is_recurring=True,
        recurrence_rule="daily",
    )
    biscuit.add_task(daily_feed)

    scheduler = Scheduler()
    all_tasks = owner.get_all_tasks()

    print("=== Sort by preferred time (CLI) ===")
    for t in scheduler.sort_by_time(all_tasks):
        pref = t.preferred_time.strftime("%H:%M") if t.preferred_time else "—"
        print(f"  {pref}  {owner.pet_name_for(t.pet_id)}: {t.title}")

    print("\n=== Filter: Biscuit, not completed ===")
    for t in owner.filter_tasks(pet_name="Biscuit", completed=False):
        print(f"  • {t.title}")

    print("\n=== Generate schedule ===")
    plan = scheduler.schedule_day(owner, date.today())
    print(format_schedule(owner, plan))

    print("\n=== Recurring: complete daily breakfast ===")
    before = len(biscuit.list_tasks())
    spawned = biscuit.mark_task_complete(daily_feed.task_id, date.today())
    after = len(biscuit.list_tasks())
    print(f"  Tasks before: {before}, after: {after}")
    if spawned:
        print(
            f"  Next occurrence: {spawned.title} due {spawned.due_date.isoformat()}"
        )


if __name__ == "__main__":
    main()
