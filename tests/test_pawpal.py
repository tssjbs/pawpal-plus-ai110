"""
Automated tests for PawPal+ (Phase 5).

Coverage focus:
- Happy paths: add tasks, multi-pet schedule, sort/filter, recurrence, conflicts
- Edge cases: owner with no tasks, time budget deferral, weekly recurrence,
  non-recurring completion, tasks without preferred time sort last
"""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    pet = Pet(name="Test", species="dog", owner_id="owner_test")
    task = Task(
        pet_id=pet.pet_id,
        title="Walk",
        category="walk",
        duration_minutes=20,
        priority=2,
    )
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Test", species="cat", owner_id="owner_test")
    assert len(pet.list_tasks()) == 0
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Feed",
            category="feeding",
            duration_minutes=10,
            priority=1,
        )
    )
    assert len(pet.list_tasks()) == 1


def test_scheduler_uses_owner_get_all_tasks():
    owner = Owner(name="Alex", daily_minutes_available=60)
    a = Pet(name="A", species="dog", owner_id=owner.owner_id)
    b = Pet(name="B", species="cat", owner_id=owner.owner_id)
    owner.add_pet(a)
    owner.add_pet(b)
    a.add_task(
        Task(pet_id=a.pet_id, title="Walk", category="walk", duration_minutes=20, priority=2)
    )
    b.add_task(
        Task(pet_id=b.pet_id, title="Meds", category="meds", duration_minutes=10, priority=5)
    )
    plan = Scheduler().schedule_day(owner, date.today())
    pet_ids = {item.task.pet_id for item in plan.items}
    assert len(pet_ids) >= 1
    assert len(owner.get_all_tasks()) == 2


def test_sort_by_time_orders_preferred_clock():
    scheduler = Scheduler()
    pet = Pet(name="P", species="dog", owner_id="o")
    late = Task(
        pet_id=pet.pet_id,
        title="Late",
        category="walk",
        duration_minutes=10,
        priority=1,
        preferred_time=time(18, 0),
    )
    early = Task(
        pet_id=pet.pet_id,
        title="Early",
        category="walk",
        duration_minutes=10,
        priority=1,
        preferred_time=time(8, 0),
    )
    ordered = scheduler.sort_by_time([late, early])
    assert [t.title for t in ordered] == ["Early", "Late"]


def test_filter_tasks_by_pet_and_status():
    owner = Owner(name="Sam", daily_minutes_available=60)
    dog = Pet(name="Rex", species="dog", owner_id=owner.owner_id)
    cat = Pet(name="Luna", species="cat", owner_id=owner.owner_id)
    owner.add_pet(dog)
    owner.add_pet(cat)
    done = Task(
        pet_id=dog.pet_id,
        title="Done walk",
        category="walk",
        duration_minutes=10,
        priority=1,
    )
    done.mark_complete()
    dog.add_task(done)
    dog.add_task(
        Task(
            pet_id=dog.pet_id,
            title="Pending feed",
            category="feeding",
            duration_minutes=5,
            priority=1,
        )
    )
    cat.add_task(
        Task(
            pet_id=cat.pet_id,
            title="Cat meds",
            category="meds",
            duration_minutes=5,
            priority=1,
        )
    )
    rex_open = owner.filter_tasks(pet_name="Rex", completed=False)
    assert len(rex_open) == 1
    assert rex_open[0].title == "Pending feed"


def test_recurring_daily_spawns_next_task():
    pet = Pet(name="P", species="dog", owner_id="o")
    today = date(2026, 10, 18)
    task = Task(
        pet_id=pet.pet_id,
        title="Daily pill",
        category="meds",
        duration_minutes=5,
        priority=3,
        is_recurring=True,
        recurrence_rule="daily",
    )
    pet.add_task(task)
    nxt = pet.mark_task_complete(task.task_id, today)
    assert task.completed is True
    assert nxt is not None
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.completed is False


def test_detect_same_time_conflicts():
    owner = Owner(name="A", daily_minutes_available=120)
    pet = Pet(name="Mochi", species="cat", owner_id=owner.owner_id)
    owner.add_pet(pet)
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Meds",
            category="meds",
            duration_minutes=10,
            priority=5,
            preferred_time=time(9, 0),
        )
    )
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Play",
            category="enrichment",
            duration_minutes=15,
            priority=2,
            preferred_time=time(9, 0),
        )
    )
    warnings = Scheduler().detect_same_time_conflicts(owner.get_all_tasks(), owner)
    assert len(warnings) == 1
    assert "09:00" in warnings[0]


