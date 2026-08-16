# Weekly Archive

Immutable weekly snapshots of the `recommended.json` rankings, preserved for
historical comparison. A new file is written every Monday at 04:00 UTC by the
`archive.yml` GitHub Action, starting from the week this folder was created.

## File format

Each snapshot is `rankings-YYYY-Www.json` (ISO week number), e.g.
`rankings-2026-W33.json`. Contents:

```json
{
  "week": "2026-W33",
  "generated_at": "2026-08-16T04:00:00Z",
  "model_count": 407,
  "recommended": { "best_overall": [...], "best_coding": [...], ... }
}
```

The `recommended` object is the exact same shape as `recommended.json` at that
point in time — so you can diff any two weeks to see how the leaderboard moved.
