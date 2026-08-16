# ModelCompass (machine-readable)

_Generated 2026-08-16T18:27:36Z — 407 models. Daily GitHub Action._

## Sources

- **openrouter**: ok (413 raw)
- **artificial_analysis**: ok (608 models)
- **aider_polyglot**: ok (54 models)
- **hf_openllm**: ok (0 matched)

## Coverage

- with_aa_benchmarks: 44
- with_aider_coding: 36
- with_hf_openllm: 0

## Recommended shortlists (real benchmarks)

### best_overall

- `anthropic/claude-opus-5` (score 0.7055)
- `anthropic/claude-fable-5` (score 0.693)
- `anthropic/claude-sonnet-5` (score 0.634)
- `deepseek/deepseek-v4-pro` (score 0.61)
- `deepseek/deepseek-v4-flash` (score 0.6045)
- `anthropic/claude-opus-5-fast` (score 0.597)
- `openai/o3` (score 0.597)
- `openai/o4-mini` (score 0.584)

### best_coding

- `openai/o4-mini` (score 0.859)
- `minimax/minimax-m2` (score 0.826)
- `openai/gpt-5-nano` (score 0.789)
- `anthropic/claude-opus-5` (score 0.78)
- `anthropic/claude-fable-5` (score 0.765)
- `nvidia/nemotron-nano-9b-v2:free` (score 0.724)
- `openai/o3-mini` (score 0.717)
- `deepseek/deepseek-v4-flash` (score 0.691)

### best_reasoning

- `anthropic/claude-opus-5` (score 0.704)
- `anthropic/claude-fable-5` (score 0.7007)
- `anthropic/claude-sonnet-5` (score 0.6257)
- `deepseek/deepseek-v4-pro` (score 0.6233)
- `anthropic/claude-opus-5-fast` (score 0.616)
- `openai/gpt-5` (score 0.6122)
- `deepseek/deepseek-v4-flash` (score 0.604)
- `minimax/minimax-m3` (score 0.591)

### best_math

- `perplexity/sonar-reasoning-pro` (score 0.8737)
- `openai/gpt-5` (score 0.8307)
- `openai/o4-mini` (score 0.8252)
- `openai/o3` (score 0.7971)
- `openai/o3-mini-high` (score 0.7476)
- `openai/o3-mini` (score 0.7141)
- `openai/o1` (score 0.6838)
- `deepseek/deepseek-r1` (score 0.6716)

### best_agents

- `minimax/minimax-m3` (score 0.8286)
- `openai/gpt-5-mini` (score 0.7544)
- `openai/gpt-5` (score 0.7306)
- `minimax/minimax-m2` (score 0.7231)
- `openai/o3` (score 0.7143)
- `upstage/solar-pro-3` (score 0.712)
- `openai/o1` (score 0.7034)
- `inception/mercury-2` (score 0.698)

### best_open_weight

- `deepseek/deepseek-v4-pro` (score 0.532)
- `deepseek/deepseek-v4-flash` (score 0.518)
- `minimax/minimax-m3` (score 0.454)
- `tencent/hy3` (score 0.422)
- `inclusionai/ling-3.0-flash` (score 0.378)
- `minimax/minimax-m2` (score 0.289)
- `openai/gpt-oss-120b` (score 0.241)
- `deepseek/deepseek-r1` (score 0.186)

### best_vision

- `anthropic/claude-opus-5` (score 0.7055)
- `anthropic/claude-fable-5` (score 0.693)
- `anthropic/claude-sonnet-5` (score 0.634)
- `anthropic/claude-opus-5-fast` (score 0.597)
- `openai/o3` (score 0.597)
- `openai/o4-mini` (score 0.584)
- `openai/gpt-5` (score 0.558)
- `minimax/minimax-m3` (score 0.52)

### best_cheap

- `inclusionai/ling-3.0-flash` (score 0.442)
- `nex-agi/nex-n2-mini`
- `openai/gpt-5-nano:batch`
- `openai/gpt-oss-120b` (score 0.493)
- `upstage/solar-pro4` (score 0.4715)
- `openai/gpt-oss-20b` (score 0.4173)
- `qwen/qwen3.7-flash`
- `nvidia/nemotron-3-nano-30b-a3b` (score 0.1025)

## Disclaimer
Recommended lists are transparent weighted blends of REAL benchmark values (Artificial Analysis indices + raw benchmarks, aider polyglot coding, HF OpenLLM academic). Models missing a benchmark contribute null (not zero). Verify high-stakes choices against primary sources.

## Methodology
Each task score = weighted mean of available normalized 0-1 benchmarks (AA indices /100; GPQA/HLE/LiveCodeBench/AIME/Math-500/SciCode already 0-1; aider pass_rate /100; HF academic averaged). Sources merged by provider+slug then name fuzzy-match. Variant families collapsed to canonical base model in shortlists.
