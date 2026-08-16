# ModelCompass (agent-readable)

A daily-updated, machine-readable catalog of AI models with **real benchmark
scores**, built so an agent can answer *"what's the best coding model?"* or
*"compare these two for my project"* **instantly** — instead of web-searching
with a stale knowledge cutoff.

## How it works

A GitHub Action (`.github/workflows/update.yml`) runs daily at **04:00 UTC**
(+ manual `workflow_dispatch`) and regenerates the dataset from live sources:

| Source | Auth | What it contributes |
|--------|------|---------------------|
| **OpenRouter** `/api/v1/models` | none | 400+ models: pricing, context window, modalities (vision/audio/image), capability flags (reasoning, tools, JSON, caching), knowledge cutoff, recency |
| **Artificial Analysis API v2** | `ARTIFICIAL_ANALYSIS_KEY` | Intelligence / Coding / Agentic / Math / Multilingual / Openness indices + raw benchmarks (GPQA, HLE, MMLU-Pro, AIME, LiveCodeBench, Terminal-Bench, IFBench, SciCode…) + speed |
| **aider polyglot** (raw GitHub YAML) | none | Real coding benchmark: 225 Exercism exercises across 6 languages → pass rates |

All sources are fetched defensively — a failure in one never breaks the others.
`meta.sources` in the output reports exactly what succeeded.

Sources are merged into unified model records by **provider + slug**, then fuzzy
name match. Models present in one source but not another simply carry `null`
for that source's benchmarks (no zero-filling). Variant families (`:batch`,
`:free`, `-preview`, …) are collapsed so shortlists show the canonical base
model only.

## Scoring (transparent, real benchmarks)

Each task score is a documented **weighted mean of real benchmark values**:
all normalized to 0–1 (AA indices ÷100; GPQA/HLE/LiveCodeBench/AIME already
0–1; aider `pass_rate_1` ÷100). Missing benchmarks contribute `null`, not zero.
Full formula in `meta.methodology`.

| Task | Benchmarks used |
|------|-----------------|
| `best_overall` | AA intelligence + coding + agentic + math + multilingual |
| `best_coding` | AA coding index, LiveCodeBench, aider polyglot |
| `best_reasoning` | AA intelligence, GPQA, AIME, HLE |
| `best_math` | AA math, AIME, Math-500, SciCode |
| `best_agents` | AA agentic, Terminal-Bench, IFBench |
| `best_open_weight` | AA intelligence + openness + coding indices (open-weight only) |
| `best_vision` | overall score, filtered to vision-capable |
| `best_cheap` | price ascending, capability as tiebreak |

## Files

| File | Purpose |
|------|---------|
| `models.json` | Full catalog: every model with raw benchmarks, pricing, metadata, per-task scores |
| `recommended.json` | Just the per-task shortlists with their benchmark evidence (small, fast to load) |
| `models.csv` | Flat spreadsheet / grep-friendly view |
| `LEADERBOARD.md` | **Human-readable leaderboard** — comparison tables per task, best for viewing directly on GitHub |
| `INDEX.md` | Machine-oriented summary (regenerated each run) |
| `rankings/` | Curated **famous rankings** — top models per famous benchmark (see below) |
| `archive/` | Immutable **weekly snapshots** of `recommended.json`, one file per ISO week |

### `rankings/` — famous rankings

`rankings/famous_rankings.md` (and `.json`) list the most famous model
benchmarks and, for each, the current top models drawn from live data:

- Artificial Analysis Intelligence Index
- Coding (aider polyglot + LiveCodeBench)
- Math (AIME / MMLU-Pro / SciCode)
- Reasoning (GPQA / HLE)
- Agentic (Terminal-Bench / AA agentic)
- Vision
- Best value (low cost)
- Open-weight

### `archive/` — weekly history

Every Monday at 04:00 UTC, `archive.yml` writes `archive/rankings-YYYY-Www.json`
— a point-in-time copy of `recommended.json`. Diff any two weeks to see how the
leaderboard moved. See `archive/README.md`.

## For humans

Open **`LEADERBOARD.md`** for a clean, GitHub-rendered table of the best models
per task (score, price, context, and the benchmark evidence behind each rank).
It's the same data as `recommended.json`, just formatted for reading.

## For agents

- **"best X"** → load `recommended.json`, read `recommended["best_coding"][0]`.
  Each entry includes `task_score` and the contributing `benchmarks`, so the
  agent can explain *why*.
- **"compare A vs B"** → load both from `models.json["models"]`, return a
  side-by-side of `benchmarks`, `price_per_million`, `context`, capability flags.

Example: *"compare openai/gpt-5.2 vs anthropic/claude-opus-4.5 for agents"* →
look both up, compare `benchmarks.aa_agentic_index`, `terminal_bench`,
`price_per_million`, `context`, `supports_tools`.

## Setup

1. Create a free key at https://artificialanalysis.ai/login → API key.
2. Add it as a **repo secret** named `ARTIFICIAL_ANALYSIS_KEY`.
   (Free tier: 100 requests/day — one request fetches all models, well within limits.)
3. The Actions run automatically. Trigger manually with
   `gh workflow run update.yml` (daily) or `gh workflow run archive.yml` (weekly).

No SSH keys, no tokens in URLs. The jobs use GitHub's built-in `GITHUB_TOKEN`.

## Honest caveats

- Benchmarks are point-in-time; the daily job keeps them current.
- Rankings are transparent blends of real metrics — verify high-stakes choices
  against primary sources. They are a sane default for a stale agent, not a
  single authoritative verdict.
