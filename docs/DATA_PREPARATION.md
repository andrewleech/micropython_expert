# Data Preparation Guide

This document describes the v2 training data pipeline for the MicroPython Expert model.

## Dataset Overview

| Dataset | Source | Examples | Status |
|---------|--------|----------|--------|
| reviews_sft.jsonl | Filtered substantive review_comments | 7,532 (from 4,537 before oversampling) | Complete |
| pr_reviews.jsonl | Aggregated multi-comment PR reviews | 501 | Complete |
| synthetic_reviews.jsonl | Claude-generated (diff->review) pairs | 500 | Complete |
| wiki_qa.jsonl | GitHub wiki pages | 403 | Complete (unchanged) |
| codebase_qa.jsonl | MicroPython source code | 3,936 | Complete (unchanged) |
| app_dev_qa.jsonl | Practical usage topics | 539 | Complete (unchanged) |
| dpo_preferences.jsonl | Targeted failure mode pairs | 4,974 | Complete |
| combined_sft.jsonl | Weighted combination | 16,710 | Complete |

## Combined Dataset Summary

| Dataset | Original | Weight | After Weighting |
|---------|----------|--------|-----------------|
| reviews_sft | 7,532 | 1.0 | 7,532 |
| pr_reviews | 501 | 2.0 | 1,002 |
| synthetic_reviews | 500 | 2.5 | 1,250 |
| wiki_qa | 403 | 1.2 | 483 |
| codebase_qa | 3,936 | 1.5 | 5,904 |
| app_dev_qa | 539 | 1.0 | 539 |

## 1. Review SFT Dataset (reviews_sft.jsonl)

**Source:** `dpgeorge_reviews.db` (from dpgeorge-review-db project)

**Generation:** `python scripts/export_sft_dataset.py`

**Filtering:**
- Only `review_comments` (inline code comments with diff context)
- `feedback_type` in (`suggestion`, `requirement`, `question`)
- `diff_hunk IS NOT NULL`
- `in_reply_to_id IS NULL` (top-level comments only)
- All `issue_comments` and review verdicts are dropped (these lack diff context and cause role confusion)

**Result:** 4,537 substantive comments -> 7,532 after quality oversampling.

**Quality oversampling:**
- `has_code_suggestion`: 1.5x
- `is_pattern`: 1.2x
- `is_style_example`: 1.3x
- Weights multiply (e.g. a comment with both `has_code_suggestion` and `is_pattern` gets 1.5 * 1.2 = 1.8x)

**Eval split:** PR-based (no PR appears in both train and eval).
- 1,206 train PRs (7,532 examples)
- 133 eval PRs (551 examples)

**Format:**
```json
{
  "messages": [
    {"role": "system", "content": "...inline review system prompt..."},
    {"role": "user", "content": "Review the following code..."},
    {"role": "assistant", "content": "...actual dpgeorge review..."}
  ],
  "metadata": {
    "comment_id": 12345,
    "pr_number": 6789,
    "domain": "correctness",
    "severity": "blocking",
    "component": "py_core",
    ...
  }
}
```

Single system prompt focused on inline code review. Metadata includes 13-field categorization from dpgeorge-review-db.

## 2. PR Review Aggregation (pr_reviews.jsonl)

**Source:** `dpgeorge_reviews.db`

**Generation:** `python scripts/export_pr_reviews.py`

**Contents:**
- PRs with 3+ substantive review_comments aggregated into single training examples
- 543 qualifying PRs -> 501 examples (42 skipped where diff context exceeded 30k chars)

**Structure:**
- User prompt: PR title + body + concatenated diffs from reviewed files
- Assistant response: file-grouped multi-issue review combining all comments for that PR

**Format:** Same JSONL messages format as reviews_sft.

## 3. Synthetic Reviews (synthetic_reviews.jsonl)

**Generation:** `python scripts/generate_synthetic_reviews.py`

**Contents:** 500 synthetic review examples generated from real PR diffs.

