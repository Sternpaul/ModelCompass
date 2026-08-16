# ModelCompass (machine-readable)

_Generated 2026-08-16T21:44:18Z — 407 models. Daily GitHub Action._

## Sources

- **openrouter**: ok (413 raw)
- **artificial_analysis**: ok (608 models)
- **aider_polyglot**: ok (54 models)

## Coverage

- with_aa_benchmarks: 92
- with_aider_coding: 36

## Recommended shortlists (real benchmarks)

### best_overall

- `anthropic/claude-fable-5` (score 0.693)
- `openai/gpt-5-codex:batch` (score 0.6785)
- `openai/gpt-5.2` (score 0.678)
- `openai/gpt-5.6-sol` (score 0.6725)
- `google/gemini-3.7-flash` (score 0.6605)
- `anthropic/claude-opus-4.8` (score 0.658)
- `openai/gpt-5.1-codex-max` (score 0.6565)
- `meta/muse-spark-1.2` (score 0.645)

### best_coding

- `openai/gpt-5.2` (score 0.894)
- `openai/o4-mini` (score 0.859)
- `openai/gpt-5.1-codex-max` (score 0.849)
- `openai/gpt-5-codex:batch` (score 0.84)
- `openai/gpt-5.1-codex-mini` (score 0.836)
- `minimax/minimax-m2` (score 0.826)
- `minimax/minimax-m2.1` (score 0.81)
- `openai/gpt-5-nano` (score 0.789)

### best_reasoning

- `anthropic/claude-fable-5` (score 0.7007)
- `google/gemini-3.7-flash` (score 0.6613)
- `anthropic/claude-opus-4.8` (score 0.66)
- `openai/gpt-5.6-sol` (score 0.6537)
- `meta/muse-spark-1.2` (score 0.6423)
- `meta/muse-spark-1.1` (score 0.6307)
- `openai/gpt-5.4` (score 0.6293)
- `google/gemini-3.1-pro-preview` (score 0.6293)

### best_math

- `perplexity/sonar-reasoning-pro` (score 0.8737)
- `openai/o4-mini` (score 0.8252)
- `openai/gpt-5` (score 0.809)
- `openai/o3` (score 0.7971)
- `google/gemini-2.5-pro` (score 0.7897)
- `openai/o3-mini-high` (score 0.7476)
- `openai/gpt-5.2` (score 0.7145)
- `openai/o3-mini` (score 0.7141)

### best_agents

- `minimax/minimax-m3` (score 0.8286)
- `xiaomi/mimo-v2.5-pro` (score 0.7986)
- `openai/gpt-5.2-codex` (score 0.7762)
- `google/gemini-3.1-flash-lite-preview` (score 0.7721)
- `google/gemini-3.1-pro-preview` (score 0.7714)
- `google/gemini-3.5-flash` (score 0.7633)
- `openai/gpt-5.4-nano` (score 0.7592)
- `minimax/minimax-m2.7` (score 0.7571)

### best_open_weight

- `deepseek/deepseek-v4-pro` (score 0.61)
- `minimax/minimax-m3` (score 0.52)
- `xiaomi/mimo-v2.5-pro` (score 0.5155)
- `minimax/minimax-m2.7` (score 0.4575)
- `inclusionai/ling-3.0-flash` (score 0.442)
- `stepfun/step-3.7-flash` (score 0.3525)
- `minimax/minimax-m2.5` (score 0.345)
- `tencent/hy3-preview` (score 0.344)

### best_vision

- `anthropic/claude-fable-5` (score 0.693)
- `openai/gpt-5-codex:batch` (score 0.6785)
- `openai/gpt-5.2` (score 0.678)
- `openai/gpt-5.6-sol` (score 0.6725)
- `google/gemini-3.7-flash` (score 0.6605)
- `anthropic/claude-opus-4.8` (score 0.658)
- `openai/gpt-5.1-codex-max` (score 0.6565)
- `meta/muse-spark-1.2` (score 0.645)

### best_cheap

- `inclusionai/ling-3.0-flash` (score 0.442)
- `nex-agi/nex-n2-mini`
- `openai/gpt-5-nano:batch`
- `upstage/solar-pro4` (score 0.4715)
- `openai/gpt-oss-20b` (score 0.3835)
- `openai/gpt-oss-120b` (score 0.3427)
- `qwen/qwen3.7-flash`
- `nvidia/nemotron-3-nano-30b-a3b` (score 0.1025)

## Disclaimer
Recommended lists are transparent weighted blends of REAL benchmark values (Artificial Analysis indices + raw benchmarks, aider polyglot coding). Models missing a benchmark contribute null (not zero). Verify high-stakes choices against primary sources.

## Methodology
Each task score = weighted mean of available normalized 0-1 benchmarks (AA indices /100; GPQA/HLE/LiveCodeBench/AIME/Math-500/SciCode already 0-1; aider pass_rate /100). Sources merged via normalized provider+slug (AA dots->hyphens, reasoning-effort suffixes tolerated), then fuzzy name match. Only routing aliases (:batch/:free/:thinking) collapse in shortlists; identity tags (-latest, -0813, -v2) stay distinct.
