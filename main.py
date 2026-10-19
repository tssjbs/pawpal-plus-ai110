"""CLI demo for PawPal+ — sorting, filtering, conflicts, recurrence, and tables."""

from datetime import date, time
from pathlib import Path

from tabulate import tabulate

from pawpal_system import Owner, Pet, Scheduler, Task, load_from_json, save_to_json

CATEGORY_EMOJI = {
    "walk": "🦮",
    "feeding": "🍽️",
    "meds": "💊",
    "grooming": "✂️",
    "enrichment": "🎾",
    "other": "📋",
}


def status_emoji(completed: bool) -> str:
    return "✅" if completed else "⏳"


def format_schedule_table(owner: Owner, plan) -> str:
    """Render the daily plan as a tabulate grid with category emojis."""
    headers = ["Start", "End", "Pet", "Task", "Min", "Priority", "Status"]
    rows = []
    for item in plan.items:
        t = item.task
        rows.append(
            [
                item.start_time.strftime("%H:%M"),
                item.end_time.strftime("%H:%M"),
                owner.pet_name_for(t.pet_id),
                f"{CATEGORY_EMOJI.get(t.category, '📋')} {t.title}",
                t.duration_minutes,
                Task.priority_label(t.priority),
                status_emoji(t.completed),
            ]
        )
    lines = [
        f"Today's Schedule — {owner.name} ({plan.plan_date.isoformat()})",
        f"Time budget: {owner.daily_minutes_available} minutes",
    ]
    if not rows:
        lines.append("(no tasks scheduled)")
    else:
        lines.append(tabulate(rows, headers=headers, tablefmt="rounded_outline"))
    warn = [
        n
        for n in plan.notes
        if "conflict" in n.lower() or "overlap" in n.lower()
    ]
    if warn:
        lines.append("\nWarnings:")
        for w in warn:
            lines.append(f"  ⚠ {w}")
    if plan.deferred_tasks:
        lines.append("\nDeferred (over budget):")
        for task in plan.deferred_tasks:
            lines.append(
                f"  • {owner.pet_name_for(task.pet_id)}: {task.title} "
                f"({task.duration_minutes} min, {Task.priority_label(task.priority)})"
            )
    return "\n".join(lines)


def main() -> None:
    data_path = Path("data.json")
    if data_path.exists():
        owner = load_from_json(data_path)
        print(f"(Loaded owner from {data_path})\n")
    else:
        owner = Owner(name="Jordan Lee", daily_minutes_available=120)
        biscuit = Pet(
            name="Biscuit",
            species="dog",
            breed="Golden Retriever",
            owner_id=owner.owner_id,
        )
        mochi = Pet(
            name="Mochi",
            species="cat",
            breed="Domestic Shorthair",
            owner_id=owner.owner_id,
        )
        owner.add_pet(biscuit)
        owner.add_pet(mochi)

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
    pets = owner.get_pets()
    biscuit = next((p for p in pets if p.name == "Biscuit"), pets[0] if pets else None)
    daily_tasks = [
        t for t in (biscuit.list_tasks() if biscuit else []) if t.title == "Daily breakfast"
    ]
    daily_feed = daily_tasks[0] if daily_tasks else None

    print("=== Priority-first schedule order (sort_by_priority) ===")
    pri_rows = [
        [
            owner.pet_name_for(t.pet_id),
            t.title,
            Task.priority_label(t.priority),
            t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
        ]
        for t in scheduler.sort_by_priority([x for x in all_tasks if not x.completed])
    ]
    print(tabulate(pri_rows, headers=["Pet", "Task", "Priority", "Preferred"], tablefmt="simple"))

    print("\n=== Sort by preferred time ===")
    time_rows = [
        [
            t.preferred_time.strftime("%H:%M") if t.preferred_time else "—",
            owner.pet_name_for(t.pet_id),
            f"{CATEGORY_EMOJI.get(t.category, '📋')} {t.title}",
        ]
        for t in scheduler.sort_by_time(all_tasks)
    ]
    print(tabulate(time_rows, headers=["Preferred", "Pet", "Task"], tablefmt="simple"))

    print("\n=== Generate schedule ===")
    plan = scheduler.schedule_day(owner, date.today())
    print(format_schedule_table(owner, plan))

    slot = scheduler.next_available_slot(plan, duration_minutes=20)
    if slot:
        print(f"\nNext available 20-minute slot today: {slot.strftime('%H:%M')}")
    else:
        print("\nNo 20-minute gap found before 22:00.")

    if daily_feed and biscuit:
        print("\n=== Recurring: complete daily breakfast ===")
        before = len(biscuit.list_tasks())
        spawned = biscuit.mark_task_complete(daily_feed.task_id, date.today())
        after = len(biscuit.list_tasks())
        print(f"  Tasks before: {before}, after: {after}")
        if spawned:
            print(
                f"  Next occurrence: {spawned.title} due {spawned.due_date.isoformat()}"
            )

    save_to_json(owner, data_path)
    print(f"\n(Saved owner to {data_path})")


if __name__ == "__main__":
    main()
