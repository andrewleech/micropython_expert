#!/usr/bin/env python3
"""
Export DPO preference dataset from review database.

Creates preference pairs by pairing reviews on similar topics with
different severity levels (blocking > suggestion > nitpick).

The intuition is that more impactful feedback (blocking issues) should be
preferred over less impactful feedback (nitpicks) for similar code contexts.

Output format (JSONL):
{
    "prompt": "system + user message (code context)",
    "chosen": "higher quality review response",
    "rejected": "lower quality review response"
}
"""

import json
import random
import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"

RANDOM_SEED = 42

# Severity ranking (higher = more preferred)
SEVERITY_RANK = {
    "blocking": 3,
    "suggestion": 2,
    "nitpick": 1,
}

# System prompt for DPO pairs
SYSTEM_PROMPT = """You are an expert MicroPython code reviewer with deep knowledge of the codebase. Your reviews are concise, technically precise, and focus on correctness, performance, and maintainability. You write in a direct, no-nonsense style - technical facts without unnecessary pleasantries."""


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_reviews_by_domain(conn):
    """Load all categorized reviews grouped by domain."""
    cursor = conn.execute("""
        SELECT
            rc.id, rc.pr_number, rc.body, rc.path, rc.diff_hunk,
            cc.severity, cc.component, cc.language_context,
            d.name as domain
        FROM review_comments rc
        JOIN comment_categories cc ON rc.id = cc.comment_id AND cc.comment_type = 'review_comment'
        JOIN domains d ON cc.domain_id = d.id
        WHERE rc.body IS NOT NULL AND rc.body != ''
            AND cc.severity IN ('blocking', 'suggestion', 'nitpick')
            AND rc.diff_hunk IS NOT NULL
    """)

    reviews_by_domain = defaultdict(lambda: defaultdict(list))
    for row in cursor:
        domain = row["domain"]
        component = row["component"] or "unknown"
        severity = row["severity"]
        reviews_by_domain[(domain, component)][severity].append(dict(row))

    return reviews_by_domain


def build_prompt(review):
    """Build the prompt part (context without response)."""
    parts = []

    if review.get("path"):
        parts.append(f"File: {review['path']}")

    if review.get("diff_hunk"):
        parts.append(f"\nCode diff:\n```\n{review['diff_hunk']}\n```")

    context = "\n".join(parts)

    user_prompt = f"""Review the following code change:

{context}

Provide specific, actionable feedback on this code."""

    return user_prompt


def create_preference_pairs(reviews_by_domain, max_pairs_per_group=10):
    """Create preference pairs from severity rankings."""
    pairs = []

    for (domain, component), severity_groups in reviews_by_domain.items():
        # Get reviews at each severity level
        blocking = severity_groups.get("blocking", [])
        suggestion = severity_groups.get("suggestion", [])
        nitpick = severity_groups.get("nitpick", [])

        # Pair blocking vs suggestion
        for chosen in blocking[:max_pairs_per_group]:
            for rejected in suggestion[:max_pairs_per_group]:
                # Only pair reviews with similar context length to avoid trivial differences
                chosen_len = len(chosen["body"])
                rejected_len = len(rejected["body"])
                if 0.3 < chosen_len / max(rejected_len, 1) < 3.0:
                    pairs.append({
                        "prompt": build_prompt(chosen),
                        "chosen": chosen["body"],
                        "rejected": rejected["body"],
                        "metadata": {
                            "domain": domain,
                            "component": component,
                            "chosen_severity": "blocking",
                            "rejected_severity": "suggestion",
                        },
                    })

        # Pair suggestion vs nitpick
        for chosen in suggestion[:max_pairs_per_group]:
            for rejected in nitpick[:max_pairs_per_group]:
                chosen_len = len(chosen["body"])
                rejected_len = len(rejected["body"])
                if 0.3 < chosen_len / max(rejected_len, 1) < 3.0:
                    pairs.append({
                        "prompt": build_prompt(chosen),
                        "chosen": chosen["body"],
                        "rejected": rejected["body"],
                        "metadata": {
                            "domain": domain,
                            "component": component,
                            "chosen_severity": "suggestion",
                            "rejected_severity": "nitpick",
                        },
                    })

        # Pair blocking vs nitpick (strongest contrast)
        for chosen in blocking[:max_pairs_per_group]:
            for rejected in nitpick[:max_pairs_per_group]:
                chosen_len = len(chosen["body"])
                rejected_len = len(rejected["body"])
                if 0.3 < chosen_len / max(rejected_len, 1) < 3.0:
                    pairs.append({
                        "prompt": build_prompt(chosen),
                        "chosen": chosen["body"],
                        "rejected": rejected["body"],
                        "metadata": {
                            "domain": domain,
                            "component": component,
                            "chosen_severity": "blocking",
                            "rejected_severity": "nitpick",
                        },
                    })

    return pairs


