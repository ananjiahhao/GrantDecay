# Sample fixtures

These two files are hand-authored test vectors, not exports from a real identity
system. They exist to exercise every finding kind in one run. Nothing here is
presented as production data.

## entitlements.txt

Four roles and four principals, constructed so each finding kind fires once:

- `deploy` confers `deploy:push`, `deploy:promote`, `deploy:rollback`. No holder
  exercises `deploy:rollback` in the window, so the role is narrowable.
- `billing` is held by `svc-batch` (dormant) and `svc-finance` (active).
