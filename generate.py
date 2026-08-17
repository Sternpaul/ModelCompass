#!/usr/bin/env python3
"""
ModelCompass generator — pure per-benchmark rankings, no mixing.

Sources (all scraped directly, no third-party snapshots):
 1. OpenRouter /api/v1/models         -> catalog: pricing, context, modality, flags
 2. Artificial Analysis API v2        -> per-dimension indices (intelligence, coding,
                                         agentic, math, multilingual, openness)
 3. arena.ai (Jina Reader)            -> LMArena ELO rankings (text, code, vision,
                                         image-edit, search, agent, …)
 4. aider polyglot YAML (raw GitHub)  -> real coding pass rates
 5. BenchLM (MIT JSON)                -> 437 benchmarks across 388 models
 6. SWE-bench raw JSON (GitHub)       -> % resolved per model

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
AIDER_YAML = (
    "https://raw.githubusercontent.com/Aider-AI/aider/main/"
    "aider/website/_data/polyglot_leaderboard.yml"
)
ARENA_BASE = "https://arena.ai/leaderboard/"
JINA_BASE = "https://r.jina.ai/"
BENCHLM_BASE = "https://benchlm.ai/data"
SWEBENCH_INFO = (
    "https://raw.githubusercontent.com/SWE-bench/swe-bench.github.io/"
    "master/data/info_for_leaderboard.json"
)
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
# Source 3: aider polyglot
# ---------------------------------------------------------------------------
def fetch_aider():
    if yaml is None:
        return {}, "pyyaml not installed"
    try:
        req = urllib.request.Request(
            AIDER_YAML, headers={"User-Agent": "modelcompass/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            data = yaml.safe_load(r.read().decode("utf-8"))
    except Exception as e:
        return {}, str(e)

    out = {}
    for row in data or []:
        name = row.get("model")
        if not name:
            continue
        base = norm(name)
        out[base] = {
            "name": name,
            "base": base,
            "pass_rate_1": scale(row.get("pass_rate_1")),
            "pass_rate_2": scale(row.get("pass_rate_2")),
            "total_cost": row.get("total_cost"),
            "seconds_per_case": row.get("seconds_per_case"),
            "date": str(row.get("date")) if row.get("date") is not None else None,
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


def discover_arena_slugs():
    """Discover all arena.ai leaderboard slugs from the overview page."""
    try:
        text = fetch_text(f"{JINA_BASE}{ARENA_BASE}")
    except Exception as e:
        log(f"Failed to discover arena slugs: {e}")
        return []
    slugs = re.findall(r"arena\.ai/leaderboard/([a-z][a-z0-9-]*)", text)
    return sorted(set(slugs))


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
# Source 6: SWE-bench raw result JSON
# ---------------------------------------------------------------------------
def fetch_swebench():
    """Fetch per-model SWE-bench results from the public GitHub repo."""
    try:
        data = fetch_json(SWEBENCH_INFO, timeout=60)
    except Exception as e:
        return {}, str(e)
    out = {}
    for model_id, tasks in data.items():
        resolved = sum(1 for t in tasks.values() if t.get("resolved"))
        total = len(tasks)
        out[model_id] = {
            "model": model_id,
            "resolved": resolved,
            "total": total,
            "pass_rate": resolved / total if total > 0 else None,
            "total_cost": sum(t.get("cost", 0) for t in tasks.values()),
        }
    return out, f"ok ({len(out)} models)"


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


def merge(or_models, aa, aider, arena, benchlm, swe):
    """Attach raw benchmark data to OpenRouter models.
    Each source stays in its own namespace under benchmarks.<source>.
    """
    or_by_id = {}
    or_by_norm = {}
    or_by_slug_only = {}
    for m in or_models:
        mid = m["id"].lower()
        or_by_id[mid] = m
        or_by_norm.setdefault(norm(m["name"]), []).append(m)
        slug_only = mid.split("/", 1)[-1] if "/" in mid else mid
        or_by_slug_only.setdefault(slug_only, []).append(m)

    counts = {"aa": 0, "aider": 0, "arena": 0, "benchlm": 0, "swe": 0}

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

    # Attach aider
    if aider:
        for base, a in aider.items():
            if base in or_by_norm:
                for m in or_by_norm[base]:
                    m["benchmarks"]["aider"] = a
                    counts["aider"] += 1
                    break

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

    # Attach SWE-bench
    if swe:
        for model_id, swe_data in swe.items():
            mid = model_id.lower()
            if mid in or_by_id:
                or_by_id[mid]["benchmarks"]["swe"] = swe_data
                counts["swe"] += 1
            else:
                nn = norm(model_id)
                if nn in or_by_norm:
                    or_by_norm[nn][0]["benchmarks"]["swe"] = swe_data
                    counts["swe"] += 1

    return counts


# ---------------------------------------------------------------------------
# Output: per-benchmark files
# ---------------------------------------------------------------------------
def _write_benchmark_json(bname, meta_info, models_list):
    os.makedirs("benchmarks", exist_ok=True)
    data = {"meta": meta_info, "models": models_list}
    path = f"benchmarks/{bname}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def write_aa_benchmarks(or_models):
    """Write per-dimension AA benchmark files."""
    AA_KEYS = {
        "aa_intelligence": "artificial_analysis_intelligence_index",
        "aa_coding": "artificial_analysis_coding_index",
        "aa_agentic": "artificial_analysis_agentic_index",
        "aa_math": "artificial_analysis_math_index",
        "aa_multilingual": "artificial_analysis_multilingual_index",
        "aa_openness": "artificial_analysis_openness_index",
    }
    written = {}
    for bname, eval_key in AA_KEYS.items():
        models_list = []
        for m in or_models:
            bm = m.get("benchmarks", {}).get("aa", {})
            evals = bm.get("evaluations", {})
            val = num(evals.get(eval_key))
            if val is not None:
                models_list.append(
                    {
                        "model": m["id"],
                        "name": m.get("name"),
                        "score": val / 100.0,
                        "raw_score": val,
                    }
                )
        models_list.sort(key=lambda x: x["score"], reverse=True)
        if models_list:
            path = _write_benchmark_json(
                bname,
                {
                    "leaderboard": bname,
                    "source_url": "https://artificialanalysis.ai",
                    "benchmark": eval_key,
                },
                models_list,
            )
            written[bname] = path
    return written


def write_aider_benchmark(aider):
    """Write the aider polyglot leaderboard from the raw source (all models,
    not just ones cross-referenced to OpenRouter)."""
    models_list = []
    for base, bm in aider.items():
        if bm.get("pass_rate_1") is None:
            continue
        models_list.append(
            {
                "model": bm.get("name"),
                "score": bm.get("pass_rate_1"),
                "pass_rate_1": bm.get("pass_rate_1"),
                "pass_rate_2": bm.get("pass_rate_2"),
                "total_cost": bm.get("total_cost"),
            }
        )
    models_list.sort(key=lambda x: x.get("score") or 0, reverse=True)
    if models_list:
        return _write_benchmark_json(
            "aider_coding",
            {
                "leaderboard": "aider_coding",
                "source_url": AIDER_YAML,
                "benchmark": "aider polyglot pass_rate_1",
            },
            models_list,
        )
    return None


def write_arena_benchmarks(arena_data):
    written = {}
    for slug, lb in arena_data.items():
        path = f"benchmarks/arena_{slug}.json"
        with open(path, "w") as f:
            json.dump(lb, f, indent=2, ensure_ascii=False)
        written[slug] = path
    return written


def write_benchlm_benchmarks(benchlm_items):
    """Write BenchLM benchmarks grouped by category.

    BenchLM's raw JSON stores per-category scores under
    scores.displayCategoryScores and per-category ranks under
    ranking.categoryRanks. We use displayCategoryScores for the
    ranking value (None entries are skipped) and attach the category rank.
    """
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
            path = _write_benchmark_json(
                bname,
                {
                    "leaderboard": bname,
                    "source_url": f"{BENCHLM_BASE}/models.json",
                    "benchmark": f"BenchLM {cat}",
                },
                models_list,
            )
            written[bname] = path
    return written


def write_swebench_benchmark(swe_data):
    models_list = []
    for model_id, swe in swe_data.items():
        models_list.append(
            {
                "model": model_id,
                "score": swe.get("pass_rate"),
                "resolved": swe.get("resolved"),
                "total": swe.get("total"),
            }
        )
    models_list.sort(key=lambda x: x.get("score") or 0, reverse=True)
    if models_list:
        return _write_benchmark_json(
            "swe_bench",
            {
                "leaderboard": "swe_bench",
                "source_url": SWEBENCH_INFO,
                "benchmark": "SWE-bench % Resolved",
            },
            models_list,
        )
    return None


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
# ---------------------------------------------------------------------------
def write_recommended_json(benchmarks_dir):
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

    for fname in sorted(os.listdir(benchmarks_dir)):
        if not fname.endswith(".json"):
            continue
        bname = fname[:-5]
        path = os.path.join(benchmarks_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue
        models = data.get("models", [])[:10]
        rec["recommended"][bname] = models
        rec["meta"]["benchmarks"][bname] = {
            "source": data.get("meta", {}).get("source_url", "unknown"),
            "model_count": len(data.get("models", [])),
            "top_n": len(models),
        }

    path = os.path.join(OUTDIR, "recommended.json")
    with open(path, "w") as f:
        json.dump(rec, f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# Output: LEADERBOARD.md (human-readable, per-benchmark tables)
# ---------------------------------------------------------------------------
def write_leaderboard_md(benchmarks_dir):
    L = []
    L.append("# ModelCompass Leaderboard\n")
    L.append(
        f"> Generated {datetime.now(timezone.utc).isoformat()} · "
        "updated daily.\n"
    )
    L.append(
        "Each table is a **pure ranking from one benchmark source**. "
        "No scores are mixed.\n"
    )

    for fname in sorted(os.listdir(benchmarks_dir)):
        if not fname.endswith(".json"):
            continue
        bname = fname[:-5]
        path = os.path.join(benchmarks_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        models = data.get("models", [])[:10]
        meta = data.get("meta", {})
        title = meta.get("leaderboard", bname)
        source_url = meta.get("source_url", "")

        L.append(f"## {title}\n")
        if source_url:
            L.append(f"_Source: [{source_url}]({source_url})_\n")
        L.append("")

        if not models:
            L.append("_No models yet._\n")
            continue

        sample = models[0]
        if "score" in sample and "scores" not in sample:
            # Simple score table
            L.append("| # | Model | Score | 95% CI | Votes |")
            L.append("|---|-------|------:|-------:|------:|")
            for i, m in enumerate(models, 1):
                score = m.get("score", "—")
                ci = m.get("ci", "—")
                votes = m.get("votes", "—")
                L.append(
                    f"| {i} | `{m.get('model', '?')}` | {score} | ±{ci} | {votes} |"
                )
        elif "scores" in sample:
            # Multi-dimension table (arena agent)
            dims = meta.get("dimensions", [])
            if dims:
                header = (
                    "| # | Model | "
                    + " | ".join(dims)
                    + " | Sessions |"
                )
                sep = (
                    "|---|-------|"
                    + "|".join(["------:" for _ in dims])
                    + "|------:|"
                )
                L.append(header)
                L.append(sep)
                for i, m in enumerate(models, 1):
                    scores = m.get("scores", [])
                    score_strs = []
                    for s in scores[: len(dims)]:
                        val = s.get("score")
                        ci_val = s.get("ci")
                        if val is not None and ci_val is not None:
                            score_strs.append(f"{val} ±{ci_val}")
                        elif val is not None:
                            score_strs.append(str(val))
                        else:
                            score_strs.append("—")
                    L.append(
                        f"| {i} | `{m.get('model', '?')}` | "
                        + " | ".join(score_strs)
                        + f" | {m.get('sessions', '—')} |"
                    )
        L.append("")

    path = os.path.join(OUTDIR, "LEADERBOARD.md")
    with open(path, "w") as f:
        f.write("\n".join(L))
    return path


# ---------------------------------------------------------------------------
# Output: consensus (Borda count, placement-based only)
# ---------------------------------------------------------------------------
def write_consensus(benchmarks_dir):
    borda = {}
    N = 10

    for fname in sorted(os.listdir(benchmarks_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(benchmarks_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        models = data.get("models", [])[:N]
        bname = fname[:-5]
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

    os.makedirs("consensus", exist_ok=True)
    path = "consensus/consensus.json"
    with open(path, "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return path


def write_consensus_md():
    path = "consensus/consensus.json"
    if not os.path.exists(path):
        return None

    with open(path) as f:
        data = json.load(f)

    L = []
    L.append("# ModelCompass Consensus\n")
    L.append(f"> Generated {data['meta']['generated_at']}\n")
    L.append(
        "Borda-count agreement: how many benchmarks each model appears "
        "in the top 10. No score mixing — just placement frequency.\n"
    )
    L.append("")
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

    with open("consensus/consensus.md", "w") as f:
        f.write("\n".join(L))
    return "consensus/consensus.md"


# ---------------------------------------------------------------------------
# Output: rankings/famous_rankings.md (static curated view)
# ---------------------------------------------------------------------------
def write_rankings():
    os.makedirs("rankings", exist_ok=True)
    L = []
    L.append("# ModelCompass Famous Rankings\n")
    L.append(
        "Curated view of the most important model rankings, "
        "with current top models from live data.\n"
    )

    famous = [
        (
            "LMArena Text (ELO)",
            "arena_text",
            "Human preference ELO from millions of blind pairwise comparisons.",
        ),
        (
            "LMArena Code (WebDev)",
            "arena_code",
            "Front-end web development and agentic coding.",
        ),
        (
            "LMArena Vision",
            "arena_vision",
            "Image and multimodal understanding.",
        ),
        (
            "LMArena Agent",
            "arena_agent",
            "Agentic task orchestration (Net Improvement, Confirmed Success, …).",
        ),
        (
            "AA Intelligence Index",
            "aa_intelligence",
            "Composite intelligence from Artificial Analysis proprietary evals.",
        ),
        (
            "AA Coding Index",
            "aa_coding",
            "Coding capability from Artificial Analysis.",
        ),
        (
            "AA Agentic Index",
            "aa_agentic",
            "Agentic / tool-use capability from Artificial Analysis.",
        ),
        (
            "aider polyglot coding",
            "aider_coding",
            "Real code generation: 225 Exercism tasks across 6 languages.",
        ),
        (
            "SWE-bench Verified",
            "swe_bench",
            "Percentage of GitHub issues resolved with correct patches.",
        ),
    ]

    for title, bname, desc in famous:
        path = f"benchmarks/{bname}.json"
        if not os.path.exists(path):
            continue
        with open(path) as f:
            data = json.load(f)
        models = data.get("models", [])[:10]
        L.append(f"## {title}\n")
        L.append(f"_{desc}_\n")
        L.append("")
        if not models:
            L.append("_No models yet._\n")
            continue
        for i, m in enumerate(models, 1):
            score = m.get("score")
            score_str = f" — score {score:.3f}" if score is not None else ""
            L.append(f"{i}. `{m.get('model', '?')}`{score_str}")
        L.append("")

    with open("rankings/famous_rankings.md", "w") as f:
        f.write("\n".join(L))


# ---------------------------------------------------------------------------
# Output: archive (weekly snapshot)
# ---------------------------------------------------------------------------
def write_archive():
    os.makedirs("archive", exist_ok=True)
    iso = datetime.now(timezone.utc).isocalendar()
    fname = f"archive/rankings-{iso[0]}-W{iso[1]:02d}.json"
    snapshot = {
        "week": f"{iso[0]}-W{iso[1]:02d}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmarks": {},
        "consensus": {},
    }
    for fname_src in os.listdir("benchmarks"):
        if fname_src.endswith(".json"):
            with open(f"benchmarks/{fname_src}") as f:
                snapshot["benchmarks"][fname_src[:-5]] = json.load(f)
    if os.path.exists("consensus/consensus.json"):
        with open("consensus/consensus.json") as f:
            snapshot["consensus"] = json.load(f)

    with open(fname, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return fname


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

    # 3. aider polyglot
    aider, aider_note = fetch_aider()
    log(f"aider polyglot: {aider_note}")

    # 4. arena.ai — discover all leaderboards, then fetch each
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

    # 5. BenchLM
    benchlm, benchlm_note = fetch_benchlm()
    log(f"BenchLM: {benchlm_note}")

    # 6. SWE-bench
    swe, swe_note = fetch_swebench()
    log(f"SWE-bench: {swe_note}")

    # Merge (cross-reference only, no blending)
    counts = merge(or_models, aa, aider, arena_data, benchlm or [], swe)
    log(f"Merged: {counts}")

    # Ensure output dirs
    os.makedirs("benchmarks", exist_ok=True)
    os.makedirs("consensus", exist_ok=True)

    # Write per-benchmark files
    log("=== Writing per-benchmark files ===")
    write_aa_benchmarks(or_models)
    write_aider_benchmark(aider)
    write_arena_benchmarks(arena_data)
    write_benchlm_benchmarks(benchlm or [])
    write_swebench_benchmark(swe)

    # Write catalog
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "openrouter": "ok",
            "artificial_analysis": aa_note,
            "aider_polyglot": aider_note,
            "arena_ai": f"ok ({len(arena_data)} leaderboards)",
            "benchlm": benchlm_note,
            "swe_bench": swe_note,
        },
    }
    write_models_json(or_models, meta, counts)
    log(f"wrote models.json ({len(or_models)} models)")

    # Write recommended.json (per-benchmark shortlists)
    write_recommended_json("benchmarks")
    log("wrote recommended.json")

    # Write consensus
    write_consensus("benchmarks")
    write_consensus_md()
    log("wrote consensus/")

    # Write leaderboard
    write_leaderboard_md("benchmarks")
    log("wrote LEADERBOARD.md")

    # Write rankings
    write_rankings()
    log("wrote rankings/famous_rankings.md")

    # Archive
    if args.archive:
        write_archive()
        log("wrote archive/")

    log("=== Done ===")


if __name__ == "__main__":
    main()
