"""Phase 2 smoke tests for PawPal+ core models."""

from datetime import date

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
