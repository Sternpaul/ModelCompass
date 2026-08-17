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

## [Nous Free Tier (models.dev / Nous Portal)](./nous_free/OVERVIEW.md) — [https://models.dev/api.json](https://models.dev/api.json)

Models listed as free on the Nous Portal (models.dev catalogue, tagged ':free'). Pricing 0.00 / 0.00 per 1M tokens. Sorted by provider then model id. Note: the Nous Portal currently lists 6 free models; 2 of them (meituan/longcat-2.0:free, upstage/solar-pro4:free) are portal-only additions not yet in the models.dev catalogue at scrape time.

- [Free](./nous_free/nous_free.json)