**Method:**
- Uses `claude -p --model claude-haiku-4-5-20251001` (Claude Code CLI, no separate API key needed)
- Selects 500 PRs by diff complexity
- Builds prompts with dpgeorge style guide + 3 few-shot examples from the review database
- Checkpoint/resume via `.synthetic_checkpoint.json`
- Runtime: ~80 minutes (two runs, first interrupted at 140, resumed to completion)
- Zero failures across all 500 PRs

## 4. Wiki Q&A Dataset (wiki_qa.jsonl)

**Source:** https://github.com/micropython/micropython/wiki

**Generation:** `python scripts/scrape_wiki.py`

**Contents:**
- 80 wiki pages scraped
- 403 Q&A sections extracted
- Topics: board setup, build troubleshooting, Viper optimization, porting, etc.

**Format:**
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert MicroPython developer..."},
    {"role": "user", "content": "How do I build MicroPython for STM32?"},
    {"role": "assistant", "content": "...wiki content..."}
  ],
  "metadata": {
    "source": "wiki",
    "page": "Building-Micropython-Binaries",
    "header": "STM32 Build"
  }
}
```

## 5. Codebase Q&A Dataset (codebase_qa.jsonl)

**Source:** MicroPython source code (submodule at `./micropython/`, pinned to v1.27.0)

**Generation:** `python scripts/generate_codebase_qa.py`

**Final count: 3,936 examples from 412 source files**

**Category Breakdown:**
| Category | Files | Q&A Pairs | Description |
|----------|-------|-----------|-------------|
| py_core | ~37 | 407 | GC, VM, compiler, objects, QSTR |
| extmod | ~27 | 294 | Hardware abstraction, networking |
| ports | ~332 | 3,059 | All 20 port implementations |
| build_system | ~8 | 88 | Makefiles, configuration |
| docs_develop | ~8 | 88 | Architecture documentation |

**Generation Process:**
1. Read source files from each category
2. Use Claude CLI (haiku model) to generate Q&A pairs
3. Three types per file: explanation, howto, debugging
4. ~11 pairs per file (5 explanation + 3 howto + 3 debugging)
5. Checkpoint-based resume for long runs

**Format:**
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert MicroPython developer..."},
    {"role": "user", "content": "What does the gc_sweep function do?"},
    {"role": "assistant", "content": "The gc_sweep function..."}
  ],
  "metadata": {
    "source": "codebase",
    "source_file": "py/gc.c",
    "category": "py_core",
    "qa_type": "explanation"
  }
}
```

## 6. Application Development Q&A (app_dev_qa.jsonl)

**Source:** Claude-generated from wiki context + practical topics

**Generation:** `python scripts/generate_app_dev_qa.py`

**Final count: 539 examples across 12 topics**

**Topic Breakdown:**
| Topic | Q&A Pairs |
|-------|-----------|
| gpio | 39 |
| i2c_spi | 48 |
| uart_serial | 48 |
| timers_pwm | 48 |
| memory | 37 |
| freezing | 48 |
| networking | 56 |
| asyncio | 40 |
| filesystem | 48 |
| debugging | 55 |
| power | 40 |
| peripherals | 56 |

**Format:**
```json
{
  "messages": [
    {"role": "system", "content": "You are an expert MicroPython developer..."},
    {"role": "user", "content": "How do I read an I2C device?"},
    {"role": "assistant", "content": "from machine import I2C..."}
  ],
  "metadata": {
    "source": "app_dev",
    "topic": "i2c_spi",
    "subtopic": "I2C read/write operations"
  }
}
```

## 7. DPO Preferences (dpo_preferences.jsonl)

**Generation:** `python scripts/export_dpo_dataset.py`

**Total: 4,974 pairs** (including 276 conciseness pairs).

Four pair types targeting identified model failure modes:

