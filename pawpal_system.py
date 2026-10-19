"""
PawPal+ logic layer — Owner, Pet, Task, and scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Optional
import uuid


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _add_minutes(t: time, minutes: int) -> time:
    """Return a new clock time after adding minutes (same day wrap)."""
    base = datetime.combine(date.today(), t)
    return (base + timedelta(minutes=minutes)).time()


@dataclass
class Task:
    """A single pet care activity with timing, priority, and completion state."""

    pet_id: str
    title: str
    category: str
    duration_minutes: int
    priority: int
    task_id: str = field(default_factory=lambda: _new_id("task"))
    is_recurring: bool = False
    recurrence_rule: str = "daily"
    preferred_time: Optional[time] = None
    due_date: Optional[date] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed for the current cycle."""
        self.completed = True

    def create_next_occurrence(self, from_date: date) -> Optional[Task]:
        """
        Build a fresh Task for the next recurrence after ``from_date``.

        Daily tasks due the next calendar day; weekly tasks due seven days later.
        Returns None when the task is not recurring or the rule is unknown.
        """
        if not self.is_recurring:
            return None
        rule = self.recurrence_rule.strip().lower()
        if rule == "daily":
            next_due = from_date + timedelta(days=1)
        elif rule == "weekly":
            next_due = from_date + timedelta(days=7)
        else:
            return None
        return Task(
            pet_id=self.pet_id,
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            is_recurring=True,
            recurrence_rule=self.recurrence_rule,
            preferred_time=self.preferred_time,
            due_date=next_due,
            completed=False,
        )

    def is_due_on(self, plan_date: date) -> bool:
        """True when the task should appear on ``plan_date`` (no due date = always)."""
        if self.due_date is None:
            return True
        return self.due_date <= plan_date


