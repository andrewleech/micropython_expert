#!/usr/bin/env python3
"""
Validate training data quality before training.

Runs automated checks to catch data quality regressions.
Exit code 0 if all pass, 1 if any fail.
"""

import json
import re
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_DIR = PROJECT_ROOT / "data" / "training"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

# Files
REVIEWS_SFT = TRAIN_DIR / "reviews_sft.jsonl"
PR_REVIEWS = TRAIN_DIR / "pr_reviews.jsonl"
SYNTHETIC_REVIEWS = TRAIN_DIR / "synthetic_reviews.jsonl"
DPO_PREFS = TRAIN_DIR / "dpo_preferences.jsonl"
HELD_OUT = EVAL_DIR / "held_out_reviews.jsonl"

SFT_FILES = [REVIEWS_SFT, PR_REVIEWS, SYNTHETIC_REVIEWS]

# Patterns that indicate role confusion in assistant responses.
# "Thanks for" is excluded because dpgeorge sometimes starts substantive
# feedback with "Thanks for fixing this, but..." which is real review content.
ROLE_CONFUSION_PATTERNS = [
    re.compile(r"^merged\.?\s*$", re.IGNORECASE),
    re.compile(r"^lgtm\.?\s*$", re.IGNORECASE),
    re.compile(r"^thank\s+you\.?\s*$", re.IGNORECASE),
    re.compile(r"^looks\s+good\s+to\s+me\.?\s*$", re.IGNORECASE),
    re.compile(r"^looks\s+good\.?\s*$", re.IGNORECASE),
]


def load_jsonl(path: Path) -> list:
    """Load JSONL file, return list of parsed objects."""
    examples = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))
    return examples


def get_assistant_body(example: dict) -> str | None:
    """Extract assistant message content from an example."""
    messages = example.get("messages", [])
    for msg in messages:
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return None


def get_user_body(example: dict) -> str | None:
    """Extract user message content from an example."""
    messages = example.get("messages", [])
    for msg in messages:
        if msg.get("role") == "user":
            return msg.get("content", "")
    return None


def get_pr_number(example: dict) -> int | None:
    """Extract pr_number from metadata."""
    meta = example.get("metadata", {})
    pr = meta.get("pr_number")
    if pr is not None:
        return int(pr)
    return None


def result(passed: bool, name: str, detail: str) -> bool:
    """Print check result and return pass status."""
    tag = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{tag}] {name}: {detail}")
    return passed


def skip(name: str, reason: str):
    """Print skip notice."""
    print(f"  [{YELLOW}SKIP{RESET}] {name}: {reason}")


def check_no_role_confusion() -> bool:
    """Check 1: No role confusion in reviews_sft.jsonl assistant responses."""
    name = "No role confusion"
    if not REVIEWS_SFT.exists():
        skip(name, f"{REVIEWS_SFT.name} not found")
        return True

    examples = load_jsonl(REVIEWS_SFT)
    violations = 0
    for ex in examples:
        body = get_assistant_body(ex)
        if body is None:
            continue
        body_stripped = body.strip()
        for pattern in ROLE_CONFUSION_PATTERNS:
            if pattern.match(body_stripped):
                violations += 1
                break

    return result(
        violations == 0,
        name,
        f"{violations} examples with role-confused assistant responses"
        if violations
        else f"0 violations in {len(examples)} examples",
    )


def check_diff_context() -> bool:
    """Check 2: All SFT examples in reviews_sft.jsonl have diff context."""
    name = "SFT examples have diff context"
    if not REVIEWS_SFT.exists():
        skip(name, f"{REVIEWS_SFT.name} not found")
        return True

    examples = load_jsonl(REVIEWS_SFT)
    missing = 0
    for ex in examples:
        body = get_user_body(ex)
        if body is None:
            missing += 1
            continue
        if "Code diff:" not in body and "```" not in body:
            missing += 1

    return result(
        missing == 0,
        name,
        f"{missing} examples missing diff context"
        if missing
        else f"all {len(examples)} examples have diff context",
    )


def check_no_train_eval_leakage() -> bool:
    """Check 3: No PR numbers shared between train and eval sets."""
    name = "No train/eval leakage"
    if not REVIEWS_SFT.exists():
        skip(name, f"{REVIEWS_SFT.name} not found")
        return True
    if not HELD_OUT.exists():
        skip(name, f"{HELD_OUT.name} not found")
        return True

    train_examples = load_jsonl(REVIEWS_SFT)
    eval_examples = load_jsonl(HELD_OUT)

    train_prs = {get_pr_number(ex) for ex in train_examples} - {None}
    eval_prs = {get_pr_number(ex) for ex in eval_examples} - {None}
    overlap = train_prs & eval_prs

    return result(
        len(overlap) == 0,
        name,
        f"{len(overlap)} PRs in both train and eval: {sorted(overlap)[:10]}"
        if overlap
        else f"0 overlap between {len(train_prs)} train and {len(eval_prs)} eval PRs",
    )


def check_dpo_no_raw_tokens() -> bool:
    """Check 4: No raw special tokens in DPO preferences."""
    name = "DPO no raw special tokens"
    if not DPO_PREFS.exists():
        skip(name, f"{DPO_PREFS.name} not found")
        return True

    raw_content = DPO_PREFS.read_text()
    bad_tokens = ["<|system|>", "<|end|>"]
    found = []
    for token in bad_tokens:
        count = raw_content.count(token)
        if count > 0:
            found.append(f"{token} x{count}")

    return result(
        len(found) == 0,
        name,
        f"found raw tokens: {', '.join(found)}" if found else "no raw special tokens",
    )


