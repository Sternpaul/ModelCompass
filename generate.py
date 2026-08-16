#!/usr/bin/env python3
"""
Model Leaderboard generator.

Fetches the live OpenRouter model catalog and produces a machine-readable,
agent-friendly dataset: models.json (full catalog), models.csv (flat),
recommended.json (per-task shortlists with rationale), and INDEX.md.

Honest scope note (see `methodology` in the output): OpenRouter exposes rich
metadata (pricing, context, modalities, supported params, knowledge cutoff,
recency) but NOT benchmark scores. Category "recommended" lists are therefore
transparent METADATA-DERIVED heuristics (capability + recency + price class),
clearly labeled as such. They are meant to give an agent a sane default when its
training cutoff is stale -- not to replace a benchmark verdict. Benchmark
ingestion is a documented future extension point.
"""

import json
import sys
import os
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone


# Variant suffixes that denote derived/equivalent offerings of the same model
# family (batch pricing, free tier, preview, latest alias, versioned snapshot...).
# Used to collapse families in shortlists so e.g. gpt-5.6-luna-pro and
# gpt-5.6-luna-pro:batch don't both appear.
VARIANT_SUFFIX = re.compile(
    r"(:batch|:nitro|:floor|:online|:offline|:cached|:extended|:free"
    r"|:thinking|:rlhf|-preview|-latest|-exp|-alpha|-beta"
    r"|-202\d{6}|-v\d+)$"
)


def family_id(mid):
    """Strip variant suffixes to get the canonical model-family id."""
    if "/" in mid:
        p, r = mid.split("/", 1)
    else:
        p, r = "", mid
    r = VARIANT_SUFFIX.sub("", r)
    return f"{p}/{r}" if p else r


def variant_quality(mid):
    """1 = canonical base model, 0 = a derived variant (batch/free/preview...).
    Higher is better so canonical wins when sorted in descending order."""
    return 1 if family_id(mid) == mid else 0


OR_API = "https://openrouter.ai/api/v1/models"
OUTDIR = "."

# Families that publish open weights (used only as a soft hint; the real signal
# is the presence of a hugging_face_id, which we capture per-model).
OPEN_WEIGHT_PROVIDERS = {
    "qwen", "google", "meta-llama", "meta", "mistralai", "deepseek",
    "nvidia", "z-ai", "moonshotai", "bytedance-seed", "microsoft",
    "openchat", "nousresearch", "inclusionai", "thudm", "alibaba",
    "01-ai", "qwen-community", "huggingface",
}


def log(*a):
    print(*a, file=sys.stderr, flush=True)


