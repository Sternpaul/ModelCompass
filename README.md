# ModelCompass (agent-readable)

A daily-updated, machine-readable catalog of AI models, intended to be loaded
by an agent **instead of** re-searching the web when its training cutoff is
stale. Say *"give me the best coding model"* and the agent reads
`recommended.json` / `models.json` instantly.

## Data source

Live **OpenRouter** `/api/v1/models` catalog (currently ~400+ models). Updated
daily via GitHub Actions (see `.github/workflows/update.yml`).

## Files

| File | Purpose |
|------|---------|
| `models.json` | Full catalog: metadata + categorical leaderboards + heuristics |
| `recommended.json` | Just the per-task shortlists (small, fast to load) |
| `models.csv` | Flat spreadsheet/grep-friendly view |
| `INDEX.md` | Human-readable summary |

## For agents

Load **`recommended.json`** (tiny) for "best X" answers. For comparisons or
custom scoring, load **`models.json`** and filter on fields like `price_per_million`,
`context`, `is_vision`, `supports_reasoning`, `knowledge_cutoff`, `age_days`.

Example: "compare openai/gpt-5.2 vs anthropic/claude-opus-4.5 for agents" →
look both up in `models.json["models"]` and compare `context`, `price_per_million`,
`supports_tools`, `supports_reasoning`, `knowledge_cutoff`.

## Honest scope

OpenRouter exposes rich **metadata** (pricing, context, modalities, supported
params, knowledge cutoff, recency) but **not benchmark scores**. Therefore the
`recommended` lists are transparent **metadata-derived heuristics** (capability
flags + recency + price class), clearly labeled as such — they are a sane
default for a stale agent, not a benchmark verdict. Benchmark ingestion is a
future extension point (the `models` array is the natural place to add a
`benchmarks` object per model).

`cap_score` formula is documented in `models.json > meta.methodology`.

## Variant handling

OpenRouter lists many *derived* variants of the same model (`:batch` pricing,
`:free` tier, `-preview`, `-latest`, versioned snapshots). For the **shortlists**
(`recommended.*`) these are collapsed by model **family**: only the canonical
base model is listed (variants are scored slightly lower so the base wins the
tie). The full raw catalog in `models.json["models"]` keeps every variant
untouched — useful for exact pricing/availability lookups.
