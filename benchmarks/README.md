# ModelCompass Benchmarks

Every benchmark lives in its own subfolder. Each subfolder contains raw `*.json` ranking files plus an `OVERVIEW.md` with the top 10 of each benchmark, explained.

**No scores are mixed across benchmarks.**

## [Artificial Analysis](./artificial-analysis/OVERVIEW.md) — [https://artificialanalysis.ai](https://artificialanalysis.ai)

Raw benchmark evaluations from Artificial Analysis' proprietary suite (AA API v2). Each file is one benchmark — higher is better unless noted. Values are the model's raw score on that benchmark.

- [AIME](./artificial-analysis/aa_aime.json)
- [AIME 2025](./artificial-analysis/aa_aime_25.json)
- [aa_artificial_analysis_coding_index](./artificial-analysis/aa_artificial_analysis_coding_index.json)
- [aa_artificial_analysis_intelligence_index](./artificial-analysis/aa_artificial_analysis_intelligence_index.json)
- [aa_artificial_analysis_math_index](./artificial-analysis/aa_artificial_analysis_math_index.json)
- [GPQA](./artificial-analysis/aa_gpqa.json)
- [HLE](./artificial-analysis/aa_hle.json)
- [IFBench](./artificial-analysis/aa_ifbench.json)
- [LCR](./artificial-analysis/aa_lcr.json)
- [LiveCodeBench](./artificial-analysis/aa_livecodebench.json)
- [MATH-500](./artificial-analysis/aa_math_500.json)
- [MMLU-Pro](./artificial-analysis/aa_mmlu_pro.json)
- [SciCode](./artificial-analysis/aa_scicode.json)
- [TAU2](./artificial-analysis/aa_tau2.json)
- [TAU-Banking](./artificial-analysis/aa_tau_banking.json)
- [Terminal-Bench Hard](./artificial-analysis/aa_terminalbench_hard.json)
- [Terminal-Bench v2.1](./artificial-analysis/aa_terminalbench_v2_1.json)

## [LMArena (arena.ai)](./arena/OVERVIEW.md) — [https://arena.ai](https://arena.ai)

Human-preference Elo from blind pairwise battles. Higher Elo = more preferred by human voters.

- [Agent Arena](./arena/arena_agent.json)
- [Code Arena](./arena/arena_code.json)
- [Document Arena](./arena/arena_document.json)
- [Image Edit Arena](./arena/arena_image-edit.json)
- [Image To Video Arena](./arena/arena_image-to-video.json)
- [Search Arena](./arena/arena_search.json)
- [Text Arena](./arena/arena_text.json)
- [Text To Image Arena](./arena/arena_text-to-image.json)
- [Text To Video Arena](./arena/arena_text-to-video.json)
- [Video Edit Arena](./arena/arena_video-edit.json)
- [Vision Arena](./arena/arena_vision.json)

## [BenchLM](./benchlm/OVERVIEW.md) — [https://benchlm.ai/data/models.json](https://benchlm.ai/data/models.json)

Aggregated category scores (0–100) across 437 benchmarks and 388 models (MIT-licensed). Higher is better.

- [Agentic](./benchlm/benchlm_agentic.json)
- [Coding](./benchlm/benchlm_coding.json)
- [Instruction Following](./benchlm/benchlm_instructionFollowing.json)
- [Knowledge](./benchlm/benchlm_knowledge.json)
- [Math](./benchlm/benchlm_math.json)
- [Multilingual](./benchlm/benchlm_multilingual.json)
- [Multimodal Grounded](./benchlm/benchlm_multimodalGrounded.json)
- [Reasoning](./benchlm/benchlm_reasoning.json)

## [OpenRouter Usage](./openrouter-usage/OVERVIEW.md) — [https://openrouter.ai/api/frontend/v1/rankings/models](https://openrouter.ai/api/frontend/v1/rankings/models)

Real-world adoption: tokens processed and request counts via OpenRouter (rolling window). NOT a quality score — usage is never blended into benchmark rankings.

- [Usage Rank](./openrouter-usage/or_usage_tokens.json)