@dataclass
class Pet:
    """Pet profile and care tasks for one animal."""

    name: str
    species: str
    owner_id: str
    pet_id: str = field(default_factory=lambda: _new_id("pet"))
    breed: str = ""
    age_years: int = 0
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> Task:
        """Add a task to this pet's list."""
        if task.pet_id != self.pet_id:
            task.pet_id = self.pet_id
        self._tasks.append(task)
        return task

    def list_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks."""
        return list(self._tasks)

    def mark_task_complete(
        self, task_id: str, reference_date: Optional[date] = None
    ) -> Optional[Task]:
        """
        Mark a task complete and, if recurring, append the next occurrence.

        Returns the newly created Task when recurrence spawns one; otherwise None.
        """
        ref = reference_date or date.today()
        for task in self._tasks:
            if task.task_id != task_id:
                continue
            task.mark_complete()
            nxt = task.create_next_occurrence(ref)
            if nxt is not None:
                self.add_task(nxt)
                return nxt
            return None
        return None


@dataclass
class Owner:
    """Owner profile, pets, and shared daily time budget."""

    name: str
    daily_minutes_available: int
    owner_id: str = field(default_factory=lambda: _new_id("owner"))
    preferences: list[str] = field(default_factory=list)
    _pets: list[Pet] = field(default_factory=list, repr=False)

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner."""
        pet.owner_id = self.owner_id
        self._pets.append(pet)
        return pet

    def get_pets(self) -> list[Pet]:
        """Return all pets for this owner."""
        return list(self._pets)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets (Scheduler entry point)."""
        tasks: list[Task] = []
        for pet in self._pets:
            tasks.extend(pet.list_tasks())
        return tasks

    def pet_name_for(self, pet_id: str) -> str:
        """Look up a pet display name by id."""
        for pet in self._pets:
            if pet.pet_id == pet_id:
                return pet.name
        return pet_id

    def filter_tasks(
        self,
        *,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> list[Task]:
        """
        Return tasks matching optional pet name and/or completion status.

        Pet name comparison is case-insensitive. Omit a filter to skip it.
        """
        tasks = self.get_all_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            target = pet_name.strip().lower()
            pet_ids = {
                p.pet_id for p in self._pets if p.name.strip().lower() == target
            }
            tasks = [t for t in tasks if t.pet_id in pet_ids]
        return tasks


@dataclass
class ScheduledItem:
    """One scheduled task slot with start/end and rationale."""

    task: Task
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class DailyPlan:
    """Scheduled and deferred tasks for one owner on one calendar day."""

    plan_date: date
    owner_id: str
    items: list[ScheduledItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    deferred_tasks: list[Task] = field(default_factory=list)


class Scheduler:
    """Organizes tasks from an Owner across pets into a daily plan."""

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """
        Sort tasks by ``preferred_time`` (earliest first, HH:MM on the clock).

        Tasks without a preferred time are listed after those with one.
        """
        return sorted(
            tasks,
            key=lambda t: (
                t.preferred_time is None,
                t.preferred_time or time(23, 59),
                t.title.lower(),
            ),
        )

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort by priority (high first), then earlier preferred time."""
        return sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                t.preferred_time or time(23, 59),
                t.title,
            ),
        )

    def detect_same_time_conflicts(
        self, tasks: list[Task], owner: Owner
    ) -> list[str]:
        """
        Lightweight conflict check: warn when multiple tasks share one preferred time.

        Does not crash or block scheduling; returns human-readable warning strings.
        """
        by_slot: dict[time, list[Task]] = {}
        for task in tasks:
            if task.completed or task.preferred_time is None:
                continue
            by_slot.setdefault(task.preferred_time, []).append(task)
        warnings: list[str] = []
        for slot, group in by_slot.items():
            if len(group) < 2:
                continue
            labels = [
                f"{owner.pet_name_for(t.pet_id)}: {t.title}" for t in group
            ]
            warnings.append(
                f"Preferred-time conflict at {slot.strftime('%H:%M')} — "
                + "; ".join(labels)
            )
        return warnings

    def apply_time_budget(self, tasks: list[Task], minutes: int) -> tuple[list[Task], list[Task]]:
        """Split tasks into those that fit the budget and those deferred."""
        chosen: list[Task] = []
        deferred: list[Task] = []
        used = 0
        for task in tasks:
            if used + task.duration_minutes <= minutes:
                chosen.append(task)
                used += task.duration_minutes
            else:
                deferred.append(task)
        return chosen, deferred

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """
        Report overlapping scheduled slots in a built plan.

        Compares exact start/end clock times only (not partial overlaps with
        different durations beyond adjacent items).
        """
        conflicts: list[str] = []
        items = sorted(plan.items, key=lambda i: i.start_time)
        for i in range(len(items) - 1):
            cur, nxt = items[i], items[i + 1]
            if cur.end_time > nxt.start_time:
                conflicts.append(
                    f"Schedule overlap: '{cur.task.title}' ends "
                    f"{cur.end_time.strftime('%H:%M')} but '{nxt.task.title}' "
                    f"starts {nxt.start_time.strftime('%H:%M')}"
                )
            elif cur.start_time == nxt.start_time:
                conflicts.append(
                    f"Same start time {cur.start_time.strftime('%H:%M')}: "
                    f"'{cur.task.title}' and '{nxt.task.title}'"
                )
        return conflicts

    def explain_plan(self, plan: DailyPlan) -> list[str]:
        """Build short explanations for scheduled and deferred tasks."""
        lines: list[str] = []
        for item in plan.items:
            lines.append(
                f"{item.task.title}: {item.reason or 'Included by priority and available time.'}"
            )
        for task in plan.deferred_tasks:
            lines.append(
                f"{task.title}: deferred — not enough minutes left in the owner's daily budget."
            )
        return lines

    def schedule_day(
        self,
        owner: Owner,
        plan_date: date,
        day_start: Optional[time] = None,
    ) -> DailyPlan:
        """Build today's plan from all pets' tasks via Owner.get_all_tasks()."""
        start = day_start or time(8, 0)
        pending = [
            t
            for t in owner.get_all_tasks()
            if not t.completed and t.is_due_on(plan_date)
        ]
        preferred_warnings = self.detect_same_time_conflicts(pending, owner)
        ordered = self.sort_by_priority(pending)
        chosen, deferred = self.apply_time_budget(
            ordered, owner.daily_minutes_available
        )

        items: list[ScheduledItem] = []
        cursor = start
        for task in chosen:
            end = _add_minutes(cursor, task.duration_minutes)
            reason = f"Priority {task.priority}"
            if task.preferred_time:
                reason += f", preferred around {task.preferred_time.strftime('%H:%M')}"
            items.append(
                ScheduledItem(
                    task=task,
                    start_time=cursor,
                    end_time=end,
                    reason=reason,
                )
            )
            cursor = end

        plan = DailyPlan(
            plan_date=plan_date,
            owner_id=owner.owner_id,
            items=items,
            deferred_tasks=deferred,
            notes=[],
        )
        if preferred_warnings:
            plan.notes.extend(preferred_warnings)
        conflicts = self.detect_conflicts(plan)
        if conflicts:
            plan.notes.extend(conflicts)
        plan.notes.extend(self.explain_plan(plan))
        return plan
