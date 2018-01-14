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


def render_surface(surfaces: list[Surface], window: Window) -> list[str]:
    """Render the granted versus exercised surface, one line per principal."""
    lines = [f"# surface for window {window.label()}"]
    lines.append("# principal granted exercised unused")
    for surface in surfaces:
        lines.append(
            f"{surface.principal} "
            f"granted={len(surface.granted)} "
            f"exercised={len(surface.exercised)} "
            f"unused={len(surface.unused)}"
        )
    return lines


def _format_finding(finding: Finding) -> str:
    perms = ",".join(finding.permissions)
    if finding.kind == KIND_NARROWABLE_ROLE:
        subject = f"role:{finding.role}"
    else:
        subject = finding.principal
    return f"{finding.kind} {subject} [{perms}] window={finding.window_label}"


def render_unused(
    findings: list[Finding], conclusive: bool, window: Window
) -> list[str]:
    """Render each finding on its own line, prefixed by its kind."""
    lines: list[str] = []
    if not conclusive:
        lines.append(
            f"# window {window.label()} is shorter than the minimum; "
            f"absence-based findings suppressed"
        )
    for finding in findings:
