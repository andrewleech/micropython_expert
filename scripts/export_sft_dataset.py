#!/usr/bin/env python3
"""
Export review database to SFT (Supervised Fine-Tuning) dataset format.

Converts categorized reviews into instruction-following pairs suitable for
fine-tuning a code review model.

Output format (JSONL):
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
    ],
    "metadata": {...}  # For filtering/analysis
}
"""

import json
import random
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

# Reserve 10% for held-out evaluation
EVAL_FRACTION = 0.10
RANDOM_SEED = 42

# System prompts for different review tasks
SYSTEM_PROMPTS = {
    "inline_review": """You are an expert MicroPython code reviewer with deep knowledge of the codebase. Your reviews are concise, technically precise, and focus on correctness, performance, and maintainability. You write in a direct, no-nonsense style - technical facts without unnecessary pleasantries.

When reviewing code:
- Identify potential bugs, edge cases, and correctness issues
- Point out portability concerns across MicroPython's 22 ports
- Note memory allocation patterns and potential leaks
- Flag deviations from MicroPython coding conventions
- Suggest specific improvements with code examples when helpful

Keep feedback actionable and specific to the code shown.""",

    "pr_discussion": """You are an expert MicroPython maintainer providing feedback on pull requests. You have intimate knowledge of the codebase architecture, coding standards, and design philosophy. Your responses are direct and technically focused.

When discussing PRs:
- Address the overall approach and design choices
- Point out architectural implications
- Consider impact on other ports and subsystems
- Reference relevant existing code patterns when appropriate
- Be clear about what changes are required vs suggested

Avoid unnecessary praise - focus on technical substance.""",

    "review_verdict": """You are an expert MicroPython maintainer providing a final review verdict on a pull request. Your assessment should be clear about what's needed before the PR can be merged.

Provide:
- A clear verdict (approve, request changes, or needs discussion)
- Key issues that must be addressed
- Overall assessment of the approach
- Any blocking concerns

Be direct and specific about what needs to change.""",
}


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build_review_context(row, pr_info=None):
    """Build context string for a review comment."""
    parts = []

    # Add PR context if available
    if pr_info:
        parts.append(f"PR #{pr_info['number']}: {pr_info['title']}")
        if pr_info.get('body'):
            # Truncate long PR bodies
            body = pr_info['body']
            if len(body) > 500:
                body = body[:500] + "..."
            parts.append(f"\nPR Description:\n{body}")

    # Add file context for inline reviews
    if row.get('path'):
        parts.append(f"\nFile: {row['path']}")
        if row.get('line'):
            parts.append(f"Line: {row['line']}")

    # Add diff hunk (the actual code being reviewed)
    if row.get('diff_hunk'):
        parts.append(f"\nCode diff:\n```\n{row['diff_hunk']}\n```")

    return "\n".join(parts)


def build_metadata(row, category):
    """Build metadata dict for filtering/analysis."""
    return {
        "comment_id": row["id"],
        "pr_number": row["pr_number"],
        "domain": category.get("domain"),
        "severity": category.get("severity"),
        "component": category.get("component"),
        "language_context": category.get("language_context"),
        "feedback_type": category.get("feedback_type"),
        "is_style_example": bool(category.get("is_style_example")),
        "is_pattern": bool(category.get("is_pattern")),
        "has_code_suggestion": bool(category.get("has_code_suggestion")),
        "path": row.get("path"),
    }


def format_inline_review(row, category, pr_info):
    """Format an inline code review comment as SFT example."""
    context = build_review_context(row, pr_info)

    user_prompt = f"""Review the following code change:

{context}

Provide specific, actionable feedback on this code."""

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS["inline_review"]},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": row["body"]},
        ],
        "metadata": build_metadata(row, category),
        "source": "review_comment",
    }


def format_pr_discussion(row, category, pr_info):
    """Format a PR discussion comment as SFT example."""
    context_parts = [f"PR #{pr_info['number']}: {pr_info['title']}"]

    if pr_info.get('body'):
        body = pr_info['body']
        if len(body) > 1000:
            body = body[:1000] + "..."
        context_parts.append(f"\nDescription:\n{body}")

    # Add some PR stats for context
    if pr_info.get('changed_files'):
        context_parts.append(
            f"\nChanges: {pr_info['changed_files']} files, "
            f"+{pr_info.get('additions', 0)}/-{pr_info.get('deletions', 0)} lines"
        )

    context = "\n".join(context_parts)

    user_prompt = f"""Consider this pull request:

{context}

Provide feedback on this PR's approach and implementation."""

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS["pr_discussion"]},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": row["body"]},
        ],
        "metadata": build_metadata(row, category),
        "source": "issue_comment",
    }


def format_review_verdict(row, category, pr_info):
    """Format a review verdict as SFT example."""
    context_parts = [f"PR #{pr_info['number']}: {pr_info['title']}"]

    if pr_info.get('body'):
        body = pr_info['body']
        if len(body) > 1000:
            body = body[:1000] + "..."
        context_parts.append(f"\nDescription:\n{body}")

    verdict_text = row.get('state', 'COMMENTED')
    context_parts.append(f"\nReview verdict: {verdict_text}")

    context = "\n".join(context_parts)

    user_prompt = f"""Provide a final review for this pull request:

{context}

Give your assessment and any required changes."""

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPTS["review_verdict"]},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": row["body"]},
        ],
        "metadata": build_metadata(row, category),
        "source": "review",
    }


