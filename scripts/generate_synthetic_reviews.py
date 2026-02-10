#!/usr/bin/env python3
"""
Generate synthetic (diff -> review) training pairs using Claude CLI.

Selects ~500 PRs with the largest/most complex diffs from the review database,
builds a prompt with dpgeorge's style guide, few-shot examples from the DB,
and the PR's diff context, then calls Claude CLI to generate a synthetic review.

Output: SFT-format JSONL at data/training/synthetic_reviews.jsonl
"""

import json
import logging
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "raw" / "dpgeorge_reviews.db"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
OUTPUT_PATH = OUTPUT_DIR / "synthetic_reviews.jsonl"
SUMMARY_PATH = OUTPUT_DIR / "synthetic_reviews_summary.json"
CHECKPOINT_PATH = OUTPUT_DIR / ".synthetic_checkpoint.json"

TARGET_PR_COUNT = 500
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_TIMEOUT = 120
CLAUDE_BUDGET = "0.05"

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

STYLE_GUIDE = """\
dpgeorge's code review style:
- Extremely terse and direct. Often just one sentence.
- Points out the specific issue without lengthy explanation.
- Uses imperative mood: "Use X instead of Y", "This should be Z", "Remove this."
- Frequently provides corrected code inline using markdown code blocks.
- Never uses greetings, pleasantries, or encouragement.
- Focuses on: correctness bugs, style violations (naming, formatting), unnecessary complexity, missing error handling, portability issues.
- Common patterns: "This can be simplified to:", "No need for X here.", "Should use mp_raise_ValueError().", "Missing check for NULL.", "Style: use lowercase."
- When code is acceptable, often just says "Looks good" or approves silently."""

