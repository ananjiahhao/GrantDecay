# GrantDecay

> 3 unused permissions across an observation window of 31 days
> (2026-06-01 to 2026-07-01), measured against the bundled sample export.

| Finding kind         | Subject         | Depends on        | Window sensitive |
| -------------------- | --------------- | ----------------- | ---------------- |
| `unused-permission`  | one principal   | absence of use    | yes              |
| `narrowable-role`    | one role        | absence of use    | yes              |
| `dormant-principal`  | one principal   | absence of use    | yes              |
| `ungranted-use`      | one principal   | presence of use   | no               |

GrantDecay finds privilege that was granted and never used. It reads an
entitlement export (principals, roles, and the permissions each role confers)
plus an access log export covering a stated window, then reports the unused
privilege surface. The headline number above and every output block in this
file were captured by running the CLI in this session against the files in
`samples/`. Nothing here is hand-written to look like program output.

The four finding kinds in the table are the whole product. Three of them rest on
absence of use, so GrantDecay only produces them when the window is long enough
to mean something. The fourth rests on presence of use, so it is always safe to
report.


## The problem

Access grows by addition. A principal is given a role to unblock one task, the
task ends, and the grant stays. A role accretes permissions because it was
easier to widen the role than to create a narrower one. Over a year, the gap
between what a principal can do and what it actually does grows quietly, and that
gap is the attack surface an incident will use.

The honest difficulty is that you cannot prove a permission is unneeded by
watching for a while and seeing it go untouched. A deploy rollback permission
may sit unused for months and then be the one thing that matters during an
outage. A billing export may fire once a quarter. Absence of use in a short
window is evidence, not proof, and a tool that forgets this will recommend
removing exactly the permission that saves you later.

GrantDecay is built around that limitation rather than pretending it away. It
requires a minimum observation window before it will call anything unused, it
stamps every finding with the window length so a reviewer can weigh it, and it
separates the one finding kind that does not depend on absence (someone using a
permission they were never granted) from the three that do.


## What it does not do
