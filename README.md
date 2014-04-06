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

- It does not connect to any identity provider, cloud API, or network service.
  It reads two local files. There are no sockets, no HTTP, no DNS anywhere in
  the code.
- It does not decide that an unused permission should be removed. It reports the
  surface and labels it with the window. The removal decision is yours, and the
  minimum window exists precisely because that decision needs judgement.
- It does not model permission hierarchies, wildcards, deny rules, conditions,
  or time-bound grants. A permission is an opaque string that either matches or
  does not.
- It does not infer intent. A permission exercised once counts as exercised, the
  same as one exercised a thousand times. The surface is about presence, not
  volume.
- It does not read real production exports. The bundled samples are authored
  test vectors, documented as such in `samples/README.md`.


## Install

No dependencies beyond the Python standard library, Python 3.11 or newer.

```
python -m pip install -e .
```

Or run straight from the source tree without installing, which is how every
command in this README was run:

```
set PYTHONPATH=src
python -m grantdecay version
```


## Quick start

The two sample files ship in `samples/`. Point the CLI at them.

Command:

```
python -m grantdecay report samples/entitlements.txt samples/accesslog.txt
```

Output captured in this session:

```
grantdecay report
window: 2026-06-01..2026-07-01 (31 days)
minimum window: 30 days
conclusive: yes
unused permission surface: 3

## unused permissions (1)
  svc-web: deploy:rollback

## narrowable roles (1)
  role:deploy: deploy:rollback

## dormant principals (1)
  svc-batch: billing:export, billing:view

## ungranted use (1)
  svc-oncall: repo:read
```

The command exits 1 because findings are present.


## The input formats

Both files are line-oriented plain text. Blank lines and lines whose first non
space character is `#` are ignored. This keeps the inputs diffable in git and
easy to author by hand.

### Entitlement export

Two record kinds:

```
role   <role_name> <permission> [<permission> ...]
grant  <principal>  <role_name>  [<role_name> ...]
```

A `role` record declares the permissions a role confers. A role may appear on
more than one `role` line, and the permission sets are unioned. A `grant` record
assigns one or more roles to a principal. A grant that names a role no `role`
record declares is a hard error, because the export cannot then be reasoned
about honestly.

### Access log export

The file must begin with a window header, then any number of events:

```
window <start> <end>
<date> <principal> <permission>
```

Dates are ISO-8601 (YYYY-MM-DD). The window is inclusive of both endpoints. An
event dated outside the window is a hard error, because the log and its stated
window would then disagree.


## Output format, field by field

The `report` command prints a header block then one section per finding kind.

| Line                          | Meaning                                              |
| ----------------------------- | ---------------------------------------------------- |
| `grantdecay report`           | fixed banner                                         |
| `window: <start>..<end> (N days)` | the observation window and its inclusive length  |
| `minimum window: N days`      | the threshold below which absence is inconclusive    |
| `conclusive: yes` or `no`     | whether the window met the minimum                   |
| `unused permission surface: N` | count of permissions held but not exercised         |
| `## <kind> (N)`               | one section header per finding kind, with a count    |
| `  <subject>: <permissions>`  | one indented line per finding                        |

The `surface` command prints one line per principal with granted, exercised, and
unused counts. The `unused` command prints one finding per line, each stamped
with the window, which is the format meant for grepping and diffing.


