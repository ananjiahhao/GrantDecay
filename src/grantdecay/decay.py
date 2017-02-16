"""The four finding kinds and the analysis that produces them.

grantdecay compares what each principal was granted against what it actually
exercised inside the observation window, then reports four kinds of finding:

    unused-permission    a principal holds a permission it never exercised.
    narrowable-role      a role confers permissions that no principal holding
                         that role ever exercised, so the role could be narrowed.
    dormant-principal    every permission a principal holds is unused; the whole
                         grant is dormant.
    ungranted-use        a principal exercised a permission it was never granted,
                         which means the entitlement export is stale or a side
                         channel exists.

The first three depend on absence of use, so they are only produced when the
window is conclusive (at least ``min_days`` long). The fourth, ungranted-use,
depends on presence of use, not absence, so it is always produced: seeing an
event that the entitlements do not explain is evidence regardless of window
length.

Every finding carries the window label so a reader can weigh the length of
observation behind it.
"""

from __future__ import annotations

from dataclasses import dataclass

from .accesslog import AccessLog
from .entitlement import Entitlements
from .window import Window, is_conclusive

KIND_UNUSED_PERMISSION = "unused-permission"
KIND_NARROWABLE_ROLE = "narrowable-role"
KIND_DORMANT_PRINCIPAL = "dormant-principal"
KIND_UNGRANTED_USE = "ungranted-use"

FINDING_KINDS = (
    KIND_UNUSED_PERMISSION,
    KIND_NARROWABLE_ROLE,
    KIND_DORMANT_PRINCIPAL,
    KIND_UNGRANTED_USE,
)


@dataclass(frozen=True)
class Finding:
    """One finding.

    ``kind`` is one of the KIND_* constants. ``principal`` is the subject, or an
    empty string for role-level findings. ``role`` is set for narrowable-role
    findings. ``permissions`` is the sorted tuple of permissions the finding
    concerns. ``window_label`` stamps the observation window on the finding.
    """

    kind: str
    principal: str
    role: str
    permissions: tuple[str, ...]
    window_label: str

    def sort_key(self) -> tuple:
        return (self.kind, self.principal, self.role, self.permissions)


@dataclass
class Surface:
    """The per-principal granted versus exercised surface.

    ``granted`` and ``exercised`` are sorted tuples of permission names. This is
    the data behind both the ``surface`` command and the diagram.
    """

    principal: str
    granted: tuple[str, ...]
    exercised: tuple[str, ...]

    @property
    def unused(self) -> tuple[str, ...]:
        """Permissions granted but not exercised, sorted."""
        used = set(self.exercised)
        return tuple(p for p in self.granted if p not in used)


def build_surface(ent: Entitlements, log: AccessLog) -> list[Surface]:
    """Return the granted versus exercised surface for every principal, sorted.

    Exercised permissions are intersected with the granted set so the surface
    shows exercised-and-granted. Permissions exercised but never granted are not
    part of a principal's granted surface; they surface as ungranted-use findings
    instead.
    """
    surfaces: list[Surface] = []
    for principal in ent.principals():
        granted = ent.effective_permissions(principal)
        granted_set = set(granted)
        used = log.used_permissions(principal)
        exercised = tuple(sorted(p for p in used if p in granted_set))
        surfaces.append(
            Surface(principal=principal, granted=granted, exercised=exercised)
        )
    return surfaces


def analyze(
    ent: Entitlements, log: AccessLog, min_days: int
) -> tuple[list[Finding], bool]:
    """Run the analysis and return (findings, conclusive).

    ``conclusive`` reflects whether the window met ``min_days``. When it did not,
    absence-based findings (the first three kinds) are suppressed and only
    ungranted-use findings are produced.
    """
    window = log.window
    label = window.label()
    conclusive = is_conclusive(window, min_days)
    findings: list[Finding] = []

    # ungranted-use: exercised but not granted. Presence-based, always produced.
    for principal in sorted({who for (who, _perm) in log.exercised_pairs()}):
        granted = set(ent.effective_permissions(principal)) if principal in ent.grants else set()
        used = log.used_permissions(principal)
        ungranted = tuple(sorted(p for p in used if p not in granted))
        if ungranted:
            findings.append(
                Finding(
                    kind=KIND_UNGRANTED_USE,
                    principal=principal,
                    role="",
                    permissions=ungranted,
                    window_label=label,
                )
            )

    if conclusive:
        _absence_findings(ent, log, label, findings)

    findings.sort(key=lambda f: f.sort_key())
    return findings, conclusive


def _absence_findings(
    ent: Entitlements, log: AccessLog, label: str, findings: list[Finding]
) -> None:
    """Append the three absence-based finding kinds to ``findings``."""
    surfaces = {s.principal: s for s in build_surface(ent, log)}

    for principal in ent.principals():
        surface = surfaces[principal]
        # dormant-principal: holds permissions but exercised none of them.
        if surface.granted and not surface.exercised:
            findings.append(
                Finding(
                    kind=KIND_DORMANT_PRINCIPAL,
                    principal=principal,
                    role="",
                    permissions=surface.granted,
                    window_label=label,
                )
            )
            continue
        # unused-permission: holds some it never exercised (but not fully dormant).
        if surface.unused:
            findings.append(
                Finding(
                    kind=KIND_UNUSED_PERMISSION,
                    principal=principal,
