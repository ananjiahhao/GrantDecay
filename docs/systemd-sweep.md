# Recipe: a systemd timer for a monthly sweep

`/etc/systemd/system/grant-decay.service`:

```ini
[Unit]
Description=Monthly entitlement decay sweep

[Service]
Type=oneshot
WorkingDirectory=/opt/review
ExecStart=/usr/bin/python3 -m grantdecay decay entitlements.txt --log access.log --window 31d --json
SuccessExitStatus=0 1
```

`SuccessExitStatus=0 1` treats findings as a successful run; the report is
the signal. Pair it with a monthly timer aligned to the review calendar.
