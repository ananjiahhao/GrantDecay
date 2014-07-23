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
