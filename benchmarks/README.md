# ModelCompass Benchmarks

Every benchmark lives in its own subfolder. Each subfolder contains raw `*.json` ranking files plus an `OVERVIEW.md` with the top 10 of each benchmark, explained.

**No scores are mixed across benchmarks.**

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
