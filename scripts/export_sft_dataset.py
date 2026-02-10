#!/usr/bin/env python3
"""Export SFT dataset from dpgeorge review comments.

Filters to substantive review_comments with diff context, applies quality
weighting via oversampling, and splits train/eval by PR number.

Output format (JSONL):
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "metadata": {...}
}
"""

import json
import math
import random
import sqlite3
from collections import Counter
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

EVAL_SPLIT_RATIO = 0.10
RANDOM_SEED = 42

# Quality weights for oversampling
WEIGHT_CODE_SUGGESTION = 1.5
WEIGHT_PATTERN = 1.2
WEIGHT_STYLE_EXAMPLE = 1.3

SYSTEM_PROMPT = """\
You are an expert MicroPython code reviewer with deep knowledge of the codebase. \
Your reviews are concise, technically precise, and focus on correctness, performance, \
and maintainability. You write in a direct, no-nonsense style - technical facts without \
unnecessary pleasantries.

When reviewing code:
- Identify potential bugs, edge cases, and correctness issues
- Point out portability concerns across MicroPython's 22 ports
- Note memory allocation patterns and potential leaks
- Flag deviations from MicroPython coding conventions
- Suggest specific improvements with code examples when helpful

Keep feedback actionable and specific to the code shown."""


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_pr_info(conn: sqlite3.Connection) -> dict[int, dict]:
    """Load PR metadata keyed by pr_number."""
    rows = conn.execute(
        "SELECT number, title, author, state, changed_files, additions, deletions "
        "FROM prs"
    ).fetchall()
    return {
        r["number"]: {
            "title": r["title"],
            "author": r["author"],
            "state": r["state"],
            "changed_files": r["changed_files"],
            "additions": r["additions"],
            "deletions": r["deletions"],
        }
        for r in rows
    }


def load_categories(conn: sqlite3.Connection) -> dict[int, dict]:
    """Load comment categories for review_comments, keyed by comment_id."""
    rows = conn.execute(
        """
        SELECT cc.comment_id, cc.theme, cc.severity, cc.is_style_example,
               cc.component, cc.port, cc.subsystem, cc.language_context,
               cc.code_construct, cc.concern_type, cc.feedback_type,
               cc.is_pattern, cc.cpython_related, cc.has_code_suggestion,
               cc.keywords, d.name AS domain
        FROM comment_categories cc
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE cc.comment_type = 'review_comment'
        """
    ).fetchall()
    return {r["comment_id"]: dict(r) for r in rows}


def load_substantive_comments(
    conn: sqlite3.Connection, categories: dict[int, dict]
) -> list[dict]:
    """Load review_comments that pass all substantive filters.

    Filters:
    - Has a category entry with feedback_type in (suggestion, requirement, question)
    - diff_hunk IS NOT NULL
    - in_reply_to_id IS NULL (top-level comments only)
    - theme != 'FAILED_CATEGORIZATION'
    """
    rows = conn.execute(
        """
        SELECT rc.id, rc.pr_number, rc.body, rc.path, rc.line,
               rc.diff_hunk, rc.in_reply_to_id
        FROM review_comments rc
        WHERE rc.diff_hunk IS NOT NULL
          AND rc.in_reply_to_id IS NULL
        """
    ).fetchall()

    accepted_feedback = {"suggestion", "requirement", "question"}
    comments = []
    filtered_no_category = 0
    filtered_feedback_type = 0
    filtered_failed = 0

    for r in rows:
        cat = categories.get(r["id"])
        if cat is None:
            filtered_no_category += 1
            continue
        if cat["feedback_type"] not in accepted_feedback:
            filtered_feedback_type += 1
            continue
        if cat["theme"] == "FAILED_CATEGORIZATION":
            filtered_failed += 1
            continue

        comments.append({
            "id": r["id"],
            "pr_number": r["pr_number"],
            "body": r["body"],
            "path": r["path"],
            "line": r["line"],
            "diff_hunk": r["diff_hunk"],
            "category": cat,
        })

    print(f"  Top-level comments with diff_hunk: {len(rows)}")
    print(f"  Filtered - no category record:     {filtered_no_category}")
    print(f"  Filtered - wrong feedback_type:     {filtered_feedback_type}")
    print(f"  Filtered - FAILED_CATEGORIZATION:   {filtered_failed}")
    print(f"  Substantive comments retained:      {len(comments)}")

    return comments