SYSTEM_PROMPT = """\
You are an expert MicroPython code reviewer with deep knowledge of the codebase. \
Your reviews are concise, technically precise, and focus on correctness, performance, \
and maintainability. You write in a direct, no-nonsense style - technical facts \
without unnecessary pleasantries.

When reviewing code:
- Identify potential bugs, edge cases, and correctness issues
- Point out portability concerns across MicroPython's 22 ports
- Note memory allocation patterns and potential leaks
- Flag deviations from MicroPython coding conventions
- Suggest specific improvements with code examples when helpful

Keep feedback actionable and specific to the code shown."""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def select_target_prs(conn, limit=TARGET_PR_COUNT):
    """Select PRs with the largest diffs that have review comments with diff hunks."""
    cursor = conn.execute(
        """
        SELECT p.number, p.title, p.changed_files, p.additions, p.deletions
        FROM prs p
        WHERE p.changed_files IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM review_comments rc
            WHERE rc.pr_number = p.number
              AND rc.diff_hunk IS NOT NULL AND rc.diff_hunk != ''
          )
        ORDER BY p.changed_files DESC, (p.additions + p.deletions) DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(row) for row in cursor]


def get_pr_diff_context(conn, pr_number):
    """Extract deduplicated diff hunks from review_comments, grouped by file path."""
    cursor = conn.execute(
        """
        SELECT path, diff_hunk
        FROM review_comments
        WHERE pr_number = ? AND diff_hunk IS NOT NULL AND diff_hunk != ''
        ORDER BY path, line
        """,
        (pr_number,),
    )

    hunks_by_file = defaultdict(list)
    seen_by_file = defaultdict(set)

    for row in cursor:
        path = row["path"] or "unknown"
        hunk = row["diff_hunk"].strip()
        if hunk not in seen_by_file[path]:
            seen_by_file[path].add(hunk)
            hunks_by_file[path].append(hunk)

    if not hunks_by_file:
        return None

    parts = []
    for path in sorted(hunks_by_file.keys()):
        parts.append(f"--- a/{path}")
        parts.append(f"+++ b/{path}")
        for hunk in hunks_by_file[path]:
            parts.append(hunk)
        parts.append("")  # blank line between files

    return "\n".join(parts)


def get_domain_for_pr(conn, pr_number):
    """Get the most common domain for a PR's review comments."""
    cursor = conn.execute(
        """
        SELECT d.name, COUNT(*) as cnt
        FROM comment_categories cc
        JOIN domains d ON cc.domain_id = d.id
        WHERE cc.comment_id IN (
            SELECT id FROM review_comments WHERE pr_number = ?
        )
        AND cc.comment_type = 'review_comment'
        GROUP BY d.name
        ORDER BY cnt DESC
        LIMIT 1
        """,
        (pr_number,),
    )
    row = cursor.fetchone()
    return row["name"] if row else None


def get_example_reviews(conn, domain, limit=3):
    """
    Get style example reviews with code suggestions from a similar domain.

    Picks reviews with is_style_example=1 AND has_code_suggestion=1,
    preferring the given domain, ordered by body length DESC.
    """
    # Try domain-matched first
    cursor = conn.execute(
        """
        SELECT rc.body, rc.path, rc.diff_hunk
        FROM review_comments rc
        JOIN comment_categories cc ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
        JOIN domains d ON cc.domain_id = d.id
        WHERE cc.is_style_example = 1
          AND cc.has_code_suggestion = 1
          AND d.name = ?
          AND rc.body IS NOT NULL AND rc.body != ''
          AND rc.diff_hunk IS NOT NULL AND rc.diff_hunk != ''
        ORDER BY LENGTH(rc.body) DESC
        LIMIT ?
        """,
        (domain, limit),
    )
    results = [dict(row) for row in cursor]

    # If not enough, fill from any domain
    if len(results) < limit:
        remaining = limit - len(results)
        existing_ids = set()
        # Fetch additional from any domain
        cursor = conn.execute(
            """
            SELECT rc.body, rc.path, rc.diff_hunk
            FROM review_comments rc
            JOIN comment_categories cc ON cc.comment_id = rc.id AND cc.comment_type = 'review_comment'
            WHERE cc.is_style_example = 1
              AND cc.has_code_suggestion = 1
              AND rc.body IS NOT NULL AND rc.body != ''
              AND rc.diff_hunk IS NOT NULL AND rc.diff_hunk != ''
            ORDER BY LENGTH(rc.body) DESC
            LIMIT ?
            """,
            (remaining + len(results),),  # fetch extra to allow dedup
        )
        for row in cursor:
            if row["body"] not in existing_ids and len(results) < limit:
                existing_ids.add(row["body"])
                if dict(row) not in results:
                    results.append(dict(row))

    return results[:limit]


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def format_example_review(example, index):
    """Format a single example review for the prompt."""
    parts = [f"Example {index}:"]
    if example.get("path"):
        parts.append(f"File: {example['path']}")
    if example.get("diff_hunk"):
        # Truncate very long hunks
        hunk = example["diff_hunk"]
        if len(hunk) > 600:
            hunk = hunk[:600] + "\n[...truncated...]"
        parts.append(f"Diff:\n```\n{hunk}\n```")
    parts.append(f"Review:\n{example['body']}")
    return "\n".join(parts)


def build_prompt(pr, diff_context, examples):
    """Build the full prompt for Claude CLI."""
    parts = [
        STYLE_GUIDE,
        "",
        "Here are examples of this reviewer's style:",
        "",
    ]

    for i, ex in enumerate(examples, 1):
        parts.append(format_example_review(ex, i))
        parts.append("")

    parts.append("---")
    parts.append("")
    parts.append(
        f"Now review the following diff from PR #{pr['number']}: {pr['title']}"
    )
    parts.append("")
    parts.append(f"```diff\n{diff_context}\n```")
    parts.append("")
    parts.append(
        "Write a code review in the style shown above. "
        "Be terse and direct. Focus on the most important issues. "
        "Provide corrected code where appropriate."
    )

    prompt = "\n".join(parts)

    # Truncate if excessively long (Claude Haiku context is large but we want
    # to keep costs down and avoid timeouts on huge diffs)
    max_chars = 50000
    if len(prompt) > max_chars:
        # Keep the beginning (style guide + examples) and truncate diff
        preamble_end = prompt.find("```diff\n")
        if preamble_end > 0:
            preamble = prompt[:preamble_end]
            remaining = max_chars - len(preamble) - 200  # leave room for suffix
            diff_section = diff_context[:remaining] + "\n[...diff truncated...]"
            prompt = (
                preamble
                + f"```diff\n{diff_section}\n```\n\n"
                + "Write a code review in the style shown above. "
                + "Be terse and direct. Focus on the most important issues. "
                + "Provide corrected code where appropriate."
            )

    return prompt


# ---------------------------------------------------------------------------
# Claude CLI
# ---------------------------------------------------------------------------


def call_claude(prompt):
    """Call Claude CLI and return the review text, or None on failure."""
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                CLAUDE_MODEL,
                "--output-format",
                "json",
                "--tools",
                "",
                "--max-budget-usd",
                CLAUDE_BUDGET,
            ],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
        )
        if result.returncode != 0:
            log.warning("Claude CLI returned %d: %s", result.returncode, result.stderr[:200])
            return None

        output = json.loads(result.stdout)
        review_text = output.get("result", "")
        if not review_text or not review_text.strip():
            log.warning("Empty result from Claude CLI")
            return None
        return review_text.strip()

    except subprocess.TimeoutExpired:
        log.warning("Claude CLI timed out after %ds", CLAUDE_TIMEOUT)
        return None
    except json.JSONDecodeError as e:
        log.warning("Failed to parse Claude CLI output: %s", e)
        return None
    except FileNotFoundError:
        log.error("Claude CLI not found. Is it installed and on PATH?")
        sys.exit(1)
    except Exception as e:
        log.warning("Unexpected error calling Claude CLI: %s", e)
        return None