def test_schedule_empty_when_pet_has_no_tasks():
    owner = Owner(name="Quiet", daily_minutes_available=60)
    owner.add_pet(Pet(name="Solo", species="dog", owner_id=owner.owner_id))
    plan = Scheduler().schedule_day(owner, date.today())
    assert plan.items == []
    assert plan.deferred_tasks == []


def test_time_budget_defers_low_priority_tasks():
    owner = Owner(name="Busy", daily_minutes_available=30)
    pet = Pet(name="Dog", species="dog", owner_id=owner.owner_id)
    owner.add_pet(pet)
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Long walk",
            category="walk",
            duration_minutes=25,
            priority=5,
        )
    )
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Optional play",
            category="enrichment",
            duration_minutes=20,
            priority=1,
        )
    )
    plan = Scheduler().schedule_day(owner, date.today())
    assert len(plan.items) == 1
    assert plan.items[0].task.title == "Long walk"
    assert len(plan.deferred_tasks) == 1
    assert plan.deferred_tasks[0].title == "Optional play"


def test_recurring_weekly_advances_seven_days():
    pet = Pet(name="P", species="cat", owner_id="o")
    start = date(2026, 10, 18)
    task = Task(
        pet_id=pet.pet_id,
        title="Weekly groom",
        category="grooming",
        duration_minutes=30,
        priority=2,
        is_recurring=True,
        recurrence_rule="weekly",
    )
    pet.add_task(task)
    nxt = pet.mark_task_complete(task.task_id, start)
    assert nxt is not None
    assert nxt.due_date == start + timedelta(days=7)


def test_non_recurring_complete_does_not_spawn():
    pet = Pet(name="P", species="dog", owner_id="o")
    task = Task(
        pet_id=pet.pet_id,
        title="One-off vet",
        category="other",
        duration_minutes=60,
        priority=4,
    )
    pet.add_task(task)
    before = len(pet.list_tasks())
    spawned = pet.mark_task_complete(task.task_id, date.today())
    assert spawned is None
    assert len(pet.list_tasks()) == before


def test_sort_by_time_puts_missing_preferred_last():
    scheduler = Scheduler()
    pet = Pet(name="P", species="dog", owner_id="o")
    with_time = Task(
        pet_id=pet.pet_id,
        title="Timed",
        category="walk",
        duration_minutes=10,
        priority=1,
        preferred_time=time(10, 0),
    )
    no_time = Task(
        pet_id=pet.pet_id,
        title="Anytime",
        category="feeding",
        duration_minutes=5,
        priority=1,
    )
    ordered = scheduler.sort_by_time([no_time, with_time])
    assert [t.title for t in ordered] == ["Timed", "Anytime"]


def test_schedule_day_surfaces_preferred_time_conflict_in_notes():
    owner = Owner(name="A", daily_minutes_available=120)
    pet = Pet(name="Cat", species="cat", owner_id=owner.owner_id)
    owner.add_pet(pet)
    for title in ("A", "B"):
        pet.add_task(
            Task(
                pet_id=pet.pet_id,
                title=title,
                category="meds",
                duration_minutes=5,
                priority=3,
                preferred_time=time(12, 0),
            )
        )
    plan = Scheduler().schedule_day(owner, date.today())
    conflict_notes = [n for n in plan.notes if "Preferred-time conflict" in n]
    assert len(conflict_notes) == 1
    assert "12:00" in conflict_notes[0]


def test_future_due_recurring_not_scheduled_until_due():
    owner = Owner(name="A", daily_minutes_available=60)
    pet = Pet(name="Dog", species="dog", owner_id=owner.owner_id)
    owner.add_pet(pet)
    tomorrow = date.today() + timedelta(days=1)
    pet.add_task(
        Task(
            pet_id=pet.pet_id,
            title="Tomorrow feed",
            category="feeding",
            duration_minutes=10,
            priority=3,
            due_date=tomorrow,
        )
    )
    plan_today = Scheduler().schedule_day(owner, date.today())
    assert plan_today.items == []
    plan_tomorrow = Scheduler().schedule_day(owner, tomorrow)
    assert len(plan_tomorrow.items) == 1
