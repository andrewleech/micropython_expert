#!/usr/bin/env python3
"""Export DPO preference pairs targeting specific model failure modes.

Creates 4 types of preference pairs:
1. Role confusion - substantive review vs merge/praise acks
2. Specificity - comments with code suggestions vs without
3. Conciseness - terse rewrites (via Claude) vs verbose originals
4. Severity - higher severity preferred over lower

Output format (JSONL) uses messages-based prompt for TRL DPOTrainer:
{
    "prompt": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    "chosen": "chosen response text",
    "rejected": "rejected response text"
}
"""

import json
import logging
import random
import sqlite3
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
OUTPUT_PATH = OUTPUT_DIR / "dpo_preferences.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "dpo_preferences_summary.json"
CHECKPOINT_PATH = OUTPUT_DIR / ".conciseness_checkpoint.json"

SYSTEM_PROMPT = (
    "You are an expert MicroPython code reviewer with deep knowledge of the "
    "codebase. Your reviews are concise, technically precise, and focus on "
    "correctness, performance, and maintainability. You write in a direct, "
    "no-nonsense style - technical facts without unnecessary pleasantries."
)


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build_prompt(path, diff_hunk):
    """Build messages-format prompt from a file path and diff hunk."""
    user_content = (
        f"Review the following code change:\n\n"
        f"File: {path or 'unknown'}\n"
        f"```diff\n{diff_hunk}\n```"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def make_pair(prompt, chosen, rejected, pair_type):
    return {
        "prompt": prompt,
        "chosen": chosen,
        "rejected": rejected,
        "type": pair_type,
    }


# ---------------------------------------------------------------------------
# Pair Type 1: Role confusion
# ---------------------------------------------------------------------------


def generate_role_confusion_pairs(conn, cap=2000):
    """Substantive review_comment (chosen) vs merge/praise issue_comment (rejected).

    Teaches the model that reviews mean substantive code feedback, not merge
    acknowledgements or praise.
    """
    log.info("Generating role confusion pairs...")

    chosen_rows = conn.execute("""
        SELECT rc.id, rc.body, rc.path, rc.diff_hunk
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        WHERE cc.feedback_type IN ('suggestion', 'requirement', 'question')
          AND rc.in_reply_to_id IS NULL
          AND rc.diff_hunk IS NOT NULL
          AND rc.body IS NOT NULL
          AND length(rc.body) > 10
    """).fetchall()

    rejected_rows = conn.execute("""
        SELECT ic.id, ic.body
        FROM issue_comments ic
        JOIN comment_categories cc
            ON cc.comment_id = ic.id AND cc.comment_type = 'issue_comment'
        WHERE cc.feedback_type IN ('merge', 'praise', 'information')
          AND ic.body IS NOT NULL
          AND length(ic.body) > 5
    """).fetchall()

    random.shuffle(chosen_rows)
    random.shuffle(rejected_rows)

    pairs = []
    rej_idx = 0
    for chosen in chosen_rows:
        if len(pairs) >= cap or rej_idx >= len(rejected_rows):
            break

        chosen_len = len(chosen["body"])
        while rej_idx < len(rejected_rows):
            rej = rejected_rows[rej_idx]
            rej_idx += 1
            ratio = len(rej["body"]) / max(chosen_len, 1)
            if 0.3 <= ratio <= 3.0:
                prompt = build_prompt(chosen["path"], chosen["diff_hunk"])
                pairs.append(make_pair(
                    prompt, chosen["body"], rej["body"], "role_confusion",
                ))
                break

    log.info(f"  Role confusion: {len(pairs)} pairs")
    return pairs


# ---------------------------------------------------------------------------
# Pair Type 2: Specificity
# ---------------------------------------------------------------------------


def generate_specificity_pairs(conn, cap=1500):
    """Comments with code suggestions (chosen) vs without (rejected).

    Paired by matching (domain, component) for topical similarity.
    Within each group, pair up to 10 chosen with 10 rejected.
    Rejected must be shorter than chosen.
    """
    log.info("Generating specificity pairs...")

    chosen_rows = conn.execute("""
        SELECT rc.id, rc.body, rc.path, rc.diff_hunk,
               d.name AS domain, cc.component
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE cc.has_code_suggestion = 1
          AND rc.body IS NOT NULL
          AND length(rc.body) > 10
          AND rc.diff_hunk IS NOT NULL
    """).fetchall()

    rejected_rows = conn.execute("""
        SELECT rc.id, rc.body, rc.path, rc.diff_hunk,
               d.name AS domain, cc.component
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE cc.has_code_suggestion = 0
          AND rc.body IS NOT NULL
          AND length(rc.body) > 10
          AND rc.diff_hunk IS NOT NULL
    """).fetchall()

    chosen_groups = defaultdict(list)
    for r in chosen_rows:
        key = (r["domain"] or "unknown", r["component"] or "unknown")
        chosen_groups[key].append(r)

    rejected_groups = defaultdict(list)
    for r in rejected_rows:
        key = (r["domain"] or "unknown", r["component"] or "unknown")
        rejected_groups[key].append(r)

    pairs = []
    for key in chosen_groups:
        if len(pairs) >= cap:
            break
        c_pool = chosen_groups[key][:10]
        r_pool = rejected_groups.get(key, [])[:10]

        for c in c_pool:
            if len(pairs) >= cap:
                break
            for r in r_pool:
                if len(pairs) >= cap:
                    break
                if len(r["body"]) >= len(c["body"]):
                    continue
                prompt = build_prompt(c["path"], c["diff_hunk"])
                pairs.append(make_pair(
                    prompt, c["body"], r["body"], "specificity",
                ))

    log.info(f"  Specificity: {len(pairs)} pairs")
    return pairs


# ---------------------------------------------------------------------------
# Pair Type 3: Conciseness (synthetic via Claude)
# ---------------------------------------------------------------------------


def _load_checkpoint():
    if CHECKPOINT_PATH.exists():
        with open(CHECKPOINT_PATH) as f:
            data = json.load(f)
        return data.get("completed", {}), data.get("failed", [])
    return {}, []


def _save_checkpoint(completed, failed):
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump({"completed": completed, "failed": failed}, f)


def _rewrite_terse(body, comment_id):
    """Call Claude CLI to produce a terse rewrite of a review comment."""
    prompt_text = (
        "Rewrite this code review comment to be more terse and direct, in the "
        "style of a senior developer who gives minimal but precise feedback. "
        "Keep only the essential technical point. Original: " + body
    )
    cmd = [
        "claude", "-p",
        "--model", "claude-haiku-4-5-20251001",
        "--output-format", "json",
        "--tools", "",
        "--max-budget-usd", "0.05",
    ]
    try:
        result = subprocess.run(
            cmd, input=prompt_text,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            log.warning(
                "  Claude failed for comment %d: exit %d", comment_id, result.returncode,
            )
            return None
        output = json.loads(result.stdout)
        if isinstance(output, dict):
            text = output.get("result", "") or output.get("text", "") or output.get("content", "")
            return text or None
        if isinstance(output, str):
            return output or None
        return None
    except subprocess.TimeoutExpired:
        log.warning("  Claude timed out for comment %d", comment_id)
        return None
    except (json.JSONDecodeError, Exception) as exc:
        log.warning("  Claude parse error for comment %d: %s", comment_id, exc)
        return None


def generate_conciseness_pairs(conn):
    """Terse Claude rewrite (chosen) vs verbose original (rejected).

    For review_comments with body > 500 chars. Uses checkpoint/resume so
    interrupted runs can continue without re-calling Claude.
    """
    log.info("Generating conciseness pairs (synthetic via Claude)...")

    rows = conn.execute("""
        SELECT rc.id, rc.body, rc.path, rc.diff_hunk
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        WHERE length(rc.body) > 500
          AND rc.diff_hunk IS NOT NULL
          AND rc.body IS NOT NULL
    """).fetchall()

    completed, failed = _load_checkpoint()
    failed_set = set(str(f) for f in failed)
    pairs = []
    total = len(rows)

    for i, row in enumerate(rows):
        cid = str(row["id"])

        if cid in completed:
            terse = completed[cid]
            if terse:
                prompt = build_prompt(row["path"], row["diff_hunk"])
                pairs.append(make_pair(prompt, terse, row["body"], "conciseness"))
            continue

        if cid in failed_set:
            continue

        log.info("  Rewriting %d/%d (comment %s)...", i + 1, total, cid)
        terse = _rewrite_terse(row["body"], row["id"])

        if terse and len(terse.strip()) > 5:
            completed[cid] = terse.strip()
            prompt = build_prompt(row["path"], row["diff_hunk"])
            pairs.append(make_pair(prompt, terse.strip(), row["body"], "conciseness"))
        else:
            failed.append(int(cid))
            failed_set.add(cid)

        if (i + 1) % 20 == 0:
            _save_checkpoint(completed, failed)
            log.info("  Checkpoint: %d done, %d failed", len(completed), len(failed))

    _save_checkpoint(completed, failed)
    log.info("  Conciseness: %d pairs (%d failed)", len(pairs), len(failed))
    return pairs


# ---------------------------------------------------------------------------
# Pair Type 4: Severity
# ---------------------------------------------------------------------------


def generate_severity_pairs(conn, cap=2000):
    """Higher severity preferred over lower, grouped by (domain, component).

    blocking > suggestion > nitpick preference ordering.
    Restricted to top-level review_comments with diff context.
    """
    log.info("Generating severity pairs...")

    rows = conn.execute("""
        SELECT rc.id, rc.body, rc.path, rc.diff_hunk,
               cc.severity, d.name AS domain, cc.component
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE rc.diff_hunk IS NOT NULL
          AND rc.in_reply_to_id IS NULL
          AND rc.body IS NOT NULL
          AND length(rc.body) > 10
          AND cc.severity IN ('blocking', 'suggestion', 'nitpick')
    """).fetchall()

    groups = defaultdict(lambda: defaultdict(list))
    for r in rows:
        key = (r["domain"] or "unknown", r["component"] or "unknown")
        groups[key][r["severity"]].append(r)

    severity_combos = [
        ("blocking", "suggestion"),
        ("blocking", "nitpick"),
        ("suggestion", "nitpick"),
    ]

    pairs = []
    for key, sev_dict in groups.items():
        for higher, lower in severity_combos:
            if len(pairs) >= cap:
                break

            h_pool = list(sev_dict.get(higher, []))
            l_pool = list(sev_dict.get(lower, []))
            random.shuffle(h_pool)
            random.shuffle(l_pool)

            count = 0
            for h in h_pool[:10]:
                if count >= 10 or len(pairs) >= cap:
                    break
                for l in l_pool[:10]:
                    if count >= 10 or len(pairs) >= cap:
                        break
                    ratio = len(l["body"]) / max(len(h["body"]), 1)
                    if not (0.3 <= ratio <= 3.0):
                        continue
                    prompt = build_prompt(h["path"], h["diff_hunk"])
                    pairs.append(make_pair(
                        prompt, h["body"], l["body"], "severity",
                    ))
                    count += 1

        if len(pairs) >= cap:
            break

    log.info("  Severity: %d pairs", len(pairs))
    return pairs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Export DPO preference pairs")
    parser.add_argument(
        "--skip-conciseness",
        action="store_true",
        help="Skip conciseness pairs (requires Claude CLI, slow)",
    )
    args = parser.parse_args()

    random.seed(42)

    if not DB_PATH.exists():
        log.error("Database not found: %s", DB_PATH)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()

    all_pairs = []

    role_pairs = generate_role_confusion_pairs(conn, cap=2000)
    all_pairs.extend(role_pairs)

    spec_pairs = generate_specificity_pairs(conn, cap=1500)
    all_pairs.extend(spec_pairs)

    if not args.skip_conciseness:
        conc_pairs = generate_conciseness_pairs(conn)
        all_pairs.extend(conc_pairs)
    else:
        log.info("Skipping conciseness pairs (--skip-conciseness)")

    sev_pairs = generate_severity_pairs(conn, cap=2000)
    all_pairs.extend(sev_pairs)

    conn.close()

    random.shuffle(all_pairs)

    with open(OUTPUT_PATH, "w") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    type_counts = defaultdict(int)
    for p in all_pairs:
        type_counts[p["type"]] += 1

    summary = {
        "total_pairs": len(all_pairs),
        "pair_counts": dict(type_counts),
        "output_file": str(OUTPUT_PATH),
    }
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    log.info("=" * 60)
    log.info("Total pairs: %d", len(all_pairs))
    for ptype, count in sorted(type_counts.items()):
        log.info("  %s: %d", ptype, count)
    log.info("Output: %s", OUTPUT_PATH)
    log.info("Summary: %s", SUMMARY_PATH)


if __name__ == "__main__":
    main()
