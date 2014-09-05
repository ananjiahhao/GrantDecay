"""Parse the entitlement export and expand roles to effective permissions.

The entitlement export is a line-oriented text file. Blank lines and lines whose
first non-space character is ``#`` are ignored. Every other line is a record of
one of two kinds:

    role   <role_name> <permission>[ <permission> ...]
    grant  <principal> <role_name>[ <role_name> ...]

A ``role`` record declares that a role confers one or more permissions. A role
may appear on more than one ``role`` line, in which case the permission sets are
unioned. A ``grant`` record assigns one or more roles to a principal.

Expansion turns the two record kinds into the effective permission set for each
principal: the union of the permissions of every role granted to that principal.
A grant that names a role never declared by any ``role`` record is an error,
because it means the export cannot be reasoned about honestly.

The parser is strict: it reports the file, line number, and reason for every
malformed record rather than guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class EntitlementError(ValueError):
    """Raised when the entitlement export cannot be parsed or expanded."""


@dataclass(frozen=True)
class Grant:
    """One principal and the ordered, de-duplicated roles granted to it."""

    principal: str
    roles: tuple[str, ...]


@dataclass
class Entitlements:
    """The parsed entitlement export.

    ``roles`` maps a role name to the sorted tuple of permissions it confers.
    ``grants`` maps a principal to its Grant. Both are built deterministically so
    that identical input yields identical structures.
    """

    roles: dict[str, tuple[str, ...]] = field(default_factory=dict)
    grants: dict[str, Grant] = field(default_factory=dict)

    def principals(self) -> tuple[str, ...]:
        """Return principals in sorted order."""
        return tuple(sorted(self.grants))

    def effective_permissions(self, principal: str) -> tuple[str, ...]:
        """Return the sorted union of permissions the principal holds.

        A principal holds every permission conferred by every role granted to it.
        """
        grant = self.grants[principal]
        perms: set[str] = set()
        for role in grant.roles:
            perms.update(self.roles.get(role, ()))
        return tuple(sorted(perms))

    def role_permissions(self, role: str) -> tuple[str, ...]:
        """Return the sorted permissions conferred by a role."""
        return self.roles.get(role, ())


def _split_record(line: str) -> list[str]:
    """Split a record into whitespace-delimited fields."""
    return line.split()


def parse_entitlements(text: str, source: str = "<entitlement>") -> Entitlements:
    """Parse the entitlement export text into an Entitlements structure.

    ``source`` is used only in error messages. Raises EntitlementError on any
    malformed or inconsistent record.
    """
    role_perms: dict[str, set[str]] = {}
    grants: dict[str, Grant] = {}

    for lineno, raw in enumerate(text.splitlines(), start=1):
