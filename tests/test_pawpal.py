"""Tests for PawPal+ core models and algorithmic helpers."""

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
