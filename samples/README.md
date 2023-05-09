# Sample fixtures

These two files are hand-authored test vectors, not exports from a real identity
system. They exist to exercise every finding kind in one run. Nothing here is
presented as production data.

## entitlements.txt

Four roles and four principals, constructed so each finding kind fires once:

- `deploy` confers `deploy:push`, `deploy:promote`, `deploy:rollback`. No holder
  exercises `deploy:rollback` in the window, so the role is narrowable.
- `billing` is held by `svc-batch` (dormant) and `svc-finance` (active).
  Because svc-finance exercises both billing permissions, the billing role
  itself is not narrowable, leaving `deploy` as the only narrowable role.
- `svc-batch` records no events, so that principal is fully dormant.
- `svc-oncall` holds the `oncall` role but exercises `repo:read`, which no role
  grants it, producing an ungranted-use finding.

## accesslog.txt

A 31 day window (2026-06-01 to 2026-07-01 inclusive), chosen to sit one day over
the 30 day default minimum so the run is conclusive. Events were written by hand
to match the entitlement design above:

- `svc-web` exercises push, promote, and both reads, but never rollback.
- `svc-batch` has no events.
- `svc-oncall` exercises its granted permissions plus `repo:read`.

To regenerate the numbers quoted in the README, run the CLI against these two
