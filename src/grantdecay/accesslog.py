"""Parse the access log export.

The access log export is a line-oriented text file. Blank lines and lines whose
first non-space character is ``#`` are ignored. The file begins with a required
header line that states the observation window as two ISO-8601 dates:

    window <start> <end>

Every subsequent record is one access event:

    <date> <principal> <permission>

where ``<date>`` is an ISO-8601 date (YYYY-MM-DD) that must fall inside the
declared window, inclusive of both endpoints. An event dated outside the window
is an error, because it means the log and its stated window disagree and no
honest conclusion can be drawn.

The parser returns the window plus the set of (principal, permission) pairs that
were exercised, along with a per-pair count so a report can show how heavily a
permission was used. Ordering of the input does not affect the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .window import Window, WindowError


class AccessLogError(ValueError):
    """Raised when the access log export cannot be parsed."""


@dataclass
class AccessLog:
    """The parsed access log.

    ``window`` is the declared observation window. ``exercised`` maps a
    (principal, permission) pair to the number of events recorded for it.
    """

    window: Window
    exercised: dict[tuple[str, str], int] = field(default_factory=dict)

    def used_permissions(self, principal: str) -> frozenset[str]:
        """Return the set of permissions the principal exercised."""
        return frozenset(
            perm for (who, perm) in self.exercised if who == principal
        )

    def exercised_pairs(self) -> frozenset[tuple[str, str]]:
        """Return every (principal, permission) pair that appears in the log."""
        return frozenset(self.exercised)

    def count(self, principal: str, permission: str) -> int:
        """Return how many events named this principal and permission."""
        return self.exercised.get((principal, permission), 0)


def _parse_date(value: str, source: str, lineno: int) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise AccessLogError(
            f"{source}:{lineno}: {value!r} is not an ISO-8601 date (YYYY-MM-DD)"
        )


def parse_access_log(text: str, source: str = "<accesslog>") -> AccessLog:
    """Parse the access log export text into an AccessLog.

    ``source`` is used only in error messages. Raises AccessLogError on any
    malformed record or on an event dated outside the declared window.
    """
    window: Window | None = None
    exercised: dict[tuple[str, str], int] = {}

    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if fields[0] == "window":
            if window is not None:
                raise AccessLogError(
                    f"{source}:{lineno}: window declared more than once"
                )
            if len(fields) != 3:
                raise AccessLogError(
                    f"{source}:{lineno}: window needs a start date and an end "
                    f"date"
                )
            start = _parse_date(fields[1], source, lineno)
            end = _parse_date(fields[2], source, lineno)
            try:
                window = Window(start=start, end=end)
            except WindowError as exc:
                raise AccessLogError(f"{source}:{lineno}: {exc}")
            continue

        if window is None:
            raise AccessLogError(
                f"{source}:{lineno}: access event before the window header; the "
                f"window must be declared first"
            )
        if len(fields) != 3:
            raise AccessLogError(
                f"{source}:{lineno}: access event needs a date, a principal, and "
                f"a permission"
            )
        when = _parse_date(fields[0], source, lineno)
        if not window.contains(when):
            raise AccessLogError(
                f"{source}:{lineno}: event dated {when.isoformat()} falls outside "
                f"the window {window.start.isoformat()}..{window.end.isoformat()}"
            )
        principal = fields[1]
        permission = fields[2]
        key = (principal, permission)
        exercised[key] = exercised.get(key, 0) + 1

    if window is None:
        raise AccessLogError(
            f"{source}: no window header found; the log must begin with "
            f"'window <start> <end>'"
        )

    return AccessLog(window=window, exercised=exercised)

# draft note 1777
