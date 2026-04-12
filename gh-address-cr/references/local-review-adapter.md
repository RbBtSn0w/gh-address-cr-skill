# Local Review Adapter Contract

`run_local_review.sh` executes an adapter command and expects a JSON array on stdout.

## Required fields per finding

- `title`
- `body`
- `path`
- `line`

## Optional fields

- `start_line`
- `end_line`
- `severity`
- `category`
- `confidence`
- `head_sha`

## Example

```json
[
  {
    "title": "Missing nil guard",
    "body": "The result of fetch_user may be null here.",
    "path": "src/service.py",
    "line": 33,
    "severity": "P1",
    "category": "correctness",
    "confidence": "high"
  }
]
```

## Notes

- The adapter should not mutate repo state.
- The adapter should not post directly to GitHub.
- `gh-address-cr` assigns stable local item ids and stores them in the PR session.
