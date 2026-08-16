# ModelCompass (machine-readable)

_Generated 2026-08-16T18:10:01Z from OpenRouter /api/v1/models (407 models). Updated daily._

## Recommended shortlists (heuristic — see disclaimer)

### best_overall

- `x-ai/grok-4.20`
- `openai/gpt-5.6-luna-pro`
- `openai/gpt-5.6-luna`
- `openai/gpt-5.6-terra-pro`
- `openai/gpt-5.6-terra`

### best_reasoning

- `x-ai/grok-4.20`
- `openai/gpt-5.6-luna-pro`
- `openai/gpt-5.6-luna`
- `openai/gpt-5.6-terra-pro`
- `openai/gpt-5.6-terra`

### best_coding

- `x-ai/grok-4.20`
- `openai/gpt-5.6-luna-pro`
- `openai/gpt-5.6-luna`
- `openai/gpt-5.6-terra-pro`
- `openai/gpt-5.6-terra`

### best_vision

- `x-ai/grok-4.20`
- `openai/gpt-5.6-luna-pro`
- `openai/gpt-5.6-luna`
- `openai/gpt-5.6-terra-pro`
- `openai/gpt-5.6-terra`

### best_agents

- `x-ai/grok-4.20`
- `openai/gpt-5.6-luna-pro`
- `openai/gpt-5.6-luna`
- `openai/gpt-5.6-terra-pro`
- `openai/gpt-5.6-terra`

### best_open_weight

- `qwen/qwen3.8-2.4t-a95b`
- `deepseek/deepseek-v4-pro-0813`
- `nvidia/nemotron-3.5-lightning`
- `deepseek/deepseek-v4-flash-0731`
- `thinkingmachines/inkling`

### best_cheap

- `inclusionai/ling-3.0-flash`
- `nex-agi/nex-n2-mini`
- `qwen/qwen3.7-flash`
- `upstage/solar-pro4`
- `openai/gpt-oss-120b`

### best_audio

- `google/gemini-3.5-flash`
- `google/gemini-3.7-flash`
- `meta/muse-spark-1.2`
- `google/gemini-3.6-flash`
- `google/gemini-3.5-flash-lite`

### best_image_generation

- `google/gemini-3-pro-image`
- `google/gemini-3.1-flash-lite-image`
- `openai/gpt-5.4-image-2`
- `google/gemini-3.1-flash-image`
- `openai/gpt-5-image-mini`

## Leaderboards (factual / sortable)

- **cheapest_by_prompt**: 389 models — top: `inclusionai/ling-2.6-flash`, `ibm-granite/granite-4.0-h-micro`, `mistralai/mistral-nemo`, `inclusionai/ling-3.0-flash`, `nex-agi/nex-n2-mini`
- **cheapest_by_completion**: 389 models — top: `inclusionai/ling-2.6-flash`, `mistralai/mistral-nemo`, `sao10k/l3-lunaris-8b`, `gryphe/mythomax-l2-13b`, `inclusionai/ling-3.0-flash`
- **largest_context**: 407 models — top: `x-ai/grok-4.20-multi-agent`, `x-ai/grok-4.20`, `meta-llama/llama-4-scout`, `openai/gpt-5.6-luna-pro`, `openai/gpt-5.6-luna-pro:batch`
- **newest**: 407 models — top: `qwen/qwen3.8-27b`, `dots-studio/dots-3-note-preview:free`, `google/gemini-3.7-flash`, `google/gemini-3.7-flash:batch`, `bytedance-seed/seed-2-1-turbo`
- **vision**: 242 models — top: `qwen/qwen3.8-27b`, `dots-studio/dots-3-note-preview:free`, `google/gemini-3.7-flash`, `google/gemini-3.7-flash:batch`, `bytedance-seed/seed-2-1-turbo`
- **audio**: 38 models — top: `google/gemini-3.7-flash`, `google/gemini-3.7-flash:batch`, `meta/muse-spark-1.2`, `thinkingmachines/inkling-small`, `google/gemini-3.6-flash`
- **image_generation**: 9 models — top: `google/gemini-3.1-flash-lite-image`, `google/gemini-3.1-flash-image`, `google/gemini-3-pro-image`, `openai/gpt-5.4-image-2`, `google/gemini-3.1-flash-image-preview`
- **supports_reasoning**: 279 models — top: `qwen/qwen3.8-27b`, `dots-studio/dots-3-note-preview:free`, `google/gemini-3.7-flash`, `google/gemini-3.7-flash:batch`, `bytedance-seed/seed-2-1-turbo`
- **supports_tools**: 343 models — top: `qwen/qwen3.8-27b`, `dots-studio/dots-3-note-preview:free`, `google/gemini-3.7-flash`, `google/gemini-3.7-flash:batch`, `bytedance-seed/seed-2-1-turbo`
- **open_weight**: 165 models — top: `qwen/qwen3.8-27b`, `qwen/qwen3.8-2.4t-a95b`, `deepseek/deepseek-v4-pro-0813`, `liquid/lfm-2.5-2.6b:free`, `nvidia/nemotron-3.5-lightning`

## Disclaimer

Category 'recommended' lists are metadata-derived HEURISTICS (capability flags + recency + price class), NOT benchmark verdicts. OpenRouter exposes no benchmark scores. Use them as a sane default when your training cutoff is stale; verify with live benchmarks before high-stakes choices.

## Methodology

cap_score = 2*reasoning + 1*tools + 0.5*json + 0.3*cache + min(context/1M,2) + max(0, 2*(1-age/365)) + 0.5*knowledge_cutoff. Recommended lists sort filtered models by cap_score (or price). Full per-model metadata is in models.json for agent-side scoring.
