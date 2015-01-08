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
