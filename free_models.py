#!/usr/bin/env python3
"""Build FREE_MODELS.md — a root-level directory of every free model across
providers, with benchmark coverage (AA + Arena) where available.

Sources:
  - Nous Portal  /api/nous/recommended-models  (authoritative for Nous-free)
  - OpenRouter   models.json  `free` flag       (authoritative for OR-free)
  - models.dev   api.json      `:free` models    (routers: kilo/unorouter/kenari/...)

Free models are NORMAL models made free by a provider — they are joined to
AA/Arena by their base id (`:free` stripped, provider prefix kept for AA which
uses `provider/slug`; for Arena we match by slug-only fuzzy since Arena uses
display names). Models with no benchmark coverage sort to the bottom.

Nous fetch is SOFT: if the portal is unreachable from CI, we fall back to the
last-known-good committed cache (free_data/nous_free_cache.json) AND emit a
warning (non-zero exit is NOT forced — the daily run must still complete).
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS_JSON = os.path.join(ROOT, "models.json")
NOUS_ENDPOINT = "https://portal.nousresearch.com/api/nous/recommended-models"
NOUS_CACHE = os.path.join(ROOT, "free_data", "nous_free_cache.json")
OUT = os.path.join(ROOT, "FREE_MODELS.md")

AA_BENCHES = {
    "aa_artificial_analysis_intelligence_index": "AA Intelligence",
    "aa_artificial_analysis_coding_index": "AA Coding",
    "aa_artificial_analysis_math_index": "AA Math",
    "aa_gpqa": "GPQA",
    "aa_aime": "AIME",
    "aa_math_500": "Math500",
    "aa_livecodebench": "LiveCodeBench",
    "aa_scicode": "SciCode",
    "aa_terminalbench_v2_1": "TerminalBench v2.1",
    "aa_hle": "HLE",
    "aa_lcr": "LCR",
    "aa_tau2": "TAU2",
    "aa_tau_banking": "TAU Banking",
    "aa_ifbench": "IFBench",
    "aa_terminalbench_hard": "TerminalBench Hard",
}
AA_PRIMARY = "aa_artificial_analysis_intelligence_index"
AA_SECONDARY = "aa_artificial_analysis_coding_index"

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"WARNING: {msg}", file=sys.stderr, flush=True)


def base_slug(mid):
    """Strip :free and routing/version suffixes -> provider/slug for join.

    Keeps identity tags like -preview, -exp, -0813 (those distinguish real
    model variants, not just routing aliases).
    """
    mid = mid.lower()
    mid = re.sub(r":(free|batch|thinking|nitro|floor|cached)$", "", mid)
    # strip date tags like -0813, -3107
    mid = re.sub(r"-(?:19|20)\d{2}$", "", mid)
    # strip effort tags only (xhigh/high/.../latest) — these are routing aliases
    mid = re.sub(r"-(?:xhigh|high|medium|low|xlow|max|latest)$", "", mid)
    return mid


def slug_only(mid):
    """Provider-stripped slug, with dots normalized to hyphens so that
    'longcat-2.0' (Nous free) matches 'longcat-2-0' (AA) etc."""
    s = mid.split("/", 1)[-1] if "/" in mid else mid
    return s.replace(".", "-")


def norm_slug(mid):
    """Full join key: base_slug + slug_only normalization (dots->hyphens)."""
    return slug_only(base_slug(mid))


def fetch_nous_free():
    """Return (list_of_model_ids, source_note). Soft fallback to cache."""
    try:
        req = urllib.request.Request(
            NOUS_ENDPOINT, headers={"User-Agent": "modelcompass/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        free = data.get("freeRecommendedModels") or []
        ids = [m.get("modelName") or m.get("model") for m in free if (m.get("modelName") or m.get("model"))]
        # refresh cache
        os.makedirs(os.path.dirname(NOUS_CACHE), exist_ok=True)
        with open(NOUS_CACHE, "w") as f:
            json.dump({"fetched_at": datetime.now(timezone.utc).isoformat(), "free": ids}, f, indent=2)
        return ids, f"live ({len(ids)} models, fetched_at={datetime.now(timezone.utc).isoformat()[:10]})"
    except Exception as e:
        if os.path.exists(NOUS_CACHE):
            with open(NOUS_CACHE) as f:
                ids = json.load(f).get("free", [])
            warn(f"Nous Portal unreachable ({e}); using committed cache ({len(ids)} models).")
            return ids, f"cache fallback ({len(ids)} models) — portal unreachable: {e}"
        warn(f"Nous Portal unreachable ({e}) AND no cache present; Nous-free models omitted.")
        return [], "FAILED — no portal, no cache"


def collect_openrouter_free(or_models):
    out = {}
    for m in or_models:
        if not m.get("free"):
            continue
        mod = m.get("modality", "")
        # Exclude audio-output models (e.g. lyria text+image->text+audio) —
        # they are not chat-competitive and clutter the free directory.
        if "->" in mod and "audio" in mod.split("->")[-1]:
            continue
        if mod and "audio" in mod and "text" not in mod and "image" not in mod:
            continue
        base = base_slug(m["id"])
        out.setdefault(base, {"id": m["id"], "name": m.get("name"), "free_on": set()})
        out[base]["free_on"].add("openrouter")
    return out


def collect_modelsdev_free():
    """All :free models from models.dev (routers)."""
    out = {}
    try:
        req = urllib.request.Request(
            "https://models.dev/api.json", headers={"User-Agent": "modelcompass/1.0"}
        )
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        warn(f"models.dev unreachable ({e}); router-free models omitted.")
        return out
    for prov, pdata in data.items():
        for mid, mval in (pdata.get("models") or {}).items():
            if not mid.endswith(":free"):
                continue
            base = base_slug(mid)
            entry = out.setdefault(base, {"id": mid, "name": mval.get("name", mid), "free_on": set()})
            entry["free_on"].add(prov)
    return out


def load_aa():
    """Return (scores, slug_scores) from the committed AA files.
    scores: {base_slug (provider-kept): {bench_key: score}}
    slug_scores: {slug_only (provider-stripped): {bench_key: score}} for
                 cross-provider joins (e.g. meituan/longcat-2.0 <-> longcat/longcat-2-0).
    """
    scores = {}
    slug_scores = {}
    aa_dir = os.path.join(ROOT, "benchmarks", "artificial-analysis")
    if not os.path.isdir(aa_dir):
        return scores, slug_scores
    for bf in AA_BENCHES:
        path = os.path.join(aa_dir, f"{bf}.json")
        if not os.path.exists(path):
            continue
        try:
            raw = json.load(open(path)).get("models", [])
        except Exception:
            continue
        for it in raw:
            mid = it.get("model", "")
            score = it.get("score")
            if mid and score is not None:
                # primary key: full base_slug (provider-kept)
                scores.setdefault(base_slug(mid), {})[bf] = score
                # secondary index: norm_slug (provider-stripped, dots->hyphens) for cross-provider join
                slug_scores.setdefault(norm_slug(mid), {})[bf] = score
    return scores, slug_scores


def load_arena():
    """Return (scores, slug_scores) from local Arena boards.
    scores: {base_slug (provider-kept): [(slug, rank, score)]}
    slug_scores: {slug_only (provider-stripped): [(slug, rank, score)]}
    """
    scores = {}
    slug_scores = {}
    arena_dir = os.path.join(ROOT, "benchmarks", "arena")
    if not os.path.isdir(arena_dir):
        return scores, slug_scores
    for fname in os.listdir(arena_dir):
        if not fname.endswith(".json") or "OVERVIEW" in fname:
            continue
        slug = fname.replace("arena_", "").replace(".json", "")
        try:
            raw = json.load(open(os.path.join(arena_dir, fname))).get("models", [])
        except Exception:
            continue
        for m in raw:
            mid = m.get("model", "")
            if mid:
                scores.setdefault(base_slug(mid), []).append(
                    (slug, m.get("rank"), m.get("score"))
                )
                slug_scores.setdefault(norm_slug(mid), []).append(
                    (slug, m.get("rank"), m.get("score"))
                )
    return scores, slug_scores


def main():
    # 1. Nous free (soft)
    nous_ids, nous_note = fetch_nous_free()
    print(f"Nous free: {nous_note}")

    # 2. Load OpenRouter catalog
    with open(MODELS_JSON) as f:
        or_models = json.load(f)["models"]

    # 3. Collect all free models
    merged = collect_openrouter_free(or_models)
    for base, e in collect_modelsdev_free().items():
        if base not in merged:
            merged[base] = e
        else:
            merged[base]["free_on"] |= e["free_on"]

    # 4. Add Nous (authoritative — overrides base if OR lists it paid)
    for mid in nous_ids:
        base = base_slug(mid)
        if base not in merged:
            merged[base] = {"id": mid, "name": mid, "free_on": set()}
        merged[base]["id"] = mid  # keep the :free id from Nous
        merged[base]["free_on"].add("nous")

    # 5. Benchmark joins
    aa, aa_slug = load_aa()
    arena, arena_slug = load_arena()

    rows = []
    for base, e in merged.items():
        mid = e["id"]
        ns = norm_slug(mid)
        # AA: exact base_slug (provider-kept), else norm_slug cross-provider join
        aa_entry = aa.get(base)
        if aa_entry is None:
            aa_entry = aa_slug.get(ns)
        # Arena: best (lowest) rank across boards
        arena_list = arena.get(base)
        if arena_list is None:
            arena_list = arena_slug.get(ns)
        best_arena = None
        if arena_list:
            best = sorted(arena_list, key=lambda x: (x[1] if x[1] is not None else 9999))[0]
            best_arena = best  # (slug, rank, score)

        rows.append({
            "id": e["id"],
            "name": e.get("name"),
            "free_on": sorted(e["free_on"]),
            "aa": aa_entry,
            "arena": best_arena,
        })

    # 6. Sort: Arena rank (primary) -> AA Intelligence (secondary) -> no-bench bottom
    def sort_key(r):
        arena_rank = r["arena"][1] if r["arena"] else 99999
        aa_intel = r["aa"].get(AA_PRIMARY) if r["aa"] else None
        aa_intel = aa_intel if aa_intel is not None else -1
        has_any = 0 if (r["arena"] is None and r["aa"] is None) else 1
        return (1 - has_any, arena_rank, -aa_intel)

    rows.sort(key=sort_key)

    # 7. Thresholds for bolding
    best_intel = max((r["aa"][AA_PRIMARY] for r in rows if r["aa"] and r["aa"].get(AA_PRIMARY) is not None), default=None)
    best_coding = max((r["aa"][AA_SECONDARY] for r in rows if r["aa"] and r["aa"].get(AA_SECONDARY) is not None), default=None)
    best_arena_rank = min((r["arena"][1] for r in rows if r["arena"] and r["arena"][1] is not None), default=None)

    # 8. Render
    L = []
    L.append("# Free Models")
    L.append("")
    L.append("A directory of every free model across providers (Nous, OpenRouter, and router "
             "aggregators), with benchmark coverage where available. Free models are normal models "
             "made free by a provider — not a separate class.")
    L.append("")
    L.append("**Sorting:** Arena rank (primary) → AA Intelligence (secondary). Models with no "
             "benchmark coverage sort to the bottom. **Bold** = best value in that column.")
    L.append("")
    if WARNINGS:
        L.append("> ⚠️ **Data warnings (run " + datetime.now(timezone.utc).isoformat()[:10] + "):**")
        for w in WARNINGS:
            L.append(f"> - {w}")
        L.append("")
    L.append("| Model | Free on | AA Intelligence | AA Coding | Arena Rank |")
    L.append("|-------|---------|-----------------|-----------|------------|")

    for r in rows:
        model = r["id"]
        free_on = "/".join(r["free_on"])

        if r["aa"]:
            intel = r["aa"].get(AA_PRIMARY)
            intel_str = f"**{intel:.1f}**" if (intel is not None and intel == best_intel) else (f"{intel:.1f}" if intel is not None else "—")
            coding = r["aa"].get(AA_SECONDARY)
            coding_str = f"**{coding:.1f}**" if (coding is not None and coding == best_coding) else (f"{coding:.1f}" if coding is not None else "—")
        else:
            intel_str = "—"
            coding_str = "—"

        if r["arena"]:
            slug, rank, score = r["arena"]
            arena_str = f"**{rank}** ({slug})" if rank == best_arena_rank else f"{rank} ({slug})"
        else:
            arena_str = "—"

        L.append(f"| {model} | {free_on} | {intel_str} | {coding_str} | {arena_str} |")

    with open(OUT, "w") as f:
        f.write("\n".join(L) + "\n")

    n_aa = sum(1 for r in rows if r["aa"])
    n_arena = sum(1 for r in rows if r["arena"])
    n_none = sum(1 for r in rows if r["arena"] is None and r["aa"] is None)
    print(f"wrote {OUT}: {len(rows)} models | AA={n_aa} Arena={n_arena} no-benchmark={n_none}")
    if WARNINGS:
        print(f"{len(WARNINGS)} warning(s) emitted (non-fatal).", file=sys.stderr)


if __name__ == "__main__":
    main()
