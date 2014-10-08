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
