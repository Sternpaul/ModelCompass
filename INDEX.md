# ModelCompass (machine-readable)

_Generated 2026-08-16T22:05:53Z — 407 models. Daily GitHub Action._

## Sources

- **openrouter**: ok (413 raw)
- **artificial_analysis**: ok (608 models)
- **aider_polyglot**: ok (54 models)

## Coverage

- with_aa_benchmarks: 150
- with_aider_coding: 36

## Recommended shortlists (real benchmarks)

### best_overall

- `anthropic/claude-fable-5` (score 0.693)
- `x-ai/grok-4.6` (score 0.6885)
- `openai/gpt-5-codex:batch` (score 0.6785)
- `openai/gpt-5.2` (score 0.678)
- `openai/gpt-5.6-sol` (score 0.6725)
- `google/gemini-3.7-flash` (score 0.6605)
- `anthropic/claude-opus-4.8` (score 0.658)
- `openai/gpt-5.1-codex-max` (score 0.6565)

### best_coding

- `openai/gpt-5.2` (score 0.894)
- `openai/gpt-5.1-codex-max` (score 0.849)
- `openai/gpt-5-codex:batch` (score 0.84)
- `openai/gpt-5.1-codex-mini` (score 0.836)
- `minimax/minimax-m2` (score 0.826)
- `minimax/minimax-m2.1` (score 0.81)
- `openai/gpt-5-nano` (score 0.789)
- `openai/gpt-5.6-sol` (score 0.772)

### best_reasoning

- `anthropic/claude-fable-5` (score 0.7007)
- `x-ai/grok-4.6` (score 0.6623)
- `google/gemini-3.7-flash` (score 0.6613)
- `anthropic/claude-opus-4.8` (score 0.66)
- `openai/gpt-5.6-sol` (score 0.6537)
- `qwen/qwen3.8-max` (score 0.646)
- `qwen/qwen3.8-2.4t-a95b` (score 0.6453)
- `meta/muse-spark-1.2` (score 0.6423)

### best_math

- `perplexity/sonar-reasoning-pro` (score 0.8737)
- `openai/o4-mini-high` (score 0.8252)
- `openai/gpt-5` (score 0.809)
- `openai/o3` (score 0.7971)
- `google/gemini-2.5-pro` (score 0.7897)
- `z-ai/glm-4.5` (score 0.7342)
- `openai/gpt-5.2` (score 0.7145)
- `openai/o3-mini-high` (score 0.7141)

### best_agents

- `minimax/minimax-m3` (score 0.8286)
- `x-ai/grok-4.3` (score 0.8129)
- `qwen/qwen3.7-max` (score 0.8054)
- `xiaomi/mimo-v2.5-pro` (score 0.7986)
- `qwen/qwen3.5-397b-a17b` (score 0.7878)
- `qwen/qwen3.7-plus` (score 0.7796)
- `openai/gpt-5.2-codex` (score 0.7762)
- `google/gemini-3.1-flash-lite-preview` (score 0.7721)

### best_open_weight

- `qwen/qwen3.8-2.4t-a95b` (score 0.648)
- `deepseek/deepseek-v4-pro` (score 0.61)
- `moonshotai/kimi-k3` (score 0.6015)
- `minimax/minimax-m3` (score 0.52)
- `moonshotai/kimi-k2.7-code` (score 0.519)
- `xiaomi/mimo-v2.5-pro` (score 0.5155)
- `nex-agi/nex-n2-pro` (score 0.504)
- `z-ai/glm-5.1` (score 0.484)

### best_vision

- `anthropic/claude-fable-5` (score 0.693)
- `x-ai/grok-4.6` (score 0.6885)
- `openai/gpt-5-codex:batch` (score 0.6785)
- `openai/gpt-5.2` (score 0.678)
- `openai/gpt-5.6-sol` (score 0.6725)
- `google/gemini-3.7-flash` (score 0.6605)
- `anthropic/claude-opus-4.8` (score 0.658)
- `openai/gpt-5.1-codex-max` (score 0.6565)

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
