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
        lines.append(_format_finding(finding))
    if not findings:
        lines.append("# no findings")
    return lines


def render_report(
    findings: list[Finding],
    conclusive: bool,
    window: Window,
    min_days: int,
) -> list[str]:
    """Render a grouped report, one block per finding kind."""
    lines = ["grantdecay report"]
    lines.append(f"window: {window.label()}")
    lines.append(f"minimum window: {min_days} days")
    if conclusive:
        lines.append("conclusive: yes")
    else:
        lines.append(
            "conclusive: no (absence-based findings suppressed; only "
            "ungranted-use is reported)"
        )

    unused_count = sum(
        len(f.permissions)
        for f in findings
        if f.kind in (KIND_UNUSED_PERMISSION, KIND_DORMANT_PRINCIPAL)
    )
    lines.append(f"unused permission surface: {unused_count}")
    lines.append("")

    by_kind: dict[str, list[Finding]] = {kind: [] for kind in FINDING_KINDS}
    for finding in findings:
        by_kind[finding.kind].append(finding)

    for kind in FINDING_KINDS:
        group = by_kind[kind]
        lines.append(f"## {_KIND_TITLES[kind]} ({len(group)})")
        if not group:
            lines.append("  none")
        else:
            for finding in group:
                subject = (
                    f"role:{finding.role}"
                    if kind == KIND_NARROWABLE_ROLE
                    else finding.principal
                )
                perms = ", ".join(finding.permissions)
                lines.append(f"  {subject}: {perms}")
        lines.append("")

    # Drop the trailing blank line for a stable tail.
    if lines and lines[-1] == "":
        lines.pop()
    return lines

# draft note 1771
