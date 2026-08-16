# ModelCompass Leaderboard

> Generated **2026-08-16T21:44:18Z** · 407 models · updated daily by GitHub Actions.

Each table ranks the best models for a task using real benchmark data (Artificial Analysis indices + aider polyglot coding). Scores are normalized 0–1 blends; `—` means the model has no benchmark for that column.

**Sources:** openrouter (ok (413 raw)) · artificial_analysis (ok (608 models)) · aider_polyglot (ok (54 models))

**Benchmark coverage:** 92 models with Artificial Analysis scores, 36 with aider coding.

## 🏆 Best Overall

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-fable-5` | 0.693 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 2 | `openai/gpt-5-codex:batch` | 0.6785 | 0.625 | 5.0 | 400k | ✅ | ✅ | AA-IQ 37 · LCB 0.84 · GPQA 0.84 · HLE 0.28 |
| 3 | `openai/gpt-5.2` | 0.678 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 38.9 · LCB 0.89 · GPQA 0.86 · HLE 0.27 |
| 4 | `openai/gpt-5.6-sol` | 0.6725 | 5.0 | 30.0 | 1.1M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 77.2 · GPQA 0.93 · HLE 0.46 |
| 5 | `google/gemini-3.7-flash` | 0.6605 | 0.375 | 1.875 | 1.0M | ✅ | ✅ | AA-IQ 56 · AA-Code 76.1 · GPQA 0.94 · HLE 0.48 |
| 6 | `anthropic/claude-opus-4.8` | 0.658 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 74.3 · GPQA 0.92 · HLE 0.49 |
| 7 | `openai/gpt-5.1-codex-max` | 0.6565 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.6 · LCB 0.85 · GPQA 0.86 · HLE 0.26 |
| 8 | `meta/muse-spark-1.2` | 0.645 | 1.25 | 4.25 | 1.0M | ✅ | ✅ | AA-IQ 56.8 · AA-Code 72.2 · GPQA 0.90 · HLE 0.46 |
| 9 | `anthropic/claude-opus-4.7` | 0.643 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 55 · AA-Code 73.6 · GPQA 0.91 · HLE 0.42 |
| 10 | `openai/gpt-5` | 0.6315 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 34.6 · LCB 0.70 · GPQA 0.84 · HLE 0.25 · AIME 0.92 |

## 💻 Best Coding

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `openai/gpt-5.2` | 0.894 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 38.9 · LCB 0.89 · GPQA 0.86 · HLE 0.27 |
| 2 | `openai/o4-mini` | 0.859 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 3 | `openai/gpt-5.1-codex-max` | 0.849 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.6 · LCB 0.85 · GPQA 0.86 · HLE 0.26 |
| 4 | `openai/gpt-5-codex:batch` | 0.84 | 0.625 | 5.0 | 400k | ✅ | ✅ | AA-IQ 37 · LCB 0.84 · GPQA 0.84 · HLE 0.28 |
| 5 | `openai/gpt-5.1-codex-mini` | 0.836 | 0.25 | 2.0 | 400k | ✅ | ✅ | AA-IQ 31.3 · LCB 0.84 · GPQA 0.81 · HLE 0.18 |
| 6 | `minimax/minimax-m2` | 0.826 | 0.255 | 1.02 | 205k | ✅ | — | AA-IQ 28.9 · LCB 0.83 · GPQA 0.78 · HLE 0.14 |
| 7 | `minimax/minimax-m2.1` | 0.81 | 0.3 | 1.2 | 205k | ✅ | — | AA-IQ 32.1 · LCB 0.81 · GPQA 0.83 · HLE 0.23 |
| 8 | `openai/gpt-5-nano` | 0.789 | 0.05 | 0.4 | 400k | ✅ | ✅ | AA-IQ 20.1 · LCB 0.79 · GPQA 0.68 · HLE 0.10 |
| 9 | `openai/gpt-5.6-sol` | 0.772 | 5.0 | 30.0 | 1.1M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 77.2 · GPQA 0.93 · HLE 0.46 |
| 10 | `anthropic/claude-fable-5` | 0.765 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |

## 🧠 Best Reasoning

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-fable-5` | 0.7007 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 2 | `google/gemini-3.7-flash` | 0.6613 | 0.375 | 1.875 | 1.0M | ✅ | ✅ | AA-IQ 56 · AA-Code 76.1 · GPQA 0.94 · HLE 0.48 |
| 3 | `anthropic/claude-opus-4.8` | 0.66 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 74.3 · GPQA 0.92 · HLE 0.49 |
| 4 | `openai/gpt-5.6-sol` | 0.6537 | 5.0 | 30.0 | 1.1M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 77.2 · GPQA 0.93 · HLE 0.46 |
| 5 | `meta/muse-spark-1.2` | 0.6423 | 1.25 | 4.25 | 1.0M | ✅ | ✅ | AA-IQ 56.8 · AA-Code 72.2 · GPQA 0.90 · HLE 0.46 |
| 6 | `meta/muse-spark-1.1` | 0.6307 | 1.25 | 4.25 | 1.0M | ✅ | ✅ | AA-IQ 53.2 · AA-Code 71.3 · GPQA 0.90 · HLE 0.46 |
| 7 | `openai/gpt-5.4` | 0.6293 | 2.5 | 15.0 | 1.1M | ✅ | ✅ | AA-IQ 53.1 · AA-Code 71.1 · GPQA 0.92 · HLE 0.44 |
| 8 | `google/gemini-3.1-pro-preview` | 0.6293 | 2.0 | 12.0 | 1.0M | ✅ | ✅ | AA-IQ 47.7 · AA-Code 68.8 · GPQA 0.94 · HLE 0.47 |
| 9 | `anthropic/claude-opus-4.7` | 0.629 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 55 · AA-Code 73.6 · GPQA 0.91 · HLE 0.42 |
| 10 | `deepseek/deepseek-v4-pro` | 0.6233 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |

## 📐 Best Math

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `perplexity/sonar-reasoning-pro` | 0.8737 | 2.0 | 8.0 | 128k | ✅ | ✅ | AA-IQ 18 · AIME 0.79 |
| 2 | `openai/o4-mini` | 0.8252 | 1.1 | 4.4 | 200k | ✅ | ✅ | AA-IQ 26.1 · LCB 0.86 · GPQA 0.78 · HLE 0.17 · AIME 0.94 |
| 3 | `openai/gpt-5` | 0.809 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 34.6 · LCB 0.70 · GPQA 0.84 · HLE 0.25 · AIME 0.92 |
| 4 | `openai/o3` | 0.7971 | 2.0 | 8.0 | 200k | ✅ | ✅ | AA-IQ 31.1 · LCB 0.81 · aider 35% · GPQA 0.83 · HLE 0.20 · AIME 0.90 |
| 5 | `google/gemini-2.5-pro` | 0.7897 | 1.25 | 10.0 | 1.0M | ✅ | ✅ | AA-IQ 25.9 · AA-Code 33.3 · LCB 0.80 · aider 46% · GPQA 0.84 · HLE 0.23 · AIME 0.89 |
| 6 | `openai/o3-mini-high` | 0.7476 | 1.1 | 4.4 | 200k | ✅ | — | AA-IQ 15.7 · AA-Code 16.3 · LCB 0.73 · GPQA 0.77 · HLE 0.12 · AIME 0.86 |
| 7 | `openai/gpt-5.2` | 0.7145 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 38.9 · LCB 0.89 · GPQA 0.86 · HLE 0.27 |
| 8 | `openai/o3-mini` | 0.7141 | 1.1 | 4.4 | 200k | ✅ | — | AA-IQ 19.2 · LCB 0.72 · GPQA 0.75 · HLE 0.08 · AIME 0.77 |
| 9 | `openai/gpt-5-codex:batch` | 0.698 | 0.625 | 5.0 | 400k | ✅ | ✅ | AA-IQ 37 · LCB 0.84 · GPQA 0.84 · HLE 0.28 |
| 10 | `openai/gpt-5.1` | 0.6865 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 37.5 · AA-Code 49.4 · LCB 0.87 · GPQA 0.87 · HLE 0.28 |

