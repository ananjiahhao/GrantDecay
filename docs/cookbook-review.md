# Cookbook: an access review with evidence

Quarterly reviews usually ask "who still needs this". GrantDecay answers the
narrower, useful question: what was never exercised in the window.

## 1. Point it at the inventory and the log

```
python -m grantdecay decay samples/entitlements.txt --log samples/accesslog.txt --window 31d
```

The report lists each entitlement with a verdict and the last matching access
line when one exists.

## 2. Read unused before unknown

An unused verdict is evidence: the grant exists and the window has no match.
An unknown verdict means the data could not answer, for example an empty log.

## 3. Attach the verdict list to the review

Verdicts are deterministic, so the attachment is comparable between quarters.