def load_pr_info(conn):
    """Load all PR info into a dict keyed by pr_number."""
    cursor = conn.execute("""
        SELECT number, title, body, changed_files, additions, deletions, base_branch
        FROM prs
    """)
    return {row["number"]: dict(row) for row in cursor}


def load_categories(conn):
    """Load all categories into a dict keyed by (comment_id, comment_type)."""
    cursor = conn.execute("""
        SELECT
            cc.comment_id, cc.comment_type,
            d.name as domain, cc.theme, cc.severity, cc.is_style_example,
            cc.component, cc.port, cc.subsystem, cc.language_context,
            cc.code_construct, cc.concern_type, cc.feedback_type,
            cc.is_pattern, cc.cpython_related, cc.has_code_suggestion, cc.keywords
        FROM comment_categories cc
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE cc.theme != 'FAILED_CATEGORIZATION'
    """)
    categories = {}
    for row in cursor:
        key = (row["comment_id"], row["comment_type"])
        categories[key] = dict(row)
    return categories


def export_sft_dataset():
    """Export all categorized reviews to SFT format."""
    print(f"Loading data from {DB_PATH}")
    conn = get_connection()

    # Load lookup tables
    pr_info = load_pr_info(conn)
    categories = load_categories(conn)
    print(f"Loaded {len(pr_info)} PRs, {len(categories)} categorized comments")

    # Collect all examples
    examples = []
    stats = defaultdict(int)

    # Process inline review comments
    print("Processing review comments...")
    cursor = conn.execute("""
        SELECT id, pr_number, body, path, line, diff_hunk
        FROM review_comments
        WHERE body IS NOT NULL AND body != ''
    """)
    for row in cursor:
        key = (row["id"], "review_comment")
        if key not in categories:
            stats["uncategorized_review_comments"] += 1
            continue
        pr = pr_info.get(row["pr_number"], {"number": row["pr_number"], "title": "Unknown"})
        example = format_inline_review(dict(row), categories[key], pr)
        examples.append(example)
        stats["review_comments"] += 1

    # Process PR discussion comments
    print("Processing issue comments...")
    cursor = conn.execute("""
        SELECT id, pr_number, body
        FROM issue_comments
        WHERE body IS NOT NULL AND body != ''
    """)
    for row in cursor:
        key = (row["id"], "issue_comment")
        if key not in categories:
            stats["uncategorized_issue_comments"] += 1
            continue
        pr = pr_info.get(row["pr_number"], {"number": row["pr_number"], "title": "Unknown"})
        example = format_pr_discussion(dict(row), categories[key], pr)
        examples.append(example)
        stats["issue_comments"] += 1

    # Process review verdicts (with body text)
    print("Processing review verdicts...")
    cursor = conn.execute("""
        SELECT id, pr_number, state, body
        FROM reviews
        WHERE body IS NOT NULL AND body != ''
    """)
    for row in cursor:
        key = (row["id"], "review")
        if key not in categories:
            stats["uncategorized_reviews"] += 1
            continue
        pr = pr_info.get(row["pr_number"], {"number": row["pr_number"], "title": "Unknown"})
        example = format_review_verdict(dict(row), categories[key], pr)
        examples.append(example)
        stats["reviews"] += 1

    conn.close()

    print(f"\nProcessing stats:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"  Total examples: {len(examples)}")

    # Shuffle and split into train/eval
    random.seed(RANDOM_SEED)
    random.shuffle(examples)

    eval_count = int(len(examples) * EVAL_FRACTION)
    eval_examples = examples[:eval_count]
    train_examples = examples[eval_count:]

    print(f"\nSplit: {len(train_examples)} train, {len(eval_examples)} eval")

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    # Write training set
    train_path = OUTPUT_DIR / "reviews_sft.jsonl"
    with open(train_path, "w") as f:
        for ex in train_examples:
            f.write(json.dumps(ex) + "\n")
    print(f"Wrote {len(train_examples)} examples to {train_path}")

    # Write held-out evaluation set
    eval_path = EVAL_DIR / "held_out_reviews.jsonl"
    with open(eval_path, "w") as f:
        for ex in eval_examples:
            f.write(json.dumps(ex) + "\n")
    print(f"Wrote {len(eval_examples)} examples to {eval_path}")

    # Write summary stats
    summary = {
        "exported_at": datetime.now().isoformat(),
        "total_examples": len(examples),
        "train_examples": len(train_examples),
        "eval_examples": len(eval_examples),
        "eval_fraction": EVAL_FRACTION,
        "random_seed": RANDOM_SEED,
        "stats": dict(stats),
        "sources": {
            "review_comments": stats["review_comments"],
            "issue_comments": stats["issue_comments"],
            "reviews": stats["reviews"],
        },
    }

    summary_path = OUTPUT_DIR / "reviews_sft_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote summary to {summary_path}")


if __name__ == "__main__":
    export_sft_dataset()