def build_review_context(comment: dict, pr_info: dict | None) -> str:
    """Build the user prompt with PR context and diff."""
    parts = []

    if pr_info:
        title = pr_info.get("title", "")
        author = pr_info.get("author", "")
        if title:
            parts.append(f"PR: {title}")
        if author:
            parts.append(f"Author: {author}")

    path = comment.get("path", "")
    if path:
        parts.append(f"File: {path}")

    line = comment.get("line")
    if line:
        parts.append(f"Line: {line}")

    parts.append("")
    parts.append("```diff")
    parts.append(comment["diff_hunk"].rstrip())
    parts.append("```")

    parts.append("")
    parts.append("Please review the code change shown above.")

    return "\n".join(parts)


def build_metadata(comment: dict, pr_info: dict | None) -> dict:
    """Build metadata dict for the JSONL record."""
    cat = comment["category"]
    meta = {
        "comment_id": comment["id"],
        "pr_number": comment["pr_number"],
        "path": comment.get("path"),
        "domain": cat.get("domain"),
        "severity": cat.get("severity"),
        "component": cat.get("component"),
        "feedback_type": cat.get("feedback_type"),
        "concern_type": cat.get("concern_type"),
        "language_context": cat.get("language_context"),
        "has_code_suggestion": bool(cat.get("has_code_suggestion")),
        "is_pattern": bool(cat.get("is_pattern")),
        "is_style_example": bool(cat.get("is_style_example")),
    }
    if pr_info:
        meta["pr_author"] = pr_info.get("author")
        meta["pr_title"] = pr_info.get("title")
    return meta


def compute_quality_weight(category: dict) -> float:
    """Compute multiplicative quality weight from category flags."""
    weight = 1.0
    if category.get("has_code_suggestion"):
        weight *= WEIGHT_CODE_SUGGESTION
    if category.get("is_pattern"):
        weight *= WEIGHT_PATTERN
    if category.get("is_style_example"):
        weight *= WEIGHT_STYLE_EXAMPLE
    return weight


def apply_oversampling(
    examples: list[dict], rng: random.Random
) -> tuple[list[dict], Counter]:
    """Apply quality-based oversampling.

    For each example with total_weight > 1, add floor(weight - 1) full copies
    plus one probabilistic copy for the fractional remainder.
    """
    result = []
    weight_counts = Counter()

    for ex in examples:
        weight = compute_quality_weight(ex["category"])
        copies = 1  # always include the original

        if weight > 1.0:
            extra = weight - 1.0
            copies += math.floor(extra)
            fractional = extra - math.floor(extra)
            if fractional > 0 and rng.random() < fractional:
                copies += 1

        weight_bucket = f"{weight:.2f}"
        weight_counts[weight_bucket] += 1

        for _ in range(copies):
            result.append(ex)

    return result, weight_counts


def format_example(comment: dict, pr_info: dict | None) -> dict:
    """Format a single comment into the messages + metadata JSONL structure."""
    user_content = build_review_context(comment, pr_info)
    assistant_content = comment["body"].strip()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": assistant_content},
    ]

    metadata = build_metadata(comment, pr_info)

    return {"messages": messages, "metadata": metadata}


def split_by_pr(
    comments: list[dict], eval_ratio: float, seed: int
) -> tuple[list[dict], list[dict], set[int]]:
    """Split comments into train/eval by PR number.

    Entire PRs go into eval (10% of PRs, not 10% of comments).
    """
    pr_numbers = sorted(set(c["pr_number"] for c in comments))
    rng = random.Random(seed)
    rng.shuffle(pr_numbers)

    n_eval = max(1, int(len(pr_numbers) * eval_ratio))
    eval_prs = set(pr_numbers[:n_eval])

    train = [c for c in comments if c["pr_number"] not in eval_prs]
    eval_ = [c for c in comments if c["pr_number"] in eval_prs]

    return train, eval_, eval_prs


