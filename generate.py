#!/usr/bin/env python3
"""
ModelCompass generator.

Fetches multiple live sources, merges them into one unified catalog, scores
models per task from REAL benchmark data, and emits machine-readable outputs
(models.json, recommended.json, models.csv, INDEX.md), a curated
rankings/ folder of famous benchmarks, and (with --archive) a weekly snapshot
under archive/.

Sources
-------
1. OpenRouter /api/v1/models        (no key)  -> catalog: pricing, context,
                                                 modality, capability flags,
                                                 knowledge cutoff, recency.
2. Artificial Analysis API v2       (key)    -> intelligence/coding/agentic/
                                                 math/multilingual/openness
                                                 indices + raw benchmarks
                                                 (GPQA, HLE, MMLU-Pro, AIME,
                                                 LiveCodeBench, Terminal-Bench,
                                                 IFBench, SciCode, ...) + speed.
3. aider polyglot YAML (raw GitHub) (no key) -> real coding pass rates.

All sources are fetched defensively: a failure in one never breaks the others.
The final `meta.sources` lists which succeeded.

Scoring is TRANSPARENT: each task score is a documented weighted blend of
real benchmark values found on the record. Models missing a benchmark simply
contribute null to that blend (not zero). See meta.methodology.
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

OR_API = "https://openrouter.ai/api/v1/models"
AA_API = "https://artificialanalysis.ai/api/v2/data/llms/models"
AIDER_YAML = ("https://raw.githubusercontent.com/Aider-AI/aider/main/"
              "aider/website/_data/polyglot_leaderboard.yml")
OUTDIR = "."

# Variant suffixes that denote derived/equivalent offerings of the same family.
VARIANT_SUFFIX = re.compile(
    r"(:batch|:nitro|:floor|:online|:offline|:cached|:extended|:free"
    r"|:thinking|:rlhf|-preview|-latest|-exp|-alpha|-beta"
    r"|-202\d{6}|-v\d+)$"
)


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def fetch_json(url, headers=None, timeout=60):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "modelcompass/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def family_id(mid):
    if "/" in mid:
        p, r = mid.split("/", 1)
    else:
        p, r = "", mid
    r = VARIANT_SUFFIX.sub("", r)
    return f"{p}/{r}" if p else r


def variant_quality(mid):
    return 1 if family_id(mid) == mid else 0


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


def avg_non_null(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


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
        ctx = max(m.get("context_length") or 0,
                  (m.get("top_provider", {}) or {}).get("context_length") or 0)
        p_in = scale(m.get("pricing", {}).get("prompt"), 1e-6)   # -> per 1M
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
            "supports_json": ("structured_outputs" in params) or ("response_format" in params),
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
            "task_scores": {},
        }
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Source 2: Artificial Analysis (key required)
# ---------------------------------------------------------------------------
def fetch_artificial_analysis(api_key):
    if not api_key:
        return None, "no API key"
    req = urllib.request.Request(
        AA_API,
        headers={
            "User-Agent": "modelcompass/1.0",
            "x-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.reason}"
    except Exception as e:  # noqa
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
# Source 3: aider polyglot coding benchmark (raw GitHub YAML, no key)
# ---------------------------------------------------------------------------
def fetch_aider():
    if yaml is None:
        return {}, "pyyaml not installed"
    try:
        req = urllib.request.Request(AIDER_YAML, headers={"User-Agent": "modelcompass/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = yaml.safe_load(r.read().decode("utf-8"))
    except Exception as e:  # noqa
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
            "pass_rate_1": scale(row.get("pass_rate_1")),       # 0-100 -> 0-1
            "pass_rate_2": scale(row.get("pass_rate_2")),
            "total_cost": row.get("total_cost"),
            "seconds_per_case": row.get("seconds_per_case"),
            "date": str(row.get("date")) if row.get("date") is not None else None,
        }
    return out, f"ok ({len(out)} models)"


# ---------------------------------------------------------------------------
# Merge OpenRouter with benchmark sources
# ---------------------------------------------------------------------------
def merge(or_models, aa, aider):
    or_by_id = {m["id"].lower(): m for m in or_models}
    or_by_norm = {}
    for m in or_models:
        or_by_norm.setdefault(norm(m["name"]), []).append(m)

    aa_used, aider_used = set(), set()

    # attach AA
    for key, a in (aa or {}).items():
        target = or_by_id.get(key)
        if not target:
            nn = norm(a.get("name", ""))
            if nn in or_by_norm:
                target = or_by_norm[nn][0]
        if target:
            ev = a.get("evaluations", {})
            target["benchmarks"]["aa"] = ev
            target["benchmarks"]["aa_speed"] = {
                "median_tps": a.get("median_tps"),
                "ttft_s": a.get("ttft"),
            }
            if target["price_per_million"]["prompt"] is None and a["pricing"]["prompt"] is not None:
                target["price_per_million"] = {
                    "prompt": round(a["pricing"]["prompt"], 6),
                    "completion": round(a["pricing"]["completion"], 6) if a["pricing"]["completion"] else None,
                    "cache_read": None,
                }
            aa_used.add(target["id"])

    # attach aider coding
    for base, a in (aider or {}).items():
        best, best_score = None, 0
        for m in or_models:
            om = norm(m["id"].split("/")[-1])
            on = norm(m["name"])
            sc = 0
            if base and (base in om or om in base):
                sc = 2
            elif base and (base in on or on in base):
                sc = 2
            else:
                bt = set(base.split())
                ot = set(om.split()) | set(on.split())
                if bt and ot:
                    ov = len(bt & ot) / len(bt)
                    sc = ov
            if sc > best_score:
                best, best_score = m, sc
        if best and best_score >= 0.5:
            best["benchmarks"]["aider_polyglot"] = {
                "pass_rate_1": a["pass_rate_1"],
                "pass_rate_2": a["pass_rate_2"],
                "total_cost": a["total_cost"],
                "seconds_per_case": a["seconds_per_case"],
                "date": a["date"],
            }
            aider_used.add(best["id"])

    return aa_used, aider_used


# ---------------------------------------------------------------------------
# Scoring (transparent, real benchmarks)
# ---------------------------------------------------------------------------
def aa_evals(rec):
    return rec.get("benchmarks", {}).get("aa", {}) or {}


def s_overall(r):
    e = aa_evals(r)
    return avg_non_null([
        scale(e.get("artificial_analysis_intelligence_index"), 100),
        scale(e.get("artificial_analysis_coding_index"), 100),
        scale(e.get("artificial_analysis_agentic_index"), 100),
        scale(e.get("artificial_analysis_math_index"), 100),
        scale(e.get("artificial_analysis_multilingual_index"), 100),
    ])


def s_coding(r):
    e = aa_evals(r)
    aider = r.get("benchmarks", {}).get("aider_polyglot", {})
    aider_v = scale(aider.get("pass_rate_1"), 100)  # 0-100 -> 0-1
    return avg_non_null([
        scale(e.get("artificial_analysis_coding_index"), 100),
        e.get("livecodebench"),
        aider_v,
    ])


def s_reasoning(r):
    e = aa_evals(r)
    return avg_non_null([
        scale(e.get("artificial_analysis_intelligence_index"), 100),
        e.get("gpqa"),
        e.get("aime"),
        e.get("hle"),
    ])


def s_math(r):
    e = aa_evals(r)
    return avg_non_null([
        scale(e.get("artificial_analysis_math_index"), 100),
        e.get("aime"),
        e.get("math_500"),
        e.get("scicode"),
    ])


def s_agents(r):
    e = aa_evals(r)
    return avg_non_null([
        scale(e.get("artificial_analysis_agentic_index"), 100),
        e.get("terminal_bench"),
        e.get("ifbench"),
    ])


def s_open_weight(r):
    e = aa_evals(r)
    return avg_non_null([
        scale(e.get("artificial_analysis_intelligence_index"), 100),
        scale(e.get("artificial_analysis_openness_index"), 100),
        scale(e.get("artificial_analysis_coding_index"), 100),
    ])


def capability_score(r):
    s = 0.0
    if r.get("supports_reasoning"):
        s += 2.0
    if r.get("supports_tools"):
        s += 1.0
    if r.get("supports_json"):
        s += 0.5
    if r.get("supports_caching"):
        s += 0.3
    if r.get("context"):
        s += min(r["context"] / 1_000_000.0, 2.0)
    if r.get("created_unix"):
        age = (datetime.now(tz=timezone.utc) - datetime.fromtimestamp(r["created_unix"], tz=timezone.utc)).days
        s += max(0.0, 2.0 * (1 - age / 365.0))
    if r.get("knowledge_cutoff"):
        s += 0.5
    return round(s, 3)


TASKS = {
    "best_overall": (s_overall, lambda r: True, True),
    "best_coding": (s_coding, lambda r: r.get("benchmarks", {}).get("aider_polyglot") or aa_evals(r).get("artificial_analysis_coding_index") or aa_evals(r).get("livecodebench"), True),
    "best_reasoning": (s_reasoning, lambda r: True, True),
    "best_math": (s_math, lambda r: True, True),
    "best_agents": (s_agents, lambda r: True, True),
    "best_open_weight": (s_open_weight, lambda r: r.get("open_weight"), True),
    "best_vision": (s_overall, lambda r: r.get("is_vision"), True),
    "best_cheap": (s_overall, lambda r: (r.get("price_per_million", {}).get("prompt") or 1e9) <= 0.5 and r.get("supports_reasoning"), False),
}


def recommend(real, task_key, top=10):
    score_fn, filter_fn, use_bench = TASKS[task_key]
    seq = [m for m in real if filter_fn(m)]
    for m in seq:
        ts = score_fn(m)
        m["_task"] = ts
        m["_fallback"] = capability_score(m) / 12.0
    if use_bench:
        seq.sort(key=lambda m: ((m["_task"] is not None), m["_task"] or 0, m["_fallback"]), reverse=True)
    else:
        seq.sort(key=lambda m: (m["price_per_million"]["prompt"] or 1e9, -(m["_task"] or 0)))
    seen, out = set(), []
    for m in seq:
        fam = family_id(m["id"])
        if fam in seen:
            continue
        seen.add(fam)
        out.append(m)
        if len(out) >= top:
            break
    return out


def slim(m, task_key):
    b = m.get("benchmarks", {})
    e = b.get("aa", {})
    return {
        "id": m["id"],
        "name": m.get("name"),
        "provider": m.get("provider"),
        "task_score": round(m.get("_task"), 4) if m.get("_task") is not None else None,
        "context": m.get("context"),
        "price_per_million": m.get("price_per_million"),
        "capability_flags": [f for f in ("reasoning", "tools", "json", "caching")
                             if m.get("supports_" + f)],
        "is_vision": m.get("is_vision"),
        "open_weight": m.get("open_weight"),
        "benchmarks": {
            "aa_intelligence_index": e.get("artificial_analysis_intelligence_index"),
            "aa_coding_index": e.get("artificial_analysis_coding_index"),
            "aa_agentic_index": e.get("artificial_analysis_agentic_index"),
            "aa_math_index": e.get("artificial_analysis_math_index"),
            "gpqa": e.get("gpqa"),
            "hle": e.get("hle"),
            "livecodebench": e.get("livecodebench"),
            "aime": e.get("aime"),
            "mmlu_pro": e.get("mmlu_pro"),
            "aider_polyglot_pass_rate_1": (b.get("aider_polyglot") or {}).get("pass_rate_1"),
        },
    }


# ---------------------------------------------------------------------------
# Curated famous rankings (data-backed)
# ---------------------------------------------------------------------------
FAMOUS_RANKINGS = [
    ("Artificial Analysis Intelligence Index", "best_overall",
     "Composite of reasoning, knowledge, math, coding & agentic. The headline "
     "'smartest model' ranking."),
    ("Coding (aider polyglot + LiveCodeBench)", "best_coding",
     "Real code generation: 225 Exercism exercises across 6 languages + LiveCodeBench."),
    ("Math (AIME / MMLU-Pro / SciCode)", "best_math",
     "Quantitative & competition math ability."),
    ("Reasoning (GPQA / HLE)", "best_reasoning",
     "Graduate-level science & 'Humanity's Last Exam' reasoning."),
    ("Agentic (Terminal-Bench / AA agentic)", "best_agents",
     "Tool use, terminal/bash, multi-step agentic tasks."),
    ("Vision (multimodal)", "best_vision",
     "Image understanding for multimodal models."),
    ("Best value (low cost)", "best_cheap",
     "Cheapest capable reasoning models."),
    ("Open-weight", "best_open_weight",
     "Best models with openly-licensed weights."),
]


def write_rankings(recommended, meta):
    os.makedirs("rankings", exist_ok=True)
    lines = ["# Famous Rankings (ModelCompass)\n",
             f"_Generated {meta['generated_at']}. Top models per famous benchmark, "
             "pulled from live benchmark data._\n"]
    data = {"generated_at": meta["generated_at"], "rankings": {}}
    for title, task, desc in FAMOUS_RANKINGS:
        rows = recommended.get(task, [])[:10]
        lines.append(f"## {title}\n")
        lines.append(f"_{desc}_\n")
        lines.append("")
        data["rankings"][task] = {
            "title": title,
            "description": desc,
            "models": [{"id": r["id"], "name": r.get("name"),
                        "task_score": r.get("task_score")} for r in rows],
        }
        if not rows:
            lines.append("_No benchmarked models yet._\n")
            continue
        for i, r in enumerate(rows, 1):
            sc = r.get("task_score")
            sc = f" — score {sc}" if sc is not None else ""
            lines.append(f"{i}. `{r['id']}`{sc}")
        lines.append("")
    with open("rankings/famous_rankings.md", "w") as f:
        f.write("\n".join(lines))
    with open("rankings/famous_rankings.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_archive(recommended, meta):
    os.makedirs("archive", exist_ok=True)
    iso = datetime.now(tz=timezone.utc).isocalendar()
    week = f"{iso[0]}-W{iso[1]:02d}"
    fname = f"archive/rankings-{week}.json"
    snapshot = {
        "week": week,
        "generated_at": meta["generated_at"],
        "model_count": meta["model_count"],
        "recommended": recommended,
    }
    with open(fname, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    return fname


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(archive=False):
    now = datetime.now(tz=timezone.utc)
    log("== ModelCompass generate ==")
    aa_key = os.environ.get("ARTIFICIAL_ANALYSIS_KEY")

    or_models = fetch_openrouter()
    log(f"OpenRouter: {len(or_models)} models")
    real = [m for m in or_models if not m["synthetic"]]

    aa, aa_note = fetch_artificial_analysis(aa_key)
    log(f"Artificial Analysis: {aa_note}")
    aider, aider_note = fetch_aider()
    log(f"aider polyglot: {aider_note}")

    aa_used, aider_used = merge(or_models, aa, aider)
    log(f"merged -> AA on {len(aa_used)}, aider on {len(aider_used)}")

    recommended = {}
    for task in TASKS:
        recommended[task] = [slim(m, task) for m in recommend(real, task)]

    for m in or_models:
        m["task_scores"] = {
            "overall": s_overall(m),
            "coding": s_coding(m),
            "reasoning": s_reasoning(m),
            "math": s_math(m),
            "agents": s_agents(m),
            "open_weight": s_open_weight(m),
        }
        m["capability_score"] = capability_score(m)

    meta = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_count": len(real),
        "synthetic_excluded": len(or_models) - len(real),
        "update_cadence": "daily (GitHub Actions)",
        "secret_env": "ARTIFICIAL_ANALYSIS_KEY",
        "sources": {
            "openrouter": f"ok ({len(or_models)} raw)",
            "artificial_analysis": aa_note,
            "aider_polyglot": aider_note,
        },
        "coverage": {
            "with_aa_benchmarks": len(aa_used),
            "with_aider_coding": len(aider_used),
        },
        "disclaimer": (
            "Recommended lists are transparent weighted blends of REAL benchmark "
            "values (Artificial Analysis indices + raw benchmarks, aider polyglot "
            "coding). Models missing a benchmark contribute null (not zero). "
            "Verify high-stakes choices against primary sources."
        ),
        "methodology": (
            "Each task score = weighted mean of available normalized 0-1 benchmarks "
            "(AA indices /100; GPQA/HLE/LiveCodeBench/AIME/Math-500/SciCode already "
            "0-1; aider pass_rate /100). Sources merged by provider+slug then name "
            "fuzzy-match. Variant families collapsed to canonical base model in "
            "shortlists."
        ),
    }

    out = {"meta": meta, "recommended": recommended, "models": or_models}

    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "models.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    with open(os.path.join(OUTDIR, "recommended.json"), "w") as f:
        json.dump({"meta": meta, "recommended": recommended}, f, indent=2, ensure_ascii=False)

    cols = ["id", "name", "provider", "source", "context", "modality", "is_vision",
            "supports_reasoning", "supports_tools", "supports_json", "open_weight",
            "knowledge_cutoff", "price_prompt_per_million", "price_completion_per_million",
            "aa_intelligence_index", "aa_coding_index", "aa_agentic_index", "aa_math_index",
            "gpqa", "hle", "livecodebench", "aider_pass_rate_1",
            "task_overall", "task_coding", "task_reasoning"]
    with open(os.path.join(OUTDIR, "models.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for m in or_models:
            e = m.get("benchmarks", {}).get("aa", {}) or {}
            ap = m.get("benchmarks", {}).get("aider_polyglot", {}) or {}
            ts = m.get("task_scores", {})
            w.writerow([
                m["id"], m.get("name"), m.get("provider"), m.get("source"),
                m.get("context"), m.get("modality"), m.get("is_vision"),
                m.get("supports_reasoning"), m.get("supports_tools"), m.get("supports_json"),
                m.get("open_weight"), m.get("knowledge_cutoff"),
                m["price_per_million"]["prompt"], m["price_per_million"]["completion"],
                e.get("artificial_analysis_intelligence_index"),
                e.get("artificial_analysis_coding_index"),
                e.get("artificial_analysis_agentic_index"),
                e.get("artificial_analysis_math_index"),
                e.get("gpqa"), e.get("hle"), e.get("livecodebench"),
                ap.get("pass_rate_1"),
                round(ts.get("overall"), 4) if ts.get("overall") is not None else None,
                round(ts.get("coding"), 4) if ts.get("coding") is not None else None,
                round(ts.get("reasoning"), 4) if ts.get("reasoning") is not None else None,
            ])

    write_index_md(meta, recommended)
    write_rankings(recommended, meta)
    write_leaderboard(recommended, meta)
    if archive:
        fn = write_archive(recommended, meta)
        log(f"wrote weekly archive {fn}")

    log("wrote models.json, recommended.json, models.csv, INDEX.md, rankings/")


def write_leaderboard(recommended, meta):
    """Human-readable Markdown leaderboard with comparison tables (GitHub UI)."""
    os.makedirs(OUTDIR, exist_ok=True)
    L = []
    L.append("# ModelCompass Leaderboard\n")
    L.append(f"> Generated **{meta['generated_at']}** · {meta['model_count']} models · "
             f"updated daily by GitHub Actions.\n")
    L.append("Each table ranks the best models for a task using real benchmark "
             "data (Artificial Analysis indices + aider polyglot coding). "
             "Scores are normalized 0–1 blends; `—` means the model has no "
             "benchmark for that column.\n")

    # sources / coverage summary
    L.append("**Sources:** " + " · ".join(f"{k} ({v})" for k, v in meta["sources"].items()) + "\n")
    L.append(f"**Benchmark coverage:** {meta['coverage'].get('with_aa_benchmarks')} models with "
             f"Artificial Analysis scores, {meta['coverage'].get('with_aider_coding')} with aider coding.\n")

    headers = {
        "best_overall": "🏆 Best Overall",
        "best_coding": "💻 Best Coding",
        "best_reasoning": "🧠 Best Reasoning",
        "best_math": "📐 Best Math",
        "best_agents": "🤖 Best Agentic",
        "best_vision": "👁️ Best Vision",
        "best_open_weight": "🔓 Best Open-Weight",
        "best_cheap": "💰 Best Value (low cost)",
    }

    for task, title in headers.items():
        rows = recommended.get(task, [])[:10]
        L.append(f"## {title}\n")
        if not rows:
            L.append("_No benchmarked models yet._\n")
            continue
        L.append("| # | Model | Score | $/1M in | $/1M out | Context | Reasoning | Vision | Key benchmarks |")
        L.append("|---|-------|------:|--------:|---------:|--------:|:--------:|:------:|----------------|")
        for i, r in enumerate(rows, 1):
            b = r.get("benchmarks", {})
            pm = r.get("price_per_million", {}) or {}
            price_in = pm.get("prompt")
            price_out = pm.get("completion")
            ctx = r.get("context") or 0
            ctx_s = f"{ctx/1000:.0f}k" if ctx < 1_000_000 else f"{ctx/1_000_000:.1f}M"
            ev = []
            if b.get("aa_intelligence_index") is not None:
                ev.append(f"AA-IQ {b['aa_intelligence_index']}")
            if b.get("aa_coding_index") is not None:
                ev.append(f"AA-Code {b['aa_coding_index']}")
            if b.get("livecodebench") is not None:
                ev.append(f"LCB {b['livecodebench']:.2f}")
            if b.get("aider_polyglot_pass_rate_1") is not None:
                ev.append(f"aider {b['aider_polyglot_pass_rate_1']:.0f}%")
            if b.get("gpqa") is not None:
                ev.append(f"GPQA {b['gpqa']:.2f}")
            if b.get("hle") is not None:
                ev.append(f"HLE {b['hle']:.2f}")
            if b.get("aime") is not None:
                ev.append(f"AIME {b['aime']:.2f}")
            L.append(
                f"| {i} | `{r['id']}` | "
                f"{r.get('task_score') if r.get('task_score') is not None else '—'} | "
                f"{price_in if price_in is not None else '—'} | "
                f"{price_out if price_out is not None else '—'} | "
                f"{ctx_s} | "
                f"{'✅' if r.get('capability_flags') and 'reasoning' in r['capability_flags'] else '—'} | "
                f"{'✅' if r.get('is_vision') else '—'} | "
                f"{' · '.join(ev) if ev else '—'} |"
            )
        L.append("")

    L.append("---\n")
    L.append(f"_{meta['disclaimer']}_\n")
    L.append(f"_{meta['methodology']}_\n")

    with open(os.path.join(OUTDIR, "LEADERBOARD.md"), "w") as f:
        f.write("\n".join(L))


def write_index_md(meta, recommended):
    lines = []
    lines.append("# ModelCompass (machine-readable)\n")
    lines.append(f"_Generated {meta['generated_at']} — {meta['model_count']} models. "
                 f"Daily GitHub Action._\n")
    lines.append("## Sources\n")
    for k, v in meta["sources"].items():
        lines.append(f"- **{k}**: {v}")
    lines.append("")
    lines.append("## Coverage\n")
    for k, v in meta["coverage"].items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Recommended shortlists (real benchmarks)\n")
    for k, v in recommended.items():
        lines.append(f"### {k}\n")
        for item in v[:8]:
            ts = item.get("task_score")
            ts = f" (score {ts})" if ts is not None else ""
            lines.append(f"- `{item['id']}`{ts}")
        lines.append("")
    lines.append("## Disclaimer\n" + meta["disclaimer"] + "\n")
    lines.append("## Methodology\n" + meta["methodology"] + "\n")
    with open(os.path.join(OUTDIR, "INDEX.md"), "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", action="store_true",
                    help="also write a weekly snapshot under archive/")
    args = ap.parse_args()
    main(archive=args.archive)
