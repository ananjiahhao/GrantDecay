"""The observation window, and refusing to conclude on a short window.

Absence of use inside a window is not proof that a permission is unneeded. A
permission might be exercised only at quarter close, during an incident, or on a
yearly audit. The honest guard against over-claiming is a minimum window: below
it, grantdecay refuses to label anything as unused and says so plainly.

This module defines the Window value type, its inclusive length in days, and the
default minimum of 30 days. The default is a policy choice, not a measurement: it
is documented as such and can be overridden on the command line.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

DEFAULT_MIN_DAYS = 30


class WindowError(ValueError):
    """Raised when a window is malformed."""


@dataclass(frozen=True)
class Window:
    """An inclusive observation window bounded by two dates.

    ``start`` must not be after ``end``. Length is measured in days, inclusive of
    both endpoints, so a window whose start equals its end has length 1.
    """

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise WindowError(
                f"window start {self.start.isoformat()} is after end "
                f"{self.end.isoformat()}"
            )

    @property
    def length_days(self) -> int:
        """Inclusive length of the window in days."""
        return (self.end - self.start).days + 1

    def contains(self, when: date) -> bool:
        """Return True if the date falls inside the window, endpoints included."""
        return self.start <= when <= self.end

    def label(self) -> str:
        """Return a short human label used to stamp findings with the window."""
        return (
            f"{self.start.isoformat()}..{self.end.isoformat()} "
            f"({self.length_days} days)"
        )


def is_conclusive(window: Window, min_days: int = DEFAULT_MIN_DAYS) -> bool:
    """Return True if the window is long enough to draw a conclusion.

    A window shorter than ``min_days`` is inconclusive: grantdecay will not label
    permissions as unused from it.
    """
    return window.length_days >= min_days
