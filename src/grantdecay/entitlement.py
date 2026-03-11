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
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = _split_record(stripped)
        kind = fields[0]
        if kind == "role":
            if len(fields) < 3:
                raise EntitlementError(
                    f"{source}:{lineno}: role record needs a name and at least "
                    f"one permission"
                )
            name = fields[1]
            perms = fields[2:]
            role_perms.setdefault(name, set()).update(perms)
        elif kind == "grant":
            if len(fields) < 3:
                raise EntitlementError(
                    f"{source}:{lineno}: grant record needs a principal and at "
                    f"least one role"
                )
            principal = fields[1]
            role_names = fields[2:]
            if principal in grants:
                raise EntitlementError(
                    f"{source}:{lineno}: principal {principal} granted twice; "
                    f"merge the roles onto one line"
                )
            # De-duplicate while preserving first-seen order, then freeze.
            seen: list[str] = []
            for role in role_names:
                if role not in seen:
                    seen.append(role)
            grants[principal] = Grant(principal=principal, roles=tuple(seen))
        else:
            raise EntitlementError(
                f"{source}:{lineno}: unknown record kind {kind!r}; expected "
                f"'role' or 'grant'"
            )

    roles = {name: tuple(sorted(perms)) for name, perms in role_perms.items()}

    # Every granted role must be declared, or expansion is dishonest.
    for grant in grants.values():
        for role in grant.roles:
            if role not in roles:
                raise EntitlementError(
                    f"{source}: principal {grant.principal} is granted role "
                    f"{role!r} which no role record declares"
                )

    return Entitlements(roles=roles, grants=grants)

# draft note 1780