def write_jsonl(records: list[dict], path: Path) -> None:
    """Write records to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def export_sft_dataset():
    """Export substantive review comments to SFT format."""
    print(f"Database: {DB_PATH}")
    print(f"Output:   {OUTPUT_DIR}")
    print()

    conn = get_connection()

    # Load data
    print("Loading PR info...")
    pr_info = load_pr_info(conn)
    print(f"  Loaded {len(pr_info)} PRs")

    print("Loading categories...")
    categories = load_categories(conn)
    print(f"  Loaded {len(categories)} review_comment categories")

    print("Loading and filtering comments...")
    comments = load_substantive_comments(conn, categories)
    conn.close()

    if not comments:
        print("No substantive comments found. Exiting.")
        return

    # Domain distribution
    print(f"\nDomain distribution (before oversampling, n={len(comments)}):")
    domain_counts = Counter(c["category"]["domain"] for c in comments)
    for domain, count in domain_counts.most_common():
        pct = 100.0 * count / len(comments)
        print(f"  {domain:20s} {count:5d} ({pct:5.1f}%)")

    # Severity distribution
    print("\nSeverity distribution:")
    severity_counts = Counter(c["category"]["severity"] for c in comments)
    for sev, count in severity_counts.most_common():
        pct = 100.0 * count / len(comments)
        print(f"  {sev:20s} {count:5d} ({pct:5.1f}%)")

    # Feedback type distribution
    print("\nFeedback type distribution:")
    ft_counts = Counter(c["category"]["feedback_type"] for c in comments)
    for ft, count in ft_counts.most_common():
        pct = 100.0 * count / len(comments)
        print(f"  {ft:20s} {count:5d} ({pct:5.1f}%)")

    # PR-based train/eval split
    print(f"\nSplitting by PR (eval ratio: {EVAL_SPLIT_RATIO:.0%}, seed: {RANDOM_SEED})...")
    train_comments, eval_comments, eval_prs = split_by_pr(
        comments, EVAL_SPLIT_RATIO, RANDOM_SEED
    )
    n_prs_total = len(set(c["pr_number"] for c in comments))
    print(f"  Total PRs:   {n_prs_total}")
    print(f"  Eval PRs:    {len(eval_prs)}")
    print(f"  Train PRs:   {n_prs_total - len(eval_prs)}")
    print(f"  Train comments (before oversampling): {len(train_comments)}")
    print(f"  Eval comments:                        {len(eval_comments)}")

    # Apply oversampling to train set only
    rng = random.Random(RANDOM_SEED)
    print("\nApplying quality-based oversampling to train set...")
    train_oversampled, weight_dist = apply_oversampling(train_comments, rng)
    print(f"  Before oversampling: {len(train_comments)}")
    print(f"  After oversampling:  {len(train_oversampled)}")
    print(f"  Added copies:        {len(train_oversampled) - len(train_comments)}")
    print("\n  Weight distribution (unique examples):")
    for weight_str in sorted(weight_dist.keys(), key=float):
        count = weight_dist[weight_str]
        print(f"    weight={weight_str}: {count} examples")

    # Shuffle train set
    rng.shuffle(train_oversampled)

    # Format examples
    print("\nFormatting examples...")
    train_records = [
        format_example(c, pr_info.get(c["pr_number"])) for c in train_oversampled
    ]
    eval_records = [
        format_example(c, pr_info.get(c["pr_number"])) for c in eval_comments
    ]

    # Write outputs
    train_path = OUTPUT_DIR / "reviews_sft.jsonl"
    eval_path = EVAL_DIR / "held_out_reviews.jsonl"
    summary_path = OUTPUT_DIR / "reviews_sft_summary.json"

    print(f"\nWriting train set: {train_path}")
    write_jsonl(train_records, train_path)

    print(f"Writing eval set:  {eval_path}")
    write_jsonl(eval_records, eval_path)

    # Build summary
    summary = {
        "source_db": str(DB_PATH),
        "filters": {
            "comment_type": "review_comment",
            "feedback_types": ["suggestion", "requirement", "question"],
            "requires_diff_hunk": True,
            "top_level_only": True,
            "excluded_themes": ["FAILED_CATEGORIZATION"],
        },
        "quality_weights": {
            "has_code_suggestion": WEIGHT_CODE_SUGGESTION,
            "is_pattern": WEIGHT_PATTERN,
            "is_style_example": WEIGHT_STYLE_EXAMPLE,
            "method": "multiplicative oversampling",
        },
        "split": {
            "method": "pr_based",
            "eval_ratio": EVAL_SPLIT_RATIO,
            "seed": RANDOM_SEED,
            "total_prs": n_prs_total,
            "eval_prs": len(eval_prs),
            "train_prs": n_prs_total - len(eval_prs),
        },
        "counts": {
            "substantive_comments": len(comments),
            "train_before_oversampling": len(train_comments),
            "train_after_oversampling": len(train_oversampled),
            "oversampled_copies": len(train_oversampled) - len(train_comments),
            "eval": len(eval_comments),
        },
        "domain_distribution": dict(domain_counts.most_common()),
        "severity_distribution": dict(severity_counts.most_common()),
        "feedback_type_distribution": dict(ft_counts.most_common()),
        "weight_distribution": dict(
            sorted(weight_dist.items(), key=lambda x: float(x[0]))
        ),
    }

    print(f"Writing summary:   {summary_path}")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print("\nDone.")
    print(f"  Train: {len(train_records)} examples ({train_path})")
    print(f"  Eval:  {len(eval_records)} examples ({eval_path})")


if __name__ == "__main__":
    export_sft_dataset()
