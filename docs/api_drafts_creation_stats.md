# `/api/drafts/creation-stats` frontend quick doc

## What changed
- Endpoint supports timezone-aware grouping by local calendar day.
- Query param: `timezone` (IANA timezone name).

## Request
- Method: `GET`
- URL: `/api/drafts/creation-stats`
- Query params:
  - `timezone` (optional, `string`, default: `UTC`)
  - Examples: `UTC`, `America/Los_Angeles`, `Europe/Berlin`

## Behavior
- Drafts are grouped by `created_at` date in the requested timezone.
- If `timezone` is omitted, grouping is done in `UTC`.

## Success response
- `200 OK`
- Body:
```json
[
  { "date": "2024-01-01", "count": 2 },
  { "date": "2024-01-02", "count": 1 }
]
```

## Error response
- `400 Bad Request` when timezone is invalid.
- Body:
```json
{ "detail": "Invalid timezone" }
```

## Frontend recommendation
- Always send user's IANA timezone:
```js
const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
// GET /api/drafts/creation-stats?timezone=${encodeURIComponent(tz)}
```