def create_style_preference_pairs(conn, max_pairs=2000):
    """Create preference pairs based on is_style_example flag."""
    cursor = conn.execute("""
        SELECT
            rc.id, rc.body, rc.path, rc.diff_hunk,
            cc.severity, cc.is_style_example
        FROM review_comments rc
        JOIN comment_categories cc ON rc.id = cc.comment_id AND cc.comment_type = 'review_comment'
        WHERE rc.body IS NOT NULL AND rc.body != ''
            AND rc.diff_hunk IS NOT NULL
    """)

    style_examples = []
    non_style_examples = []

    for row in cursor:
        if row["is_style_example"]:
            style_examples.append(dict(row))
        else:
            non_style_examples.append(dict(row))

    # Shuffle for random pairing
    random.shuffle(style_examples)
    random.shuffle(non_style_examples)

    pairs = []
    for chosen, rejected in zip(
        style_examples[:max_pairs], non_style_examples[:max_pairs]
    ):
        # Match by similar length
        chosen_len = len(chosen["body"])
        rejected_len = len(rejected["body"])
        if 0.3 < chosen_len / max(rejected_len, 1) < 3.0:
            pairs.append({
                "prompt": build_prompt(chosen),
                "chosen": chosen["body"],
                "rejected": rejected["body"],
                "metadata": {
                    "type": "style_preference",
                    "chosen_is_style_example": True,
                    "rejected_is_style_example": False,
                },
            })

    return pairs


def export_dpo_dataset():
    """Main export function."""
    print(f"Loading data from {DB_PATH}")
    conn = get_connection()

    random.seed(RANDOM_SEED)

    # Create severity-based pairs
    print("Loading reviews by domain...")
    reviews_by_domain = load_reviews_by_domain(conn)
    print(f"Found {len(reviews_by_domain)} domain/component groups")

    print("Creating severity preference pairs...")
    severity_pairs = create_preference_pairs(reviews_by_domain)
    print(f"Created {len(severity_pairs)} severity-based pairs")

    # Create style-based pairs
    print("Creating style preference pairs...")
    style_pairs = create_style_preference_pairs(conn)
    print(f"Created {len(style_pairs)} style-based pairs")

    # Combine and shuffle
    all_pairs = severity_pairs + style_pairs
    random.shuffle(all_pairs)

    print(f"\nTotal preference pairs: {len(all_pairs)}")

    # Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "dpo_preferences.jsonl"

    with open(output_path, "w") as f:
        for pair in all_pairs:
            # Format for DPO training (without metadata)
            output = {
                "prompt": f"<|system|>\n{SYSTEM_PROMPT}<|end|>\n<|user|>\n{pair['prompt']}<|end|>\n<|assistant|>\n",
                "chosen": pair["chosen"],
                "rejected": pair["rejected"],
            }
            f.write(json.dumps(output) + "\n")

    print(f"Wrote {len(all_pairs)} pairs to {output_path}")

    # Write summary
    summary = {
        "exported_at": datetime.now().isoformat(),
        "total_pairs": len(all_pairs),
        "severity_pairs": len(severity_pairs),
        "style_pairs": len(style_pairs),
        "random_seed": RANDOM_SEED,
    }

    summary_path = OUTPUT_DIR / "dpo_preferences_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote summary to {summary_path}")

    conn.close()


if __name__ == "__main__":
    export_dpo_dataset()
