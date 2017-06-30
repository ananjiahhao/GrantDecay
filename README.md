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


## Reading the report, and what each finding should trigger

| Finding             | What it means                                    | Action to consider                         |
| ------------------- | ------------------------------------------------ | ------------------------------------------ |
| `unused-permission` | a principal holds a permission it never used     | narrow the grant, or note why it is kept   |
| `narrowable-role`   | no holder of a role used one of its permissions  | split or trim the role                     |
| `dormant-principal` | a principal used none of its permissions         | review whether the principal is still live |
| `ungranted-use`     | a permission was used that was never granted     | the export is stale, or a side channel     |

The first three ask you to consider removing access, and the window label tells
you how much confidence the observation carries. The fourth is different: it is
not about removing access, it is a signal that your entitlement export does not
match reality. Either the export was captured before a grant that has since been
made, or something is exercising a permission through a path the entitlement
system does not see. Both are worth knowing before you trust any of the other
findings.


## The algorithm and its hard edge

The core comparison is a set difference per principal: granted permissions minus
exercised permissions equals unused permissions. That part is simple. The hard
edge is deciding when the set difference is allowed to mean anything.

GrantDecay uses a minimum window, default 30 days, set in `window.py`. When the
observation window is shorter than the minimum, the three absence-based finding
kinds are suppressed entirely and the report says `conclusive: no`. Only
`ungranted-use` survives, because it depends on presence of use, which a short
window can still establish.

This is deliberately conservative. A 30 day default will miss a permission that
is only exercised quarterly, and that is the point: it is better to under-report
unused surface than to recommend removing a permission that a longer window would
have shown to be in use. The 30 day figure is a policy choice, not a measurement,
and you can override it with `--min-days`.

The narrowable-role check has its own edge. A role is narrowable when some
permission it confers was exercised by none of its holders. A role held only by a
dormant principal would therefore look narrowable for every one of its
permissions, which double-reports the same fact already captured by the dormant
principal finding. The bundled sample avoids this by giving the billing role a
second, active holder, so the role and the dormant principal are reported
independently. See the design notes below.


## Worked walkthrough, one principal end to end

Follow `svc-web` through the sample run.

In `samples/entitlements.txt`, `svc-web` is granted two roles:

```
grant svc-web    deploy read
```

The `deploy` role confers three permissions and `read` confers two:

```
role deploy   deploy:push deploy:promote deploy:rollback
role read     repo:read logs:read
```

Expansion unions those into the effective set of five permissions: `deploy:push`,
`deploy:promote`, `deploy:rollback`, `logs:read`, `repo:read`.

In `samples/accesslog.txt`, `svc-web` produces six events inside the window, but
they only ever name four distinct permissions: push, promote, repo:read, and
logs:read. It never exercises `deploy:rollback`.

So the surface for `svc-web` is granted 5, exercised 4, unused 1:

```
svc-web granted=5 exercised=4 unused=1
```

That single unused permission, `deploy:rollback`, becomes an `unused-permission`
finding against `svc-web`. Because no other holder of the `deploy` role exercised
rollback either, the same permission also produces a `narrowable-role` finding
against `deploy`. Two findings, one root cause, reported at the two levels where
a reviewer might act.


## Commands

| Command   | Arguments                              | Purpose                                 |
| --------- | -------------------------------------- | --------------------------------------- |
| `surface` | entitlements, accesslog                | granted versus exercised per principal  |
| `unused`  | entitlements, accesslog, `--min-days`  | each finding on its own line            |
| `report`  | entitlements, accesslog, `--min-days`  | grouped report of the four kinds        |
| `version` | none                                   | print the version                       |

### surface

Command:

```
python -m grantdecay surface samples/entitlements.txt samples/accesslog.txt
```

Output captured in this session:

```
# surface for window 2026-06-01..2026-07-01 (31 days)
# principal granted exercised unused
svc-batch granted=2 exercised=0 unused=2
svc-finance granted=2 exercised=2 unused=0
svc-oncall granted=2 exercised=2 unused=0
svc-web granted=5 exercised=4 unused=1
```

### unused

Command:

```
python -m grantdecay unused samples/entitlements.txt samples/accesslog.txt
```

Output captured in this session:

```
dormant-principal svc-batch [billing:export,billing:view] window=2026-06-01..2026-07-01 (31 days)
narrowable-role role:deploy [deploy:rollback] window=2026-06-01..2026-07-01 (31 days)
ungranted-use svc-oncall [repo:read] window=2026-06-01..2026-07-01 (31 days)
unused-permission svc-web [deploy:rollback] window=2026-06-01..2026-07-01 (31 days)
```

### version

Command:

```
python -m grantdecay version
```

Output captured in this session:

```
grantdecay 0.1.0
```


## The unused surface, drawn from this run

![Grouped bar chart of granted versus exercised permission counts for the four
sample principals. svc-batch has 2 granted and 0 exercised, svc-finance 2 and 2,
svc-oncall 2 and 2, svc-web 5 granted and 4 exercised. Amber ticks mark the
unused gap on svc-batch and svc-web.](docs/assets/unused-surface.svg)

The bars are the exact numbers the `surface` command printed above. Slate is
granted, green is exercised, and the amber tick marks the unused gap. svc-batch
is the visibly dormant case: a full granted bar with no exercised bar at all.


## Exit codes