## 🤖 Best Agentic

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `minimax/minimax-m3` | 0.8286 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 2 | `xiaomi/mimo-v2.5-pro` | 0.7986 | 0.435 | 0.87 | 1.1M | ✅ | — | AA-IQ 42.9 · AA-Code 60.2 · GPQA 0.87 · HLE 0.36 |
| 3 | `openai/gpt-5.2-codex` | 0.7762 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 41.2 · GPQA 0.90 · HLE 0.36 |
| 4 | `google/gemini-3.1-flash-lite-preview` | 0.7721 | 0.25 | 1.5 | 1.0M | ✅ | ✅ | AA-IQ 25.6 · AA-Code 34.7 · GPQA 0.82 · HLE 0.17 |
| 5 | `google/gemini-3.1-pro-preview` | 0.7714 | 2.0 | 12.0 | 1.0M | ✅ | ✅ | AA-IQ 47.7 · AA-Code 68.8 · GPQA 0.94 · HLE 0.47 |
| 6 | `google/gemini-3.5-flash` | 0.7633 | 1.5 | 9.0 | 1.0M | ✅ | ✅ | AA-IQ 52 · AA-Code 70.1 · GPQA 0.92 · HLE 0.43 |
| 7 | `openai/gpt-5.4-nano` | 0.7592 | 0.2 | 1.25 | 400k | ✅ | ✅ | AA-IQ 39.7 · AA-Code 56.1 · GPQA 0.82 · HLE 0.28 |
| 8 | `minimax/minimax-m2.7` | 0.7571 | 0.3 | 1.2 | 205k | ✅ | — | AA-IQ 38.9 · AA-Code 52.6 · GPQA 0.87 · HLE 0.30 |
| 9 | `openai/gpt-5.3-codex` | 0.7537 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 45.5 · GPQA 0.92 · HLE 0.42 |
| 10 | `openai/gpt-5-codex:batch` | 0.7415 | 0.625 | 5.0 | 400k | ✅ | ✅ | AA-IQ 37 · LCB 0.84 · GPQA 0.84 · HLE 0.28 |

## 👁️ Best Vision

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `anthropic/claude-fable-5` | 0.693 | 10.0 | 50.0 | 1.0M | ✅ | ✅ | AA-IQ 62.1 · AA-Code 76.5 · GPQA 0.93 · HLE 0.56 |
| 2 | `openai/gpt-5-codex:batch` | 0.6785 | 0.625 | 5.0 | 400k | ✅ | ✅ | AA-IQ 37 · LCB 0.84 · GPQA 0.84 · HLE 0.28 |
| 3 | `openai/gpt-5.2` | 0.678 | 1.75 | 14.0 | 400k | ✅ | ✅ | AA-IQ 38.9 · LCB 0.89 · GPQA 0.86 · HLE 0.27 |
| 4 | `openai/gpt-5.6-sol` | 0.6725 | 5.0 | 30.0 | 1.1M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 77.2 · GPQA 0.93 · HLE 0.46 |
| 5 | `google/gemini-3.7-flash` | 0.6605 | 0.375 | 1.875 | 1.0M | ✅ | ✅ | AA-IQ 56 · AA-Code 76.1 · GPQA 0.94 · HLE 0.48 |
| 6 | `anthropic/claude-opus-4.8` | 0.658 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 57.3 · AA-Code 74.3 · GPQA 0.92 · HLE 0.49 |
| 7 | `openai/gpt-5.1-codex-max` | 0.6565 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 35.6 · LCB 0.85 · GPQA 0.86 · HLE 0.26 |
| 8 | `meta/muse-spark-1.2` | 0.645 | 1.25 | 4.25 | 1.0M | ✅ | ✅ | AA-IQ 56.8 · AA-Code 72.2 · GPQA 0.90 · HLE 0.46 |
| 9 | `anthropic/claude-opus-4.7` | 0.643 | 5.0 | 25.0 | 1.0M | ✅ | ✅ | AA-IQ 55 · AA-Code 73.6 · GPQA 0.91 · HLE 0.42 |
| 10 | `openai/gpt-5` | 0.6315 | 1.25 | 10.0 | 400k | ✅ | ✅ | AA-IQ 34.6 · LCB 0.70 · GPQA 0.84 · HLE 0.25 · AIME 0.92 |

