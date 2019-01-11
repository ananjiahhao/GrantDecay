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