def fetch_models():
    req = urllib.request.Request(OR_API, headers={"User-Agent": "model-leaderboard/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))["data"]


def usd_per_million(m, key):
    """Return USD price per 1,000,000 tokens for a pricing key, or None."""
    try:
        v = float(m.get("pricing", {}).get(key))
    except (TypeError, ValueError):
        return None
    if v is None:
        return None
    return v * 1_000_000.0


def parse_created(m):
    c = m.get("created")
    if not c:
        return None
    try:
        return datetime.fromtimestamp(int(c), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def norm_modality(m):
    a = m.get("architecture", {}) or {}
    return a.get("modality", "") or ""


def main():
    log("fetching OpenRouter catalog ...")
    raw = fetch_models()
    log(f"  got {len(raw)} raw entries")

    now = datetime.now(tz=timezone.utc)
    models = []
    for m in raw:
        mid = m.get("id", "")
        arch = m.get("architecture", {}) or {}
        modality = norm_modality(m)
        out_mods = set(arch.get("output_modalities", []) or [])
        in_mods = set(arch.get("input_modalities", []) or [])
        params = m.get("supported_parameters", []) or []
        provider = mid.split("/")[0] if "/" in mid else ""
        created = parse_created(m)
        age_days = (now - created).days if created else None
        ctx = max(
            m.get("context_length") or 0,
            (m.get("top_provider", {}) or {}).get("context_length") or 0,
        )
        p_in = usd_per_million(m, "prompt")
        p_out = usd_per_million(m, "completion")
        p_cache = usd_per_million(m, "input_cache_read")

        is_vision = "image" in in_mods
        is_audio_in = "audio" in in_mods
        is_video_in = "video" in in_mods
        is_image_out = "image" in out_mods
        is_audio_out = "audio" in out_mods
        synthetic = provider == "openrouter"  # routing abstractions, not real models

        rec = {
            "id": mid,
            "family": family_id(mid),
            "name": m.get("name"),
            "provider": provider,
            "created_unix": m.get("created"),
            "created_date": created.strftime("%Y-%m-%d") if created else None,
            "age_days": age_days,
            "context": ctx,
            "modality": modality,
            "is_vision": is_vision,
            "is_audio_input": is_audio_in,
            "is_video_input": is_video_in,
            "is_image_output": is_image_out,
            "is_audio_output": is_audio_out,
            "supports_reasoning": "reasoning" in params,
            "supports_tools": "tools" in params,
            "supports_json": ("structured_outputs" in params) or ("response_format" in params),
            "supports_caching": p_cache is not None and p_cache > 0,
            "knowledge_cutoff": m.get("knowledge_cutoff"),
            "hugging_face_id": m.get("hugging_face_id"),
            "open_weight": bool(m.get("hugging_face_id")),
            "synthetic": synthetic,
            "free": (p_in is not None and p_in <= 0) and not synthetic,
            "price_per_million": {
                "prompt": round(p_in, 6) if p_in is not None else None,
                "completion": round(p_out, 6) if p_out is not None else None,
                "cache_read": round(p_cache, 6) if p_cache is not None else None,
            },
            "description": (m.get("description") or "")[:500],
        }
        models.append(rec)

    real = [m for m in models if not m["synthetic"]]
    log(f"  {len(real)} real models (excluded {len(models)-len(real)} synthetic routers)")

    # ---- categorical leaderboards (factual / sortable) ----
    def nonempty(seq):
        return [m for m in real if m["id"]]

    def by_price(key):
        seq = [m for m in real if m["price_per_million"][key] is not None
               and m["price_per_million"][key] > 0]
        seq.sort(key=lambda m: m["price_per_million"][key])
        return [m["id"] for m in seq]

    def by_context():
        seq = [m for m in real if m["context"]]
        seq.sort(key=lambda m: m["context"], reverse=True)
        return [m["id"] for m in seq]

    def by_newest():
        seq = [m for m in real if m["created_unix"]]
        seq.sort(key=lambda m: m["created_unix"], reverse=True)
        return [m["id"] for m in seq]

    def with_flag(key):
        seq = [m for m in real if m.get(key)]
        return [m["id"] for m in seq]

    def vision_models():
        seq = [m for m in real if m["is_vision"]]
        return [m["id"] for m in seq]

    def audio_models():
        seq = [m for m in real if m["is_audio_input"] or m["is_audio_output"]]
        return [m["id"] for m in seq]

    def image_gen_models():
        seq = [m for m in real if m["is_image_output"]]
        return [m["id"] for m in seq]

    # ---- transparent metadata capability score (NOT a quality score) ----
    def cap_score(m):
        s = 0.0
        if m["supports_reasoning"]:
            s += 2.0
        if m["supports_tools"]:
            s += 1.0
        if m["supports_json"]:
            s += 0.5
        if m["supports_caching"]:
            s += 0.3
        if m["context"]:
            s += min(m["context"] / 1_000_000.0, 2.0)  # up to +2 for >=1M ctx
        if m["age_days"] is not None:
            # recency boost: newest ~120d -> +2, decays to 0 by ~1yr
            s += max(0.0, 2.0 * (1 - m["age_days"] / 365.0))
        if m["knowledge_cutoff"]:
            s += 0.5
        return round(s, 3)

    for m in models:
        m["capability_score"] = cap_score(m)

    # ---- heuristic recommended shortlists ----
    def recommend(filter_fn, sort_key, top=8):
        seq = [m for m in real if filter_fn(m)]

        def keyf(m):
            sk = sort_key(m)
            sk = sk if isinstance(sk, tuple) else (sk,)
            # tiebreak: canonical base model ranks above its variants
            return (variant_quality(m["id"]),) + sk

        seq.sort(key=keyf, reverse=True)
        seen, out = set(), []
        for m in seq:
            fam = family_id(m["id"])
            if fam in seen:
                continue
            seen.add(fam)
            out.append(m["id"])
            if len(out) >= top:
                break
        return out


    recommended = {
        "best_overall": recommend(
            lambda m: m["supports_reasoning"] and m["supports_tools"],
            lambda m: m["capability_score"],
        ),
        "best_reasoning": recommend(
            lambda m: m["supports_reasoning"],
            lambda m: m["capability_score"],
        ),
        "best_coding": recommend(
            lambda m: m["supports_reasoning"] and m["supports_tools"] and m["context"] >= 32000,
            lambda m: (m["capability_score"], m["context"]),
        ),
        "best_vision": recommend(
            lambda m: m["is_vision"] and m["supports_reasoning"],
            lambda m: m["capability_score"],
        ),
        "best_agents": recommend(
            lambda m: m["supports_tools"] and m["supports_reasoning"] and m["context"] >= 128000,
            lambda m: m["capability_score"],
        ),
        "best_open_weight": recommend(
            lambda m: m["open_weight"] and m["supports_reasoning"],
            lambda m: m["capability_score"],
        ),
        "best_cheap": recommend(
            lambda m: (m["price_per_million"]["prompt"] or 1e9) <= 0.5
            and m["supports_reasoning"],
            lambda m: (-(m["price_per_million"]["prompt"] or 0), m["capability_score"]),
        ),
        "best_audio": recommend(
            lambda m: m["is_audio_input"] or m["is_audio_output"],
            lambda m: m["capability_score"],
        ),
        "best_image_generation": recommend(
            lambda m: m["is_image_output"],
            lambda m: m["capability_score"],
        ),
    }

    leaderboards = {
        "cheapest_by_prompt": by_price("prompt"),
        "cheapest_by_completion": by_price("completion"),
        "largest_context": by_context(),
        "newest": by_newest(),
        "vision": vision_models(),
        "audio": audio_models(),
        "image_generation": image_gen_models(),
        "supports_reasoning": with_flag("supports_reasoning"),
        "supports_tools": with_flag("supports_tools"),
        "open_weight": with_flag("open_weight"),
    }

    meta = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "OpenRouter /api/v1/models",
        "source_url": "https://openrouter.ai/docs#models",
        "model_count": len(real),
        "synthetic_excluded": len(models) - len(real),
        "update_cadence": "daily (GitHub Actions)",
        "disclaimer": (
            "Category 'recommended' lists are metadata-derived HEURISTICS "
            "(capability flags + recency + price class), NOT benchmark verdicts. "
            "OpenRouter exposes no benchmark scores. Use them as a sane default "
            "when your training cutoff is stale; verify with live benchmarks "
            "before high-stakes choices."
        ),
        "methodology": (
            "cap_score = 2*reasoning + 1*tools + 0.5*json + 0.3*cache + "
            "min(context/1M,2) + max(0, 2*(1-age/365)) + 0.5*knowledge_cutoff. "
            "Recommended lists sort filtered models by cap_score (or price). "
            "Full per-model metadata is in models.json for agent-side scoring."
        ),
    }

    out = {
        "meta": meta,
        "recommended": recommended,
        "leaderboards": leaderboards,
        "models": models,
    }

    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, "models.json"), "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    # flat CSV for spreadsheets / quick grep
    import csv
    cols = ["id", "name", "provider", "created_date", "age_days", "context",
            "modality", "is_vision", "is_audio_input", "is_video_input",
            "is_image_output", "supports_reasoning", "supports_tools",
            "supports_json", "open_weight", "knowledge_cutoff",
            "price_prompt_per_million", "price_completion_per_million",
            "price_cache_read_per_million", "hugging_face_id"]
    with open(os.path.join(OUTDIR, "models.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for m in models:
            w.writerow([
                m["id"], m["name"], m["provider"], m["created_date"],
                m["age_days"], m["context"], m["modality"], m["is_vision"],
                m["is_audio_input"], m["is_video_input"], m["is_image_output"],
                m["supports_reasoning"], m["supports_tools"], m["supports_json"],
                m["open_weight"], m["knowledge_cutoff"],
                m["price_per_million"]["prompt"],
                m["price_per_million"]["completion"],
                m["price_per_million"]["cache_read"],
                m["hugging_face_id"],
            ])

    with open(os.path.join(OUTDIR, "recommended.json"), "w") as f:
        json.dump({"meta": meta, "recommended": recommended}, f, indent=2, ensure_ascii=False)

    write_index_md(out)
    log("wrote models.json, models.csv, recommended.json, INDEX.md")


def write_index_md(out):
    meta = out["meta"]
    rec = out["recommended"]
    lb = out["leaderboards"]
    lines = []
    lines.append("# Model Leaderboard (machine-readable)\n")
    lines.append(f"_Generated {meta['generated_at']} from {meta['source']} "
                 f"({meta['model_count']} models). Updated daily._\n")
    lines.append("## Recommended shortlists (heuristic — see disclaimer)\n")
    for k, v in rec.items():
        lines.append(f"### {k}\n")
        for mid in v[:5]:
            lines.append(f"- `{mid}`")
        lines.append("")
    lines.append("## Leaderboards (factual / sortable)\n")
    for k, v in lb.items():
        lines.append(f"- **{k}**: {len(v)} models — top: "
                     + ", ".join(f"`{x}`" for x in v[:5]))
    lines.append("")
    lines.append("## Disclaimer\n")
    lines.append(meta["disclaimer"] + "\n")
    lines.append("## Methodology\n")
    lines.append(meta["methodology"] + "\n")
    with open(os.path.join(OUTDIR, "INDEX.md"), "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