| Code | Meaning                                            |
| ---- | -------------------------------------------------- |
| 0    | clean, no findings                                 |
| 1    | findings present                                   |
| 2    | usage error, including a malformed input file      |

The `surface` command exits 1 when any principal has unused permissions. The
`unused` and `report` commands exit 1 when any finding is present. A malformed
entitlement or access log file exits 2 with a diagnostic on stderr naming the
file and line.


## Determinism

Identical input produces byte-identical output. Findings are sorted by kind, then
principal, then role, then permission tuple. Permissions within a finding are
sorted. There is no wall-clock time or randomness in any output. The window dates
that appear come only from the access log header, never from the system clock.


## Repository layout

```
grantdecay/
  README.md                 this file
  LICENSE                   MIT, holder "the grantdecay authors", 2026
  CHANGELOG.md              release notes
  .gitignore                Python ignores
  pyproject.toml            setuptools, src layout, console script
  src/grantdecay/
    __init__.py             package version
    __main__.py             enables python -m grantdecay
    cli.py                  argparse subcommands: surface, unused, report, version
    entitlement.py          parse the entitlement export, expand roles
    accesslog.py            parse the access log export and its window
    window.py               the observation window and the minimum-window guard
    decay.py                the four finding kinds and the analysis
    report.py               line-oriented renderers for each command
  tests/
    test_grantdecay.py      stdlib unittest suite
  samples/
    entitlements.txt        authored entitlement test vector
    accesslog.txt           authored access log test vector
    README.md               how the fixtures were constructed
  docs/assets/
    logo.svg                wordmark
    unused-surface.svg      granted versus exercised bar chart from this run
```


## Glossary

| Term          | Meaning in GrantDecay                                            |
| ------------- | --------------------------------------------------------------- |
| principal     | an identity that holds grants: a user or a service account      |
| role          | a named bundle of permissions                                   |
| permission    | an opaque action string, for example `deploy:push`              |
| grant         | the assignment of one or more roles to a principal              |
| effective set | the union of all permissions a principal holds through its roles |
| exercised     | a permission that appears in the access log for a principal     |
| window        | the inclusive date range the access log claims to cover         |
| conclusive    | the window met the minimum length, so absence findings are made |
| dormant       | a principal that exercised none of its permissions              |


## Design decisions

### A minimum window instead of a confidence score

The rejected alternative was to attach a confidence percentage to each unused
finding based on window length. That would have looked more precise and been
less honest: a percentage invites a reader to act on a low-confidence finding
anyway. A hard threshold that suppresses absence findings below the minimum
forces the question, do you have enough observation, before any recommendation
appears. The cost is bluntness. A 29 day window reports nothing absence-based
even though it is barely short. That bluntness is the point.

### Separating ungranted-use from the absence findings

Ungranted-use could have been folded in as a fifth column of the surface. It was
kept separate because it depends on the opposite kind of evidence. The three
absence findings get weaker as the window shrinks; ungranted-use does not,
because seeing an event is proof the event happened regardless of window length.
Mixing evidence that strengthens with observation and evidence that does not
under one heading would blur the one distinction the tool most wants to make.

### Roles expand, permissions stay opaque

GrantDecay expands roles to permissions but treats each permission as an opaque
string. The rejected alternative was to model permission structure: wildcards,
hierarchies, resource scoping. That is where real entitlement systems differ
most from each other, and modelling it would have tied the tool to one provider
and multiplied the ways it could be subtly wrong. An opaque string that either
matches or does not is portable and cannot be quietly incorrect.


## Verification

All four checks required by the project standard were run in this session.

Test suite:

```
python -m unittest discover -s tests -v
```

The suite reports:

```
Ran 28 tests in 0.006s

OK
```

The 28 tests cover window length and endpoint logic, the conclusiveness
threshold, entitlement parsing and role expansion, rejection of malformed and
inconsistent records, access log parsing and window enforcement, the surface
counts, all four finding kinds, suppression of absence findings on a short
window, deterministic ordering, and every CLI subcommand with its exit code.

The CLI was run end to end against `samples/`, and the output blocks above are
the verbatim result. Both SVGs under `docs/assets/` parse as XML. A search of
the whole project for the em dash character returns nothing.


## Limitations and roadmap

The limitations are structural, not temporary. GrantDecay reads two files and
compares strings. It has no view of permission hierarchies, of time-bound or
conditional grants, or of why a permission is held. The minimum window will miss
rarely-exercised permissions by design, and a permission exercised once counts
the same as one exercised constantly.

Possible future work, without dates or promises: an input adapter for a common
entitlement export format; a per-permission last-seen date so the report can show
how long a permission has been dormant rather than a binary used-or-not; and an
option to treat a permission exercised only near a window boundary as low
confidence, since a single edge event is weak evidence of ongoing need.


## The mark

<img src="docs/assets/logo.svg" width="200"
     alt="Wordmark reading GrantDecay, with grant in slate ink and decay in
     amber, split at the compound word boundary." />

The wordmark splits the name at its morpheme boundary. "grant" is set in slate,
the colour this project uses for privilege as issued. "decay" is set in the amber
accent, the same colour the bar chart uses to mark the unused gap. The split
carries the whole idea of the tool: a grant that was correct when made loses
relevance as it goes unexercised, and GrantDecay measures that gap. There is no
pictorial mark because the tool's output is a list of findings, and a wordmark
represents that honestly without inventing geometry.


## License

MIT. See [LICENSE](LICENSE).

<!-- draft note 411 -->
