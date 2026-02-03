# Data Preparation Guide

This document describes the datasets used for training the MicroPython Expert model.

## Dataset Overview

| Dataset | Source | Examples | Status |
|---------|--------|----------|--------|
| reviews_sft.jsonl | dpgeorge review database | 16,753 | Complete |
| wiki_qa.jsonl | GitHub wiki pages | 403 | Complete |
| codebase_qa.jsonl | MicroPython source code | Target: 10-20K | Pending |
| app_dev_qa.jsonl | Practical usage topics | Target: 3-5K | Pending |
| dpo_preferences.jsonl | Severity-ranked reviews | 5,359 | Complete |

## 1. Review SFT Dataset (reviews_sft.jsonl)

**Source:** `/data/raw/dpgeorge_reviews.db` (from dpgeorge-review-db project)

**Generation:** `python scripts/export_sft_dataset.py`

**Contents:**
- 6,842 inline code review comments with diff context
- 9,518 PR discussion comments
- 393 review verdicts (APPROVED/CHANGES_REQUESTED)

**Format:**
```json
{
  "messages": [
    {"role": "system", "content": "...review system prompt..."},
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

**Notes:**
- 10% reserved for held-out evaluation (1,861 examples)
- Metadata includes 13-field categorization from dpgeorge-review-db
- Three system prompts: inline_review, pr_discussion, review_verdict

## 2. Wiki Q&A Dataset (wiki_qa.jsonl)

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

## 3. Codebase Q&A Dataset (codebase_qa.jsonl) - Pending

**Source:** MicroPython source code (submodule at `./micropython/`, pinned to v1.27.0)

**Generation:** `python scripts/generate_codebase_qa.py`

**Target: 10,000-20,000 examples**

**Categories:**
- py_core (4,000): GC, VM, compiler, objects, QSTR
- extmod (3,000): Hardware abstraction, networking, filesystem
- ports (5,000): All 22 port implementations
- build_system (1,500): Makefiles, configuration
- docs_develop (1,500): Architecture documentation

**Generation Process:**
1. Read source files from each category
2. Use Claude CLI to generate Q&A pairs
3. Three types per file: explanation, howto, debugging
4. Checkpoint-based resume for long runs

## 4. Application Development Q&A (app_dev_qa.jsonl) - Pending

**Source:** Claude-generated from wiki context + topics

**Generation:** `python scripts/generate_app_dev_qa.py`

**Target: 3,000-5,000 examples**

**Topics (12 total):**
- GPIO and Pin Control (400)
- I2C and SPI Communication (500)
- UART and Serial (300)
- Timers and PWM (350)
- Memory Management (450)
- Freezing and Deploying (350)
- WiFi and Networking (450)
- Async Programming (400)
- Filesystem and Storage (300)
- Debugging Techniques (400)
- Power Management (300)
- Common Peripheral Patterns (500)

## 5. DPO Preferences (dpo_preferences.jsonl)

**Source:** Review database severity rankings

**Generation:** `python scripts/export_dpo_dataset.py`

**Contents:**
- 4,931 severity-based pairs (blocking > suggestion > nitpick)
- 428 style-based pairs (is_style_example = true preferred)

**Format:**
```json
{
  "prompt": "<|system|>...<|user|>...",
  "chosen": "...blocking/suggestion review...",
  "rejected": "...nitpick/non-style review..."
}
```

## Combining Datasets

**Generation:** `python scripts/combine_datasets.py`

**Weights:**
- reviews_sft: 1.0 (baseline)
- wiki_qa: 1.2 (slight oversample for practical knowledge)
- codebase_qa: 1.5 (oversample for architecture knowledge)
- app_dev_qa: 1.0 (baseline)

**Output:** `combined_sft.jsonl`

## Evaluation Datasets

Located in `/data/eval/`:

| Dataset | Purpose | Examples |
|---------|---------|----------|
| held_out_reviews.jsonl | Style/quality eval | 1,861 |
| factual_qa.jsonl | Factual accuracy | Pending |
| port_knowledge.jsonl | Port-specific accuracy | Pending |
| style_benchmark.jsonl | A/B style testing | Pending |

**Generation:** `python scripts/generate_eval_benchmark.py --all`

## Data Quality Notes

1. **Review data** is real human-written content from a single expert (dpgeorge)
2. **Wiki data** is community-maintained, quality varies
3. **Generated Q&A** uses Claude with source code context for grounding
4. **DPO pairs** assume severity ranking correlates with feedback quality

## Running Data Preparation

Complete sequence:
```bash
cd /home/anl/mpy/micropython-expert
source venv/bin/activate

# Already complete:
python scripts/export_sft_dataset.py
python scripts/scrape_wiki.py
python scripts/export_dpo_dataset.py

# To run (uses Claude CLI, takes time):
python scripts/generate_codebase_qa.py
python scripts/generate_app_dev_qa.py
python scripts/generate_eval_benchmark.py --all

# Final combination:
python scripts/combine_datasets.py
```
