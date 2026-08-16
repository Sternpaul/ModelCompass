# ModelCompass Leaderboard

> Generated **2026-08-16T21:40:53Z** · 407 models · updated daily by GitHub Actions.

Each table ranks the best models for a task using real benchmark data (Artificial Analysis indices + aider polyglot coding). Scores are normalized 0–1 blends; `—` means the model has no benchmark for that column.

**Sources:** openrouter (ok (413 raw)) · artificial_analysis (ok (608 models)) · aider_polyglot (ok (54 models))

**Benchmark coverage:** 44 models with Artificial Analysis scores, 36 with aider coding.

## 🏆 Best Overall

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-opus-5` | 0.7055 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 63.1 · AA-Code 78 · GPQA 0.93 · HLE 0.55 |
| 2 | `anthropic/claude-fable-5` | 0.693 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 3 | `anthropic/claude-sonnet-5` | 0.634 | 2.0 | 10.0 | 1.0M | ✅ | ✅ | AA-IQ 55.3 · AA-Code 71.5 · aider 22% · GPQA 0.91 · HLE 0.41 |
| 4 | `deepseek/deepseek-v4-pro` | 0.61 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |
| 5 | `deepseek/deepseek-v4-flash` | 0.6045 | 0.06146 | 0.12292 | 1.0M | ✅ | — | AA-IQ 51.8 · AA-Code 69.1 · GPQA 0.91 · HLE 0.39 |
| 6 | `anthropic/claude-opus-5-fast` | 0.597 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 52.5 · AA-Code 66.9 · GPQA 0.89 · HLE 0.43 |
| 7 | `openai/o3` | 0.597 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |
| 8 | `openai/o4-mini` | 0.584 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 9 | `openai/gpt-5` | 0.558 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.3 · AA-Code 37.8 · LCB 0.85 · GPQA 0.85 · HLE 0.28 · AIME 0.96 |
| 10 | `minimax/minimax-m2` | 0.536 | 0.255 | 1.02 | 205k | ✅ | — | AA-IQ 28.9 · LCB 0.83 · GPQA 0.78 · HLE 0.14 |

## 💻 Best Coding

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `openai/o4-mini` | 0.859 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 2 | `minimax/minimax-m2` | 0.826 | 0.255 | 1.02 | 205k | ✅ | — | AA-IQ 28.9 · LCB 0.83 · GPQA 0.78 · HLE 0.14 |
| 3 | `openai/gpt-5-nano` | 0.789 | 0.05 | 0.4 | 400k | ✅ | ✅ | AA-IQ 20.1 · LCB 0.79 · GPQA 0.68 · HLE 0.10 |
| 4 | `anthropic/claude-opus-5` | 0.78 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 63.1 · AA-Code 78 · GPQA 0.93 · HLE 0.55 |
| 5 | `anthropic/claude-fable-5` | 0.765 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 6 | `nvidia/nemotron-nano-9b-v2:free` | 0.724 | 0.0 | 0.0 | 128k | ✅ | — | AA-IQ 8.7 · LCB 0.72 · GPQA 0.57 · HLE 0.05 |
| 7 | `openai/o3-mini` | 0.717 | 1.1 | 4.4 | 200k | ✅ | — | AA-IQ 19.2 · LCB 0.72 · GPQA 0.75 · HLE 0.08 · AIME 0.77 |
| 8 | `deepseek/deepseek-v4-flash` | 0.691 | 0.06146 | 0.12292 | 1.0M | ✅ | — | AA-IQ 51.8 · AA-Code 69.1 · GPQA 0.91 · HLE 0.39 |
| 9 | `deepseek/deepseek-v4-pro` | 0.688 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |
| 10 | `anthropic/claude-opus-5-fast` | 0.669 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 52.5 · AA-Code 66.9 · GPQA 0.89 · HLE 0.43 |

## 🧠 Best Reasoning

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-opus-5` | 0.704 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 63.1 · AA-Code 78 · GPQA 0.93 · HLE 0.55 |
| 2 | `anthropic/claude-fable-5` | 0.7007 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 3 | `anthropic/claude-sonnet-5` | 0.6257 | 2.0 | 10.0 | 1.0M | ✅ | ✅ | AA-IQ 55.3 · AA-Code 71.5 · aider 22% · GPQA 0.91 · HLE 0.41 |
| 4 | `deepseek/deepseek-v4-pro` | 0.6233 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |
| 5 | `anthropic/claude-opus-5-fast` | 0.616 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 52.5 · AA-Code 66.9 · GPQA 0.89 · HLE 0.43 |
| 6 | `openai/gpt-5` | 0.6122 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.3 · AA-Code 37.8 · LCB 0.85 · GPQA 0.85 · HLE 0.28 · AIME 0.96 |
| 7 | `deepseek/deepseek-v4-flash` | 0.604 | 0.06146 | 0.12292 | 1.0M | ✅ | — | AA-IQ 51.8 · AA-Code 69.1 · GPQA 0.91 · HLE 0.39 |
| 8 | `minimax/minimax-m3` | 0.591 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 9 | `openai/o3-pro` | 0.589 | 20.0 | 80.0 | 200k | ✅ | ✅ | AA-IQ 33.3 · aider 44% · GPQA 0.84 |
| 10 | `openai/o3` | 0.5606 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |

## 📐 Best Math

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `perplexity/sonar-reasoning-pro` | 0.8737 | 2.0 | 8.0 | 128k | ✅ | ✅ | AA-IQ 18 · AIME 0.79 |
| 2 | `openai/gpt-5` | 0.8307 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.3 · AA-Code 37.8 · LCB 0.85 · GPQA 0.85 · HLE 0.28 · AIME 0.96 |
| 3 | `openai/o4-mini` | 0.8252 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 4 | `openai/o3` | 0.7971 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |
| 5 | `openai/o3-mini-high` | 0.7476 | 1.1 | 4.4 | 200k | ✅ | — | AA-IQ 15.7 · AA-Code 16.3 · LCB 0.73 · GPQA 0.77 · HLE 0.12 · AIME 0.86 |
| 6 | `openai/o3-mini` | 0.7141 | 1.1 | 4.4 | 200k | ✅ | — | AA-IQ 19.2 · LCB 0.72 · GPQA 0.75 · HLE 0.08 · AIME 0.77 |
| 7 | `openai/o1` | 0.6838 | 15.0 | 60.0 | 200k | ✅ | ✅ | AA-IQ 23.9 · AA-Code 39.7 · LCB 0.68 · aider 6% · GPQA 0.75 · HLE 0.07 · AIME 0.72 |
| 8 | `deepseek/deepseek-r1` | 0.6716 | 0.7 | 2.5 | 64k | ✅ | — | AA-IQ 18.6 · AA-Code 24.6 · LCB 0.62 · aider 27% · GPQA 0.71 · HLE 0.09 · AIME 0.68 |
| 9 | `openai/gpt-oss-120b` | 0.6615 | 0.03 | 0.17 | 131k | ✅ | — | AA-IQ 24.1 · AA-Code 30.4 · LCB 0.88 · aider 14% · GPQA 0.78 · HLE 0.20 |
| 10 | `openai/gpt-5-mini` | 0.6495 | 0.25 | 2.0 | 400k | ✅ | ✅ | AA-IQ 25.8 · AA-Code 15.6 · LCB 0.84 · GPQA 0.83 · HLE 0.21 |

