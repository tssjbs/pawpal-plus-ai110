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

No methods were implemented yet; Scheduler methods raise `NotImplementedError` until scheduling logic is built in later phases.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