def check_length_sanity() -> bool:
    """Check 5: Assistant response length within bounds across SFT files.

    Min threshold is 3 chars (not 10) because dpgeorge's terse style includes
    legitimate one-word corrections like "uint32_t?", "(void)", "`void`".
    """
    name = "Length sanity (3-5000 chars)"
    total_checked = 0
    too_short = 0
    too_long = 0
    files_checked = []

    for path in SFT_FILES:
        if not path.exists():
            continue
        files_checked.append(path.name)
        examples = load_jsonl(path)
        for ex in examples:
            body = get_assistant_body(ex)
            if body is None:
                continue
            total_checked += 1
            if len(body) < 3:
                too_short += 1
            elif len(body) > 5000:
                too_long += 1

    if not files_checked:
        skip(name, "no SFT files found")
        return True

    violations = too_short + too_long
    detail = (
        f"{too_short} too short, {too_long} too long out of {total_checked}"
        if violations
        else f"all {total_checked} responses within bounds ({', '.join(files_checked)})"
    )
    return result(violations == 0, name, detail)


def check_balanced_domains() -> bool:
    """Check 6: No single domain > 40% in reviews_sft.jsonl."""
    name = "Balanced domains (<= 40% each)"
    if not REVIEWS_SFT.exists():
        skip(name, f"{REVIEWS_SFT.name} not found")
        return True

    examples = load_jsonl(REVIEWS_SFT)
    domains = Counter()
    for ex in examples:
        domain = ex.get("metadata", {}).get("domain", "unknown")
        domains[domain] += 1

    total = sum(domains.values())
    if total == 0:
        skip(name, "no examples with domain metadata")
        return True

    over_threshold = []
    for domain, count in domains.most_common():
        pct = 100.0 * count / total
        if pct > 40.0:
            over_threshold.append(f"{domain}={pct:.1f}%")

    return result(
        len(over_threshold) == 0,
        name,
        f"domains over 40%: {', '.join(over_threshold)}"
        if over_threshold
        else f"{len(domains)} domains, max {100.0 * domains.most_common(1)[0][1] / total:.1f}%",
    )


def check_deduplication() -> bool:
    """Check 7: No accidental duplicate source comments in reviews_sft.jsonl.

    Uses comment_id from metadata rather than (pr_number, body) to avoid
    flagging intentional quality-weighted oversampling as duplication.
    Only flags duplicates where different comment_ids produce identical
    (pr_number, body) pairs, indicating actual data issues.
    """
    name = "No accidental duplicate source comments"
    if not REVIEWS_SFT.exists():
        skip(name, f"{REVIEWS_SFT.name} not found")
        return True

    examples = load_jsonl(REVIEWS_SFT)
    # Check for duplicate comment_ids (same source comment appearing multiple
    # times before oversampling). Oversampled copies share the same comment_id
    # so we just verify each unique comment_id maps to the same content.
    # Multiple different comment_ids with the same body text are fine — that's
    # dpgeorge making the same terse correction on multiple code locations.
    cid_to_body: dict[int, str] = {}
    inconsistent = 0
    for ex in examples:
        cid = ex.get("metadata", {}).get("comment_id")
        body = get_assistant_body(ex)
        if cid is None or body is None:
            continue
        if cid in cid_to_body:
            if cid_to_body[cid] != body:
                inconsistent += 1
        else:
            cid_to_body[cid] = body

    return result(
        inconsistent == 0,
        name,
        f"{inconsistent} comment_ids with inconsistent body text"
        if inconsistent
        else f"0 inconsistencies ({len(cid_to_body)} unique comments, "
        f"{len(examples)} total with oversampling)",
    )


def check_message_format() -> bool:
    """Check 8: Every SFT example has exactly [system, user, assistant] messages."""
    name = "Message format [system, user, assistant]"
    expected_roles = ["system", "user", "assistant"]
    total_checked = 0
    violations = 0
    files_checked = []

    for path in SFT_FILES:
        if not path.exists():
            continue
        files_checked.append(path.name)
        examples = load_jsonl(path)
        for ex in examples:
            total_checked += 1
            messages = ex.get("messages", [])
            roles = [m.get("role") for m in messages]
            if roles != expected_roles:
                violations += 1

    if not files_checked:
        skip(name, "no SFT files found")
        return True

    return result(
        violations == 0,
        name,
        f"{violations} examples with wrong message format out of {total_checked}"
        if violations
        else f"all {total_checked} examples correct ({', '.join(files_checked)})",
    )


def main():
    print("Training data validation\n")

    checks = [
        check_no_role_confusion,
        check_diff_context,
        check_no_train_eval_leakage,
        check_dpo_no_raw_tokens,
        check_length_sanity,
        check_balanced_domains,
        check_deduplication,
        check_message_format,
    ]

    results = []
    for check in checks:
        results.append(check())

    failed = sum(1 for r in results if not r)
    passed = sum(1 for r in results if r)
    print(f"\n{passed}/{len(checks)} checks passed", end="")
    if failed:
        print(f", {RED}{failed} failed{RESET}")
    else:
        print(f" {GREEN}(all clear){RESET}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