## 🤖 Best Agentic

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `minimax/minimax-m3` | 0.8286 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 2 | `openai/gpt-5-mini` | 0.7544 | 0.25 | 2.0 | 400k | ✅ | ✅ | AA-IQ 25.8 · AA-Code 15.6 · LCB 0.84 · GPQA 0.83 · HLE 0.21 |
| 3 | `openai/gpt-5` | 0.7306 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.3 · AA-Code 37.8 · LCB 0.85 · GPQA 0.85 · HLE 0.28 · AIME 0.96 |
| 4 | `minimax/minimax-m2` | 0.7231 | 0.255 | 1.02 | 205k | ✅ | — | AA-IQ 28.9 · LCB 0.83 · GPQA 0.78 · HLE 0.14 |
| 5 | `openai/o3` | 0.7143 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |
| 6 | `upstage/solar-pro-3` | 0.712 | 0.15 | 0.6 | 131k | ✅ | — | AA-IQ 14.5 · AA-Code 16.2 · GPQA 0.72 · HLE 0.10 |
| 7 | `openai/o1` | 0.7034 | 15.0 | 60.0 | 200k | ✅ | ✅ | AA-IQ 23.9 · AA-Code 39.7 · LCB 0.68 · aider 6% · GPQA 0.75 · HLE 0.07 · AIME 0.72 |
| 8 | `inception/mercury-2` | 0.698 | 0.25 | 0.75 | 128k | ✅ | — | AA-IQ 21.9 · AA-Code 31.1 · GPQA 0.77 · HLE 0.17 |
| 9 | `openai/gpt-oss-120b` | 0.6898 | 0.03 | 0.17 | 131k | ✅ | — | AA-IQ 24.1 · AA-Code 30.4 · LCB 0.88 · aider 14% · GPQA 0.78 · HLE 0.20 |
| 10 | `openai/o4-mini` | 0.6871 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |

