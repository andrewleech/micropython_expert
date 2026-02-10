#!/usr/bin/env python3
"""
Export aggregated PR-level review training examples.

Groups multiple review comments per PR into single training examples where the
assistant provides a file-grouped review of the entire PR. Only includes PRs
with 3+ substantive review comments (suggestions, requirements, questions) that
have diff context and are not reply threads.

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
import sqlite3
from collections import defaultdict, OrderedDict
from datetime import datetime
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
OUTPUT_PATH = OUTPUT_DIR / "pr_reviews.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "pr_reviews_summary.json"

# Token budget: skip PRs where the combined diff context is unreasonably large.
# This avoids generating examples that would exceed typical context windows.
MAX_DIFF_CHARS = 30_000

SYSTEM_PROMPT = (
    "You are an expert MicroPython code reviewer. Review this pull request "
    "and provide feedback on all issues found. Group your comments by file. "
    "Be direct and specific."
)

# Minimum substantive comments per PR to qualify
MIN_COMMENTS = 3


def get_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_qualifying_pr_numbers(conn):
    """Return set of pr_numbers with >= MIN_COMMENTS substantive review comments."""
    cursor = conn.execute(
        """
        SELECT rc.pr_number
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        WHERE cc.feedback_type IN ('suggestion', 'requirement', 'question')
          AND rc.diff_hunk IS NOT NULL
          AND rc.in_reply_to_id IS NULL
          AND cc.theme != 'FAILED_CATEGORIZATION'
        GROUP BY rc.pr_number
        HAVING COUNT(*) >= ?
        """,
        (MIN_COMMENTS,),
    )
    return [row["pr_number"] for row in cursor]


def load_pr_info(conn, pr_numbers):
    """Load PR metadata for the given pr_numbers."""
    placeholders = ",".join("?" * len(pr_numbers))
    cursor = conn.execute(
        f"SELECT number, title, body FROM prs WHERE number IN ({placeholders})",
        pr_numbers,
    )
    return {row["number"]: dict(row) for row in cursor}


def load_comments_for_prs(conn, pr_numbers):
    """Load all substantive review comments for qualifying PRs, with domain info."""
    placeholders = ",".join("?" * len(pr_numbers))
    cursor = conn.execute(
        f"""
        SELECT
            rc.id, rc.pr_number, rc.body, rc.path, rc.line, rc.diff_hunk,
            d.name AS domain
        FROM review_comments rc
        JOIN comment_categories cc
            ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        LEFT JOIN domains d ON cc.domain_id = d.id
        WHERE cc.feedback_type IN ('suggestion', 'requirement', 'question')
          AND rc.diff_hunk IS NOT NULL
          AND rc.in_reply_to_id IS NULL
          AND cc.theme != 'FAILED_CATEGORIZATION'
          AND rc.pr_number IN ({placeholders})
        ORDER BY rc.pr_number, rc.path, rc.line
        """,
        pr_numbers,
    )
    grouped = defaultdict(list)
    for row in cursor:
        grouped[row["pr_number"]].append(dict(row))
    return grouped


def build_user_prompt(pr_info, comments):
    """Build the user prompt from PR metadata and deduplicated diff hunks."""
    parts = []

    # PR header
    title = pr_info.get("title") or "Untitled"
    parts.append(f"PR: {title}")

    body = pr_info.get("body") or ""
    if body:
        if len(body) > 500:
            body = body[:500] + "..."
        parts.append(f"\nDescription:\n{body}")

    # Collect diff hunks grouped by file, deduplicating
    file_hunks = OrderedDict()
    for c in comments:
        path = c["path"] or "unknown"
        if path not in file_hunks:
            file_hunks[path] = []
        hunk = c["diff_hunk"]
        if hunk and hunk not in file_hunks[path]:
            file_hunks[path].append(hunk)

    parts.append("\nCode changes:")
    for path, hunks in file_hunks.items():
        parts.append(f"\n**{path}**")
        for hunk in hunks:
            parts.append(f"```\n{hunk}\n```")

    return "\n".join(parts)


def build_assistant_response(comments):
    """Build file-grouped review response from comments."""
    file_comments = OrderedDict()
    for c in comments:
        path = c["path"] or "unknown"
        if path not in file_comments:
            file_comments[path] = []
        line = c["line"]
        body = (c["body"] or "").strip()
        if not body:
            continue
        file_comments[path].append((line, body))

    parts = []
    for path, entries in file_comments.items():
        if not entries:
            continue
        parts.append(f"**{path}**")
        for line, body in entries:
            if line is not None:
                parts.append(f"- Line {line}: {body}")
            else:
                parts.append(f"- {body}")
        parts.append("")  # blank line between files

    return "\n".join(parts).rstrip()


def export_pr_reviews():
    """Main export function."""
    print(f"Database: {DB_PATH}")
    conn = get_connection()

    # Step 1: Find qualifying PRs
    pr_numbers = get_qualifying_pr_numbers(conn)
    print(f"Qualifying PRs (>= {MIN_COMMENTS} substantive comments): {len(pr_numbers)}")

    if not pr_numbers:
        print("No qualifying PRs found.")
        conn.close()
        return

    # Step 2: Load data
    pr_info_map = load_pr_info(conn, pr_numbers)
    comments_by_pr = load_comments_for_prs(conn, pr_numbers)
    conn.close()

    # Step 3: Build examples
    examples = []
    skipped_too_large = 0
    skipped_empty_response = 0
    total_comments = 0
    all_files = set()
    comments_per_pr = []

    for pr_num in sorted(comments_by_pr.keys()):
        comments = comments_by_pr[pr_num]
        pr = pr_info_map.get(pr_num, {"number": pr_num, "title": "Unknown", "body": ""})

        user_prompt = build_user_prompt(pr, comments)

        # Skip if combined diff context is too large
        if len(user_prompt) > MAX_DIFF_CHARS:
            skipped_too_large += 1
            continue

        assistant_response = build_assistant_response(comments)
        if not assistant_response.strip():
            skipped_empty_response += 1
            continue

        # Collect metadata
        files_reviewed = list(OrderedDict.fromkeys(c["path"] for c in comments if c["path"]))
        domains = sorted(set(c["domain"] for c in comments if c["domain"]))

        all_files.update(files_reviewed)
        total_comments += len(comments)
        comments_per_pr.append(len(comments))

        example = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response},
            ],
            "metadata": {
                "pr_number": pr_num,
                "num_comments": len(comments),
                "files_reviewed": files_reviewed,
                "domains": domains,
            },
        }
        examples.append(example)

    # Step 4: Write output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    avg_comments = sum(comments_per_pr) / len(comments_per_pr) if comments_per_pr else 0

    summary = {
        "exported_at": datetime.now().isoformat(),
        "total_qualifying_prs": len(pr_numbers),
        "total_output_examples": len(examples),
        "skipped_too_large": skipped_too_large,
        "skipped_empty_response": skipped_empty_response,
        "total_comments_included": total_comments,
        "avg_comments_per_pr": round(avg_comments, 1),
        "total_unique_files": len(all_files),
        "max_diff_chars": MAX_DIFF_CHARS,
        "min_comments": MIN_COMMENTS,
    }

    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)

    # Print stats
    print(f"\n--- Stats ---")
    print(f"Total qualifying PRs:   {len(pr_numbers)}")
    print(f"Total output examples:  {len(examples)}")
    print(f"Skipped (too large):    {skipped_too_large}")
    print(f"Skipped (empty resp):   {skipped_empty_response}")
    print(f"Average comments/PR:    {avg_comments:.1f}")
    print(f"Total unique files:     {len(all_files)}")
    print(f"\nWrote {OUTPUT_PATH}")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    export_pr_reviews()
