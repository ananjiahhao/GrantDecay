# JSON output fields

`decay` and `window` accept `--json`.

| Field | Type | Meaning |
|---|---|---|
| principal | string | Account or service name |
| resource | string | What the entitlement grants |
| granted | string | Grant date, ISO 8601 |
| verdict | string | used, unused, or unknown |
| last_match | string or null | Timestamp of the last matching access line |
| unused_days | integer or null | Window days with no match |
| window_start | string | Observation window start |
| window_end | string | Observation window end |

Null means the data did not support an answer; the tool never guesses.
