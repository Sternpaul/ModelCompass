#!/usr/bin/env python3
"""
ModelCompass generator — pure per-benchmark rankings, no mixing.

Sources (all fetched directly, no third-party snapshots):
 1. OpenRouter /api/v1/models        -> catalog: pricing, context, modality, flags
 2. Artificial Analysis API v2       -> 17 raw benchmarks + 3 composite indices
 3. arena.ai (Jina Reader)           -> LMArena Elo (11 leaderboards)
 4. BenchLM (MIT JSON)               -> 437 benchmarks across 388 models

Each source writes its OWN file(s) under benchmarks/.  No scores are blended.
consensus/ contains a Borda-count placement-agreement summary only.
models.json carries raw benchmark cross-references, no derived scores.
"""

import json
import os
import re
import sys
import csv
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OR_API = "https://openrouter.ai/api/v1/models"
AA_API = "https://artificialanalysis.ai/api/v2/data/llms/models"
ARENA_BASE = "https://arena.ai/leaderboard/"
JINA_BASE = "https://r.jina.ai/"
BENCHLM_BASE = "https://benchlm.ai/data"
OUTDIR = "."

# Collapse only routing aliases; keep identity-bearing tags (e.g. -0813, -latest)
COLLAPSE_COLON = re.compile(
    r"(:batch|:free|:thinking|:nitro|:floor|:cached)$"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(*a):
    print(*a, file=sys.stderr, flush=True)


def fetch_json(url, headers=None, timeout=60):
    req = urllib.request.Request(
        url, headers=headers or {"User-Agent": "modelcompass/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_text(url, headers=None, timeout=60):
    req = urllib.request.Request(
        url, headers=headers or {"User-Agent": "modelcompass/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def family_id(mid):
    if "/" in mid:
        p, r = mid.split("/", 1)
    else:
        p, r = "", mid
    r = COLLAPSE_COLON.sub("", r)
    return f"{p}/{r}" if p else r


def norm(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\d{4}-\d{2}-\d{2}", "", s)
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def scale(x, by=1.0):
    v = num(x)
    return None if v is None else v / by


# ---------------------------------------------------------------------------
# Source 1: OpenRouter catalog
# ---------------------------------------------------------------------------
def fetch_openrouter():
    data = fetch_json(OR_API, timeout=60)["data"]
    out = []
    for m in data:
        mid = m.get("id", "")
        arch = m.get("architecture", {}) or {}
        in_mods = set(arch.get("input_modalities", []) or [])
        out_mods = set(arch.get("output_modalities", []) or [])
        params = m.get("supported_parameters", []) or []
        provider = mid.split("/")[0] if "/" in mid else ""
        ctx = max(
            m.get("context_length") or 0,
            (m.get("top_provider", {}) or {}).get("context_length") or 0,
        )
        p_in = scale(m.get("pricing", {}).get("prompt"), 1e-6)
        p_out = scale(m.get("pricing", {}).get("completion"), 1e-6)
        p_cache = scale(m.get("pricing", {}).get("input_cache_read"), 1e-6)

        rec = {
            "id": mid,
            "name": m.get("name"),
            "provider": provider,
            "family": family_id(mid),
            "source": "openrouter",
            "created_unix": m.get("created"),
            "context": ctx,
            "modality": arch.get("modality", ""),
            "is_vision": "image" in in_mods,
            "is_audio_input": "audio" in in_mods,
            "is_video_input": "video" in in_mods,
            "is_image_output": "image" in out_mods,
            "is_audio_output": "audio" in out_mods,
            "supports_reasoning": "reasoning" in params,
            "supports_tools": "tools" in params,
            "supports_json": ("structured_outputs" in params)
            or ("response_format" in params),
            "supports_caching": bool(p_cache and p_cache > 0),
            "knowledge_cutoff": m.get("knowledge_cutoff"),
            "hugging_face_id": m.get("hugging_face_id"),
            "open_weight": bool(m.get("hugging_face_id")),
            "synthetic": provider == "openrouter",
            "free": bool(p_in is not None and p_in <= 0 and provider != "openrouter"),
            "price_per_million": {
                "prompt": round(p_in, 6) if p_in is not None else None,
                "completion": round(p_out, 6) if p_out is not None else None,
                "cache_read": round(p_cache, 6) if p_cache is not None else None,
            },
            "benchmarks": {},
        }
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Source 2: Artificial Analysis
# ---------------------------------------------------------------------------
def fetch_artificial_analysis(api_key):
    if not api_key:
        return None, "no API key"
    req = urllib.request.Request(
        AA_API,
        headers={"User-Agent": "modelcompass/1.0", "x-api-key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return None, str(e)

    models = payload.get("data", []) if isinstance(payload, dict) else []
    out = {}
    for m in models:
        creator = (m.get("model_creator") or {}).get("slug") or ""
        slug = m.get("slug") or ""
        evals = m.get("evaluations") or {}
        pricing = m.get("pricing") or {}
        key = f"{creator}/{slug}".lower()
        out[key] = {
            "key": key,
            "name": m.get("name"),
            "creator_slug": creator,
            "slug": slug,
            "evaluations": evals,
            "pricing": {
                "prompt": scale(pricing.get("price_1m_input_tokens")),
                "completion": scale(pricing.get("price_1m_output_tokens")),
                "blended": scale(pricing.get("price_1m_blended_3_to_1")),
            },
            "median_tps": num(m.get("median_output_tokens_per_second")),
            "ttft": num(m.get("median_time_to_first_token_seconds")),
        }
    return out, f"ok ({len(out)} models)"


# ---------------------------------------------------------------------------
# Source 4: arena.ai (Jina Reader — same technique as community scrapers)
# ---------------------------------------------------------------------------
def _parse_number(s):
    if not s:
        return None
    s = s.strip()
    m = re.match(r"([\d.]+)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _parse_number_with_ci(s):
    """'12.19%±1.45%' -> (12.19, 1.45) ; '12.19%' -> (12.19, None)."""
    if not s:
        return None, None
    s = s.strip()
    score = None
    ci = None
    m = re.match(r"([\d.]+)\s*%?", s)
    if m:
        score = float(m.group(1))
    m_ci = re.search(r"±\s*([\d.]+)\s*%?", s)
    if m_ci:
        ci = float(m_ci.group(1))
    return score, ci


def _parse_int(s):
    if not s:
        return None
    s = s.strip().replace(",", "")
    if not s or s == "-":
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_arena_general(content, slug):
    """Parse general leaderboard table (text, code, vision, …)."""
    lines = content.split("\n")
    models = []
    in_table = False
    for line in lines:
        if "| Rank |" in line or "|---|" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 6:
                continue
            rank_m = re.match(r"\s*(\d+)", cells[0])
            if not rank_m:
                continue
            rank = int(rank_m.group(1))

            # The model cell is the first cell containing a markdown link
            # [name](url); arena tables often insert a rank-change badge
            # column right after the rank, so we don't assume a fixed index.
            model_cell = None
            model_idx = None
            for i, c in enumerate(cells[1:], start=1):
                if re.search(r"\[[^\]]+\]\(https?://", c):
                    model_cell = c
                    model_idx = i
                    break
            if model_cell is None:
                continue
            assert model_idx is not None  # guaranteed by the loop above
            m = re.match(r"\[([^\]]+)\]", model_cell)
            model_name = m.group(1) if m else model_cell

            vendor_match = re.search(r"\]\([^)]*\)\s*([^·]+?)\s*·", model_cell)
            vendor = vendor_match.group(1).strip() if vendor_match else None

            lic_match = re.search(
                r"·\s*(proprietary|open|Open Source|MIT|Apache|GPL|CC-|Community|Non-commercial)",
                model_cell, re.I,
            )
            license = "proprietary" if (
                lic_match and "proprietary" in lic_match.group(1).lower()
            ) else ("open" if lic_match else None)

            # Score/CI/votes follow the model cell
            score = _parse_number(cells[model_idx + 1]) if model_idx + 1 < len(cells) else None
            ci = _parse_number(cells[model_idx + 2]) if model_idx + 2 < len(cells) else None
            votes = _parse_int(cells[model_idx + 3]) if model_idx + 3 < len(cells) else None

            models.append(
                {
                    "rank": rank,
                    "model": model_name,
                    "vendor": vendor,
                    "license": license,
                    "score": score,
                    "ci": ci,
                    "votes": votes,
                }
            )

    return {
        "meta": {
            "leaderboard": slug,
            "source_url": f"https://arena.ai/leaderboard/{slug}",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(models),
        },
        "models": models,
    }, f"ok ({len(models)} models)"


def _parse_arena_agent(content, slug):
    """Parse agent leaderboard with dimension scores."""
    lines = content.split("\n")
    models = []
    dimensions = []
    in_table = False
    for line in lines:
        if "| Rank |" in line or "|---|" in line:
            in_table = True
            if "| Rank |" in line:
                cells = [c.strip() for c in line.strip("|").split("|")]
                # Extract dimension names (skip Rank, Model, Sessions, Price)
                dimensions = [
                    re.sub(r"\s*\([^)]*\)", "", c).strip()
                    for c in cells
                    if c and c not in ("Rank", "Model", "Sessions", "Price $/M", "Price $/M tokens")
                ]
                dimensions = [d for d in dimensions if d]
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 4:
                continue
            rank_m = re.match(r"\s*(\d+)", cells[0])
            if not rank_m:
                continue
            rank = int(rank_m.group(1))

            model_cell = cells[1]
            m = re.match(r"\[([^\]]+)\]", model_cell)
            model_name = m.group(1) if m else model_cell

            vendor_match = re.search(r"\]\([^)]*\)\s*([^·]+?)\s*·", model_cell)
            vendor = vendor_match.group(1).strip() if vendor_match else None

            lic_match = re.search(
                r"·\s*(proprietary|open|Open Source|MIT|Apache|GPL|CC-|Community|Non-commercial)",
                model_cell, re.I,
            )
            license = "proprietary" if (
                lic_match and "proprietary" in lic_match.group(1).lower()
            ) else ("open" if lic_match else None)

            scores = []
            for i, dim in enumerate(dimensions):
                cell_idx = 2 + i
                if cell_idx < len(cells):
                    score_val, ci_val = _parse_number_with_ci(cells[cell_idx])
                    scores.append({"name": dim, "score": score_val, "ci": ci_val})

            sessions = _parse_int(cells[-2]) if len(cells) >= 2 else None

            models.append(
                {
                    "rank": rank,
                    "model": model_name,
                    "vendor": vendor,
                    "license": license,
                    "scores": scores,
                    "sessions": sessions,
                }
            )

    return {
        "meta": {
            "leaderboard": slug,
            "source_url": f"https://arena.ai/leaderboard/{slug}",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(models),
            "dimensions": dimensions,
        },
        "models": models,
    }, f"ok ({len(models)} models)"


def fetch_arena_leaderboard(slug):
    """Fetch a single arena.ai leaderboard via Jina Reader."""
    url = f"{JINA_BASE}{ARENA_BASE}{slug}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "X-Return-Format": "markdown",
            "User-Agent": "modelcompass/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            wrapper = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return None, f"fetch error: {e}"

    content = wrapper.get("data", {}).get("content", "")
    if not content:
        return None, "empty content"

    if slug == "agent":
        return _parse_arena_agent(content, slug)
    return _parse_arena_general(content, slug)


# Known arena.ai leaderboards (fetched live from each page — not a third-party
# snapshot). The overview page is a JS SPA and no longer exposes stable links,
# so we enumerate the well-known boards here; the discover scrape is a fallback.
ARENA_SLUGS = [
    "agent",
    "code",
    "text",
    "vision",
    "document",
    "search",
    "image-edit",
    "image-to-video",
    "text-to-image",
    "text-to-video",
    "video-edit",
]


def discover_arena_slugs():
    """Return the known arena.ai leaderboard slugs.

    The overview page is a JS SPA that no longer exposes stable per-board
    links, so we use a curated list and fetch each board live. (A scrape-based
    fallback runs first in case arena.ai changes its URL scheme.)
    """
    slugs = set()
    try:
        text = fetch_text(f"{JINA_BASE}{ARENA_BASE}")
        slugs.update(re.findall(r"arena\.ai/leaderboard/([a-z][a-z0-9-]*)", text))
    except Exception as e:
        log(f"Arena slug scrape failed ({e}); using curated list")
    slugs.update(ARENA_SLUGS)
    return sorted(slugs)


# ---------------------------------------------------------------------------
# Source 5: BenchLM (MIT licensed raw JSON)
# ---------------------------------------------------------------------------
def fetch_benchlm():
    """Fetch BenchLM models.json — 388 models, 437 benchmarks."""
    try:
        data = fetch_json(f"{BENCHLM_BASE}/models.json", timeout=60)
    except Exception as e:
        return None, str(e)
    items = data.get("items", []) if isinstance(data, dict) else []
    return items, f"ok ({len(items)} models)"


# ---------------------------------------------------------------------------
# Merge: cross-reference only, no score blending
# ---------------------------------------------------------------------------
def base_slug(model_id):
    """Strip reasoning-effort / deviation suffixes (xhigh, high, max, xlow,
    low, medium, batch, free, latest, thinking, -0824, -0813, -3107 …) so that
    e.g. 'openai/gpt-5.6-sol-high' collapses to 'openai/gpt-5.6-sol'.
    Composed prefixes like 'deepseek/deepseek-v4-pro-0813' have NO base and
    return as-is on purpose."""
    parts = model_id.rsplit("-", 1)
    if len(parts) != 2:
        return model_id
    head, tail = parts
    # suffix tokens that always mean 'a variant of the same model'
    if re.fullmatch(r"(x?high|x?low|medium|batch|free|latest|thinking|"
                    r"\d{3,4}|"
                    r"[a-z]{1,4}\d{1,4})", tail):
        return head
    return model_id


def merge(or_models, aa, arena, benchlm):
    """Attach raw benchmark data to OpenRouter models.
    Each source stays in its own namespace under benchmarks.<source>."""
    or_by_id = {}
    or_by_norm = {}
    or_by_slug_only = {}
    for m in or_models:
        mid = m["id"].lower()
        or_by_id[mid] = m
        or_by_norm.setdefault(norm(m["name"]), []).append(m)
        slug_only = mid.split("/", 1)[-1] if "/" in mid else mid
        or_by_slug_only.setdefault(slug_only, []).append(m)

    counts = {"aa": 0, "arena": 0, "benchlm": 0}

    # Attach AA
    if aa:
        for key, a in aa.items():
            creator = a.get("creator_slug", "")
            slug = a.get("slug", "")
            target = None
            k = f"{creator}/{slug}".lower()
            if k in or_by_id:
                target = or_by_id[k]
            else:
                base = base_slug(k.replace(".", "-"))
                if base in or_by_id:
                    target = or_by_id[base]
                else:
                    so = base.split("/", 1)[-1]
                    if so in or_by_slug_only:
                        target = or_by_slug_only[so][0]
                    else:
                        nn = norm(a.get("name", ""))
                        if nn in or_by_norm:
                            target = or_by_norm[nn][0]
            if target:
                target["benchmarks"]["aa"] = a
                counts["aa"] += 1

    # Attach arena
    if arena:
        for lb_slug, lb_data in arena.items():
            for model_info in lb_data.get("models", []):
                nn = norm(model_info.get("model", ""))
                if nn in or_by_norm:
                    for m in or_by_norm[nn]:
                        m["benchmarks"].setdefault("arena", {})
                        m["benchmarks"]["arena"][lb_slug] = model_info
                        counts["arena"] += 1
                        break

    # Attach BenchLM
    if benchlm:
        for bm in benchlm:
            slug = bm.get("slug", "").lower()
            model_name = bm.get("model", "")
            target = None
            if slug and slug in or_by_id:
                target = or_by_id[slug]
            else:
                if slug in or_by_slug_only:
                    target = or_by_slug_only[slug][0]
                elif slug:
                    base = base_slug(slug)
                    if base in or_by_slug_only:
                        target = or_by_slug_only[base][0]
                if target is None:
                    nn = norm(model_name)
                    if nn in or_by_norm:
                        target = or_by_norm[nn][0]
            if target:
                target["benchmarks"]["benchlm"] = bm
                counts["benchlm"] += 1

    return counts


# ---------------------------------------------------------------------------
# Output: per-benchmark files
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Source registry: where each benchmark lives + how to present it
# ---------------------------------------------------------------------------
SOURCE_META = {
    "artificial-analysis": {
        "title": "Artificial Analysis",
        "source_url": "https://artificialanalysis.ai",
        "desc": "Raw benchmark evaluations from Artificial Analysis' proprietary "
                "suite (AA API v2). Each file is one benchmark — higher is better "
                "unless noted. Values are the model's raw score on that benchmark.",
        "benches": {
            "aa_intelligence": ("Intelligence Index", "Composite intelligence index (0–100)."),
            "aa_coding": ("Coding Index", "Composite coding capability index (0–100)."),
            "aa_math": ("Math Index", "Composite math reasoning index (0–100)."),
            "aa_aime": ("AIME", "American Invitational Mathematics Examination accuracy (%)."),
            "aa_aime_25": ("AIME 2025", "AIME 2025 accuracy (%)."),
            "aa_gpqa": ("GPQA", "Graduate-level Google-Proof Q&A diamond accuracy (%)."),
            "aa_hle": ("HLE", "Humanity's Last Exam accuracy (%)."),
            "aa_ifbench": ("IFBench", "Instruction-following benchmark score (%)."),
            "aa_lcr": ("LCR", "Long-context reasoning score (%)."),
            "aa_livecodebench": ("LiveCodeBench", "LiveCodeBench coding accuracy (%)."),
            "aa_math_500": ("MATH-500", "MATH-500 competition-math accuracy (%)."),
            "aa_mmlu_pro": ("MMLU-Pro", "MMLU-Pro knowledge accuracy (%)."),
            "aa_scicode": ("SciCode", "SciCode scientific coding accuracy (%)."),
            "aa_tau2": ("TAU2", "TAU-bench agent benchmark (%)."),
            "aa_tau_banking": ("TAU-Banking", "TAU-bench banking domain agent score (%)."),
            "aa_terminalbench_hard": ("Terminal-Bench Hard", "Terminal-Bench hard sys-admin tasks (%)."),
            "aa_terminalbench_v2_1": ("Terminal-Bench v2.1", "Terminal-Bench v2.1 sys-admin tasks (%)."),
        },
    },
    "arena": {
        "title": "LMArena (arena.ai)",
        "source_url": "https://arena.ai",
        "desc": "Human-preference Elo from blind pairwise battles. "
                "Higher Elo = more preferred by human voters.",
        "benches": {},  # filled dynamically from discovered slugs
    },
    "benchlm": {
        "title": "BenchLM",
        "source_url": f"{BENCHLM_BASE}/models.json",
        "desc": "Aggregated category scores (0–100) across 437 benchmarks and 388 "
                "models (MIT-licensed). Higher is better.",
        "benches": {
            "benchlm_agentic": ("Agentic", "Tool-use / agentic task category score."),
            "benchlm_coding": ("Coding", "Code generation category score."),
            "benchlm_math": ("Math", "Quantitative reasoning category score."),
            "benchlm_reasoning": ("Reasoning", "Logical reasoning category score."),
            "benchlm_knowledge": ("Knowledge", "Factual knowledge category score."),
            "benchlm_multilingual": ("Multilingual", "Non-English capability category score."),
            "benchlm_multimodalGrounded": ("Multimodal Grounded", "Vision+text grounded understanding."),
            "benchlm_instructionFollowing": ("Instruction Following", "Following complex instructions."),
        },
    },
    "consensus": {
        "title": "Consensus (Borda)",
        "source_url": "",
        "desc": "Placement agreement across all benchmarks. Counts how many top-10 "
                "lists a model appears in — never an averaged score.",
        "benches": {
            "consensus": ("Consensus Ranking", "Top-10 appearance count, tie-broken by Borda points."),
        },
    },
}

WRITTEN = {}  # subdir -> [bname, ...]


def _write_benchmark_json(subdir, bname, meta_info, models_list):
    out_dir = os.path.join("benchmarks", subdir)
    os.makedirs(out_dir, exist_ok=True)
    data = {"meta": meta_info, "models": models_list}
    path = os.path.join(out_dir, f"{bname}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    WRITTEN.setdefault(subdir, []).append(bname)
    return path


def write_aa_benchmarks(or_models):
    """Write every Artificial Analysis benchmark into artificial-analysis/.

    We emit one file per evaluation key that actually appears in the data
    (17 fields), not a hard-coded subset - so newly added AA benchmarks show
    up automatically. `fetched_at` is stamped on each file's meta.
    """
    subdir = "artificial-analysis"
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Discover which evaluation keys exist across the catalog
    seen = {}
    for m in or_models:
        evals = (m.get("benchmarks", {}).get("aa", {}) or {}).get("evaluations", {})
        for k in evals:
            seen.setdefault(k, 0)
            seen[k] += 1

    written = {}
    for eval_key, n in sorted(seen.items()):
        models_list = []
        for m in or_models:
            evals = (m.get("benchmarks", {}).get("aa", {}) or {}).get("evaluations", {})
            val = num(evals.get(eval_key))
            if val is not None:
                models_list.append(
                    {
                        "model": m["id"],
                        "name": m.get("name"),
                        "score": val,
                    }
                )
        models_list.sort(key=lambda x: x["score"], reverse=True)
        if models_list:
            bname = f"aa_{eval_key}"
            _write_benchmark_json(
                subdir, bname,
                {
                    "leaderboard": bname,
                    "source_url": "https://artificialanalysis.ai",
                    "benchmark": eval_key,
                    "fetched_at": fetched_at,
                    "model_count_with_data": n,
                },
                models_list,
            )
            written[bname] = True
    return written


def write_arena_benchmarks(arena_data):
    subdir = "arena"
    for slug, lb in arena_data.items():
        _write_benchmark_json(
            subdir, f"arena_{slug}", lb.get("meta", {}), lb.get("models", [])
        )
        # Register a human title for this leaderboard
        SOURCE_META["arena"]["benches"].setdefault(
            f"arena_{slug}",
            (slug.replace("-", " ").title() + " Arena", "Human-preference Elo."),
        )
    return None


def write_benchlm_benchmarks(benchlm_items):
    """Write BenchLM benchmarks grouped by category into benchlm/.

    BenchLM's raw JSON stores per-category scores under
    scores.displayCategoryScores and per-category ranks under
    ranking.categoryRanks. We use displayCategoryScores for the
    ranking value (None entries are skipped) and attach the category rank.
    """
    subdir = "benchlm"
    if not benchlm_items:
        return {}
    # Collect all categories from displayCategoryScores (the inner dict only)
    categories = set()
    for bm in benchlm_items:
        scores = (bm.get("scores") or {}).get("displayCategoryScores") or {}
        categories.update(scores.keys())

    written = {}
    for cat in sorted(categories):
        models_list = []
        for bm in benchlm_items:
            scores = (bm.get("scores") or {}).get("displayCategoryScores") or {}
            val = scores.get(cat)
            if val is None:
                continue
            rank = ((bm.get("ranking") or {}).get("categoryRanks") or {}).get(cat)
            models_list.append(
                {
                    "model": bm.get("slug", ""),
                    "name": bm.get("model", ""),
                    "creator": bm.get("creator", ""),
                    "score": val,
                    "category_rank": rank,
                }
            )
        models_list.sort(key=lambda x: x.get("score") or 0, reverse=True)
        if models_list:
            bname = f"benchlm_{cat}"
            _write_benchmark_json(
                subdir, bname,
                {
                    "leaderboard": bname,
                    "source_url": f"{BENCHLM_BASE}/models.json",
                    "benchmark": f"BenchLM {cat}",
                },
                models_list,
            )
            written[bname] = True
    return written


# ---------------------------------------------------------------------------
# Output: models.json (catalog, no derived scores)
# ---------------------------------------------------------------------------
def write_models_json(or_models, meta, counts):
    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_count": len(or_models),
            "sources": meta.get("sources", {}),
            "coverage": counts,
            "note": (
                "Each model carries raw benchmark data under benchmarks.<source>. "
                "No scores are blended across sources."
            ),
        },
        "models": or_models,
    }
    path = os.path.join(OUTDIR, "models.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# Output: recommended.json (per-benchmark top-10, no mixing)
# Walks the new benchmarks/<source>/ subfolders.
# ---------------------------------------------------------------------------
def write_recommended_json():
    rec = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "description": (
                "Per-benchmark shortlists. No score mixing. "
                "Each list is a pure ranking from one source."
            ),
            "benchmarks": {},
        },
        "recommended": {},
    }

    for subdir in sorted(WRITTEN.keys()):
        sdir = os.path.join("benchmarks", subdir)
        if not os.path.isdir(sdir):
            continue
        for fname in sorted(os.listdir(sdir)):
            if not fname.endswith(".json"):
                continue
            bname = fname[:-5]
            path = os.path.join(sdir, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception:
                continue
            models = data.get("models", [])[:10]
            rec["recommended"][bname] = models
            rec["meta"]["benchmarks"][bname] = {
                "source": data.get("meta", {}).get("source_url", "unknown"),
                "subdir": subdir,
                "model_count": len(data.get("models", [])),
                "top_n": len(models),
            }

    path = os.path.join(OUTDIR, "recommended.json")
    with open(path, "w") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# Output: per-source OVERVIEW.md + benchmarks/README.md index
# ---------------------------------------------------------------------------
def _model_score_str(m):
    """Render a model's score for an OVERVIEW row."""
    if "scores" in m and m.get("scores"):
        return ", ".join(
            f"{s.get('name', '?')}: {s.get('score')}" for s in m["scores"]
        )
    score = m.get("score")
    if score is None:
        return "—"
    if isinstance(score, float):
        return f"{score:.3f}"
    return str(score)


def write_source_overview(subdir, meta):
    """Write benchmarks/<subdir>/OVERVIEW.md with the top 10 of each bench."""
    sdir = os.path.join("benchmarks", subdir)
    if not os.path.isdir(sdir):
        return None
    benches = meta.get("benches", {})
    L = [f"# {meta.get('title', subdir)}\n"]
    src = meta.get("source_url", "")
    if src:
        L.append(f"> Source: [{src}]({src})\n")
    L.append(f"{meta.get('desc', '')}\n")
    L.append(
        "Each table is a **pure ranking on a single metric**. "
        "No scores are mixed across benchmarks.\n"
    )

    for bname in sorted(WRITTEN.get(subdir, [])):
        if bname not in benches:
            continue
        title, explain = benches[bname]
        path = os.path.join(sdir, f"{bname}.json")
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue
        models = data.get("models", [])[:10]
        L.append(f"## {title}\n")
        L.append(f"_{explain}_\n")
        L.append("")
        if not models:
            L.append("_No models yet._\n")
            continue
        L.append("| # | Model | Score |")
        L.append("|---|-------|------:|")
        for i, m in enumerate(models, 1):
            L.append(f"| {i} | `{m.get('model', '?')}` | {_model_score_str(m)} |")
        L.append("")

    out = os.path.join(sdir, "OVERVIEW.md")
    with open(out, "w") as f:
        f.write("\n".join(L))
    return out


def write_benchmarks_readme():
    """Write benchmarks/README.md index linking to each subfolder OVERVIEW.md."""
    L = ["# ModelCompass Benchmarks\n"]
    L.append(
        "Every benchmark lives in its own subfolder. Each subfolder contains "
        "raw `*.json` ranking files plus an `OVERVIEW.md` with the top 10 of "
        "each benchmark, explained.\n"
    )
    L.append("**No scores are mixed across benchmarks.**\n")
    for subdir, meta in SOURCE_META.items():
        if not WRITTEN.get(subdir):
            continue
        url = meta.get("source_url", "")
        src_line = f" — [{url}]({url})" if url else ""
        L.append(f"## [{meta.get('title', subdir)}](./{subdir}/OVERVIEW.md){src_line}\n")
        L.append(f"{meta.get('desc', '')}\n")
        for bname in sorted(WRITTEN.get(subdir, [])):
            title, _ = meta.get("benches", {}).get(bname, (bname, ""))
            L.append(f"- [{title}](./{subdir}/{bname}.json)")
        L.append("")

    out = os.path.join("benchmarks", "README.md")
    with open(out, "w") as f:
        f.write("\n".join(L))
    return out


# ---------------------------------------------------------------------------
# Output: consensus (Borda count, placement-based only) -> benchmarks/consensus/
# ---------------------------------------------------------------------------
def write_consensus():
    subdir = "consensus"
    borda = {}
    N = 10

    # Walk every benchmark json across all source subfolders
    for sdir in sorted(WRITTEN.keys()):
        base = os.path.join("benchmarks", sdir)
        if not os.path.isdir(base):
            continue
        for fname in sorted(os.listdir(base)):
            if not fname.endswith(".json"):
                continue
            bname = fname[:-5]
            path = os.path.join(base, fname)
            try:
                with open(path) as f:
                    data = json.load(f)
            except Exception:
                continue
            models = data.get("models", [])[:N]
            for i, m in enumerate(models):
                model_id = m.get("model", "")
                score = m.get("score")
                if model_id not in borda:
                    borda[model_id] = {
                        "model": model_id,
                        "top_appearances": 0,
                        "borda_points": 0,
                        "benchmarks": {},
                    }
                borda[model_id]["top_appearances"] += 1
                borda[model_id]["borda_points"] += max(0, N - i)
                borda[model_id]["benchmarks"][bname] = {
                    "rank": i + 1,
                    "score": score,
                }

    ranked = sorted(
        borda.values(), key=lambda x: (-x["top_appearances"], -x["borda_points"])
    )

    out = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "method": "borda_count",
            "description": (
                "Placement agreement across benchmarks. "
                "No score mixing — counts how many top-10 lists each model appears in."
            ),
            "N": N,
        },
        "consensus": ranked,
    }

    _write_benchmark_json(subdir, "consensus", out.get("meta", {}), [])
    # consensus.json carries the full ranked list
    cdir = os.path.join("benchmarks", subdir)
    os.makedirs(cdir, exist_ok=True)
    with open(os.path.join(cdir, "consensus.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    WRITTEN.setdefault(subdir, []).append("consensus")
    return os.path.join(cdir, "consensus.json")


def write_consensus_overview():
    """Write benchmarks/consensus/OVERVIEW.md (top-20 of the Borda ranking)."""
    subdir = "consensus"
    cdir = os.path.join("benchmarks", subdir)
    path = os.path.join(cdir, "consensus.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)

    L = ["# Consensus (Borda)\n"]
    L.append(
        "Placement agreement across all benchmarks. A model's rank here is "
        "how many top-10 lists it appears in (Borda points as tiebreak) — "
        "**never an averaged score**.\n"
    )
    L.append("| Rank | Model | Top-10 Appearances | Borda Points | Benchmarks |")
    L.append("|------|-------|--------------------:|-------------:|------------|")
    for i, entry in enumerate(data.get("consensus", [])[:20], 1):
        bm_list = sorted(entry.get("benchmarks", {}).keys())
        bm_display = ", ".join(bm_list[:5])
        if len(bm_list) > 5:
            bm_display += "…"
        L.append(
            f"| {i} | `{entry['model']}` | "
            f"{entry['top_appearances']} | {entry['borda_points']} | {bm_display} |"
        )
    out = os.path.join(cdir, "OVERVIEW.md")
    with open(out, "w") as f:
        f.write("\n".join(L))
    return out


# ---------------------------------------------------------------------------
# Output: archive — mirrors benchmarks/ into archive/<YYYY-MM>/<YYYY-MM-DD>/
# ---------------------------------------------------------------------------
def write_archive():
    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    day = now.strftime("%Y-%m-%d")
    dest_root = os.path.join("archive", month, day)
    os.makedirs(dest_root, exist_ok=True)

    # Mirror every benchmarks/<subdir>/*.json into archive/<YYYY-MM>/<YYYY-MM-DD>/<subdir>/
    copied = 0
    for subdir in sorted(WRITTEN.keys()):
        base = os.path.join("benchmarks", subdir)
        if not os.path.isdir(base):
            continue
        for fname in sorted(os.listdir(base)):
            if not fname.endswith(".json"):
                continue
            dest_dir = os.path.join(dest_root, subdir)
            os.makedirs(dest_dir, exist_ok=True)
            src = os.path.join(base, fname)
            with open(src) as f:
                content = f.read()
            with open(os.path.join(dest_dir, fname), "w") as f:
                f.write(content)
            copied += 1

    # Snapshot the catalog + recommended.json at top of this snapshot
    for top in ("models.json", "recommended.json"):
        src = os.path.join(OUTDIR, top)
        if os.path.exists(src):
            with open(src) as f:
                content = f.read()
            with open(os.path.join(dest_root, top), "w") as f:
                f.write(content)

    # Day index README
    idx = [f"# Archive — {day}\n"]
    idx.append(
        "Snapshot of the `benchmarks/` tree taken on this date. "
        "Same subfolder layout as `benchmarks/`.\n"
    )
    for subdir in sorted(WRITTEN.keys()):
        idx.append(f"- [{subdir}/](./{subdir}/)")
    with open(os.path.join(dest_root, "README.md"), "w") as f:
        f.write("\n".join(idx))

    return dest_root, copied


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="ModelCompass generator")
    parser.add_argument(
        "--archive", action="store_true", help="also write weekly archive snapshot"
    )
    parser.add_argument(
        "--aa-key",
        default=os.environ.get("ARTIFICIAL_ANALYSIS_KEY", ""),
        help="Artificial Analysis API key",
    )
    args = parser.parse_args()

    log("=== Fetching sources ===")

    # 1. OpenRouter catalog
    or_models = fetch_openrouter()
    log(f"OpenRouter: {len(or_models)} models")

    # 2. Artificial Analysis
    aa, aa_note = fetch_artificial_analysis(args.aa_key)
    log(f"Artificial Analysis: {aa_note}")

    # 3. arena.ai — known leaderboards (fetched live), scrape-discovery fallback
    arena_data = {}
    slugs = discover_arena_slugs()
    log(f"Arena.ai: discovered {len(slugs)} leaderboards")
    for slug in slugs:
        lb, note = fetch_arena_leaderboard(slug)
        if lb:
            arena_data[slug] = lb
            log(f"  {slug}: {note} ({lb['meta']['model_count']} models)")
        else:
            log(f"  {slug}: {note}")

    # 4. BenchLM
    benchlm, benchlm_note = fetch_benchlm()
    log(f"BenchLM: {benchlm_note}")

    # Merge (cross-reference only, no blending)
    counts = merge(or_models, aa, arena_data, benchlm or [])
    log(f"Merged: {counts}")

    # Ensure output dirs — benchmarks/ is rebuilt fresh each run
    if os.path.isdir("benchmarks"):
        import shutil
        shutil.rmtree("benchmarks")
    os.makedirs("benchmarks", exist_ok=True)
    WRITTEN.clear()

    # Write per-benchmark files (into per-source subfolders)
    log("=== Writing per-benchmark files ===")
    write_aa_benchmarks(or_models)
    write_arena_benchmarks(arena_data)
    write_benchlm_benchmarks(benchlm or [])

    # Write catalog
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "openrouter": "ok",
            "artificial_analysis": aa_note,
            "arena_ai": f"ok ({len(arena_data)} leaderboards)",
            "benchlm": benchlm_note,
        },
    }
    write_models_json(or_models, meta, counts)
    log(f"wrote models.json ({len(or_models)} models)")

    # Per-source OVERVIEW.md + benchmarks/README.md index
    for subdir, smeta in SOURCE_META.items():
        if WRITTEN.get(subdir):
            write_source_overview(subdir, smeta)
    write_benchmarks_readme()
    log("wrote benchmarks/<source>/OVERVIEW.md + benchmarks/README.md")

    # Write recommended.json (per-benchmark shortlists)
    write_recommended_json()
    log("wrote recommended.json")

    # Write consensus (into benchmarks/consensus/) + its OVERVIEW.md
    write_consensus()
    write_consensus_overview()
    log("wrote benchmarks/consensus/")

    # Archive
    if args.archive:
        dest, copied = write_archive()
        log(f"wrote {dest} ({copied} files)")

    log("=== Done ===")


if __name__ == "__main__":
    main()
