# Step 1: Import required modules
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List


# Step 2: Define a simple event type for step changes
@dataclass
class StepEvent:
    name: str


# Step 3: Implement the StepTracker class
class StepTracker:
    """Global tracker for build steps."""

    def __init__(self, steps: List[str], step: int = 0) -> None:
        self.steps = steps
        self.current = step
        self.listeners: List[Callable[[StepEvent], None]] = []
        self._display_current()

    def register(self, listener: Callable[[StepEvent], None]) -> None:
        """Register a listener for step change events."""
        self.listeners.append(listener)

    def dispatch(self, event: StepEvent) -> None:
        """Set the current step via an event."""
        if event.name in self.steps:
            self.current = self.steps.index(event.name)
            self._display_current()
            for listener in self.listeners:
                listener(event)

    def advance(self) -> None:
        """Move to the next step and notify listeners."""
        if self.current + 1 < len(self.steps):
            self.current += 1
            self._display_current()
            event = StepEvent(self.steps[self.current])
            for listener in self.listeners:
                listener(event)

    def _display_current(self) -> None:
        """Print a ribbon indicating the current step."""
        step_name = self.steps[self.current]
        print(f"=== [StepTracker] {step_name} ===")


# Step 4: Create a global instance with default steps
DEFAULT_STEPS = ["Scaffolding", "Wiring API", "Styling"]
step_tracker = StepTracker(DEFAULT_STEPS)
