"""Render deterministic, line-oriented output for the CLI.

Three renderers:

    render_surface   the granted versus exercised surface, one line per principal.
    render_unused    each finding on its own line, prefixed by kind.
    render_report    a grouped report with a header, the window, a conclusiveness
                     note, and each finding kind as its own block.

Every renderer returns a list of lines with no trailing newline so the CLI can
join them and diffs stay stable.
"""

from __future__ import annotations

from .decay import (
    FINDING_KINDS,
    KIND_DORMANT_PRINCIPAL,
    KIND_NARROWABLE_ROLE,
    KIND_UNGRANTED_USE,
    KIND_UNUSED_PERMISSION,
    Finding,
    Surface,
)
from .window import Window

_KIND_TITLES = {
    KIND_UNUSED_PERMISSION: "unused permissions",
    KIND_NARROWABLE_ROLE: "narrowable roles",
    KIND_DORMANT_PRINCIPAL: "dormant principals",
    KIND_UNGRANTED_USE: "ungranted use",
}