## 👁️ Best Vision

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-opus-5` | 0.7055 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 63.1 · AA-Code 78 · GPQA 0.93 · HLE 0.55 |
| 2 | `anthropic/claude-fable-5` | 0.693 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 3 | `anthropic/claude-sonnet-5` | 0.634 | 2.0 | 10.0 | 1.0M | ✅ | ✅ | AA-IQ 55.3 · AA-Code 71.5 · aider 22% · GPQA 0.91 · HLE 0.41 |
| 4 | `anthropic/claude-opus-5-fast` | 0.597 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 52.5 · AA-Code 66.9 · GPQA 0.89 · HLE 0.43 |
| 5 | `openai/o3` | 0.597 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |
| 6 | `openai/o4-mini` | 0.584 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 7 | `openai/gpt-5` | 0.558 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.3 · AA-Code 37.8 · LCB 0.85 · GPQA 0.85 · HLE 0.28 · AIME 0.96 |
| 8 | `minimax/minimax-m3` | 0.52 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 9 | `openai/gpt-5-nano` | 0.519 | 0.05 | 0.4 | 400k | ✅ | ✅ | AA-IQ 20.1 · LCB 0.79 · GPQA 0.68 · HLE 0.10 |
| 10 | `openai/gpt-5-mini` | 0.4403 | 0.25 | 2.0 | 400k | ✅ | ✅ | AA-IQ 25.8 · AA-Code 15.6 · LCB 0.84 · GPQA 0.83 · HLE 0.21 |

## 🔓 Best Open-Weight

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `deepseek/deepseek-v4-pro` | 0.61 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |
| 2 | `deepseek/deepseek-v4-flash` | 0.6045 | 0.06146 | 0.12292 | 1.0M | ✅ | — | AA-IQ 51.8 · AA-Code 69.1 · GPQA 0.91 · HLE 0.39 |
| 3 | `minimax/minimax-m3` | 0.52 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 4 | `tencent/hy3` | 0.505 | 0.132 | 0.528 | 262k | ✅ | — | AA-IQ 42.2 · AA-Code 58.8 · GPQA 0.90 · HLE 0.34 |
| 5 | `inclusionai/ling-3.0-flash` | 0.442 | 0.021 | 0.063 | 262k | ✅ | — | AA-IQ 37.8 · AA-Code 50.6 · GPQA 0.85 · HLE 0.24 |
| 6 | `minimax/minimax-m2` | 0.289 | 0.255 | 1.02 | 205k | ✅ | — | AA-IQ 28.9 · LCB 0.83 · GPQA 0.78 · HLE 0.14 |
| 7 | `openai/gpt-oss-120b` | 0.2725 | 0.03 | 0.17 | 131k | ✅ | — | AA-IQ 24.1 · AA-Code 30.4 · LCB 0.88 · aider 14% · GPQA 0.78 · HLE 0.20 |
| 8 | `deepseek/deepseek-r1` | 0.216 | 0.7 | 2.5 | 64k | ✅ | — | AA-IQ 18.6 · AA-Code 24.6 · LCB 0.62 · aider 27% · GPQA 0.71 · HLE 0.09 · AIME 0.68 |
| 9 | `openai/gpt-oss-20b` | 0.1795 | 0.03 | 0.13 | 131k | ✅ | — | AA-IQ 15.2 · AA-Code 20.7 · LCB 0.78 · GPQA 0.69 · HLE 0.11 |
| 10 | `deepseek/deepseek-r1-distill-llama-70b` | 0.098 | 0.8 | 0.8 | 8k | ✅ | — | AA-IQ 9.8 · LCB 0.27 · GPQA 0.40 · HLE 0.05 · AIME 0.67 |

## 💰 Best Value (low cost)

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `inclusionai/ling-3.0-flash` | 0.442 | 0.021 | 0.063 | 262k | ✅ | — | AA-IQ 37.8 · AA-Code 50.6 · GPQA 0.85 · HLE 0.24 |
| 2 | `nex-agi/nex-n2-mini` | — | 0.025 | 0.1 | 262k | ✅ | ✅ | — |
| 3 | `openai/gpt-5-nano:batch` | — | 0.025 | 0.2 | 400k | ✅ | ✅ | — |
| 4 | `openai/gpt-oss-120b` | 0.493 | 0.03 | 0.17 | 131k | ✅ | — | AA-IQ 24.1 · AA-Code 30.4 · LCB 0.88 · aider 14% · GPQA 0.78 · HLE 0.20 |
| 5 | `upstage/solar-pro4` | 0.4715 | 0.03 | 0.12 | 524k | ✅ | — | AA-IQ 41.6 · AA-Code 52.7 · GPQA 0.89 · HLE 0.29 |
| 6 | `openai/gpt-oss-20b` | 0.4173 | 0.03 | 0.13 | 131k | ✅ | — | AA-IQ 15.2 · AA-Code 20.7 · LCB 0.78 · GPQA 0.69 · HLE 0.11 |
| 7 | `qwen/qwen3.7-flash` | — | 0.03 | 0.13 | 1.0M | ✅ | ✅ | — |
| 8 | `nvidia/nemotron-3-nano-30b-a3b` | 0.1025 | 0.05 | 0.2 | 262k | ✅ | — | AA-IQ 7.2 · LCB 0.36 · GPQA 0.40 · HLE 0.05 |
| 9 | `google/gemini-2.5-flash-lite:batch` | — | 0.05 | 0.2 | 1.0M | ✅ | ✅ | — |
| 10 | `poolside/laguna-xs-2.1` | — | 0.06 | 0.12 | 262k | ✅ | — | — |

---

_Recommended lists are transparent weighted blends of REAL benchmark values (Artificial Analysis indices + raw benchmarks, aider polyglot coding). Models missing a benchmark contribute null (not zero). Verify high-stakes choices against primary sources._

_Each task score = weighted mean of available normalized 0-1 benchmarks (AA indices /100; GPQA/HLE/LiveCodeBench/AIME/Math-500/SciCode already 0-1; aider pass_rate /100). Sources merged by provider+slug then name fuzzy-match. Variant families collapsed to canonical base model in shortlists._
