#!/usr/bin/env python3
"""
ModelCompass generator — pure per-benchmark rankings, no mixing.

Sources (all fetched directly, no third-party snapshots):
 1. OpenRouter /api/v1/models        -> catalog: pricing, context, modality, flags (deduped with models.dev)
 1b. models.dev /api.json            -> catalog: broad universe of "what models exist" (6667 models)
 2. Artificial Analysis API v2       -> raw benchmark spine (~600 models, all written directly)
 3. arena.ai (Jina Reader)           -> LMArena Elo spine (11 leaderboards)
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
# Source 1b: models.dev catalog (broad universe of "what models exist")
# ---------------------------------------------------------------------------
MODELS_DEV_URL = "https://models.dev/api.json"


def fetch_modelsdev():
    """Return (list_of_catalog_recs, note). Deduped against OpenRouter by
    base slug so routers like kilo/openrouter/... don't create dup rows.

    models.dev has NO benchmark scores — it is catalog-only (pricing, context,
    modality, capability flags). It widens the universe so models that exist on
    AA/Arena/BenchLM but not in OpenRouter still get a catalog entry.
    """
    try:
        data = fetch_json(MODELS_DEV_URL, timeout=90)
    except Exception as e:
        return [], f"fetch error: {e}"

    out = []
    for prov, pdata in data.items():
        for mid, mval in (pdata.get("models") or {}).items():
            cost = (mval.get("cost") or {})
            limit = (mval.get("limit") or {})
            mods = (mval.get("modalities") or {})
            in_mods = set(mods.get("input", []) or [])
            out_mods = set(mods.get("output", []) or [])
            p_in = scale(cost.get("input"), 1e-6)
            p_out = scale(cost.get("output"), 1e-6)
            rec = {
                "id": mid,
                "name": mval.get("name", mid),
                "provider": mid.split("/")[0] if "/" in mid else prov,
                "family": family_id(mid),
                "source": "models.dev",
                "created_unix": None,
                "context": limit.get("context"),
                "modality": "/".join(sorted(in_mods | out_mods)) if (in_mods | out_mods) else "",
                "is_vision": "image" in in_mods,
                "is_audio_input": "audio" in in_mods,
                "is_video_input": "video" in in_mods,
                "is_image_output": "image" in out_mods,
                "is_audio_output": "audio" in out_mods,
                "supports_reasoning": bool(mval.get("reasoning")),
                "supports_tools": bool(mval.get("tool_call")),
                "supports_json": False,
                "supports_caching": False,
                "knowledge_cutoff": mval.get("knowledge"),
                "hugging_face_id": None,
                "open_weight": bool(mval.get("open_weights")),
                "synthetic": False,
                "free": mid.endswith(":free"),
                "price_per_million": {
                    "prompt": round(p_in, 6) if p_in is not None else None,
                    "completion": round(p_out, 6) if p_out is not None else None,
                    "cache_read": None,
                },
                "benchmarks": {},
            }
            out.append(rec)
    return out, f"ok ({len(out)} models from {len(data)} providers)"


# ---------------------------------------------------------------------------
# Source 1c: OpenRouter usage rankings (real-world adoption signal)
# ---------------------------------------------------------------------------
OR_RANKINGS_URL = "https://openrouter.ai/api/frontend/v1/rankings/models"


def fetch_or_usage():
    """Return (usage_dict, note). usage_dict maps model_permaslug -> aggregate
    usage over the returned window: total tokens (prompt+completion), request
    count. This is REAL-WORLD USAGE, not a quality benchmark — it lives in its
    own spine and never blends into scores."""
    try:
        data = fetch_json(OR_RANKINGS_URL, timeout=60)["data"]
    except Exception as e:
        return {}, f"fetch error: {e}"
    agg = {}
    for row in data:
        slug = row.get("model_permaslug") or ""
        if not slug:
            continue
        a = agg.setdefault(slug, {"tokens": 0, "requests": 0, "days": set()})
        a["tokens"] += (row.get("total_prompt_tokens") or 0) + (
            row.get("total_completion_tokens") or 0
        )
        a["requests"] += row.get("count") or 0
        if row.get("date"):
            a["days"].add(row["date"][:10])
    for a in agg.values():
        a.pop("days", None)
    return agg, f"ok ({len(agg)} models with live usage)"


# ---------------------------------------------------------------------------
# Source 1d: DeepSWE (datacurve.ai) — agentic software-engineering eval
# ---------------------------------------------------------------------------
DEEPSWE_URL = (
    "https://deepswe.datacurve.ai/artifacts/v1.1/leaderboard-live.json"
)


def fetch_deepswe():
    """Return (rows, note). DeepSWE = pass@1 on 113 real GitHub issues run
    through agent harnesses (mini-swe-agent etc). Fresh artifact JSON with
    generated_at; soft-fail with note if unavailable."""
    try:
        d = fetch_json(DEEPSWE_URL, timeout=60)
    except Exception as e:
        return [], f"fetch error: {e}"
    rows = d.get("rows") or []
    out = []
    for r in rows:
        if not r.get("model"):
            continue
        out.append({
            "model": r["model"],
            "harness": r.get("harness"),
            "reasoning_effort": r.get("reasoning_effort"),
            "pass_rate": r.get("pass_rate"),
            "n_passed": r.get("n_passed"),
            "n_attempted": r.get("n_attempted"),
            "mean_cost_usd": r.get("mean_cost_usd"),
            "mean_output_tokens": r.get("mean_output_tokens"),
        })
    return out, f"ok ({len(out)} configs, generated_at={d.get('generated_at', '?')[:10]})"


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
    # keep only digits / commas (drops trailing labels like "votes")
    digits = re.sub(r"[^0-9,]", "", s.strip())
    digits = digits.replace(",", "")
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _is_sep_row(line):
    """True for a markdown table separator row like |---|---:---|."""
    s = line.strip()
    if not s.startswith("|"):
        return False
    cells = [c.strip() for c in s.strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-+:?", c) for c in cells if c != "")


def _parse_arena_general(content, slug):
    """Parse a general arena.ai leaderboard (text, code, vision, …).

    Change-proof against Arena's display format:
      * Supports the current cell-per-line layout (each field on its own line,
        tab/newline separated) AND legacy markdown `|` tables.
      * Records are anchored on the VENDOR line (contains '·'), not on a column
        header text, so renaming/reordering columns never hides the data.
      * Score / CI / votes are located relative to the vendor line by position,
        with `±` detection for CI, so inserted/renamed columns can't shift values.
    """
    lines = content.split("\n")

    # ---- Path A: current cell-per-line layout (each field on its own line) ----
    models_a = _parse_arena_cell_layout(lines, slug)
    if models_a:
        return {
            "meta": {
                "leaderboard": slug,
                "source_url": f"https://arena.ai/leaderboard/{slug}",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "model_count": len(models_a),
                "layout": "cell",
            },
            "models": models_a,
        }, f"ok ({len(models_a)} models)"

    # ---- Path B: legacy markdown `|` table layout ----
    models = []
    header_cells = None
    pending_header = None
    in_table = False
    for line in lines:
        if line.startswith("|"):
            if _is_sep_row(line):
                # Header = the | row immediately before this separator.
                header_cells = pending_header
                in_table = True
                pending_header = None
                continue
            pending_header = line
            if not in_table or header_cells is None:
                continue
        else:
            # Non-table line resets the pending header so later tables still parse.
            pending_header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        rank_m = re.match(r"\s*(\d+)", cells[0])
        if not rank_m:
            continue
        rank = int(rank_m.group(1))

        # Model cell = first cell that is a markdown link [name](http...)
        model_idx = None
        for i, c in enumerate(cells[1:], start=1):
            if re.search(r"\[[^\]]+\]\(https?://", c):
                model_idx = i
                break
        if model_idx is None:
            continue
        m = re.match(r"\[([^\]]+)\]", cells[model_idx])
        model_name = m.group(1) if m else cells[model_idx]

        vendor_match = re.search(r"\]\([^)]*\)\s*([^·]+?)\s*·", cells[model_idx])
        vendor = vendor_match.group(1).strip() if vendor_match else None

        lic_match = re.search(
            r"·\s*(proprietary|open|Open Source|MIT|Apache|GPL|CC-|Community|Non-commercial)",
            cells[model_idx], re.I,
        )
        license = "proprietary" if (
            lic_match and "proprietary" in lic_match.group(1).lower()
        ) else ("open" if lic_match else None)

        # Score / CI / votes by role (not fixed offset)
        tail = cells[model_idx + 1:]
        score = None
        ci = None
        votes = None
        for c in tail:
            if score is None:
                val = _parse_number(c)
                if val is not None:
                    score = val
                    ci_m = re.search(r"±\s*[\d.]+", c)
                    ci = _parse_number(ci_m.group(0)) if ci_m else None
                    continue
            if ci is None and "±" in c:
                ci = _parse_number(c)
                continue
            if votes is None and re.search(r"votes", c, re.I):
                votes = _parse_int(c)
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
            "layout": "table",
        },
        "models": models,
    }, f"ok ({len(models)} models)"


def _parse_arena_cell_layout(lines, slug):
    """Parse the current Arena layout where each field is on its own line.

    A record looks like:
        <rank>
        <previous rank>        (or blank)
        <badge / extra int>    (optional)
        <model slug>           (may contain spaces/parens, e.g. 'muse-spark-1.2 (xHigh)')
        <Vendor> · <License>
        <score>
        ±<ci>
        <votes>\\t<price>\\t<context>

    We anchor on the vendor line (contains '·') and read the surrounding fields
    by position, so renamed/reordered columns cannot hide the data.
    """
    models = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i].strip()
        # Vendor line marks a record; model slug is the line immediately above it.
        if "·" in line and i > 0:
            vendor_line = line
            model = lines[i - 1].strip()
            # Score = first numeric line after the vendor line
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            score = _parse_number(lines[j]) if j < n else None
            ci = None
            if j + 1 < n and lines[j + 1].strip().startswith("±"):
                ci = _parse_number(re.sub(r"^±\s*", "", lines[j + 1]))
            # Combined votes/price/context line
            k = j + 2
            while k < n and lines[k].strip() == "":
                k += 1
            combined = lines[k].strip() if k < n else ""
            votes = None
            if combined:
                # votes is the first integer token in the combined line
                vm = re.search(r"(\d[\d,]*)", combined)
                if vm:
                    votes = _parse_int(vm.group(1))
            # Rank = the FARTHEST-back pure-integer line in the window above the
            # vendor line (record order is: rank, prev-rank, badge, model, vendor).
            # Scan from farthest (back=6) toward the vendor so we take the first
            # one in document order, which is the true rank.
            rank = None
            for back in range(6, 1, -1):
                cand = lines[i - back].strip() if i - back >= 0 else ""
                if re.fullmatch(r"\d+", cand):
                    rank = int(cand)
                    break
            vendor_match = re.search(r"([^·]+?)\s*·", vendor_line)
            vendor = vendor_match.group(1).strip() if vendor_match else None
            lic_match = re.search(
                r"·\s*(proprietary|open|Open Source|MIT|Apache|GPL|CC-|Community|Non-commercial)",
                vendor_line, re.I,
            )
            license = "proprietary" if (
                lic_match and "proprietary" in lic_match.group(1).lower()
            ) else ("open" if lic_match else None)
            if model and score is not None:
                models.append(
                    {
                        "rank": rank if rank is not None else len(models) + 1,
                        "model": model,
                        "vendor": vendor,
                        "license": license,
                        "score": score,
                        "ci": ci,
                        "votes": votes,
                    }
                )
            i = k + 1
            continue
        i += 1
    return models


def _parse_arena_agent(content, slug):
    """Parse the agent leaderboard (dimension scores per model).

    Layout-change-proof:
      * Table detected by its separator row, not the header text.
      * The model cell is the first markdown-link cell in the header; dimension
        names are the cells between the model cell and the end (minus known
        trailing columns like Sessions/Price), so renaming Rank/Model/Sessions
        or inserting columns does not break dimension mapping.
    """
    lines = content.split("\n")
    models = []
    dimensions = []
    model_col = 1
    header_cells = None
    pending_header = None
    in_table = False
    for line in lines:
        if line.startswith("|"):
            if _is_sep_row(line):
                # Header = the | row immediately before this separator.
                header_cells = pending_header
                in_table = True
                pending_header = None
                if header_cells is not None:
                    hc = [c.strip() for c in header_cells.strip("|").split("|")]
                    for i, c in enumerate(hc):
                        if re.search(r"\[[^\]]+\]\(https?://", c):
                            model_col = i
                            break
                    trailing = {"Sessions", "Price $/M", "Price $/M tokens", "Price"}
                    dims = []
                    for c in hc[model_col + 1:]:
                        name = re.sub(r"\s*\([^)]*\)", "", c).strip()
                        if not name or name in trailing:
                            continue
                        dims.append(name)
                    dimensions = dims
                continue
            pending_header = line
            if not in_table or header_cells is None:
                continue
        else:
            pending_header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        rank_m = re.match(r"\s*(\d+)", cells[0])
        if not rank_m:
            continue
        rank = int(rank_m.group(1))

        model_cell = cells[model_col] if model_col < len(cells) else (cells[1] if len(cells) > 1 else "")
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

        # Dimension scores are the cells immediately after the model cell.
        scores = []
        for i, dim in enumerate(dimensions):
            cell_idx = model_col + 1 + i
            if cell_idx < len(cells):
                score_val, ci_val = _parse_number_with_ci(cells[cell_idx])
                scores.append({"name": dim, "score": score_val, "ci": ci_val})

        # Sessions = last numeric-ish cell before any trailing price column.
        sessions = _parse_int(cells[-1]) if cells else None

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
            "layout": "table",
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

    try:
        if slug == "agent":
            return _parse_arena_agent(content, slug)
        return _parse_arena_general(content, slug)
    except Exception as e:
        # A layout change on this board must never crash the whole run.
        return None, f"parse error (board layout changed?): {e}"


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
    """Return the set of arena.ai leaderboard slugs to fetch.

    Strategy (defense in depth, NOT purely hardcoded):
      1. Scrape the live overview page via Jina Reader first. This auto-discovers
         any NEW board arena.ai adds, so we pick up changes without code edits.
      2. Union with a curated fallback list (ARENA_SLUGS) so that if the overview
         page's format changes / the scrape returns nothing, we never silently
         regress to zero boards.
    """
    scraped = set()
    try:
        text = fetch_text(f"{JINA_BASE}{ARENA_BASE}")
        scraped.update(re.findall(r"arena\.ai/leaderboard/([a-z][a-z0-9-]*)", text))
    except Exception as e:
        log(f"Arena slug scrape failed ({e}); using curated fallback")
    if scraped:
        log(f"Arena slug scrape found {len(scraped)} boards (live)")
    else:
        log("Arena slug scrape found 0 — using curated fallback list")
    new_boards = sorted(scraped - set(ARENA_SLUGS))
    if new_boards:
        log(f"Arena: {len(new_boards)} new board(s) not in curated list: {new_boards}")
    slugs = set(ARENA_SLUGS) | scraped
    return sorted(slugs), sorted(scraped)


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


def merge(catalog, aa, arena, benchlm):
    """Attach catalog enrichment to benchmark spines (no filtering).
    Each benchmark stays in its own namespace under benchmarks/<source>/.

    `catalog` = OR ∪ models.dev universe. We use it only to DECORATE
    benchmark rows with pricing/context/flags where a match is found — never
    to decide whether a benchmark row exists.
    """
    cat_by_id = {}
    cat_by_norm = {}
    cat_by_slug_only = {}
    for m in catalog:
        mid = m["id"].lower()
        cat_by_id[mid] = m
        cat_by_norm.setdefault(norm(m["name"]), []).append(m)
        slug_only = mid.split("/", 1)[-1] if "/" in mid else mid
        cat_by_slug_only.setdefault(slug_only, []).append(m)

    counts = {"aa": 0, "arena": 0, "benchlm": 0}

    # Attach AA
    if aa:
        for key, a in aa.items():
            creator = a.get("creator_slug", "")
            slug = a.get("slug", "")
            target = None
            k = f"{creator}/{slug}".lower()
            if k in cat_by_id:
                target = cat_by_id[k]
            else:
                base = base_slug(k.replace(".", "-"))
                if base in cat_by_id:
                    target = cat_by_id[base]
                else:
                    so = base.split("/", 1)[-1]
                    if so in cat_by_slug_only:
                        target = cat_by_slug_only[so][0]
                    else:
                        nn = norm(a.get("name", ""))
                        if nn in cat_by_norm:
                            target = cat_by_norm[nn][0]
            if target:
                target["benchmarks"]["aa"] = a
                counts["aa"] += 1

    # Attach arena
    if arena:
        for lb_slug, lb_data in arena.items():
            for model_info in lb_data.get("models", []):
                nn = norm(model_info.get("model", ""))
                if nn in cat_by_norm:
                    for m in cat_by_norm[nn]:
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
            if slug and slug in cat_by_id:
                target = cat_by_id[slug]
            else:
                if slug in cat_by_slug_only:
                    target = cat_by_slug_only[slug][0]
                elif slug:
                    base = base_slug(slug)
                    if base in cat_by_slug_only:
                        target = cat_by_slug_only[base][0]
                if target is None:
                    nn = norm(model_name)
                    if nn in cat_by_norm:
                        target = cat_by_norm[nn][0]
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
    "openrouter-usage": {
        "title": "OpenRouter Usage",
        "source_url": OR_RANKINGS_URL,
        "desc": "Real-world adoption: tokens processed and request counts via "
                "OpenRouter (rolling window). NOT a quality score — usage is "
                "never blended into benchmark rankings.",
        "benches": {
            "or_usage_tokens": ("Usage Rank", "Rank by total tokens processed; requests kept alongside."),
        },
    },
    "deepswe": {
        "title": "DeepSWE (Datacurve)",
        "source_url": DEEPSWE_URL,
        "desc": "Agentic software-engineering eval: pass@1 on 113 real GitHub "
                "issues executed through agent harnesses. Cost and token stats "
                "kept as raw columns, never blended.",
        "benches": {
            "deepswe_v1_1": ("DeepSWE v1.1", "pass@1 per harness+model+effort config."),
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


def write_aa_benchmarks(aa):
    """Write every Artificial Analysis benchmark into artificial-analysis/.

    AA is its OWN spine: we iterate the full AA response (every model AA
    returns), NOT just OpenRouter-matched models. This recovers models like
    meituan/longcat-2.0 that exist on AA but not in the OR catalog.

    We emit one file per evaluation key that actually appears across the AA
    catalog (17 fields), sorted by score (higher = better). `fetched_at` is
    stamped on each file's meta.
    """
    subdir = "artificial-analysis"
    if not aa:
        return {}
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Discover which evaluation keys exist across the full AA catalog
    seen = {}
    for key, a in aa.items():
        evals = (a.get("evaluations") or {})
        for k in evals:
            seen.setdefault(k, 0)
            seen[k] += 1

    written = {}
    for eval_key, n in sorted(seen.items()):
        models_list = []
        for key, a in aa.items():
            val = num((a.get("evaluations") or {}).get(eval_key))
            if val is not None:
                models_list.append(
                    {
                        "model": key,
                        "name": a.get("name"),
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


def write_usage_benchmarks(usage):
    """Write OpenRouter real-world usage into openrouter-usage/.

    Usage is NOT a quality score: models are ranked by tokens processed
    (adoption), with request counts kept alongside. Never blended into
    benchmark rankings.
    """
    subdir = "openrouter-usage"
    if not usage:
        return {}
    rows = []
    for slug, a in usage.items():
        if not (a.get("tokens") or a.get("requests")):
            continue
        rows.append(
            {
                "model": slug,
                "tokens": a["tokens"],
                "requests": a["requests"],
            }
        )
    rows.sort(key=lambda r: r["tokens"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    _write_benchmark_json(
        subdir,
        "or_usage_tokens",
        {
            "leaderboard": "or_usage_tokens",
            "source_url": OR_RANKINGS_URL,
            "benchmark": "OpenRouter Usage (tokens, rolling window)",
        },
        rows,
    )
    return {"or_usage_tokens": True}


def write_deepswe_benchmarks(deepswe_rows):
    """Write DeepSWE agentic-SWE results into deepswe/. Each row is one
    harness+model+effort config; ranked by pass_rate. Cost/tokens kept as
    separate raw columns, never blended."""
    subdir = "deepswe"
    if not deepswe_rows:
        return {}
    rows = [r for r in deepswe_rows if r.get("pass_rate") is not None]
    rows.sort(key=lambda r: r["pass_rate"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    _write_benchmark_json(
        subdir,
        "deepswe_v1_1",
        {
            "leaderboard": "deepswe_v1_1",
            "source_url": DEEPSWE_URL,
            "benchmark": "DeepSWE v1.1 (113-task agentic SWE, pass@1)",
        },
        rows,
    )
    return {"deepswe_v1_1": True}



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
# Output: weekly movers (rank deltas vs newest previous archive snapshot)
# ---------------------------------------------------------------------------
def _load_rank_map(path):
    """{model: rank} from a benchmark json file."""
    try:
        with open(path) as f:
            models = json.load(f).get("models", [])
    except Exception:
        return {}
    return {m.get("model", ""): m.get("rank") or m.get("score") for m in models
            if m.get("model")}


def write_movers():
    """Compare current benchmark ranks with the most recent archive snapshot
    and write benchmarks/movers/movers.json + .md. Deterministic rank diffs,
    no score blending. Soft-fails (with a note) if no previous snapshot exists.
    """
    subdir = "movers"
    snaps = []
    if os.path.isdir("archive"):
        for month in sorted(os.listdir("archive")):
            mdir = os.path.join("archive", month)
            if not os.path.isdir(mdir):
                continue
            for day in sorted(os.listdir(mdir)):
                snaps.append((month + day, os.path.join(mdir, day)))
    snaps = [s for s in snaps if s[0] != datetime.now(timezone.utc).strftime("%Y%m%d")]
    if not snaps:
        log("Movers: no previous archive snapshot yet — skipped (not an error)")
        return
    prev_root = sorted(snaps)[-1][1]

    # Track a small deterministic set of high-signal boards
    boards = [
        ("arena/arena_text.json", "Arena Text"),
        ("arena/arena_code.json", "Arena Code"),
        ("artificial-analysis/aa_artificial_analysis_intelligence_index.json", "AA Intelligence"),
    ]
    out = []
    for rel, label in boards:
        cur = _load_rank_map(os.path.join("benchmarks", rel))
        old = _load_rank_map(os.path.join(prev_root, rel))
        if not cur or not old:
            continue
        # rank files may store score in 'rank' slot; treat smaller=better for
        # ranks and larger=better for scores uniformly by using signed delta
        for model, cur_v in cur.items():
            if model in old and cur_v is not None and old[model] is not None:
                delta = old[model] - cur_v  # positive = moved up
                if abs(delta) >= 1:
                    out.append({
                        "board": label,
                        "model": model,
                        "previous": old[model],
                        "current": cur_v,
                        "delta": round(delta, 4),
                    })
    if not out:
        log(f"Movers: no rank changes vs {os.path.basename(prev_root)}")
        return
    out.sort(key=lambda r: -abs(r["delta"]))
    os.makedirs(os.path.join("benchmarks", subdir), exist_ok=True)
    payload = {
        "meta": {
            "leaderboard": "movers",
            "compared_against": os.path.basename(prev_root),
            "note": "Signed rank/value deltas per board. Positive = moved up.",
        },
        "models": out[:200],
    }
    with open(os.path.join("benchmarks", subdir, "movers.json"), "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    WRITTEN.setdefault(subdir, []).append("movers")
    log(f"Movers: {len(out)} changes vs {os.path.basename(prev_root)}")


# ---------------------------------------------------------------------------
# Output: price-performance frontier (from catalog + AA intelligence)
# ---------------------------------------------------------------------------
def write_price_performance():
    """Cheapest models per AA-Intelligence band, from catalog pricing.
    Deterministic: no derived scores — raw price + raw score side by side.
    """
    try:
        with open(os.path.join(OUTDIR, "models.json")) as f:
            catalog = json.load(f)["models"]
    except Exception as e:
        log(f"Price-performance: models.json unreadable ({e}) — skipped")
        return
    rows = []
    for m in catalog:
        aa = (m.get("benchmarks") or {}).get("aa") or {}
        intel = (aa.get("evaluations") or {}).get(
            "artificial_analysis_intelligence_index"
        )
        price = (m.get("price_per_million") or {}).get("prompt")
        if price is None:
            # fall back to AA's own blended price (attached with the spine)
            price = ((aa.get("pricing") or {}).get("blended"))
        if intel is None or price is None or price <= 0:
            continue
        rows.append({
            "model": m["id"],
            "aa_intelligence": intel,
            "prompt_price_per_m": price,
            "value": round(intel / price, 2),  # intelligence points per $/M — explicit ratio, not a blended score
        })
    rows.sort(key=lambda r: -r["value"])
    if not rows:
        log("Price-performance: no models with both AA intelligence and price — skipped")
        return
    subdir = "price-performance"
    os.makedirs(os.path.join("benchmarks", subdir), exist_ok=True)
    payload = {
        "meta": {
            "leaderboard": "price_performance",
            "note": "value = AA Intelligence / prompt $ per M tokens. "
                    "Explicit ratio of two raw numbers — not a blended score.",
        },
        "models": rows[:200],
    }
    with open(os.path.join("benchmarks", subdir, "price_performance.json"), "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    WRITTEN.setdefault(subdir, []).append("price_performance")
    log(f"Price-performance: {len(rows)} priced models with AA intelligence")


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

    # 1. OpenRouter catalog (pricing, context, modalities, flags)
    or_models = fetch_openrouter()
    log(f"OpenRouter: {len(or_models)} models")

    # 1b. models.dev catalog (broadens universe: 6667 models, no scores)
    md_models, md_note = fetch_modelsdev()
    log(f"models.dev: {md_note}")
    or_by_base = {base_slug(m["id"]): m for m in or_models}
    for m in md_models:
        base = base_slug(m["id"])
        if base not in or_by_base:
            or_models.append(m)
            or_by_base[base] = m
    log(f"Catalog (OR + models.dev deduped): {len(or_models)} unique base models")

    # 2. Artificial Analysis (its own spine — ~600 models, all written)
    aa, aa_note = fetch_artificial_analysis(args.aa_key)
    log(f"Artificial Analysis: {aa_note}")

    # 3. arena.ai — scrape-discovered live, curated fallback if scrape fails
    arena_data = {}
    slugs, scraped_slugs = discover_arena_slugs()
    log(f"Arena.ai: {len(slugs)} leaderboards ({len(scraped_slugs)} live-discovered + curated fallback)")
    live_boards = 0
    for slug in slugs:
        lb, note = fetch_arena_leaderboard(slug)
        if lb:
            arena_data[slug] = lb
            if slug in scraped_slugs:
                live_boards += 1
            log(f"  {slug}: {note} ({lb['meta']['model_count']} models)")
        else:
            log(f"  {slug}: {note}")

    # 4. BenchLM
    benchlm, benchlm_note = fetch_benchlm()
    log(f"BenchLM: {benchlm_note}")

    # 5. OpenRouter usage (real-world adoption, separate spine)
    usage, usage_note = fetch_or_usage()
    log(f"OpenRouter usage: {usage_note}")

    # 6. DeepSWE (agentic SWE, separate spine)
    deepswe_rows, deepswe_note = fetch_deepswe()
    log(f"DeepSWE: {deepswe_note}")

    # Merge: attach catalog enrichment to benchmark spines (no filtering)
    counts = merge(or_models, aa, arena_data, benchlm or [])
    log(f"Merged: {counts}")

    # Ensure output dirs — benchmarks/ is rebuilt fresh each run
    if os.path.isdir("benchmarks"):
        import shutil
        shutil.rmtree("benchmarks")
    os.makedirs("benchmarks", exist_ok=True)
    WRITTEN.clear()

    # Write per-benchmark files (each benchmark is its own spine)
    log("=== Writing per-benchmark files ===")
    write_aa_benchmarks(aa)
    write_arena_benchmarks(arena_data)
    write_benchlm_benchmarks(benchlm or [])
    write_usage_benchmarks(usage)
    write_deepswe_benchmarks(deepswe_rows)
    # Write catalog
    arena_note = (
        f"ok ({len(arena_data)} leaderboards; "
        f"{live_boards} live-discovered via scrape, {len(arena_data) - live_boards} from curated fallback)"
    )
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "openrouter": "ok",
            "models.dev": md_note,
            "openrouter_usage": usage_note,
            "deepswe": deepswe_note,
            "artificial_analysis": aa_note,
            "arena_ai": arena_note,
            "benchlm": benchlm_note,
        },
    }
    write_models_json(or_models, meta, counts)
    log(f"wrote models.json ({len(or_models)} models)")

    # Movers + price-performance (need models.json / archives on disk first)
    write_movers()
    write_price_performance()

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