# ---------------------------------------------------------------------------
# Checkpoint management
# ---------------------------------------------------------------------------


def load_checkpoint():
    """Load completed PR numbers from checkpoint file."""
    if CHECKPOINT_PATH.exists():
        try:
            data = json.loads(CHECKPOINT_PATH.read_text())
            completed = set(data.get("completed_prs", []))
            log.info("Loaded checkpoint: %d PRs already completed", len(completed))
            return completed
        except (json.JSONDecodeError, KeyError):
            log.warning("Corrupt checkpoint file, starting fresh")
    return set()


def save_checkpoint(completed_prs):
    """Save completed PR numbers to checkpoint file."""
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "completed_prs": sorted(completed_prs),
        "updated_at": datetime.now().isoformat(),
    }
    CHECKPOINT_PATH.write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if not DB_PATH.exists():
        log.error("Database not found at %s", DB_PATH)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = get_connection()
    completed = load_checkpoint()

    # Select target PRs
    target_prs = select_target_prs(conn)
    log.info("Selected %d target PRs (by diff complexity)", len(target_prs))

    # Pre-load existing output lines if resuming, to append
    existing_lines = []
    if OUTPUT_PATH.exists() and completed:
        with open(OUTPUT_PATH) as f:
            existing_lines = f.readlines()
        log.info("Existing output has %d lines", len(existing_lines))

    generated = len(completed)
    skipped = 0
    failed = 0
    start_time = time.time()

    # Open output in append mode if resuming, write mode otherwise
    mode = "a" if completed else "w"
    with open(OUTPUT_PATH, mode) as out_f:
        for i, pr in enumerate(target_prs):
            pr_num = pr["number"]

            if pr_num in completed:
                continue

            # Get diff context
            diff_context = get_pr_diff_context(conn, pr_num)
            if not diff_context:
                log.warning("PR #%d: no diff context, skipping", pr_num)
                skipped += 1
                continue

            # Get domain for few-shot example selection
            domain = get_domain_for_pr(conn, pr_num)
            if not domain:
                domain = "correctness"  # fallback

            # Get few-shot examples
            examples = get_example_reviews(conn, domain, limit=3)

            # Build prompt and call Claude
            prompt = build_prompt(pr, diff_context, examples)
            review_text = call_claude(prompt)

            if review_text is None:
                failed += 1
                log.warning(
                    "PR #%d: generation failed (%d failed so far)", pr_num, failed
                )
                continue

            # Build SFT record
            user_content = (
                f"Review the following code change from PR #{pr_num}: {pr['title']}\n\n"
                f"```diff\n{diff_context}\n```\n\n"
                f"Provide specific, actionable feedback on this code."
            )

            record = {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                    {"role": "assistant", "content": review_text},
                ],
                "metadata": {
                    "pr_number": pr_num,
                    "source": "synthetic",
                    "model": CLAUDE_MODEL,
                    "domain": domain,
                    "changed_files": pr.get("changed_files"),
                    "additions": pr.get("additions"),
                    "deletions": pr.get("deletions"),
                },
            }

            out_f.write(json.dumps(record) + "\n")
            out_f.flush()

            # Update checkpoint
            completed.add(pr_num)
            generated += 1
            save_checkpoint(completed)

            # Progress logging
            if generated % 10 == 0:
                elapsed = time.time() - start_time
                rate = (generated - len(completed - {pr_num})) / max(elapsed, 1) * 3600
                log.info(
                    "Generated %d/%d synthetic reviews, %d skipped/failed (%.0f/hr)",
                    generated,
                    len(target_prs),
                    skipped + failed,
                    rate,
                )

    conn.close()

    # Write summary
    elapsed_total = time.time() - start_time
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_target_prs": len(target_prs),
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "model": CLAUDE_MODEL,
        "elapsed_seconds": round(elapsed_total, 1),
        "output_path": str(OUTPUT_PATH),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))

    log.info("Done. Generated %d/%d synthetic reviews, %d skipped, %d failed",
             generated, len(target_prs), skipped, failed)
    log.info("Output: %s", OUTPUT_PATH)
    log.info("Summary: %s", SUMMARY_PATH)


if __name__ == "__main__":
    main()
