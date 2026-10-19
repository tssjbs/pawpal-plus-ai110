"""
PawPal+ logic layer — Owner, Pet, Task, and scheduling (Phase 1 skeletons).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
import uuid


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class Task:
    """A single pet care action (walk, feeding, meds, etc.)."""

    pet_id: str
    title: str
    category: str
    duration_minutes: int
    priority: int
    task_id: str = field(default_factory=lambda: _new_id("task"))
    is_recurring: bool = False
    recurrence_rule: str = "daily"

    def mark_complete(self) -> None:
        """Record completion (persistence TBD in later phases)."""
        raise NotImplementedError("mark_complete will be implemented in Phase 2+")


@dataclass
class Pet:
    """Pet profile and the task list attached to this animal."""

    name: str
    species: str
    owner_id: str
    pet_id: str = field(default_factory=lambda: _new_id("pet"))
    breed: str = ""
    age_years: int = 0
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> Task:
        """Attach a care task to this pet."""
        if task.pet_id != self.pet_id:
            task.pet_id = self.pet_id
        self._tasks.append(task)
        return task

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self._tasks)


@dataclass
class Owner:
    """Pet owner profile and daily planning constraints."""

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
        """Return pets owned by this user."""
        return list(self._pets)


@dataclass
class ScheduledItem:
    """One task placed on the daily timeline with a short explanation."""

    task: Task
    start_time: time
    end_time: time
    reason: str = ""


@dataclass
class DailyPlan:
    """Output of the scheduler for a single pet and day."""

    plan_date: date
    pet_id: str
    items: list[ScheduledItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    deferred_tasks: list[Task] = field(default_factory=list)


class Scheduler:
    """Builds ordered daily plans from tasks, time budget, and priorities."""

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Order tasks so higher priority values come first."""
        raise NotImplementedError

    def apply_time_budget(self, tasks: list[Task], minutes: int) -> list[Task]:
        """Return tasks that fit within the available minutes (greedy placeholder)."""
        raise NotImplementedError

    def detect_conflicts(self, plan: DailyPlan) -> list[str]:
        """Find overlapping scheduled items or invalid slots."""
        raise NotImplementedError

    def explain_plan(self, plan: DailyPlan) -> list[str]:
        """Human-readable reasons for inclusion, order, and deferrals."""
        raise NotImplementedError

    def schedule_day(
        self,
        owner: Owner,
        pet: Pet,
        tasks: list[Task],
        plan_date: date,
        day_start: Optional[time] = None,
    ) -> DailyPlan:
        """Produce a daily plan for one pet using owner time and task metadata."""
        raise NotImplementedError
