# Data Preparation Guide

This document describes the datasets used for training the MicroPython Expert model.

## Dataset Overview

| Dataset | Source | Examples | Status |
|---------|--------|----------|--------|
| reviews_sft.jsonl | dpgeorge review database | 16,753 | ✅ Complete |
| wiki_qa.jsonl | GitHub wiki pages | 403 | ✅ Complete |
| codebase_qa.jsonl | MicroPython source code | 3,936 | ✅ Complete |
| app_dev_qa.jsonl | Practical usage topics | 539 | ✅ Complete |
| dpo_preferences.jsonl | Severity-ranked reviews | 5,359 | ✅ Complete |
| combined_sft.jsonl | Weighted combination | 23,679 | ✅ Complete |

## Combined Dataset Summary

| Dataset | Original | Weight | After Weighting | % of Total |
|---------|----------|--------|-----------------|------------|
| reviews_sft | 16,753 | 1.0 | 16,753 | 70.8% |
| wiki_qa | 403 | 1.2 | 483 | 2.0% |
| codebase_qa | 3,936 | 1.5 | 5,904 | 24.9% |
| app_dev_qa | 539 | 1.0 | 539 | 2.3% |
| **Total** | **21,631** | | **23,679** | **100%** |

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

## 3. Codebase Q&A Dataset (codebase_qa.jsonl)

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

## 4. Application Development Q&A (app_dev_qa.jsonl)

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

## Evaluation Datasets

Located in `/data/eval/`:

| Dataset | Purpose | Examples |
|---------|---------|----------|
| held_out_reviews.jsonl | Style/quality eval | 1,861 |
| factual_qa.jsonl | Factual accuracy | 113 |
| port_knowledge.jsonl | Port-specific accuracy | 95 |
| style_benchmark.jsonl | A/B style testing | 200 |

**Generation:** `python scripts/generate_eval_benchmark.py --all`

## Data Quality Notes

1. **Review data** is real human-written content from a single expert (dpgeorge)
2. **Wiki data** is community-maintained, quality varies
3. **Generated Q&A** uses Claude (haiku) with source code context for grounding
4. **DPO pairs** assume severity ranking correlates with feedback quality
5. **Malformed responses** (24 total) were filtered during app_dev generation

## Running Data Preparation

Complete sequence (already run):
```bash
cd /home/anl/mpy/micropython-expert
source venv/bin/activate

# Step 1: Export review data (done)
python scripts/export_sft_dataset.py

# Step 2: Scrape wiki (done)
python scripts/scrape_wiki.py

# Step 3: Export DPO preferences (done)
python scripts/export_dpo_dataset.py

# Step 4: Generate codebase Q&A (done - took ~5 hours)
python scripts/generate_codebase_qa.py

# Step 5: Generate app dev Q&A (done - took ~1.5 hours)
python scripts/generate_app_dev_qa.py

# Step 6: Generate eval benchmarks (done)
python scripts/generate_eval_benchmark.py --all

# Step 7: Combine datasets (done)
python scripts/combine_datasets.py
```

## File Sizes

```
data/training/
  reviews_sft.jsonl       40M   16,753 examples
  wiki_qa.jsonl          574K      403 examples
  codebase_qa.jsonl      4.2M    3,936 examples
  app_dev_qa.jsonl       590K      539 examples
  dpo_preferences.jsonl   10M    5,359 pairs
  combined_sft.jsonl      57M   23,679 examples (weighted)

data/eval/
  held_out_reviews.jsonl  4.4M   1,861 examples
  factual_qa.jsonl         44K     113 examples
  port_knowledge.jsonl     35K      95 examples
  style_benchmark.jsonl   300K     200 examples
```

Total training data: ~112MB
Total eval data: ~4.8MB