## 🔓 Best Open-Weight

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `deepseek/deepseek-v4-pro` | 0.61 | 1.168 | 2.336 | 1.0M | ✅ | — | AA-IQ 53.2 · AA-Code 68.8 · GPQA 0.93 · HLE 0.41 |
| 2 | `minimax/minimax-m3` | 0.52 | 0.3 | 1.2 | 1.0M | ✅ | ✅ | AA-IQ 45.4 · AA-Code 58.6 · GPQA 0.93 · HLE 0.39 |
| 3 | `xiaomi/mimo-v2.5-pro` | 0.5155 | 0.435 | 0.87 | 1.1M | ✅ | — | AA-IQ 42.9 · AA-Code 60.2 · GPQA 0.87 · HLE 0.36 |
| 4 | `minimax/minimax-m2.7` | 0.4575 | 0.3 | 1.2 | 205k | ✅ | — | AA-IQ 38.9 · AA-Code 52.6 · GPQA 0.87 · HLE 0.30 |
| 5 | `inclusionai/ling-3.0-flash` | 0.442 | 0.021 | 0.063 | 262k | ✅ | — | AA-IQ 37.8 · AA-Code 50.6 · GPQA 0.85 · HLE 0.24 |
| 6 | `stepfun/step-3.7-flash` | 0.3525 | 0.2 | 1.15 | 262k | ✅ | ✅ | AA-IQ 30.9 · AA-Code 39.6 · GPQA 0.81 · HLE 0.21 |
| 7 | `minimax/minimax-m2.5` | 0.345 | 0.22 | 0.9 | 205k | ✅ | — | AA-IQ 34.5 · GPQA 0.85 · HLE 0.20 |
| 8 | `tencent/hy3-preview` | 0.344 | 0.18 | 0.6 | 262k | ✅ | — | AA-IQ 34.4 · GPQA 0.87 · HLE 0.28 |
| 9 | `minimax/minimax-m2.1` | 0.321 | 0.3 | 1.2 | 205k | ✅ | — | AA-IQ 32.1 · LCB 0.81 · GPQA 0.83 · HLE 0.23 |
| 10 | `deepseek/deepseek-v4-flash` | 0.293 | 0.06146 | 0.12292 | 1.0M | ✅ | — | AA-IQ 29.3 · GPQA 0.72 · HLE 0.08 |

## 💰 Best Value (low cost)

| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |
|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|
| 1 | `inclusionai/ling-3.0-flash` | 0.442 | 0.021 | 0.063 | 262k | ✅ | — | AA-IQ 37.8 · AA-Code 50.6 · GPQA 0.85 · HLE 0.24 |
| 2 | `nex-agi/nex-n2-mini` | — | 0.025 | 0.1 | 262k | ✅ | ✅ | — |
| 3 | `openai/gpt-5-nano:batch` | — | 0.025 | 0.2 | 400k | ✅ | ✅ | — |
| 4 | `upstage/solar-pro4` | 0.4715 | 0.03 | 0.12 | 524k | ✅ | — | AA-IQ 41.6 · AA-Code 52.7 · GPQA 0.89 · HLE 0.29 |
| 5 | `openai/gpt-oss-20b` | 0.3835 | 0.03 | 0.13 | 131k | ✅ | — | AA-IQ 14.4 · LCB 0.65 · GPQA 0.61 · HLE 0.05 |
| 6 | `openai/gpt-oss-120b` | 0.3427 | 0.03 | 0.17 | 131k | ✅ | — | AA-IQ 14.9 · AA-Code 21.2 · LCB 0.71 · aider 14% · GPQA 0.67 · HLE 0.06 |
| 7 | `qwen/qwen3.7-flash` | — | 0.03 | 0.13 | 1.0M | ✅ | ✅ | — |
| 8 | `nvidia/nemotron-3-nano-30b-a3b` | 0.1025 | 0.05 | 0.2 | 262k | ✅ | — | AA-IQ 7.2 · LCB 0.36 · GPQA 0.40 · HLE 0.05 |
| 9 | `google/gemini-2.5-flash-lite:batch` | — | 0.05 | 0.2 | 1.0M | ✅ | ✅ | — |
| 10 | `poolside/laguna-xs-2.1` | — | 0.06 | 0.12 | 262k | ✅ | — | — |

---

_Recommended lists are transparent weighted blends of REAL benchmark values (Artificial Analysis indices + raw benchmarks, aider polyglot coding). Models missing a benchmark contribute null (not zero). Verify high-stakes choices against primary sources._

_Each task score = weighted mean of available normalized 0-1 benchmarks (AA indices /100; GPQA/HLE/LiveCodeBench/AIME/Math-500/SciCode already 0-1; aider pass_rate /100). Sources merged via normalized provider+slug (AA dots->hyphens, reasoning-effort suffixes tolerated), then fuzzy name match. Only routing aliases (:batch/:free/:thinking) collapse in shortlists; identity tags (-latest, -0813, -v2) stay distinct._