| Pair Type | Count | Description |
|-----------|-------|-------------|
| Role confusion | ~2,000 | Substantive review_comment (chosen) vs merge/praise issue_comment (rejected) |
| Specificity | ~1,500 | Comments with code suggestions (chosen) vs without (rejected), matched by domain/component |
| Severity | ~1,198 | Higher severity preferred (blocking > suggestion > nitpick) |
| Conciseness | 276 | Terse Claude rewrite (chosen) vs verbose original (rejected). Generated via `claude -p`. Use `--skip-conciseness` to skip regeneration |

**Format:**
```json
{
  "prompt": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "chosen": "chosen response text",
  "rejected": "rejected response text",
  "type": "role_confusion"
}
```

The prompt field uses messages-based format (not hardcoded chat template tokens).

## Evaluation Datasets

Located in `data/eval/`:

| Dataset | Purpose | Examples |
|---------|---------|----------|
| held_out_reviews.jsonl | Style/quality eval | 551 |
| factual_qa.jsonl | Factual accuracy | 113 |
| port_knowledge.jsonl | Port-specific accuracy | 95 |
| style_benchmark.jsonl | A/B style testing | 200 |

**Generation:** `python scripts/generate_eval_benchmark.py --all`

## Validation

`python scripts/validate_training_data.py` runs 8 automated checks that must pass before training:

1. All JSONL files parse without errors
2. Every example has the required `messages` field with system/user/assistant roles
3. No empty assistant responses
4. No duplicate examples (by content hash)
5. DPO pairs have `prompt`, `chosen`, `rejected`, and `type` fields
6. Train/eval PR sets are disjoint (no data leakage)
7. Combined dataset weights match expected counts within tolerance
8. Metadata fields present and non-null where required

## Running Data Preparation

```bash
cd /home/anl/mpy/micropython-expert
source venv/bin/activate

python scripts/export_sft_dataset.py
python scripts/export_pr_reviews.py
python scripts/export_dpo_dataset.py          # add --skip-conciseness for fast run
python scripts/generate_synthetic_reviews.py  # optional, ~30min, uses Claude Code CLI
python scripts/combine_datasets.py
python scripts/validate_training_data.py      # must pass before training
```

Wiki, codebase, and app_dev datasets do not need regeneration unless sources change:
```bash
python scripts/scrape_wiki.py                 # only if wiki content updated
python scripts/generate_codebase_qa.py        # only if pinned micropython version changes (~5 hours)
python scripts/generate_app_dev_qa.py         # only if topics change (~1.5 hours)
python scripts/generate_eval_benchmark.py --all  # only if eval criteria change
```

## Data Quality Notes

1. **Review data** is real human-written content from a single expert (dpgeorge), filtered to substantive inline comments only
2. **Wiki data** is community-maintained, quality varies
3. **Generated Q&A** uses Claude (haiku) with source code context for grounding
4. **DPO pairs** target specific failure modes observed in v1 benchmarks (role confusion, lack of specificity, severity awareness)
5. **Malformed responses** (24 total) were filtered during app_dev generation

## v1 to v2 Migration

v2 replaced the v1 pipeline on Feb 4, 2025. Benchmark results from v1 showed the model produced fabricated responses, traced to training on `issue_comments` that lack diff context. The model learned to generate merge approvals and generic praise instead of substantive code review.

Key changes in v2:
- **Filtered to substantive review_comments only.** Dropped all issue_comments and review verdicts. Only review_comments with feedback_type in (suggestion, requirement, question) and a non-null diff_hunk are included.
- **PR-based eval split.** Train and eval sets are split by PR number, not random sampling, to prevent data leakage from multi-comment PRs.
- **Quality oversampling.** Comments with code suggestions, reusable patterns, or style examples are oversampled to increase their representation.
- **Targeted DPO pairs.** Replaced generic severity-only DPO with four pair types addressing specific failure modes (role confusion, specificity, conciseness, severity).
- **Automated validation.** `validate_training_data.py` enforces 8 checks before training can proceed.
